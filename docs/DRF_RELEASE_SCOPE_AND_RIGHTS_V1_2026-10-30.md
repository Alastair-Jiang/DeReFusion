# 发布范围与数据权利处置 V1 — 2026-10-30

**状态：** 项目内部处置记录。不是法律意见，不构成任何来源的发布许可，也不把"用户允许推送"解释为第三方授权。

## 1. 结论先说

- 本轮**不新增任何原始行情、逐键预测、checkpoint、模型权重或派生数值结果的公开**。
- 本轮交付到分支的内容是：一个失败即关闭的执行释放门禁、一个接收器源代码候选、四份治理文本、一份证据补充清单。它们不含第三方数据字段。
- 177 路径候选树 `852065887fb5a80122f39102daa8afba2508d94f` 仍未获独立批准，**未合并、未发布**。
- 历史 `results/`、`checkpoints/`、`dataset/`、`data/raw/yahoo/` 已存在于远程，那是既有暴露，不是本轮追认的发布授权。

## 2. 本次交付新增了什么

代码：

- `reproduction/analysis/compression_replay_release_v2.py`（新，失败即关闭的释放入口）
- `tests/test_compression_replay_release_v2.py`（新，合成测试）
- `reproduction/analysis/receive_phase1_completed.py`（改，授权校验 + 健康探针整合）
- `tests/test_phase1_completed_receiver.py`（改，26 项 mock 测试）

记录：

- `docs/DRF_RECONCILIATION_BASELINE_V2_2026-10-30.md`
- `docs/DRF_HISTORICAL_EXECUTION_LIMITS_V1_2026-10-30.md`
- `docs/DRF_RELEASE_SCOPE_AND_RIGHTS_V1_2026-10-30.md`（本文件）
- `docs/DRF_DELIVERY_REPORT_2026-10-30.md`
- `research_work/project_management_2026_10_10/remediation_2026_10_30/build_evidence_supplement.py`
- `research_work/project_management_2026_10_10/remediation_2026_10_30/EVIDENCE_SUPPLEMENT_V2.json`
- `research_work/project_management_2026_10_10/remediation_2026_10_30/EVIDENCE_REVIEW_V1.md`

证据补充清单只记录路径、大小、SHA-256、Git blob、粗粒度模式计数（凭据样式命中数、是否含本地绝对路径），**不复制任何审阅正文**。

## 3. 未合并候选（177 路径）与 README 评审

### 3.1 候选构成

按冻结策略 `docs/DRF_ARTIFACT_BOUNDARY_V1_2026-10-13.json`（SHA-256 `8af09798f79f3351a82a35323c529c80365aaa6780f0f2f11a9bea23565ac25f`）用与检查器相同的匹配规则重新分类 177 条暂存路径：

| 分类 | 数量 |
|---|---|
| `tracked-candidate` | 25 |
| `review-required`（默认） | 152 |
| `local-only` | 0 |

文件类型：84 `.json`、47 `.md`、35 `.py`、4 `.csv`、4 `.txt`、3 `.gitattributes`。没有 `.npy`、`.npz`、`.pth`、`.pt` 或原始 OHLC。四个 CSV 是结果表与登记表，不是原始行情。

**这项检查只是拒绝清单检查**：`check_artifact_boundary.py` 只报 `local-only` 命中，"通过"不等于 152 条默认项获得逐项批准，也不等于内容、权利或秘密审查。

### 3.2 README 修订

| 对象 | 标识 | 评审结论 |
|---|---|---|
| 已暂存版本 | blob `00fd5905cc820929e5bc775234ec3e389705d246`，SHA-256 `4321aedb6b4fc7211a08554b9deb00719ff763a32f2ec9f96891e23c1bc1d32a`，20,830 字节 | **不准确**。第 9 行称"本次只发布汇总报告"，但候选新增了代码、协议、审计记录与逐 seed 结果记录，而基线本来就跟踪了结果与 checkpoint。 |
| 未暂存修订 | 工作树 SHA-256 `5f36d00f125caa2b58796a44687b959e406d43e248b140f9d11d4f84660bf70b`，20,946 字节 | **准确**。改为"发布与数据边界"：候选含代码、协议、审计记录及汇总/逐 seed 结果；不新增原始行情、逐键预测、checkpoint 或权重；历史已跟踪部分数据、结果与 checkpoint；CDD 与 Bitstamp 派生成果仍需分别审查。 |

对未暂存修订逐条核对：

