# DeReFusion 固定压缩工程化计划（K3 规划，V1）

规划人：Claude Code 工程化规划负责人（Kimi K3）。
日期：2026-10-13。主仓库 `C:\Users\26843\Documents\ChatGPT\redefusion`；分支 `docs/project-status-catalog-2026-10-10`；HEAD `5a8220ab0fdfb72601671f9fadf7de5e8a3b7554`（与远程该分支一致，已 `git ls-remote` 核实）。
审查对象：`compression_pilot_2026_10_13`（压缩最小试验，全部未提交）与 `shrink_exploration_2026_10_13`（父批，已跟踪）的全部协议、执行器、结果与审计工件，以及 `model_bundle_v3/source`、顶层 `models/derefusion/`、`requirements/`、`.gitignore`、`reproduction/README.md`。
已读输入的逐文件 SHA-256 见同目录 `INPUT_HASHES.json`；结构化问题清单见 `FINDINGS.json`。
本计划只新增本目录工件：不修改冻结执行器、协议、结果、模型源码与任何已有改动；不训练、不评分、不读取测试角色数组；不提交、不推送 Git。

---

## A. 现有工程链能否独立运行

结论：**当前不能。** 从干净 Git checkout 出发，压缩最小试验与父批 shrink 试验都无法复跑。阻断点按严重度如下，每条附实际证据。

### A.1 已证实的阻断点

