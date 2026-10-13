# K3 独立工程复核报告：压缩工程实施包 v1

复核人：Claude Code 中 Kimi K3（独立工程审查者）。
日期：2026-10-13。主仓库 `C:\Users\26843\Documents\ChatGPT\redefusion`；分支 `docs/project-status-catalog-2026-10-10`（实测未变）；基线 HEAD `5a8220ab0fdfb72601671f9fadf7de5e8a3b7554`（复核全程未移动）。
复核对象：暂存区 62 个文件（43 A + 19 M）、`compression_engineering_implementation_v1` 全部清单与验收记录、`docs/DRF_COMPRESSION_ENGINEERING_DISPOSITION_V1_2026-10-13.md`。
方式：只读静态审查 + 经授权在新验证环境独立重跑两个合成 unittest 文件与 `check_artifact_boundary.py`。未修改任何文件或暂存区，未训练、未评分、未读测试角色数组、未提交。

## 总体判定

**工程包适合提交。无 P0、无 P1。** 七项重点检查全部通过，六项 P2 记录如下（均为记录完整性/健壮性提示，不改变语义正确性，不阻断提交）。

## 检查项结论与实证

### 1. 归档源码字节、隔离加载与 drift 拒绝 —— 通过

- 三个归档文件 + 空 `__init__.py` 的 staged blob SHA-256 与旧 pin 逐项一致（`468a861d…`/`91ae3bce…`/`a7dc201d…`/`e3b0c442…`），同时与 `BUNDLE_PIN_MANIFEST_V1.json`、`loader.py` 内置 `PINS`、MANIFEST 三向一致。
- `loader.py:41-57` 的私有 import 映射：`level==0` 且精确命中 `'layers.RevIN'`/`'layers.derefusion_components'` 才重定向到模块局部私有模块（不注册 `sys.modules`、不改 `sys.path`、不触顶层 `layers`）；无 fromlist 的裸 `import layers.RevIN` 显式 `ImportError`。归档源码实际两行 import 均为 from-import（`DeReFusion.py:3-4`），命中映射。
- 独立重跑 `PinnedSource` 三项测试通过：seq96/48 参数 21,743/21,599、同 seed 初始化逐张量相等且 96 排序哈希 `564e61a1…`、**前向输出逐位相等**；`sys.modules` 注入空 `layers.*` 后加载仍正确且全局未污染（`test_loader_isolated_from_other_layers_modules`）；`RevIN.py` 追加一字节即 `ValueError`（`test_archive_drift_rejected`）。
- P2-4：映射为名字精确匹配，覆盖完整性依赖归档 sha pin 封死源码——pin 在则风险为零，建议 manifest 注明该前提。

### 2. 聚合模块固定函数语义与测试独立性 —— 通过

- `fixed_ohlc.py:41-53` 与冻结 `aggregate()`（`run_pilot_v1.py:79-85`）逐行对应并参数化；`aggregate_ohlc` 拒绝非 plan、错形状、complex/bool/str、非有限（`dtype.kind in 'fiu'` + `isfinite`），52 行注释诚实说明跨通道不等式在缩放后不可校验。
- 测试含**真正独立参照**：`test_exact_frozen_transform_and_no_input_mutation` 直接加载冻结执行器 `aggregate` 作 oracle，4 dtype × 4 样本量随机对照 + 输入不变 + 无内存共享；`test_block_boundaries…` 手算期望值对照；`test_positive_affine_commutation` 与冻结合成检查同参数（rtol=0, atol=2e-14）。
- `AggregationPlan` frozen dataclass：正整校验（拒 bool/float）、`block_days*n_blocks+recent_days==context_days` 完整分块、channel_order 锁定 OHLC tuple；`canonical_json`（sort_keys+separators）/`config_sha256`/`position_spans_days` 确定性均有断言。
- `derived_cache_key` 六元绑定（源包、源 manifest、scaler、模块、numpy 版本、配置哈希），比 K3 原计划四元组更全；逐元扰动区分性与格式拒绝均有测试。
- 目标不接触：模块无 y/keys/role 概念（`fixed_ohlc.py:1` docstring 声明），角色边界留在执行器层——与原设计分界一致。

### 3. replay bootstrap 绑定、相对路径与授权门控 —— 通过

