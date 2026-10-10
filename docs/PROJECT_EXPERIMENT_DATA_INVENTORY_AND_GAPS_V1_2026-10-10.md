# DeReFusion 实验记录与数据资产总盘点及缺口清单 v1

**盘点日期：** 2026-10-10
**主仓库：** `C:/Users/26843/Documents/ChatGPT/redefusion`
**盘点基线：** 分支 `docs/project-status-catalog-2026-10-10`，HEAD `6866dbde6ba547a9124e9b4578f6951f4d3e22c9`；基于 `origin/main` `001717222fb50f588ec28746e0deb2cd66bb07ef`。
**范围说明：** 只读盘点 Git、文档、路径和文件元数据；没有打开原始 OHLC/价格、预测/真值数组或 checkpoint 内容，没有训练、拟合、评分或功效分析。

本文是全仓导航和缺口台账，不是新的实验协议、授权、科学结论或数据许可。历史文件继续按原日期和版本解释；任何候选材料不因被索引而升格为控制文件。

## 项目进度与证据状态

| 研究线 | 当前可核对状态 | 可支持的结论边界 | 远程入口/来源 |
|---|---|---|---|
| 历史结构与证据闭环 | Gate A 结构验证为 FAIL；F1 为 SUCCESS，但 7 个追加资产中 3 个不稳定；C1 最终报告为 FAIL，独立盲复算未发现实质数值差异 | 保留失败、异常和修订史；不得把早期方向性信号写成已复现发现 | [证据索引](../reports/README.md)，`reports/evidence_closure/00–29` |
| Phase 1 Stage A | GPU 校准 15/15 完成；CPU 旁路校准 13 pass、1 resource-blocked、1 无 receipt | 运行校准，不作科学比较 | [Phase 1 总览](../reports/phase1/phase1-experiment-data-and-progress-20260930.md) |
| Phase 1 Stage B | 300/300 逻辑设置有合格产物：P4 245/300；RTX 8000 补充 55/55，零重叠 | 两轨分开报告；覆盖完整不代表单硬件完整面板，也不支持跨硬件排名/等效 | 同上及 `reports/phase1/stage-b-*` |
| Phase 1 Stage C | RTX 5060 Ti 单轨 360/360；完整性/配对复核完成 | 当前是分层描述性点估计；未报告 CI 或 p 值，不能宣称确认性优越 | 同上及 `reports/phase1/stage-c-*` |
| Phase 1 Stage D | 冻结清单 144 项均为 planned；没有已核实 attempt | 尚未执行；进度报告记载没有阶段专属执行授权 | 同上、`docs/PHASE1_PREREGISTRATION.md` |
| R1 forward-increment | 本地候选合成工程材料包括生命周期 v1/v2、role-custody probe、binding/transport 测试及多版计划；当前可见的候选闸门决定写明真实值/预处理/训练/评分未放行 | 合成测试不证明真实来源、生产隔离、统计功效或研究效果；本轮不运行真实数据 | 本地候选在 `research_work/forward_increment/`；关键综述/闸门文件尚未进入远程主干 |
| 数据与运行产物 | 仓库有数据注册表、历史摘要 CSV、run manifests/receipts/logs、分析脚本和大量本地输出 | 每条结果仍须回连协议、attempt、源码/配置、数据身份、环境与审计收据 | `reproduction/`、`results/`、`sweep_runs/`、`reports/` |

历史阶段总览来源是已跟踪 `reports/README.md` 与 Phase 1 报告；R1 细节来源包括本地未跟踪候选 `research_work/forward_increment/lead_design_2026_10_07/project_synthesis_v1/PROJECT_ASSESSMENT_AND_ROADMAP.md` 和 `R1_EXECUTION_GATE_DECISION_V1.md`。这些 R1 候选的版本/授权状态需在纳入远程权威索引前另行核验。

## 仓库材料清点

### 已在 Git 索引中的记录

- 当前主仓库索引为 1,507 个已跟踪文件；其中 `docs/` 22 个、`reports/` 66 个，`reports/evidence_closure/` 39 个、`reports/phase1/` 24 个。
- `reports/README.md` 是历史结论与报告时间线入口；其中明确标记过期快照、失败结果、阶段状态和阅读顺序。
- Phase 1 报告附有冻结 manifest 哈希、Stage B 分轨 intake/日志核验、Stage C 预测键/数组配对检查、逐阶段报告和复算脚本入口。
- `reproduction/results/dataset_registry.csv` 有资产/文件/队列/行数/日期/字节哈希/质量检查字段，但表头没有逐资产数据供应商、授权条款或再发布许可字段。
- 根目录有 `README.md`、`CONTRIBUTING.md`、`LICENSE`、`Dockerfile` 和 `requirements/`；贡献指南说明目前不接受 PR。代码 MIT 许可不能替代数据集或预训练权重的单独许可。

