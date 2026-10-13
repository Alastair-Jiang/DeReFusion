"""Independent arithmetic/coverage consistency check of a completed matrix; no refitting."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIVATE=ROOT/'data/shrink-cdd-20261013-v1'
RESULT=HERE/'CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json'
AUDIT=HERE/'CDD_INTERNAL_CONSISTENCY_AUDIT_V1_2.json'
REPORT=ROOT/'docs/DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def close(a,b,rtol=1e-10):
    if not math.isclose(float(a),float(b),rel_tol=rtol,abs_tol=1e-9):
        raise ValueError('Arithmetic mismatch')
def main():
    if AUDIT.exists() or REPORT.exists(): raise ValueError('Completed audit/report already exists')
    result=json.loads(RESULT.read_text(encoding='utf-8'))
    p=json.loads((HERE/'SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json').read_text(encoding='utf-8'))
    prep=json.loads((HERE/'CDD_PREPARATION_MANIFEST_V1_1.json').read_text(encoding='utf-8'))
    freeze_path=HERE/'CDD_VALIDATION_ROSTER_FREEZE_V1_1.json'
    freeze=json.loads(freeze_path.read_text(encoding='utf-8'))
    frozen_time=datetime.fromisoformat(freeze['frozen_at_utc']).timestamp()
    if result['completed_F_fits']!=24 or len(result['runs'])!=24 or result['total_optimizer_steps']!=14400:
        raise ValueError('Run count/step mismatch')
    expected={(a,f,s) for a in p['assets'] for f in p['line_A']['fractions'] for s in p['model']['seeds']}
    if {(r['asset'],r['fraction'],r['seed']) for r in result['runs']}!=expected: raise ValueError('Missing/duplicate combination')
    raw={}
    for asset in p['assets']:
        path=PRIVATE/(asset+'.raw.csv')
        if sha(path)!=p['raw_sha256'][asset]: raise ValueError('Raw pin drift')
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        if lines[0].startswith('http'): lines=lines[1:]
        rows=[]
        for r in csv.DictReader(lines):
            d=datetime.fromtimestamp(float(r['unix']),timezone.utc).date().isoformat()
            if '2018-01-01'<=d<'2026-01-01': rows.append((d,*[float(r[k]) for k in ['open','high','low','close']]))
        rows.sort(); dates=[r[0] for r in rows]; values=np.array([r[1:] for r in rows],dtype=np.float64)
        raw[asset]=(dates,values)
    conditions={(r['asset'],r['fraction']):r for r in prep['combinations']}
    for (asset,fraction),c in conditions.items():
        dates,values=raw[asset]
        train=[i for i,d in enumerate(dates) if i>=96 and d<'2023-01-01']
        selected=train[-math.ceil(fraction*len(train)):]
        start,end=selected[0]-96,selected[-1]+1
        fitted_mean=values[start:end].mean(0); fitted_std=values[start:end].std(0)
        prefix=[values[i,3] for i,d in enumerate(dates) if d<'2023-01-01']
        denominator=math.fsum((float(b)-float(a))**2 for a,b in zip(prefix[:-1],prefix[1:]))/(len(prefix)-1)
        close(denominator,c['rmsse_denominator'])
        index_by_date={d:i for i,d in enumerate(dates)}
        for role,info in c['packages'].items():
            path=Path(info['path'])
            if sha(path)!=info['sha256']: raise ValueError('Prepared package pin drift')
            with np.load(path,allow_pickle=False) as z:
                keys=z['keys'].tolist(); x=z['x']; y=z['y']
                if len(keys)!=info['count'] or sha_text(keys)!=info['keys_sha256']: raise ValueError('Expected package keys mismatch')
                if role=='train': ix=selected
                elif role=='validation': ix=[i for i,d in enumerate(dates) if '2023-01-01'<=d<'2024-01-01']
                else: ix=[i for i,d in enumerate(dates) if '2024-01-01'<=d<'2026-01-01']
                expected_keys=[f'CDD-BITSTAMP|{asset}|{dates[i]}T00:00:00Z|h1-close' for i in ix]
                if keys!=expected_keys: raise ValueError('Split/key mismatch against raw dates')
                close(float(z['close_output_std']),float(fitted_std[3]))
                close(float(z['rmsse_denominator']),denominator)
                # Reconstruct every target and three independent context positions directly from raw inputs.
                np.testing.assert_array_equal(y,((values[ix]-fitted_mean)/fitted_std).astype(np.float32))
                for k in sorted({0,len(keys)//2,len(keys)-1}):
                    i=index_by_date[keys[k].split('|')[2][:10]]
                    np.testing.assert_array_equal(x[k],((values[i-96:i]-fitted_mean)/fitted_std).astype(np.float32))
    for r in result['runs']:
        fit=r['fit']; c=conditions[(r['asset'],r['fraction'])]
        if fit['steps']!=600 or fit['parameters']!=21743 or fit['validation_keys']!=365 or fit['test_path_received']:
            raise ValueError('Fit contract mismatch')
        if fit['train_package_sha256']!=c['packages']['train']['sha256'] or fit['validation_package_sha256']!=c['packages']['validation']['sha256']:
            raise ValueError('Fit input digest mismatch')
        if [h['step'] for h in fit['history']]!=list(range(50,601,50)): raise ValueError('Validation cadence mismatch')
        best=min(fit['history'],key=lambda h:h['validation_normalized_mse'])
        if best['step']!=fit['best_step']: raise ValueError('Checkpoint minimum/tie rule mismatch')
        checkpoint=Path(r['checkpoint']); predictions=checkpoint.with_name('evaluation.predictions.csv')
        if checkpoint.stat().st_mtime>frozen_time or predictions.stat().st_mtime<frozen_time:
            raise ValueError('Fit/roster/evaluation timestamp order inconsistent')
        with predictions.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
        keys=[x['key'] for x in rows]
        if len(keys)!=731 or len(set(keys))!=731 or sha_text(keys)!=c['packages']['test']['keys_sha256']:
            raise ValueError('Prediction key coverage mismatch')
        with np.load(c['packages']['test']['path'],allow_pickle=False) as z:
            np.testing.assert_array_equal(np.array([float(np.float32(x['target_normalized_close'])) for x in rows]),z['y'][:,3].astype(np.float64))
            np.testing.assert_array_equal(np.array([float(x['P_normalized_close']) for x in rows]),z['x'][:,-1,3].astype(np.float64))
        if sha(checkpoint)!=r['evaluation']['checkpoint_sha256']: raise ValueError('Checkpoint identity mismatch')
        for period,metrics in r['evaluation']['metrics'].items():
            selected=rows if period=='all' else [x for x in rows if '|'+period+'-' in x['key']]
            if len(selected)!=metrics['key_count']: raise ValueError('Period key-count mismatch')
            for arm in ['F','L','P']:
                errors=[(float(x[arm+'_normalized_close'])-float(np.float32(x['target_normalized_close'])))**2*c['close_output_std']**2 for x in selected]
                mse=math.fsum(errors)/len(errors)
                close(mse,metrics['mse'][arm]); close(math.sqrt(mse/c['rmsse_denominator']),metrics['rmsse'][arm])
            close(metrics['mse']['L']-metrics['mse']['F'],metrics['mse_L_minus_F'])
    rank=[]
    for a in p['assets']:
        vals=[r['fit']['validation_rmsse']['F'] for r in result['runs'] if r['asset']==a and r['fraction']==1]
        rank.append({'asset':a,'mean_validation_rmsse_F':math.fsum(vals)/3})
    rank.sort(key=lambda x:(x['mean_validation_rmsse_F'],x['asset']))
    if [r['asset'] for r in rank]!=[r['asset'] for r in freeze['ranking']]: raise ValueError('Frozen roster mismatch')
    for roster in result['line_B_rosters']:
        members=[r['asset'] for r in rank[:roster['size']]]
        if roster['assets']!=members: raise ValueError('Roster composition mismatch')
        scores=[]
        for asset in members:
            values=[r['evaluation']['metrics'][roster['period']]['rmsse']['F'] for r in result['runs'] if r['asset']==asset and r['fraction']==1]
            scores.append(math.fsum(values)/3)
        close(math.fsum(scores)/len(scores),roster['equal_asset_mean_RMSSE_F'])
        ordered=sorted(scores); n=len(ordered)
        median=ordered[n//2] if n%2 else (ordered[n//2-1]+ordered[n//2])/2
        close(median,roster['median_asset_RMSSE_F'])
    audit={'result':'PASS','type':'Codex internal consistency check; independent DSH review pending',
           'timestamp_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),
           'results_sha256':sha(RESULT),'checked_F_fits':24,'independently_reviewed_F_fits':0,
           'checks':['Raw/source/fit package digest binding','Split dates, all normalized targets, first/middle/last contexts from raw inputs',
                     'Training-only scaler and fixed full-train RMSSE denominator','600 steps, 12 validations, earliest minimum checkpoint',
                     'All 731 keys and yearly subsets; standard-library fsum metrics from stored predictions',
                     'Validation-only ranking, roster mean/median arithmetic and checkpoint-before-freeze/predictions-after-freeze timestamp order'],
           'csv_target_codec':'Evaluator wrote NumPy float32 shortest-roundtrip targets; auditor v1.2 decodes target text to float32 before float64 arithmetic. Initial v1.1 treated decimal target text directly as float64 and raised an exact-equality failure (maximum normalized difference 2.35656739e-7); fits, packages, checkpoints, predictions and stored metrics unchanged.',
           'publication':'Internal report only; no public raw/weights/predictions release'}
    AUDIT.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    lines=['# CDD shrink exploration — completed first batch','',
           '2026-10-13; new CDD Bitstamp BTC/USD and ETH/USD data. Protocol `DRF-SHRINK-CDD-EXPLORATORY-20261013-V0.2`.',
           'Checkout `C:/Users/26843/Documents/ChatGPT/redefusion`; HEAD `a74126c11d857da8514074b72282adc8d47f28a7`.',
           '', '24/24 DeReFusion fits completed; 14,400 actual optimizer steps. Eight history conditions, three seeds per condition; all 731 test keys evaluated. Internal arithmetic/coverage checks: 24/24 PASS. Independent DSH scientific/source review: pending.',
           '', '## Line A — history reduction','',
           'Full 2024–2025 test RMSSE below. F is seed-mean DeReFusion; L is deterministic validation-selected ridge; P is persistence. Lower is better. The denominator is fixed per asset across fractions. This is exploratory test description, not a new confirmation or a rule for silently selecting future data.',
           '', '| Asset | History-target fraction | Train targets | F mean RMSSE | F seed range | L RMSSE | P RMSSE |',
           '|---|---:|---:|---:|---:|---:|---:|']
    summary=[]
    for a in p['assets']:
        for fraction in p['line_A']['fractions']:
            rr=[r for r in result['runs'] if r['asset']==a and r['fraction']==fraction]
            f=[r['evaluation']['metrics']['all']['rmsse']['F'] for r in rr]
            l=rr[0]['evaluation']['metrics']['all']['rmsse']['L']; persistence=rr[0]['evaluation']['metrics']['all']['rmsse']['P']
            item={'asset':a,'fraction':fraction,'F_mean_RMSSE':math.fsum(f)/3,'F_min':min(f),'F_max':max(f),'L_RMSSE':l,'P_RMSSE':persistence}
            summary.append(item)
            lines.append(f'| {a} | {fraction:.0%} | {conditions[(a,fraction)]["train_target_count"]} | {item["F_mean_RMSSE"]:.4f} | {min(f):.4f}–{max(f):.4f} | {l:.4f} | {persistence:.4f} |')
    lines += ['', '## Line B — validation-frozen asset screen','',
              'Ranking: '+ ' → '.join(r['asset'] for r in rank)+'. Ranking uses full-history mean validation RMSSE(F) across three seeds and was frozen before test evaluation.',
              '', '| Roster | Test period | Equal-asset mean RMSSE(F) |', '|---|---|---:|']
    for r in result['line_B_rosters']:
        lines.append(f'| {",".join(r["assets"])} | {r["period"]} | {r["equal_asset_mean_RMSSE_F"]:.4f} |')
    lines += ['', 'Roster-size differences describe composition: each asset is trained independently, so dropping an asset changes no retained asset model.',
              '', '## Interpretation and records','',
              'This first batch covers two crypto assets on a common 24/7 daily grid. It supplies no GSPC/N225 evidence. The new source and 600-step schedule also prevent attributing differences from old Yahoo experiment reports to shrinkage alone. All fractions retain 96 preceding context candles; raw spans differ from target-count fractions. The 600-step cap is not a convergence guarantee. Historical test exposure, seed repeats and two calendar years prevent confirmatory or market-level inference. F−L does not isolate the nonlinear mechanism.',
              '', 'Complete per-seed/year MSE, RMSSE, difference, keys, validation histories and hashes: `CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json`. Raw/predictions/checkpoints remain under the already gitignored data root. Internal use basis is in `DRF_CDD_PROJECT_STARTUP_DECISION_2026-10-13.md`; no raw/weight/prediction publication or commercial use is granted.',
              '', 'Results SHA-256: `'+sha(RESULT)+'`.', 'Internal check SHA-256: `'+sha(AUDIT)+'`.']
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    progress_path=HERE/'PROGRESS_2026-10-13.json'
    progress=json.loads(progress_path.read_text(encoding='utf-8'))
    progress['status']='FIRST_CDD_TWO_ASSET_EXPLORATORY_BATCH_COMPLETE_INTERNAL_CHECKS_PASS_INDEPENDENT_REVIEW_PENDING'
    progress['active_counts']={'planned_F_fits':24,'completed_F_fits':24,'internally_checked_F_fits':24,'independently_reviewed_F_fits':0,'unique_history_conditions':8,'qualified_assets':2}
    progress['last_updated_local']=datetime.now().astimezone().isoformat()
    for track in progress['tracks'].values(): track['state']='FIRST_TWO_ASSET_BATCH_COMPLETE_INTERNAL_CHECKS_PASS'; track['run_authorized']=True
    progress['tracks']['history_window_reduction']['shared_test_prediction_keys']='731 complete daily keys per asset, identical across fractions and seeds; manifests bound'
    progress['tracks']['history_window_reduction']['primary_compute_control']='600 optimizer steps per fit; complete validation every 50; checkpoint by strict minimum; no early stopping'
    for gate in progress['gates']:
        if gate['id']=='G3': gate['state']='COMPLETE_INTERNAL_CHECKS_PASS'; gate['evidence']='24 fits/14400 steps; exact shared key coverage and metric checks PASS; independent DSH review pending'
    for key,path in [('cdd_results',RESULT),('cdd_internal_audit',AUDIT),('cdd_result_report',REPORT),('cdd_roster_freeze',freeze_path)]:
        progress['candidate_artifacts'][key]=str(path.relative_to(ROOT)).replace('\\','/')
        progress['candidate_artifacts'][key+'_sha256']=sha(path)
    progress['latest_actions'].append('Completed the first two-asset real-data exploration on the new CDD source; internally checked all 24 fits, 14400 steps, shared keys, metrics and frozen roster. Independent review pending; no public data/model/prediction release.')
    progress_path.write_text(json.dumps(progress,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'PASS','checked_F_fits':24,'independent_review':'pending','summary':summary,'report':str(REPORT)}))
def sha_text(keys): return hashlib.sha256('\n'.join(keys).encode()).hexdigest()
if __name__=='__main__': main()

