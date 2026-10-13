"""One locked retrospective temporal extrapolation; no fitting or selection."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'): os.environ[name]='2'
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from types import SimpleNamespace
import numpy as np
import torch

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from models.derefusion.bundle_v3_pin.loader import load_model_class,verify_archive
PRIVATE=ROOT/'data/raw48-oos-20261013-v1'
OLD=ROOT/'research_work/project_management_2026_10_10/compression_diagnostic_2026_10_13_v2'
OLD_PRIVATE=ROOT/'data/cdd-compression-diagnostic-20261013-v2'
RAW=ROOT/'data/shrink-cdd-20261013-v1/ETHUSD.raw.csv'

def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def dump(p,o):
    p=Path(p).resolve()
    if not (p.is_relative_to(HERE) or p.is_relative_to(PRIVATE)) or p.exists(): raise ValueError('Boundary/overwrite')
    b=(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    write(p,b)
def write(p,b):
    p=Path(p).resolve()
    if p.exists() or not (p.is_relative_to(HERE) or p.is_relative_to(PRIVATE)): raise ValueError('Boundary/overwrite')
    if p.is_relative_to(PRIVATE) and sum(q.stat().st_size for q in PRIVATE.rglob('*') if q.is_file())+len(b)>33554432: raise ValueError('Output cap')
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def statehash(state):
    h=hashlib.sha256()
    for k,v in sorted(state.items()): h.update(k.encode());h.update(v.numpy().tobytes())
    return h.hexdigest()
def check(released=False):
    p=load(HERE/'PROTOCOL_V1.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==p['head']
    assert platform.python_version()=='3.11.15' and torch.__version__=='2.5.1+cpu' and np.__version__=='2.1.2'
    assert all(sha(ROOT/k)==v for k,v in p['input_sha256'].items())
    verify_archive();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    if released:
        r=load(HERE/'EXECUTION_RELEASE_V1.json')
        assert r['decision']=='APPROVED' and r['protocol_sha256']==sha(HERE/'PROTOCOL_V1.json')
        assert all(sha(HERE/k)==v for k,v in r['gates'].items())
    return p
def model(state):
    cfg=dict(load(OLD/'PROTOCOL_V1.json')['model_configuration'],seq_len=48)
    m=load_model_class()(SimpleNamespace(**cfg)).float();m.load_state_dict(state);m.eval();return m
def infer(state,x):
    m=model(state);out=[]
    with torch.no_grad():
        for i in range(0,len(x),64):out.append(m(torch.from_numpy(x[i:i+64]),None,None,None)[:,0,3].double().numpy())
    out=np.concatenate(out);assert out.shape==(len(x),) and np.isfinite(out).all();return out

def preflight():
    p=check();checks=[]
    with np.load(OLD_PRIVATE/'packages/raw48/validation.npz',allow_pickle=False) as z:x=z['x'].copy();keys=z['keys'].tolist()
    for item in p['F_models']:
        state=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True)
        assert statehash(state)==item['state_tensor_sha256']
        out=infer(state,x)
        with np.load(OLD_PRIVATE/f"runs/raw48_s{item['seed']}/1800_predictions.npz",allow_pickle=False) as z:
            assert z['keys'].tolist()==keys and np.array_equal(out,z['F_best'])
        probe=np.repeat(x[:1],65,axis=0);assert len(infer(state,probe))==65
        checks.append(dict(seed=item['seed'],restored_validation_keys=len(keys),state_hash=item['state_tensor_sha256']))
    assert len(checks)==3
    dump(HERE/'PREFLIGHT_V1.json',dict(result='PASS',checks=checks,protocol_sha256=sha(HERE/'PROTOCOL_V1.json'),scope='Frozen raw48 validation recovery and 65-key tail; no 2026 OHLC parsing'))

def release():
    check();review=load(HERE/'ENGINEERING_REVIEW_V1.json')
    assert review['result']=='PASS' and review['code_sha256']==sha(Path(__file__)) and review['protocol_sha256']==sha(HERE/'PROTOCOL_V1.json')
    assert load(HERE/'PREFLIGHT_V1.json')['result']=='PASS'
    dump(HERE/'EXECUTION_RELEASE_V1.json',dict(decision='APPROVED',protocol_sha256=sha(HERE/'PROTOCOL_V1.json'),gates={f:sha(HERE/f) for f in ['PREFLIGHT_V1.json','ENGINEERING_REVIEW_V1.json','EXPOSURE_REGISTER_V1.md']},decision_owner='Codex project delegate',authorization_basis='Standing project delegation and latest instruction to proceed with high-quality-model next step',scope='Existing ETH snapshot: training-scaler reconstruction, 2026 daily OHLC quality checks and one fixed raw48 F/L/P evaluation; zero fits, no candidate revision',timestamp_utc=utc()))

def collect():
    """Only parse prices in immutable scaler/context/evaluation intervals."""
    rows=RAW.read_text(encoding='utf-8-sig').splitlines();rows=rows[1:] if rows[0].startswith('http') else rows
    records={}
    for row in csv.DictReader(rows):
        ts=float(row['unix']);ts=ts/1000 if ts>=1e12 else ts;dt=datetime.fromtimestamp(ts,timezone.utc);d=dt.date().isoformat()
        if not ('2018-01-01'<=d<'2023-01-01' or '2025-11-14'<=d<'2026-10-13'):continue
        assert not (dt.hour or dt.minute or dt.second or dt.microsecond) and row['date'][:10]==d
        assert row['symbol'].replace('/','')=='ETHUSD' and d not in records
        v=np.array([float(row[c]) for c in ['open','high','low','close']],dtype=np.float64)
        assert np.isfinite(v).all() and (v>0).all() and v[1]>=max(v[0],v[2],v[3]) and v[2]<=min(v[0],v[1],v[3])
        records[d]=v
    return records
def dates(start,stop):
    d,e=date.fromisoformat(start),date.fromisoformat(stop);out=[]
    while d<e:out.append(d.isoformat());d+=timedelta(days=1)
    return out

def evaluate():
    p=check(True);records=collect()
    td=dates('2018-01-01','2023-01-01');train=np.stack([records[d] for d in td]);mean=train.mean(0);std=train.std(0)
    assert (std>0).all();scale=float(np.mean(np.diff(train[:,3])**2))
    normalized=(train-mean)/std;targets=dates('2018-04-07','2023-01-01');indices=[td.index(d) for d in targets]
    # Authenticate reconstruction against every historical training sample.
    xt=np.stack([normalized[i-48:i] for i in indices]).astype(np.float32);yt=normalized[indices].astype(np.float32)
    with np.load(OLD_PRIVATE/'packages/raw48/train.npz',allow_pickle=False) as z:
        assert np.array_equal(xt,z['x']) and np.array_equal(yt,z['y']) and float(z['close_output_std'])==std[3] and float(z['rmsse_denominator'])==scale
    dd=dates('2025-11-14','2026-10-13');raw=np.stack([records[d] for d in dd]);normalized=(raw-mean)/std
    evaldates=dates(p['evaluation_start'],p['evaluation_stop']);ix=[dd.index(d) for d in evaldates]
    x=np.stack([normalized[i-48:i] for i in ix]).astype(np.float32);y=raw[ix,3].copy();last=raw[np.array(ix)-1,3].copy()
    keys=[f'CDD-BITSTAMP|ETHUSD|{d}T00:00:00Z|h1-close' for d in evaldates]
    assert keys==p['expected_keys'] and len(keys)==285 and np.isfinite(x).all()
    predictions={'P':last}
    for item in p['F_models']:
        state=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True);assert statehash(state)==item['state_tensor_sha256']
        predictions[f"F_s{item['seed']}"]=infer(state,x)*std[3]+mean[3]
    with np.load(ROOT/p['L_file'],allow_pickle=False) as z:
        pred=(x.reshape(len(x),-1).astype(np.float64)-z['x_mean'])@z['legacy_coef']+float(z['y_mean'])
    predictions['L']=pred*std[3]+mean[3]
    assert all(np.isfinite(v).all() for v in predictions.values())
    b=io.BytesIO();np.savez(b,x=x,target_raw_close=y,keys=np.array(keys),scaler_mean=mean,scaler_std=std,rmsse_denominator=np.array(scale),**predictions);write(PRIVATE/'evaluation_payload.npz',b.getvalue())
    result={}
    for period,start,stop in [('all',p['evaluation_start'],p['evaluation_stop']),('first','2026-01-01','2026-07-01'),('second','2026-07-01','2026-10-13')]:
        ids=[i for i,d in enumerate(evaldates) if start<=d<stop];scores={}
        for name,pred in predictions.items():
            errors=[float(pred[i])-float(y[i]) for i in ids];mse=math.fsum(e*e for e in errors)/len(errors)
            scores[name]=dict(MSE=mse,MAE=math.fsum(abs(e) for e in errors)/len(errors),RMSSE=math.sqrt(mse/scale))
        avg=math.fsum(scores[f'F_s{s}']['MSE'] for s in (17,29,43))/3
        result[period]=dict(keys=len(ids),scores=scores,mean_seed_F_MSE=avg,F_minus_L_MSE=avg-scores['L']['MSE'],F_over_L_MSE=avg/scores['L']['MSE'],F_minus_P_MSE=avg-scores['P']['MSE'],F_over_P_MSE=avg/scores['P']['MSE'])
    dump(HERE/'RESULTS_V1.json',dict(protocol_id=p['protocol_id'],head=p['head'],protocol_sha256=sha(HERE/'PROTOCOL_V1.json'),release_sha256=sha(HERE/'EXECUTION_RELEASE_V1.json'),payload_sha256=sha(PRIVATE/'evaluation_payload.npz'),evaluated_keys=len(keys),keys_sha256=hashlib.sha256('\n'.join(keys).encode()).hexdigest(),metrics=result,new_F_fits=0,new_L_fits=0,original_2024_2025_test_packages_read=False,finished_at_utc=utc(),interpretation='One newly locked retrospective 2026 temporal evaluation; exposure supported in this lineage, not certified globally unexposed, no formal confirmation'))
    print(json.dumps(result,ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['preflight','release','evaluate']);a=ap.parse_args()
    {'preflight':preflight,'release':release,'evaluate':evaluate}[a.phase]()
if __name__=='__main__':
    try:main()
    except Exception as e:
        dump(HERE/('FAILURE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),dict(reason=str(e),type=type(e).__name__,timestamp_utc=utc()));raise