### 主仓库中尚未跟踪的候选材料

在新建本盘点文件前，原生 Windows Git 枚举到 12,261 个未跟踪文件；部分深层路径触发 Windows 文件名过长警告，因此该计数是可枚举数，不是完整文件系统证明。另有 3 个已跟踪文件未提交修改。它们均保留在本地，不纳入本次提交。

| 路径组 | 未跟踪文件数 | 处理状态 |
|---|---:|---|
| `reproduction/` | 8,716 | 大量运行收据、输入/输出和检查点；须逐 attempt 分类，不批量上传 |
| `research_work/` | 3,457 | 多个代理/角色研究工作包、合成夹具与候选治理材料；含长路径假 fixture |
| `_research/` | 63 | 外部研究缓存/下载候选，来源和发布权利未审 |
| `docs/` | 13 | 下方候选文档表；未统一审阅，不视为已发布 |
| `reports/` | 6 | 下方报告路径；未统一审阅，不视为已发布 |
| `tests/` | 3 | 未跟踪验证脚本，须审查后才能纳入自动化测试 |
| `scripts/` | 1 | 未跟踪运行脚本，未审核其行为/依赖 |
| 根目录临时文件 | 2 | `.fs-safe-*.tmp`，未删除，来源/用途待确认 |

未跟踪文件按扩展名统计：`.json` 5,679、`.npy` 2,158、`.bin` 924、`.csv` 871、`.log` 716、`.pth` 644、`.txt` 496、`.py` 250、`.jsonl` 220、`.md` 184、`.tsv` 27、`.html` 23、`.gz` 17、`.patch` 10、`.sha256` 10、`.pdf` 9、`.tmp` 8、无扩展名 8；扩展名不能识别数据内容、来源、授权或实验状态。

按路径元数据汇总的未跟踪文件大小：.npy 36,557,360 字节、.csv 1,538,627 字节、.pth 237,573,644 字节、.log 7,937,399 字节、.json 30,350,484 字节、.gz 3,277,757 字节。被忽略的本地目录另有 dataset/ 62 个文件共 8,786,277 字节、data/ 2 个文件共 5,746 字节、checkpoints/ 443 个文件共 960,482,240 字节；只看目录和文件属性，未读内容。

未跟踪 `docs/` 候选共 13 件：

- `DRF_FORWARD_INCREMENT_APPROVAL_PACK_V0.1_2026-10-02.md`
- `DRF_FORWARD_INCREMENT_DESIGN_HANDOFF_DRAFT_2026-10-02.md`
- `DRF_FORWARD_INCREMENT_LEAD_REVIEW_2026-10-02.md`
- `DRF_FORWARD_INCREMENT_PROTOCOL_DRAFT_V0.1_2026-10-02.md`
- `DRF_LAB_WORKFLOW_CROSSWALK_V1_2026-10-08.md`、`DRF_LAB_WORKFLOW_CROSSWALK_V2_2026-10-09.md`
- `DRF_MAIN_CHECKOUT_RECONCILIATION_V1_2026-10-07.md` 与配对 JSON
- `DRF_PROJECT_CONTROL_INDEX_V1_2026-10-08.md`
- `DRF_R1_BINDING_STATIC_REVIEW_V1_2026-10-08.md`
- `DRF_SMALL_PANEL_PLAN_V0.1_2026-10-06.md`
- `DRF_TAKEOVER_DECISION_V1_2026-10-08.md`
- `QWEN_PARALLEL_WORK_PLAN_2026-10-02.md`

未跟踪 `reports/` 候选共 6 件：`DRF_AGENT_TAKEOVER_PROGRESS_V1_2026-10-08.md`、`agent-claim-verification-20261005.md`、`forward-increment/capacity_forward_increment_arms_20261002.json`、`forward-increment/handoff_reconciliation_2026-10-02.md`、`forward-increment/l0_input_eligibility_20261002.csv`、`phase1/stage-b-preclose-audit-20260930.md`。

另有未跟踪 Python/测试/脚本候选：`reproduction/analysis/audit_forward_increment_inputs.py`、`capacity_forward_increment_arms.py`、`serve_phase1_ops_status.py`、`supervise_phase1_delivery.py`、`windows_credential.py`，三个测试/核验脚本，以及 `scripts/register_phase1_delivery_supervisor.ps1`。其中涉及凭据或环境操作的文件在完成安全审查前不得发布或运行。

