# 独立只读复核报告 — `docs/management/v1_1`（Codex 对 v1 审查的处置）

> 公开脱敏副本：本机仓库绝对路径已替换为 `[local repository root withheld]`。本文件不是收到报告的逐字节原件；源报告 SHA-256 与本副本 SHA-256 分别记录在同目录 `baseline.json` 的 `dsh_review_v1_1` 中。正文中的审查结论与证据内容未作改写。

## A. 检查身份与范围

| 项 | 值 |
|---|---|
| 检查时间 | 2026-10-10 18:54:57 – 18:57:47（+0800） |
| 真实路径 | `[local repository root withheld]`（`git rev-parse --show-toplevel` 一致） |
| 分支 | `docs/project-status-catalog-2026-10-10`（上游 `origin/docs/project-status-catalog-2026-10-10` = `8953da1`）；`origin/main` = `0017172…` |
| HEAD | `8953da122bd5fca293f8c2d68e166e53138403a5`（tree `6dc4d57f…`）——与任务给定一致，检查期间未变 |
| 实际 manifest 哈希 | `docs/management/v1_1/hashes.json` = `ec414113e75e0068b96fe85e76b3b20c43c3ae6f9417493d05ed2f206cea71b4`（18:54:57 与 18:57:47 两次一致）——**与给定 pin 逐位相同** |
| 包清单自洽 | listed 20 / present 20 / unlisted 空 / hash mismatches **0**；`git ls-files docs/management` = 0（确为未提交候选） |
| 工作区状态 | 6 个已跟踪文件未暂存修改（`README.md`、两份 2026-10-10 文档、receiver、`freeze-summary.json`、receiver test）；0 已暂存；`README.md` mtime 18:34:07（= v1 审查期间已记录的漂移） |
| 检查范围 | v1_1 全部 20 个 pinned 文件；`baseline.json` 全部 pin（31 输入 + 53 证据 + 14 模型源 + 5 既有修改）；`receipt_manifest_join.json`（729 条全量重算）；`receipt_environment_artifact_index.json`（结构 + 全量汇总重算 + 6 条环境哈希抽检 + 1 条产物字节抽检）；A–D manifest；v1↔v1_1 逐文件比对；`verify_package.py` 全部检查项的**独立复现**；两处 writer 源码；`management_v1_as_reviewed` 备份 |
| 未做 | 未修改/提交/推送；未运行包内脚本或 `verify_package.py`（改为逐条独立复现）；未读数价格、预测/真值、checkpoint、日志正文、凭据；未联网 |

**漂移**：无影响本次判断的漂移。两处需登记：① 受审对象 `docs/management/v1` 在 v1 审查**之后**被改动（8 MB 索引被移出，目录由 19 文件回到 manifest 的 18 文件；`hashes.json` 仍为 `4a0601af…`）；② `dsh_review.report_sha256` 无法在仓库内复核（见 P2-1）。审查继续，不受影响。

---

## B. 逐项复核（PASS / FAIL / UNKNOWN）