| # | 缺口 | 证据（文件:行 / 命令输出） | 影响 |
|---|---|---|---|
| A1 | **执行器 pin 的模型源码不在 Git 中，也不在远程** | 父协议 `SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json` 的 `model.bundle` 指向 `research_work/forward_increment/lead_design_2026_10_07/adapter_candidate_2026_10_07/integration_candidate_v1/model_bundle_v3/source`；`git ls-files research_work/forward_increment/` 输出为空；`git check-ignore -v` 对该路径退出码 1（未被忽略，只是从未 `git add`）。磁盘上 3 个 pin 文件哈希与父协议 `source_sha256` 逐项一致 | 干净 checkout 后 `verify_sources()`（`run_pilot_v1.py:67-77`、`run_shrink_cdd_v1_1.py:40-43`）必然报 `Model source drift`，任何 phase 都无法启动 |
| A2 | **压缩试验整批工件未提交** | `git ls-files research_work/project_management_2026_10_10/compression_pilot_2026_10_13/` 输出为空；目录含执行器 `run_pilot_v1.py`、协议、结果、审计、哈希清单共 10 个文件 | 远程连试验的存在和执行器源码都不可见；与交接快照"本地未提交候选"一致 |
| A3 | **训练/验证输入全部是本机私有 NPZ（gitignored）** | `PREPARATION_V1.json` 记录的四个包路径均在 `data\shrink-cdd-20261013-v1\` 与 `data\cdd-compression-pilot-20261013-v1\`；`.gitignore:153` 为 `/data/`。本批复核四个包 sha256 与 PREPARATION pin 逐项一致 | 干净 checkout 无输入；须按下文 A.4 链式重建 |
| A4 | **worker 强制本机绝对路径** | `run_pilot_v1.py:243-245`：`Path(prepared[role]['path']).resolve() != Path(path).resolve()` 即拒绝；PREPARATION 记录的路径含 `C:\Users\26843\...` | 换机、换盘符、Linux/macOS 上即使重建了字节一致的 NPZ，worker 也拒绝；须重走 prepare+release 链重签路径 |
| A5 | **CPU 实验环境无重建配方** | `EXECUTION_RELEASE_V1.json` 记录 `torch 2.5.1+cpu / python 3.11.15`；本机仓库 `.venv`（gitignored，`.gitignore:109`）实测正是该版本组合；`requirements/torch-cu121.txt` 只 pin `torch==2.5.1` + cu121 index（CUDA 轮，非本实验所用 CPU 轮）；`requirements/core.txt` pin `numpy==2.1.2`（与 `.venv` 实测一致）；`reproduction/README.md` 只写"Recommended: Python 3.11 and torch 2.5.1" | 远程无法确定地重建 `2.5.1+cpu`；torch 轮差异（cpu/cu）不保证逐位一致的训练轨迹 |
| A6 | **HEAD pin 与"补依赖需新提交"的结构性张力** | `run_pilot_v1.py:67-69` 要求当前 HEAD == 协议 `head`（`5a8220a...`）；修复 A1/A2/A5 必然产生新提交、移动 HEAD | 直接补提交后，旧协议/旧释放立即失效。必须走 A.4 的重签程序，不能"提交后直接复跑" |

### A.2 已核实的正面事实（不要当成缺口重做）

- **字节级架构等价已验证**：顶层已跟踪 `models/derefusion/DeReFusion.py`（sha `7e5194f7...`）与 bundle pin 版（sha `468a861d...`）是同架构的两份源码（单体内嵌 vs 拆分到 `layers/derefusion_components.py`）。用本机 `.venv` 实测：同配置（seq_len=96 等）两者参数数均为 21,743，`named_parameters` 名称与形状逐一对齐；同 seed=17 初始化后 state_dict 排序哈希**逐位一致**（`564e61a1...`）。`layers/RevIN.py` 顶层与 bundle 版仅在行尾（CRLF vs LF）不同，去 CR 后逐字节一致。bundle 三个 `__init__.py` 均为 0 字节（未被父协议 pin 覆盖——小缺口，见 FINDINGS D-09）。
- **NPZ 字节级确定性已验证**：`np.savez`（无压缩）写出的 zip 条目时间戳固定为 1980-01-01（numpy 行为，本机 `.venv` numpy 2.1.2 实测同一数组间隔 1.2s 两次保存字节相同）。故"重建 NPZ 字节复现 PREPARATION pin"在 numpy 版本一致时成立。这是 numpy 实现行为而非格式标准，重建配方必须 pin numpy 并实测验证。
- **checkpoint 张量级绑定不受容器影响**：`run_pilot_v1.py:293-295` 的 `state_tensor_sha256` 对排序后 key+tensor bytes 取哈希；`audit_and_report_v1.py:67-70` 已用 checkpoint 重算复算通过。torch.save 容器字节可变性不影响该绑定。
- **父批数据获取链完整且已跟踪**：`source_bootstrap_v1.py`（供应商页面快照）→ `CDD_LOCAL_RESEARCH_QUALIFICATION_RELEASE_V1.json`（资质释放）→ `qualify_cdd_v1.py`（host 白名单 `api/www.cryptodatadownload.com`、2 MiB 上限、OHLC QA、release 门控）→ `run_shrink_cdd_v1_1.py prepare`（raw.csv→NPZ，键/manifest/scaler 绑定）→ `run_pilot_v1.py prepare`（父包→mixed48 包）。每一环都有 pin 校验与拒绝覆盖。

### A.3 无本机历史产物时的合法重建链（A.4 的答案）

前提：A1/A2/A5 先修复（否则执行器与模型源码都拿不到）。链如下，每步注明 pin 校验点：

1. 干净 checkout 到补依赖后的新 HEAD；按新 `requirements/torch-cpu.txt`（拟新增，见 E 节 T3）建环境。
2. `python research_work/.../shrink_exploration_2026_10_13/qualify_cdd_v1.py`：重下两资产 raw.csv（需资质释放 `head` 字段与当前 HEAD 匹配——**该释放 pin 的是旧 HEAD `a74126c...`，须按既有释放程序重签**；且上游 CDD 文件字节必须仍等于父协议 `raw_sha256` pin——见未核实事项 U1）。
3. `python run_shrink_cdd_v1_1.py --phase prepare`：raw.csv→NPZ。确定性（A.2 第二条），产物 sha 应复现 `CDD_PREPARATION_MANIFEST_V1_1.json` pin；不一致即停，不得强行继续。
4. `python run_pilot_v1.py --phase prepare`：父包→mixed48 包，应复现 `PREPARATION_V1.json` pin。
5. 绝对路径问题（A4）：新机器路径不同，PREPARATION 内嵌路径必然变化，因此**重建后须按执行器既有程序重新 synthetic→prepare→release→run 全套签发**，旧 RESULTS 的复现性靠"新 RESULTS 的 `state_tensor_sha256` / `validation_mse` 与旧值比对"来验收（raw96 组应逐位复现 `1a438fc3...`；这正是本批已用过的父子批对照方法，`run_pilot_v1.py:348-353`）。

### A.4 随机性、平台与入口明确性评估

- 随机性：明确。`torch.use_deterministic_algorithms(True)`、双 `manual_seed(17)`、DataLoader `generator` seed 17、线程数 2（环境变量 + `torch.set_num_threads`），见 `run_pilot_v1.py:2-4, 89-92, 253-254`。
- 平台：训练与聚合跨平台可跑；`peak_working_set()` 仅 Windows（`run_pilot_v1.py:100-116`），其他平台记 null（summary 字段仍在）。定时用 `perf_counter/monotonic`，跨平台正确。
- 入口：`--phase {synthetic,prepare,release,run,worker}` 五段式（`run_pilot_v1.py:363-377`），顺序由 release 门控强制；但压缩批目录**无 README** 写明该顺序与环境前提——小缺口（T6）。

---

## B. 固定预处理模块的工程接口设计

现状：`aggregate()` 是冻结执行器内嵌函数（`run_pilot_v1.py:79-85`），无独立模块、无版本号、无显式配置序列化/配置哈希、无形式化缓存键。以下设计**只新增、不改动冻结执行器**；未来批次的执行器 import 新模块，本批 `aggregate()` 原样保留作历史锚点。

### B.1 模块位置与形态（最小方案）

```
reproduction/preprocessing/__init__.py            （空）
reproduction/preprocessing/fixed_ohlc.py          （纯函数 + 配置 + 错误处理）
tests/test_fixed_ohlc_preprocessing.py            （不触碰真实数据的单元测试）
```

放 `reproduction/` 而非 `research_work/`：前者是仓库已确立的可跟踪复现代码区（`reproduction/README.md` layout 节），后者是批管理工件区。测试放既有 `tests/`（该目录已有 `test_phase1_completed_receiver.py` 等先例）。**不新建顶层包、不改 `exp/`、`models/`、冻结执行器。**

### B.2 接口签名与语义

```python
# reproduction/preprocessing/fixed_ohlc.py
TRANSFORM_ID = "fixed-ohlc-block-aggregate"
TRANSFORM_VERSION = 1

