"""Version-bound local CDD exploratory matrix. Raw/prediction/model files stay gitignored."""
import os
for _thread_env in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_thread_env] = '2'
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIVATE = ROOT / 'data/shrink-cdd-20261013-v1'
PROTOCOL_PATH = HERE / 'SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json'
P = json.loads(PROTOCOL_PATH.read_text(encoding='utf-8'))
BUNDLE = ROOT / P['model']['bundle']
PREP = HERE / 'CDD_PREPARATION_MANIFEST_V1_1.json'
SYNTHETIC = HERE / 'CDD_MATRIX_SYNTHETIC_CHECK_V1_1.json'
RELEASE = HERE / 'CDD_MATRIX_EXECUTION_RELEASE_V1_1.json'
RESULT = HERE / 'CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def utc():
    return datetime.now(timezone.utc).isoformat()

def source_check():
    for rel, expected in P['model']['source_sha256'].items():
        if sha((BUNDLE / rel).read_bytes()) != expected:
            raise ValueError('Source pin drift: ' + rel)

def model(seed):
    source_check()
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    np.random.seed(seed)
    sys.path.insert(0, str(BUNDLE))
    spec = importlib.util.spec_from_file_location('shrink_full_derefusion', BUNDLE / 'models/derefusion/DeReFusion.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Model(SimpleNamespace(**P['model']['configuration'])).float()

def package(root, asset, fraction, values, dates, train_idx, val_idx, test_idx, scale):
    retain = math.ceil(fraction * len(train_idx))
    selected = train_idx[-retain:]
    start, end = selected[0] - 96, selected[-1] + 1
    mean = values[start:end].mean(axis=0)
    std = values[start:end].std(axis=0)
    if not np.isfinite(std).all() or (std <= 0).any() or scale <= 0:
        raise ValueError('Invalid training scale')
    normalized = (values - mean) / std
    location = root / f'{asset}_f{int(fraction*100):03d}'
    location.mkdir(parents=True, exist_ok=False)
    description = {'asset': asset, 'fraction': fraction, 'train_target_count': len(selected),
                   'train_raw_context_start': dates[start], 'train_last_target': dates[end-1],
                   'train_raw_candle_count': int(end-start), 'close_output_std': float(std[3]),
                   'rmsse_denominator': float(scale), 'packages': {}}
    for role, indices in [('train', selected), ('validation', val_idx), ('test', test_idx)]:
        keys = [f'CDD-BITSTAMP|{asset}|{dates[i]}T00:00:00Z|h1-close' for i in indices]
        x = np.stack([normalized[i-96:i] for i in indices]).astype(np.float32)
        y = normalized[indices].astype(np.float32)
        path = location / (role + '.npz')
        np.savez(path, role=np.array(role), x=x, y=y, keys=np.array(keys),
                 close_output_std=np.array(std[3]), rmsse_denominator=np.array(scale))
        manifest = path.with_suffix('.keys.json')
        write_json(manifest, {'role': role, 'expected_keys': keys, 'payload_sha256': sha(path.read_bytes())})
        description['packages'][role] = {'path': str(path), 'manifest': str(manifest),
                                          'sha256': sha(path.read_bytes()), 'count': len(keys),
                                          'keys_sha256': sha('\n'.join(keys).encode())}
    return description

def read_package(path, expected):
    manifest = json.loads(path.with_suffix('.keys.json').read_text(encoding='utf-8'))
    if sha(path.read_bytes()) != manifest['payload_sha256'] or manifest['role'] != expected:
        raise ValueError('Package identity drift')
    with np.load(path, allow_pickle=False) as z:
        if str(z['role'].item()) != expected:
            raise ValueError('Package role mismatch')
        x, y, keys = z['x'].copy(), z['y'].copy(), z['keys'].tolist()
        sd, scale = float(z['close_output_std']), float(z['rmsse_denominator'])
    if x.shape != (len(keys),96,4) or y.shape != (len(keys),4) or not len(keys):
        raise ValueError('Package shape mismatch')
    if keys != manifest['expected_keys'] or len(set(keys)) != len(keys):
        raise ValueError('Key coverage/uniqueness mismatch')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Non-finite package')
    return x, y, keys, sd, scale

def predict(m, x):
    m.eval()
    batches = []
    with torch.no_grad():
        for i in range(0, len(x), 64):
            y = m(torch.from_numpy(x[i:i+64]), None, None, None)
            if y.shape != (min(64,len(x)-i),1,4):
                raise ValueError('Model output shape mismatch')
            batches.append(y[:,0,3].double().numpy())
    result = np.concatenate(batches)
    if len(result) != len(x) or not np.isfinite(result).all():
        raise ValueError('Prediction coverage/non-finite failure')
    return result

def fit(train, validation, out, seed, steps):
    xt, yt, kt, sd, scale = read_package(train, 'train')
    xv, yv, kv, sv, vs = read_package(validation, 'validation')
    if sd != sv or scale != vs:
        raise ValueError('Inconsistent train-fitted transform')
    m = model(seed)
    nparams = sum(p.numel() for p in m.parameters())
    opt = torch.optim.Adam(m.parameters(), lr=.001, betas=(.9,.999), eps=1e-8, weight_decay=0)
    loader = DataLoader(TensorDataset(torch.from_numpy(xt), torch.from_numpy(yt)),
                        batch_size=32, shuffle=True, drop_last=False,
                        generator=torch.Generator().manual_seed(seed))
    iterator = iter(loader)
    best, best_state, best_step = float('inf'), None, None
    history, seen = [], 0
    for step in range(1, steps+1):
        try:
            xb,yb = next(iterator)
        except StopIteration:
            iterator = iter(loader)
            xb,yb = next(iterator)
        m.train()
        opt.zero_grad(set_to_none=True)
        pred = m(xb,None,None,None)
        loss = torch.mean((pred[:,0,3]-yb[:,3])**2)
        if not torch.isfinite(loss):
            raise ValueError('Non-finite fit loss')
        loss.backward()
        opt.step()
        seen += len(xb)
        if step % 50 == 0 or step == steps:
            val = float(np.mean((predict(m,xv)-yv[:,3].astype(np.float64))**2))
            improved = val < best
            if improved:
                best, best_step = val, step
                best_state = {k:v.detach().cpu().clone() for k,v in m.state_dict().items()}
            history.append({'step': step, 'validation_normalized_mse': val, 'strict_improvement': improved})
    # Ridge uses train-centered flattened windows and an unpenalized intercept.
    flat = xt.reshape(len(xt), -1).astype(np.float64)
    flat_val = xv.reshape(len(xv), -1).astype(np.float64)
    xm, ym = flat.mean(0), float(yt[:,3].mean(dtype=np.float64))
    centered = flat-xm
    gram = centered.T@centered/len(flat)
    rhs = centered.T@(yt[:,3].astype(np.float64)-ym)/len(flat)
    ridge_best, weights, chosen, ridge_history = float('inf'), None, None, []
    for alpha in P['linear_baseline']['lambdas']:
        coef = np.linalg.solve(gram+alpha*np.eye(flat.shape[1]), rhs)
        val_pred = (flat_val-xm)@coef+ym
        score = float(np.mean((val_pred-yv[:,3].astype(np.float64))**2))
        ridge_history.append({'lambda': alpha, 'validation_normalized_mse': score})
        if score < ridge_best:
            ridge_best, weights, chosen = score, coef, alpha
    state_digest = hashlib.sha256()
    for k,v in sorted(best_state.items()):
        state_digest.update(k.encode()); state_digest.update(v.numpy().tobytes())
    val_p = float(np.mean((xv[:,-1,3].astype(np.float64)-yv[:,3].astype(np.float64))**2))
    summary = {'seed':seed, 'steps':steps, 'training_samples_seen':seen,
               'effective_epochs': seen/len(xt), 'parameters': nparams, 'best_step':best_step,
               'validation_keys':len(kv), 'train_keys':len(kt),
               'validation_keys_sha256':sha('\n'.join(kv).encode()),
               'validation_mse': {'F':best*sd**2, 'L':ridge_best*sd**2, 'P':val_p*sd**2},
               'validation_rmsse': {'F':math.sqrt(best*sd**2/scale), 'L':math.sqrt(ridge_best*sd**2/scale), 'P':math.sqrt(val_p*sd**2/scale)},
               'ridge_lambda':chosen, 'ridge_history':ridge_history, 'history':history,
               'state_tensor_sha256':state_digest.hexdigest(),
               'train_package_sha256':sha(train.read_bytes()), 'validation_package_sha256':sha(validation.read_bytes()),
               'test_path_received':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    torch.save({'F':best_state, 'ridge_coef':torch.from_numpy(weights), 'ridge_x_mean':torch.from_numpy(xm),
                'ridge_y_mean':ym, 'close_output_std':sd, 'rmsse_denominator':scale,
                'summary':summary}, out)
    write_json(out.with_suffix('.fit.json'), summary)
    return summary

def evaluate(checkpoint, test, out):
    x,y,keys,sd,scale = read_package(test,'test')
    saved = torch.load(checkpoint,map_location='cpu',weights_only=True)
    if saved['close_output_std'] != sd or saved['rmsse_denominator'] != scale:
        raise ValueError('Evaluator transform mismatch')
    m = model(saved['summary']['seed']); m.load_state_dict(saved['F'])
    predictions = {'F':predict(m,x),
                   'L':(x.reshape(len(x),-1).astype(np.float64)-saved['ridge_x_mean'].numpy())@saved['ridge_coef'].numpy()+saved['ridge_y_mean'],
                   'P':x[:,-1,3].astype(np.float64)}
    errors = {arm:(v-y[:,3].astype(np.float64))**2*sd**2 for arm,v in predictions.items()}
    metrics = {}
    for period in ['all','2024','2025']:
        ix = np.arange(len(keys)) if period == 'all' else np.array([i for i,k in enumerate(keys) if '|'+period+'-' in k])
        if not len(ix):
            continue
        mse = {arm:float(err[ix].mean()) for arm,err in errors.items()}
        metrics[period] = {'key_count':len(ix), 'mse':mse,
                           'rmsse':{arm:math.sqrt(v/scale) for arm,v in mse.items()},
                           'mse_L_minus_F':mse['L']-mse['F']}
    if not all(np.isfinite(v).all() for v in predictions.values()):
        raise ValueError('Non-finite forecast')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_suffix('.predictions.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['key','F_normalized_close','L_normalized_close','P_normalized_close','target_normalized_close'])
        for i,key in enumerate(keys):
            w.writerow([key,*[predictions[a][i] for a in ['F','L','P']],y[i,3]])
    result={'test_keys_sha256':sha('\n'.join(keys).encode()), 'test_key_count':len(keys),
            'checkpoint_sha256':sha(checkpoint.read_bytes()), 'metrics':metrics}
    write_json(out,result)
    return result

def child(args):
    started=time.monotonic()
    proc=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),*map(str,args)],
                        capture_output=True,text=True,timeout=1800)
    if proc.returncode:
        raise RuntimeError(f'Worker failed ({proc.returncode}): '+proc.stderr[-2000:])
    result=json.loads(proc.stdout.strip().splitlines()[-1]); result['seconds']=time.monotonic()-started
    return result

