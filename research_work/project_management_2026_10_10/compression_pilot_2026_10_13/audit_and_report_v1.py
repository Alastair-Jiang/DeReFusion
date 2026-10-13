"""Internally check the completed pilot without fitting or reading test inputs."""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from datetime import date, timedelta
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('compression_pilot_frozen', HERE/'run_pilot_v1.py')
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.verify_release()
r = json.loads(pilot.RESULT.read_text(encoding='utf-8'))
prep = json.loads(pilot.PREP.read_text(encoding='utf-8'))
assert r['total_optimizer_steps'] == 1200 and not r['test_read_or_scored']
assert r['release_sha256'] == pilot.sha(pilot.RELEASE)
assert r['batch_seconds'] < pilot.P['resources']['batch_seconds']

def expected_keys(start, stop):
    day, end, keys = date.fromisoformat(start), date.fromisoformat(stop), []
    while day < end:
        keys.append(f'CDD-BITSTAMP|ETHUSD|{day.isoformat()}T00:00:00Z|h1-close')
        day += timedelta(days=1)
    return keys

roles = {}
for role in ('train', 'validation'):
    paths = [Path(prep['arms'][a][role]['path']) for a in pilot.ARMS]
    raw = pilot.read_role(paths[0], role, 96)
    compact = pilot.read_role(paths[1], role, 48)
    x, y, keys, sd, scale = raw
    xc, yc, kc, sdc, scalec = compact
    assert (sd, scale) == (sdc, scalec) and keys == kc and np.array_equal(y, yc)
    bounds = ('2018-04-07', '2023-01-01') if role == 'train' else ('2023-01-01', '2024-01-01')
    assert keys == expected_keys(*bounds)
    # Reconstruct all groups by a separate loop instead of calling aggregate().
    oracle = np.empty((len(x), 48, 4), dtype=x.dtype)
    for group in range(16):
        segment = x[:, group*4:group*4+4]
        oracle[:, group, 0] = segment[:, 0, 0]
        oracle[:, group, 1] = np.max(segment[:, :, 1], axis=1)
        oracle[:, group, 2] = np.min(segment[:, :, 2], axis=1)
        oracle[:, group, 3] = segment[:, -1, 3]
    oracle[:, 16:] = x[:, 64:]
    assert np.array_equal(oracle, xc) and np.array_equal(x[:, -1], xc[:, -1])
    roles[role] = {'raw96': raw, 'mixed48': compact}

private_receipts = {}
for arm, row in zip(pilot.ARMS, r['arms']):
    assert row['arm'] == arm and row['steps'] == 600 and row['samples_seen'] == 18900
    assert row['train_keys'] == 1730 and row['validation_keys'] == 365 and not row['test_inputs_received']
    assert row['parameters'] == (21743 if arm == 'raw96' else 21599)
    assert row['worker_seconds'] < pilot.P['resources']['worker_seconds']
    assert [v['step'] for v in row['history']] == list(range(50, 601, 50))
    minimum = min(row['history'], key=lambda v: v['validation_normalized_MSE'])
    assert minimum['step'] == row['best_step']
    x, y, keys, sd, scale = roles['validation'][arm]
    output = pilot.PRIVATE/'runs'/arm
    rows = list(csv.DictReader((output/'validation.predictions.csv').open(encoding='utf-8', newline='')))
    assert [v['key'] for v in rows] == keys and len(rows) == 365
    saved = torch.load(output/'model.pt', map_location='cpu', weights_only=True)
    state_hash = hashlib.sha256()
    for key, value in sorted(saved['F'].items()):
        state_hash.update(key.encode()); state_hash.update(value.numpy().tobytes())
    assert state_hash.hexdigest() == row['state_tensor_sha256']
    m = pilot.model(arm); m.load_state_dict(saved['F'])
    restored = pilot.predict(m, x)
    stored = {a: np.array([float(v[a]) for v in rows]) for a in ('F', 'L', 'P', 'target')}
    assert np.array_equal(stored['target'], y[:, 3].astype(np.float64))
    assert np.array_equal(stored['F'], restored)
    ridge = (x.reshape(len(x), -1).astype(np.float64)-saved['ridge_x_mean'].numpy())@saved['ridge_coef'].numpy()+saved['ridge_y_mean']
    assert np.array_equal(stored['L'], ridge)
    assert np.array_equal(stored['P'], x[:, -1, 3].astype(np.float64))
    for a in ('F', 'L', 'P'):
        mse = math.fsum((float(p)-float(t))**2 for p, t in zip(stored[a], stored['target']))/len(rows)*sd**2
        assert math.isclose(mse, row['mse'][a], rel_tol=1e-12, abs_tol=1e-10)
        assert math.isclose(math.sqrt(mse/scale), row['rmsse'][a], rel_tol=1e-12)
    assert math.isclose(minimum['validation_normalized_MSE']*sd**2, row['mse']['F'], rel_tol=1e-12)
    assert row['validation_keys_sha256'] == hashlib.sha256('\n'.join(keys).encode()).hexdigest()
    private_receipts[arm] = {f: pilot.sha(output/f) for f in ('model.pt', 'fit.json', 'validation.predictions.csv')}

