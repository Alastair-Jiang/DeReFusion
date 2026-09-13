# Briefing for an external reviewer (ChatGPT)

**Project:** DeReFusion reproduction + operator-specialization research line
**Repository:** `Alastair-Jiang/DeReFusion` (public) · local `C:\Users\26843\Desktop\project\repos\DeReFusion`
**State as of:** 2026-09-13 17:20 (Asia/Shanghai) · head commit `8d1b017`
**Status of the current experiment:** running (framework-level runs for 4 new assets), Gate A verdict pending (~20:00)

This document is self-contained: it states what the project is, what the current goal is, what has
already been established (with numbers), what is being tested right now, the rules that must not be
broken, and the decisions we need help with.

---

## 1. What this project is

The starting point is a **reproduction** of *Hsieh & Chen (2026), "DeReFusion", Applied Soft Computing
203:116252*: a financial time-series forecasting framework with a DLinear base branch, an
LSTM–Transformer residual branch, parameter-free additive fusion, and RevIN. Reproduction is done
with independently fetched 2016–2025 daily OHLC data, on CPU, under a frozen protocol
(70/10/20 chronological split, fixed seeds, paired bootstrap CIs with 4000 resamples).

The reproduction turned into a research line with a single organising question:

> **Does the structural state of the input determine which operator (linear vs nonlinear) is more
> useful?**

That question matters because a "yes" would justify sample-level routing / adaptive gating; a "no"
would mean operator choice is a per-asset configuration problem rather than a per-sample one.
The reproduction itself reproduced the published ordering, so the framework is a valid testbed.

## 2. Current goal (this phase)

We are validating a **candidate asset-level structural regularity** that emerged internally, on
**new assets that were pre-registered before being run**, and then issuing a single gate verdict:

```
Gate A: PASS / CONDITIONAL / FAIL  ->  may we consider a structured (NS-inspired) nonlinear
                                       operator benchmark at all?  (eligibility only, no NS work)
```

The next-stage hypothesis under consideration is *"a temporal NS-inspired structured nonlinear
operator may be worth testing against a capacity-matched MLP"*. **Nothing in this phase implements
NS, gating, routing, MoE or attention** — the sole output is an eligibility verdict.

## 3. What is already established (with numbers)

### 3.1 Reproduction (GSPC, seed 2021, T = forecast horizon)
| Model | T=1 MSE | T=24 MSE | T=24 R² | Params |
|---|---|---|---|---|
| DeReFusion (additive fusion) | 0.01647 | **0.06230** | 0.8691 | 28,436 |
| revin-DLinear (linear base) | **0.01577** | 0.07007 | 0.8528 | 4,664 |
| gatev1 (volatility-aware gate) | — | 0.06767 | 0.8578 | 28,580 |
| gatev2 (learnable gate) | 0.02526 | 0.07191 | 0.8489 | ~28k |

The published ordering reproduces at T=24 (+11.1% for additive fusion over the linear base);
both gate variants lose to parameter-free addition.

### 3.2 Volatility conditioning (interaction = ΔMSE_high50 − ΔMSE_low50, relative volatility)
| Asset | Interaction | 95% CI | Reading |
|---|---|---|---|
| GSPC seed 2021 | −0.01205 | [−0.01545, −0.00876] | supported (nonlinear value grows with volatility) |
| GSPC seed 2022 | −0.02248 | [−0.02719, −0.01792] | supported, same sign (seed-robust) |
| ETHUSD | −0.00943 | [−0.01881, +0.00033] | directionally negative, statistically inconclusive |
| BTCUSD | +0.01502 | [+0.00615, +0.02378] | supported and **opposite in sign** |

→ **Volatility is not a universal operator-selection criterion** (`INCONSISTENT` across assets).
A methodological check showed raw volatility is heavily time-confounded (corr with sample index
+0.44 for GSPC, −0.67 for BTCUSD); the de-trended `RV_rel` is the primary measure.