### 独立 worktree 小面板材料与输入漂移

独立 worktree HEAD 为 `001717222fb50f588ec28746e0deb2cd66bb07ef`，三份候选材料 SHA-256 与来源清单一致：审查稿 `ed23c318566d5d680628a0b53bb3ae6798394f3efe295662e51ca3a8ce5c4f70`；空白执行锁模板 `23bbc3ccfc061ee19edf05d0c7fc1bdec87cc4bbe99739ea27805617dd1d4ef8`；审查哈希清单 `14922dc1a82d8124efc5d3241b5a51a0ca6b1e4dee0d6d1ae9f1efb7fa6be632`。没有把它们复制或合并进主仓库。

审查清单所绑定的五份输入与主仓库逐项比较：

| 输入 | 独立 worktree 哈希 | 主仓库当前哈希 | 一致 |
|---|---|---|---|
| `DRF_SMALL_PANEL_PLAN_V0.1_2026-10-06.md` | `cfd9036ec6001225156ff87f9e82a6a9689add9442f01473bad1521f08b84b53` | 同左 | 是 |
| `DRF_FORWARD_INCREMENT_DESIGN_HANDOFF_DRAFT_2026-10-02.md` | `462c2f786c44e027b5a2773996344cc8b25fe26f90b26d54f51174d6d6e32d66` | 同左 | 是 |
| `PHASE1_EXECUTION_DECISION_V1.2.json` | `41e844da469b7d616904b076f291b032dfe90b4c6aff6ae0360f4915dccf3624` | `39ddcbcfe7213aaa010e15a9f6edf435d4313079ddc5751749cc30f4f85baa64` | 否 |
| `PHASE1_PREREGISTRATION.md` | `00b7882a78b6d936d8b675d184f04ff24d2e3ce9f1a2d10a9a4df6cbef523825` | `e9d0f075ba552928ab8683adb7f842f49e6a3aa4002dafda7bc4529a4698aa67` | 否 |
| `EXPERIMENTAL_DOCTRINE.md` | `9d6c41662bdd8ba9914e9f0a96f4f9e113ffb4f7fa10b21c7c891ef309e9ab5e` | `eb9d56d8be421ffd035c3cb5f42963d397fbd47093c76587bb40171518047e2f` | 否 |

因此该审查稿只能作为绑定 `0017172` worktree 输入快照的历史候选；不能把审查结论直接套用到当前主仓库。需基于主仓库当前五个哈希重新审查，或逐项解释差异后另发新版本。

## 数据与模型产物的存储状态

- `dataset/` 当前有 62 个文件，其中项目 README 说明 61 个日频 OHLC CSV、149,474 行；原始数据目录被 Git 忽略。这里只核对文件数量/文档声明，没有读 CSV 值。
- `data/` 有 2 个文件，`checkpoints/` 有 443 个文件；没有打开内容或核验许可。
- 本地候选与阶段记录提及 `.npy` 预测/真值数组、CSV/JSON 收据、`.pth` 模型权重和日志。按前述状态清点，这些产物不随本次文档提交上传。
- `LICENSE` 是代码 MIT 许可；README 明示数据与预训练模型可能有独立条款。当前数据注册表没有逐项许可/供应商字段，不能从代码许可证推断 OHLC 或派生结果可公开再分发。

## 缺失与待补清单

优先级针对“让记录可审计并决定能否公开”，不是执行研究授权。

### P0：发布/复现前必须补齐

1. **数据权利台账：** 每个资产的供应商、下载/授权日期、适用服务条款、再分发许可、署名要求、地域/用途限制；派生预测、真值、特征和模型权重是否可公开也须逐类确认。验收：责任人和证据链接/文件齐全；未知明确标 `unknown`，未知不得上传。
2. **完整 attempt 账本：** 将每个 run 目录与稳定 `attempt_id`、研究问题、协议版本、Git commit/dirty 状态、配置、数据哈希、环境、命令、seed、硬件、开始/结束状态、失败/重试、输出清单和分析报告一一对应。验收：成功、失败、部分、未收据、重试都能从索引追到原件；保留旧 attempt，不覆盖。
3. **分轨归档与数据包策略：** 明确哪些原始/派生文件允许随 Git、哪些应放授权对象存储/数据仓库、哪些仅发布 schema/来源版本/校验和。验收：每类文件有 owner、访问方式、保留期、备份和公开边界；不能只依赖本机路径。
4. **R1 新执行锁与 release 证据：** 当前候选执行模板有多个必填项为空，包括资产/来源、目标/单位/复权、窗口/跨度、边界/共同键、臂实现/配置、拟合与验证/失败规则、测试访问控制、环境/预算和责任人。需要逐项完成并绑定哈希；设计批准、对话委托或合成测试均不能代替数据权利与 release 证据。