@dataclass(frozen=True)
class AggregationPlan:
    context_days: int      # 原始窗口长度（本批 96）
    block_days: int        # 聚合块天数（本批 4）
    n_blocks: int          # 聚合块数（本批 16）
    recent_days: int       # 尾部保留日线天数（本批 32）
    channel_order: tuple = ("open", "high", "low", "close")  # 冻结，不可配置

    def __post_init__(self):  # 非法配置即拒绝
        if self.block_days * self.n_blocks + self.recent_days != self.context_days:
            raise ValueError(...)
        if min(self.context_days, self.block_days, self.n_blocks, self.recent_days) <= 0:
            raise ValueError(...)

    def canonical_json(self) -> str:   # 键排序、无空白、ensure_ascii=False
    def config_sha256(self) -> str:    # sha256(canonical_json)
    def position_spans_days(self) -> list[int]:  # 每位置天数跨度：[4]*16+[1]*32，供 C 节元数据

def aggregate_ohlc(x: np.ndarray, plan: AggregationPlan) -> np.ndarray:
    """x: (n, context_days, 4)，任意实数 dtype；返回 (n, n_blocks+recent_days, 4)，同 dtype。
    块内 O=首日 O、H=max H、L=min L、C=末日 C；尾部 recent_days 行原样保留。
    纯函数：不改输入、无 I/O、无随机、无全局状态。
    拒绝：ndim!=3、第二维!=context_days、第三维!=4、非有限值。"""
