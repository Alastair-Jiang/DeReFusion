# PROJECT-BRIEF — complete project understanding (read-only engagement)

> **Read this first. Then follow the reading map in §9.**
>
> **Engagement mode: read-only.** The requester wants an outside agent to *understand* this
> project and to help with **planning**. Do **not** modify the repository — no commits, no branch
> pushes, no file edits, no experiment runs. If an action seems necessary, propose it instead.
>
> Anything in this file is a *summary*; when a number matters, verify it against the file named in
> §9. Where the project is uncertain, this file says so explicitly — do not resolve uncertainty by
> assumption.
>
> **Planning addendum:** a later request separately authorised documentation-only planning changes.
> The authoritative post-Gate decision tree and NS-inspired feasibility boundary are now recorded
> in `reports/evidence_closure/16_post_gate_experiment_program.md`. It changes no evidence or frozen
> Gate rule and authorises no experiment by itself; this brief remains the read-only entry point.

---

## 1. What the project is

Two stacked things:

1. **A reproduction** of *Hsieh & Chen (2026), "DeReFusion", Applied Soft Computing 203:116252*:
   a DLinear base branch + an LSTM–Transformer residual branch + **parameter-free additive
   fusion** + RevIN, on daily OHLC data (2016–2025), CPU-only, under a **frozen protocol**
   (70/10/20 chronological split; fixed seeds; paired bootstrap with 4000 resamples; `seq_len 96`,
   `label_len 48`, `d_model 32`, 30 epochs, patience 5, lr 1e-4, batch 32, cosine schedule).
   The published ordering reproduces, so the framework is a usable testbed.

2. **One research question** layered on top:

   > **Does the structural state of the input determine which operator (linear vs nonlinear) is
   > more useful?**

Measured at **two different layers, which must never be conflated**:

