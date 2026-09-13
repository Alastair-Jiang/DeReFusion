# External Review Request — DeReFusion operator-specialization line

**Version:** 2026-09-13 17:30 (Asia/Shanghai) · **Repository:** `Alastair-Jiang/DeReFusion` (public)
**Head commit:** `bf65f86` · **Status:** one experiment in flight; the decisive number does not exist yet

**How to use this document.** It is self-contained. Sections 1–3 are the project and its evidence;
section 4 is what has been locked and when; section 5 is the crux question with the author's
pre-committed position; section 6 is the frozen verdict rule; section 7 is what we ask you to answer.
No other context is required, but the repository paths in section 9 let you verify every number.

---

## 1. Project in one paragraph

We reproduced *Hsieh & Chen (2026), "DeReFusion", Applied Soft Computing 203:116252* — a financial
time-series forecaster with a DLinear base branch, an LSTM–Transformer residual branch,
parameter-free additive fusion, and RevIN — on independently fetched 2016–2025 daily OHLC data, CPU
only, under a frozen protocol (70/10/20 chronological split, fixed seeds, paired bootstrap CIs,
4000 resamples). The reproduction reproduced the published ordering, so the framework is a valid
testbed for one organising question: **does the structural state of the input determine which
operator — linear or nonlinear — is more useful?** A "yes" would justify sample-level routing or
adaptive gating; a "no" would make operator choice a per-asset configuration decision.

## 2. Current phase and the single decision

This phase performs **external validation** of a candidate asset-level structural regularity on new
assets that were **pre-registered before any operator result was seen**, and then issues **one**
verdict:

```
Gate A: PASS / CONDITIONAL / FAIL
        -> may a structured (NS-inspired) nonlinear operator benchmark be considered at all?
```

**Eligibility only.** Nothing in this phase implements NS, gating, routing, MoE, attention, a
pressure term, or any learned routing. "Eligible" would mean the *question* is well-posed and worth
compute; it is **not** evidence that any NS-inspired operator works.

Current goal, restated as the box it must fit:

```
Evidence -> Stable phenomenon -> Structural explanation -> New operator hypothesis
```

and explicitly **not**: `Idea -> add complexity -> performance gain -> post-hoc explanation`.

## 3. Established evidence (numbers)

### 3.1 Reproduction (GSPC, seed 2021)
| Model | T=1 MSE | T=24 MSE | T=24 R² | Params |
|---|---|---|---|---|
| DeReFusion (additive fusion) | 0.01647 | **0.06230** | 0.8691 | 28,436 |
| revin-DLinear (linear base) | **0.01577** | 0.07007 | 0.8528 | 4,664 |
| gatev1 (volatility-aware gate) | — | 0.06767 | 0.8578 | 28,580 |
| gatev2 (learnable gate) | 0.02526 | 0.07191 | 0.8489 | ~28k |

Published ordering reproduces at T=24 (+11.1% additive fusion over the linear base); both gate
variants lose to parameter-free addition.

### 3.2 Volatility conditioning — interaction = ΔMSE(high-vol half) − ΔMSE(low-vol half)
| Asset | Interaction | 95% CI | Reading |
|---|---|---|---|
| GSPC seed 2021 | −0.01205 | [−0.01545, −0.00876] | supported |
| GSPC seed 2022 | −0.02248 | [−0.02719, −0.01792] | supported, same sign (seed-robust) |
| ETHUSD | −0.00943 | [−0.01881, +0.00033] | directionally negative, **statistically inconclusive** |
| BTCUSD | +0.01502 | [+0.00615, +0.02378] | supported and **opposite in sign** |

→ Volatility is **not** a universal operator-selection criterion (**INCONSISTENT** across assets).
Raw volatility is heavily time-confounded (corr. with sample index +0.44 GSPC, −0.67 BTCUSD); the
de-trended `RV_rel` is the primary measure.

### 3.3 Adaptive fusion does not pay
GSPC, T=24: the volatility-aware gate scores 0.06767, i.e. **8.6% worse** than parameter-free
addition (0.06230). The nonlinear branch is never worse in calm regimes, so the optimal gate weight
is ≈ constant — no switching headroom. Gating line stopped.

