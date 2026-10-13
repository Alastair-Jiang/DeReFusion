# Shrink exploration — execution matrix candidate v0.1

Date: 2026-10-13 (Asia/Shanghai)  
Status: **DESIGN CANDIDATE — NO REAL-DATA ACCESS OR RUN RELEASE**  
Parent design: `SHRINK_EXPLORATION_PROTOCOL_DRAFT_V0.1.md`  
This file separates the two questions into independent run families. It does not modify R1 or authorize data use.

## Shared candidate contract

Carry forward these fields only as candidates from `R1_APPROVED_DESIGN_V1.json`; this is a new exploratory study and needs its own version-bound release:

| Field | Candidate value | Still to verify/freeze |
|---|---|---|
| Target/features | Next observed-row `Close`; `Open,High,Low,Close`; MS | Source schema, units, adjustments, positive/valid target range |
| Sequence/horizon | `seq_len=96`, `pred_len=1`, per-asset observed-row order | Calendar/grid meaning and row/key reconciliation per asset |
| Time split | Train `[2018-01-01,2023-01-01)`, validation `[2023-01-01,2024-01-01)`, exploratory test `[2024-01-01,2026-01-01)`, half-open on target date | Reconcile exact keys; historical exposure means this cannot support an unexposed confirmation |
| Neural arm | Full DeReFusion; config `d_model=32`, `n_heads=4`, `e_layers=1`, `d_ff=128`, `dropout=0.3`, moving average 25, one LSTM layer; Adam `lr=0.001`, batch 32, seeds 17/29/43 | Re-pin actual source/config; decide optimizer-step cap, validation cadence, and stop rule before data access |
| Baselines | Same-history ridge linear model; persistence | Freeze ridge feature transform, lambda selection, and exact persistence formula |
| Comparison | Shared evaluation keys; per-asset MSE and train-scale RMSSE; report each seed and each test calendar year | Freeze RMSSE scale formula, coverage floor, missing-key handling, and resource cap |
| Inference | Exploratory descriptions only; no pooled raw MSE, market-level significance, or confirmatory wording | Keep all failure/deviation rows and all assets/windows visible |

## Line A — reduce history within each asset

**Question:** For a fixed qualified asset and model/baseline pair, how does the descriptive test loss change when only the training-history tail is reduced?

| Run factor | Fixed levels / rule |
|---|---|
| Qualified assets | Exact assets passing source, rights, target, grid, and coverage checks; lock list before any prices are read |
| Training-history fraction | 25%, 50%, 75%, 100% of eligible training-prefix target rows, taking a contiguous tail ending at the same train cutoff |
| Invariants | Same file hash, target, features, context length, validation/test periods, shared test keys, F/L/P definitions, seed list, preprocessing and validation rules |
| Main output | Per `(asset, fraction, seed, test year)`: key coverage, MSE(F), MSE(L), MSE(P), RMSSE, `MSE(L)-MSE(F)`, optimizer steps, epochs, and failure/deviation status |
| Interpretation | Each fraction is paired on identical test keys within asset. No independent-market-sample claim; seeds are optimization repeats. |

The exact number of train targets per fraction and the common evaluation-key manifest are generated only after a source-qualified file is admitted. The split/key generator must be model-independent and must not inspect price values to choose keys. A coverage failure disqualifies that asset/fraction under a pre-written rule; it does not silently shrink the common key set.

## Line B — screen assets and report reduced panels

**Question:** Which eligible assets are easier for the frozen per-asset forecasting task, and what happens to a clearly labeled portfolio summary when the asset roster is narrowed?

This line is a **descriptive asset screen**, not evidence that dropping assets improves any given asset's forecast. The current design trains each asset independently; a causal claim about fewer training assets would require a separate pooled cross-asset training experiment.

| Run factor | Fixed levels / rule |
|---|---|
| Candidate assets | Independently qualify each asset before score review; preserve failures and ineligible assets in the roster |
| History | 100% eligible training prefix for each asset |
| Difficulty ranking | Rank by validation RMSSE of the frozen primary model, with a predeclared deterministic tie rule; do not use test scores to select the roster |
| Roster sizes | Nested top-1, top-2, top-3, and all-qualified-asset sets from the validation ranking |
| Outputs | Full per-asset results first; then equal-asset mean/median RMSSE and coverage for each roster, labeled as composition-sensitive and exploratory |
| Test use | Use test only after the validation ranking and roster definitions are frozen; current 2024–2025 test period has prior research exposure, so results remain exploratory and need a genuinely later untouched period for confirmation |

Report trading-calendar and 24/7 assets separately unless a justified comparable estimand is established. Never average raw MSE across unlike price scales. The ranking identifies only assets that were easier under this specific model, target, split, and historical sample.

## Current gates

| Gate | Status | Evidence / next action |
|---|---|---|
| G0 — source and processing basis | **BLOCKED** | All four per-file rights bases remain unverified. The current Yahoo Terms of Service prohibit automated access/collection without Yahoo's express prior permission; see [Yahoo Terms of Service, §2.4.9](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html). This is a present-day source, not proof of the terms applicable at historical acquisition or of the actual source for BTCUSD/ETHUSD/GSPC. Obtain custodian evidence and the applicable dated/region-specific terms, or replace with a source whose license expressly permits this research use. |
| G1 — question and design | **PARTIALLY FROZEN** | The two estimands, factors, rank rule, and reporting limits are specified here. Exact feature/scaler behavior, step cap, validation cadence, loss/coverage thresholds, tie rules, and output rights still need a frozen configuration. |
| G2 — scoped execution release | **NOT READY** | Requires G0 clearance, exact file hashes/row-key manifests, completed synthetic resource/failure check for this candidate matrix, and a signed local run manifest. |
| G3 — empirical execution and audit | **NOT STARTED** | No real-data values have been read and no fits/scores have been run for this study. |

## Immediate work order

1. Ask the T004 custodian for a sanitized, signed source-and-rights statement, exact acquisition date/method, applicable Yahoo terms/version/region, and explicit local research-processing permission. For BTCUSD/ETHUSD/GSPC, request equivalent per-file records from the unknown acquiring agent; scripts and Git commits are insufficient.
2. Freeze the remaining configuration and run the candidate matrix through synthetic inputs only. Synthetic success validates plumbing, not data permission or forecast performance.
3. If G0 remains unresolved, issue a documented no-run decision by the deadline and identify a rights-cleared replacement source. Do not read prices to try to infer where the files came from.

