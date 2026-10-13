# SOURCE_REPORT — DeReFusion 论文来源与全文可及性（只读）

检查时间：2026-10-13 14:43–15:1x（+0800）
仓库：`C:/Users/26843/Documents/ChatGPT/redefusion`
实际检查版本：分支 `docs/project-status-catalog-2026-10-10`，HEAD `db308d2b3bdf4fc14339ea4652974f4e6765e36c`（与交接值一致；本次检查期间未变）。工作区脏：6 个已跟踪文件被修改（`README.md`、`docs/DRF_TAKEOVER_STATUS_CORRECTION_V1_2026-10-10.md`、`docs/PROJECT_STATUS_AND_EXPERIMENT_CATALOG_V1_2026-10-10.md`、`reproduction/analysis/receive_phase1_completed.py`、`reproduction/results/phase1/local-5060-manifests/freeze-summary.json`、`tests/test_phase1_completed_receiver.py`）+ 大量未跟踪。未修改任何既有文件、未提交/推送。
边界遵守：未训练、未评分、未读 test 数组、未使用凭据、未付费、未绕过付费墙、未联系作者、未复制论文到仓库。

## 1. 直接结论：本机存在合法已有全文（这是本轮的关键新发现）

| 项 | 值 |
|---|---|
| PDF | `C:\Users\26843\Desktop\project\02_papers\DeReFusion_ASOC_2026.pdf` |
| PDF SHA-256 | `69b1dfcb6f4566917037ff50d5b28c8a32af385db40857e244bfc7345340cba7`（11,211,549 B，mtime 2026-09-09T00:08:54） |
| 全文文本（本地抽取件） | `C:\Users\26843\Desktop\project\02_papers\txt\DeReFusion_ASOC_2026_fulltext.md` |
| 全文文本 SHA-256 | `023d134450be5c62b140dc6c85c2d5fd83f0bab9fc9ab0693e3581d5120309f5`（315,026 B，mtime 2026-09-09T00:15:16） |
| 身份依据（我直接读到的，非摘要） | 标题/作者 `Chih-Chien Hsieh, Mu-Yen Chen`（Department of Engineering Science, National Cheng Kung University, Tainan）；`https://doi.org/10.1016/j.asoc.2026.116252`（fulltext L44）；`Applied Soft Computing 203 (2026) 116252`（多页眉）；`Received 4 May 2026; Received in revised form 22 July 2026; Accepted 17 August 2026`（L45）；39 个页标记（第1–39页） |
| 我实际阅读范围 | 全文抽取件的以下区段（均按 hashed 文件的**行号**定位）：L1–40（题名/作者/Highlights/摘要头）、L95–134（引言与架构主张）、L300–374（§3 方法学、问题表述、RevIN）、L430–618（§3.4 残差分支、Algorithm 1、Eq 7–9、Table 2、§4.1 数据）、L618–737（§4.2 预处理/切分/窗口、§4.3 指标）、L738–837（Table 3 超参、§4.4 实现细节）、L1020–1060（目标通道/门控分析，抽查）、L1555–1594（Table 10 参数计数叙述）、L15185–15202（Data availability）。其余（结果表、消融表、附录）**未逐页精读**。 |

全文有再分发限制（论文明确"raw downloaded data are not redistributed"；出版社版权归 Elsevier），因此**未**把 PDF/文本复制进仓库，本报告只记路径与哈希。

## 2. 与项目既有记录的关系（证据分级）

- **新增：全文可直接核验**。`compression_diagnostic_2026_10_13_v2/PAPER_FIDELITY_CROSSWALK_V1.md` 与 qwen03 的 `PAPER_SOURCE_ADDENDUM_*` 均以"只有出版社摘要可见、全文 UNVERIFIED"为前提；本机 `Desktop\project\02_papers` 早在 **2026-09-09** 就已有全文与提取件。项目此前的检索范围限定在仓库 `docs/`、`research_work/`，未扩展到本机论文保存目录，因此"未找到全文"是**范围限制**的结果，不是全文不存在。
- **项目记录的摘要级陈述**（A 级，仍不是全文证据）：`PAPER_SOURCE_ADDENDUM_2026-10-06.md`（摘要含 DLinear/LSTM–Transformer/RevIN/相加）、`PAPER_SOURCE_ADDENDUM_CORRECTION_2026-10-07.md`（补充 Available online 2026-08-21、article 203/116252、十基准、Yahoo 十资产 2016–2025）。
- **本轮直接核验后与摘要一致的项目陈述**：架构两分支、RevIN、直接相加、融合算子受控比较、Yahoo 十资产 2016–2025 —— 均已在全文命中（见 `PAPER_VS_REPO_TABLE.md`）。

## 3. 作者官方实现（本轮新识别，未获取）

论文 Data availability（fulltext L15190–15198）明确：数据由 `yfinance` 以 2016-01-01 至 2025-12-31 取得、原始数据**不再分发**，而"数据获取与预处理代码，包括 ticker 与样本期"位于：

- **`https://github.com/twcch/DeReFusion`**

我于 2026-10-13 只读取该仓库**落地页**用于身份记录（HTTP 200）：页面标题自述为 "A simple-by-design Decomposition–Residual Fusion forecaster and fair benchmark for non-stationary financial time series. **Built on thuml/Time-Series-Library.**"。
**未** clone、**未**下载其代码、**未**比较其实现、**未**把它当作本项目实现（也未把本项目当作它）。仓库全库检索 `twcch` 命中 0 次 —— 项目此前未记录作者官方仓库地址。

## 4. 检索范围与失败记录

| 检索 | 范围 | 结果 |
|---|---|---|
| 文件名/元数据筛查 | `C:\Users\26843\Downloads`、`Desktop`、`Documents`（递归，按 `derefusion`/`hsieh`/`asoc`/`116252`/`S156849462601700X`） | **命中全文 PDF + 提取文本**（见 §1）；另命中大量**项目自身**交接/复现资料（非论文） |
| 仓库内筛查 | `PAPER_FIDELITY*`、`compression_diagnostic*`、`paper` 相关 | 命中 crosswalk 与 V2 目录；**未**在仓库内发现论文全文 |
| 作者官方代码 | 论文给出的 GitHub URL | 落地页可达（HTTP 200）；**未**获取内容 |
| 出版社页面 | ScienceDirect（DOI 与 pii） | **本轮未重试**（项目既有记录 2026-10-06 直开返回 403；不绕过）。本地已有合法全文，不构成阻碍 |
| 机构仓储 / 作者主页 | — | **未检索**（首轮 30 分钟预算内，本地全文已满足核验需要） |

失败/未竟项如实记录：出版社直开 403（历史记录）、机构仓储未查、作者代码未获取。**不**据此声称论文不存在或不可得。

## 5. 证据分级小结

1. **直接核实（全文）**：题名/作者/期刊/DOI/日期、Highlights、§2.4 RevIN 论证、§3 架构与 Algorithm 1、Eq 7–9、§4.1 数据、§4.2 切分与窗口、§4.3 指标、Table 3 超参与收敛配置、§4.4 环境、Table 10 参数叙述、Data availability 与官方代码 URL。
2. **仅来自摘要/项目记录**：无（本轮关键项已升级为全文证据）；项目记录中的"作者无官方代码"已被证伪（存在 twcch/DeReFusion，但未获取）。
3. **仍未核实**：作者代码实际内容；Table 10 的精确数值单元格（我只读到叙述"about 26k"）；每资产精确切分日历点；Table 3 的 d_model=16 与 ~26k 参数之间的论文内部一致性（见对账表容量行）。