```

语义锚点：`aggregate_ohlc(x, AggregationPlan(96, 4, 16, 32))` 必须与冻结执行器 `aggregate()` 在全定义域逐位一致——这是单元测试的第一条（用合成数组，不用真实数据）。

### B.3 关键工程决定（逐条绑定证据）

1. **缩放与聚合的顺序保持"先缩放、后聚合"**。父批 `package()`（`run_shrink_cdd_v1_1.py:62-87`）在打包前完成 channelwise population 缩放，压缩批 `prepare()` 对已缩放数组聚合。合成检查已验证正仿射变换与聚合交换（`run_pilot_v1.py:160-161`，rtol=0、atol=2e-14），因此模块**接受已缩放输入**，scaler 不进入本模块；缩放器绑定留在包层（NPZ 内 `close_output_std` 等字段），避免两处各存一份真相。
2. **键/目标不变性**：变换只改 x，不改 y、keys、scaler；每个输出位置对应的"目标 candle 键"不变（聚合的是输入上下文，不是目标）。位置→原始日期的映射由 `plan.position_spans_days()` 与包 manifest 共同记录。
3. **缓存键形式化**：`cache_key = sha256(source_package_sha256 | plan.config_sha256() | module_file_sha256 | numpy_version)`。本批 prepare 已隐式含其中三项（PREPARATION 记录源包 sha 与 runner sha）；新执行器应把四元组显式写入派生包 manifest。命中即跳过重建，不命中即重建并记录——重建产物仍走"拒绝覆盖 + 新目录"惯例。
4. **历史保留**：任何 plan/config/code 变更 → `TRANSFORM_VERSION` 升版 + 新派生目录；旧包、旧 manifest 一律不删不改（沿用两批既有的 exists-即拒惯例，`run_pilot_v1.py:59-65, 322, 329-330`）。
5. **测试隔离不进入模块**：模块无角色概念；角色边界留在执行器/worker 层（现有 `run_pilot_v1.py:370-372` worker 拒收 test 参数的模式）。单元测试只用合成数组，真实数据验收走"派生包 sha 复现 pin"比对。
6. **dtype 透传**：`astype(x.dtype, copy=False)`（与冻结实现一致），float32 进 float32 出；聚合本身在 numpy 内完成，H=max/L=min 对 float32 精确，O/C 是选取，无数值漂移源。

### B.4 输入/输出契约汇总

| 项 | 约定 | 依据 |
|---|---|---|
| 输入形状 | `(n, 96, 4)` float32（本批）；模块按 plan 泛化 | `read_role` 校验 `run_pilot_v1.py:128` |
| 通道顺序 | 固定 OHLC，索引 0..3 | 父批打包 `run_shrink_cdd_v1_1.py:71-80` |
| 单位 | 训练缩放后的无量纲单位；原始单位 USD/ETH 仅经 scaler 还原 | 父协议 `preprocessing` 字段 |
| 时间跨度 | 输入窗口 96 个已完成日线；输出前 16 位置各跨 4 天、后 32 位置各跨 1 天 | `PROTOCOL_V1.json` `arms.mixed48.transform` |
| 输出形状 | `(n, 48, 4)` 同 dtype；y/keys/scaler 原样随包传递 | `PREPARATION_V1.json` mixed48 shape |
| 错误处理 | 非有限/错形状/非法 plan → `ValueError`，fail closed | 与 `read_role`/`aggregate` 现有行为一致 |

---

## C. 混合时间尺度与公平对照

问题（协议已声明，`PROTOCOL_V1.json` `mixed_time_resolution_caveat`）：mixed48 的前 16 位置跨 4 天、后 32 位置跨 1 天，模型等权处理；`moving_avg=25` 的实际墙钟跨度随位置从 100 天变到 25 天；RevIN 对聚合块与日块等权。下列选项均不据本次验证分数挑选"最佳压缩"，只谈工程化对照。

### 选项 C-1（推荐，最小优先）：新增 raw48 等长对照组 + 位置跨度元数据

- **做什么**：下一协议加入第三组 `raw48`——仅取每窗口**最近 48 天日线**（同一已缩放父批数组的尾部切片，不重新拟合 scaler），`seq_len=48`；同时在派生包 manifest 记录每位置天数跨度（mixed48 用 `[4]*16+[1]*32`，raw48/raw96 恒 1）。
- **改变了什么**：mixed48 vs raw48 是同 `seq_len`、同参数形状、同初始化形状、同暴露次数的对照，回答"多覆盖的 64 天粗粒度历史相对纯 48 天日线是否有增量"；mixed48 vs raw96（本批已有）回答"同覆盖 96 天下分辨率降低的代价"。两个比较分开后，研究问题从"压缩整体好不好"变成可分离的两问。
- **工程事实**：raw48 与 mixed48 的模型参数数完全相同（seq_len 同为 48 → 21,599），同 seed 初始化**逐位一致**（参数形状决定抽样序列，已实测同形同 seed 初始化逐位一致）；persistence 基线跨组逐键相等可作工程断言（本批已断言 raw96/mixed48 的 P MSE 相等，`run_pilot_v1.py:347`）。
- **成本**：约一组额外 fit（本批实测 mixed48 worker 12.6 秒量级）+ 一个派生包（尾切片，无聚合逻辑）+ 协议/执行器扩展。**不改模型源码、不改 bundle pin、不改 scaler。**
- **局限**：raw48 改变训练窗口覆盖，训练语境比 raw96 短（研究上须声明）；RevIN/moving_avg 语义差异在 mixed48 vs 任何纯日组的比较中仍然固有存在，C-1 不能归因它——只能把"覆盖"与"分辨率"分开。是否接受该语义代价、是否进入测试评估、seed 数量与可接受误差界，均属新研究协议判断，不在本工程方案内决定。

### 选项 C-2（次小）：仅元数据化，不加新组

- 只在 manifest/结果中记录位置跨度与 `moving_avg` 随位置的实际天数范围（前 16 位置 kernel=25 覆盖 100 天，尾部 25 天）。成本近零，但不产生任何新的区分能力，只改善报告准确性。可作为 C-1 的伴随项，不单独成案。

### 选项 C-3（不推荐现阶段做）：时长标记/架构改动

- 给模型加 position-duration 通道或 embedding，让网络知晓每位置跨度。需要改 `model_bundle_v3` 源码、改 pin、参数数变化、初始化变化，且引入新自由度，归因更复杂；属于新研究协议+新模型版本，工程量与审查量远超 C-1。现阶段不做。

### 工程可验证 vs 研究协议判断（明确分界）

- **工程可验证**：三组包形状/键/缩放一致性断言；raw48/mixed48 参数数与初始化逐位一致断言；persistence 跨组逐键相等断言；样本暴露相等断言；位置跨度元数据与 plan 重算一致断言。
- **仍须研究协议判断**：可接受精度代价界；seed 集合（本批单 seed 17）；是否允许测试评估；raw48 训练语境缩短的解释口径；"同覆盖"是否必须 96 天。本方案不替研究侧预设数值。

---

## D. 执行与资源管理：核验结果

先核验实现，缺口单列。**已有能力（不得当作缺失）**——全部在 `run_pilot_v1.py` 实测核对：

| 能力 | 实现位置 | 状态 |
|---|---|---|
| worker 硬超时 | `:335` `timeout=min(remaining, worker_seconds)`，subprocess 级 | 已实现，300s pin |
| 整批硬超时与剩余预算传递 | `:325-327` worker 前剩余<=0 拒；`:343-344` 批末超限拒；remaining 传给每个 worker | 已实现，900s pin |
| 输出字节上限 | `:57-65` `bounded_write` 写前累加私有目录字节比对 64 MiB pin | 已实现；实测输出 2,479,067 B |
| 覆盖拒绝 | `:49-50, 59-60` 公共/私有均拒覆盖；`:322, 329-330` RESULT 与 runs/<arm> exists 即拒 | 已实现 |
| 失败记录 | `:380-385` FAILURE_UTC 时间戳 JSON（含异常类型、原因、runner sha） | 已实现 |
| 显式重试（无静默重跑） | `:330` "Prior attempt exists; stop" | 已实现；**恢复是手动的**：须人工删除 runs/<arm> 后整批重跑（RESULT 拒覆盖）。2 组规模可接受；扩展到多组时这是 D-05 缺口 |
| checkpoint 身份绑定 | `:293-295` 张量级 sha；`:306-308` checkpoint 内嵌 summary；审计 `:67-70` 复算 | 已实现 |
| 验证选择 | `:269-275` 每 50 步完整 365 键、strict improvement、ties 留早 | 已实现 |
| 逐键预测 × 汇总绑定 | `:310-315` CSV(key,F,L,P,target) 与 fit.json 同目录；审计逐键恢复 F/L/P 并重算 MSE（`audit_and_report_v1.py:73-83`） | 已实现 |
| 样本暴露/参数数 | `:296-297` samples_seen=18,900、effective_epochs、parameters | 已实现 |
| 计时范围 | `:276` neural_seconds 仅训练循环（含 12 次验证）；`:334-339` worker_seconds 为 run 侧墙钟 | 已实现，**范围不含模型构建/包加载/ridge/序列化**——报告已声明，勿外推为端到端 |
| 内存测量范围 | `:277` 训练循环结束后、ridge 前读取进程峰值 working set；仅 Windows（`:101-102` 其他平台 null） | 已实现，范围声明准确；跨平台缺口见 D-04 |
| 测试输入隔离 | `:370-372` worker 拒收 test 参数；RESULTS `test_inputs_received:false` | 已实现 |

**缺口（已证实，按严重度）**：

- **D-01（高）执行器与模型源码不可远程获得**：即 A1/A2，资源管理再完善也无从谈起。
- **D-02（高）无 CPU 环境 pin**：A5。计时/内存/逐位复现都以 `2.5.1+cpu` 为前提，远程无法确定重建。
- **D-03（中）绝对路径耦合**：A4。跨机恢复须重走全签发链；建议下一版执行器把 PREPARATION 路径改为仓库相对并 resolve（属执行器修改，须走"新版执行器+新协议"路径，不得改冻结文件）。
- **D-04（中）内存测量仅 Windows**：`peak_working_set` 非 nt 返回 None。若 Mac Mini M4 参与复算，该指标缺失；可选方案：resource.getrusage（ru_maxrss，POSIX）作第二来源并在 summary 标注来源平台。
- **D-05（低）无批内进度持久化**：父批有 `RUN_PROGRESS.json`（`run_shrink_cdd_v1_1.py:319`），压缩批无等价物（2 组可接受）；扩展组数/seed 后须补"完成计数+尾批键覆盖"的进度文件，否则中断后无法区分"完成 1/2 组"与"未开始"。
- **D-06（低）批末超时检查位置**：`:343-344` 在全部 worker 完成后才断言批末未超时——超时批已产出的组不会回滚（设计如此，fail closed 保留证据），但报告侧应明示该语义，避免误读为"超时即无效"。
- **D-07（低）私有/可提交区分靠惯例不靠清单**：`DELIVERABLE_HASHES_V1.json` 声明 "excludes private outputs" 但仓库无一份机器可检查的"可提交/私有"边界文件；T5 拟新增 `ARTIFACT_BOUNDARY_V1.json`（路径模式 + gitignore 依据 + 处置）。

**Windows/跨平台路径**：执行器全部用 `pathlib.Path`，subprocess 用 `sys.executable`，无 shell 拼接；唯二平台耦合是内存测量（D-04）与 PREPARATION 绝对路径（D-03）。

---

## E. 按依赖排序的实施清单

图例：类型 = 工程修复 / 实验方案变化 / 外部边界核实。验收方法均为本地可执行检查；除注明外不需要真实数据或训练。

### T0（前置，人工）— Git 提交授权

- 优先级：P0 前置。缺口：本计划所有"入 Git"动作按本轮边界（不提交、不推送）不能由我执行。
- 改动：无文件；用户或获授权者在会话末提交。依赖：全部后续 T1–T7 的"远程可得"验收依赖它。
- 验收：`git status` 出现预期新文件且无私有路径。不需要真实数据。风险：误提交私有文件——用 T5 边界清单核对。

### T1 — 模型源码最小集入 Git（类型：工程修复）

- 优先级：P0。缺口：A1（`git ls-files research_work/forward_increment/` 为空）。
- 新文件（内容=磁盘现字节，sha 逐项等于父协议 pin）：
  - `models/derefusion/bundle_v3_pin/DeReFusion.py`（sha `468a861d...`）
  - `models/derefusion/bundle_v3_pin/derefusion_components.py`（sha `91ae3bce...`）
  - `models/derefusion/bundle_v3_pin/RevIN.py`（sha `a7dc201d...`，LF 行尾原样）
  - `models/derefusion/bundle_v3_pin/__init__.py`（空）
  - `models/derefusion/bundle_v3_pin/BUNDLE_PIN_MANIFEST_V1.json`：三文件 sha + 来源路径 + "与顶层单体版功能等价"的验证记录（参数数/初始化逐位一致，本计划 A.2 已实测）
- 具体改动：仅新增；目录放 `models/derefusion/` 下使源码处于既有模型区，**不改动** `research_work/forward_increment/` 原目录（历史锚点保留），不改顶层 `DeReFusion.py`/`layers/RevIN.py`。
- 配套（必要）：父协议 `model.bundle` 指向旧路径——不得改冻结协议文本；在新协议模板中把 bundle 路径改指 `models/derefusion/bundle_v3_pin/`，并在新协议里把 3 个空 `__init__.py` 一并纳入 pin（修 D-09，见 FINDINGS）。
- 验收：`git ls-files models/derefusion/bundle_v3_pin/` 非空；`sha256sum` 三项等于 pin；干净 worktree checkout 后按 BUNDLE=新路径 import 可实例化且参数 21,743。
- 不需要真实数据/训练（实例化+参数计数即可）。风险：低；复制错误由 sha 比对拦截。依赖：T0。

### T2 — 压缩试验批工件入 Git（类型：工程修复）

- 优先级：P0。缺口：A2。
- 改动：`git add research_work/project_management_2026_10_10/compression_pilot_2026_10_13/`（10 个文件，全部为文本记录/脚本，无数据）+ `docs/DRF_CDD_ETH_COMPRESSION_MINIMAL_PILOT_2026-10-13.md`。
- 验收：`git ls-files` 该目录 10 文件；与 `DELIVERABLE_HASHES_V1.json` 逐项 sha 比对一致（该清单不含自身，本批复核当前值 `2cd89223...`）。
- 不需要真实数据。风险：低。依赖：T0；与 T1 同批提交以最小化 HEAD 移动次数。

### T3 — CPU 环境 pin 与重建配方（类型：工程修复）

- 优先级：P0。缺口：A5。
- 新文件：`requirements/torch-cpu.txt`（`--index-url https://download.pytorch.org/whl/cpu` + `torch==2.5.1`）；`docs/DRF_CPU_ENVIRONMENT_RECIPE_V1_2026-10-13.md`（venv 创建命令、`pip install -r requirements/torch-cpu.txt -r requirements/core.txt`、验收脚本输出样例：python 3.11.x / torch 2.5.1+cpu / numpy 2.1.2）。
- 验收：新建 venv 按配方安装后 `python -c` 打印三项版本与预期一致；`run_pilot_v1.py --phase synthetic` 的 import 链可加载（不运行训练）。
- 不需要真实数据。风险：pytorch.org 索引可用性（外部边界 U3）。依赖：T0。