- `generate()`：尝试名白名单正则（非法名 create nothing，有测试）；深拷贝旧协议后绑定**真实** git HEAD/branch（subprocess 实测）；`replay.code_sha256` 覆盖冻结引擎四件 + replay 自身 + 预处理模块 + loader + manifest + 两个 requirements；历史目标（两臂 `state_tensor_sha256`/`mse.F`）随协议封存；`EXECUTION_AUTHORIZATION_TEMPLATE.json` 恒 `NOT_APPROVED`。
- `configure()`：`resolve_relative` 拒绝绝对路径/Windows drive 与 root/反斜杠/`..` 并 `is_relative_to` 复查（`compression_replay.py:35-44`）；`historical_private_relative` 只接受 `data/shrink-cdd-20261013-v1/packages_v1_1/ETHUSD_f100/` 前缀的历史绝对路径重绑定；新 PREPARATION 记相对路径并留 `historical_source_rebinding` 映射（修掉旧绝对路径耦合）。
- 计算逻辑复用：monkey-patch 冻结引擎的 ROOT/HERE/P/PROTOCOL/PRIVATE/记录路径，`model()` 改走隔离 loader，`aggregate` 改走 `fixed_ohlc`，`verify_sources` 增加 HEAD、code_sha256、父批三件、归档、环境三元组（3.11.15/2.5.1+cpu/2.1.2 精确绑死）五重校验。冻结文件零改动。
- **授权门控 fail-closed 实证**：`release()` 要求 `EXECUTION_AUTHORIZATION.json` 六项字段精确匹配（decision/scope/head/protocol_sha256/owner/basis 缺一即 ValueError，`compression_replay.py:190-194`）；独立重跑 `test_generation_binds_sources_but_does_not_authorize_fitting`：无授权文件时 `release()` 抛 FileNotFoundError，RELEASE/PRIVATE 均未创建；`verify_release` 包装层额外绑定授权文件哈希，授权变更使释放失效。
- 派生对账：`prepare()` 断言 mixed48 派生载荷逐字节等于历史 pin（`:176`）。
- P2-3：replay 记录的 `runner_sha256` 从此指向 attempt wrapper 而非冻结引擎本体（引擎身份由 `code_sha256` 绑定）；重签文档未显式说明该语义变化，建议补一句。
- P2-6：`resolve_relative` 拒绝一切 `\`——Windows 防御合理，Linux 下理论误伤含反斜杠文件名（仓库无此命名，实际无影响）。

### 4. 逐字节封存与 16 处行尾修复 —— 通过（实际 18 处）

- 独立逐文件验证：16 个 shrink 文件 + 2 个 docs 的 HEAD blob（LF）→ staged blob（CRLF）**去 CR 后逐字节相等**，无任何内容变化；staged blob 与工作区冻结字节逐项一致；staged sha 与 receipt 记录逐项一致。
- 含义：首次提交时 autocrlf 把工作区 CRLF 转成 LF 入库，导致 Git blob ≠ 协议/manifest pin 的执行字节；本次以 `-text` 封存 + 重暂存原字节修复，旧提交保留不改写。
- `.gitattributes` 新增规则全部为窄路径（具体目录/具体文件），`git check-attr` 实测 `text: unset` 生效；`bundle_v3_pin/.gitattributes` 局部双保险；未对 tests/、reproduction/ 全目录设宽规则。
- P2-1：receipt 的 `newline_only_blob_repairs` 只列 shrink 目录 16 项（verify 脚本 `verify_staged_source_v1.py:64-74` 只扫描该目录），两个 docs 的同性质修复未列入。性质已独立验证相同，建议提交信息中说明"18 处 newline-only"以免清单口径歧义。

### 5. 机器边界策略与私有隔离 —— 通过

- 策略 `deny_before_allow`、default `review-required`；local-only 覆盖 data/dataset/checkpoints/results/npz/npy/pt/pth/predictions.csv/venv。
- **920 条历史 tracked private-like 路径**：保留历史、单独列审、明确"不把历史跟踪当作新上传许可"——与任务书要求一致，未借删除历史让检查通过。
- 独立重跑 `check_artifact_boundary.py`：62 个 staged 路径 0 违规；`violations()` 大小写不敏感（`model.PT` 命中）有测试。
- 未暂存改动恰为 receipt 声明的 5 项用户既有改动（`git status` 实测）；测试产物 `data/compression-replay-attempts/` 确认 gitignored。
- 无任何 raw/NPZ/逐键预测/checkpoint/环境目录进入 stage；verify 脚本导出时断言无 .npy/.npz/.pt/.pth（`verify_staged_source_v1.py:45`）。

### 6. 环境验收真实性 —— 通过

- 新验证环境实物位于 gitignored `data/engineering-cpu-validation-20261013-v1/.venv`，实测 `3.11.15 / 2.5.1+cpu / 2.1.2`；**我用该环境独立重跑 13 项测试全部 OK**（8+5，与 receipt 一致），未触碰真实数据。
- wheelhouse 9 个 PyPI wheel 实物 sha 与下载回执、requirements pin 三向一致（回执 sha `4752131e…` 与 receipt 绑定）；torch wheel 走 download.pytorch.org 精确 URL+sha pin（`torch-cpu-win311-wheel.txt`），已装未留 wheel 文件（P2-2：完全离线重建需按 pin 重下 torch）。
- 导出 zip sha 与 receipt 一致（`9ad21915…`）；fixture 当前 68 文件 = 62 导出 + 6 个测试 attempt 产物（receipt 的 62 为测试前计数，自洽；P2-5 建议注明）。
- receipt 明确 "not a complete Git checkout or real-data replay"、`new_real_F_fits: 0`、`test_role_arrays_read: false`、`full_real_replay_acceptance: NOT_RUN`；一次工程偏差（v1 文件名假设）有保留现场与影响说明。

### 7. raw48 草案表述准确性 —— 通过

- `DRAFT_NOT_RELEASED_NOT_EXECUTABLE`；问题表述限定"matched model shapes 下的联合表示权衡"；覆盖差正确写为 **48 天**（96−48，非 K3 原稿的 64）；重叠区粗化正确写为 16 天（day 48–63 聚合为 4 块）。
- 明确"Coverage, resolution, RevIN and moving-average semantics are not individually isolated"、"Raw48 is a capacity control, not proof of incremental information"——未声称完全分离。
- `position_spans_days` 为 `[4]*16+[1]*32`，无"25 位置=100 天"错误；`acceptance_margin: null` 且声明"不能在查看新分数后补设接受界"；seeds 标记 Proposal；`missing_before_release` 七项含独立工程复核与 runner/preparation/audit 新建。

## P2 清单（不阻断提交，建议提交信息或后续补记）

1. receipt 行尾修复清单 16 项 vs 实际 18 项（+2 docs，同性质已验证）——口径补记。
2. torch wheel 未留档 wheelhouse（URL+sha pin 在，重装可复得）。
3. replay 的 `runner_sha256` 语义变为指向 attempt wrapper——重签文档补一句说明。
4. loader 私有映射的名字精确匹配前提（归档 pin 封死）——manifest 注明。
5. 测试运行会在 data/ 留合成 attempt 产物；fixture 68 vs receipt 62 的关系建议注明。
6. `resolve_relative` 的全 `\` 拒绝在 Linux 的理论边界。

## 保留事项（不因本轮复核改变）

- **真实两臂复跑 NOT_RUN**：需私有输入就位、正式 `EXECUTION_AUTHORIZATION.json`、复跑对账 raw96 `1a438fc3…`/2092.513855618721 与 mixed48 `3166c0d1…`/2242.5347423209273，且须恢复 checkpoint/逐键预测/覆盖核对，非汇总指标对账可替代。
- 新尝试的完整独立审计适配未实施（旧 audit 脚本依赖旧目录）。
- **压缩批全面独立科学验收仍 PENDING**（原始数组逐元素独立复核）；本轮工程复核不升级为科学验收。
- raw48 正式协议未签发：接受界/seed/评估范围待研究侧前瞻填写。
- 上游 CDD 字节稳定性（重建链前提）与跨平台逐位一致性未验证；同 OS/CPU 仅为必要候选。
- 920 条历史 tracked private-like 路径的处置审计另行排队。

## 提交建议

43 A + 19 M 可提交。建议提交信息写明：工程新增、bundle pin 归档、18 处 newline-only 字节封存、无数据/环境入仓。提交后 HEAD 移动，重签按 `DRF_PROTOCOL_RESPIN_PROCEDURE_V1` 在新 HEAD 上执行；提交与推送须用户明确授权。
