# 阶段报告审阅证据补充 V1 — 2026-10-30

**状态：** 证据清单，不是审阅复现。本文件与 `EVIDENCE_SUPPLEMENT_V2.json` 只记录字节身份与处置分类。

## 1. 方法

对 `docs/DRF_SHRINK_STAGE_REPORT_1830_V1_2026-10-13_HASHES.json` 声明的 14 项输入：

1. 在主检出按声明路径读取，重新计算 SHA-256；
2. 在隔离候选工作区用 `git cat-file -e :<path>` 判断该路径是否在 index 中，并取 blob id；
3. 对存在的文件统计行数、字节数、凭据样式命中数、是否含本地绝对路径；
4. 不为任何文件建立副本，不把正文写入清单。

生成脚本：`build_evidence_supplement.py`（同一目录）。清单中的绝对路径被刻意省略，只写明"主检出"与"隔离工作区"。

## 2. 结果

| 项 | 数量 |
|---|---|
| 声明 | 14 |
| 存在且哈希匹配 | 12 |
| 存在但哈希不符 | 0 |
| 缺失 | 2 |
| 在候选 index 中 | 3 |
| 本地未跟踪（不发布） | 9 |
| 不可核验 | 2 |

阶段报告本身的 SHA-256 记录在清单的 `subject_report_sha256` 字段。

## 3. 2 项缺失原件

- `research_work/project_management_2026_10_10/shrink_exploration_2026_10_13/dsh_raw_array_review_v1/RAW_ARRAY_AUDIT_REPORT.md`
- `research_work/project_management_2026_10_10/shrink_exploration_2026_10_13/dsh_raw_array_review_v1/DELIVERABLE_HASHES.json`

本轮再次在项目目录与 `.codex/visualizations` 下按文件名递归搜索，未找到。处置：标记 `missing-not-verifiable`，不重建、不推断、不以新做的复算冒充原件。

## 4. 9 项本地材料

分成两个目录：

- `stage_review_kimi_2026_10_13/`：`STAGE_REVIEW_REPORT.md`、`STAGE_REVIEW_LEDGER.json`、`INPUT_HASHES.json`、`DELIVERABLE_HASHES.json`
- `stage_review_followup_kimi_2026_10_13/`：`FOLLOWUP_REVIEW_REPORT.md`、`NEXT_STAGE_MINIMAL_PLAN_V1.md`、`DECISION_TABLE.json`、`INPUT_HASHES.json`、`DELIVERABLE_HASHES.json`

逐份检查的结论：

- 字节身份：全部与阶段报告声明一致。
- 内容性质：审阅报告、审阅台账、输入哈希清单、交付哈希清单、一份标注 `DESIGN_ONLY / NOT_AUTHORIZED` 的下一阶段设计稿。
- 敏感信息：凭据样式命中 0；4 份含本机绝对路径。
- 来源：文件正文自称 "DSH independent read-only reviewer"，所在目录名却是 `..._kimi_...`。**目录名与自称身份不一致**，因此不把它们表述为已验证的 Kimi 审阅或已验证的 DSH 审阅。
- 发布范围：不发布。任何发布都需要先脱敏（去本机路径）、再逐份裁定，并需要原作者/委托方确认作者身份。

## 5. 独立性声明

- 这 9 份材料是**历史**审阅记录，其独立性、作者与完整性无法由仓库内字节自证。
- 主审阅者在 `SCIENCE_RECHECK_2026-10-30.md` 中记录的数组与指标复算是**新的证据**，不是对历史 DSH 审阅的复现，也不继承其结论。
- 数值复算一致只说明"保存的字节与声明的协议/算术一致"，不说明第三方来源、发布权利、跨硬件等价或科学有效性。