### T4 — 新 HEAD 重签程序文档（类型：工程修复）

- 优先级：P0（T1–T3 提交后 HEAD 必然移动，复跑立即需要）。
- 新文件：`docs/DRF_PROTOCOL_RESPIN_PROCEDURE_V1_2026-10-13.md`：① 新协议副本更新 `head`/`branch`/bundle 路径字段并重算各 pin；② 依次 synthetic→prepare→release→run 重签发；③ 复现验收标准：新 RESULTS 的 raw96 组 `state_tensor_sha256` 与 `validation_mse` 必须逐位等于旧批 `1a438fc3...` / `2092.513855618721`（方法即本批用过的父子对照，`run_pilot_v1.py:348-353`）；④ 任何一步 pin 不复现即停并记录，不得放宽。
- 验收：文档经一轮桌面走查（dry-run 到 release 前）；不需要真实数据/训练（真正的重签复跑属于获授权后的实验行为，单独立项）。
- 依赖：T1–T3。

### T5 — 私有/可提交边界清单（类型：工程修复）

- 优先级：P1。缺口：D-07。
- 新文件：`docs/DRF_ARTIFACT_BOUNDARY_V1_2026-10-13.json`：每条 {path_glob, 处置(tracked/local-only/forbidden), 依据(gitignore 行/协议字段)}，覆盖 `data/**`、`research_work/forward_increment/**`、`models/derefusion/bundle_v3_pin/**`、`compression_pilot_2026_10_13/**`、`*.npz`、`*.pt`、`validation.predictions.csv`。
- 验收：`git ls-files` 与清单 tracked 集合交集核对无 forbidden 项；CI 手工脚本一遍过。不需要真实数据。依赖：T0（T1/T2 前后核对用）。

