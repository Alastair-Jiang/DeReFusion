# Status report for an external decision-maker (2026-09-14)

**Purpose:** hand an outside planner enough verified state to decide *what this project should do
next* — including deciding that the right answer is "wait". Nothing here is a request to execute
code; it is a request for a **decision plus reasoning**.

**Read the sources, not just this summary.** Public repo: `github.com/Alastair-Jiang/DeReFusion`
(`main`). Key files:

| Topic | File |
|---|---|
| Entry / map / pitfalls | `RESEARCH-LINE.md` |
| Whole-project briefing + misreading table | `PROJECT-BRIEF.md` |
| Post-Gate plan (FAIL/CONDITIONAL branches) | `reports/evidence_closure/16_post_gate_experiment_program.md` |
| Gate A result (FAIL) | `reports/evidence_closure/14_structural_validation_result.md` |
| F1 result (SUCCESS + caveat) | `reports/evidence_closure/21_f1_result.md` |
| Adopted F1 framing + allocation | `reports/evidence_closure/22_f1_framing_and_task_allocation.md` |
| C1 pre-registration, now incl. the LOCKED cohort table | `reports/evidence_closure/23_c1_preregistration.md` |
| NS direction assessment (external, archived) | `reports/evidence_closure/17_ns_directions_astra.md` |
| Two-machine split | `docs/TWO-INSTANCE-SPLIT.md` |

---

## 1. What the project is

Reproduction of *Hsieh & Chen (2026), DeReFusion* (Applied Soft Computing 203:116252) plus one
research question on top: **does the structural state of the input determine which operator (linear
vs nonlinear) is more useful?** Two measurement layers are kept strictly separate: the framework
layer (DeReFusion vs `revin-DLinear`, volatility-stratified) and a capacity-controlled proxy layer
(linear map vs MLP at matched budgets).

## 2. Established results (frozen protocol, CPU-only)

| Finding | Status |
|---|---|
| Reproduction validated (T=24: additive 0.06230 < linear 0.07007 < gate 0.07191) | Supported |
| Gating / adaptive fusion does not pay (8.6 % worse than parameter-free addition) | Supported (negative) |
| Volatility is **not** a universal operator-selection criterion (GSPC supports, ETHUSD indeterminate, BTCUSD reverses) | Inconsistent |
| Operator preference is **capacity-sensitive** (width 23→64→128: ETHUSD 12/36→36/36 nonlinear-favoured; BTCUSD never; 25 sign reversals) | Supported |
| No robust **sample-level** routing (12 states × 3 assets × 3 seeds, capacity-matched) | Not supported |
| **Asset-level** heterogeneity | Supported, but capacity-controlled coverage was only three assets |
| Candidate structural regularity `\|ACF1\|` ↔ interaction: ρ = **+0.688** (p = 0.007, LOO [+0.610, +0.786]) on N = 14, of which **10 are the discovery set** | Candidate only |
| Gate A verdict on that candidate | **FAIL** — triggered the frozen capacity-contradiction condition (BOE, EASTMONEY change sign between widths 64 and 128); PASS was unreachable; preference match 2/4, direction 3/4 |
| Consequence | `NS_BENCHMARK_ELIGIBLE` **downgraded from CONDITIONAL**; `\|ACF1\|` re-framed as **sample-specific** |

## 3. F1 (the breadth panel) — SUCCESS, with half the conclusion being a caveat

70 additional capacity-controlled fits (`reproduction/results/operator-regime-capacity_f1.csv`):

- **Stable (seed- and width-stable): 4 of 7** — TM (nonlinear), DJI, EURUSD, USDJPY (linear);
  **3 new opposite-sign pairs** beyond ETH/BTC → the locked success criterion is met.
- **Unstable: 3 of 7** — BABA (never seed-stable), NVO (seed-unstable at 128), SOX (sign flips
  between widths). Per-seed direction consistency also degrades with capacity: 75/88 → 68/88 → 61/88.