assert r['arms'][0]['mse']['P'] == r['arms'][1]['mse']['P']
assert r['fresh_control_matches_parent_state'] and r['fresh_control_matches_parent_validation_MSE']
assert pilot.private_bytes() <= pilot.P['resources']['private_output_bytes']
raw, comp = r['arms']
delta_mse = 100*(comp['mse']['F']/raw['mse']['F']-1)
delta_rmsse = 100*(comp['rmsse']['F']/raw['rmsse']['F']-1)
saved_time = 100*(1-comp['neural_fit_validation_seconds']/raw['neural_fit_validation_seconds'])
saved_mem = 100*(1-comp['training_phase_peak_working_set_bytes']/raw['training_phase_peak_working_set_bytes'])
ridge_mse_change = 100*(comp['mse']['L']/raw['mse']['L']-1)
audit = {'result': 'PASS', 'timestamp_utc': pilot.utc(), 'type': 'Codex internal consistency audit; not independent DSH acceptance',
         'script_sha256': pilot.sha(__file__), 'results_sha256': pilot.sha(pilot.RESULT),
         'checked_F_fits': 2, 'checked_validation_keys_per_fit': 365, 'independent_review': 'PENDING',
         'checks': ['All train/validation compressed arrays reconstructed by separate loop',
                    'Targets/key sets/scalers/sample exposures equal', 'Earliest minimum checkpoint and 600-step cadence',
                    'Restored F and ridge forecasts match every stored prediction', 'Standard-library full-key metric recomputation',
                    'Original96 bitwise state/validation replay matches parent', 'Persistence exact equality',
                    'Resource caps and source/release identities'],
         'private_artifact_sha256': private_receipts,
         'summary_changes_pct': {'F_MSE_increase': delta_mse, 'F_RMSSE_increase': delta_rmsse,
                                 'neural_fit_validation_time_reduction': saved_time,
                                 'training_phase_peak_process_working_set_reduction': saved_mem,
                                 'ridge_MSE_change': ridge_mse_change}}