### 3.3 Adaptive fusion (gating) does not pay
On GSPC (T=24) the volatility-aware gate scores MSE 0.06767, i.e. **8.6% worse** than
parameter-free addition (0.06230). Because the nonlinear branch is never worse in calm regimes,
the optimal gate weight is ~constant → the gate has no switching headroom. Gating line stopped.

### 3.4 Capacity sensitivity (only the nonlinear operator's hidden width varies)
| Hidden width | MLP params | GSPC | BTCUSD | ETHUSD |
|---|---|---|---|---|
| 23 | 9,431 | +0.0598 (0/36 nonlinear-favoured) | +0.1783 (0/36) | +0.0145 (12/36) |
| 64 | 26,200 | +0.0250 (7/36) | +0.1888 (0/36) | **−0.0281 (36/36)** |
| 128 | 52,376 | +0.0061 (8/36) | +0.2998 (0/36) | **−0.0321 (36/36)** |

(36 = 12 pre-registered structural states × 3 seeds.) Findings: 25 sign reversals across widths
(23 of them ETHUSD, 8 GSPC — all at one seed only, i.e. seed-unstable; BTC none); across-state
spread *shrinks* with capacity; per-seed direction consistency degrades 31→29→28 of 36.
→ **`CAPACITY_SENSITIVE = YES` (magnitude HIGH).** The earlier "linear dominates everywhere"
reading was partly a capacity artefact, but the permitted wording is only
*"capacity sensitivity is a major uncertainty/confounder"* — **not** an attribution to a
representation bottleneck.

### 3.5 Sample-level routing: NOT supported
12 pre-registered structural states × 3 assets × 3 seeds with capacity-matched operators
(linear 9,240 params vs MLP 9,431 params, identical training protocol): GSPC and BTCUSD favour the
linear operator in **12/12** states; ETHUSD's apparent state-dependence is **asset-wide** at
adequate capacity (all 12 states reverse at once), i.e. not state-specific.
→ **`NO_ROBUST_SAMPLE_LEVEL_ROUTING_EVIDENCE`.** The router/gating direction stays paused.

### 3.6 Asset-level heterogeneity: SUPPORTED
Under capacity control: **ETHUSD → nonlinear** (36/36 observations at widths 64 and 128, 3 seeds),
**BTCUSD → linear** (36/36 at every width), **GSPC → near parity** at width 128 (+0.0061).
This is *asset-level* operator heterogeneity — an operator-per-asset configuration question.

### 3.7 Candidate structural regularity (N = 10 assets, exploratory)
Interaction effects span zero (6 negative, 4 positive; 5 statistically supported). Spearman
association with the interaction effect:

| Feature | ρ | p | LOO range | Status |
|---|---|---|---|---|
| **\|ACF1\|** | **+0.733** | 0.016 | [+0.633, +0.817], no sign flip | candidate |
| **Realized volatility** | **+0.661** | 0.038 | [+0.533, +0.900], no sign flip | candidate |
| Kurtosis | +0.345 | 0.328 | stable | not significant |
| Trend persistence / skew | +0.042 / +0.067 | 0.91 / 0.86 | **sign flips under LOO** | single-asset sensitive |
| Jump ratio | — | — | — | **constant (1/95) for all assets → no discriminative power** |

Reading: assets with **higher |ACF1| and higher realized volatility** show a *weaker or reversed*
nonlinear advantage in turbulent regimes. GSPC seed-merge sensitivity was tested
(`GSPC_SEED_SENSITIVE = NO`: ρ ∈ [+0.66, +0.69] under either single seed, +0.817 with GSPC dropped).
A previous evidence-closure pass issued **PATH 1 (candidate structural regularity)** and
**NS_BENCHMARK_ELIGIBLE = CONDITIONAL**.

## 4. What is being tested right now (the current experiment)

The protocol requires **external validation of the above regularity on new assets chosen before any
operator result is seen**, then a single gate verdict. Status:

