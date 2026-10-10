# 并行工作底稿：receipt 对账与冻结摘要写入链

检查时点：2026-10-10。仓库 `[local repository root withheld]`，分支 `docs/project-status-catalog-2026-10-10`，HEAD `8953da122bd5fca293f8c2d68e166e53138403a5`。只读检查 manifest 与 receipt 的白名单元数据、Git diff 和相关 Python 写入路径；没有打开价格、预测/真值数组、权重或运行日志，没有启动实验。接收器修改与 receiver test 属于开始任务前已有工作区变更。

## Receipt 与计划行

`receipt_manifest_join.json` 按协议、stage、asset、model、horizon、seed、origin，把快照中的 729 条 receipt 元数据和四份 Phase 1 manifest 关联：819 个计划行。728 个 receipt 路径各自唯一映射至一行，但不同计划行覆盖数是 675：A 15/15、B 300/300、C 360/360、D 0/144。状态陈述为 calibration_pass 28、completed_unreviewed 699、resource_blocked 1、interrupted 1。28 条 calibration receipt 对应 15 个逻辑 ID，其中 13 条没有 run ID。

724 个不同 receipt 文件哈希中有 4 组重复，产生 5 个额外 quarantine 文件；这些副本与各自 attempt 下的 receipt 字节一致，attempt ID 相同。计数是文件/receipt 路径，不是新增运行次数。

`planned` 是源 manifest 原值。这项 join 只证明 receipt 与计划身份可对上，不证明文件内容哈希、模型输出或运行科学上有效；699 仍是未复核完成陈述。它也没有将不同设备轨道合并。详细逐条记录、manifest 哈希、receipt 元数据索引哈希保存在 JSON 文件中。

## 冻结摘要写入链

盘点快照在 18:24 +0800 记录了 5 个已跟踪文件修改；根 README 的管理入口于 18:34 后新增，DSH 18:38 检查时共见 6 个。本文第一次检查时也见 6 个。此前 focused diff 涉及 receiver、freeze-summary、receiver test 三个文件；它们不是全仓库改动总数。`freeze-summary.json` 一直是既有 tracked diff，本任务没有编辑。

HEAD 中摘要状态是 `frozen_pre_authorization`；DSH 核对已提交的初次生成脚本实际写 `frozen_not_yet_authorized`，后续授权脚本原子替换为 `authorized_nonconfirmatory_execution`。首段真实来源未能从已提交代码还原。dirty 工作区值不能补足生成记录。DSH 用历史哈希旁证该 dirty 文件早于本轮任务。

代码检索发现两个写入路径：

1. `reproduction/batches/freeze_local_5060_supplement.py` 创建新的输出目录（`mkdir(exist_ok=False)`），用 `write_text` 初次写 `freeze-summary.json`。若目录已存在脚本会停止，因此这条路径不会覆盖现存摘要。
2. `reproduction/batches/write_local_5060_authorizations.py` 读取摘要、加上授权状态和授权文件哈希，通过临时文件、`fsync`、`os.replace` 原子替换摘要。这确实会替换同一路径的字节内容。

在仓库生产代码、测试及文本检索中未发现此摘要的读取者；可见授权入口分别创建授权 JSON。仓库外消费者未知。证据支持“一个脚本仅初次创建、后一个脚本原子替换同一路径”，不足以证明摘要被执行门禁消费。授权记录及 dirty diff 的审批链仍需核对。应使用追加事件或不同版本路径改善历史可追溯性；不要改写既有文件。

## 复核边界

DSH 审计输入 SHA-256 为 `422091f45a920ac23867749e84cc606205ce5ff8202cf58923254c79e04c470d`，检查 HEAD 为 `8953da122bd5fca293f8c2d68e166e53138403a5`。报告确认先前“两个脚本都覆盖”的说法不准确。v1.1 已按该报告修订，须以新 manifest 哈希再审。

## 其他 v1 修订依据

- Git/walk 未跟踪计数差 10 可由快照时间点解释：collector 创建新输出目录后先枚举 Git，之后才写本次输出；当时输出根内已有两个前序目录，各含 4 和 6 个文件。Git 计入这 10 个文件，而递归 walk 排除整个输出根。
- 数据台账中的 30 个 Yahoo 提及是脚本 ticker 线索与历史 cohort 声明并集；权利审查台账的 20 是 `c1-20` cohort 级 Yahoo 指定，另外 10 项未升级为逐文件来源证据。
- R1 12 小时仍为批准设计硬限制。按每个神经拟合最慢 30 分钟计算，24 个拟合耗尽全部预算；尚无 ridge、评分、汇总和余量耗时证据。因此 v1.1 添加 fit release 前置条件，未修改已批准设计。
