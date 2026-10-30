# 交付报告：仓库整合阻塞项处置 — 2026-10-30

**状态：** 分支候选。**未合并 `main`。** 本报告不构成科学结论、跨硬件等价证明或第三方数据发布授权。

## 1. 基线与交付对象

| 对象 | 值 | 核验方式 |
|---|---|---|
| 远程 `main` | `87bc113d892320a343d61893b1c849ce4391dca5` | `git ls-remote --heads origin` 直连读取 |
| 候选另一父提交 | `ae6507423a6f78354735bedc1c786432f9f3edd1` | 记录值；远程该分支已前移，见第 2 节 |
| 177 路径候选树 | `852065887fb5a80122f39102daa8afba2508d94f` | `git merge-tree --write-tree 87bc113 ae650742` 与 `git write-tree` 双向一致 |
| 交付分支 | `codex/remediation-delivery-20261030` | 从 `origin/main` 新建，未改写任何既有分支 |
| 交付工作区 | `<主目录>\.codex\worktrees\derefusion-delivery-20261030` | 独立工作区，主检出未受影响 |

交付提交：

| 提交 | 内容 |
|---|---|
| `5546524` | `fix(replay): add fail-closed release entry without assert gates` |
| `dfc977b` | `fix(receiver): reconcile batch authorization with health probe` |
| `a778ccd` | `docs: record reconciliation baseline, execution limits and release scope` |
| `e232ae7` | `fix(replay,receiver): close review findings on gate and prefetch` |
| 本文档提交 | `docs: add delivery report`（哈希见推送记录） |

工作区清单与主检出脏状态见 `DRF_RECONCILIATION_BASELINE_V2_2026-10-30.md`。基线变化摘要：远程 `docs/project-status-catalog-2026-10-10` 从 `ae650742` 前移到 `6a65204`（+2 提交）；候选树仍绑定 `ae650742`，因此旧评审对象未变，但若改用新 tip 重合并必须重新评审。

## 2. 原阻塞项状态

| # | 阻塞项 | 状态 | 依据 |
|---|---|---|---|
| 1 | `compression_replay.py` 用断言做释放先决条件 | **部分解决**：新入口已交付并测试；历史文件未修，仍不安全 | `DRF_HISTORICAL_EXECUTION_LIMITS_V1_2026-10-30.md` 第 3.1、4 节 |
| 2 | raw48 历史执行器用断言做授权/输入检查 | **已隔离**：按 blob 与 SHA-256 记录为 `HISTORICAL_ONLY`，未重跑 | 同上第 3.3 节 |
| 3 | CDD v1 / v1.1 直接 worker 入口绕过协调器 | **已隔离**：两版快照保留并记录限制 | 同上第 3.4 节 |
| 4 | synthetic lifecycle 直接 worker 接受调用方路径 | **已隔离**：记录"合成身份只是假设" | 同上第 3.5 节 |
| 5 | README 发布描述 | **已复核**：候选内未暂存修订经逐条核对为准确；未单独落 `main` | `DRF_RELEASE_SCOPE_AND_RIGHTS_V1_2026-10-30.md` 第 3.2 节 |
| 6 | 发布范围与数据权利 | **部分闭合**：已形成逐来源/逐成果处置表并冻结"本轮不新增公开"；逐项裁定仍需负责人 | 同上第 5、6 节 |
| 7 | DSH 历史审阅报告与清单缺失 | **仍缺外部证据**：两处路径再次搜索未找到，标"不可核验" | `EVIDENCE_REVIEW_V1.md` 第 3 节 |
| 8 | 9 份本地审阅记录哈希匹配但不在候选 | **已核实并留置**：9 项本地、哈希匹配、凭据样式 0 命中、4 项含本机路径、不发布 | 同上第 4 节 |
| 9 | 接收器与 live-flow 变更重叠 | **已解决（源码级）**：授权校验 + 健康探针整合，29 项 mock 测试通过，独立审阅 APPROVE WITH FIXES 且修复已复核 | 本报告第 3、4、5.3 节 |

## 3. 修改文件