- **Data acquisition was blocked and then solved.** On this host the Windows system proxy
  (`127.0.0.1:7897`) is enabled but its TLS forwarding is broken — *the* cause of all
  "SSL handshake timeout" failures (Yahoo, Stooq, and even a mirror that had worked minutes
  earlier). Requests that explicitly bypass the proxy work. The only working market-data source
  found is **Sohu**; 31 new candidate datasets were fetched (A-share large caps + ETFs, 2016–2025,
  schema identical). *Provenance deviation recorded: original ten assets from Yahoo, new ones from
  Sohu, all new assets are A-shares.*
- **Pre-registration locked** (commit `669c80e`) before any run: from full-history new candidates,
  take the 2 with the **lowest** and the 2 with the **highest** `|ACF1|`:
  **BYD (0.0324), BOE (0.0408)** — low; **EASTMONEY (0.1296), YANGHE (0.1307)** — high.
  Predicted directions were locked, including conflict flags (BYD has low |ACF1| but high RV, so the
  two candidate features predict opposite signs for it).
- **Capacity layer already done** (proxy operators, widths 64/128, 3 seeds — commit `5f35dc6`):

| New asset | \|ACF1\| | mean ΔMSE w64 / w128 | Pre-registered expectation | Verdict |
|---|---|---|---|---|
| BYD | 0.032 | −0.066 / −0.085 | nonlinear-favoured | **MATCH** |
| BOE | 0.041 | +0.009 / −0.0004 | nonlinear-favoured | mismatch (mixed/tie) |
| EASTMONEY | 0.130 | +0.004 / −0.005 | linear-favoured | mismatch (mixed/tie) |
| **YANGHE** | **0.131 (highest)** | **−0.006 / −0.013** | linear-favoured | **mismatch, opposite sign, per-seed consistent (`---`)** |

  → On the operator-preference layer the structural prediction matches **1 of 4** new assets, and the
  highest-`|ACF1|` asset contradicts it in a seed-consistent way. This is an unfavourable signal,
  reported as such.
- **Framework layer running now:** 8 runs (4 new assets × {DeReFusion, revin-DLinear}, T=24,
  seed 2021, 2-way parallel), from 17:14, ETA ≈ 19:45–20:15, then 4 stratifications. This produces
  the new **interaction effects** needed to recompute ρ on **N = 14**.
- **Gate A tooling ready:** `reproduction/analysis/sv_gate_a.py` (N=14 table, Spearman + p for both
  candidate features, leave-one-asset-out, five views [all / exclude GSPC / LOO range / width 64 /
  width 128], capacity sign-contradiction check, per-asset comparison against the pre-registration,
  and the PASS / CONDITIONAL / FAIL verdict), plus an idempotent, duplicate-aware finalisation job at
  19:45.

## 5. Decision rules (pre-registered, not adjustable now)

- **PASS** if: (1) new assets' preference broadly consistent with the association, (2) the `|ACF1|`
  Spearman direction does not flip, (3) no fatal LOO sign flip, (4) not driven by one new asset,
  (5) widths 64 and 128 do not contradict each other, (6) no protocol/leakage/selection problem.
- **CONDITIONAL** if the direction holds but statistical support weakens markedly.
- **FAIL** on sign reversal, strong single-asset dependence, capacity contradiction, or
  disappearance of the association.
- If FAIL: `NS_BENCHMARK_ELIGIBLE` is downgraded from CONDITIONAL, and the `|ACF1|` relation is
  re-framed as *sample-specific* rather than a portable regularity.

## 6. Hard constraints in force

No new adaptive gating, router, MoE, attention, learned routing, pressure term, or NS module; no
NS inside the full DeReFusion; no changes to volatility or structural-feature definitions,
thresholds, statistical tests, split, horizon, window, seeds, or capacity settings; no re-selecting
assets after seeing results; no post-hoc dropping of seeds/assets/regimes; raw results are kept
(never summary-only); experiments are not invented when existing evidence suffices. Language must be
*"NS-inspired / temporal NS-inspired nonlinear operator"* — never "financial markets are fluids" or
similar. Negative evidence is reported with the same prominence as positive evidence.

