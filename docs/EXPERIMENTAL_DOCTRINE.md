# Experimental doctrine: gates for computational research

**Status:** proposed; not yet adopted.
**Date:** 2026-09-28.
**Scope:** how a protocol in this repository is built, gated and reported.
**Relationship to frozen documents:** this document governs the *construction*
of future protocols. It does not retroactively bind `phase1-v1.1-2026-09-19`,
and it does not convert any past deviation into a compliant one. Where it would
have caught something Phase 1 did, the remedy is a v1.2 amendment signed before
the affected stage runs — not an appeal to this text.

## 0. Why this exists

The repository already has strong *epistemic* hygiene: immutable receipts,
content hashes, attempt lineage, preregistered estimands. What it lacks is a
*process* layer that would notice when the thing being measured is not the thing
that was named. The incidents below all passed every existing check.

| Incident | Passed every existing check because | Caught by |
|---|---|---|
| I1 `revin-TimesNet` is **15.96×** its reference configuration (75,010,401 params vs 4,700,225; 99.95% of them in the Inception kernels) | nothing compared the configuration to its reference implementation | L1.2–L1.5 |
| I2 A05 recorded `status: resource_blocked` while its own `termination` field read `manual controlled interrupt during backward pass` | no check compared a status field against a termination field | L2.2–L2.3 |
| I3 `PACKAGE_ROOT` was a single path; parking CPU packages outside it made the runner see an **empty** root and select all 15 fits as fresh attempt-1 | it failed silently — no error, no conflict, just a different selection | L2.5 |
| I4 The C1 implementation silently dropped 96 windows via `nanmedian` where `diff(log(Close))` was undefined | the dropped windows were never counted, so the N looked correct | L0.3, L0.5, L0.7 |
| I5 Five FX feeds carry OHLC-envelope violations at 1.1–6.4% of rows, uniformly across train/val/test | declared qualitatively in prereg §2 with no count, magnitude or per-split incidence | L0.4, L0.6 |
| I6 Cross-platform newline conversion broke every frozen hash at once | no clause declared a line-ending policy for hash-compared artifacts | L1.7 |

The common shape: **a number was correct in itself and wrong in what it was
attached to.** The gates below exist to make that specific failure loud.

## 1. Three principles

- **P1 — One number, one provenance.** Every number that appears in a report
  resolves to an artifact hash and the configuration that produced it. A number
  whose provenance is a later reconstruction is labelled as such.
- **P2 — Assert before execute.** Every gate is a machine-checkable assertion
  evaluated *before* the expensive step it guards, not a review conducted after.
  A gate that can only be run by reading output is not a gate.
- **P3 — Every deviation produces an assertion.** A deviation record that ends
  in a disposition and no new check has not finished. The disposition fixes this
  instance; the assertion is what stops the next one.

## 2. Layers

Each layer has an entry condition, assertions, the statuses it may assign, and
an exit condition. A layer may not be entered until the previous layer's exit
condition holds. Nothing in L2–L5 may be used to revise an L0 or L1 verdict.

### L0 — Input eligibility

Establishes that each asset is a well-formed instance of the declared task.
Runs before any model, and its output is a per-asset status table.

- **L0.1** Every asset is identified by a content hash, verified at consumption
  time and not only at registration.
- **L0.2** Every asset declares its **time grid** (trading calendar vs calendar
  day) and the wall-clock span that `seq_len` and each horizon denote on that
  grid. Assets are pooled or paired only when their grids are declared
  comparable; otherwise results are reported per grid.
- **L0.3** The declared target is well-defined across the asset's observed range
  **in every split**. A target undefined on any row of a split is a finding, not
  a filter.
- **L0.4** Input-channel defects and target-channel defects are separated and
  reported separately. A defect confined to input channels is input noise; a
  defect touching the target is a validity question. These do not carry the same
  consequence and must not share a status.
- **L0.5** No observation is removed, offset, clamped, filled, or dropped for
  being non-finite without a **pre-declared rule** naming the transform, the
  affected row set, and the sensitivity analysis that will accompany it. Silent
  removal through a NaN-skipping reducer is removal.
- **L0.6** Every defect is **quantified**: affected row count, magnitude
  distribution, and per-split incidence. A qualitative declaration is not
  sufficient for a confirmatory cohort.
- **L0.7** Defect handling is declared **before outcomes are visible**. A defect
  first noticed after outcomes exist may be reported and bounded by sensitivity
  analysis; it may not be handled by a newly written rule.

**Statuses:** `eligible` · `inapplicable` · `requires-resolution` ·
`excluded-by-protocol` · `protocol-deviation`.
**Exit:** every asset in the declared cohort carries one status and its evidence.

### L1 — Implementation fidelity

Establishes that each named model **is** the thing its name refers to. Runs
before any number from that model is used for planning or comparison.

- **L1.1** Each model names its reference implementation as repository, file and
  commit, plus the exact reference configuration.
- **L1.2** A line-by-line hyperparameter comparison against the reference is
  recorded, with every departure and its stated reason.
- **L1.3** A departure is admissible only with a **scale check** on the values
  that set capacity: `d_ff/d_model`, `d_model/n_heads`, and parameter count
  against the reference configuration.
- **L1.4** A model whose capacity differs from its reference by more than the
  declared factor is **not that baseline**, whatever its filename says. It may
  run as a declared variant, reported under a different name.
  *Threshold: **TBD**; 4× is proposed, as it admits the conventional FFN
  expansion while rejecting I1 (15.96×) and the head-dimension departure
  (64 → 4).*