| 路径 | 变更 | Git blob | SHA-256 |
|---|---|---|---|
| `reproduction/analysis/compression_replay_release_v2.py` | 新增 376 行 | `37450207d7d2b4f9579a831434a0958be13f3ba5` | `d96906dde47617e44fbc3599ee6fdbd1a6b574ab998b436fe3a6ac94c3f72d8e` |
| `tests/test_compression_replay_release_v2.py` | 新增 441 行 | `aa7b0f72a9fee11c65b2c54e676738c374769bda` | `5e81da79095fa9323351783cf21459578ab6a2519d4e155f98b0f2fe0f3e1716` |
| `reproduction/analysis/receive_phase1_completed.py` | +192 / −20 | `7f43d80b9ddcabef7e195b7773763f1be2a7e020` | `0ec33c5b35f10551b23c18f95ee6db8d99a4402e6b46fe925f249d83c59599ce` |
| `tests/test_phase1_completed_receiver.py` | +293 / −8 | `c19733c380b8306065b28a772144bac00efcda60` | `7467f1533dd1ee32104ec7f599a17bf311049bf8e3627605c0db5df2925452d3` |
| `docs/DRF_RECONCILIATION_BASELINE_V2_2026-10-30.md` | 新增 | — | — |
| `docs/DRF_HISTORICAL_EXECUTION_LIMITS_V1_2026-10-30.md` | 新增 | — | — |
| `docs/DRF_RELEASE_SCOPE_AND_RIGHTS_V1_2026-10-30.md` | 新增 | — | — |
| `research_work/.../remediation_2026_10_30/build_evidence_supplement.py` | 新增 | — | — |
| `research_work/.../remediation_2026_10_30/EVIDENCE_SUPPLEMENT_V2.json` | 新增 | — | — |
| `research_work/.../remediation_2026_10_30/EVIDENCE_REVIEW_V1.md` | 新增 | — | — |

新增内容不含原始行情、逐键预测、checkpoint、模型权重或凭据值。接收器候选**不含** `codex/live-hardware-flow` 的 7 个 `pred.npy`，也不含 Windows Credential Manager 读取模块。

## 4. 测试记录

**环境：** Windows，Python 3.11.15，torch 2.11.0+cu128，NumPy 2.4.6（`D:/env/python.exe`）。合成测试；无网络、无真实数据、无训练。

| 命令 | 结果 |
|---|---|
| `python -B -m unittest tests.test_compression_replay_release_v2` | 50 passed |
| `python -B -m unittest tests.test_phase1_completed_receiver` | 29 passed |
| 上述两项合并运行（正常模式） | 79 passed |
| 上述两项合并运行（`python -O`） | 79 passed |
| 11 个测试模块全量收集 | 101 收集 / 92 通过 / 9 错误 |

9 项错误全部是导入期 `ModuleNotFoundError`：`sklearn`、`matplotlib`、`reformer_pytorch` 在本环境缺失。涉及模块（`test_explicit_date_split`、`test_phase1_calibration_runner`、`test_phase1_completed_package_intake`、`test_phase1_intake_consumer`、`test_phase1_recovery`、`test_phase1_stage_c_authorization`、`test_phase1_stage_runner`、`test_phase1_model_shapes` 的两例）本轮未改动。

**没有运行的检查：**

- 真实 SFTP 传输、真实 GPU 探针、任何训练/拟合/评分。
- `research-ops-site` 构建与 live-flow 站点组件（不在本分支）。
- CUDA 环境下的模型形状测试（缺 `reformer_pytorch`）。
- 177 路径候选的重新解析与哈希扫描（本轮未改动该候选）。
- 数组与指标的数值复算（本轮未重跑；引用的是 `SCIENCE_RECHECK_2026-10-30.md` 的既有记录）。

## 5. 独立审阅

### 5.1 方式与独立性声明

两轮审阅由**独立上下文的只读子代理**完成：审阅者看不到主代理的推理过程，只拿到文件路径、需求清单和只读命令。两个代理均未修改、提交或推送任何内容，只使用临时 fixture 做动态探针。

**必须说明的限制：** 本会话的子代理与主代理属于同一模型族，不构成"跨模型独立验证"。真正可复现的判据是确定性测试与字节哈希，不是代理身份。上一轮历史审阅用的是不同模型，本轮没有那个条件。

### 5.2 对象 A：fail-closed 释放入口

**首轮结论：APPROVE WITH FIXES。** 核心绑定检查未发现 fail-open 路径，文件内无 `assert`，两套测试通过。主要发现与处置：

| 发现 | 严重度 | 处置 |
|---|---|---|
| A-F1 交付分支不含被钉住的历史文件与 `PREPARATION_V1.json`，入口在 main 基线上无法对真实历史做端到端演练 | 高（若把该分支当最终交付目标即为阻断） | **已披露并限定**：文档与 docstring 明确"历史文件只在 docs 候选、main 上会失败关闭"；未伪造真实记录的 smoke test |
| A-F2 runner 未被协议钉住，"runner 绑定"只是三方互证 | 中 | **已修**：要求 `replay.runner_sha256` |
| A-F3 `--attempt` 可以是 root 下任意目录，可写入冻结目录 | 中 | **已修**：限定 `data/compression-replay-attempts/<安全名>` |
| A-F4 git 失败时信任调用方给的 `--current-head` | 中低 | **已修**：非 git 根必须显式 `--allow-non-git-fixture` |
| A-F5 仅 runner 检查符号链接 | 低 | **已修**：五个记录文件都要求普通文件 |
| A-F6 缺失 pin 字段会 `None == None` 通过；历史 preparation 载入时未复检 | 低 | **已修**：pin 字段必须存在且类型正确；载入后重哈希并与钉住值比较 |
| A-F7 协议的 status/branch/resources 未使用 | 低 | **部分修**：decision_owner 与授权交叉校验；释放记录补 branch/resources |