- **Adopted framing (owner, 2026-09-14):** F1 supports only the narrow claim that asset-level
  preference is *not an ETH/BTC artefact*; the 3/7 instability is **half the conclusion**. Preference
  is reproducible on most tested assets but **is not a constant property of an asset**, and capacity
  is the **main uncertainty/confounder rather than a fixable deficiency**.
- An independent recomputation by the peer machine reproduced the verdict with **zero differences**.

## 4. What is running right now

**C1 — the independent prospective same-source cohort.** State:

- **Cohort LOCKED** (`23` §8): 20 assets, **single provider (Yahoo chart API)** — the same provider as
  the discovery set, different markets; per-file SHA-256 recorded; no exclusions triggered; acquired
  through the peer machine's working proxy because this host cannot reach Yahoo (403 direct, TLS
  timeouts through its own broken proxy).
- **Predictor FROZEN before any outcome exists**: `\|ACF1\|` computed **only from windows that end
  strictly before each series' decision point** (`border1_test`), with a printed leakage check —
  **ALL PASS 20/20**; pre-cutoff spread 0.0470 (META) to 0.1257 (WMT). The contemporaneous
  test-window analogue differs materially for several assets and is contrast-only.
- **Analysis pipeline validated**: the interaction collector is a thin driver around the *frozen*
  stratification script and reproduced the recorded values exactly (GSPC −0.01205, BTCUSD +0.01502,
  ETHUSD −0.00943); the final analysis applies the frozen operational criteria and exits 0
  (replicated) or 1 (failed → `\|ACF1\|` closes permanently as the structural bridge).
- **Execution is delegated**: the peer machine (Lenovo 83JM, CPU-only, no GPU, no WSL) started the
  **120-run panel** at 13:36 (20 assets × 2 arms × 3 seeds), two lanes, offline-capable, idempotent,
  with stall detection by process-tree CPU time and automatic manifest pushes every 40 runs or 6 h.
  **Progress 0/120; ETA 60–120 h.** Receipt + artifacts arrive as per-seed batches.
- **Role split to preserve independence**: peer executes and returns raw artefacts
  (`metrics/pred/true` + command line per run, no checkpoints); this host computes the predictor and
  runs the analysis; the peer then independently recomputes the per-asset interactions from its own
  artefacts, blind to the analysis, and reports differences rather than fixing them.

## 5. Hard constraints (any proposal must respect these)

No changes to frozen thresholds, definitions, seeds, splits, metrics or capacity settings. No
asset/seed re-selection after seeing results. Raw results retained. **F1 must not re-open**: Gate A,
`NS_BENCHMARK_ELIGIBLE`, any structural feature as an asset-selection rule, routing/gating, or the
dormant NS-operator runner. Negative evidence is reported as prominently as positive evidence.

## 6. The decision requested

Given §2–§4, **what should this project do next?** Candidate options (not exhaustive, and "none of
these" is a legitimate answer):

- **A. Wait for C1 and nothing else.** The only licensed analysis is C1's primary; everything else is
  either closed or contingent. Resource note: this host is idle, the peer is busy ~60–120 h.
- **B. Pre-commit the interpretation of both C1 branches** now (a replicate branch that upgrades only
  *portability* and still forbids mechanism/selection claims; a fail branch that closes the
  structural bridge permanently and states what remains), so the reading cannot drift after the data
  lands.
- **C. Add a third-party recomputation** of C1's headline number (e.g. an independent cloud agent
  recomputing ρ from the committed predictor and interaction artifacts) to strengthen verification
  beyond executor/analyst separation.
- **D. Re-plan the operator question** for the case where C1 replicates: which ordinary operator
  families would be worth testing under capacity control, and what would make a *structured*
  (NS-inspired) operator worth a benchmark — given that the external assessment judged its usable
  content narrow and largely reproducible by ordinary convolution/SSM.
- **E. Retirement plan**: if C1 fails, what does the project keep, and how is the NS frame archived
  without implying it was tested and refuted?

**Please return:** the chosen course, the reasoning, the **next two or three concrete actions** with
their owner (this host / the peer / the operator), the **failure criterion** for each, and anything in
this report you think is wrong or overstated. Explicitly state anything you would *not* do and why.