def synthetic():
    if SYNTHETIC.exists(): raise ValueError('Synthetic record already exists')
    rng=np.random.default_rng(421)
    close=100+np.cumsum(rng.normal(0,.2,210))
    values=np.column_stack([close+.03,close+.2,close-.2,close])
    dates=[f'SYN-{i:04d}' for i in range(len(values))]
    indices=(np.arange(96,180),np.arange(180,199),np.arange(199,210))
    with tempfile.TemporaryDirectory(prefix='drf_cdd_matrix_synth_') as td:
        root=Path(td)
        a=package(root/'a','SYN',.25,values,dates,*indices,.04)
        write_json(root/'package_description.json', a)
        mutated=values.copy(); mutated[199:] += 1000
        b=package(root/'b','SYN',.25,mutated,dates,*indices,.04)
        for role in ['train','validation']:
            ax,ay,ak,asd,asc=read_package(Path(a['packages'][role]['path']),role)
            bx,by,bk,bsd,bsc=read_package(Path(b['packages'][role]['path']),role)
            if not np.array_equal(ax,bx) or not np.array_equal(ay,by) or ak!=bk or asd!=bsd or asc!=bsc:
                raise ValueError('Test mutation contaminated fit packages')
        train,val,test=[Path(a['packages'][role]['path']) for role in ['train','validation','test']]
        fitted=child(['--worker','fit','--train',train,'--validation',val,'--checkpoint',root/'synthetic.pt','--seed',17,'--steps',12])
        evaluated=child(['--worker','evaluate','--test',test,'--checkpoint',root/'synthetic.pt','--out',root/'eval.json'])
        bad=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker','fit','--train',str(train),
                            '--validation',str(val),'--test',str(test),'--checkpoint',str(root/'bad.pt'),'--seed','17','--steps','12'],capture_output=True,text=True)
        if bad.returncode==0 or (root/'bad.pt').exists(): raise ValueError('Fit worker accepted test argument')
        if fitted['validation_keys']!=19 or evaluated['test_key_count']!=11: raise ValueError('Tail coverage failed')
        write_json(SYNTHETIC,{'result':'PASS','scope':'Synthetic matrix pipeline, not real performance',
                             'protocol_sha256':sha(PROTOCOL_PATH.read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),
                             'torch':torch.__version__,'checks':{'test_mutation_fit_packages_unchanged':True,
                             'fit_worker_rejects_test_argument':True,'incomplete_batch_keys_included':True,
                             'checkpoint_restore_and_F_L_P_evaluation':True},
                             'fit':fitted,'evaluation':evaluated,'timestamp_utc':utc()})
    print(json.dumps({'result':'PASS','synthetic_record':str(SYNTHETIC)}),flush=True)