### 5.3 对象 B：接收器候选

**首轮结论：APPROVE WITH FIXES。** 未发现授权绕过，未发现相对基线的行为回退，26 项测试通过。主要发现与处置：

| 发现 | 严重度 | 处置 |
|---|---|---|
| B-1 `prefetch(max_concurrent_requests=...)` 在旧 paramiko 上会抛 `TypeError`，整轮接收失败 | 中 | **已修**：按关键字逐级降级，最后退化为不预取；新增 3 项测试 |
| B-2 `manifest_hash_verified` 在真实批次上不可达 | 中低 | **仅记录**：该字段只证明"某个收到的 `*manifest.csv` 的字节等于授权哈希"；仓库内没有生产者把 manifest 放进批次根目录，因此对 rtx8000 批次它恒为 `False`，也不是行级键集校验 |
| B-3 预取只限制在途请求数，不限制内存 | 低 | 记录为已知限制 |
| B-4 发布失败会留下空的 `attempts/<id>`，该 attempt 之后永久失败关闭 | 低 | 记录为已知限制 |
| B-5 批次校验失败时不会写 `remote_health.json` | 信息 | 记录为已知限制 |

### 5.4 修复后复核

修复提交后再次请求两位审阅者只审"增量"。

接收器侧结论：B-1 已关闭，未引入新的 fail-open；唯一保留意见是 `except TypeError` 可能吞掉 paramiko 内部的真实 `TypeError`（只影响诊断，不影响完整性）。

释放入口侧结论：F2、F5 确认关闭；F3、F6 当时仍有两个可收紧点——目录规则接受区域根与嵌套子目录、`keys_count: true` 在钉住侧可绕过布尔排除——均已修复并加测试（目录必须是区域直接子目录；两侧都排除布尔）。F1 的披露原先把失败消息写错（既有历史协议其实停在"no replay object"），已改正并补上"runner_sha256 为必填、既有协议都不满足"这一句。

新增的守卫测试直接读取模块源码，断言不存在以 `assert` 开头的语句，把"不依赖断言"从人工检查变成可执行检查。

### 5.5 审阅未覆盖的范围

审阅者没有：复核 177 路径候选的内容、评估任何数值结论、重跑历史实验、验证第三方数据权利、执行真实 SFTP 或 GPU 探针。审阅通过不等于科学结论或发布权利通过。

## 6. 数据来源与发布边界

- 本轮新增公开内容：代码、合成测试、治理文本、证据清单。**无第三方数据字段。**
- `main` 已跟踪：`results/` 705、`checkpoints/` 36、`dataset/` 61 CSV、`data/raw/yahoo/` 2 文件。既有暴露，不追认。
- CDD 与 Bitstamp API 的处置分别为 `requires-resolution` 与 `local-only`；详见 `DRF_RELEASE_SCOPE_AND_RIGHTS_V1_2026-10-30.md` 第 5、6 节。
- 缺失原件：`dsh_raw_array_review_v1/RAW_ARRAY_AUDIT_REPORT.md` 与 `DELIVERABLE_HASHES.json`——不可核验，不重建。
- 9 份本地审阅材料作者身份未证实（目录名 kimi，正文自称 DSH），不作为已验证审阅引用。
- 无法核验的科学主张：跨硬件等价、确认性显著性、第三方再分发权。本轮均未新增任何此类主张。

## 7. 提交与推送范围

见第 1 节提交表；推送范围将在推送后补记于本节。**未合并到 `main`**；177 路径候选、各既有分支与工作区、历史协议与结果均未改动或删除。

## 8. 留给后续 Stage 的事项

1. 177 路径候选的整体裁决（语义、权利、安全）与逐路径 `review-required` 决策。
2. README 未暂存修订与候选一起评审、一起暂存。
3. 两份 DSH 原件的定位，或正式记录为"永久不可核验"。
4. 接收器与 `serve_phase1_ops_status.py` / 站点组件的接口对齐（本分支只交付接收侧）。
5. 主检出 `freeze-summary.json` 的本地状态改写需要负责人裁定；本轮未采用。
6. 未来任何执行协议必须声明 `replay.gate = compression-replay-release/v2`、绑定本入口的 SHA-256，并在 `replay.runner_sha256` 中钉住 wrapper；因此新生成器必须先写 wrapper 再写协议（冻结的 `generate()` 顺序相反，不能直接复用）。
7. 外部 PR #2 的报告表述与其跟踪清单不一致问题。

## 9. 不成立的等式

代码测试通过 ≠ 科学结论成立；历史结果复算通过 ≠ 跨硬件等价；仓库合并 ≠ 发布权利通过；哈希一致 ≠ 来源或独立性已验证。