| Layer | What it measures | How |
|---|---|---|
| **Framework layer** | the interaction effect (does the nonlinear branch's advantage change with volatility?) | DeReFusion vs `revin-DLinear`, volatility-stratified (High = Q4+Q5, Low = Q1+Q2) |
| **Capacity-controlled proxy layer** | *operator preference* under a matched parameter budget | linear map (9,240 params) vs MLP (9,431 / 26,200 / 52,376), over 12 pre-registered structural states, 3 seeds |

## 2. Evidence ledger (all findings, with status)

| # | Finding | Numbers | Status |
|---|---|---|---|
| 1 | Reproduction validated | T=24: additive **0.06230** < linear base 0.07007 < gate 0.07191; T=1: linear base 0.01577 ≤ additive 0.01647; params 28,436 vs 4,664 | **Supported** |
| 2 | Gating does not pay | gatev1 0.06767 vs additive 0.06230 → **8.6% worse**; optimal weight ≈ constant (no switching headroom) | **Supported (negative)** |
| 3 | Volatility is **not** a universal operator-selection criterion | GSPC interaction −0.01205 / −0.02248 (2 seeds, both supported); ETHUSD −0.00943 (CI touches 0); BTCUSD **+0.01502** (supported, opposite sign). N=10: 6 negative / 4 positive, 5 supported | **Inconsistent across assets** |
| 4 | Operator preference is capacity-sensitive | hidden 23→64→128: ETHUSD +0.0145 → −0.0281 → −0.0321 (12/36 → **36/36** → 36/36 nonlinear-favoured); BTCUSD never nonlinear; GSPC ≈ parity at 128 (+0.0061). 25 sign reversals; per-seed consistency 31→29→28 of 36 | **Supported (magnitude HIGH)** |
| 5 | No robust **sample-level** routing | 12 structural states × 3 assets × 3 seeds, capacity-matched: GSPC & BTCUSD prefer linear in **12/12** states; ETHUSD's flip is **asset-wide** | **Not supported** |
| 6 | **Asset-level** heterogeneity exists | capacity-controlled: ETHUSD → nonlinear (36/36), BTCUSD → linear (36/36), GSPC → near parity | **Supported (3 assets only)** |
| 7 | Candidate structural regularity | ρ(\|ACF1\|, interaction) = **+0.733** (p=0.016), LOO [+0.633, +0.817]; ρ(realized vol, interaction) = **+0.661** (p=0.038), LOO [+0.533, +0.900]; `GSPC_SEED_SENSITIVE = NO` (ρ ∈ [+0.66, +0.69] per seed) | **Candidate / exploratory only** |
| 8 | Features that do **not** work | trend persistence (+0.042) and skew (+0.067) **flip sign under LOO**; jump ratio is **constant (1/95) for all assets** → no discriminative power | **Rejected as explanations** |
| 9 | Structural validation (in flight) | 4 pre-registered new assets; capacity layer done: **1 of 4 matched**, and the **highest-\|ACF1\| asset (YANGHE) reversed, seed-consistently** | **Unfavourable; verdict pending** |

### Two caveats that must travel with #7

- the structural features are computed **on the same test segment** as the outcome → the
  association is **contemporaneous and descriptive**; it **cannot** support an ex-ante
  ("look at the structure, then pick the operator") rule;
- **eight** features were screened before `|ACF1|`/volatility emerged → those p-values are **not
  multiplicity-clean**.

## 3. What has been ruled out

- **Volatility as a universal selection criterion** (finding #3).
- **Adaptive fusion / gating / α(X) routing as a performance lever** (finding #2, plus the
  no-headroom argument).
- **Sample-level routing** in the tested form (finding #5).
- **"Nonlinear operators are universally better"** — the opposite of the naive reading is also
  false: preference is asset-dependent and capacity-dependent.
- **Attributing early linear-favoured results to a "representation bottleneck"** — not supported;
  the permitted wording is only *"capacity sensitivity is a major uncertainty / confounder"*.
- **Trend persistence, skewness, jump ratio** as structural explanations (finding #8).

## 4. Current phase (as of 2026-09-13 evening)

**Structural validation** of finding #7 on four **pre-registered** new assets, chosen by a fixed
rule (2 lowest + 2 highest `|ACF1|` among full-history candidates) **before** any operator result:

| Group | Asset | \|ACF1\| | Pre-registered expectation |
|---|---|---|---|
| low | BYD | 0.0324 | interaction more negative → nonlinear-favoured |
| low | BOE | 0.0408 | interaction more negative → nonlinear-favoured |
| high | EASTMONEY | 0.1296 | interaction more positive → linear-favoured |
| high | YANGHE | 0.1307 | interaction more positive → linear-favoured |

- **Capacity layer (done):** 1 of 4 matched; YANGHE (highest `|ACF1|`) reversed with per-seed
  consistent signs → an unfavourable result, reported unspun.
- **Framework layer (in flight):** 8 runs (4 assets × {DeReFusion, revin-DLinear}) → the N=14
  interaction-level ρ.
- **The verdict rule is frozen** (`12a`, with the accuracy correction and cap in `12b`):
  `PASS` is **unreachable** (a pre-registered pass condition already failed); the live outcomes are
  **FAIL** or **CONDITIONAL**, and the result is **capped at CONDITIONAL regardless** because
  10 of the 14 assets are the original discovery set.

## 5. Open questions / uncertainties (in the project's own words)

| Uncertainty | Current state |
|---|---|
| **Operator form** | unresolved — only generic operators (linear map, MLP) have been tested |
| **Capacity** | known to matter; mechanism unknown; only 3 assets have capacity-controlled data |
| **Asset dependence** | supported; not explained |
| **Structural explanation** | candidate only (`\|ACF1\|`, realized volatility); not causal; not multiplicity-clean; contemporaneous |
| **Sample-level routing** | no evidence; direction paused |
| **Data provenance** | the discovery set came from Yahoo; the new cohort came from Sohu (A-shares) because this host cannot reach Yahoo (finding: local proxy breaks TLS; direct access returns 403) — so market *and* provider changed together |

## 6. Roadmap options (plan around these; do not execute here)

- **If the verdict is CONDITIONAL:** the only defensible next step is an **independent,
  prospective structural validation on a same-source cohort** — ≈15–20 assets, ≥3 seeds per asset,
  `|ACF1|` as the **single primary predictor** (realized volatility secondary; Holm if both),
  features computed **strictly before** the decision point, primary analysis run **only** on the new
  cohort. Resource rule: **more independent assets beats more seeds on existing assets.**
- **If the verdict is FAIL:** first ask whether **asset-level operator preference is itself a stable,
  reproducible property** across seeds, capacities and periods (only 3 assets have been examined).
- **The NS question** ("would a structured, NS-inspired nonlinear operator help?") stays a
  **downstream hypothesis**. It may only be considered after the prospective validation replicates,
  and even then the benchmark should start from **ordinary operator families** under capacity
  control and introduce a structured operator only if the data show the structure it exploits.
  **Eligibility is not evidence that NS works.**

## 7. Hard constraints (any proposal must respect these)

- No new adaptive gating, router, MoE, attention, learned routing, pressure term, or NS module; no
  NS inside DeReFusion.
- No changes to volatility/structural-feature definitions, thresholds, statistical tests, split,
  horizon, window, seeds, or capacity settings.
- No re-selecting assets/seeds after seeing results; no post-hoc dropping of assets/seeds/regimes.
- Raw results are always kept (never summary-only).
- Gate thresholds and the CONDITIONAL cap are frozen.
- Terminology: *NS-inspired / temporal NS-inspired nonlinear operator* only — never
  "markets are fluids" / "Navier–Stokes governs financial dynamics" as a factual claim.
- Negative evidence is reported with the same prominence as positive evidence.

## 8. Common misreadings to avoid

| Misreading | Correct statement |
|---|---|
| "Nonlinear is useless" | false: ETHUSD prefers it 36/36 at adequate capacity |
| "Nonlinear is always better" | false: BTCUSD never prefers it |
| "Volatility decides the operator" | false: the sign differs across assets |
| "The `\|ACF1\|` rule lets us pick operators per asset" | false: the association is contemporaneous, exploratory, and not multiplicity-clean |
| "NS is refuted" | false: it has never been tested; only the *eligibility* to test it is gated |
| "Capacity is just a bottleneck" | not supported; that wording is banned |
| "The gate says we should build a router" | false: routing has no robust evidence; the gate is about a *structured operator* question, and it is currently capped at CONDITIONAL |

## 9. Reading map (authoritative sources)

| Topic | File |
|---|---|
| Entry point / repo map / environment pitfalls | `RESEARCH-LINE.md` |
| Index of every report | `reports/README.md` |
| Experiment inventory (E1–E8) and coverage holes | `reports/evidence_closure/01_experiment_inventory.md` |
| Integrity matrix (protocol/raw/seed/leakage/post-hoc) | `reports/evidence_closure/02_experiment_integrity.md` |
| Per-asset table (N=10) | `reports/evidence_closure/03_asset_summary.md` |
| Structural associations + LOO + seed sensitivity | `reports/evidence_closure/04_structural_association.md` |
| Capacity sensitivity (23/64/128) | `reports/evidence_closure/05_capacity_sensitivity.md` |
| Q1–Q5 diagnosis + PATH gate | `reports/evidence_closure/06_final_diagnosis.md` |
| Status matrix R1–R9 | `reports/evidence_closure/07_evidence_matrix.md` |
| Evidence chain (+ arrows deliberately not drawn) | `reports/evidence_closure/08_evidence_chain.md` |
| Eligibility gate + upgrade conditions | `reports/evidence_closure/09_next_stage_gate.md` |
| Pre-registration (locked before runs) | `reports/evidence_closure/11_structural_validation_preregistration.md` |
| **Frozen verdict rule** | `reports/evidence_closure/12a_gate_a_decision_rule_addendum.md` |
| Adopted reviewer corrections (labels, cap, wording) | `reports/evidence_closure/12b_reviewer_response_and_corrections.md` |
| Two external reviews (verbatim) | `reports/evidence_closure/13_*`, `13b_*` |
| Gate A result (written when the runs finish) | `reports/evidence_closure/14_*` |
| Data-acquisition diagnosis + source policy | `reports/evidence_closure/15_data_acquisition_diagnosis.md` |
| Post-Gate experiment program + NS feasibility boundary | `reports/evidence_closure/16_post_gate_experiment_program.md` |
| Raw per-setting results | `reproduction/results/` (JSON/TXT/CSV) |
| Raw per-run outputs and weights | `results/`, `checkpoints/` |
| Analysis scripts | `reproduction/analysis/` |
| Runnable batch commands | `reproduction/batches/` |

## 10. What a planner is asked to produce

1. A reading-based statement of **what is established, what is merely candidate, and what is
   unknown** (in its own words, verified against §9 files — flag any disagreement with this brief).
2. The **plan conditional on the pending verdict** (both branches), each with prerequisites,
   resource estimates and explicit failure criteria.
3. A recommendation on the **single highest-value next experiment**, justified by the evidence
   matrix — **not** by the attractiveness of any model family.
4. Anything in this brief that a careful reader should **distrust**, with reasons.