| # | 复核项 | 结论 | 证据 |
|---|---|---|---|
| 1 | 包文件完整纳入哈希 | **PASS** | 20 listed = 20 present，0 mismatch；新增 `receipt_environment_artifact_index.json` 已入 manifest（`08894183…` 实测一致）。v1 当时的 P0-1 消除 |
| 2 | v1 目录恢复与原 manifest 匹配 | **PASS** | v1 现 18 文件、listed 18/present 18、0 mismatch、`hashes.json` 仍 `4a0601af…` |
| 3 | 已审版本留痕 | **PASS** | `baseline.json:929` 指向 `…/followup_after_dsh_review/management_v1_as_reviewed`；实测该备份 18 个文件对 v1 manifest **0 mismatch** |
| 4 | 728 条 receipt 各自匹配一行 | **PASS** | `receipt_manifest_join.json` 每条记录新增 `manifest_match.matched_row_key / manifest_path / manifest_sha256 / manifest_data_row_number`；728 条匹配 + 1 条 `resource_blocked` 无运行身份；无一条多匹配、无重复路径 |
| 5 | 只覆盖 675 个不同计划行 | **PASS** | 我按 `matched_row_key` 独立去重：A 15、B 300、C 360、D 0 → **675**；`manifest_data_row_number` 全部在范围内（728/728）；抽查 B 第 3 行，`row_key` 与该行 7 个身份列完全一致 |
| 6 | 4 组重复哈希 = 5 个 quarantine 副本 | **PASS** | 4 组（x2/x3/x2/x2），extra = 5；5 条路径全部位于 `rtx8000-intake-20260929-v2/quarantine/…`，`same_attempt_ids: true`，与对应 attempt 原件字节一致 |
| 7 | freeze-summary 状态不一致标为来源未知 | **PASS** | `EXPERIMENTS.md:33`、`gaps.json:50`（G04）、`PLAN_AND_GAPS.md:44` 均写明 HEAD `frozen_pre_authorization` ≠ 已提交 creator `frozen_not_yet_authorized`，首段来源 UNKNOWN；明确「不得依靠该摘要放行」；无 reader，外部消费者 UNKNOWN |
| 8 | 12 小时硬预算保留 + 计时前置条件 | **PASS** | `EXPERIMENTS.md:31` 保留批准设计硬上限并写明「24×30 分钟正好占满 12 小时，没有为 ridge、评估和汇总留时间」，要求合成计时 + 余量证明；`r1_release_candidate.json` fit 段 `release_preconditions` 新增该条，并加 `revision_note`；已批准设计文件与 12 h 上限**未被修改** |
| 9 | Yahoo 30 行 vs 历史 cohort 20 行 | **PASS** | `REPOSITORY_AND_DATA.md:31`、`COORDINATION_FINDINGS:33` 明确 20 = `c1-20` cohort 级指定、41 = 当时 supplier 未建立、30 = 脚本 ticker 候选与 cohort 线索并集、多出 10 项未升级为逐文件证据；我实测 datasets.csv 中 Yahoo 提及 30 行、历史 cohort 指针 20 行，与表述相符 |
| 10 | Git/walk 计数差 10 | **PASS** | `README.md:27`、`COORDINATION_FINDINGS:32`、`baseline.json:912-916` 均解释为 walk 排除输出根、而当时其中已有两个前序快照 **4 + 6** 文件；我独立确认两目录实际为 4 与 6 个文件，且 collector 在 Git 枚举前先建输出目录（`collect_metadata.py:31` 早于 `:32-34`），解释成立 |
| 11 | 不同盘点时点 | **PASS** | `COORDINATION_FINDINGS:15` 记录 18:24 快照 5 个已跟踪改动、根 README 入口 18:34 后新增、DSH 18:38 见 6 个；与实测 mtime 18:34:07 一致 |
| 12 | 新增环境/产物索引只作元数据说明 | **PASS** | `evidence_level`（索引 L3）= "metadata hashes and filenames/stat only; declared artifact content hashes not recomputed"；每件产物带 `content_hash_checked: false`；`README.md:31`、`EXPERIMENTS.md:15` 明写"按文件名…没有重算 payload 哈希，没有读取日志、checkpoint、预测或真值内容" |
| 13 | 索引数值可复核 | **PASS** | 729 receipt、29 无环境哈希、**700** 匹配、3,637 声明产物 / 3,637 存在 / 0 缺失（我按记录全量重算一致）；651 个 fingerprint 文件实例 ↔ **3** 个不同哈希（未把 651 当成 651 个环境）；6 条抽检的 matched 文件实测 SHA-256 与 receipt 声明值相同；抽检 attempt 的 5 件产物索引字节数与磁盘完全一致 |
| 14 | `verify_package.py` 判定与 v1_1 一致 | **PASS** | 逐条独立复现其全部检查：HEAD 一致、31 input pins、67 evidence/model pins、5 既有修改、61/61 datasets 且 raw sha 全空、18 gaps 无重复无悬空依赖、`DRAFT_BLOCKED`/`execution_permitted=false`/issuer 空、design 哈希与 4 键一致、`real_run_release_issued=false` —— **全部通过** |
| 15 | 未越界为执行放行 | **PASS** | `r1_release_candidate.json` 仍 `DRAFT_BLOCKED`、四阶段 `not_issued`、`authorization.json` `real_run_release_issued=false`、`external_authorization_granted=false` |
| 16 | 数据台账仍未升级未知状态 | **PASS** | `datasets.csv` 与 v1 字节相同（61 行全 UNVERIFIED、`current_raw_sha256` 全空），未因新增解释而改写行级状态 |
| 17 | 被审响应文本自身可核 | **UNKNOWN** | `baseline.json:924` 的 `report_sha256`（`422091f4…`）指向 DSH 报告字节，但仓库内无该副本，无法复算 |

---

## C. 问题清单

### P0
无。

### P1
无。

