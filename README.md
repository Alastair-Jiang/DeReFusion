# DeReFusion research fork / DeReFusion 研究分支

[English](#english) · [中文](#中文) ·
[仓库审计](docs/REPOSITORY_AUDIT_2026-09-18.md) ·
[后续计划](docs/LITERATURE_AND_NEXT_PLAN.md) ·
[证据链](reports/README.md)

> This repository is an independently maintained research fork based on the
> public DeReFusion implementation and THUML Time-Series-Library. It is **not
> represented here as the paper authors' official release**.

参考论文 / Reference paper: Chih-Chien Hsieh and Mu-Yen Chen,
*DeReFusion: A Controlled Comparison of Soft Computing Fusion Strategies for
Financial Time Series Forecasting via a Decomposition-Residual Architecture*,
Applied Soft Computing 203 (2026), 116252.
[论文 DOI](https://doi.org/10.1016/j.asoc.2026.116252)

---

## 中文

### 1. 项目是什么

DeReFusion 是一个面向非平稳金融时序的分解—残差双分支预测模型：

1. RevIN 对每个输入窗口做可逆归一化；
2. DLinear 基座分支建模趋势/季节等低复杂度成分；
3. `Linear → LSTM → Transformer → Linear` 残差分支建模基座未解释部分；
4. 两分支直接相加，再用 RevIN 反归一化。

```text
OHLC window
   └─ RevIN(norm)
       ├─ DLinear decomposition base ──┐
       └─ LSTM+Transformer residual ─├─ add ─ RevIN(denorm) ─ forecast
```

仓库不只包含模型，还保留了复现、容量对照、预注册规则、原始预测数组、
SHA-256 清单、失败门控和独立盲复算规格。它现在更像一个“证据闭环仓库”，
而不是单纯的模型演示仓库。

### 2. 当前研究结论

| 问题 | 当前结论 | 强度/边界 |
|---|---|---|
| 直接加法是否必须换成学习门控 | 未获支持 | 测试的波动率门控比无参加法差 8.6%；不外推到所有门控。 |
| 结构状态能否逐窗口路由算子 | 未获稳定支持 | 不重启自适应 gate/router/MoE。 |
| `|ACF1|` 能否解释算子偏好 | Gate A **FAIL** | N=14 关联方向保留，但 BOE/EASTMONEY 的容量变化导致偏好符号反转；10/14 还是发现集。 |
| 资产层面的算子异质性是否存在 | F1 **窄义成功** | 7 个追加资产中 4 个种子与宽度稳定，3 个不稳定；是倾向，不是资产不变属性。 |
| C1 前瞻性闭环 | **FAIL** | 120/120 运行完成；`rho=-0.1519, p=0.5227`，候选未复现，`|ACF1|` 永久退出。独立审计验证了输入与失败稳健性，并发现交接规则缺口。 |
| Navier–Stokes/NS 设想 | **未测试，也未被反驳** | 现有 OHLC 没有已证明的守恒量、边界条件或 PDE 残差；当前证据不授权物理机制主张。 |

详细审查、可疑点和修正见
[`docs/REPOSITORY_AUDIT_2026-09-18.md`](docs/REPOSITORY_AUDIT_2026-09-18.md)。

### 3. 数据

`dataset/` 现有 61 份日频 OHLC CSV，共 149,474 行。完整的文件级 SHA-256、
行数、日期范围、证据队列与质量检查在
[`dataset_registry.csv`](reproduction/results/dataset_registry.csv)，分组与问题说明见
[`dataset/README.md`](dataset/README.md)。

关键警告：

- 5 份外汇数据有少量 OHLC 包络违反，原始值未被静默修改；
- WTI 保留 2020 年负油价，使局部对数收益率无定义；
- `supporting-unregistered` 数据不能临时加入确证性分析。

### 4. 仓库结构

```text
run.py                         统一任务入口
models/                        DeReFusion、消融、门控、RevIN 基线、TSFM 适配器
layers/                        RevIN、attention、embedding 等
data_provider/                 数据集与加载器
dataset/                       61 份 OHLC CSV 与数据说明
reproduction/analysis/         可复算分析程序
reproduction/results/          结构化结果、注册表、失败证据
reproduction/c1_handoff/       C1 原始数组、manifest 与盲审交接
reports/evidence_closure/      00–26 号冻结决策链（按顺序阅读）
docs/                          仓库审计、文献地图和双语阶段报告
requirements/                  核心与可选依赖分组
```

### 5. 环境与安装

建议 Python 3.11。不要为了跑 DeReFusion 就安装全部基础模型栈。

```bash
# 有 CUDA 12.1 时；CPU/MPS 请先按 PyTorch 官方命令安装 torch==2.5.1
pip install -r requirements/torch-cu121.txt
pip install -r requirements/core.txt

# 仅在运行 Chronos/Moirai/TimesFM 时
pip install -r requirements/foundation.txt
```

平台限定的 Mamba 依赖单独放在
`requirements/mamba-linux-cu12.txt`。完整说明见
[`requirements/README.md`](requirements/README.md)。

### 6. 单次训练/评测

```bash
python run.py \
  --task_name long_term_forecast --is_training 1 \
  --model_id GSPC_96_24 --model DeReFusion \
  --data custom --root_path ./dataset/ --data_path GSPC-2016-2025.csv \
  --features MS --target Close --freq b \
  --seq_len 96 --label_len 48 --pred_len 24 \
  --enc_in 4 --dec_in 4 --c_out 1 \
  --d_model 32 --moving_avg 25 --train_epochs 30 --batch_size 32 \
  --learning_rate 0.0001 --patience 5 --lradj cosine \
  --rand_seed 2021 --no_use_gpu
```

可用模型名由 `exp/exp_basic.py` 递归发现 `models/**/*.py` 中的 `Model`。
核心模型包括 `DeReFusion`、`DeReFusion-woDy`、
`DeReFusion-woLSTM`、`DeReFusion-woTransformer`、三个 `gatev*` 变体以及
`revin-*` 基线。

### 7. 复算与阅读顺序

```bash
python reproduction/analysis/dataset_audit.py
python reproduction/analysis/f1_analysis.py
python reproduction/analysis/build_c1_blind_manifest.py
```

建议阅读：

1. 本 README；
2. [仓库与证据审计](docs/REPOSITORY_AUDIT_2026-09-18.md)；
3. [`reports/README.md`](reports/README.md) 的结论索引；
4. Gate A 报告 14 → F1 报告 21 → C1 预承诺 24/24a/24b → 最终报告 26；
5. [前沿文献与下一步](docs/LITERATURE_AND_NEXT_PLAN.md)。

### 8. 后续原则

下一步做现代基线刷新（TimeMixer、state-space
基线、Chronos-2、TimesFM-3、Moirai）。评估必须报告资产/种子/预测步长失败，
并同时考虑准确率、校准、时延、内存与能耗。只有在参数量与计算预算匹配后，
频域/算子归纳偏置仍稳定超过普通 MLP、时域卷积与状态空间基线，才值得继续。

---

## English

### Project

DeReFusion applies RevIN, predicts a decomposed linear base with DLinear,
models the remaining signal with an LSTM–Transformer residual branch, and fuses
the two by direct addition. This fork adds a reproducible evidence programme:
ablations, gate variants, capacity-matched proxy operators, pre-registered
decision gates, retained raw arrays and independent blind recomputation.

### Current evidence

- A learned volatility gate did not beat direct addition in the tested setup;
  sample-level routing is unsupported.
- Gate A failed its frozen capacity-contradiction rule. The exploratory
  `|ACF1|` association cannot be presented as a validated selector.
- F1 found stable operator preferences for 4/7 additional assets in both
  directions, with a substantial 3/7 unstable minority.
- C1 finished all 120 prospective runs and failed (`rho=-0.1519`, `p=0.5227`).
  The candidate is retired. An independent audit verified the raw inputs and
  robustness of failure, while identifying an aggregation-rule handoff gap.
- No Navier–Stokes-inspired operator has been tested. The idea is neither
  validated nor refuted and must not be described as financial physics.

### Data and reproducibility

The repository includes 61 daily OHLC files. The canonical file-level hashes,
date ranges and quality findings are in
[`dataset_registry.csv`](reproduction/results/dataset_registry.csv). See the
[data note](dataset/README.md), [reproduction guide](reproduction/README.md),
and [evidence index](reports/README.md).

Install Python 3.11, then the PyTorch build appropriate for the machine and
`requirements/core.txt`. Foundation models are optional and intentionally
separated. The command in the Chinese section above is the canonical trained
model example; add `--no_use_gpu` for CPU.

### Scientific boundary and next work

The next valid comparison is a pre-registered modern baseline refresh with
asset-clustered uncertainty, rolling origins, multiple seeds/horizons, and
accuracy–compute reporting. A spectral or neural-operator residual may be tested
only as a matched architectural bias against ordinary MLP, convolution and
state-space controls. See the full
[literature map and plan](docs/LITERATURE_AND_NEXT_PLAN.md).

## Citation, provenance and licence

If using the original method, cite the 2026 Applied Soft Computing paper linked
above. TSLib provenance is documented in the source headers and history. This
fork is released under the [MIT licence](LICENSE); dataset and pretrained-model
terms must also be checked at their respective sources.