pilot.dump(HERE/'INTERNAL_AUDIT_V1.json', audit)
report_path = ROOT/'docs/DRF_CDD_ETH_COMPRESSION_MINIMAL_PILOT_2026-10-13.md'
rows = '\n'.join(f"| {v['arm']} | {v['rmsse']['F']:.6f} | {v['rmsse']['L']:.6f} | {v['rmsse']['P']:.6f} | {v['neural_fit_validation_seconds']:.3f} | {v['training_phase_peak_working_set_bytes']/1024**2:.2f} | {v['parameters']} |" for v in r['arms'])
report = f'''# ETH 固定 OHLC 压缩：最小试验结果

协议 `{pilot.P['protocol_id']}`；主仓库 `{ROOT}`；分支 `{pilot.P['branch']}`；执行 HEAD `{pilot.P['head']}`。完成于 `{r['finished_at_utc']}`（UTC）。

## 本批结论

已完成两次真实训练、共 1,200 optimizer steps，内部一致性核对 PASS 2/2。原始 96 天对照逐位复现此前同 seed 的 checkpoint 张量及验证 MSE。该固定压缩函数能够减少输入计算，但本次 DeReFusion 精度有损，不能作为已有收益改进方案直接替换原输入。

把更早的 64 天按四天一组聚合为 16 个 OHLC，最近 32 天保留日线；合计 48 个位置，覆盖原来同一 96 天。O 取第一日、H 取最大值、L 取最小值、C 取最后一日。没有删除目标样本，训练目标仍为 1,730、验证目标仍为 365。训练/验证输入 x 的 float32 张量字节数均减少 50%；源文件和旧包保留，整体磁盘占用并未减半。

## 验证结果

只使用 2023 年验证键，未读取或评分 2024–2025 测试输入。两组同 seed 17、batch 32、600 步、18,900 样本暴露、相同冻结训练缩放与 RMSSE 标尺，按每 50 步完整验证选择 checkpoint。RMSSE 越低越好。

| 输入 | DeReFusion RMSSE | Ridge RMSSE | 持久性 RMSSE | 神经训练+验证秒 | 训练阶段进程峰值 MiB | 参数数 |
|---|---:|---:|---:|---:|---:|---:|
{rows}

压缩组 DeReFusion MSE 增加 **{delta_mse:.2f}%**，RMSSE 增加 **{delta_rmsse:.2f}%**。本次测得神经训练加验证耗时减少 **{saved_time:.2f}%**，训练阶段整个进程峰值 working set 减少 **{saved_mem:.2f}%**。整批耗时 `{r['batch_seconds']:.3f}` 秒，聚合两角色数组约 `{r['aggregation_seconds']:.6f}` 秒。Ridge MSE 变化 **{ridge_mse_change:+.2f}%**，说明压缩对不同模型的影响有差异。两组 DeReFusion 仍不及持久性基线。

## 门控与检查

| 检查 | 输入 | 状态 | 证据 | 下一步允许动作 |
|---|---|---|---|---|
| 来源与本地用途 | 原 CDD 内部研究释放、冻结 ETH 包 | PASS，沿用限定范围 | 无新下载，parent/source pins 匹配 | 仅本地诊断 |
| 固定变换正确性 | 合成样本与全部 train/validation 数组 | PASS | 独立循环重建所有聚合区间，最近 32 天、目标与键精确不变 | 比较本次描述性差异 |
| 模型配置 | 原 pinned 源，seq_len 96/48 | PASS，偏离已声明 | 21,743/21,599 参数；d_ff/d_model=4，d_model/n_heads=8 | 不作纯预处理机制归因 |
| 训练执行与覆盖 | 两 worker、365 验证键 | PASS | 每组 600 步、12 次验证、尾批完整、最早最低 checkpoint | 报告两次完成 |
| 内部指标核对 | checkpoint 与逐键预测 | PASS 2/2 | 全部预测恢复一致、标准库损失复算、原始对照逐位重现 | 内部结果交付 |
| 资源 | 300 秒/worker、900 秒/batch、64 MiB 私有输出 | PASS | 剩余时间限制 worker、写入前空间检查、实际输出 {pilot.private_bytes():,} bytes | 不外推单次计时 |
| 独立复核 | DSH/其他独立审查 | PENDING | 本批尚未收到 | 提供只读审查包 |
| 科学可接受精度损失界 | 研究目标/精度要求 | TBD | 未事先设数值容忍界；本批有损 | 若继续，先定义资源与精度目标再开新协议 |

## 限制与下一步

这是一资产、一 seed、验证集已用于 checkpoint 选择的可行性诊断；不能宣称泛化提升。资源是原始后压缩各一次测量，顺序固定，含验证开销和进程基础内存，不能宣称稳定加速倍率。

模型没有四天/一天的时长标记，RevIN 对聚合和日线位置等权，moving_avg=25 的实际时间跨度随位置变化；三个时序投影随输入长度缩短，初始化抽样也变化。这些因素同时改变，不能将精度变化唯一归因于信息压缩。

本次先保留为“省计算、存在精度代价”的候选，不直接替换主流程。若继续，应在新协议中明确可接受误差代价、采用同一输入长度的机制对照，并复核多个预先规定 seed。后续新增方案不能以反复挑选本验证集最好结果来充当确认。原 R1 确认协议不变。

结果摘要 SHA-256：`{pilot.sha(pilot.RESULT)}`。内部核对 SHA-256：`{pilot.sha(HERE/'INTERNAL_AUDIT_V1.json')}`。原始/角色数组、逐键预测和 checkpoint 均留在 gitignored 私有目录。本批未提交 Git；公开摘要须另行审查。
'''
assert not report_path.exists(), 'Preserve prior report'
report_path.write_text(report, encoding='utf-8')
pilot.dump(HERE/'PROGRESS_V1.json', {'status': 'COMPLETE_INTERNAL_AUDIT_PASS_INDEPENDENT_REVIEW_PENDING',
          'planned_F_fits': 2, 'completed_F_fits': 2, 'internally_checked_F_fits': 2,
          'independently_reviewed_F_fits': 0, 'optimizer_steps': 1200, 'test_read_or_scored': False,
          'report': report_path.relative_to(ROOT).as_posix(), 'report_sha256': pilot.sha(report_path),
          'results_sha256': pilot.sha(pilot.RESULT), 'internal_audit_sha256': pilot.sha(HERE/'INTERNAL_AUDIT_V1.json')})
pilot.dump(HERE/'DELIVERABLE_HASHES_V1.json', {'scope': 'Local pilot candidate records, excludes private outputs',
          'head': pilot.P['head'], 'files': {x.relative_to(ROOT).as_posix(): pilot.sha(x) for x in HERE.iterdir() if x.is_file()},
          'report': {report_path.relative_to(ROOT).as_posix(): pilot.sha(report_path)}})
print(json.dumps({'audit': 'PASS', 'checked_fits': 2, 'changes_pct': audit['summary_changes_pct'], 'report': str(report_path)}))
