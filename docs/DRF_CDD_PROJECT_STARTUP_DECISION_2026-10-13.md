# DeReFusion startup decision — new CDD exploratory data

2026-10-13, Asia/Shanghai. Checkout: `C:/Users/26843/Documents/ChatGPT/redefusion`; branch `docs/project-status-catalog-2026-10-10`; HEAD `a74126c11d857da8514074b72282adc8d47f28a7`. Existing tracked modifications and untracked materials are preserved.

## Decision and basis

The user's project-lead delegation and subsequent direction to prioritize obtaining a usable permission basis or another viable route authorize Codex to make a scoped startup decision. A project-wide wait for the old Yahoo-labelled files is no longer the execution path. The original files retain their unresolved source/use status. A newly acquired CryptoDataDownload (CDD) Bitstamp BTC/USD and ETH/USD version is admitted for **local, internal, non-commercial research**.

The supplier's official [research offering](https://www.cryptodatadownload.com/about/) expressly invites research and analysis, its [terms](https://www.cryptodatadownload.com/terms-of-use/) describe a research starting point and non-commercial use, and its [Bitstamp download page](https://www.cryptodatadownload.com/data/bitstamp/) expressly provides CSVs for automated consumption. These pages were retrieved and stored locally with timestamps and SHA-256 digests before acquisition. This affirmative, documented offering is accepted as the operational use basis; no additional signed supplier letter is required for this narrow scope.

The supplier disclaims warranties, including third-party rights restrictions. The decision records that residual uncertainty and does not certify unrestricted upstream rights. A concrete conflicting restriction or supplier objection stops the affected use. Commercial use and public raw-data, prediction, checkpoint, or weight release remain outside the release. Current homepage marketing about commercial use does not override the more restrictive non-commercial terms used here.

## What was opened

| Action | Scope/status |
|---|---|
| Acquisition and QA | Completed on the two new CDD Bitstamp inputs; HTTP 200, distinct raw hashes, no overwrite of Yahoo files |
| Date/schema/OHLC checks | PASS; each has all 2,922 daily UTC keys in `[2018-01-01,2026-01-01)`, no gaps, duplicates, non-positive/non-finite OHLC or range inconsistency |
| Preprocessing | Eight conditions completed under new protocol v0.2; role-specific packages and exact key/hash manifests |
| Fitting/evaluation | Released under `CDD_MATRIX_EXECUTION_RELEASE_V1_1.json`; live counts/results are in the progress record and final result artifact |
| Public redistribution/commercial use | Not released |
| Original Yahoo BTCUSD/ETHUSD/GSPC/N225 files | Source/use basis remains unresolved; no retroactive permission inferred |

The local data and terms snapshots are under the already gitignored `data/shrink-cdd-20261013-v1/`. Qualification and experiment manifests contain metadata/hashes, while raw CSVs, normalized role packages, per-key predictions and checkpoints remain local.

## Experiment contract

`DRF-SHRINK-CDD-EXPLORATORY-20261013-V0.2` fixes two USD crypto assets, four history fractions (25/50/75/100%), seeds 17/29/43, and 600 optimizer steps per F fit: 24 neural fits / 14,400 maximum steps. Validation occurs every 50 steps; strict minimum complete validation-key MSE chooses the checkpoint. The deterministic ridge baseline uses the same retained training contexts and validation dates; persistence predicts the last context Close. Model architecture/settings are the pinned full DeReFusion bundle, with 21,743 parameters, `d_ff/d_model=4` and `d_model/n_heads=8`.

Training targets are 433/865/1,298/1,730 per fraction. Each condition also retains 96 preceding context candles, so actual raw history is 529/961/1,394/1,826 candles; the target-fraction label is not a claim that raw candles equal that fraction exactly. Validation has 365 keys; test has the same 731 keys for every history fraction of a given asset. A fixed full-training-prefix naive-loss denominator makes RMSSE comparable across history fractions. No test data determines preprocessing, checkpoint selection, ridge lambda or roster membership.

The asset-screen line reuses the full-history fits and freezes the mean validation RMSSE ranking across all three seeds before evaluation. With two qualified assets it produces top-1 and all-2 roster summaries; this is a narrower first batch than the original four-asset plan. Shared fits do not make the two questions statistically independent. Removing assets changes the reported roster composition and does not demonstrate an improvement in an individual asset's training.

Results are exploratory. The historical test interval has broader project exposure; seeds and test years are not independent market samples. The fixed 600-step budget may undertrain. F versus ridge does not isolate the nonlinear branch mechanism. No public result release or scientific claim acceptance is implied by an internal execution release.

## Repair and identity notes

- The initial snapshot helper encountered shell-quoting, missing `requests`, and out-of-root filesystem-permission problems. The implemented helper uses the standard library and the existing gitignored data root. No price data was acquired during those failed preparations.
- Runner v1 passed its synthetic model/role checks and wrote eight real-data role packages, then failed while serializing a NumPy integer in the preparation metadata. The failed attempt and packages remain preserved. Runner v1.1 converts that metadata field to a Python integer, adds a metadata-serialization synthetic check, and writes fresh `packages_v1_1/` and `runs_v1_1/` roots. Scientific settings are unchanged. Both v1 and v1.1 synthetic records are retained; only v1.1 is released for fitting.
- The release builder's initial whole-repository untracked inventory encountered existing Windows long-path warnings in historical fixture directories. Its inventory digest is a limited inventory, not proof of complete repository coverage. Exact active protocol, runner, preparation, synthetic, model-source and raw-input digests are independently bound and checked. The focused candidate inventory was subsequently checked with a per-command `core.longpaths=true` override, without changing Git configuration or historical fixture files.
- The initial post-run auditor decoded CSV target text directly as float64, although the evaluator wrote NumPy float32 shortest-roundtrip target representations. The resulting exact-equality failure was a codec mismatch (maximum normalized difference `2.35656739e-7`). Auditor v1.2 decodes target text back to float32 before float64 metric arithmetic, exactly recovers the frozen targets, and passes all 24 checks. The old auditor is preserved; fits, predictions and the original stored metric JSON were not changed. This repair does not grant scientific independent-review status.

## Bound artifacts

Active files under `research_work/project_management_2026_10_10/shrink_exploration_2026_10_13/`:

- `CDD_LOCAL_RESEARCH_QUALIFICATION_RELEASE_V1.json` and `CDD_QUALIFICATION_RESULTS_V1.json`
- `SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json`
- `run_shrink_cdd_v1_1.py`, `CDD_MATRIX_SYNTHETIC_CHECK_V1_1.json`, `CDD_PREPARATION_MANIFEST_V1_1.json`
- `CDD_MATRIX_EXECUTION_RELEASE_V1_1.json`
- `CDD_VALIDATION_ROSTER_FREEZE_V1_1.json` when the validation roster is frozen
- `CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json` when evaluation completes
- `CDD_INTERNAL_CONSISTENCY_AUDIT_V1_2.json` and `audit_and_report_cdd_v1_2.py`; older v1.1 auditor retained
- `CDD_DATASET_USE_REGISTER_V1.csv` and `CDD_WORKTREE_INVENTORY_SUPPLEMENT_V1.json`
- `PROGRESS_2026-10-13.json` separates planned/completed/internal-checked/independently-reviewed counts

Hashes and exact local paths are in the release/preparation/qualification manifests; results must be inspected before reporting empirical completion.
