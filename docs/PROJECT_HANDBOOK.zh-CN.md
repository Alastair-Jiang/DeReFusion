# DeReFusion 项目说明书

> **用途**：本说明书是本仓库的研究、工程与复现总览。它说明项目试图回答什么、已经知道什么、哪些结论不成立、证据在哪里、如何安全复现，以及下一步被允许做什么。
>
> **当前状态**：2026-09-14；`main` 的记录状态为 Gate A = **FAIL**，F1 广度面板 = **SUCCESS（但存在大比例不稳定资产）**。这两个结论并不矛盾：前者否决了结构特征到算子选择的可迁移桥梁，后者支持“资产层面偏好并非单一资产偶然现象”。
>
> **阅读原则**：本项目将“可观察关联”“预测选择规则”“模型有效性”和“机制解释”严格分开。任何没有原始产物、协议和失败条件支撑的陈述，都不是项目结论。

---

## 目录

1. [一页总览](#一页总览)
2. [问题、边界与非目标](#问题边界与非目标)
3. [仓库结构与信息源优先级](#仓库结构与信息源优先级)
4. [系统与模型技术说明](#系统与模型技术说明)
5. [数据、切分和实验协议](#数据切分和实验协议)
6. [研究设计：两层证据不能混用](#研究设计两层证据不能混用)
7. [推进进度、结论与证据账本](#推进进度结论与证据账本)
8. [Gate A、F1 与当前研究位置](#gate-af1-与当前研究位置)
9. [问题分析与风险登记](#问题分析与风险登记)
10. [复现、运行和验收指南](#复现运行和验收指南)
11. [当前允许的下一步：C1](#当前允许的下一步c1)
12. [协作、提交和文档治理](#协作提交和文档治理)
13. [术语表与参考资料](#术语表与参考资料)

---

## 一页总览

### 项目是什么

DeReFusion 是基于 [THUML Time-Series-Library](https://github.com/thuml/Time-Series-Library) 的金融时间序列预测复现与研究仓库。上游论文是 Hsieh & Chen（2026）的 *DeReFusion: A Controlled Comparison of Soft Computing Fusion Strategies for Financial Time Series Forecasting via a Decomposition-Residual Architecture*，发表于 *Applied Soft Computing*，DOI：[10.1016/j.asoc.2026.116252](https://doi.org/10.1016/j.asoc.2026.116252)。

工程基线是一个双分支预测器：线性分解分支负责稳定、低复杂度的趋势/季节外推；LSTM–Transformer 残差分支负责拟合线性基座未解释部分；二者通过无参数的直接相加融合，并在输入与输出之间使用 RevIN 实例归一化。

在复现之上，本 fork 进一步提出但**不预设答案**的问题：

> 在给定资产、容量和市场状态下，线性与非线性算子的相对价值是否存在可复现、可解释的差异？

### 截至当前可安全陈述的结果

| 命题 | 状态 | 证据与正确表述 |
|---|---|---|
| 原论文的核心排序可被复现 | 支持 | GSPC、T=24、seed 2021：DeReFusion MSE 0.06230 < revin-DLinear 0.07007 < learnable gate 0.07191。 |
| 更复杂的门控会带来收益 | 不支持 | gatev1 为 0.06767，仍差于直接相加的 0.06230；没有证据显示需要样本级切换。 |
| 非线性算子普遍优于线性算子 | 不支持 | BTCUSD 稳定偏线性；ETHUSD 在较宽 MLP 下偏非线性；GSPC 在宽度 128 接近持平。 |
| 样本级路由可行 | 不支持 | 12 个预注册状态、三资产、三种子下，没有稳定的“状态 → 算子”映射；容量变化主要改变资产级偏好。 |
| 资产级算子异质性存在 | 支持，但有限定 | F1 在原 Yahoo 资产上新增 TM（非线性）、DJI/EURUSD/USDJPY（线性）四个跨种子、跨宽度稳定资产；BABA/NVO/SOX 不稳定。 |
| `|ACF1|` 可以在新资产上选择算子 | 不支持 / 已关闭 | Gate A 因 BOE、EASTMONEY 的容量符号矛盾而 FAIL。N=14 的相关仍为正，但为发现集扩展且特征与结果同段测量，不能形成事前规则。 |
| NS-inspired 算子值得立即实现 | 不允许 | Gate A FAIL 后，NS benchmark eligibility 被降级；该方向只是远期假设，不是现行模型计划。 |

### 决策总图

```text
原论文复现
  └─ 统一预测协议 + 原始产物
       ├─ 框架层：DeReFusion vs revin-DLinear 的波动率交互
       └─ 代理层：线性 map vs MLP 的容量控制比较
            ├─ 无稳健样本级差异 → 关闭 routing / gate / MoE
            ├─ 多资产异质性 → F1 扩展检验 → SUCCESS（含不稳定少数）
            └─ |ACF1| 结构桥 → Gate A → FAIL
                 └─ 禁止用特征选算子；不启动 NS 实现

当前唯一被许可的研究准备：C1 独立、同源、前瞻 cohort 的数据锁定与验证。
```

---

## 问题、边界与非目标

### 核心问题

项目研究的是**预测算子在何种条件下有价值**，不是寻找单一“最佳模型”。非线性分支的表现应被读作：

\[
\text{value of nonlinearity} = f(\text{asset},\ \text{capacity},\ \text{condition},\ \text{protocol}).
\]

因此，平均 MSE 排名不足以回答研究问题；必须同时报告资产、种子、宽度、状态切片和不确定性。

### 明确非目标

- 不声称金融市场服从 Navier–Stokes、流体方程或任何已知守恒律。
- 不把同一测试段上的特征–结果关联说成可部署的事前选择策略。
- 不在失败后重选特征、阈值、资产、种子或显著性标准。
- 不以“更大模型”“更复杂门控”代替对容量匹配和普通基线的比较。
- 不把 F1 的资产异质性结果误写成 `|ACF1|`、波动率或任何单一结构特征的解释证据。

### 写作与工程标准

说明书吸收 Jane Street 公开工程文章所倡导的实践：小而可审查的变更、将行为显式化的测试/产物、可回到完整版本的环境、以及将失败路径写进设计本身。它不是对任何公司的方法或内容的复制。

- “单一修订即环境”的可追溯思路，参考 [Building reproducible Python environments with XARs](https://blog.janestreet.com/building-reproducible-python-environments-with-xars/)；本仓库对应做法是把运行命令、数据哈希、预测数组、日志和报告一起保留。
- “小变更、快速审查、可见行为”的协作思路，参考 [Ironing out your development style](https://blog.janestreet.com/ironing-out-your-development-style/)；本仓库对应做法是冻结规则、分离计划与结果、每次修改提交到远端。
- “测试同时记录意图和可观察行为”的思路，参考 [What if writing tests was a joyful experience?](https://blog.janestreet.com/the-joy-of-expect-tests/)；本仓库对应做法是保留原始预测、逐样本误差和可重复分析脚本，而非只保存一个汇总数字。

---

## 仓库结构与信息源优先级

```text
run.py                         CLI、随机种子、任务调度
models/derefusion/             DeReFusion 与消融/门控变体
layers/RevIN.py                实例归一化与反归一化
data_provider/                 Dataset_Custom、切分与 StandardScaler
exp/                           训练、验证、测试、产物落盘
dataset/                       原始十资产 OHLC 数据
reproduction/analysis/         分层、容量、Gate A、F1、C1 工具
reproduction/results/          JSON/CSV/TXT 原始分析产物
reports/evidence_closure/      预注册、审计、结果、决策与限制
docs/                          面向读者的说明、历史路线图与论文产物
```

### 发生冲突时，以谁为准

| 优先级 | 文件 / 证据 | 作用 |
|---|---|---|
| 1 | `reports/evidence_closure/14_structural_validation_result.md` | Gate A 最终裁决；不得被历史计划覆盖。 |
| 2 | `reports/evidence_closure/21_f1_result.md` | F1 最终结果与其限定。 |
| 3 | `reports/evidence_closure/16_post_gate_experiment_program.md`、`23_c1_preregistration.md` | 现行后续边界与 C1 的预注册骨架。 |
| 4 | `PROJECT-BRIEF.md`、`RESEARCH-LINE.md` | 研究全景与硬约束。 |
| 5 | `reproduction/results/`、`results/`、`sweep_runs/` | 原始计算产物与日志；数字问题回到这里。 |
| 6 | `README.md` | 上游项目的安装与模型概览。 |
| 7 | `docs/ROADMAP.md` | **历史快照**；其中大量旧待办已被后续证据否决，不能作为执行依据。 |

每一项可引用的研究结论都应能从说明文字回到脚本、配置、原始数组/CSV 和日志。若无法回溯，正确的状态是“待核验”，而不是“已知”。

---

## 系统与模型技术说明

### 输入、输出与张量形状

金融数据使用 `date,Open,High,Low,Close` 五列。默认主协议以 OHLC 四通道作为输入，预测单一 `Close`：

```text
x_enc : [B, L, 4]       L = seq_len = 96
forecast : [B, T, 4]    T = pred_len；评估取 Close 通道
```

`MS` 模式将目标 `Close` 移到内部目标位置，`c_out=1` 表示评估的目标维度。所有日频实验显式传入 `--data custom --features MS --target Close --freq b`，不可依赖 TSLib 的 ETT 默认值。

### DeReFusion 前向路径

实现位置：[模型代码](../models/derefusion/DeReFusion.py)。令输入窗口为 \(x\)：

1. **RevIN 标准化**：逐样本、逐通道计算窗口均值和标准差；统计量 `detach`，随后应用可学习 affine 参数。
2. **DLinear 基座**：移动平均分解 \(x = s + t\)，对季节项 \(s\) 和趋势项 \(t\) 分别做 `Linear(L → T)`，输出 `base`。
3. **混合残差分支**：`Linear(4 → D)` → 单层 LSTM → 单层 Transformer Encoder → 时间投影 `Linear(L → T)` → 通道投影 `Linear(D → 4)`，输出 `residual`。默认研究配置中 `D=32`，Transformer 分支固定使用 4 个头、dropout 0.3。
4. **直接融合**：\(\hat y_{norm}=base+residual\)。没有门、路由器或条件权重。
5. **RevIN 反归一化**：复用当前样本窗口的均值/方差回到原尺度。

```text
x_enc ── RevIN(norm) ──┬─ DLinear seasonal/trend ── base ─────┐
                       └─ projection → LSTM → Transformer ─ residual ─┤ + ─ RevIN(denorm)
                                                                         └─ forecast
```

这是一种**分解–残差归纳偏置**：线性部分承接低复杂度外推，残差分支学习剩余偏差。它不是因果分解，也不保证两分支分别对应经济学上的“趋势”和“噪声”。

### 变体与比较对象

| 类别 | 名称 | 目的 |
|---|---|---|
| 基线 | `revin-DLinear` 等十个 RevIN 包装的 TSLib 模型 | 把归一化固定，比较骨干复杂度而不是 preprocessing。 |
| 消融 | `DeReFusion-woDy`、`-woLSTM`、`-woTransformer` | 检验残差分支、LSTM、Transformer 的边际作用。 |
| 门控 | `gatev1-volatilityaware`、`gatev2-learnable`、`gatev3-inputconditioned` | 检验直接相加是否值得被条件化融合取代；不是当前继续方向。 |
| 容量代理 | 线性映射 vs MLP（width 23/64/128） | 以较受控的普通算子比较隔离容量影响；不是对 DeReFusion 结构本身的完全替代。 |

### 训练与评估实现

`run.py` 设定 Python、NumPy 与 PyTorch 随机种子，选择任务类；`exp/exp_basic.py` 递归发现 `models/` 下的模型模块并按需导入；`exp/exp_long_term_forecasting.py` 使用 Adam、MSELoss、EarlyStopping 和学习率策略。

测试产物包含 `metrics.npy`（MAE、MSE、RMSE、MAPE、MSPE、R²）、`pred.npy`、`true.npy`，并写入参数量、训练时间、推理速度与 CUDA 峰值显存。指标实现见 `utils/metrics.py`。MAPE/MSPE 在接近零的价格或收益任务中会不稳定，因此本项目的核心判别仍以 MSE 差及其配对 bootstrap 区间为主。

---

## 数据、切分和实验协议

### 数据范围

原始研究面板包含十个 2016-01-01 至 2025-12-31 的日频资产：BABA、NVO、TM、GSPC、DJI、SOX、EURUSD、USDJPY、BTCUSD、ETHUSD。股指/个股、外汇与加密资产的交易日历不同，这是行数不同的正常原因，不是应被填补的缺失值。

新增 Gate A 压力测试使用四个 A 股资产 BYD、BOE、EASTMONEY、YANGHE。它们来自 Sohu，而原面板来自 Yahoo；这同时改变了市场、微观结构和提供商，故只能称为**域偏移压力测试**，不是独立外部验证。

### 固定协议

| 维度 | 固定设置 |
|---|---|
| 切分 | 时间顺序 70% / 10% / 20%；验证和测试窗口各向前扩展 `seq_len` 提供 lookback。 |
| 缩放 | `StandardScaler` 只在训练集拟合，再变换验证/测试集。 |
| 归一化 | 所有训练模型均以 RevIN 处理，避免将归一化能力误归因于骨干。 |
| 主任务 | `long_term_forecast`；主要研究点为 `L=96`、`label_len=48`、`T=24`。 |
| 优化 | Adam、MSE、`lr=1e-4`、batch 32、30 epochs、patience 5、cosine schedule。 |
| 种子 | 常用 2021/2022/2023；每次运行在 setting 名中记录种子。 |
| 统计 | 逐样本配对 bootstrap，4,000 次重采样；保留预测、真实值和状态掩码。 |
| 设备 | 当前复现环境为 Windows、CPU；必须添加 `--no_use_gpu`。 |

### 波动率分层与交互量

项目采用去趋势的相对波动率作为跨资产主口径。绝对波动率会与时间段混淆（例如 GSPC 与 BTCUSD 的时间相关方向不同），所以只能作对照。主交互量为：

\[
\Delta_{interaction}=\Delta MSE_{high50}-\Delta MSE_{low50},\quad
\Delta MSE=MSE_{nonlinear}-MSE_{linear}.
\]

负值表示非线性相对优势在高波动状态更强；正值表示相反。该量是**框架层**中 DeReFusion 相对 `revin-DLinear` 的条件效应，不等于容量代理层中的 MLP–线性偏好。

---

## 研究设计：两层证据不能混用

### A 层：框架层交互

问题是：在相同预测管线中，DeReFusion 相对线性基线的差异是否会随着波动状态而改变？输出是 `Δ_interaction`，用于描述模型分支在状态下的相对表现。

它能够支持“某资产中条件效应的方向”或“跨资产的描述性关联”。它**不能**直接回答哪种普通算子在相同参数预算下更合适。

### B 层：容量控制代理

问题是：给定相同输入、切分、种子、优化器和训练预算，线性 map 与 MLP 的相对误差在资产间是否稳定？width 23 是近似参数匹配点（9,240 vs 9,431 参数）；width 64/128 是容量敏感性比较，并非严格匹配。

12 个结构状态只是对同一 `(asset, width, seed)` 训练结果做**评估分层**，不是将训练量放大 12 倍。它能够支持普通线性/MLP 在特定资产与容量下的偏好，但不能自动推出 DeReFusion 的某个结构部件是原因。

### 为什么这个区分重要

若 A 层相关为正而 B 层宽度翻转，正确结论不是“相关无效”或“模型证明了相关”，而是：关联无法承受一个用于选算子的必要稳定性检验。Gate A 正是依据这个原则失败。

同理，F1 找到更多稳定的 MLP/线性资产，并不修复 `|ACF1|` 的失败；它只加强“资产异质性值得作为观察对象”的结论。

---

## 推进进度、结论与证据账本

### 时间线

| 阶段 | 完成状态 | 产物与结论 |
|---|---|---|
| P0：原论文复现 | 完成 | GSPC 上复现 T=24 的加法融合排序；建立数据、训练、日志与可视化管线。 |
| P1：波动率分层 | 完成 | 发现绝对波动率的时间混淆，确立 relative volatility 为主口径；跨资产交互方向并不一致。 |
| P2：门控与路由检验 | 完成并关闭 | 门控未优于直接相加；状态级偏好未稳定，禁止继续 router/gate/MoE/attention 方向。 |
| P3：容量敏感性 | 完成 | ETHUSD 在宽 MLP 时翻为非线性偏好；BTCUSD 始终线性；GSPC 趋近持平。容量是重大混杂因素。 |
| P4：N=10 结构关联 | 完成，仅探索性 | `|ACF1|` 与交互 ρ=+0.733（p=0.016），LOO 不翻向；因筛选和同时段测量，仅为候选。 |
| P5：Gate A（N=14） | 完成，FAIL | 相关仍 +0.688（p=0.007）且 LOO 稳定，但 BOE、EASTMONEY 在 w64/w128 出现偏好符号矛盾，触发冻结 FAIL 规则。 |
| P6：F1 原资产广度面板 | 完成，SUCCESS | 在七个剩余 Yahoo 资产中得四个严格稳定新资产和相反偏好对；同时 3/7 不稳定。 |
| P7：C1 独立前瞻 cohort | 未开始 / 数据阻塞 | 规则骨架与 intake validator 已就位；待单一提供商、哈希锁定、单独 lock commit 和所有者授权。 |

### 关键数值与含义

1. **容量敏感性不是注脚。** ETHUSD 的 mean ΔMSE 从 width 23 的 +0.0145 变为 width 64 的 −0.0281、width 128 的 −0.0321；BTCUSD 则始终偏线性；GSPC 到 width 128 为 +0.0061。它排除了“一种容量或一种算子对所有资产都更好”的简化说法。
2. **跨资产波动率作用不统一。** GSPC 在两个种子上高波动时更利于非线性；BTCUSD 方向相反；ETHUSD 方向相近但区间触零。故波动率不能作为通用路由键。
3. **结构关联仍是描述，不是部署规则。** N=14 的 `|ACF1|` 相关为 +0.688（p=0.007，LOO +0.610 至 +0.786），但 10/14 来自发现样本，且特征在测试段上计算。统计数字好看不等于获得前瞻有效性。
4. **F1 成功有边界。** TM 在 width 64/128 均稳定非线性，DJI/EURUSD/USDJPY 均稳定线性；BABA、NVO、SOX 不满足严格标准。结论应是“资产层面异质性在原来源面板的多数资产上复现，并存在明显不稳定少数”，不能是“每个资产都有永久的偏好标签”。

### 证据强度标注

| 标签 | 含义 | 本项目示例 |
|---|---|---|
| 已复现 | 在声明协议下被运行产物直接支持 | GSPC 的 T=24 论文排序。 |
| 支持 | 证据与预先定义判据一致，但有明确范围 | F1 的原来源资产级异质性。 |
| 候选 | 方向性发现，缺少独立/前瞻证实 | N=10 的 `|ACF1|` 关联；现已不再作为结构桥。 |
| 不支持 | 检验没有留下可用的正证据 | 样本级 routing、门控优于直接相加。 |
| 禁止 / 未授权 | 即使技术上可做，也未满足研究治理条件 | NS-inspired 算子、重启 Gate A、特征重筛。 |

---

## Gate A、F1 与当前研究位置

### Gate A：为什么是 FAIL

Gate A 的初衷是检验 `|ACF1|` 候选关联能否在四个预先选定的新资产上承受压力。PASS 在结果生成前已经不可达；剩余的 FAIL/CONDITIONAL 由冻结规则机械裁决。

N=14 的 A 层并没有崩溃：`ρ(|ACF1|, interaction)=+0.688`、p=0.007、LOO 不翻向。但 B 层中 BOE 与 EASTMONEY 的平均 ΔMSE 在 width 64 与 128 之间改变符号。这意味着即使某个特征与交互量同向，它也无法支持一个对容量鲁棒的算子选择推论；该情况触发冻结的容量矛盾 FAIL 条款。

因此精确结论是：

> Gate A 失败的原因是二级、派生的算子偏好推论出现容量矛盾；不是因为 N=14 的交互相关消失。无论如何，10/14 与发现集重叠且特征–结果为同段测量，均不足以把关联提升为独立、前瞻验证。

### F1：为什么又是 SUCCESS

Gate A FAIL 后，项目没有继续寻找另一个结构特征，而是退回更基础的问题：资产级普通算子偏好是否在原数据来源中可复现？F1 对余下七个 Yahoo 资产使用既有线性–MLP 代理和冻结设置。

F1 的预注册成功条件是：至少两个额外稳定资产，且至少一对新的相反偏好资产。TM（非线性）与 DJI/EURUSD/USDJPY（线性）满足条件，所以 F1 成功。它提高的是资产异质性的覆盖度，而不是 `|ACF1|` 的可解释性或 NS 的资格。

### 当前状态机

```text
Gate A FAIL
  ├─ 关闭：|ACF1| 作为本线结构桥 / 用特征选择算子 / NS 实现
  ├─ 完成：F1 原来源异质性检验 → SUCCESS（含 3/7 不稳定）
  └─ 仅可准备：C1 独立同源前瞻 cohort
       ├─ 数据未获得 → 不可训练
       ├─ 数据通过校验 → 生成草案锁表
       ├─ 所有者审阅 + 单独 lock commit → 才可观察特征
       └─ 所有者再次授权 → 才可执行训练
```

---

## 问题分析与风险登记

### 科学与统计风险

| 风险 | 为什么重要 | 当前处理 | 仍不能做什么 |
|---|---|---|---|
| 特征筛选 / 多重比较 | 最初筛过八个特征，p 值不是 multiplicity-clean | 仅保留候选/历史记录；C1 只将 `|ACF1|` 作为主预测量 | 不能把最显著特征包装成已确认规律。 |
| 同时段测量 | 特征与交互在同一测试段上计算 | 文档统一标为 contemporaneous/descriptive | 不能据此“先看特征再选模型”。 |
| 容量混杂 | MLP 宽度改变偏好方向与稳定性 | 保留 23/64/128，并明确仅 w23 近似参数匹配 | 不能把宽模型优势说成算子形式必然优势。 |
| 资产相关性 | 同市场资产并非独立样本 | A 股四资产标为域偏移压力测试，非独立 cohort | 不能把 N=14 当作独立外部验证。 |
| 稳定性 | F1 有 3/7 不稳定资产 | 成功与限制同等显著地报告 | 不能把每个资产强行分到永久类别。 |
| 多种子不足 | 部分框架层只使用一个种子 | C1 要求每资产至少三种子 | 不能用单种子点估计夸大确定性。 |

### 数据与基础设施风险

| 风险 | 现象 | 缓解措施 |
|---|---|---|
| Yahoo 获取受阻 | 系统代理导致 TLS timeout；绕过代理后 Yahoo 返回 403 | 不隐式替换来源；单提供商、完整 cohort、哈希和 provenance 记录。详见 `15_data_acquisition_diagnosis.md`。 |
| 代理/网络差异 | 代理、DNS、区域和反爬可能让获取结果不可重复 | 在批量抓取前做单标的健康检查；记录下载时间、来源与哈希。 |
| Windows 编码 | PowerShell 5.1 读取非 ASCII `.ps1` 可能出错 | 批处理脚本保持 ASCII；日志用 UTF-8。 |
| DataLoader 停滞 | 杀子进程可能导致父训练器死锁 | 用进程 CPU 时间而非单一日志判断；使用幂等、可恢复批处理。 |
| 依赖脆弱 | `sktime`、`datasets`、`huggingface_hub` 等被无条件导入 | 在环境清单中固定版本，并在跑批前做导入烟雾测试。 |

### 技术债与改进方向（不等于获准研究）

- `data_provider/data_loader.py` 对 ETT 与 custom 数据集共用的依赖较重，最小预测复现仍会加载部分非核心依赖；应将其作为工程可移植性问题记录，而非在结论文件中悄然修改。
- `run.py` 设置随机种子但未强制 cuDNN deterministic；CUDA 复现需报告运行差异。当前主环境为 CPU，仍应把硬件、PyTorch 与依赖版本写入结果元数据。
- 顶层 README 服务于上游论文，`docs/ROADMAP.md` 是历史快照；阅读者必须先看本说明书及证据闭环报告，避免执行已撤销的路线。
- 任何未来的算子形式比较都必须至少匹配普通 MLP、普通时序卷积和/或 SSM 的参数与计算预算，并预先写出失败判据；这是一项未来方法学要求，不是当前授权。

---

## 复现、运行和验收指南

### 环境前提

推荐从项目虚拟环境执行。当前已记录的复现环境为 Windows、Python 3.13、CPU PyTorch；上游 README 推荐 Python 3.11 和 CUDA PyTorch，二者不可混写为同一个严格复现环境。运行前核对本地 `.venv`、`requirements/` 与报告中实际使用的版本。

最小训练示例：

```powershell
.venv\Scripts\python.exe run.py --task_name long_term_forecast --is_training 1 `
  --model_id GSPC_96_24 --model DeReFusion --data custom --root_path ./dataset/ `
  --data_path GSPC-2016-2025.csv --features MS --target Close --freq b `
  --seq_len 96 --label_len 48 --pred_len 24 --enc_in 4 --dec_in 4 --c_out 1 `
  --d_model 32 --moving_avg 25 --train_epochs 30 --batch_size 32 `
  --learning_rate 0.0001 --patience 5 --lradj cosine --rand_seed 2021 --no_use_gpu
```

### 复现验收清单

运行或评审一项实验时，至少检查：

- [ ] CSV 精确为 `date,Open,High,Low,Close`，日期严格递增，无重复；来源、调整策略和 SHA-256 已记录。
- [ ] 使用时间顺序 70/10/20 切分，Scaler 仅拟合训练部分。
- [ ] 明确传入 `custom`、`MS`、`Close`、`b`、`4/4/1`，没有沿用 ETT 默认值。
- [ ] 命令、git commit、Python/PyTorch 版本、设备、种子、数据哈希被写入日志或报告。
- [ ] `pred.npy`、`true.npy`、`metrics.npy`、训练日志与分析 JSON/CSV 都存在；不得只保留表格。
- [ ] 比较中分清框架层和容量代理层；宽度 64/128 不被称为严格参数匹配。
- [ ] 报告同时展示成功、失败、无显著性与不稳定结果。

### C1 intake 校验（仅数据接收，不运行实验）

当单一提供商的候选 cohort 交付后，可先运行：

```powershell
.venv\Scripts\python.exe reproduction/analysis/c1_cohort_validate.py `
  --cohort <cohort-directory> --repo . --draft <draft-lock-table.md>
```

该工具校验 schema、日期、覆盖期、重复、哈希、候选宇宙与来源收据，并只生成**草案**锁表。草案不是 lock，也不授权特征计算或训练。

---

## 当前允许的下一步：C1

### C1 要回答的问题

在一个真正独立、单一来源、15–20 资产的 cohort 中，`|ACF1|` 是否能够在**测试期开始之前**计算，并与后续固定协议下的交互量保持同向、LOO 稳定的关联？

这检验的是候选关联的可移植性，不是恢复 Gate A、恢复 NS eligibility、生成资产选模器，或验证任何物理机制。

### C1 的硬前置条件

1. 一个提供商覆盖整个 cohort，且所有资产使用同一调整策略。
2. 预先命名完整候选宇宙；不得根据 ACF、波动率或结果挑选极端资产。
3. 数据在 2016–2025 覆盖充分，所有纳入/排除有机械规则、行数和 SHA-256。
4. 填完锁表并单独提交 `lock: C1 cohort <provider> <n> assets` 后，才允许查看特征与结果。
5. 主预测量 `|ACF1|` 和次预测量 realized volatility 只能用验证切点前的数据；任何测试期索引进入预测量即为完整性失败。
6. 每资产两条框架臂、三种子、固定 T=24/L=96/70-10-20/4,000 bootstrap；只有所有者明确授权后才执行。

### C1 的失败也有价值

若 C1 方向翻转、相关绝对值过小、p 值未过冻结操作阈值、LOO 穿零、单资产驱动，或出现完整性问题，则 `|ACF1|` 在本项目中永久退出结构桥角色。结果必须被完整保存和报告，而不是改用另一组特征继续搜索。

---

## 协作、提交和文档治理

### 变更原则

1. **先说明意图和判据，再动代码或数据。** 对研究规则尤其如此。
2. **计划、原始结果与解释分文件保存。** 计划文件不能倒写结果，结果文件不能重写已冻结规则。
3. **小改动、可审查、可回滚。** 每个提交聚焦一个问题；不要混入无关格式化、数据替换或重构。
4. **远端是协作记录。** 本地修改经过验证并获所有者认可后，提交并推送到 `origin/main`；提交说明应描述证据或工程变化，而不是夸张结论。
5. **所有失败保持可见。** 不删除失败日志、状态、种子或资产；修复应追加记录而非抹去历史。

### 推荐提交格式

```text
docs: add handbook with Gate A/F1 evidence boundaries
data: lock C1 cohort <provider> <n> assets
tool: validate C1 cohort schema and provenance
result: record <experiment> with raw artifacts and fixed verdict
```

提交前最小检查：`git status --short`、只审阅本次 diff、核对文档链接、运行与变更匹配的脚本/测试。提交后核对 `git log -1` 与 `git status --short`，再推送。

### 文档更新规则

- 新结果：新增带日期和产物路径的证据报告，不改写既有结果。
- 新计划：写明是否只是草案、是否已锁定、是否授权执行。
- 撤销方向：在当前文档和执行入口中显式标出，不依赖读者自行发现旧计划过期。
- 数字：优先从原始 CSV/JSON 或产生它的脚本复核；摘要不能成为唯一来源。

---

## 术语表与参考资料

### 术语表

| 术语 | 定义 |
|---|---|
| DeReFusion | DLinear 分解基座与 LSTM–Transformer 残差的直接相加预测器。 |
| RevIN | Reversible Instance Normalization；按样本窗口归一化并在输出端反归一化。 |
| 框架层 | DeReFusion 与 `revin-DLinear` 在波动状态下的交互分析。 |
| 容量代理层 | 线性 map 与普通 MLP 的受控算子比较。 |
| ΔMSE | 本说明书中为 `MSE_nonlinear - MSE_linear`；负值偏非线性，正值偏线性。 |
| 交互量 | 高波动半区 ΔMSE 减低波动半区 ΔMSE；表示条件效应变化。 |
| Gate A | 对候选结构关联与其派生算子偏好推论的冻结裁决，最终为 FAIL。 |
| F1 | Gate A FAIL 后针对余下七个原 Yahoo 资产的容量控制广度面板，最终为 SUCCESS（含限制）。 |
| C1 | 尚未运行的独立、同源、前瞻 cohort 验证计划。 |
| 同时段描述性关联 | 特征与结果在同一测试段测量；可以描述共变，但不能作为事前决策规则。 |

### 仓库内一手资料

- [项目简报](../PROJECT-BRIEF.md)
- [研究线入口](../RESEARCH-LINE.md)
- [Gate A 最终报告](../reports/evidence_closure/14_structural_validation_result.md)
- [后 Gate 研究计划](../reports/evidence_closure/16_post_gate_experiment_program.md)
- [F1 最终报告](../reports/evidence_closure/21_f1_result.md)
- [C1 预注册骨架](../reports/evidence_closure/23_c1_preregistration.md)
- [数据获取诊断](../reports/evidence_closure/15_data_acquisition_diagnosis.md)
- [原论文复现资产说明](../reproduction/README.md)

### 外部参考

1. Hsieh, C.-C. & Chen, M.-Y. (2026). *DeReFusion: A Controlled Comparison of Soft Computing Fusion Strategies for Financial Time Series Forecasting via a Decomposition-Residual Architecture*. Applied Soft Computing, 203, 116252. [DOI](https://doi.org/10.1016/j.asoc.2026.116252)
2. THUML. [Time-Series-Library](https://github.com/thuml/Time-Series-Library).
3. Jane Street. [Building reproducible Python environments with XARs](https://blog.janestreet.com/building-reproducible-python-environments-with-xars/), 2023.
4. Jane Street. [Ironing out your development style](https://blog.janestreet.com/ironing-out-your-development-style/), 2016.
5. Jane Street. [What if writing tests was a joyful experience?](https://blog.janestreet.com/the-joy-of-expect-tests/), 2023.

---

## 读者的下一步

- 想了解**项目是否值得继续**：先读本说明书的“当前状态机”和 Gate A/F1 两节。
- 想**复现实验**：按“复现、运行和验收指南”操作，再回到原始结果与脚本核对。
- 想提出**新模型**：先阅读“问题、边界与非目标”及 `16_post_gate_experiment_program.md`；当前不允许把新模型包装为对已关闭结构桥的验证。
- 想推进**C1**：只能先解决同源数据获取、验证、草案锁表和单独 lock commit；训练前仍需明确授权。

本项目最重要的产品不是一个看似更聪明的融合结构，而是一条可以被反驳、审计、复现和安全延续的研究记录。