### T6 — 预处理模块与单元测试（类型：工程修复）

- 优先级：P1。缺口：B 节现状（聚合逻辑锁在冻结执行器内，无版本化接口）。
- 新文件：B.1 三个文件。单元测试用合成数组断言：① 与冻结 `aggregate()` 在全合成域逐位一致（从冻结执行器 import 对照，测试内 import，不改冻结文件）；② OHLC 块边界/尾部保留/末端 Close 精确；③ 正仿射交换（rtol=0, atol=2e-14）；④ 非有限/错形状/非法 plan 全拒绝；⑤ `config_sha256` 稳定性（同 plan 两次相同、字段差异即不同）。
- 验收：`tests/test_fixed_ohlc_preprocessing.py` 全绿；不需要真实数据。
- 依赖：T1（测试要 import bundle 模型做形状联测时可走新 pin 路径；纯聚合测试无此依赖）。

### T7 — raw48 对照组协议草案（类型：实验方案变化）

- 优先级：P2。缺口：C 节（当前无法分离"覆盖"与"分辨率"）。
- 新文件：`research_work/project_management_2026_10_10/compression_followup_YYYY_MM_DD/PROTOCOL_V0.1-DRAFT.json`（草案，未签发）：三臂 raw96/mixed48/raw48，其余预算/门控沿用 V1；含位置跨度元数据要求、raw48 尾部切片定义、不重新拟合 scaler 的声明、可接受误差界留空待研究侧填写。
- 验收：草案经研究侧（Codex/用户）评审；工程侧只验证：草案引用的所有 pin 路径存在、raw48/mixed48 参数形状相等的预计算断言可执行（合成数据）。
- **需要真实数据与训练才能出结果，但本任务只交付草案**；执行须等新释放。依赖：T4（新协议须在新 HEAD 上签）、研究判断 J1–J3（见下）。
- 风险：把 C-1 误当"已选定的最佳压缩"——草案必须保留"不作分数挑选"声明；不得复用本批验证结果做组间筛选。

