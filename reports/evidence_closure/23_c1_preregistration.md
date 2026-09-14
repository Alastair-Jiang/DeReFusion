# 23 · C1 pre-registration skeleton — independent prospective same-source cohort

**Status:** SKELETON. Rules are locked here; **hashes, asset names and the provider are intentionally
left as slots** because the data does not exist yet. This file authorises nothing: C1 may only run
after (a) the cohort is acquired, (b) the slots are filled and a **separate lock commit** is made
*before* any feature or outcome is inspected, and (c) the owner authorises execution.
**Owner instruction:** 2026-09-14 13:06 ("都办了") — draft this skeleton and dispatch the two geng
tasks. Base commit at drafting time: `0a48245`.

**Lineage:** `16` §4 (branch C, experiment C1) with the scope corrections of `19` (shared position
with the external agent) and `22` (adopted F1 framing and task allocation).

---

## 1. What C1 tests — and what it must never be used for

**Tests:** whether the candidate structural association (`|ACF1|` ↔ interaction sign) survives in a
genuinely independent, single-source, **prospective** cohort — i.e. whether it is *portable* rather
than sample-specific.

**Never used for:** re-opening Gate A; restoring `NS_BENCHMARK_ELIGIBLE`; creating an
asset-selection rule; reviving the dormant operator runner; routing or gating. `|ACF1|` stays
sample-specific until this test passes — and even then, only portability of the candidate is
upgraded, never a mechanism claim.

## 2. Data requirements (must all hold before the lock commit)

1. **One provider only.** No composite cohorts — a single source for the whole cohort.
2. **Complete daily OHLC, 2016-01-01 → 2025-12-31**, one row per trading day, per asset.
3. **Identical adjustment policy** across every asset in the cohort (documented; e.g. all raw
   closes, or all adjusted — not mixed).
4. **Provenance declared.** The discovery set came from Yahoo; if this cohort comes from another
   provider or market, that deviation is written next to every result (the reviewer's requirement).
5. **No source substitution after outcomes are seen.** If a provider fails mid-acquisition, the
   cohort is re-locked from scratch with a new commit — assets are never swapped in.

## 3. Universe and exclusion rules (mechanical; locked before inspection)

- **Target size:** 15–20 assets.
- **Universe:** every asset in a **pre-named** candidate list (the list is written at lock time and
  never edited afterwards).
- **No selection by `|ACF1|`, volatility or any other feature.** All eligible assets are included —
  the earlier design's "2 lowest + 2 highest" rule belongs to the *discovery* phase and is **not**
  reused here.
- **Mechanical exclusions only** (thresholds fixed at lock time, before data): history not covering
  the window; missing rows beyond a fixed fraction; non-positive or duplicated prices; duplicated
  dates. Every exclusion is reported by name with its reason.

## 4. Predictor (prospective — this is the point of the exercise)

- **Primary:** `|ACF1|`, computed from returns available **strictly before the decision point** (the
  validation cutoff), using the unchanged estimator (one-day returns, single lag, absolute value;
  window fixed at lock time). Features computed over the test segment are **not** usable here — that
  is exactly the contemporaneous-descriptive limitation recorded in `12b` §2.5.
- **Secondary:** realized volatility over the same pre-cutoff window. Reported separately.
- **The six rejected features** (trend persistence, skewness, kurtosis, jump ratio, sign
  persistence, relative volatility as a *predictor*) are **not rescanned**.
- A **leakage check line must be printed** by the analysis: every predictor value derives from
  indices `< cutoff`; any overlap invalidates the run.

## 5. Outcome (unchanged protocol)

The frozen interaction measure: DeReFusion vs `revin-DLinear`, `T=24`, `seq_len 96`, `label_len 48`,
70/10/20 chronological split, seeds 2021/2022/2023, paired bootstrap 4000 resamples; High = Q4+Q5,
Low = Q1+Q2 of the pre-cutoff-free relative volatility definition already frozen in E4/E5.

## 6. Analysis and decision rules (reused verbatim from the frozen set)

- Spearman ρ(`|ACF1|`, interaction) with an exploratory p-value, plus leave-one-asset-out.
- **Primary analysis runs on the new cohort only**; the old ten / pooled N=14 may be shown **only as
  labelled context**, never as the primary test.
- Reused operational criteria: sign reversal, `|ρ| < 0.30`, `p > 0.10`, LOO range crossing zero,
  single-asset dependence, any integrity finding.
- **Success** = the association replicates prospectively under those criteria.
- **Failure** = `|ACF1|` is closed **permanently** as this project's structural bridge, and the
  result is recorded as such.

## 7. Resource envelope

15–20 assets × 2 framework arms × 3 seeds = **90–120 training runs** ≈ **25–35 h** wall-clock at
2-way parallelism on this host, plus a restart budget (detached batches were killed silently three
times on 2026-09-13). Long campaigns must run under the idempotent self-healing launcher and be
verified by **process CPU time**, not by log output.

## 8. Lock table — slots to be filled at lock time (currently EMPTY on purpose)

| # | Asset | Provider | Rows | First date | Last date | SHA-256 |
|---|---|---|---|---|---|---|
| 1 | *(slot)* | *(slot)* | — | — | — | — |
| … | | | | | | |

**Lock procedure:** fill this table → commit with the message `lock: C1 cohort <provider> <n> assets`
→ record the lock commit hash below → *then* inspect features and outcomes.

- Lock commit: *(to be filled)*
- Provider + adjustment policy: *(to be filled)*
- Cutoff date (decision point): *(to be filled)*
- Exclusion thresholds applied: *(to be filled)*

## 9. Explicit prohibitions

No running before data + lock + owner authorisation; no rule change after outcomes are seen; no
adding or dropping assets; no metric shopping; no reinterpreting a failure as success; no
outsourcing the analysis to a party that has seen the outcome first.