def prepare():
    if PREP.exists(): raise ValueError('Preparation record already exists')
    qa_path=HERE/'CDD_QUALIFICATION_RESULTS_V1.json'
    if sha(qa_path.read_bytes())!=P['qualification_record_sha256']: raise ValueError('QA pin drift')
    record={'protocol_id':P['protocol_id'],'protocol_sha256':sha(PROTOCOL_PATH.read_bytes()),
            'runner_sha256':sha(Path(__file__).read_bytes()),'source_sha256':P['model']['source_sha256'],
            'prepared_at_utc':utc(),'combinations':[]}
    source_check()
    for asset in P['assets']:
        raw=PRIVATE/(asset+'.raw.csv')
        if sha(raw.read_bytes())!=P['raw_sha256'][asset]: raise ValueError('Raw pin drift')
        lines=raw.read_text(encoding='utf-8-sig').splitlines()
        if lines[0].startswith('http'): lines=lines[1:]
        records=[]
        for row in csv.DictReader(lines):
            d=datetime.fromtimestamp(float(row['unix']),timezone.utc).date().isoformat()
            if '2018-01-01'<=d<'2026-01-01':
                records.append((d,*[float(row[k]) for k in ['open','high','low','close']]))
        records.sort()
        dates=[r[0] for r in records]; values=np.array([r[1:] for r in records],dtype=np.float64)
        train=np.array([i for i,d in enumerate(dates) if i>=96 and d<'2023-01-01'])
        val=np.array([i for i,d in enumerate(dates) if '2023-01-01'<=d<'2024-01-01'])
        test=np.array([i for i,d in enumerate(dates) if '2024-01-01'<=d<'2026-01-01'])
        prefix=values[[i for i,d in enumerate(dates) if d<'2023-01-01'],3]
        scale=float(np.mean(np.diff(prefix)**2))
        for fraction in P['line_A']['fractions']:
            entry=package(PRIVATE/'packages_v1_1',asset,fraction,values,dates,train,val,test,scale)
            record['combinations'].append(entry)
            print(json.dumps({'prepared':asset,'fraction':fraction,'train_targets':entry['train_target_count'],
                              'validation_keys':len(val),'test_keys':len(test)}),flush=True)
    keysets={r['asset']:set() for r in record['combinations']}
    for r in record['combinations']: keysets[r['asset']].add(r['packages']['test']['keys_sha256'])
    if any(len(v)!=1 for v in keysets.values()): raise ValueError('Common evaluation keys mismatch')
    record['result']='PASS'; write_json(PREP,record)

