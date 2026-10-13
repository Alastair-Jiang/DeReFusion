# 交接给 Codex：第一批可执行任务（V1）

来源：`ENGINEERING_PLAN.md`（同目录）E 节；问题证据：`FINDINGS.json`；输入基线：`INPUT_HASHES.json`。
交接时仓库状态：分支 `docs/project-status-catalog-2026-10-10`，HEAD `5a8220ab0fdfb72601671f9fadf7de5e8a3b7554`。本目录工件为新增、未提交。
接续前先核对 HEAD 与本文件记录一致；若已移动，停止并按实际状态重新固定输入（本计划全部 pin 以 `5a8220a` 为基线）。

**硬边界（全程有效）**：不修改冻结执行器/协议/结果（两批均含）、不修改顶层 `models/derefusion/DeReFusion.py` 与 `layers/RevIN.py`、不修改 `research_work/forward_increment/` 原目录、不动工作区 76 项既有改动；数据/NPZ/预测/checkpoint 保持本地，任何提交前按任务 1 的边界核对；不读取测试角色数组；除任务 4 明确授权的合成级验证外不训练。提交与推送只在用户明确授权后进行。

---

## 任务 1（P0）：私有/可提交边界清单——先做，后续任务的提交安全网

- 新文件：`docs/DRF_ARTIFACT_BOUNDARY_V1_2026-10-13.json`
- 内容：每条 `{path_glob, disposition(tracked|local-only|forbidden), basis}`，至少覆盖：
  - `data/**` → local-only（`.gitignore:153` `/data/`）
  - `**/*.npz`、`**/runs/**`、`**/model.pt`、`**/validation.predictions.csv` → local-only/forbidden（两批协议 publication 字段）
  - `research_work/forward_increment/**` → local-only 现状（未跟踪、未忽略；T1 只复制 6 个文件出区）
  - `research_work/project_management_2026_10_10/compression_pilot_2026_10_13/**` → tracked 候选（10 个文本文件，无数据）
  - `models/derefusion/bundle_v3_pin/**` → tracked 候选（任务 2 新建）
  - `.venv/**`、`checkpoints/**`、`dataset/**` → local-only（`.gitignore:109,165,152`）
- 验收：`git ls-files` 与清单 forbidden 集合求交集为空；清单本身入库。
- 不需要真实数据。依赖：无。

## 任务 2（P0）：模型源码 pin 版入 Git（修 FINDINGS C-01/C-13）

- 新增（内容=磁盘现字节，逐字节复制，不得重打行尾）：
  - 源 `research_work/forward_increment/lead_design_2026_10_07/adapter_candidate_2026_10_07/integration_candidate_v1/model_bundle_v3/source/models/derefusion/DeReFusion.py` → `models/derefusion/bundle_v3_pin/DeReFusion.py`，入库后 sha256 必须仍为 `468a861d4e616a414ec603df87128ebe55bafe5f296502b54aef8aed23e5b091`
  - 源 `.../source/layers/derefusion_components.py` → `models/derefusion/bundle_v3_pin/derefusion_components.py`，sha 必须仍为 `91ae3bce16f8d758be71987672144fe400dd5f6a65352bf040c90c678ccd0a33`
  - 源 `.../source/layers/RevIN.py` → `models/derefusion/bundle_v3_pin/RevIN.py`，sha 必须仍为 `a7dc201d7ce2604bbdc19262d7c9ba8073a665e70f7cb734543d640c63bcf5cc`（LF 行尾原样）
  - `models/derefusion/bundle_v3_pin/__init__.py`（0 字节）
  - `models/derefusion/bundle_v3_pin/BUNDLE_PIN_MANIFEST_V1.json`：三文件 sha、来源路径、等价性记录（同配置参数 21,743、同 seed=17 初始化 state_dict 排序 sha `564e61a1...` 与顶层单体版逐位一致、RevIN 仅行尾差异），以及"后续协议 pin 须含 __init__.py"条款
- 注意：复制后 `DeReFusion.py` 内 `from layers.RevIN import RevIN` / `from layers.derefusion_components import ...` 的 import 语义会随调用方 sys.path 变化——manifest 中写明：该目录是**字节级 pin 存档**，执行器引用时须按协议把调用方路径解析到存档目录或按新协议指定的方式加载；不要为"让 import 更自然"而改名/移动/加包结构。
- 验收：`git ls-files models/derefusion/bundle_v3_pin/` 为 5 文件；`sha256sum` 三项等于上述 pin；干净 worktree checkout 后文件字节一致。
- 不需要真实数据/训练。依赖：任务 1。

## 任务 3（P0）：压缩试验批工件 + 报告入 Git（修 C-02）

- `git add`：`research_work/project_management_2026_10_10/compression_pilot_2026_10_13/`（10 文件）与 `docs/DRF_CDD_ETH_COMPRESSION_MINIMAL_PILOT_2026-10-13.md`。
- 验收：`git ls-files` 该目录恰为 10 文件；与 `DELIVERABLE_HASHES_V1.json` 内记录逐项 sha 一致（该清单不含自身；当前其自身 sha `2cd892235280b46c2a7400261ab1b9ee00ca128b9a26f9b6035cfae128b2fda3`）。
- 不需要真实数据。依赖：任务 1；与任务 2 同批提交以最小化 HEAD 移动。

