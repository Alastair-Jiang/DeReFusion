"""Independent implementation of locked forecast/target recovery; zero fitting."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[name]='2'
from pathlib import Path
from datetime import datetime,timezone,timedelta
import csv
import hashlib
import json
import math
import sys
from types import SimpleNamespace
import numpy as np
import torch

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from models.derefusion.bundle_v3_pin.loader import load_model_class
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10),(a,b)
def dump(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
P=load(HERE/'PROTOCOL_V1.json');R=load(HERE/'RESULTS_V1.json');PRIVATE=ROOT/'data/raw48-oos-20261013-v1'
assert R['protocol_sha256']==sha(HERE/'PROTOCOL_V1.json') and R['release_sha256']==sha(HERE/'EXECUTION_RELEASE_V1.json')
assert R['payload_sha256']==sha(PRIVATE/'evaluation_payload.npz')
assert R['new_F_fits']==R['new_L_fits']==0 and not R['original_2024_2025_test_packages_read']
with np.load(PRIVATE/'evaluation_payload.npz',allow_pickle=False) as z:
    values={k:z[k].copy() for k in z.files}
keys=values['keys'].tolist();assert keys==P['expected_keys'] and len(keys)==285
lines=(ROOT/'data/shrink-cdd-20261013-v1/ETHUSD.raw.csv').read_text(encoding='utf-8-sig').splitlines()
if lines[0].startswith('http'):lines=lines[1:]
raw={};checks=0
for row in csv.DictReader(lines):
    timestamp=float(row['unix']);timestamp=timestamp/1000 if timestamp>=1e12 else timestamp
    dt=datetime.fromtimestamp(timestamp,timezone.utc);d=dt.date().isoformat()
    if not ('2018-01-01'<=d<'2023-01-01' or '2025-11-14'<=d<'2026-10-13'):continue
    assert row['date'][:10]==d and row['symbol'].replace('/','')=='ETHUSD' and d not in raw
    v=np.array([float(row[k]) for k in ('open','high','low','close')],dtype=np.float64)
    assert np.isfinite(v).all() and (v>0).all() and v[1]>=v.max() and v[2]<=v.min()
    assert dt.hour==dt.minute==dt.second==dt.microsecond==0
    raw[d]=v;checks+=1
train=np.stack([raw[d] for d in sorted(raw) if d<'2023-01-01'])
assert len(train)==1826 and np.array_equal(train.mean(0),values['scaler_mean']) and np.array_equal(train.std(0),values['scaler_std'])
close(float(np.mean(np.diff(train[:,3])**2)),float(values['rmsse_denominator']))
days=[key.split('|')[2][:10] for key in keys];x=values['x'];target=values['target_raw_close']
for i,d in enumerate(days):
    when=datetime.fromisoformat(d)
    context=np.stack([raw[(when-timedelta(days=j)).date().isoformat()] for j in range(48,0,-1)])
    oracle=((context-values['scaler_mean'])/values['scaler_std']).astype(np.float32)
    assert np.array_equal(oracle,x[i]) and target[i]==raw[d][3]
    assert values['P'][i]==context[-1,3]
assert values['x'].shape==(285,48,4) and all(np.isfinite(v).all() for k,v in values.items() if k!='keys')
torch.set_num_threads(2);torch.use_deterministic_algorithms(True);restored=[]
old=ROOT/'research_work/project_management_2026_10_10/compression_diagnostic_2026_10_13_v2'
for item in P['F_models']:
    state=torch.load(ROOT/item['path'],map_location='cpu',weights_only=True)
    h=hashlib.sha256()
    for name,tensor in sorted(state.items()):h.update(name.encode());h.update(tensor.numpy().tobytes())
    assert h.hexdigest()==item['state_tensor_sha256']
    cfg=dict(load(old/'PROTOCOL_V1.json')['model_configuration'],seq_len=48)
    m=load_model_class()(SimpleNamespace(**cfg)).float();m.load_state_dict(state);m.eval();out=[]
    with torch.no_grad():
        for i in range(0,285,64):out.append(m(torch.from_numpy(x[i:i+64]),None,None,None)[:,0,3].double().numpy())
    pred=np.concatenate(out)*values['scaler_std'][3]+values['scaler_mean'][3]
    assert np.array_equal(pred,values[f"F_s{item['seed']}"])
    restored.append(dict(seed=item['seed'],keys=285,result='PASS'))
with np.load(ROOT/P['L_file'],allow_pickle=False) as z:
    pred=(x.reshape(285,-1).astype(np.float64)-z['x_mean'])@z['legacy_coef']+float(z['y_mean'])
assert np.array_equal(pred*values['scaler_std'][3]+values['scaler_mean'][3],values['L'])
for period,start,stop in [('all','2026-01-01','2026-10-13'),('first','2026-01-01','2026-07-01'),('second','2026-07-01','2026-10-13')]:
    ids=[i for i,d in enumerate(days) if start<=d<stop];record=R['metrics'][period];assert record['keys']==len(ids)
    for name in ('F_s17','F_s29','F_s43','L','P'):
        err=values[name][ids]-target[ids];mse=float(np.mean(err**2));mae=float(np.mean(np.abs(err)))
        close(record['scores'][name]['MSE'],mse);close(record['scores'][name]['MAE'],mae)
        close(record['scores'][name]['RMSSE'],math.sqrt(mse/float(values['rmsse_denominator'])))
    avg=sum(record['scores'][f'F_s{s}']['MSE'] for s in (17,29,43))/3
    close(avg,record['mean_seed_F_MSE']);close(avg-record['scores']['L']['MSE'],record['F_minus_L_MSE']);close(avg/record['scores']['L']['MSE'],record['F_over_L_MSE'])
    close(avg-record['scores']['P']['MSE'],record['F_minus_P_MSE']);close(avg/record['scores']['P']['MSE'],record['F_over_P_MSE'])
dump(HERE/'INTERNAL_AUDIT_V1.json',dict(result='PASS',scope='Separate implementation by responsible agent, not external independent array acceptance',code_sha256=sha(Path(__file__)),results_sha256=sha(HERE/'RESULTS_V1.json'),payload_sha256=sha(PRIVATE/'evaluation_payload.npz'),restored_F_models=3,restored_F_prediction_values=855,source_rows_checked=checks,input_windows_reconstructed=285,subperiod_keys=[181,104],new_fits=0,checks=restored,zero_2024_2025_role_packages=True))
table='\n'.join(f"| {label} | {r['keys']} | {r['mean_seed_F_MSE']:.3f} | {r['scores']['L']['MSE']:.3f} | {r['scores']['P']['MSE']:.3f} | {r['F_over_L_MSE']:.4f} | {r['F_over_P_MSE']:.4f} |" for label,r in R['metrics'].items())
seedtable='\n'.join(f"| {s} | {R['metrics']['all']['scores'][f'F_s{s}']['MSE']:.3f} |" for s in (17,29,43))
text=f'''# 锁定raw48的2026时间外推结果

主仓库HEAD `{P['head']}`；协议 `{P['protocol_id']}`。仅一次历史时间外推，285天，0次F/线性拟合。三个已有2023验证选中的模型、固定ridge与持久性，事先冻结后才解析2026 OHLC。不是未来实时前瞻或正式确认。

| 区间 | 键数 | 三seed平均F MSE | L MSE | P MSE | F/L | F/P |
|---|---:|---:|---:|---:|---:|---:|
{table}

| seed | 全期F MSE |
|---|---:|
{seedtable}

MSE为原USD价格平方损失。主量是mean_seed_F_MSE−L_MSE，不是平均预测ensemble；三个seed和两个子段不增加独立市场样本数。此表只描述一个已选择资产/模型在该历史时间段上的表现，数值接受/非劣/功效条件仍TBD。

三个模型855个预测值精确恢复；所有285输入窗口、源真值与P逐项核对，训练scaler恢复与旧训练数组及原2018–2022统计一致。全期及181/104子段损失复算PASS。原2024/25角色包未打开，但允许2025年末源历史作为2026因果输入上下文。

原CDD管线有明确2026价格过滤；其他代理暴露未知。2026数据完整字节早已下载，因此这是新锁定的历史评估，不宣称全局未暴露。原论文保真待DSH核验，既有R1未修改。

科学处置见DECISION_V1.md。私有输入与逐键预测保留data/，不发布。
'''
with (HERE/'RESULT_REPORT_V1.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print(json.dumps(dict(audit='PASS',models=3,keys=285,metrics=R['metrics']),ensure_ascii=False))