- **L1.5** A hyperparameter is **not shared across architectures when it does not
  denote the same quantity in them.** Sharing a name is not sharing a meaning.
  An equal-capacity-budget grid is admissible for models where the parameters
  play the same role, and inadmissible where they do not.
- **L1.6** Determinism settings and any unsupported operations they disable are
  recorded.
- **L1.7** Any artifact whose hash is compared across platforms has a declared
  line-ending policy.

**Statuses:** `reference-matched` · `declared-variant` · `unverified`.
**Exit:** no model enters L2 or above at `unverified`.

### L2 — Calibration

Establishes feasibility and cost. **Produces no scientific claim.**

- **L2.1** Calibration measures cost and feasibility only. Its losses are not
  compared, ranked or published as evidence, and every artifact it emits says so
  in its own metadata.
- **L2.2** A resource verdict (`resource_blocked`, `timed_out`) must derive from
  a threshold **validated on the same device class**. An unvalidated threshold
  produces a finding about the threshold, not about the model.
- **L2.3** A `status` field and a `termination` field must not contradict each
  other. Where they do, the contradiction invalidates the *status*, and the
  termination record stands as the account of what happened.
- **L2.4** Attempt lineage: each logical run has exactly one validated successful
  attempt. Zero is incomplete; more than one is a conflict and fails stop.
- **L2.5** **The attempt visibility domain is closed.** Every reader of attempt
  state resolves the same set of roots. A reader that globs a subset is a silent
  failure generator and is itself a defect.
- **L2.6** No resource plan may rest on a configuration that has not passed L1.
- **L2.7** A device change inside a stage is a **protocol event**, not an
  operational choice, and requires a prior amendment however small its scope.

**Statuses:** `calibration_pass` · `resource_blocked` · `failed` · `timed_out` ·
`artifact_invalid` · `infrastructure_interruption`.
**Exit:** every fit carries a status whose supporting fields do not contradict it.

### L3 — Screen

Establishes runtime and gross failure across the declared cohort.

- **L3.1** Evaluation keys are generated **before** models run; every compared
  model covers the same keys, including incomplete test batches.
- **L3.2** Screen does not select assets, change the primary model pair, or
  determine which failures to hide.
- **L3.3** A model family that fails or is blocked at screen is recorded with its
  reason and is not silently dropped from later stages.

**Exit:** a coverage table showing every declared key covered by every compared
model, or an explicit statement of which keys are not.

### L4 — Confirmation

- **L4.1** The estimand, its strata and its pooling rule are declared before
  outcomes.
- **L4.2** Only pre-declared pairs are compared.
- **L4.3** Every dynamic transform — scaling, imputation, feature computation,
  selection, tuning — is fit on the applicable training prefix or inner
  validation loop only, and the fit domain is recorded per artifact.
- **L4.4** An active confirmation protocol is not modified. Approved changes take
  a **new protocol ID** and require independent confirmation before any
  confirmatory claim.

### L5 — Temporal robustness

- **L5.1** Rolling splits use explicit, end-exclusive date boundaries.
- **L5.2** A fixed-ratio split is never relabelled as rolling-origin evaluation.
- **L5.3** Each split may borrow only the preceding `seq_len` rows as input
  context; scaling is fit on training rows only.
- **L5.4** Sensitivity analyses declared before outcomes are reported alongside
  the primary result; those declared after are labelled exploratory and carry no
  confirmatory weight.

## 3. Deviation, amendment and reporting

- **X1** Every deviation produces three things: a record, a root cause, and **an
  assertion added to this doctrine or to the affected protocol's gates**. A
  deviation that produces no assertion has not been closed.
- **X2** A violation is recorded as a violation. It is not relabelled as a
  technicality, and its motive does not make it compliant. Splitting a rule into
  "letter" and "spirit" and claiming only the letter was touched is relabelling.
- **X3** A post-hoc record does not acquire amendment authority by being written
  down. Authority comes from being written before the outcome, not from being
  written carefully.
- **X4** Motive, consequence and compliance are three separate questions. A
  favourable answer to one does not answer the others.
- **X5** Unsupported numeric thresholds are marked `TBD` and named as such in any
  gate table, together with whether a research-question, power, precision or
  resource analysis is needed to set them.

## 4. Gate table format

Every gate evaluation returns a table of:

| check | input | status | evidence | next permitted action |
|---|---|---|---|---|

A row whose evidence is a narrative rather than an artifact hash is not a pass.

## 5. Incident index

Clauses exist because of specific events, not in the abstract. The mapping is
maintained so that a clause whose incident has been structurally eliminated can
be retired, and so that a clause cannot be weakened without confronting what it
was written for.

| Clause | Incident |
|---|---|
| L0.3, L0.5, L0.7 | I4 — silent `nanmedian` removal of 96 undefined-log windows in C1 |
| L0.4, L0.6 | I5 — five FX feeds, violations unquantified in prereg §2 |
| L0.2 | BTCUSD 3,653 calendar-day rows vs equities ~2,514 trading-day rows |
| L1.2–L1.5 | I1 — `revin-TimesNet` at 15.96× its reference |
| L1.7 | I6 — cross-platform newline conversion |
| L2.2–L2.3 | I2 — A05 status/termination contradiction |
| L2.5 | I3 — single-rooted `PACKAGE_ROOT` |
| X2 | the deviation record's letter-vs-spirit framing |
