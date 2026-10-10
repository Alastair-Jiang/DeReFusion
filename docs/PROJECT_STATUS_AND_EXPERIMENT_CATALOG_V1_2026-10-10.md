# DeReFusion — project status & experiment records

**Snapshot date:** 2026-10-10

**Repository snapshot:** 盘点开始时 checkout 为 `docs/project-status-catalog-2026-10-10`，HEAD `bf6ba8fc497ef03645f59511594ac0ddf240c305`（父提交 `9b200379d813debff885b6e0a54e23667246b95e`）；`origin/main` 当时为 `001717222fb50f588ec28746e0deb2cd66bb07ef`。这是本次盘点的时间点记录，推送前会将分支更新到最新 `origin/main`。

**Status:** research archive and reproduction work in progress; R1 real-data execution gate remains closed.

> Navigation and status only. This is not a protocol, approval, data licence, result, or execution release. No OHLC/price values or project result payloads are reproduced here.

## At a glance

DeReFusion is a time-series forecasting research codebase with historical model/ablation, asset-sweep, Phase 1, and forward-increment (R1) work. The repository contains source, protocols, run manifests/logs, analysis scripts, reports, datasets, and derived artifacts. The immediate goal is to make these materials navigable without conflating historical results, synthetic engineering, and authorized future execution.

- Historical evidence lives across reports/evidence_closure/, reports/phase1/, reproduction/, results/, and sweep_runs/. Interpret each artifact only under its own protocol, manifest, date, and attempt identity; newer filenames do not supersede approvals or preregistrations.
- R1 design is documented in its approved design. Design approval is not permission to access or process real values, train, or score.
- Synthetic engineering: source_role_composition_v1 is the more complete source→role→worker candidate; worker_identity_transport_v1 is a narrower predecessor. Existing tests support only their specified synthetic fixtures—not real-source provenance, production isolation, or execution readiness. See the control index for exact coverage and review gaps.
- Latest documented R1 state: no real OHLC/price values were read and no R1 real-data preprocessing, fitting, training, or scoring was authorized or performed. Keep the gate closed absent a dated, hash-bound release decision and required data permissions.
- The checkout has extensive pre-existing local modifications and untracked experiment artifacts. They are not implicitly approved for publication. Do not bulk-stage or publish datasets, logs, checkpoints, credentials, or unreviewed changes.

## Research and evidence map

| Workstream | Contents | Navigation | Evidence status |
|---|---|---|---|
| Model / ablation development | DeReFusion implementation, RevIN/Mamba layers, ablation and gating variants | models/, layers/, docs/reports/ | Version-specific review required; no single frozen release implied |
| Historical reproduction / sweeps | Run scripts, console records, logs, result folders and analysis | reproduction/, results/, sweep_runs/, reports/evidence_closure/ | Historical evidence; interpret against relevant protocol and run identity |
| Phase 1 | Stage B/C summaries, intake/recovery records, manifests and result bundles | reports/phase1/, reproduction/results/phase1/, reproduction/c1_handoff/ | Separate historical research line; does not authorize R1 |
| R1 forward increment | Approved design, gate decisions, candidate implementation, synthetic QA and plans | Project control index, workflow crosswalk v2, research_work/forward_increment/ | Design approved; real execution not released; candidates remain candidates |
| Data and derived artifacts | Raw/curated data, source metadata, result tables, checkpoints and intermediates | data/, dataset/, reproduction/results/, results/ | Rights, sensitivity, provenance and publication status must be reviewed before external release |

从已跟踪的 [README](../README.md)、[报告索引](../reports/README.md)、[Phase 1 预注册](PHASE1_PREREGISTRATION.md) 和 [Phase 1 数据与进展报告](../reports/phase1/phase1-experiment-data-and-progress-20260930.md) 开始导航。接管期间形成的扩展控制索引、交叉表与审查记录仍是本地候选，未随本目录自动发布；发布前需逐项审阅并固定哈希。

