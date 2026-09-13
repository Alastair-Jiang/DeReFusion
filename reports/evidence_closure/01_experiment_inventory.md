# 01 · Experiment Inventory

Every experiment family that feeds the evidence chain, with its frozen protocol and status.
"Frozen" means the definition (features, thresholds, splits, seeds, metrics) was fixed before
outcomes were inspected and was not modified afterwards.

| # | Family | Script / command source | Assets | Protocol | Seeds | Output (versioned) | Status |
|---|---|---|---|---|---|---|---|
| E1 | Baseline reproduction | `batches/run_batch_repro*.ps1` | GSPC, BTCUSD, ETHUSD | seq96/label48/pred∈{1,24}, d_model 32, 30 ep, patience 5, lr 1e-4, bs 32, cosine | 2021 | run dirs (local) + digest (`result_long_term_forecast.txt`) | complete |
| E2 | Gate ablations | same runners, `--model DeReFusion-gatev1-volatilityaware / -gatev2-learnable` | GSPC | identical to E1 | 2021 | run dirs (local) | complete (gatev3 never run — declared, not needed) |
| E3 | Volatility stratification | `analysis/analyze_volatility_regimes.py --rv-mode {relative,absolute}` | 10 assets + GSPC s2022 | causal RV on input window; train-only thresholds; 4000-resample paired bootstrap | 2021 (+2022 GSPC) | `results/volatility_stratification_*.{json,txt}` (19 files) | complete |
| E4 | Capacity sensitivity | `analysis/structure_routing_capacity_check.py` | GSPC, BTCUSD, ETHUSD | hidden ∈ {23,64,128} as **only** variable; everything else identical to E5 | 2021,2022,2023 | `results/operator-regime-capacity.csv` | complete |
| E5 | Structural-state × operator proxy | `analysis/structure_routing_experiment.py` | GSPC, BTCUSD, ETHUSD | 12 pre-registered states (train-median splits + K=3 k-means); linear (9,240 params) vs MLP (9,431); identical training protocol | 2021,2022,2023 | `results/structure_routing_raw.json`, `structural-state-summary.csv`, `operator-regime-results.csv` | complete |
| E6 | Asset-level heterogeneity (N=10) | `analysis/final_diagnosis.py` | 10 assets (GSPC merged from 2 seeds) | interaction = Δ_high50 − Δ_low50; direction vs significance separated; Spearman + LOO | 2021 (+2022 GSPC) | `asset-dependence-summary.csv`, `asset-dependence-exploration.md`, `final-diagnosis.md` | complete |
| E7 | PATH gate | inside `final_diagnosis.py` | — | five/six strict PATH-1 conditions implemented mechanically | — | verdict in `final-diagnosis.md` | complete |
| E8 | GSPC seed-merge sensitivity | `analysis/check_gspc_seed_sensitivity.py` | GSPC | recompute candidate associations with GSPC = s2021 / s2022 / merged / dropped | 2021,2022 | printed table (this task) | complete |

## Coverage and known holes

| Item | State |
|---|---|
| Assets with full stratification | 10 (GSPC, BTCUSD, ETHUSD, USDJPY, EURUSD, SOX, DJI, BABA, NVO, TM) |
| Horizons | `T ∈ {1, 24}` only (`T ∈ {7,12,36}` never run) |
| Input windows | `L = 96` only (`L ∈ {48,192}` never run) |
| Seeds | stratification & asset-level: 1/asset (GSPC 2); proxy & capacity: 3 |
| Gate variants | gatev1, gatev2 run; **gatev3-inputconditioned never run** |
| Ablations | `-woDy / -woLSTM / -woTransformer` never run (was queued as a candidate task for a second machine, since cancelled by operator instruction) |

These holes are **declared** rather than filled: none of them is required to answer the five
closure questions, and the protocol forbids designing new experiments when the existing evidence
is sufficient (spec §1).
