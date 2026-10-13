# PAPER_VS_REPO_TABLE — 原论文 vs 当前归档实现（逐项）

- 论文证据：本地全文 `C:\Users\26843\Desktop\project\02_papers\txt\DeReFusion_ASOC_2026_fulltext.md`（SHA-256 `023d1344…0309f5`），行号形如 `L###`；页界标记为"第 N 页"。
- 代码证据：仓库 HEAD `db308d2b3bdf4fc14339ea4652974f4e6765e36c` 下文件路径:行号。归档模型 pin：`models/derefusion/bundle_v3_pin/{DeReFusion.py=468a861d…, derefusion_components.py=91ae3bce…, RevIN.py=a7dc201d…}`；V2 诊断：`…/compression_diagnostic_2026_10_13_v2/run_diagnostic.py=c29e6ed8…`。
- 判定口径：**一致**（可逐项对上）/ **有差别**（已定位差异）/ **未核实**（缺证据）。不据成绩推断机制。

| # | 维度 | 原论文（依据） | 当前归档实现（依据） | 判定 |
|---|---|---|---|---|
| 1 | 研究问题 | 固定架构/数据/协议，**只变融合算子**：直接相加 vs 静态加权 vs 动态门控，十基准受控比较（L97–114；§4.5.2 L868–878） | 项目问题="非线性分支是否在严格时间切分下相对线性基线提供稳定样本外信息"（`README.md:120`；`PAPER_SOURCE_ADDENDUM_CORRECTION_2026-10-07.md:21`）。V2 诊断问题=混合分辨率表示（`PROTOCOL_V1.json.question`） | **有差别**（不同估计目标）；不是论文问题复现 |
| 2 | 数据 | 日线 OHLC，`yfinance`，2016-01-01…2025-12-31；10 资产 BABA/NVO/TM/DJI/GSPC/SOX/BTCUSD/ETHUSD/EURUSD/USDJPY（§4.1 L578–587；Data availability L15192–15198） | V2：新 CDD Bitstamp **ETHUSD 单资产**，计划区间 [2018-01-01,2026-01-01)（`PROTOCOL_V1.json`；`CDD_QUALIFICATION_RESULTS_V1.json`） | **有差别**（来源、资产数、区间均不同） |
| 3 | 目标 | 预测 Y∈R^{T×C}；评估与门控分析在**收盘价（target）通道**（§4.3 Eq 11 L667–679；§4.5.2 L1027、L1046） | 下一完整日 Close；模型出 4 通道，loss 与预测取索引 3（`run_shrink_cdd_v1_1.py:143`；V2 同构） | 通道选择**一致**；论文训练 loss 是否覆盖全部 C 通道**未核实**（Eq 11 形式上是 Y∈R^{T×C} 全体） |
| 4 | 切分 | 时间序 70%/10%/20%（训练/验证/测试）；验证集用于早停；**精确切分逻辑见公开代码**（§4.2 L617–624） | 日期制：训练目标 2018-04-07…2022-12-31（1730 键）、验证 2023 全年（365 键）、test 未读（`CDD_PREPARATION_MANIFEST_V1_1.json`） | 形式**一致**（严格时间序、验证供选择）；**精确切点不同/未核实**（论文交其代码） |
| 5 | 窗口/跨度 | 主 L=96；T∈{1,7,12,24,36}；L 敏感性 {48,96,192}（§4.2 L654–658） | raw96=96 位置/96 天；raw48=48/48；mixed48=48 位置/96 天；H=1（`PROTOCOL_V1.json.arms`） | raw96、raw48、T=1 **一致**；mixed48 是项目自创变体，论文无 |
| 6 | 融合公式 | `F = Y_base + Y_res`（Eq 8 L550），**无融合参数**；再 Eq 9 对称反归一化（L556–566） | `x_norm=revin(x_enc,'norm'); base=dlinear_branch(x_norm); residual=res_branch(x_norm); fused=base+residual; revin(fused,'denorm')`（`DeReFusion.py:36–41`） | **一致**（逐项对应 Eq 8/9） |
| 7 | **残差分支输入** | Algorithm 1 第 3 步第 6 行：`Z_e ← LINEAR_{C→d}(X_n)`（L486）；"From the same `X_n`"（L439）。**输入是同一 RevIN 归一化窗口，不是基础分支的误差**；"残差"指 F=恒等捷径+残差项的学习形式（L553–555） | 两个分支都接收 `x_norm`（`DeReFusion.py:37–39`）；组件层 `ResidualBranch.forward` 直接处理 `x`（`derefusion_components.py:125–133`），无 `x−base` | **一致（关键项）**。代码**没有**把基础预测误差作为输入或标签 |
| 7b | README 叙述 | — | `README.md:23`"两个分支并行接收同一归一化窗口……'残差分支'是结构名称，当前代码没有专门把基础预测误差作为它的输入或训练标签"；`:53`"代码没有先计算并输入基础预测的误差"；`:70`"联合训练不能自动证明它独立预测了一个已训练线性模型的误差" | **已更正**：先前 crosswalk 指出的"计算基础预测未解释部分"过强叙述，在当前 README 中已被显式否定（该 README 修改**尚未提交**，属脏工作区） |
| 8 | RevIN | 逐实例、逐通道均值/方差归一化，两分支共享同一归一化空间，对称反归一化（§2.4 L278–305；§3.2 Eq 2–3；Eq 9 L556–566）；另训练集 z-score 标准化 Eq 10（§4.2 L626–652） | `RevIN(enc_in)` 包裹；`revin(x,'norm')/('denorm')`（`DeReFusion.py:27,37,41`）；诊断另用训练前缀 mean/std 缩放 | 结构**一致**；与作者实现的逐行细节（eps/affine 初始化）**未核实**（作者代码未获取） |
| 9 | 容量 | Table 3：DeReFusion 收敛 `d_model=16`、编码层 **1**、`n_heads=2`、`d_ff=4·d_model`（L778–779）；搜索空间 d_model{16,32,64}、层{1..8}、dropout[0.05,0.6]；基线 d_model=32/2 层/2 heads/d_ff=2d（L776–777）。Table 10：DeReFusion **约 26k** 参数（5 个 horizon 平均，L1570–1577） | pinned：`d_model=32`、`n_heads=4`、`e_layers=1`、`d_ff=128`、`dropout=0.3`、`moving_avg=25`、`enc_in=4`（`PROTOCOL_V1.json.model_configuration`）。我用 pinned 源独立实例化计数：repo 配置 **21,743**（T=1）；论文 Table 3 配置 **5,903**（T=1），T∈{1,7,12,24,36} 均值 **10,268**；repo 配置同口径均值 **26,108** | **有差别 + 论文内部不一致**：(a) repo 的 d_model/heads/d_ff（32/4/128）与 Table 3 所述 DeReFusion（16/2/64）**不同**，是 2× 加宽；(b) 但 Table 10 的"~26k"与本实现下 **repo 配置**（均值 26,108）吻合，而与 Table 3 配置（均值 10,268）不吻合。二者只能靠作者代码定案（已定位 `github.com/twcch/DeReFusion`，未获取）。比例量 d_ff/d=4、d/heads=8 两侧相同 |
| 10 | 损失通道 | `batch 32 / MSE`（Table 3 L756–757）；两分支与 RevIN 仿射参数**联合端到端**优化（L570–572）；Eq 11 = MSE | `loss = mean((pred[:,0,3]-yb[:,3])**2)` 仅 Close 通道（`run_shrink_cdd_v1_1.py:143`）；batch 32 | 仅-Close 与论文评估通道一致；论文训练是否含其余 C 通道**未核实** |
| 11 | 优化器/停止规则 | Adam / **1×10⁻⁴**；早停=验证 MSE（patience **5**）；种子 **{2020,2021,2022,2023,2024}**（Table 3 L753–763） | Adam / **1×10⁻³**（10× 高）；**无早停**——固定 600/1200/1800 步、每 50 步验证、最早严格最小者保留；种子 **{17,29,43}**（`PROTOCOL_V1.json`；`run_shrink_cdd_v1_1.py:134,149–155`；`run_diagnostic.py:199`） | **有差别**（均已在项目内声明为行政预算/自选，非论文设置） |
| 12 | 软件/环境 | 三台不同机器；明确不用墙钟时间比较效率，改用可训练参数量（L787–799） | Python 3.11.15 / torch 2.5.1+cpu / numpy 2.1.2，CPU 2 线程（`PROTOCOL_V1.json`、release） | **有差别**（项目为单机 CPU 轨道；论文跨机） |
| 13 | 作者官方实现 | Data availability 指向 `https://github.com/twcch/DeReFusion`（L15196–15198），自述"Built on thuml/Time-Series-Library" | 本项目为 TSLib 之上的**独立**架构变体（`README.md`、bundle_v3 pin）；仓库内 `twcch` 命中 0 次 | **未核实**：作者代码未获取，无法做逐行超参对照；不得把本项目当作作者官方实现，也不得反向声称 |