### P2-1 `dsh_review.report_sha256` 在仓库内不可复核
- **路径/行**：`docs/management/v1_1/baseline.json:923-928`
- **证据**：该键记录 `report_sha256 = 422091f4…`、`reviewed_manifest_sha256 = 4a0601af…`、`conclusion = revision_required`、`reviewed_head = 8953da1…`；其中 manifest/head/conclusion 我均已独立验证，但响应文本本体未随包保存（`followup_after_dsh_review/` 内只有索引、说明与 v1 快照）。
- **影响**：无法证明被引用的 DSH 意见字节与 Codex 处置所依据者相同；若日后出现歧义，无法裁定。
- **最小修复**：把送审时的响应文本（或其中被引用的关键段落）复制到 `followup_after_dsh_review/` 并在 `dsh_review` 中同时记录路径与哈希；否则把该字段改为 "hash of response as delivered, copy not retained"。

### P2-2 受审的 v1 目录在审查后被改动
- **路径/行**：`docs/management/v1/`（目录内容），`baseline.json:929`、`DSH_REVIEW_RESPONSE_V1_1.md:7`
- **证据**：v1 现有 18 文件（审查时含第 19 个 `receipt_environment_artifact_index.json`，现已被移出）；`hashes.json` 未变（`4a0601af…`）；`management_v1_as_reviewed/` 备份与 v1 manifest **0 mismatch**。
- **影响**：低。被移出的文件本不属于 pinned 集合，且原件、manifest、备份三者可互证；但"已送审包的目录可被改动"这一做法本身削弱目录级冻结语义。
- **最小修复**：明确以 manifest + `as_reviewed` 快照为绑定记录（而非目录本身）；后续对已送审版本一律不改目录，修正只进新版本（v1.1 已如此做）。

### P2-3 本地说明的"文件大小核对"措辞强于索引实际字段
- **路径/行**：`research_work/project_management_2026_10_10/followup_after_dsh_review/CODEX_RECEIPT_LINKAGE_NOTE.md:13`
- **证据**：该行写"按 receipt 所在 attempt 文件夹的文件名和文件大小核对，3,637 项都存在"；而 receipt 的 `sha256` 字段只含 name→hash，**不含声明字节数**，索引记录的是 `present` + 实际 `bytes`（无 declared size 可比），包内文本正确地只写"按文件名均存在"。
- **影响**：低（该说明在 pinned 包之外）。若日后被引为包内表述，会构成"做了未做的核对"。
- **最小修复**：把该句改为"按文件名核对存在；实际字节数已记录，未与任何声明大小比对"。

### P2-4（可选增强）包内校验脚本未覆盖新索引的语义
- **路径/行**：`docs/management/v1_1/verify_package.py`（与 v1 字节相同）
- **证据**：脚本只校验文件集合与哈希、pins、datasets/gaps、release 状态；不检查 `receipt_environment_artifact_index.json` 的 `head` 是否等于 `baseline.head`、也不检查其 `evidence_level` 是否仍标注未重算内容哈希。
- **影响**：低（该文件已被 manifest 绑定，完整性有保障；缺的是语义回归）。
- **最小修复**：加两条断言——索引 `head == baseline.head`，且索引内不存在 `content_hash_checked: true`。

### 值得记录的正面事实
- 651 个 `environment_fingerprint.json` 文件实例对应 **3** 个不同哈希（394 / 246 / 60，对应本地 5060 Ti、P4、RTX8000 三条轨道），索引未把文件数当成环境数或运行数。
- join 的 `matched_row_key` 可直接与 manifest 行对齐（抽查一致），使"675"从断言变为可复算量。

---

## D. 结论

**v1 报告中我提出的 8 项问题全部核实已修正**，且修正方式与证据链相符：文件集合漂移消除、join 增加行键/行号/manifest 哈希、675 vs 728 的区分写入三处文档、quarantine 5 份副本有据、freeze-summary 首段来源如实标为 UNKNOWN、12 h 硬上限保留并加计时前置条件、Yahoo 20/30 与 Git/walk 10 两个数字口径均有可复算证据。新增环境与产物索引**确实只作元数据说明**，并显式标注未重算内容哈希，未发现任何"路径级存在"被写成"内容已验证"的表述。

剩余 3 项均为 P2（一项在仓库外说明文字，两项为留痕/脚本增强），不阻断 v1.1 作为管理设计候选。管理包自检脚本的全部检查我已独立复现通过。

**本复核结论不构成 R1 执行放行**：`r1_release_candidate.json` 仍为 `DRAFT_BLOCKED`、四阶段均 `not_issued`、`execution_permitted=false`，任何真实数据 QA、预处理、拟合、冻结或评分仍须另行签发绑定哈希、范围、预算与终止条件的阶段 release；本报告也未验证 699 条 `completed_unreviewed`、3,637 件声明产物或任何历史数值结论的科学有效性。