### 3.4 Capacity sensitivity (only the nonlinear operator's hidden width varies)
| Hidden | MLP params | GSPC | BTCUSD | ETHUSD |
|---|---|---|---|---|
| 23 | 9,431 | +0.0598 (0/36 nonlinear-favoured) | +0.1783 (0/36) | +0.0145 (12/36) |
| 64 | 26,200 | +0.0250 (7/36) | +0.1888 (0/36) | **−0.0281 (36/36)** |
| 128 | 52,376 | +0.0061 (8/36) | +0.2998 (0/36) | **−0.0321 (36/36)** |

36 = 12 pre-registered structural states × 3 seeds. 25 sign reversals across widths (23 ETHUSD;
8 GSPC, all at one seed only → seed-unstable; BTC none); across-state spread *shrinks* with capacity;
per-seed direction consistency degrades 31 → 29 → 28 of 36.
→ `CAPACITY_SENSITIVE = YES (HIGH)`. Permitted wording only: *"capacity sensitivity is a major
uncertainty/confounder"* — **not** an attribution to a representation bottleneck.

### 3.5 Sample-level routing: NOT supported
12 pre-registered structural states × 3 assets × 3 seeds, capacity-matched operators (linear 9,240
params vs MLP 9,431 params, identical training protocol): GSPC and BTCUSD favour the linear operator
in **12/12** states; ETHUSD's apparent state-dependence is **asset-wide** at adequate capacity (all
12 states reverse at once), i.e. not state-specific.
→ `NO_ROBUST_SAMPLE_LEVEL_ROUTING_EVIDENCE`; the router/gating direction stays paused.

### 3.6 Asset-level heterogeneity: SUPPORTED (coverage: 3 assets)
Capacity-controlled: **ETHUSD → nonlinear** (36/36 at widths 64 and 128, 3 seeds); **BTCUSD →
linear** (36/36 at every width); **GSPC → near parity** at width 128 (+0.0061). The remaining seven
assets have interaction-level data only.

### 3.7 Candidate structural regularity (N = 10, exploratory)
Interaction signs span zero (6 negative, 4 positive; 5 supported). Spearman with the interaction:

| Feature | ρ | p | LOO range | Status |
|---|---|---|---|---|
| **\|ACF1\|** | **+0.733** | 0.016 | [+0.633, +0.817], no flip | candidate |
| **Realized volatility** | **+0.661** | 0.038 | [+0.533, +0.900], no flip | candidate |
| Kurtosis | +0.345 | 0.328 | stable | not significant |
| Trend persistence / skew | +0.042 / +0.067 | 0.91 / 0.86 | **sign flips under LOO** | single-asset sensitive |
| Jump ratio | — | — | — | **constant (1/95) for all assets → no discriminative power** |

GSPC seed-merge sensitivity tested: `GSPC_SEED_SENSITIVE = NO` (ρ ∈ [+0.66, +0.69] under either
single seed; +0.817 with GSPC dropped). Prior evidence-closure pass: **PATH 1** (candidate
structural regularity) and `NS_BENCHMARK_ELIGIBLE = CONDITIONAL`.

## 4. What is locked, and when

1. **Pre-registration** (`reports/evidence_closure/11_structural_validation_preregistration.md`,
   commit `669c80e`) — locked **before any operator run**. New assets chosen by a fixed rule (2
   lowest + 2 highest `|ACF1|` among full-history new candidates):

| Group | Asset | \|ACF1\| | realized vol | Pre-registered expectation |
|---|---|---|---|---|
| low | BYD | 0.0324 | 0.0233 | interaction more negative → nonlinear-favoured |
| low | BOE | 0.0408 | 0.0154 | interaction more negative → nonlinear-favoured |
| high | EASTMONEY | 0.1296 | 0.0236 | interaction more positive → linear-favoured |
| high | YANGHE | 0.1307 | 0.0151 | interaction more positive → linear-favoured |

   Conflict flags were recorded too (BYD: low `|ACF1|` but high RV → the two features predict
   opposite signs). Data provenance deviation is declared: the original ten assets came from Yahoo
   Finance, the new ones from **Sohu**, and all new assets are **A-shares** (the host's system proxy
   had broken TLS forwarding, which blocked every other channel; requests bypassing it work).

