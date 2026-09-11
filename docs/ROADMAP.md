# DeReFusion 复现与研究路线（ROADMAP）

> 更新：2026-09-11 ｜ 记录**已完成成果**与**待办清单**（含不在当日 18:00 计划内的部分）。
> 上游：Hsieh & Chen, *DeReFusion*, Applied Soft Computing 203 (2026) 116252。本仓库为其复现 fork。
> 复现资产集中在 `reproduction/`（见 `reproduction/README.md`），上游代码结构未改动。

---

## 仓库布局

```
reproduction/            复现资产（脚本/批次/结果）
  data/                  数据集重建脚本
  analysis/              工况分层分析、混淆诊断、汇总
  batches/               实验批次（PowerShell，串行）
  results/               分层分析结果（JSON/TXT）
docs/                    文档
  ROADMAP.md             本文件
  reports/               复现报告、工况分层报告
  latex/                 ASC（elsarticle）与 IEEEtran 两版论文格式报告
```

---

## 一、已完成（Completed）

### 1. 环境与数据
- 环境：Windows / Python 3.13 venv / PyTorch 2.14 (CPU) / MiKTeX。
- 数据重建：上游 `dataset/` 被 gitignore → `reproduction/data/fetch_dataset_v3.py`（urllib + 浏览器 UA，避开 yfinance 限流）
  自拉 10 资产日线 OHLC（2016–2025，26,920 行），行数与论文一致（股指/个股 2,513；FX 2,602；BTC 3,653；ETH 2,975），已 `git add -f` 入库。
- 上游修复：`exp/exp_basic.py` 的 emoji 打印导致 Windows GBK 控制台崩溃 → 改 ASCII（提交 37b612f）。

### 2. 论文核心实验复现（GSPC, seed 2021）
| 模型 | T=1 MSE | T=24 MSE | T=24 R² | 参数量 |
|---|---|---|---|---|
| DeReFusion（加法融合） | 0.0165 | **0.0623** | **0.869** | 28,436 |
| revin-DLinear（线性基座） | **0.0158** | 0.0701 | 0.853 | ~3k |
| gatev2-learnable（门控） | 0.0253 | 0.0719 | 0.849 | ~28k |

结论：**加法融合 > 线性 > 门控**（T=24），论文核心规律复现；参数量 28,436 ≈ 论文 ~26k。
报告：`docs/reports/derefusion-repro-report.md`（含 CP1–CP6 插入点与 6 条环境坑位）。

### 3. 工况分层评估框架（新增，论文未做）
- `reproduction/analysis/analyze_volatility_regimes.py`：按 realized volatility 分层 + 逐样本配对 bootstrap +
  交互效应检验 + 五分位性能曲线 + 与原始 npy 的对齐校验。
- 两种口径：`absolute`（输入窗口对数收益 std）与 `relative`（÷ 过去 120 样本中位波动率，严格因果）。
- **方法学发现**：绝对口径与时间段强相关（GSPC corr=+0.44，BTC corr=−0.67）；去趋势后 GSPC 中间分位的
  "线性反超"消失，模式变干净 → 跨资产比较应以 relative 为主口径。
- GSPC（relative, seed 2021）：高波动分位非线性显著占优（high20% +20.7%，胜率 82.3%），平静分位打平；
  交互效应 −0.0085 [−0.012, −0.005]。
- `reproduction/analysis/check_time_confound.py`：上述混淆诊断。
- 报告：`docs/reports/derefusion-volatility-stratification.md`；结果：`reproduction/results/`。

### 4. 跨市场复核（BTCUSD T=24）
- BTC DeReFusion：MSE 0.2180 / R² 0.8755（同协议、同种子）。
- BTC revin-DLinear 与分层分析：见当日批次产出（`reproduction/results/volatility_stratification_BTCUSD_*`）。

### 5. 论文格式产出
- `docs/latex/`：ASC（elsarticle，12 页，含 graphical abstract / highlights / CRediT）与 IEEEtran（双栏）
  两版复现报告源码与 PDF。

### 6. 工具链
- `reproduction/batches/`：GSPC 复现批次 v1/v2、BTCUSD 批次、无人值守流水线（带截止保护）。
- `reproduction/analysis/make_summary.py`：汇总 `result_long_term_forecast.txt` + 全部分层 JSON → 可读摘要（含机械判定 A/B/C）。

---

## 二、待办（Pending）

### A. 不在当日 18:00 计划内的部分（尚未执行）
1. **NS 结构化非线性算子（1D Burgers 类比）**：作为 CP1 新模型实现，替换 LSTM–Transformer 残差分支；
   判据为在高波动五分位击败**同参数量 MLP**（非全样本平均）。
2. **完整多种子网格**：5 seeds × {GSPC, BTCUSD, ETHUSD} × {DeReFusion, revin-DLinear}。
3. **补齐其余 7 个资产**：USDJPY、EURUSD、SOX、DJI、BABA、NVO、TM（论文 10 资产网格）。
4. **补全预测步长网格**：T ∈ {7, 12, 36}（当前仅 {1, 24}）。
5. **回看窗口网格**：L ∈ {48, 192}（当前仅 96）。
6. **门控族补全**：`DeReFusion-gatev3-inputconditioned` 从未运行。
7. **工况定义升级**：HMM / Markov-switching 状态识别替代波动率五分位。
8. **统计严谨性**：Diebold–Mariano 检验、Model Confidence Set、多种子置信区间（当前单种子 + 逐样本 bootstrap）。
9. **经济价值评估**：Sharpe / 回测（论文明确指出统计精度 ≠ 经济价值）。
10. **结构感知路由主线**：以本复现协议为公平性基础，实现 router + 资产/特征轴嵌入，GSPC → BTCUSD → hs300 面板。
11. **论文撰写**：复现 + 工况分层 + 路由实验整合为 ASC 投稿稿。

### B. 当日 18:00 批次覆盖的部分（自动运行中）
- gatev1-volatilityaware（GSPC T=24）总体指标判定
- GSPC seed 2022 / 2023 稳健性
- ETHUSD 跨资产复核
- BTCUSD 分层报告填实 + 多资产稳健性报告

---

## 三、已知坑位（复现必读）

1. 隐式依赖：`patool`、`huggingface_hub`、`sktime`(+`scikit-base`)、`datasets` 为 data pipeline 无条件导入。
2. `sktime` 安装需 `pip download`（可续传）+ 本地 whl；`joblib` pin `1.5.3`。
3. CPU 必须 `--no_use_gpu`。
4. Windows：`PYTHONIOENCODING=utf-8`；PowerShell 5.1 读含中文的 `.ps1` 会按 ANSI 解析报语法错 → **批次脚本保持纯 ASCII**。
5. exec 后台进程超时上限（本机 3h）：超时杀外壳，已落盘结果不受影响；长批次用截止保护 + 状态日志。
6. 结果目录名含 seed（`..._seed{seed}_0`），多种子不互相覆盖。
7. `results/`、`checkpoints/`、`result_long_term_forecast.txt` 被 gitignore，需本地生成。
