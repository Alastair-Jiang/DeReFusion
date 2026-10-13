"""Record the received review without changing frozen experiment artifacts."""
import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
D = pathlib.Path(__file__).resolve().parent
ATTACHMENT = pathlib.Path('C:/Users/26843/.codex/attachments/7d20cf32-a095-4ad8-bf3a-9244d6dd4332/已粘贴的文本.txt')
EXPECTED_HEAD = 'a74126c11d857da8514074b72282adc8d47f28a7'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == EXPECTED_HEAD, 'Checkout drift: stop'
assert sha(ATTACHMENT) == 'e12cac9d29b327fe8591cf066455473eac795cddc92184fcbd73d1a37a1b6d8a'
p = json.loads((D / 'PROGRESS_2026-10-13.json').read_text(encoding='utf-8'))
bindings = {}
for key, relative in p['candidate_artifacts'].items():
    if key.endswith('_sha256') or key + '_sha256' not in p['candidate_artifacts']:
        continue
    path = ROOT / relative
    actual = sha(path)
    assert actual == p['candidate_artifacts'][key + '_sha256'], f'Drift: {relative}'
    bindings[relative] = actual
r = json.loads((D / 'CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json').read_text(encoding='utf-8'))
a = json.loads((D / 'CDD_INTERNAL_CONSISTENCY_AUDIT_V1_2.json').read_text(encoding='utf-8'))
assert a['result'] == 'PASS' and a['checked_F_fits'] == 24
assert a['results_sha256'] == sha(D / 'CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json')
epochs = []
for fraction in [0.25, 0.5, 0.75, 1.0]:
    fits = [x['fit'] for x in r['runs'] if x['fraction'] == fraction]
    assert len(fits) == 6
    epochs.append({'fraction': fraction, 'training_targets': fits[0]['train_keys'],
                   'samples_seen_min': min(x['training_samples_seen'] for x in fits),
                   'samples_seen_max': max(x['training_samples_seen'] for x in fits),
                   'effective_epochs_min': min(x['effective_epochs'] for x in fits),
                   'effective_epochs_max': max(x['effective_epochs'] for x in fits)})
private_root = ROOT / 'data/shrink-cdd-20261013-v1'
private_files = [x for x in private_root.rglob('*') if x.is_file()]
output_bytes = sum(x.stat().st_size for x in private_files)
predictions = list(private_root.glob('runs_v1_1/**/evaluation.predictions.csv'))
assert len(predictions) == 24
assert output_bytes < 2 * 1024 ** 3
subprocess.run(['git', 'check-ignore', '--quiet', str(private_root / 'BTCUSD.raw.csv')], cwd=ROOT, check=True)
timestamp = datetime.now(timezone.utc).isoformat()
record_path = D / 'CDD_DSH_REVIEW_DISPOSITION_V1.json'
report_path = ROOT / 'docs/DRF_CDD_DSH_REVIEW_DISPOSITION_2026-10-13.md'
assert not record_path.exists() and not report_path.exists(), 'Preserve prior disposition'
record = {'timestamp_utc': timestamp, 'repository': str(ROOT), 'head': head,
          'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
          'review_input_path': str(ATTACHMENT), 'review_input_sha256': sha(ATTACHMENT),
          'verified_artifact_bindings': bindings, 'effective_training_exposure': epochs,
          'private_storage': {'files': len(private_files), 'bytes': output_bytes,
                              'prediction_files': len(predictions), 'gitignored': True,
                              'scope': 'Whole CDD private directory including failed v1 packages and snapshots'},
          'acceptance': 'No invalidating defect reported; bounded exploratory batch accepted with stated limitations',
          'counts': {'planned_F_fits': 24, 'completed_F_fits': 24, 'evaluated_F_fits': 24,
                     'internally_checked_F_fits': 24, 'independent_structural_arithmetic_review_F_fits': 24,
                     'independent_raw_array_review_F_fits': 0,
                     'independent_full_scientific_acceptance': 'not claimed'},
          'remaining': ['Independent raw-array comparison and bitwise refit determinism not verified',
                        'Programmatic hard output/batch budget enforcement requires a successor before future runs',
                        'Commercial use and public raw/prediction/weight distribution not released; summary publication requires separate review',
                        'Original Yahoo-labelled four-asset source basis unresolved'],
          'immutable_artifacts_changed': False}