2. **Gate A decision-rule addendum** (`reports/evidence_closure/12a_gate_a_decision_rule_addendum.md`,
   commit `bf65f86`) — locked **while the decisive number did not exist**, with this audit evidence
   recorded in the file:

```
$ ls reproduction/results/volatility_stratification_{BYD,BOE,EASTMONEY,YANGHE}_relative_s2021.json
  -> none of the four files exists (framework runs still in flight, started 17:14)
```

3. **Capacity layer already complete** (commit `5f35dc6`; proxy operators, widths 64/128, 3 seeds):

| New asset | \|ACF1\| | mean ΔMSE w64 / w128 | Expected | Verdict |
|---|---|---|---|---|
| BYD | 0.032 | −0.066 / −0.085 | nonlinear | **MATCH** |
| BOE | 0.041 | +0.009 / −0.0004 | nonlinear | mismatch (mixed/tie) |
| EASTMONEY | 0.130 | +0.004 / −0.005 | linear | mismatch (mixed/tie) |
| **YANGHE** | **0.131 (highest)** | **−0.006 / −0.013** | linear | **mismatch, opposite sign, per-seed consistent** |

4. **In flight:** 8 framework runs (4 new assets × {DeReFusion, revin-DLinear}, T=24, seed 2021),
   started 17:14, ETA ≈ 19:45–20:15, then 4 stratifications → the N=14 interaction-level ρ.

## 5. The crux question, and the author's pre-committed position

**Question.** Should the capacity-level operator-preference mismatch count as auxiliary
counter-evidence against the interaction-level structural regularity, or may only the N=14
interaction-level ρ decide Gate A?

**Position (committed before the result).** The two layers measure different things and must not be
weighted equally:

| Layer | Quantity | What it can test |
|---|---|---|
| **A — interaction level (primary)** | ρ between asset features and **Δ_interaction** on the extended asset set | whether the **regularity itself** survives new assets. This is the quantity the regularity was fitted on. |
| **B — operator-preference level (pre-registered secondary)** | mean ΔMSE of the proxy operators at widths 64/128 per new asset, 3 seeds | whether a **derived implication** of the regularity holds. The regularity never asserted a ΔMSE-level consequence; that implication was an extrapolation, locked in advance as a prediction. |

A consequence can fail while the claim survives; a claim can fail while a noisy consequence looks
right. Hence: **A tests the claim, B tests a consequence of the claim.**

## 6. Frozen verdict rule

- Pre-registered PASS condition (1) — *"the new assets' operator preference is broadly consistent
  with the association"* — is already failed at **1 of 4** (BYD matches; BOE/EASTMONEY mixed/tie;
  YANGHE reversed with per-seed-consistent signs at both widths).
  ⇒ **`PASS` is unreachable**, removed by the pre-registered conditions themselves.
- **`FAIL` if any of:** (i) ρ(\|ACF1\|, Δ_interaction) on the extended set flips sign vs +0.733, or
  drops below +0.30, or p rises above 0.10, or the LOO range crosses zero; (ii) Layer B becomes
  **systematic** — **≥3 of 4** new assets contradict the pre-registered preference with
  per-seed-consistent mean ΔMSE signs at both widths; (iii) for any new asset the sign of the mean
  ΔMSE differs between widths 64 and 128; (iv) ρ is single-asset driven (drop-one sign flip);
  (v) a protocol/leakage/post-hoc-selection finding.
- **`CONDITIONAL` if** Layer A holds (sign preserved, LOO-stable, p < 0.10, not single-asset driven)
  while Layer B stays as observed → keep the regularity as an **interaction-level candidate only**,
  **explicitly withdraw the operator-preference implication**, and require an independent, same-source,
  multi-seed replication before any structured-operator benchmark.
- Thresholds are enforced mechanically by `reproduction/analysis/sv_gate_a.py`; no threshold may be
  adjusted once the N=14 numbers exist.

**Rationale for the ≥3/4 threshold (recorded before the result).** Layer B's new assets are all
A-shares from a different data source; a systematic market/microstructure difference could produce
operator-preference mismatches for reasons unrelated to the regularity. So a single reversed asset
is not decisive — but this cuts both ways: a fully *passing* Layer B would also have been weak
evidence, which is consistent with keeping Layer A primary.