## 任务 4（P0）：CPU 环境 pin 与重建配方（修 C-05）

- 新文件 1：`requirements/torch-cpu.txt`
  ```
  --index-url https://download.pytorch.org/whl/cpu
  torch==2.5.1
  ```
- 新文件 2：`docs/DRF_CPU_ENVIRONMENT_RECIPE_V1_2026-10-13.md`：venv 创建（Python 3.11）、`pip install -r requirements/torch-cpu.txt -r requirements/core.txt`、验收命令与预期输出（`python -c` 打印 3.11.x / 2.5.1+cpu / 2.1.2）；注明 cu121 文件与本实验无关、CUDA 轮不保证与 CPU 轮逐位一致。
- 验收：新建临时 venv 按配方安装，版本三项符合；用该 venv 对 `run_pilot_v1.py` 做 import 级加载检查（`--help` 或 import 阶段，**不运行任何 phase**）。
- 不需要真实数据。依赖：任务 1。

## 任务 5（P0）：新 HEAD 重签程序文档（修 C-04/C-06，任务 2–4 提交后必需）

- 新文件：`docs/DRF_PROTOCOL_RESPIN_PROCEDURE_V1_2026-10-13.md`，内容要点（完整骨架见 ENGINEERING_PLAN T4）：
  1. 新协议副本更新 `head`/`branch`/bundle 路径（指向 `models/derefusion/bundle_v3_pin/`），重算全部 pin；
  2. 顺序 synthetic→prepare→release→run 重签发（各 phase 既有拒绝覆盖语义不变，旧工件保留）；
  3. 复现验收：新 RESULTS raw96 组 `state_tensor_sha256` == `1a438fc30394c45ac4552a14b6f1c26d8bd9b0dee1bac205259cb89611f96270` 且 `mse.F` == `2092.513855618721`；mixed48 组同理对照旧值；任何不符即停并记录，不得放宽；
  4. 限定同 OS 同 CPU 架构做逐位断言（FINDINGS U-06）；跨平台只比指标容差；
  5. 重建数据链（U-01 未核实）：qualify 重下→父批 prepare→压缩批 prepare，各步 sha 与既有 pin 比对，不符即停。
- 验收：文档桌面走查一遍（dry-run 到 release 之前）；**真正重签复跑属实验行为，须用户另行授权后单独立项**。
- 不需要真实数据/训练（文档任务）。依赖：任务 2–4。

## 任务 6（P1）：固定预处理模块 + 单元测试（ENGINEERING_PLAN B 节）

- 新文件：`reproduction/preprocessing/__init__.py`（空）、`reproduction/preprocessing/fixed_ohlc.py`、`tests/test_fixed_ohlc_preprocessing.py`。
- 接口按 B.2 签名冻结：`AggregationPlan(context_days, block_days, n_blocks, recent_days, channel_order=("open","high","low","close"))`、`canonical_json()`、`config_sha256()`、`position_spans_days()`、`aggregate_ohlc(x, plan)`；`TRANSFORM_ID="fixed-ohlc-block-aggregate"`、`TRANSFORM_VERSION=1`。
- 单元测试（全部合成数组，禁止真实数据）：
  1. 与冻结执行器 `aggregate()`（测试内 import `run_pilot_v1.py`，不修改它）在全合成域逐位一致——随机多形状合法输入；
  2. 块边界 O/H/L/C 选取、尾部 32 行原样、末端 Close 精确；
  3. 正仿射交换 rtol=0、atol=2e-14；
  4. 非有限/错形状/非法 plan 全 `ValueError`；
  5. `config_sha256` 稳定性与区分性。
- 验收：测试全绿。不需要真实数据。依赖：无强依赖（联测模型形状时可用任务 2 的 pin 路径）。

## 任务 7（P2）：raw48 对照组协议草案（实验方案变化，只交付草案）

- 新文件：`research_work/project_management_2026_10_10/compression_followup_2026_10_1X/PROTOCOL_V0.1-DRAFT.json`（日期以实际为准；**草案，不签发、不执行**）。
- 三臂 `raw96/mixed48/raw48`；raw48 = 同一已缩放父批数组的尾部 48 天切片，不重拟合 scaler；预算/门控沿用 V1 量级；manifest 增加 `position_spans_days`；保留"不据本批验证分数挑选方案"声明；可接受误差界留空待研究侧填。
- 工程预断言（草案附带，合成数据可验）：raw48 与 mixed48 模型参数形状一致（同 seq_len=48 → 21,599）、同 seed 初始化逐位一致、persistence 跨组逐键相等的断言写法。
- 验收：草案交研究侧评审；执行须等新释放。依赖：任务 5；研究判断 J-01/J-02/J-03 未填前不得签正式协议。

---

## 明确不属于本批交接的事

- 重签复跑、raw48 实际训练、任何测试集读取/评分：须用户授权 + 新执行释放。
- 压缩批独立复核（J-04）：按父批 DSH 处置建议，下一轮优先"独立原始数组抽查"，由用户指定独立方。
- 旧 Yahoo 四资产处置（U-05）：维持隔离，单独议题。
- 对外摘要发布（U-02）：单独审查。
