"""Bound ETH development diagnostic. Frozen historical artifacts remain read-only."""
import os
for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[name] = '2'
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
from types import SimpleNamespace
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from models.derefusion.bundle_v3_pin.loader import load_model_class, verify_archive
from reproduction.preprocessing.fixed_ohlc import AggregationPlan, aggregate_ohlc
HISTORY = ROOT/'research_work/project_management_2026_10_10/compression_pilot_2026_10_13'
PRIVATE = ROOT/'data/cdd-compression-diagnostic-20261013-v2'
ARMS = ('raw96', 'raw48', 'mixed48')
PLAN = AggregationPlan(96, 4, 16, 32)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def utc(): return datetime.now(timezone.utc).isoformat()
def protocol(): return load(HERE/'PROTOCOL_V1.json')
def head(): return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
def private_bytes(): return sum(p.stat().st_size for p in PRIVATE.rglob('*') if p.is_file()) if PRIVATE.exists() else 0

def write_bytes(p, payload):
    p = Path(p).resolve()
    if not (p.is_relative_to(PRIVATE) or p.is_relative_to(HERE)) or p.exists():
        raise ValueError('Invalid destination or overwrite: '+str(p))
    if p.is_relative_to(PRIVATE) and private_bytes()+len(payload) > protocol()['resources']['private_output_bytes']:
        raise ValueError('Private output cap')
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f: f.write(payload)

