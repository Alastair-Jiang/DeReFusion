# 实验管理与证据标准

## 状态与身份

协议：draft → reviewed → approved_design → stage_released → closed/superseded。Attempt：planned → started → completed_unreviewed / failed / interrupted → validated / rejected。运行完成、产物接收、结构验收和科学可用是四个不同字段。目录数、receipt 数和不同文件哈希数都不是独立实验数量。

logical_run_id 绑定协议版本、数据快照、资产、模型、跨度、seed 和配置；attempt_id 标识一次实际执行。重试新建 attempt，写 `supersedes_attempt` 与原因，不覆盖旧 checkpoint/日志，不选择最好的一次隐藏其余失败。只有身份和预定重试规则满足时才可替代失败 attempt。因效果不佳不能重试。

每次运行保留：起止时间、仓库/源码/配置/协议/数据/环境身份、设备、命令的脱敏版本、随机源、分割键、实际 optimizer steps、早停轨迹、选中 checkpoint、资源消耗、完整预测键和产物 manifest、退出原因。授权 commit 不自动等于执行代码 commit。

## 验收

元数据 join 在 [receipt_manifest_join.json](receipt_manifest_join.json) 中：729 条 receipt 路径中 728 条分别唯一对应一个计划行，但只覆盖 675 个不同计划行（A 15、B 300、C 360、D 0；总计划数 819）。A 的 28 条 calibration receipt 对应 15 个计划 ID，其中 13 条没有逻辑运行 ID。另有 5 个 quarantine receipt 是与原 attempt 字节完全相同的副本，不计作新尝试。1 条 resource_blocked 无运行身份。699 条 completed 状态仍未复核。这个身份 join 不验收 attempt；数值与产物内容尚未审查。

关联的环境和产物文件身份见 [receipt_environment_artifact_index.json](receipt_environment_artifact_index.json)：700 条含环境指纹哈希的 receipt 可匹配本地 fingerprint 文件；3,637 个声明产物按文件名均存在。产物内容哈希未重算，不能据此认定产物有效或数值正确。

结构验收检查文件完整性和身份；数值验收必须另有授权，检查共同键、真值一致、尺度、指标重算和非有限输出；研究验收再检查预注册、测试暴露和主张范围。合成测试不证明真实泛化，hash 匹配不证明算法正确。

Stage B 的 245 P4 + 55 RTX8000 是历史覆盖报告，不能直接合并模型排名。Stage C 既有 360 项的描述性验收来自历史报告，本轮未重算；缺少事前 bootstrap/汇总设定不能看完结果再补成确认性。Stage D 的 144 行是计划，本包不启动它。

## R1 近期主线

沿用已批准 `R1-exploratory-small-panel-20261007-v1`：四资产 BTCUSD、ETHUSD、GSPC、N225；OHLC 的 96 行历史预测下一观测行 Close。F/L 为主比较，B 和 persistence 为辅助；主 gain 为 MSE(L)−MSE(F)。F−B 同时改变多个因素，不能单独证明非线性机制。

训练目标日期 [2018,2023)，验证 [2023,2024)，测试 [2024,2026)，另逐年报告 2024/2025；不把三 seed 或重叠键当独立市场样本。不跨资产合并显著性，不自动做功效分析。当前历史已暴露，保持探索性。

按顺序完成：来源及内部使用依据 → 保管人 QA → 固定切分/行/键身份 → 精确 F/B 合成生命周期独立复核 → T0 接口负例 → 合成资源检查和可执行 manifest → 拟合 release → 验证选择并冻结 → evaluator release → 全量分层报告。

T0 是可信操作者下防误操作：输入 allowlist、禁止 worker 使用 test 路径、冻结前禁止 evaluator、错键/错 hash/混角色包拒绝。不宣称同用户恶意进程隔离，不要求无关的 OS 账号或加密签名认证。

R1 批准设计的硬上限：CPU、1 个并行 fit、2 线程、0 data workers、神经 float32、ridge/汇总 float64、累计 12 小时、每神经 fit 30 分钟、付费 0；计划 24 神经 fits、24 ridge 候选求解、4 个选中 ridge、24 个选中神经模型，persistence 无拟合。24×30 分钟正好占满 12 小时，没有为 ridge、评估和汇总留时间。release 前必须用合成计时估算各阶段耗时、保留失败/收尾余量，并确认总估算在 12 小时内；如果不成立，先拟新协议 amendment 或重排工作，不能改写旧批准设计。超时保留 incomplete，不静默更换设备或参数。

冻结摘要状态链有未解释的历史差异：HEAD 中摘要写 `frozen_pre_authorization`，该提交可见的初次生成器写 `frozen_not_yet_authorized`，后续授权器原子替换为 `authorized_nonconfirmatory_execution`。首段真实来源未知；dirty 工作区值不能补足生成证据。仓库内未找到读取该摘要的执行门禁；外部消费者未知。不得依靠该摘要放行，直至找回来源，或将其明确标为不可重建并由新追加事件承接。

研究改动形成 amendment：触发原因、旧/新版本、已看信息、受影响运行、是否另建探索性系列。下一次独立确认需要新的事前汇总/区间/成功判据和数据选择依据；不能重命名旧测试数据获得“未暴露”身份。
