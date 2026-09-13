# Reproduction assets — DeReFusion (Applied Soft Computing 203, 2026)

本目录收录对 Hsieh & Chen, *DeReFusion*（ASC 203, 2026, 116252）的复现资产。
**上游代码库结构保持不变**（`run.py`、`exp/`、`models/`、`data_provider/`、`utils/`、`layers/`、`scripts/<task>/` 等），
本目录只承载复现新增的脚本、批次与结果。所有命令均**在仓库根目录执行**。

---

## 目录结构

```
reproduction/
├── README.md                      # 本文件
├── data/                          # 数据集重建（上游 dataset/ 被 gitignore，需重建）
│   ├── fetch_dataset.py           # 10 资产日线 OHLC 抓取（初版）
│   ├── fetch_dataset_v2.py
│   └── fetch_dataset_v3.py        # 现行版本（urllib 直连 Yahoo chart API，UA 必带）
├── analysis/
│   ├── analyze_volatility_regimes.py   # 工况分层评估（核心）
│   ├── check_time_confound.py          # 波动率分层 vs 时间段 混淆诊断
│   ├── make_summary.py                 # 汇总 result log + 分层 JSON → 摘要
│   └── run_ns_hypothesis_benchmark.py  # 锁定 manifest 后的独立算子基准（默认只预检）
├── configs/
│   └── ns_hypothesis_benchmark.example.json
├── batches/                       # 实验批次（PowerShell，串行）
│   ├── run_batch_repro.ps1        # GSPC 复现批次 v1
│   ├── run_batch_repro2.ps1       # GSPC 复现批次 v2（3 模型 × 2 时域）
│   ├── run_btc_repro.ps1          # BTCUSD T=24 跨市场复核
│   ├── run_btc_revin.ps1
│   └── run_afternoon_batch.ps1    # 无人值守流水线（等待→分析→队列→摘要，带截止保护）
└── results/                       # 分层分析结果（JSON/TXT）
```

---

## 环境

- Windows / Python 3.13（venv）/ PyTorch 2.14 **CPU** / MiKTeX（LaTeX 报告另见 `docs/latex/`）
- 安装要点（复现时踩过的坑）：
  - 隐式依赖：`patool`、`huggingface_hub`、`sktime`(+`scikit-base`)、`datasets` —— 缺一即崩
  - `sktime` 若 pip 直连断流：`pip download`（可续传）+ 本地 whl 安装；`joblib` 需 pin `1.5.3`
  - CPU 环境**必须**加 `--no_use_gpu`（`run.py` 默认 CUDA 并 assert）
  - 控制台建议设 `PYTHONIOENCODING=utf-8`

## 数据

```powershell
# 在仓库根目录
.venv\Scripts\python.exe reproduction/data/fetch_dataset_v3.py
```
生成 `dataset/<ASSET>-2016-2025.csv`（date,Open,High,Low,Close）。行数须与论文一致：
股指/个股 2,513；FX 2,602；BTC 3,653；ETH 2,975。仓库已 `git add -f` 入库这 10 个 CSV。

## 复现实验

```powershell
.venv\Scripts\python.exe run.py --task_name long_term_forecast --is_training 1 `
  --model_id GSPC_96_24 --model DeReFusion --data custom --root_path ./dataset/ `
  --data_path GSPC-2016-2025.csv --features MS --target Close --freq b `
  --seq_len 96 --label_len 48 --pred_len 24 --enc_in 4 --dec_in 4 --c_out 1 `
  --d_model 32 --moving_avg 25 --train_epochs 30 --batch_size 32 `
  --learning_rate 0.0001 --patience 5 --lradj cosine --rand_seed 2021 --no_use_gpu