### P1：确认性解释和全量索引前补齐

5. **Stage C 推断规则对账：** 冻结预注册写了资产簇 bootstrap 95% CI，但 Phase 1 收口报告说 bootstrap seed/重采样次数/区间算法/跨层汇总未预先锁定，故现报告仅作描述。查找结果揭盲前的原始固定记录；若不存在，保持描述性，不能用事后挑出的统计参数补成确认性结论。
6. **可复现环境锁：** 目前有多份 requirements 文件和 Dockerfile，但未发现 `pyproject.toml`、conda environment lock 或 GitHub Actions workflow。为每条正式运行保存精确 Python/库版本、CUDA/驱动/硬件、OS、镜像 digest 和启动命令，并说明跨平台差异。
7. **长路径清点：** Windows Git 对深层合成 fixture 报 `Filename too long`。需在支持长路径的环境中补一轮仅路径/元数据清点，或为新合成 fixture 设计短路径；验收前不能宣称 12,261 是完整文件总数。
8. **WSL/Windows Git 视图差异：** 已有同文件 blob 哈希差异的报告，但原因未知。明确换行规范、`core.autocrlf`、bindfs 映射和 Git 配置影响；今后主仓库状态以原生 Windows Git 为基准并留验证记录。
9. **本地候选文档状态：** 13 份未跟踪文档和 6 份未跟踪报告须逐份标记 `historical/draft/reviewed/superseded/ready-to-publish`，检查绝对路径、机密、事实依据、链接和引用；之后再决定进入远程，不能整目录 `git add`。
10. **独立 worktree 审查重绑定：** 小面板审查输入 5 项中 3 项与主仓库哈希不同。按主仓库固定输入重做版本化审查，或者在审查稿中限定为 worktree 快照历史审查；本次不直接移植审查稿/执行锁。
11. **合成安全与运行证据层级：** lifecycle v2 报告声明 F/B 实际 optimizer steps 为 11/50、两次输出哈希相同；role-custody 报告限于可信托管人的 synthetic T0 payload-integrity。当前材料未显示独立重新运行这两条结果；若将其用于正式资格门，先由不同环境/身份重跑固定哈希和负控，明确威胁模型，不写成生产隔离认证。

### P2：公开项目完善

12. **数据集引用/许可文件：** 增加按来源的 `DATA_SOURCES.md`/data card；若许可允许再分发，逐项附条款，否则只给获取说明和校验和。当前未找到 `CITATION.cff`，可添加软件/论文引用元数据。
13. **自动化质量门：** 当前未发现 `.github/workflows/`。可先为文档链接、JSON schema、哈希清单、关键单元测试建立 CI；CI 不应读取或上传真实数据/checkpoint。
14. **公开档案元信息：** 为正式论文/代码版本补 DOI/归档版本、引用方式、release/tag 与明确维护状态。`CONTRIBUTING.md` 说明不接受 PR，因此外部协作治理文件不是当前阻断项。

## 本次发布边界与下一步

本次只发布这份总盘点和对应导航修订。未跟踪候选文件、数据、预测/真值数组、checkpoint、日志、缓存、凭据相关脚本和临时文件均未提交、未推送；三份独立 worktree 小面板文件也未复制。下一轮按 P0→P1 清单逐项处理，先完成 attempt ledger 和数据权利台账，再对候选文档做版本/事实审查；任何数值数据、真实训练或确认性分析都必须依照届时有效的授权与项目门控另行决定。

## 相关入口

- [项目状态与实验导航](PROJECT_STATUS_AND_EXPERIMENT_CATALOG_V1_2026-10-10.md)
- [历史证据索引](../reports/README.md)
- [Phase 1 预注册](PHASE1_PREREGISTRATION.md)
- [Phase 1 数据与进度总览](../reports/phase1/phase1-experiment-data-and-progress-20260930.md)
- [`dataset_registry.csv`](../reproduction/results/dataset_registry.csv)；`dataset/README.md` 虽在本地，但整个 `dataset/` 目录被忽略，不属于当前远程入口。
