# Phase 1 现有数据可用性与复用盘点（2026-09-30）

**范围：** 盘点仓库中现成的 Phase 1 清单、intake、attempt 产物、分析摘要和授权状态，判断哪些问题可由现有数据回答。此盘点不读取 Stage B 测试分数、不启动训练、不移动或改写原始产物，也不修改现行协议。

## 结论摘要

当前无需先重跑完整 Stage B。现有数据最实际的用法是：

1. 把 Stage C 作为 DeReFusion 与 RevIN-DLinear 主问题的现成配对证据；配对和数值完整性已复核，但目前只有分层描述性点估计，缺少事前固定的 bootstrap 参数，不能当作确认性区间结论。
2. 将 Stage B 的 P4 轨道单独处理：其中 240 个非 TimesNet 设置形成完整的 4 模型 × 30 资产 × 2 horizon 同轨子面板，可在明确标为探索性的前提下，复用预测/真值/指标产物，不必重跑。具体分析前须核实并冻结 estimand、分层和多重性规则。
3. RTX8000 的 55 个 TimesNet 设置保留为独立补充数据，适合运行可行性、耗时和该轨道自身的描述性审查；不能拿来填补 P4 的 TimesNet 面板并与 P4 模型排名。
4. 暂缓 Stage D。144 个冻结设置仍是 planned，且无专属授权；只有明确的时间稳健性问题需要它时，再另立执行决策。

## 现有数据盘点

| 阶段/轨道 | 实际可用量 | 已验证内容 | 可回答的问题 | 主要限制 |
|---|---:|---|---|---|
| Stage A GPU calibration | 15/15 | `calibration_pass` receipts | 代码/环境/产物保留/运行可行性校准 | 按预注册不比较 calibration loss，不作模型效果证据 |
| Stage A CPU 辅助轨道 | 13 pass、1 resource-blocked、1 缺 receipt | 有单独偏差记录 | 历史实现和资源诊断 | 与 P4 GPU 不同机器/构建；含执行偏差；不并入正式 GPU 校准或效果比较 |
| Stage B P4 主轨 | 245 个 eligible，其中 240 个非 TimesNet，5 个 TimesNet | intake 0 issues；完整 receipt、哈希和日志核验；四个非 TimesNet 模型各覆盖全部 30 资产 × 2 horizon | 240-fit 同一 P4 轨道的四模型探索性比较；本轨训练耗时和技术失败审查 | 原授权仍是 partial；无 P4 TimesNet 完整面板；分数尚未进入技术收口分析 |
| Stage B RTX8000 补充轨 | 55/55 TimesNet eligible | 最新 intake 0 issues；补充清单和产物一致 | TimesNet 补充轨自身的完整性、运行时间、描述性误差分布 | 不与 P4 pooling、排名或声称硬件数值等价 |
| Stage C RTX 5060 Ti | 360/360；180 个 DLinear/DeReFusion 配对 | 1,080 个数值文件哈希、配对 keys/targets 和 MSE 复算通过 | 主模型对按 cohort、horizon、seed 的配对描述性结果；数据完整性复核 | 预注册缺少 bootstrap seed、重采样数、区间算法和跨 horizon/seed 汇总规则；现有点估计不是确认性区间结论 |
| Stage D | 0/144 | 冻结 manifest 全部 planned；未发现专属授权或 attempt | 暂无结果可用 | 不应按现授权启动 |
| 本机 Intel Arc 140T | 非 Phase 1 训练数据 | 隔离 XPU 环境设备发现及基础 tensor 前后向探针通过 | 后端适配可行性调查 | 仓库训练入口未支持 XPU；探针不验证完整模型或实现保真；旧 NVIDIA 授权不适用 |

## 可调整的分析路线

### 路线 A：先利用 Stage C 回答主模型问题

Stage C 已有同一执行轨道上的 360 个训练设置，覆盖 30 个资产、两个 horizon、三个 seed；配对 prediction keys、真值和保存/复算 MSE 已通过核验。现成报告给出 12 个 cohort × horizon × seed 分层点估计，没有把 horizon/seed 事后合并。

**可立即使用：** 完整性证据、资产级配对数据、已报告的分层描述性点估计。

**不可直接声称：** 已满足确认性 bootstrap 区间判据或总体优越性。先查有无结果查看前形成且可验证的 bootstrap/aggregation 记录；若没有，保留描述性定位，不从当前结果反推统计参数。

### 路线 B：复用 Stage B 的 P4 四模型子面板

240 个 P4 非 TimesNet fit 是现成、全覆盖的同轨子面板。其逻辑网格可由冻结清单和 P4 intake 确定，不依赖分数筛选模型或资产。可先只读核对四模型预测键、真值、指标和哈希是否两两兼容，再冻结一个**探索性、限 P4 的**分析定义后提取指标。

这个分析可以增加现代 baseline 的上下文，并直接复用 240 个 fit；它不等于原始五模型完整 Stage B，也不产生确认性结论。multiplicity family、估计量汇总和区间细节如不能从已有预注册唯一恢复，应先标为 `TBD`，不得看完分数再定。

### 路线 C：保留 RTX8000 TimesNet 轨道的独立用途

55 个包可用于该轨的可用性、训练时间和完整性；也可对该轨全部固定数据作单模型描述性汇总，但结果须保持轨道标签。若研究问题要求和四个 P4 模型直接作完整排名，这 55 个包不能提供所需同轨比较。

### 路线 D：Stage D 先不做

Stage D 没有结果产物，也没有执行授权。它只服务于预注册的时间稳健性问题；若当前重点是主模型对或 modern-baseline 描述，先不投入这 144 个 fit 更合适。若之后仍需要时间稳健性结论，再先解决统计规则、执行授权和资源计划。

## 建议的低成本推进顺序

1. 保存本盘点作为数据入口；保持所有原始 attempt、receipt 和数组原位只读。
2. 对 Stage B P4 的 240 个候选包做纯完整性/配对兼容性核验，不读分数；整理为固定 eligible-ID 列表。
3. 复核 Stage C bootstrap/aggregation 的仓库历史及可验证外部记录。若无记录，保留点估计为描述性证据，不事后造参数。
4. 在任何 Stage B 指标被读取前，确定是否需要一份版本化的限 P4 探索性分析计划；计划应固定所有 240 个设置、cohort 分层、比较 family、缺失处理和输出措辞。
5. 只有当现有数据无法回答明确的新问题时，才考虑新训练；届时用新轨道/授权，不覆盖旧结果。完整 300-fit 单硬件复做属于备用选择，不是默认下一步。

## 证据入口

- Stage B 覆盖与 pooling/ranking 限制：`stage-b-coverage-audit-20260930.md`。
- Stage B 分轨运行时、245+55 组成和技术核验：`stage-b-technical-closeout-20260930.md`、`stage-b-runtime-by-track-20260930.csv`、`stage-b-runtime-setting-ledger-20260930.csv`。
- Stage C 配对数据、描述性点估计和区间限制：`stage-c-descriptive-review-20260930.md`、`stage-c-descriptive-estimates-20260930.csv`、`stage-c-asset-paired-estimates-20260930.csv`。
- Stage D 与 XPU 门控：`phase1-next-steps-gate-20260930.md`、`stage-b-local-intel-xpu-readiness-20260930.md`。
- 冻结目标和统计方案：`docs/PHASE1_PREREGISTRATION.md`。