## 7. Repository map (for verification)

```
reproduction/analysis/   analyze_volatility_regimes.py, structure_routing_experiment.py,
                         structure_routing_capacity_check.py (--assets/--widths overrides),
                         final_diagnosis.py, asset_dependence_analysis.py,
                         association_robustness_check.py, check_gspc_seed_sensitivity.py,
                         sv_gate_a.py, candidate_features.py, sv_capacity_report.py
reproduction/batches/    run_batch_repro*.ps1, run_asset_sweep.ps1,
                         run_structural_validation.ps1   <-- currently running
reproduction/results/    volatility_stratification_*.json/.txt, operator-regime-capacity*.csv,
                         structure_routing_raw.json, candidate_pool_features.csv
reports/evidence_closure/ 00_repo_audit ... 11_structural_validation_preregistration
docs/ROADMAP.md          state of record + environment pitfalls
docs/latex/              stage reports (elsarticle + IEEEtran, EN/ZH twins, PDFs)
```
Known environment pitfalls (documented, cost real time): the broken system proxy above; killing
DataLoader worker processes (`spawn_main`) deadlocks the parent trainer, so a stall must be detected
by process CPU time rather than log output; PowerShell scripts must stay ASCII-only; CPU runs need
`--no_use_gpu`; the data pipeline needs `patool`, `huggingface_hub`, `sktime`, `datasets`, and
`joblib==1.5.3`.

## 8. Open questions we would like an external reviewer to help decide

1. **Is the operator-preference mismatch decisive?** The association was fitted on the *interaction*
   (framework-level, volatility-conditioned) but partially checked on the *operator preference*
   (proxy operators). They are different quantities — is it defensible to treat a mismatch in the
   latter as evidence against the former, or must the verdict rest only on the interaction-level
   ρ recomputation? What is the cleanest way to state that distinction in the final report?
2. **What would a sufficient validation look like?** Given 1 seed per asset, N ≈ 14, and a data
   source change, what is the minimum credible design to move from CANDIDATE to SUPPORTED
   (more assets vs more seeds vs a held-out market), and how should multiplicity be controlled?
3. **If Gate A is FAIL or CONDITIONAL**, what is the defensible next research question? Should the
   line stop at "operator choice is asset- and capacity-dependent, structurally unexplained", or is
   there a legitimate reframing (e.g. testing operator families per asset under capacity control)
   that does not smuggle in the NS assumption?
4. **How to present the capacity result without over-claiming?** We currently refuse to attribute the
   early linear-favoured results to a representation bottleneck. Is that the right level of caution,
   and what evidence would be needed to make a stronger capacity claim?
5. **Anything we are fooling ourselves about.** Specifically: is `|ACF1|` likely to be a proxy for
   something else (trading frequency, market microstructure, sample period), and does the A-share-only
   extension systematically bias the test?

---

## 9. One-paragraph summary to hand to a planner

We reproduced a published fusion framework and then investigated whether the linear-vs-nonlinear
operator choice should be made per-sample (routing) or per-asset (configuration). The evidence so
far: routing has **no** robust support; operator preference is **asset-dependent** and
**capacity-sensitive**; the earlier uniform preference for the linear operator was partly a capacity
artefact; and a candidate regularity (`|ACF1|`, realized volatility ↔ weaker nonlinear advantage in
turbulent regimes) was found on ten assets. We are now externally validating that regularity on four
pre-registered new assets. The capacity layer already shows 1 of 4 matches, with the highest-`|ACF1|`
asset pointing the opposite way; the interaction-level test finishes within hours. The single
decision to make afterwards is the Gate A verdict (PASS / CONDITIONAL / FAIL) and, if not FAIL,
whether a **capacity-matched structured nonlinear operator benchmark** is justified — with NS treated
as one candidate hypothesis, never as an assumption, and no model work done in this phase.