def dump(p, obj): write_bytes(p, (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())

def check(require_release=False):
    p = protocol()
    if head() != p['head']: raise ValueError('HEAD drift')
    if platform.python_version() != '3.11.15' or torch.__version__ != '2.5.1+cpu' or np.__version__ != '2.1.2':
        raise ValueError('Environment drift')
    for rel, pin in p['code_and_history_sha256'].items():
        if sha(ROOT/rel) != pin: raise ValueError('Code/history drift: '+rel)
    verify_archive()
    if require_release:
        a = load(HERE/'EXECUTION_RELEASE_V1.json')
        if a['decision'] != 'APPROVED' or a['protocol_sha256'] != sha(HERE/'PROTOCOL_V1.json') or a['head'] != head():
            raise ValueError('No exact-bound execution release')
        for rel, pin in a['gate_sha256'].items():
            if sha(HERE/rel) != pin: raise ValueError('Gate drift: '+rel)
    return p

def engine():
    spec = importlib.util.spec_from_file_location('_historic_diagnostic_utilities', HISTORY/'run_pilot_v1.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def transformed(x, arm):
    if arm == 'raw96': return x
    if arm == 'raw48': return x[:, -48:].copy()
    if arm == 'mixed48': return aggregate_ohlc(x, PLAN)
    raise ValueError('Unknown arm')

def model(arm, seed):
    torch.set_num_threads(2); torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed); np.random.seed(seed)
    cfg = dict(protocol()['model_configuration'], seq_len=96 if arm == 'raw96' else 48)
    return load_model_class()(SimpleNamespace(**cfg)).float()

def state_hash(state):
    h = hashlib.sha256()
    for k,v in sorted(state.items()): h.update(k.encode()); h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def source_role(role):
    check()
    item = load(HISTORY/'PREPARATION_V1.json')['arms']['raw96'][role]
    p = ROOT/f'data/shrink-cdd-20261013-v1/packages_v1_1/ETHUSD_f100/{role}.npz'
    if sha(p) != item['sha256'] or sha(p.with_suffix('.keys.json')) != item['manifest_sha256']:
        raise ValueError('Input role drift')
    return engine().read_role(p, role, 96)

def role(arm, which):
    prep = load(HERE/'PREPARATION_V1.json')['arms'][arm][which]
    p = ROOT/prep['path']
    if sha(p) != prep['sha256'] or sha(p.with_suffix('.keys.json')) != prep['manifest_sha256']:
        raise ValueError('Prepared role drift')
    return engine().read_role(p, which, 96 if arm == 'raw96' else 48)

def predict(m, x): return engine().predict(m, x)
def clone_state(m): return {k:v.detach().cpu().clone() for k,v in m.state_dict().items()}
def mse(pred, target, sd): return math.fsum((float(a)-float(b))**2 for a,b in zip(pred,target))/len(target)*sd**2

def synthetic():
    check()
    x = np.arange(3*96*4,dtype=np.float32).reshape(3,96,4)
    assert np.array_equal(transformed(x,'raw48'), x[:,-48:])
    xc = transformed(x,'mixed48'); oracle=np.empty_like(xc)
    for j in range(16):
        b=x[:,4*j:4*j+4]; oracle[:,j]=np.stack([b[:,0,0],b[:,:,1].max(1),b[:,:,2].min(1),b[:,-1,3]],1)
    oracle[:,16:]=x[:,64:]
    assert np.array_equal(oracle,xc) and not np.shares_memory(x,xc)
    for seed in (17,29,43):
        a,b=model('raw48',seed),model('mixed48',seed)
        assert state_hash(a.state_dict()) == state_hash(b.state_dict())
    params={}
    for arm in ARMS:
        m=model(arm,17); xin=transformed(x,arm); out=m(torch.from_numpy(xin),None,None,None)
        assert out.shape == (3,1,4)
        loss=(out[:,0,3]-torch.from_numpy(xin[:,-1,3])).square().mean(); loss.backward()
        assert torch.isfinite(loss) and all(torch.isfinite(v.grad).all() for v in m.parameters() if v.grad is not None)
        assert len(predict(m,np.repeat(xin[:1],65,axis=0))) == 65
        params[arm]=sum(v.numel() for v in m.parameters())
    assert params == {'raw96':21743,'raw48':21599,'mixed48':21599}
    assert min([(50,2.),(100,1.),(150,1.)],key=lambda t:t[1])[0] == 100
    try: write_bytes(ROOT/'outside-diagnostic-probe', b'bad')
    except ValueError: pass
    else: raise AssertionError('Boundary failure')
    dump(HERE/'SYNTHETIC_CHECK_V1.json',dict(result='PASS',parameters=params,scope='Synthetic forward/gradient, transformations, paired initialization, 65-key tail and write-boundary checks',protocol_sha256=sha(HERE/'PROTOCOL_V1.json')))

def expected_keys(start,stop):
    d,e=date.fromisoformat(start),date.fromisoformat(stop); out=[]
    while d<e:
        out.append(f'CDD-BITSTAMP|ETHUSD|{d.isoformat()}T00:00:00Z|h1-close'); d+=timedelta(days=1)
    return out

def prepare():
    check(); result=dict(result='PASS',arms={a:{} for a in ARMS},source_checks=[])
    originals={}
    for which,start,stop in [('train','2018-04-07','2023-01-01'),('validation','2023-01-01','2024-01-01')]:
        x,y,keys,sd,scale=source_role(which); originals[which]=(x,y,keys,sd,scale)
        assert keys == expected_keys(start,stop)
        assert np.array_equal(x[:-1,1:],x[1:,:-1]) and np.array_equal(y[:-1],x[1:,-1])
        for arm in ARMS:
            xc=transformed(x,arm)
            assert np.array_equal(xc[:,-1],x[:,-1])
            dest=PRIVATE/'packages'/arm/(which+'.npz'); buf=io.BytesIO()
            np.savez(buf,role=np.array(which),x=xc,y=y,keys=np.array(keys),close_output_std=np.array(sd),rmsse_denominator=np.array(scale))
            write_bytes(dest,buf.getvalue())
            dump(dest.with_suffix('.keys.json'),dict(role=which,expected_keys=keys,payload_sha256=sha(dest)))
            if arm in ('raw96','mixed48'):
                assert sha(dest)==load(HISTORY/'PREPARATION_V1.json')['arms'][arm][which]['sha256']
            result['arms'][arm][which]=dict(path=dest.relative_to(ROOT).as_posix(),sha256=sha(dest),manifest_sha256=sha(dest.with_suffix('.keys.json')),keys_count=len(keys),keys_sha256=hashlib.sha256('\n'.join(keys).encode()).hexdigest(),shape=list(xc.shape),x_bytes=xc.nbytes,close_output_std=sd,rmsse_denominator=scale)
    tx,ty,_,ts,td=originals['train']; vx,vy,_,vs,vd=originals['validation']
    assert (ts,td)==(vs,vd) and np.array_equal(tx[-1,1:],vx[0,:-1]) and np.array_equal(ty[-1],vx[0,-1])
    result['source_checks']=['Full within-role adjacent-window/target equality','Train-validation boundary equality','Exact independently dated key sets','Same scaler and ruler','Historical raw96/mixed48 payload bytes reproduced']
    result['source_scope']='Package continuity and declared completed-daily-bar contract; external candle identity inherited from parent, not newly authenticated'
    result['position_spans_days']={'raw96':[1]*96,'raw48':[1]*48,'mixed48':PLAN.position_spans_days()}
    dump(HERE/'PREPARATION_V1.json',result)

def restore_history():
    check(); old=load(HISTORY/'RESULTS_V1.json'); audit=load(HISTORY/'INTERNAL_AUDIT_V1.json'); checks=[]
    for item in old['arms']:
        arm=item['arm']; out=ROOT/'data/cdd-compression-pilot-20261013-v1/runs'/arm
        for name,pin in audit['private_artifact_sha256'][arm].items():
            assert sha(out/name)==pin
        saved=torch.load(out/'model.pt',map_location='cpu',weights_only=True)
        assert state_hash(saved['F'])==item['state_tensor_sha256']
        x,y,keys,sd,scale=role(arm,'validation'); m=model(arm,17); m.load_state_dict(saved['F'])
        f=predict(m,x); rows=list(csv.DictReader((out/'validation.predictions.csv').open(encoding='utf-8',newline='')))
        assert [r['key'] for r in rows]==keys
        assert np.array_equal(f,np.array([float(r['F']) for r in rows]))
        assert np.array_equal(y[:,3].astype(np.float64),np.array([float(r['target']) for r in rows]))
        l=(x.reshape(len(x),-1).astype(np.float64)-saved['ridge_x_mean'].numpy())@saved['ridge_coef'].numpy()+saved['ridge_y_mean']
        for name,values in [('F',f),('L',l),('P',x[:,-1,3].astype(np.float64))]:
            assert np.array_equal(values,np.array([float(r[name]) for r in rows]))
            assert math.isclose(mse(values,y[:,3],sd),item['mse'][name],rel_tol=1e-12)
        checks.append(dict(arm=arm,state_tensor_sha256=state_hash(saved['F']),validation_keys=len(keys)))
    dump(HERE/'HISTORICAL_RESTORE_V1.json',dict(result='PASS',checks=checks,fits=0,test_read=False,scope='All frozen validation predictions recovered with archive loader; no re-selection'))

def release():
    check(); gates=['SYNTHETIC_CHECK_V1.json','PREPARATION_V1.json','HISTORICAL_RESTORE_V1.json','ENGINEERING_REVIEW_V1.json']
    assert all(load(HERE/x)['result']=='PASS' for x in gates)
    dump(HERE/'EXECUTION_RELEASE_V1.json',dict(decision='APPROVED',head=head(),protocol_sha256=sha(HERE/'PROTOCOL_V1.json'),gate_sha256={x:sha(HERE/x) for x in gates},decision_owner='Codex project delegate',authorization_basis='User standing project delegation plus explicit instruction to execute high-quality-model V2 plan',scope='Nine ETH training/validation trajectories plus three deterministic ridge flows; no test, external contacts or paid compute',timestamp_utc=utc()))

def persist_state(path,state):
    b=io.BytesIO(); torch.save(state,b); write_bytes(path,b.getvalue())

def worker(arm,seed):
    check(True); out=PRIVATE/'runs'/f'{arm}_s{seed}'
    if out.exists(): raise ValueError('No attempt reuse')
    xt,yt,kt,sd,scale=role(arm,'train'); xv,yv,kv,sv,ss=role(arm,'validation')
    assert (sd,scale)==(sv,ss)
    m=model(arm,seed); initial=state_hash(m.state_dict())
    opt=torch.optim.Adam(m.parameters(),lr=.001,betas=(.9,.999),eps=1e-8,weight_decay=0)
    loader=DataLoader(TensorDataset(torch.from_numpy(xt),torch.from_numpy(yt)),batch_size=32,shuffle=True,drop_last=False,generator=torch.Generator().manual_seed(seed))
    it=iter(loader); best=float('inf'); beststate=None; beststep=None; hist=[]; snapshots=[]; seen=0; started=time.perf_counter()
    for step in range(1,1801):
        try: xb,yb=next(it)
        except StopIteration: it=iter(loader); xb,yb=next(it)
        m.train(); opt.zero_grad(set_to_none=True); yp=m(xb,None,None,None)
        loss=(yp[:,0,3]-yb[:,3]).square().mean()
        if not torch.isfinite(loss): raise ValueError('Nonfinite loss')
        loss.backward()
        if not all(torch.isfinite(v.grad).all() for v in m.parameters() if v.grad is not None): raise ValueError('Nonfinite gradient')
        opt.step(); seen+=len(xb)
        if step%50==0:
            val=float(np.mean((predict(m,xv)-yv[:,3].astype(np.float64))**2)); improved=val<best
            if not math.isfinite(val): raise ValueError('Nonfinite validation')
            if improved: best,beststep,beststate=val,step,clone_state(m)
            hist.append(dict(step=step,validation_normalized_MSE=val,strict_improvement=improved))
        if step in (600,1200,1800):
            elapsed=time.perf_counter()-started; peak=engine().peak_working_set(); laststate=clone_state(m)
            terminal=predict(m,xv); m.load_state_dict(beststate); chosen=predict(m,xv); m.load_state_dict(laststate)
            if seed==17 and arm in ('raw96','mixed48') and step==600:
                old=next(a for a in load(HISTORY/'RESULTS_V1.json')['arms'] if a['arm']==arm)
                assert state_hash(beststate)==old['state_tensor_sha256'], '600-step control state mismatch'
                assert math.isclose(mse(chosen,yv[:,3],sd),old['mse']['F'],rel_tol=1e-12)
            for kind,state in [('best',beststate),('terminal',laststate)]: persist_state(out/f'{step}_{kind}.pt',state)
            b=io.BytesIO(); np.savez(b,F_best=chosen,F_terminal=terminal,keys=np.array(kv)); write_bytes(out/f'{step}_predictions.npz',b.getvalue())
            snapshots.append(dict(budget=step,best_step=beststep,best_state_tensor_sha256=state_hash(beststate),terminal_state_tensor_sha256=state_hash(laststate),F_MSE=mse(chosen,yv[:,3],sd),terminal_MSE=mse(terminal,yv[:,3],sd),samples_seen=seen,effective_epochs=seen/len(kt),neural_elapsed_seconds=elapsed,peak_working_set_bytes=peak))
    result=dict(arm=arm,seed=seed,steps=1800,initial_state_tensor_sha256=initial,train_keys=len(kt),validation_keys=len(kv),parameters=sum(v.numel() for v in m.parameters()),history=hist,snapshots=snapshots,validation_keys_sha256=hashlib.sha256('\n'.join(kv).encode()).hexdigest(),test_read=False)
    dump(out/'fit.json',result); print(json.dumps(result,allow_nan=False))

def ridge_worker(arm):
    check(True); out=PRIVATE/'ridge'/arm
    xt,yt,_,sd,scale=role(arm,'train'); xv,yv,keys,_,_=role(arm,'validation')
    flat=xt.reshape(len(xt),-1).astype(np.float64); fv=xv.reshape(len(xv),-1).astype(np.float64)
    xm=flat.mean(0); ym=float(yt[:,3].mean(dtype=np.float64)); z=flat-xm; target=yt[:,3].astype(np.float64)-ym
    gram=z.T@z/len(z); rhs=z.T@target/len(z); rows=[]; coeff={}; predictions={}; started=time.perf_counter()
    for alpha in protocol()['ridge_wide_lambdas']:
        w=np.linalg.lstsq(z,target,rcond=1e-12)[0] if alpha==0 else np.linalg.solve(gram+alpha*np.eye(z.shape[1]),rhs)
        pred=(fv-xm)@w+ym
        if not np.isfinite(w).all() or not np.isfinite(pred).all(): raise ValueError('Nonfinite ridge')
        score=float(np.mean((pred-yv[:,3].astype(np.float64))**2)); rows.append(dict(lambda_value=alpha,validation_normalized_MSE=score,MSE=mse(pred,yv[:,3],sd)))
        coeff[alpha]=w; predictions[alpha]=pred
    legacy=min([r for r in rows if r['lambda_value'] in protocol()['ridge_legacy_lambdas']],key=lambda r:r['validation_normalized_MSE'])
    wide=min(rows,key=lambda r:r['validation_normalized_MSE'])
    b=io.BytesIO(); np.savez(b,L_legacy=predictions[legacy['lambda_value']],L_wide=predictions[wide['lambda_value']],P=xv[:,-1,3].astype(np.float64),legacy_coef=coeff[legacy['lambda_value']],wide_coef=coeff[wide['lambda_value']],x_mean=xm,y_mean=np.array(ym),keys=np.array(keys))
    write_bytes(out/'predictions_and_coefficients.npz',b.getvalue())
    result=dict(arm=arm,candidate_solutions=len(rows),candidates=rows,L_legacy=legacy,L_wide=wide,P_MSE=mse(xv[:,-1,3],yv[:,3],sd),seconds=time.perf_counter()-started)
    dump(out/'fit.json',result); print(json.dumps(result,allow_nan=False))

def run():
    p=check(True); summaries=[]; baselines=[]; start=time.monotonic()
    def child(args):
        remaining=p['resources']['batch_seconds']-(time.monotonic()-start)
        if remaining<=0: raise ValueError('Batch cap')
        cp=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),*args],cwd=ROOT,capture_output=True,text=True,timeout=min(300,remaining))
        if cp.returncode: raise RuntimeError(cp.stderr[-3000:])
        return json.loads(cp.stdout.strip().splitlines()[-1])
    for arm in ARMS:
        result=child(['ridge','--arm',arm]); baselines.append(result)
        print(json.dumps(dict(ridge_complete=arm,L_legacy_MSE=result['L_legacy']['MSE'],L_wide_MSE=result['L_wide']['MSE'])),flush=True)
    order=[(17,'raw96'),(17,'raw48'),(17,'mixed48'),(29,'raw48'),(29,'mixed48'),(29,'raw96'),(43,'mixed48'),(43,'raw96'),(43,'raw48')]
    for seed,arm in order:
        result=child(['worker','--arm',arm,'--seed',str(seed)]); summaries.append(result)
        print(json.dumps(dict(complete=len(summaries),planned=9,arm=arm,seed=seed,F_MSE_1800=result['snapshots'][-1]['F_MSE'])),flush=True)
    assert sum(r['steps'] for r in summaries)==16200
    dump(HERE/'RESULTS_V1.json',dict(protocol_id=p['protocol_id'],head=head(),protocol_sha256=sha(HERE/'PROTOCOL_V1.json'),release_sha256=sha(HERE/'EXECUTION_RELEASE_V1.json'),scope='Exposed validation-only development',runs=summaries,baselines=baselines,completed_F_fits=9,total_optimizer_steps=16200,unique_ridge_flows=3,ridge_candidate_solutions=30,batch_seconds=time.monotonic()-start,private_bytes=private_bytes(),test_read=False,finished_at_utc=utc()))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('phase',choices=['synthetic','prepare','restore','release','run','worker','ridge']); ap.add_argument('--arm',choices=ARMS); ap.add_argument('--seed',type=int,choices=[17,29,43]); args=ap.parse_args()
    if args.phase=='worker' and (args.arm is None or args.seed is None): ap.error('arm and seed required')
    if args.phase=='ridge' and args.arm is None: ap.error('arm required')
    if args.phase=='worker': worker(args.arm,args.seed)
    elif args.phase=='ridge': ridge_worker(args.arm)
    else: {'synthetic':synthetic,'prepare':prepare,'restore':restore_history,'release':release,'run':run}[args.phase]()

if __name__=='__main__':
    try: main()
    except Exception as exc:
        dump(HERE/('FAILURE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),dict(reason=str(exc),type=type(exc).__name__,timestamp_utc=utc()))
        raise
