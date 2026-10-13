# DSH 对管理包 v1 的审查意见与 v1.1 处置

依据：用户提供的 DSH 独立报告，检查时段 2026-10-10 18:38:51–18:44 +0800，报告 SHA-256 `422091f45a920ac23867749e84cc606205ce5ff8202cf58923254c79e04c470d`。审查对象 manifest SHA-256 `4a0601afe97b5700d0836e3b4bdeab28bed278bc06430d2160cfc0a038dccde8`。v1 原样备份见本地 `research_work/project_management_2026_10_10/followup_after_dsh_review/management_v1_as_reviewed/`。

| DSH 项 | 处置 | v1.1 记录 |
|---|---|---|
| P0-1 文件集合漂移 | v1 当时多出 8 MB 环境/产物身份索引；审查后已移出 v1，现 v1 目录重新匹配原 manifest。v1.1 明确纳入索引并重新生成 manifest | 本文件、`hashes.json` |
| P1-1 728 条映射会误读作 728 个不同计划行 | 修正 join：每条 receipt 保存 row key、manifest 行号和 manifest SHA。728 条唯一 receipt→行映射覆盖 675/819 行；A 15、B 300、C 360、D 0 | `receipt_manifest_join.json`、`README.md`、`EXPERIMENTS.md` |
| P1-2 HEAD 冻结状态无 writer 来源 | 记录 HEAD `frozen_pre_authorization` 与已提交 writer `frozen_not_yet_authorized` 不一致；首段来源 UNKNOWN；不依赖摘要放行，不改原件 | `EXPERIMENTS.md`、`gaps.json`、`PLAN_AND_GAPS.md` |
| P1-3 R1 预算无余量 | 12 小时是原批准硬上限；24×30 分钟正好耗尽全部上限。保留批准设计，不擅自加时；fit release 前须合成计时并证明所有阶段和余量可纳入，失败则先提 amendment | `EXPERIMENTS.md`、`gaps.json` |
| P2-1 5 份相同 receipt 未解释 | 记录为 4 组、5 个额外 quarantine 文件，与对应 attempt receipt 字节一致；不是新增 receipt 身份。原始 attempt 留存 | `receipt_manifest_join.json`、`README.md`、`EXPERIMENTS.md` |
| P2-2 Yahoo 30 行与历史 rights 台账 20/41 未对账 | 解释 20 是 cohort 级历史 designation；30 是脚本 ticker 候选与 cohort 线索的并集；多出的 10 只算脚本线索，不证明文件来源或许可 | `REPOSITORY_AND_DATA.md`、`datasets.csv` 保持逐行未知状态 |
| P2-3 Git/walk 未跟踪数差 10 未解释 | 用快照目录现存的两个前置快照 4+6 文件，解释 walk 排除整个输出树而 Git 计入先前文件；保留两种计数及口径 | `README.md`、`baseline.json` |
| P2-4 时间点不一致 | 明确 18:24 快照为 5 个已跟踪改动；README 管理入口 18:34 后加入；DSH 18:38 时看到 6 个。冻结链重点文件另说明，不再把范围数写成全仓库总数 | `COORDINATION_FINDINGS_2026-10-10.md` |
| 冻结摘要初次写入 | 接受 DSH 对旧报告措辞的更正：初次生成器只新建目录/文件，授权器通过原子替换同一路径；仓库内无 reader。外部消费者 UNKNOWN | `COORDINATION_FINDINGS_2026-10-10.md`、`EXPERIMENTS.md` |

本次状态没有更改 approved design、Phase 1 manifest、receipt、授权摘要或历史运行产物。环境/产物关联只是哈希引用与文件名/大小存在检查；没有重算 payload hash。DSH 报告也发现其他 checkout 不能穷尽；此限制仍然存在。

修订版 v1.1 目前是未提交候选，须以其全新 `hashes.json` SHA-256 交 DSH 再审。只有该复核闭环后，才按项目发布流程评估管理文档提交。
