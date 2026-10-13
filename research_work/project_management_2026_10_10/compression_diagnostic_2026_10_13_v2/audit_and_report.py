"""Read-only recovery of new completed validation predictions; no fitting/test access."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'): os.environ[name]='2'
from pathlib import Path
import hashlib
import json
import math
import sys
import csv
from types import SimpleNamespace
import numpy as np
import torch

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from models.derefusion.bundle_v3_pin.loader import load_model_class
P=json.loads((HERE/'PROTOCOL_V1.json').read_text(encoding='utf-8-sig'))
R=json.loads((HERE/'RESULTS_V1.json').read_text(encoding='utf-8-sig'))
PREP=json.loads((HERE/'PREPARATION_V1.json').read_text(encoding='utf-8-sig'))
PRIVATE=ROOT/'data/cdd-compression-diagnostic-20261013-v2'
torch.set_num_threads(2); torch.use_deterministic_algorithms(True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def hash_state(state):
    h=hashlib.sha256()
    for name,value in sorted(state.items()): h.update(name.encode()); h.update(value.numpy().tobytes())
    return h.hexdigest()
def write_new(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f: f.write(text)
def dump(path,obj): write_new(path,json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def close(a,b): assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10),(a,b)
def mse(pred,y,sd): return math.fsum((float(v)-float(t))**2 for v,t in zip(pred,y))/len(y)*sd**2
def read_role(arm,role):
    row=PREP['arms'][arm][role]; path=ROOT/row['path']; assert sha(path)==row['sha256']
    assert sha(path.with_suffix('.keys.json'))==row['manifest_sha256']
    meta=json.loads(path.with_suffix('.keys.json').read_text())
    with np.load(path,allow_pickle=False) as z:
        x,y,keys=z['x'].copy(),z['y'].copy(),z['keys'].tolist(); sd=float(z['close_output_std']); scale=float(z['rmsse_denominator'])
        assert str(z['role'].item())==role and keys==meta['expected_keys']
    return x,y,keys,sd,scale
def recover(state,arm,x):
    cfg=dict(P['model_configuration'],seq_len=96 if arm=='raw96' else 48)
    m=load_model_class()(SimpleNamespace(**cfg)).float(); m.load_state_dict(state); m.eval(); pieces=[]
    with torch.no_grad():
        for i in range(0,len(x),64): pieces.append(m(torch.from_numpy(x[i:i+64]),None,None,None)[:,0,3].double().numpy())
    output=np.concatenate(pieces)
    assert output.shape==(len(x),) and np.isfinite(output).all()
    return output

assert R['protocol_sha256']==sha(HERE/'PROTOCOL_V1.json') and R['release_sha256']==sha(HERE/'EXECUTION_RELEASE_V1.json')
assert len(R['runs'])==9 and R['total_optimizer_steps']==16200 and not R['test_read']
assert len(R['baselines'])==3 and R['ridge_candidate_solutions']==30
assert len({(v['arm'],v['seed']) for v in R['runs']})==9
roles={}; base={}; pins={}; audit=[]; rows=[]
for arm in ('raw96','raw48','mixed48'):
    roles[arm]={role:read_role(arm,role) for role in ('train','validation')}
    x,y,keys,sd,scale=roles[arm]['validation']
    rb=next(r for r in R['baselines'] if r['arm']==arm)
    out=PRIVATE/'ridge'/arm; pins[(out/'fit.json').relative_to(ROOT).as_posix()]=sha(out/'fit.json')
    with np.load(out/'predictions_and_coefficients.npz',allow_pickle=False) as z:
        assert z['keys'].tolist()==keys
        for label,coef in [('L_legacy','legacy_coef'),('L_wide','wide_coef')]:
            recovered=(x.reshape(len(x),-1).astype(np.float64)-z['x_mean'])@z[coef]+float(z['y_mean'])
            assert np.array_equal(recovered,z[label])
            close(mse(recovered,y[:,3],sd),rb[label]['MSE'])
        assert np.array_equal(z['P'],x[:,-1,3].astype(np.float64))
        close(mse(z['P'],y[:,3],sd),rb['P_MSE'])
    assert rb['L_wide']==min(rb['candidates'],key=lambda z:z['validation_normalized_MSE'])
    assert rb['L_legacy']==min([z for z in rb['candidates'] if z['lambda_value'] in P['ridge_legacy_lambdas']],key=lambda z:z['validation_normalized_MSE'])
    base[arm]=rb
    pins[(out/'predictions_and_coefficients.npz').relative_to(ROOT).as_posix()]=sha(out/'predictions_and_coefficients.npz')

raw=roles['raw96']
for role in ('train','validation'):
    x,y,k,sd,scale=raw[role]; a,b=roles['raw48'][role],roles['mixed48'][role]
    assert np.array_equal(a[0],x[:,-48:])
    oracle=np.empty_like(b[0])
    for j in range(16):
        block=x[:,j*4:j*4+4]
        oracle[:,j,0]=block[:,0,0]; oracle[:,j,1]=block[:,:,1].max(1); oracle[:,j,2]=block[:,:,2].min(1); oracle[:,j,3]=block[:,-1,3]
    oracle[:,16:]=x[:,64:]; assert np.array_equal(oracle,b[0])
    for other in (a,b): assert np.array_equal(y,other[1]) and k==other[2] and (sd,scale)==other[3:]

for run in R['runs']:
    arm,seed=run['arm'],run['seed']; out=PRIVATE/'runs'/f'{arm}_s{seed}'
    x,y,keys,sd,scale=roles[arm]['validation']; assert len(keys)==365 and run['train_keys']==1730
    assert [v['step'] for v in run['history']]==list(range(50,1801,50))
    assert run['steps']==1800 and not run['test_read']
    assert [s['budget'] for s in run['snapshots']]==[600,1200,1800]
    assert run['validation_keys_sha256']==hashlib.sha256('\n'.join(keys).encode()).hexdigest()
    for snap in run['snapshots']:
        budget=snap['budget']; h=[v for v in run['history'] if v['step']<=budget]
        selected=min(h,key=lambda v:v['validation_normalized_MSE']); assert selected['step']==snap['best_step']
        full,rem=divmod(budget,55); expected_seen=full*1730+min(rem*32,1730)
        assert snap['samples_seen']==expected_seen
        close(snap['effective_epochs'],expected_seen/1730)
        with np.load(out/f'{budget}_predictions.npz',allow_pickle=False) as z:
            assert z['keys'].tolist()==keys
            for kind,label,score in [('best','F_best','F_MSE'),('terminal','F_terminal','terminal_MSE')]:
                path=out/f'{budget}_{kind}.pt'; state=torch.load(path,map_location='cpu',weights_only=True)
                assert hash_state(state)==snap[f'{kind}_state_tensor_sha256']
                restored=recover(state,arm,x); assert np.array_equal(restored,z[label])
                close(mse(restored,y[:,3],sd),snap[score])
                pins[path.relative_to(ROOT).as_posix()]=sha(path)
        close(selected['validation_normalized_MSE']*sd**2,snap['F_MSE'])
        close(h[-1]['validation_normalized_MSE']*sd**2,snap['terminal_MSE'])
        pins[(out/f'{budget}_predictions.npz').relative_to(ROOT).as_posix()]=sha(out/f'{budget}_predictions.npz')
        b=base[arm]
        rows.append(dict(arm=arm,seed=seed,budget=budget,best_step=snap['best_step'],F_MSE=snap['F_MSE'],F_RMSSE=math.sqrt(snap['F_MSE']/scale),terminal_MSE=snap['terminal_MSE'],F_over_P=snap['F_MSE']/b['P_MSE'],F_over_L_legacy=snap['F_MSE']/b['L_legacy']['MSE'],F_over_L_wide=snap['F_MSE']/b['L_wide']['MSE'],L_legacy_MSE=b['L_legacy']['MSE'],L_wide_MSE=b['L_wide']['MSE'],P_MSE=b['P_MSE'],samples_seen=snap['samples_seen'],effective_epochs=snap['effective_epochs'],neural_elapsed_seconds=snap['neural_elapsed_seconds'],peak_working_set_MiB=snap['peak_working_set_bytes']/1024**2))
    audit.append(dict(arm=arm,seed=seed,recovered_checkpoints=6,keys_per_checkpoint=365,result='PASS'))
    pins[(out/'fit.json').relative_to(ROOT).as_posix()]=sha(out/'fit.json')

for seed in (17,29,43):
    equal=[r['initial_state_tensor_sha256'] for r in R['runs'] if r['seed']==seed and r['arm'] in ('raw48','mixed48')]; assert equal[0]==equal[1]
assert all(base[a]['P_MSE']==base['raw96']['P_MSE'] for a in base)
assert len(rows)==27
means=[]
for budget in (600,1200,1800):
    for arm in ('raw96','raw48','mixed48'):
        rr=[r for r in rows if r['budget']==budget and r['arm']==arm]
        means.append(dict(arm=arm,budget=budget,mean_F_MSE=float(np.mean([r['F_MSE'] for r in rr])),mean_F_RMSSE=float(np.mean([r['F_RMSSE'] for r in rr])),mean_F_over_P=float(np.mean([r['F_over_P'] for r in rr])),mean_seconds=float(np.mean([r['neural_elapsed_seconds'] for r in rr]))))
paired=[]
for budget in (600,1200,1800):
    for seed in (17,29,43):
        group={r['arm']:r for r in rows if r['budget']==budget and r['seed']==seed}
        paired.append(dict(seed=seed,budget=budget,mixed48_over_raw48_MSE=group['mixed48']['F_MSE']/group['raw48']['F_MSE'],raw48_over_raw96_MSE=group['raw48']['F_MSE']/group['raw96']['F_MSE'],mixed48_over_raw96_MSE=group['mixed48']['F_MSE']/group['raw96']['F_MSE']))
with (HERE/'ALL_RESULTS_V1.csv').open('x',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
dump(HERE/'INTERNAL_AUDIT_V1.json',dict(result='PASS',scope='Separate audit implementation, same responsible agent; independent scientific acceptance pending',script_sha256=sha(Path(__file__)),result_sha256=sha(HERE/'RESULTS_V1.json'),checked_F_fits=9,restored_checkpoints=54,checked_prediction_values=54*365,role_arrays='train/validation only',test_read=False,checks=audit,private_artifact_sha256=pins))
dump(HERE/'ANALYSIS_V1.json',dict(means=means,paired=paired,baselines=base,claim='Descriptive exposed-validation development only'))
table='\n'.join(f"| {r['budget']} | {r['arm']} | {r['mean_F_MSE']:.3f} | {r['mean_F_RMSSE']:.6f} | {r['mean_F_over_P']:.4f} | {r['mean_seconds']:.2f} |" for r in means)
basetable='\n'.join(f"| {a} | {base[a]['L_legacy']['lambda_value']:g} | {base[a]['L_legacy']['MSE']:.3f} | {base[a]['L_wide']['lambda_value']:g} | {base[a]['L_wide']['MSE']:.3f} |" for a in ('raw96','raw48','mixed48'))
pairtable='\n'.join(f"| {r['budget']} | {r['seed']} | {r['mixed48_over_raw48_MSE']:.4f} | {r['raw48_over_raw96_MSE']:.4f} | {r['mixed48_over_raw96_MSE']:.4f} |" for r in paired)
write_new(HERE/'RESULT_REPORT_V1.md',f'''# 三表示与训练预算开发诊断结果

主仓库 `{ROOT.as_posix()}`；执行HEAD `{R['head']}`；协议 `{P['protocol_id']}`。已完成9次F拟合/16200步、3个确定性ridge流程/30候选解。内部独立实现恢复检查9/9，54个checkpoint、每个365验证键，精确恢复；这仍不是外部独立科学接受。没有读取或评分测试。

## 完整预算比较

三个seed是优化重复，不是三个独立市场。下表F取各预算内最早最低验证checkpoint，均值是三个seed的描述统计。

| 步数预算 | 表示 | 平均F MSE | 平均F RMSSE | 平均F/P MSE比 | 累计平均秒 |
|---|---|---:|---:|---:|---:|
{table}

P验证MSE三臂相同：{base['raw96']['P_MSE']:.6f}。时间含每50步验证，以及此前预算截面的附加诊断/存储开销；单worker一次、轮转顺序、不同seed，不是纯训练时间或稳定加速基准。

## 线性基线敏感性

| 表示 | 旧lambda | 旧L MSE | 扩展lambda | 扩展L MSE |
|---|---:|---:|---:|---:|
{basetable}

旧L和新L分开保存；新L网格含0，0用float64 SVD最小范数rcond=1e-12，其余沿用正则化求解。均由暴露验证选参，不代表线性预测能力的理论上限。

## 同seed配对（小于1表示分子误差更低）

| 预算 | seed | mixed48/raw48 | raw48/raw96 | mixed48/raw96 |
|---|---|---:|---:|---:|
{pairtable}

## 范围与证据

ETH f100目标1730、2023验证365；训练scaler与RMSSE分母、目标和键完全相同。raw96覆盖96天，raw48覆盖48天，mixed48覆盖96天但旧64天聚合。raw48/mixed48同容量、同seed初始权重逐位相同。三种表示全部train/validation派生数组由独立循环/尾切核对。

seed17 raw96/mixed48截至600步最佳状态与旧批逐位相同，原控制成立。600/1200/1800对应同一连续轨迹，不是27次拟合。完整逐seed27行结果见ALL_RESULTS_V1.csv，包括预算末端误差、样本暴露、内存和F/L两种比值。

本批属于ETH事后开发诊断，不回答其他市场、未来确认、纯覆盖/分辨率因果效应或可接受非劣。新旧时间都非正式硬件基准。既有R1未修改；一致特征选择尚未执行。

整批执行{R['batch_seconds']:.2f}秒；执行完成时私有输出{R['private_bytes']}字节。审查解释和下一步决定另见DECISION_V1.md。
''')
print(json.dumps(dict(audit='PASS',fits=9,restored_checkpoints=54,means=means,baselines={a:{'lambda':b['L_wide']['lambda_value'],'MSE':b['L_wide']['MSE']} for a,b in base.items()}),ensure_ascii=False))
