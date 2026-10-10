# DeReFusion — project status & experiment records

**Snapshot date:** 2026-10-10

**Repository snapshot:** main at 9b200379d813debff885b6e0a54e23667246b95e; local checkout was 2 commits behind origin/main at last status check.

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

Start with the [project control index](DRF_PROJECT_CONTROL_INDEX_V1_2026-10-08.md) and [lab workflow crosswalk](DRF_LAB_WORKFLOW_CROSSWALK_V2_2026-10-09.md) for the detailed control chain, status distinctions, synthetic-test limits, and gate checklist. These link existing records in place; they do not silently rewrite history.

## Recommended experiment record fields

For each attempt, maintain a stable record linking (not copying) the research question and claim boundary; protocol and approval/release state; code revision and dirty-tree scope; config, command, dependencies/runtime and hardware; dataset/source identity, rights, transformation and split/role definition; attempt ID, seed, start/end status, resource budget, failures/retries/deviations; output paths and permitted hashes; analysis/report link, limitations and review status. Preserve failed and partial attempts. A hash proves byte identity only—not rights, provenance, scientific validity, correct execution, or independent reproducibility.

## Publication and data boundary

This document is not blanket clearance for the repository. Before publishing an experiment bundle, review its exact staged diff for data rights, confidential content, raw/derived data, credentials, local paths, checkpoints, and user-authored changes. Keep restricted datasets out of Git; where allowed, publish acquisition instructions, schemas, version identifiers, checksums, and transformation code instead of values. Use an approved archive mechanism only after rights and storage review.

R1 real OHLC/price access, preprocessing, fitting/training and scoring remain closed. A future step requires an append-only, dated/versioned decision tied to the then-current HEAD and input/config/data identities and SHA-256, with scope, resource ceiling, stopping conditions, deviations, and applicable permissions. Design approval and synthetic tests are not that decision.

## Repository housekeeping snapshot

At the latest inspected snapshot: local main was two commits behind origin/main; 458 modified tracked paths and 58 untracked status entries; zero staged. The checkout contains extensive user-authored changes. No bulk staging is appropriate. Any remote publication should be limited to specifically reviewed, metadata-only documentation; experiment payloads and unrelated work remain untouched unless separately cleared.

## References

- [Project control index](DRF_PROJECT_CONTROL_INDEX_V1_2026-10-08.md) — authority hierarchy, file navigation, candidate evidence and publication controls.
- [Lab workflow crosswalk v2](DRF_LAB_WORKFLOW_CROSSWALK_V2_2026-10-09.md) — lifecycle mapping and scoped standards.
- [Takeover progress log](../reports/DRF_AGENT_TAKEOVER_PROGRESS_V1_2026-10-08.md) — dated operational record and QA history.
- [Approved R1 design](../research_work/forward_increment/lead_design_2026_10_07/R1_APPROVED_DESIGN_V1.json) and [R1 execution gate decision](../research_work/forward_increment/lead_design_2026_10_07/project_synthesis_v1/R1_EXECUTION_GATE_DECISION_V1.md) — controlling design/gate records; read together.

---

**Scope note:** assembled from existing governance summaries and repository path/status metadata. Dataset/result payloads were not inspected. This does not claim every local file was individually audited or cleared for publication.
