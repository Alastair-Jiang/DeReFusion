# 仓库与数据管理

## checkout 和写入

主路径为 `[local repository root withheld]`。任务启动记录 toplevel、branch、HEAD、工作区状态和输入 SHA-256；结束再次检查。分配并发任务时使用各自 checkout 和具名输出范围。禁止两个 agent 同时改同一文件。

其他 checkout 采用顺序：记录双方 HEAD → 同名文件 raw SHA-256 → 文本 diff 与来源核对 → 选定版本 → 新候选路径 → 验证 → 审核后集成。若需要换行规范化哈希，另列算法，不能代替 raw hash。不得直接复制覆盖主仓库、冻结文件或用户已有改动。`.codex/worktrees/40a7` 的三份审查候选仍未导入；需要时按此流程单独采用。

## 目录职责和渐进整理

| 现有路径 | 角色 / 处理 |
|---|---|
| models、layers、exp、data_provider、utils | 活动实现；每次实验绑定具体源码而非仅模型名 |
| docs/management/v1_1 | 当前修订候选；v1 为 DSH 已审原样版本，v1.1 待新哈希复核 |
| docs 中预注册、决策 | 科学控制记录；用追加 amendment/release 引用旧哈希 |
| research_work/forward_increment | 未提交候选、合成证据；按现有路径引用，不批量移动 |
| reproduction/results、results、checkpoints | 历史运行与产物；先索引、去重关联，后决定归档；不能按目录名推断都被忽略 |
| dataset | 历史数据快照；不原地清洗、重下载覆盖或删除 |
| research_work/project_management_2026_10_10 | 本地详细盘点；不直接全量发布 |

新实验建议采用 `research_work/runs/<protocol_id>/<logical_run_id>/<attempt_id>/`；原始数据的新快照放入经明确选择的本地数据根，按 `provider/snapshot_id/` 分层。路径本身不保证被 Git 忽略，建立前检查 `git check-ignore`，提交前检查实际 index。旧实验不为统一外观而搬家，目录索引优先于物理迁移。

## 数据合同

每份数据至少记录 dataset_id、供应商及证券代码、下载工具和版本/提交、获取时间/操作者、原始响应与派生文件身份、时区/交易日历、频率、列映射、单位/货币、复权方式、缺失/重复/非正值/异常处理、内部使用依据、原始再分发与衍生产物许可、证据路径及哈希。

`datasets.csv` 中 registry_sha256 是历史登记表的陈述，本轮没有读价格文件重新计算；git_blob_oid 也不是 raw SHA-256。空值是明确待补，不得填写猜测。用户回忆四个 R1 文件由某 agent 找来，只能记录为用户回忆。脚本列出 ticker 只证明存在获取路径，不能证明当前文件来自那次执行，尤其脚本会跳过已有文件。

本轮新增来源线索：提交 `d89bee8c5c61717e78d56a1366ef9624781cbf1d` 的说明和三版 fetch_dataset 脚本提到原始十资产的 Yahoo 获取路径；fetch_candidate_pool 列出 N225 等 Yahoo 代码；fetch_pool_sohu 两个脚本与结构验证预注册记述 Sohu 扩展池。61 个资产均能关联到至少一个脚本候选，但部分资产同时出现在多个来源脚本中，因此台账保留全部候选。既有“41 份来源未知”审查仍作为历史记录保留；新增线索没有把任何一份升级为逐文件获取证实或许可通过。

权利台账数字口径：历史审查的 20 行是 `c1-20` cohort 级 Yahoo 指定，41 行当时 supplier 未建立；本台账 30 行提到 Yahoo，是脚本 ticker 候选与该 20 行 cohort 线索的并集。多出的 10 行仅为脚本候选，未升级为逐文件来源证据。61 份的实际 acquisition linkage 和内部/公开许可仍为 `UNVERIFIED`。

质量检查采用新 QA release：保存报告，不修改原始值。变换输出使用新的 snapshot_id，记录 parent hash、变换源码和配置哈希。异常 FX 包络、WTI 非正值等历史报告需追溯，不静默修正。对每个新协议决定哪些异常可接受，不能根据测试效果选择处理方式。

切分以目标日期和预测键决定；生成 train/validation/test 的键、行绑定、样本数量和 hash。标准化只拟合 train，选择只看 validation，test 由保管人交给冻结后的 evaluator。可信角色可持有完整源哈希，fit worker 只接收 train/validation 身份。每次接触测试信息记录 exposure 事件。

## Git、公开材料和恢复

普通发布流程：精确文件 allowlist → 本地结构验证 → 独立复核指定包哈希 → 检查 staged diff/name/status/大小 → 查秘密、绝对本地敏感路径、数据许可和二进制产物 → 核对远程和分支 → focused commit → 普通 push → 核对远程 commit。禁止 `git add .` 批量接收未知运行材料。未提交依赖必须随审核包发布或在公开说明中明确不可复现的缺口。

现有 tracked 数据和二进制需要专项发布审查。仅新增 `.gitignore` 不能撤回已跟踪对象；只删除工作树文件也不能消除历史或独立 fork。处理公开历史是另一项有备份、有影响清单的工作，不能在本次脏工作区直接重写或清理 `.git`。

备份标准：运行前核对可用磁盘和输出预算；数据/协议/产物至少保留两个独立位置的副本，记录 manifest、hash、介质/位置、时间和恢复演练结果。未验证副本不得宣称已备份。原始数据和已报告产物不自动过期；临时/cache 文件仅在确认所有权、依赖和恢复能力后清理。当前备份与恢复演练尚未核实，列入缺失项。

凭据只用环境或系统凭据引用，不写日志、报告、Git。环境记录采取包版本和设备信息允许清单，不转储整个环境变量。完整路径与 receipt 索引默认本地保管；对外发布摘要与必要的脱敏索引。