```
换模型只需改 `--model`（`DeReFusion` / `revin-DLinear` / `DeReFusion-gatev1-volatilityaware` / `...-gatev2-learnable` / `...-gatev3-inputconditioned`）；
换资产改 `--data_path` 与 `--model_id`。结果目录名含种子（`..._seed{seed}_0`），多种子不会互相覆盖。

## 工况分层分析

```powershell
# 绝对波动率（对照口径）
.venv\Scripts\python.exe reproduction/analysis/analyze_volatility_regimes.py `
  --csv dataset/GSPC-2016-2025.csv --tag GSPC --seed 2021 --rv-mode absolute
# 相对波动率（主口径；去趋势，避免与时间段混淆）
.venv\Scripts\python.exe reproduction/analysis/analyze_volatility_regimes.py `
  --csv dataset/GSPC-2016-2025.csv --tag GSPC --seed 2021 --rv-mode relative
```
输出 `reproduction/results/volatility_stratification_<TAG>_<MODE>_s<SEED>.json|txt`，内含：
分层（最低/最高 20%、低/高半区）的 MSE/MAE/MSPE/95% 分位误差、逐样本配对 bootstrap 95%CI、胜率、
交互效应 (Δ_high50 − Δ_low50)、五分位性能曲线。

> **口径提醒**：绝对波动率与时间段强相关（GSPC corr=+0.44，BTC corr=−0.67）。跨资产比较应以
> `relative` 口径为主判定，`absolute` 仅作对照。

## 批次脚本

```powershell
# 全批次（串行，含截止保护）
powershell -NoProfile -ExecutionPolicy Bypass -File reproduction/batches/run_afternoon_batch.ps1
```
> 注意：Windows PowerShell 5.1 读取含中文的 `.ps1` 会按 ANSI 解析而报语法错，**批次脚本保持纯 ASCII**。

## Temporal NS-inspired nonlinear operator benchmark

`run_ns_hypothesis_benchmark.py` 是独立代理基准，不修改或接入 DeReFusion。它固定运行
MLP、普通因果时序卷积、非选择性 SSM 和 temporal NS-inspired nonlinear operator；所有模型
使用同一锁定输入视图、种子、切分与训练预算。默认只检查 manifest，不训练也不写输出：

```powershell
.venv\Scripts\python.exe reproduction/analysis/run_ns_hypothesis_benchmark.py `
  --manifest reproduction/configs/ns_hypothesis_benchmark.example.json
```

执行前，OpenClaw 需要把模板替换成已锁定的 manifest，提供完整资产列表与 SHA-256、`C1_REPLICATED`
资格证据报告路径及事先写定的证伪文字。只有显式 `--execute` 才会训练；执行器拒绝未锁定
manifest、缺失资格证据、哈希不匹配、缺少任一普通基线或已有输出目录。每个运行会保留预测、
目标、逐样本平方误差、前瞻性 `closure_q` 探测器和配对 bootstrap 汇总。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File reproduction/batches/run_ns_hypothesis_benchmark.ps1 `
  -Manifest path\to\locked-manifest.json -Execute
```

## 结果与报告

| 位置 | 内容 |
|---|---|
| `reproduction/results/` | 分层分析原始结果（JSON/TXT） |
| `docs/ROADMAP.md` | 已完成 / 待办清单 |
| `docs/reports/` | 复现报告、工况分层报告 |
| `docs/latex/` | ASC（elsarticle）与 IEEEtran 两版论文格式报告 |

## 已知坑位

1. `results/`、`checkpoints/`、`result_long_term_forecast.txt` 被 gitignore（体积大），需本地生成。
2. exec 后台进程有超时上限（本机 3h）：超时会杀外壳，但已落盘的结果不受影响；长批次请用 `run_afternoon_batch.ps1` 的截止保护。
3. 上游 `exp/exp_basic.py` 的 emoji 打印会导致 Windows GBK 控制台崩溃，本 fork 已改为 ASCII（提交 37b612f）。
4. `scripts/` 下的 `analyze_volatility_regimes.py` / `make_summary.py` 为**临时兼容入口**（转发到本目录），
   仅为让 2026-09-11 启动的批次跑完，随后删除。