### 未核实外部边界（核实前不得当成事实使用）

- **U1**：CDD 上游 CSV 字节稳定性——重建链第 2 步依赖上游文件仍等于 `raw_sha256` pin。已完成日线理论上不变，但供应商修订/重发未核实；若变动，须走新资质释放+新 pin，不得混用。
- **U2**：CDD 限定本地非商业研究依据不覆盖公开摘要对外发布；摘要外发须单独审查（两批文档均已声明）。
- **U3**：download.pytorch.org cpu 索引与 numpy 2.1.2 wheel 的持续可用性。
- **U4**：`np.savez` 固定 1980 时间戳是 numpy 实现行为（2.1.2 实测），跨 numpy 版本未核实——重建配方 pin numpy==2.1.2 并实测验证。
- **U5**：旧 Yahoo 四资产来源问题仍未解决（`SOURCE_RIGHTS_GAP_REGISTER` 系列），与 CDD 链完全隔离，本计划不涉及。

---

## 附：本轮只读复核记录

- 四个私有 NPZ（raw96/mixed48 × train/validation）sha256 与 `PREPARATION_V1.json` pin 逐项一致（本机读取，未复制、未改动）。
- 压缩批全部 pin 链（PROTOCOL→SYNTHETIC→PREPARATION→RELEASE→RESULTS→INTERNAL_AUDIT→PROGRESS→DELIVERABLE_HASHES→报告）当前 sha 与互相引用一致，无版本漂移。
- bundle 三源码 sha 与父协议 pin 一致；顶层/bundle 模型等价性实测通过（A.2）。
- 仓库 HEAD 自交接快照以来未移动；工作区 76 项既有改动/未跟踪材料原样保留，未触碰。