def run():
    release=json.loads(RELEASE.read_text(encoding='utf-8'))
    if release['decision']!='APPROVED': raise ValueError('Run not released')
    for path,key in [(PROTOCOL_PATH,'protocol_sha256'),(Path(__file__),'runner_sha256'),(PREP,'preparation_sha256'),(SYNTHETIC,'synthetic_sha256')]:
        if sha(path.read_bytes())!=release[key]: raise ValueError('Execution pin drift: '+key)
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()!=release['head']: raise ValueError('HEAD drift')
    if RESULT.exists(): raise ValueError('Results exist; no overwrite')
    prep=json.loads(PREP.read_text(encoding='utf-8'))
    summaries=[]; started=time.monotonic()
    for combination in prep['combinations']:
        for seed in P['model']['seeds']:
            if time.monotonic()-started>P['budget']['maximum_seconds_batch']: raise ValueError('Batch budget exceeded')
            ckpt=PRIVATE/'runs_v1_1'/f"{combination['asset']}_f{int(combination['fraction']*100):03d}_s{seed}"/'model.pt'
            if ckpt.exists(): raise ValueError('Fit artifact exists; no silent retry')
            train=combination['packages']['train']['path']; val=combination['packages']['validation']['path']
            fitted=child(['--worker','fit','--train',train,'--validation',val,'--checkpoint',ckpt,
                          '--seed',seed,'--steps',P['model']['steps_per_fit']])
            summaries.append({'asset':combination['asset'],'fraction':combination['fraction'],'seed':seed,
                              'fit':fitted,'checkpoint':str(ckpt),'test':combination['packages']['test']['path']})
            write_json(PRIVATE/'RUN_PROGRESS.json',{'stage':'FIT','completed_F_fits':len(summaries),'planned_F_fits':24,'updated_at_utc':utc()})
            print(json.dumps({'completed_F_fits':len(summaries),'planned':24,'asset':combination['asset'],
                              'fraction':combination['fraction'],'seed':seed,'worker_seconds':round(fitted['seconds'],2)}),flush=True)
    rank=[]
    for asset in P['assets']:
        vals=[r['fit']['validation_rmsse']['F'] for r in summaries if r['asset']==asset and r['fraction']==1]
        if len(vals)!=3: raise ValueError('Ranking has missing seeds')
        rank.append({'asset':asset,'mean_validation_rmsse_F':float(np.mean(vals))})
    rank.sort(key=lambda x:(x['mean_validation_rmsse_F'],x['asset']))
    ranking_path=HERE/'CDD_VALIDATION_ROSTER_FREEZE_V1_1.json'
    if ranking_path.exists(): raise ValueError('Roster already frozen')
    write_json(ranking_path,{'protocol_id':P['protocol_id'],'frozen_at_utc':utc(),'before_any_test_evaluation':True,'ranking':rank})
    for row in summaries:
        row['evaluation']=child(['--worker','evaluate','--test',row['test'],'--checkpoint',row['checkpoint'],
                                 '--out',Path(row['checkpoint']).with_name('evaluation.json')])
    roster=[]
    for n in [1,len(rank)]:
        members=[r['asset'] for r in rank[:n]]
        for period in ['all','2024','2025']:
            asset_scores=[np.mean([r['evaluation']['metrics'][period]['rmsse']['F'] for r in summaries
                                  if r['asset']==a and r['fraction']==1]) for a in members]
            roster.append({'size':n,'assets':members,'period':period,'equal_asset_mean_RMSSE_F':float(np.mean(asset_scores)),
                           'median_asset_RMSSE_F':float(np.median(asset_scores))})
    result={'protocol_id':P['protocol_id'],'release_sha256':sha(RELEASE.read_bytes()),'scope':'EXPLORATORY; new CDD source, not R1 confirmation',
            'finished_at_utc':utc(),'planned_F_fits':24,'completed_F_fits':len(summaries),
            'total_optimizer_steps':sum(r['fit']['steps'] for r in summaries),'source_raw_sha256':P['raw_sha256'],
            'validation_roster_freeze_sha256':sha(ranking_path.read_bytes()),'runs':summaries,'line_B_rosters':roster,
            'limitations':['Two crypto assets only, 24/7 grid; no stock-index evidence','600-step cap is not a convergence guarantee',
                           'Validation-selected rosters change composition, not training quality of an individual asset',
                           'Three seeds and two test years are not independent markets','Historical test exposure; exploratory only',
                           'No nonlinear-mechanism attribution; no commercial/public raw, predictions or weights release']}
    write_json(RESULT,result)
    print(json.dumps({'result':'COMPLETE','completed_F_fits':len(summaries),'results':str(RESULT)}),flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--phase',choices=['synthetic','prepare','run'])
    ap.add_argument('--worker',choices=['fit','evaluate'])
    for arg in ['train','validation','test','checkpoint','out']: ap.add_argument('--'+arg,type=Path)
    ap.add_argument('--seed',type=int); ap.add_argument('--steps',type=int)
    a=ap.parse_args()
    if a.worker=='fit':
        if a.test is not None or a.out is not None: ap.error('Fit worker must not receive test/evaluation inputs')
        if not all([a.train,a.validation,a.checkpoint,a.seed,a.steps]): ap.error('Fit inputs missing')
        print(json.dumps(fit(a.train,a.validation,a.checkpoint,a.seed,a.steps)),flush=True)
    elif a.worker=='evaluate':
        if a.train is not None or a.validation is not None: ap.error('Evaluator must not receive fit inputs')
        print(json.dumps(evaluate(a.checkpoint,a.test,a.out)),flush=True)
    elif a.phase=='synthetic': synthetic()
    elif a.phase=='prepare': prepare()
    elif a.phase=='run': run()
    else: ap.error('Select a phase or worker')

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        write_json(PRIVATE/('FAILURE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json'),
                   {'timestamp_utc':utc(),'exception_type':type(e).__name__,'reason':str(e),'runner_sha256':sha(Path(__file__).read_bytes())})
        raise