write_json(record_path, record)
rows = '\n'.join(f"| {x['fraction']:.0%} | {x['training_targets']} | {x['samples_seen_min']}–{x['samples_seen_max']} | {x['effective_epochs_min']:.6f}–{x['effective_epochs_max']:.6f} |" for x in epochs)
report_path.write_text(f'''# CDD 缩小式探索：DSH 复核处置与验收边界

核验时间（UTC）：{timestamp}。主仓库 `{ROOT}`，分支 `{record['branch']}`，HEAD `{head}`。
DSH 输入 SHA-256：`{sha(ATTACHMENT)}`。全部既有进度表输入摘要重新匹配；冻结协议、执行器、输入包、结果和内部审计未修改。完整绑定见 `CDD_DSH_REVIEW_DISPOSITION_V1.json`。

## 接收结论

DSH 未发现使本批无效的 P0/P1 缺陷，并认可新 CDD 两资产的限定本地非商业研究依据。首批 24 次拟合、24 次评估、14,400 optimizer steps 已完成。内部 v1.2 一致性审计 PASS 24/24；DSH 对 24 项结构、键、时序和汇总算术的独立核对已接收。DSH 未逐元素核对原始价格与全部 role 数组，因此独立原始数组复核计数仍为 0，不把这些计数合并成“全面独立科学认证”。

## 逐项处置

| 审查项 | 处置 |
|---|---|
| 内部审计尚未运行 | 该状态与当前工件不符。现有 v1.2 输出 PASS；输入结果摘要匹配。保留 v1.1 目标文本解码失败和 v1.2 float32 解码修复的记录，不改训练或指标结果。 |
| 回顾性测试措辞 | 统一写“回顾性时间留出测试”。下载时已可观测历史，不是前瞻实盘或未接触确认。相对于拟合数据，时间留出仍可属于拟合样本外；不能仅因事后下载就否定该定义。避免无条件的“样本外预测性能”表述。 |
| 等步数与等 epoch 混淆 | 接受并补记下表。本实验比较固定 600 步预算下的历史窗口策略，同时改变训练重复暴露、近期分布和缩放统计量；不能将差异归因于纯粹的数据量。 |
| 预算强制缺项 | 接受。本批整个私有目录 {output_bytes:,} bytes，低于 2 GiB；实际完成不代表程序具备硬限额。后续执行器须采用剩余批次时间约束 worker 超时，并在写入与阶段边界强制检查空间。不得追认旧执行器已强制执行。 |
| 资格脚本注释过宽 | 固定实际行为：审查可用的 2026 前历史，包括 2018 前记录；不解析 2026 及以后 OHLC。release 明确允许此前历史。保留已执行脚本摘要，后续版本改注释。 |
| per-key 输出分类 | 24 份归一化预测与目标 CSV 和 checkpoint、role 包、raw 均为私有、gitignored 工件，未授权公开或复制到远程。 |
| 大小写哈希 | 旧摘要是合法 64 位 hex，比较可转小写；保留旧文档原样，不把大小写格式作为内容漂移。 |
| 长路径清单缺项 | 已有独立补充清单使用临时 core.longpaths 覆盖重新枚举成功；是路径清单覆盖，不是全部文件内容审计。 |
| 早期助手失败 | 只有会话工具记录，未取得 DSH 独立核验的独立日志；不补造当时日志。v1 序列化失败记录与旧包已保留。 |
| 旧文件时间戳 | mtime 支持未发生写入，不足以证明从未读取。不得将 mtime 当作访问审计。 |

## 实际训练暴露

每个比例包含两资产 × 三 seed；范围来自冻结结果的实际计数。

| 保留比例 | 训练目标数 | 实际样本暴露数范围 | 等效 epoch 范围 |
|---|---:|---:|---:|
{rows}

## 结果及下一步

75% 历史的三 seed 平均误差在两资产中均略低于 100%，25% 均更差；所有 DeReFusion 条件仍逊于持久性基线。ETH 是验证集预先排序的较易资产。删除 BTC 后组合均值下降属于构成变化，不意味着 ETH 模型因减少资产而改善。完整结果见 `DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md`。

本批两个探索问题的初步结果已交付；并未补齐原先四资产矩阵或证明一般性规律。下一轮优先以独立原始数组抽查关闭复核缺项，然后在新协议中选择“固定步数”或“固定 epoch”的单一主要问题，先修预算强制与做合成检查，再签发精确哈希执行释放。当前不据测试表现继续调参，不重写确认性预注册。

CDD 提供方的研究邀请不等于上游全部权利清除。商业使用、公开原始数据/预测/权重仍未放行；摘要对外发布单独审查。旧 Yahoo 四资产维持来源待核实，禁止同符号混用。此次没有 Git 提交或推送。
''', encoding='utf-8')
p['status'] = 'FIRST_CDD_TWO_ASSET_BATCH_COMPLETE_INTERNAL_PASS_DSH_LIMITED_REVIEW_RECEIVED'
p['active_counts'].update(record['counts'])
p['active_counts']['independently_reviewed_F_fits'] = 0
p['independent_review_scope'] = '24 structural/arithmetic checks; 0 raw-array/full scientific acceptances. See disposition.'
p['last_updated_local'] = datetime.now().astimezone().isoformat()
p['latest_actions'].append('Received DSH limited independent review; reverified immutable bindings, reconciled stale audit status, recorded actual epoch exposure and budget enforcement gap; no refit or publication.')
for gate in p['gates']:
    if gate['id'] == 'G3':
        gate['state'] = 'COMPLETE_INTERNAL_PASS_DSH_LIMITED_REVIEW_RECEIVED'
        gate['evidence'] = p['independent_review_scope']
for key, path in [('cdd_dsh_disposition', record_path), ('cdd_dsh_disposition_report', report_path)]:
    p['candidate_artifacts'][key] = path.relative_to(ROOT).as_posix()
    p['candidate_artifacts'][key + '_sha256'] = sha(path)
write_json(D / 'PROGRESS_2026-10-13.json', p)
manifest = {'timestamp_utc': timestamp, 'head': head, 'scope': 'CDD candidate deliverables only; no private data',
            'files': {x.relative_to(ROOT).as_posix(): sha(x) for x in D.glob('*') if x.is_file() and x.name.startswith(('CDD_', 'run_shrink_cdd', 'audit_and_report_cdd', 'record_dsh', 'SHRINK_CDD', 'PROGRESS_'))},
            'reports': {x.relative_to(ROOT).as_posix(): sha(x) for x in [report_path, ROOT / 'docs/DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md']}}
write_json(D / 'CDD_DELIVERABLE_HASHES_V1.json', manifest)
print(json.dumps({'status': p['status'], 'exposure': epochs, 'private_bytes': output_bytes, 'verified_bindings': len(bindings), 'disposition_sha256': sha(record_path)}, ensure_ascii=False))