## 明确结论

1. **能否称"原论文复现"：不能。** 当前实现共享论文的**高层架构**（DLinear 基分支 + LSTM-Transformer 残差分支 + RevIN 包裹 + Eq 8 直接相加；关键的第 7 项残差输入与论文 Algorithm 1 一致），但在 **研究问题（1）、数据（2）、容量配置（9）、优化器/学习率/停止规则（11）、种子（11）** 上均与论文不同；作者官方实现已定位但未获取，无法做逐行保真对照。准确名称仍是"归档仓库变体的开发诊断"。
2. **第 5 项（残差分支语义）已可定论**：论文与代码都把**同一归一化窗口 `X_n`** 送入两个分支；论文的"residual"是 `F=恒等+残差` 的学习分解（Eq 8），**不是**"预测基础模型的未解释误差"。因此不能依据分支名字做机制归因；当前 README 已按此更正（未提交）。
3. **容量项需要一次作者代码对照或一次容量量级说明**：repo 配置与 Table 3 收敛配置差 2×（d_model/heads/d_ff），而论文 Table 10 的 ~26k 又与本 repo 配置吻合、与 Table 3 配置不吻合。这是**论文内部**需要靠作者代码解决的分歧，不能由本项目"替论文证明"。
4. 未证实项一律保持**未核实**：论文训练 loss 的通道范围、每资产精确切分日历点、RevIN 逐行细节、作者代码内容、Table 10 精确数值。