## Recommended experiment record fields

For each attempt, maintain a stable record linking (not copying) the research question and claim boundary; protocol and approval/release state; code revision and dirty-tree scope; config, command, dependencies/runtime and hardware; dataset/source identity, rights, transformation and split/role definition; attempt ID, seed, start/end status, resource budget, failures/retries/deviations; output paths and permitted hashes; analysis/report link, limitations and review status. Preserve failed and partial attempts. A hash proves byte identity only—not rights, provenance, scientific validity, correct execution, or independent reproducibility.

## Publication and data boundary

This document is not blanket clearance for the repository. Before publishing an experiment bundle, review its exact staged diff for data rights, confidential content, raw/derived data, credentials, local paths, checkpoints, and user-authored changes. Keep restricted datasets out of Git; where allowed, publish acquisition instructions, schemas, version identifiers, checksums, and transformation code instead of values. Use an approved archive mechanism only after rights and storage review.

R1 real OHLC/price access, preprocessing, fitting/training and scoring remain closed. A future step requires an append-only, dated/versioned decision tied to the then-current HEAD and input/config/data identities and SHA-256, with scope, resource ceiling, stopping conditions, deviations, and applicable permissions. Design approval and synthetic tests are not that decision.

## Repository housekeeping snapshot

盘点开始时，Windows 原生 Git 显示当前目录位于任务分支；3 个已跟踪文件有未暂存修改，约 12,261 个未跟踪文件（状态按逐文件展开；部分超长路径无法由 Windows Git 枚举）。另有大量运行结果、检查点和研究材料。此前 WSL 挂载视图报告的 458 项修改与原生 Git 不一致，不应作为当前事实；详见[同日状态更正记录](DRF_TAKEOVER_STATUS_CORRECTION_V1_2026-10-10.md)。未经逐项审阅，不批量暂存或发布。

本轮仅对文件路径、扩展名和大小作元数据盘点；未读取数据集、预测数组、日志或权重内容。先前盘点到的未跟踪项包括 2,158 个 `.npy`、871 个 `.csv`、644 个 `.pth`、716 个 `.log` 和 5,679 个 `.json` 文件（类型可能重叠于研究用途，不能据扩展名推断内容/许可）。这些文件未纳入本次发布。原始 `data/` 与 `dataset/` 目录由忽略规则排除；被跟踪的注册表和报告仍须按各自来源、许可与协议解释。文件哈希只证明字节身份，不证明数据授权或科学有效性。

## References

- [Repository README](../README.md) — project scope, reproducibility and reading order.
- [Evidence index](../reports/README.md) — append-only historical conclusions and evidence chronology.
- [Phase 1 preregistration](PHASE1_PREREGISTRATION.md) and [Phase 1 data/progress report](../reports/phase1/phase1-experiment-data-and-progress-20260930.md) — published Phase 1 protocol and status.
- R1 control documents are mentioned only where supported by this project’s existing takeover records; their local candidate copies are not linked as published artifacts in this index.

---

**Scope note:** assembled from existing governance summaries and repository path/status metadata. Dataset/result payloads were not inspected. This does not claim every local file was individually audited or cleared for publication.


## GitHub 项目组织参考

本目录采用“入口说明 + 按工作流导航 + 实验记录字段 + 数据/产物发布边界”的组织方式。可对照 [THUML Time-Series-Library](https://github.com/thuml/Time-Series-Library) 的模型、数据准备与实验脚本导航，以及 [Nixtla NeuralForecast](https://github.com/Nixtla/neuralforecast) 的文档、基准和工程入口。TSLib README 同时提醒其部分基准可能已不再适合衡量当前进展，因此本项目也应把结论绑定到协议、时间和可复核产物；这里只借鉴公开项目的可发现性，不表示 DeReFusion 与其研究结论等价，也不声称本仓库已达到其测试或维护覆盖。