## 7. What we ask you to answer (as external reviewer)

1. **The five project questions** (`reports/CHATGPT_BRIEF.md` §8): (a) is the operator-preference
   mismatch decisive, and how should the layer distinction be stated; (b) what minimum design would
   move the regularity from CANDIDATE to SUPPORTED given 1 seed/asset, N ≈ 14 and a source change —
   and how to control multiplicity; (c) if Gate A is FAIL/CONDITIONAL, what is the defensible next
   research question that does not smuggle in the NS assumption; (d) how to state the capacity
   result without over-claiming, and what evidence would justify a stronger claim; (e) where we may
   be fooling ourselves (is `|ACF1|` a proxy for liquidity/microstructure/sample period; does an
   A-share-only extension bias the test).
2. **Your verdict on section 5.** Do you accept "Layer A primary, Layer B a derived consequence"? If
   you disagree, say so **now**: the disagreement must be resolved *before* the N=14 number exists
   (that is the point of locking). If your argument is stronger, we will record a `12b` revision with
   timestamp and rationale, still before the result.
3. **Your opinion on the thresholds** (≥3/4, \|ρ\| < 0.30, p > 0.10). Also changeable only before the
   result exists.
4. **Your weighting of the provenance deviation** (Yahoo → Sohu; all new assets A-shares).
5. **Your recommended next research question** if the verdict is CONDITIONAL or FAIL — the strictest
   defensible framing you would accept.

## 8. Constraints your recommendation must respect

No new adaptive gating, router, MoE, attention, learned routing, pressure term, or NS module; no NS
inside the full DeReFusion; no changes to volatility or structural-feature definitions, thresholds,
statistical tests, split, horizon, window, seeds, or capacity settings; no re-selecting assets after
seeing results; no post-hoc dropping of seeds/assets/regimes; raw results are always kept (never
summary-only); no new experiments invented when existing evidence suffices; terminology must stay
*"NS-inspired / temporal NS-inspired nonlinear operator"* (never "markets are fluids" or similar);
negative evidence is reported with the same prominence as positive evidence; and the stage stops at
the verdict — it does not begin the benchmark.

## 9. Artifacts for verification

```
reports/CHATGPT_BRIEF.md                             this project, for a planner
reports/evidence_closure/00_repo_audit.md             branch/head/dirty state, dir map, gaps
reports/evidence_closure/01_experiment_inventory.md   E1..E8, protocol, seeds, status
reports/evidence_closure/02_experiment_integrity.md   same-protocol/raw/seed/leakage/post-hoc matrix
reports/evidence_closure/03_asset_summary.md          per-asset table (N=10)
reports/evidence_closure/04_structural_association.md Spearman + LOO + GSPC seed sensitivity
reports/evidence_closure/05_capacity_sensitivity.md   23/64/128 and the three checks
reports/evidence_closure/06_final_diagnosis.md        Q1..Q5 + six-condition PATH gate
reports/evidence_closure/07_evidence_matrix.md        R1..R9 with status vocabulary
reports/evidence_closure/08_evidence_chain.md         chain, support per step, non-claims
reports/evidence_closure/09_next_stage_gate.md        CONDITIONAL verdict + upgrade conditions
reports/evidence_closure/10_structural_validation_blocked.md   acquisition blocker + §9 check
reports/evidence_closure/11_structural_validation_preregistration.md   assets + directions LOCKED
reports/evidence_closure/12a_gate_a_decision_rule_addendum.md          verdict rule LOCKED
reproduction/analysis/                                 all analysis scripts (see 00_repo_audit.md)
reproduction/results/                                  versioned per-setting JSON/TXT/CSV
docs/ROADMAP.md                                        state of record + environment pitfalls
docs/latex/                                            stage reports (elsarticle + IEEEtran, EN/ZH)
```

**Timeline.** Framework runs finish ≈ 19:45–20:15; an idempotent finalisation job at 19:45 computes
the N=14 analysis and the Gate A verdict. Anything you answer before then can still change the locked
rules; anything after can only be recorded as commentary in the final report.