- "候选包含代码、协议、审计记录及汇总和逐 seed 结果记录"——与第 3.1 节的文件类型计数一致。
- "候选不新增原始行情、逐键预测、checkpoint 或模型权重"——177 条路径中无 `.npy/`.npz/`.pth/`.pt`，四个 CSV 均为结果/登记表。
- "仓库历史中已经跟踪了部分数据、结果和 checkpoint"——见第 4 节计数。

因此：该修订文本可以接受，但**它描述的是候选**。只有候选本身获准提交时才应随候选一起暂存；本轮不把它单独落进 `main`，以免 `main` 的 README 描述一个不存在的合并。

## 4. 历史已跟踪清单（`87bc113`）

| 范围 | 已跟踪文件数 |
|---|---|
| 全库 | 1,563 |
| `results/` | 705 |
| `checkpoints/` | 36 |
| `dataset/`（日频 OHLC CSV） | 61 |
| `data/raw/yahoo/` | 2 |

这些文件在远程 `main` 上已经可达。它们的存在不证明来源、许可或再分发权，也不因为本轮检查而被追认。

## 5. 逐来源处置

| 来源 | 已核实 | 未核实 | 本轮处置 |
|---|---|---|---|
| CryptoDataDownload（CDD） | 当前 FAQ 与使用条款文本（记录于 `SCIENCE_RECHECK_2026-10-30.md`，本轮未重新抓取）；内部执行记录；派生协议标注 `NOT_RELEASED` | 取得日期条款快照、上游第三方权利、逐成果发布依据 | 原始 OHLC、角色包、逐键数组、checkpoint 保持 local-only；派生汇总与指标 `requires-resolution`；本轮不新增公开 |
| Bitstamp API（raw48） | 本地有界执行记录；预测与指标可复算 | 再分发权、取得日期条款、逐成果发布依据 | 原始与派生均保持 local-only；本轮不新增公开 |
| Yahoo（历史同名数据） | 仅知 `data/raw/yahoo/` 两个元数据文件已跟踪 | 获取路径、权利、代表性 | local-only；不据此挑选资产或比较 |
| 公开代码 / 论文 | 代码来源与许可证记录在仓库；DeReFusion 与 THUML 库为独立研究使用 | 论文实际运行配置仍未完全解消 | 代码许可与数据权利分开处理；不把代码许可扩展到数据 |

CDD 的三条现行表述（可发布研究成果、不得再分发原始数据集、条款限制商业使用并提示第三方权利）**不能合并成"已获发布许可"**。它们指向的是"研究成果可以发表、原始数据不可以再分发"，而逐成果是否属于可发表的研究成果仍需要单独判断。

## 6. 逐成果处置

| 对象 | 状态 | 本轮处置 |
|---|---|---|
| 61 份 OHLC 原始 CSV（已跟踪） | 权利未闭合 | 保持原样；不作为新发布依据 |
| CDD 角色包、逐键预测、checkpoint | local-only | 不发布、不复制、不重写 |
| CDD 派生汇总与指标（候选与历史报告） | 权利未闭合 | 不进入新的公开候选；候选整体未获批 |
| raw48 预测、指标与派生摘要 | 权利未闭合 | 仅内部描述性使用；不新增公开 |
| 177 路径候选中的文档、协议、审计 | 152 条默认 `review-required` | 逐路径裁定前不提交、不发布 |
| 历史已跟踪 `results/`、`checkpoints/` | 既有历史暴露 | 保留原样；不作为新发布依据 |
| 9 份本地审阅记录（目录名 kimi，正文自称 DSH 独立复核） | 哈希匹配、本地未跟踪 | 不发布；如需发布须先脱敏并单独批准 |
| 2 份 DSH 原始数组审阅原件 | 本机未找到 | 标"不可核验"；不重建、不冒充 |
| 本轮新增代码与治理文本 | 项目自有文本 | 不含第三方数据；随分支提交，是否对外发布仍由项目决定 |

## 7. 审阅证据补充

14 项阶段报告输入的重查结果（`EVIDENCE_SUPPLEMENT_V2.json`）：

- 12 项存在于主检出且 SHA-256 匹配；0 项存在但哈希不符；2 项缺失。
- 3 项在候选 index 中；9 项为本地未跟踪材料；2 项标 `missing-not-verifiable`。
- 凭据样式命中总数 0；9 项本地材料中 4 项含本地绝对路径（需脱敏后才可能发布）。

两项缺失原件：`.../dsh_raw_array_review_v1/RAW_ARRAY_AUDIT_REPORT.md` 与同目录 `DELIVERABLE_HASHES.json`。本轮在项目目录与 `.codex/visualizations` 下按文件名再次搜索，未找到。**不重建、不推断其内容。**

需要明确的归属问题：9 份本地材料所在的目录名为 `..._kimi_...`，但文件正文自称 "DSH independent read-only reviewer"。字节身份可以核验，**作者身份与独立性不能由仓库内文件自证**。主审阅者本轮新做的数组与指标复算属于**新的独立证据**，不是对历史 DSH 审阅的复现或替代。

## 8. 未解决事项

1. 逐成果的发布裁定（CDD 与 Bitstamp 分别、按文件与指标）。
2. 177 路径候选的完整语义、权利与安全审阅。
3. 两份 DSH 原件的定位或"永久不可核验"的正式记录。
4. 外部 PR #2 的报告表述与其跟踪清单不一致问题（本轮未查询该 PR 状态）。
5. `check_artifact_boundary.py` 的 `review-required` 默认项没有逐项决策机制。
