# CDD shrink exploration — completed first batch

2026-10-13; new CDD Bitstamp BTC/USD and ETH/USD data. Protocol `DRF-SHRINK-CDD-EXPLORATORY-20261013-V0.2`.
Checkout `C:/Users/26843/Documents/ChatGPT/redefusion`; HEAD `a74126c11d857da8514074b72282adc8d47f28a7`.

24/24 DeReFusion fits completed; 14,400 actual optimizer steps. Eight history conditions, three seeds per condition; all 731 test keys evaluated. Internal arithmetic/coverage checks: 24/24 PASS. DSH limited independent structural, key, timing, source and summary-arithmetic review received; raw-array review and full scientific acceptance remain pending. See the disposition report.

## Line A — history reduction

Full 2024–2025 test RMSSE below. F is seed-mean DeReFusion; L is deterministic validation-selected ridge; P is persistence. Lower is better. The denominator is fixed per asset across fractions. This is exploratory test description, not a new confirmation or a rule for silently selecting future data.

| Asset | History-target fraction | Train targets | F mean RMSSE | F seed range | L RMSSE | P RMSSE |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSD | 25% | 433 | 2.3759 | 2.2614–2.5290 | 2.5478 | 1.9663 |
| BTCUSD | 50% | 865 | 2.1485 | 2.1035–2.1939 | 2.2489 | 1.9663 |
| BTCUSD | 75% | 1298 | 2.1475 | 2.1018–2.2036 | 2.1411 | 1.9663 |
| BTCUSD | 100% | 1730 | 2.1623 | 2.0887–2.2477 | 2.1254 | 1.9663 |
| ETHUSD | 25% | 433 | 1.5597 | 1.4776–1.6637 | 1.6558 | 1.3793 |
| ETHUSD | 50% | 865 | 1.5034 | 1.4683–1.5458 | 1.5464 | 1.3793 |
| ETHUSD | 75% | 1298 | 1.4969 | 1.4562–1.5568 | 1.5086 | 1.3793 |
| ETHUSD | 100% | 1730 | 1.5314 | 1.4866–1.5999 | 1.4995 | 1.3793 |

## Line B — validation-frozen asset screen

Ranking: ETHUSD → BTCUSD. Ranking uses full-history mean validation RMSSE(F) across three seeds and was frozen before test evaluation.

| Roster | Test period | Equal-asset mean RMSSE(F) |
|---|---|---:|
| ETHUSD | all | 1.5314 |
| ETHUSD | 2024 | 1.4102 |
| ETHUSD | 2025 | 1.6439 |
| ETHUSD,BTCUSD | all | 1.8468 |
| ETHUSD,BTCUSD | 2024 | 1.7166 |
| ETHUSD,BTCUSD | 2025 | 1.9684 |

Roster-size differences describe composition: each asset is trained independently, so dropping an asset changes no retained asset model.

## Interpretation and records

This first batch covers two crypto assets on a common 24/7 daily grid. It supplies no GSPC/N225 evidence. The new source and 600-step schedule also prevent attributing differences from old Yahoo experiment reports to shrinkage alone. All fractions retain 96 preceding context candles; raw spans differ from target-count fractions. The 600-step cap is not a convergence guarantee. Historical test exposure, seed repeats and two calendar years prevent confirmatory or market-level inference. F−L does not isolate the nonlinear mechanism.

Complete per-seed/year MSE, RMSSE, difference, keys, validation histories and hashes: `CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json`. Raw/predictions/checkpoints remain under the already gitignored data root. Internal use basis is in `DRF_CDD_PROJECT_STARTUP_DECISION_2026-10-13.md`; no raw/weight/prediction publication or commercial use is granted.

Results SHA-256: `dd8017676a0ccfe64bb4ab4bcf6ab81e477d183f2495377900049249b03883f5`.
Internal check SHA-256: `569c4e10891fa8846e134d2329fed65ea863140988da57feabaef39453c02723`.
