# Research line in this fork — start here

> `README.md` (top level) is the **upstream paper's** readme — leave it as is.
> This file documents the work carried out in **this fork**: what has been done, what the
> current state is, where everything lives, and how to reproduce it.
>
> **Outside reader / planning agent:** start from [`PROJECT-BRIEF.md`](PROJECT-BRIEF.md) — a
> self-contained, **read-only** briefing (evidence ledger, frozen rules, roadmap options, caveats,
> reading map).

---

## 1. What this line is

Two things, stacked:

1. **A reproduction** of *Hsieh & Chen (2026), "DeReFusion", Applied Soft Computing 203:116252* —
   DLinear base branch + LSTM–Transformer residual branch + parameter-free additive fusion +
   RevIN — on independently fetched 2016–2025 daily OHLC data, CPU only, under a frozen protocol
   (70/10/20 chronological split, fixed seeds, paired bootstrap with 4000 resamples).
   The published ordering reproduces, so the framework is a valid testbed.

2. **One organising research question** on top of it:

   > **Does the structural state of the input determine which operator (linear vs nonlinear)
   > is more useful?**

   A "yes" would justify sample-level routing / adaptive gating; a "no" makes operator choice a
   per-asset configuration decision. Two measurement layers are used and must not be conflated:
   the **framework layer** (DeReFusion vs `revin-DLinear`, volatility-stratified) and the
   **capacity-controlled proxy layer** (linear map vs MLP with a matched parameter budget, over
   pre-registered structural states).

## 2. Results so far (numbers)

| Finding | Evidence |
|---|---|
| Reproduction validated | T=24: additive fusion 0.06230 < linear base 0.07007 < gate 0.07191; T=1: linear base wins marginally |
| Volatility is **not** a universal operator-selection criterion | GSPC interaction −0.01205 / −0.02248 (two seeds, supported); ETHUSD −0.00943 (directionally negative, CI touches 0); BTCUSD **+0.01502** (supported, opposite sign) → `INCONSISTENT` |
| Adaptive fusion / gating does not pay | gatev1 0.06767 vs additive 0.06230 (**8.6% worse**); the optimal weight is ≈ constant — no switching headroom |
| Operator preference is capacity-sensitive | hidden 23→64→128: ETHUSD +0.0145 → −0.0281 → −0.0321 (12/36 → **36/36** → 36/36 preferring nonlinear); BTCUSD never nonlinear; GSPC ≈ parity at 128. 25 sign reversals across widths |
| No robust **sample-level** routing | 12 pre-registered structural states × 3 assets × 3 seeds, capacity-matched: GSPC/BTCUSD prefer linear in 12/12 states; ETHUSD's flip is **asset-wide** |
| **Asset-level** heterogeneity **is** supported | capacity-controlled: ETHUSD → nonlinear (36/36), BTCUSD → linear (36/36), GSPC → near parity |
| Candidate structural regularity (N=10, exploratory) | ρ(\|ACF1\|, interaction) = **+0.733** (p=0.016); ρ(realized vol, interaction) = **+0.661** (p=0.038); both LOO-stable; `GSPC_SEED_SENSITIVE = NO` |

**Two honest caveats that must travel with those numbers** (see `reports/evidence_closure/12b`):

- the structural features are computed **on the same test segment** as the outcome → the
  association is **contemporaneous and descriptive**, not an ex-ante selection rule;
- eight features were screened before `|ACF1|`/volatility emerged → the p-values are **not
  multiplicity-clean**.

## 3. Current phase — structural validation (in flight)

External validation of the candidate regularity on **four pre-registered new assets**
(chosen by a fixed rule — 2 lowest + 2 highest `|ACF1|` — before any operator result):

| Group | Asset | \|ACF1\| | Pre-registered expectation |
|---|---|---|---|
| low | BYD | 0.0324 | interaction more negative → nonlinear-favoured |
| low | BOE | 0.0408 | interaction more negative → nonlinear-favoured |
| high | EASTMONEY | 0.1296 | interaction more positive → linear-favoured |
| high | YANGHE | 0.1307 | interaction more positive → linear-favoured |

- **Capacity layer already done:** 1 of 4 matched; **YANGHE (highest `|ACF1|`) reversed with
  per-seed-consistent signs** → an unfavourable signal, recorded unspun.
- **Framework layer:** 8 runs (4 assets × {DeReFusion, revin-DLinear}) → N=14 interaction-level ρ.
- **Gate A** (`PASS` unreachable / `FAIL` / `CONDITIONAL`) is decided by the frozen rule in
  `reports/evidence_closure/12a`, with the corrections and cap in `12b`, and two archived external
  reviews (`13`, `13b`). Verdict + report land in `reports/evidence_closure/14_*`.

## 4. Next step after the verdict

**Not** an NS module. The only defensible next step is an **independent, prospective structural
validation on a same-source cohort** (≈15–20 assets, ≥3 seeds per asset, `|ACF1|` as the single
primary predictor, features computed strictly before the decision point). A temporal
NS-inspired nonlinear operator remains a **downstream hypothesis**, never an assumption.

The executable decision tree is specified in
[`reports/evidence_closure/16_post_gate_experiment_program.md`](reports/evidence_closure/16_post_gate_experiment_program.md):
`FAIL` first triggers an all-remaining-assets capacity-controlled stability panel;
`CONDITIONAL` triggers the independent prospective cohort. Both branches have fixed prerequisites,
resource envelopes and falsification criteria. No branch starts until `14_*` records Gate A.

## 5. Repository map

```
reproduction/
  analysis/     analyze_volatility_regimes.py · structure_routing_experiment.py ·
                structure_routing_capacity_check.py (--assets/--widths overrides) ·
                final_diagnosis.py · asset_dependence_analysis.py ·
                association_robustness_check.py · check_gspc_seed_sensitivity.py ·
                candidate_features.py · sv_gate_a.py · sv_capacity_report.py
  batches/      run_batch_repro*.ps1 · run_asset_sweep.ps1 · run_structural_validation.ps1
  data/         fetch_dataset*.py · fetch_pool_sohu*.py · yahoo_download.py · probes/diagnostics
  results/      volatility_stratification_*.{json,txt} · operator-regime-capacity*.csv ·
                structure_routing_raw.json · candidate_pool_features.csv
reports/
  evidence_closure/00..15   the audit → closure → review → gate trail (see reports/README.md)
  CHATGPT_BRIEF.md · REVIEW_REQUEST.md · ns_hypothesis_charter.md · ns_related_work_map.md
docs/          ROADMAP.md (state of record + pitfalls) · latex/ (stage reports, EN/ZH, PDF)
dataset/       ten 2016–2025 daily OHLC CSVs (Yahoo) committed with git add -f
data/raw/yahoo/  target for the new cohort data (NOTE: /data/ is git-ignored → git add -f)
sweep_runs/    per-run training logs · *_log.txt at top level: batch logs
draft branch   `draft/ns-benchmark-runner` holds a **dormant draft artefact** (an NS benchmark
               runner + a handoff-package snapshot) added at the operator's request and kept off
               `main`; see that branch's `DRAFT-BRANCH-NOTES.md`. It is not eligible to run in this
               line (Gate A = FAIL) and the constraint list in §7 is unchanged.
```

## 6. How to reproduce

```powershell
# environment (Windows, CPU-only runs)
.venv\Scripts\python.exe run.py --task_name long_term_forecast --is_training 1 `
  --model_id GSPC_96_24 --model DeReFusion --data custom --root_path ./dataset/ `
  --data_path GSPC-2016-2025.csv --features MS --target Close --freq b `
  --seq_len 96 --label_len 48 --pred_len 24 --enc_in 4 --dec_in 4 --c_out 1 `
  --d_model 32 --moving_avg 25 --train_epochs 30 --batch_size 32 --learning_rate 0.0001 `
  --patience 5 --lradj cosine --rand_seed 2021 --no_use_gpu
```

Known pitfalls (they cost real time):

- **CPU runs need `--no_use_gpu`.**
- **Batch logs**: PowerShell scripts must stay **ASCII-only** (Chinese in a `.ps1` breaks parsing).
- **Data deps**: `patool`, `huggingface_hub`, `sktime`, `datasets`, `joblib==1.5.3`.
- **Stalled runs**: killing DataLoader worker processes (`spawn_main`) deadlocks the parent
  trainer — detect a stall by **process CPU time**, not by log output. Long batches are therefore
  launched **idempotently** (the scripts skip completed runs) and resumed if the process dies.
- **Network**: the host's system proxy (`127.0.0.1:7897`) has broken TLS forwarding — every HTTPS
  request through it fails. Bypass it explicitly (`ProxyHandler({})` / `curl --noproxy '*'`).
  From this host Yahoo answers 403 and Stooq serves a JS challenge; the market-data source that
  works is **Sohu** (A-shares). See `reports/evidence_closure/15_*`.

## 7. Hard constraints for anyone (human or agent) touching this line

- **No** new adaptive gating, router, MoE, attention, learned routing, pressure term, or NS module;
  no NS inside DeReFusion.
- **No** changes to volatility / structural-feature definitions, thresholds, statistical tests,
  split, horizon, window, seeds or capacity settings.
- **No** re-selecting assets or seeds after seeing results; **no** post-hoc dropping of
  assets/seeds/regimes; raw results are always kept (never summary-only).
- Gate thresholds and the `CONDITIONAL` cap are **frozen** (see `12a`/`12b`).
- Terminology: *NS-inspired / temporal NS-inspired nonlinear operator* only — never
  "markets are fluids" or similar as a factual claim.
- Negative evidence is reported with the same prominence as positive evidence.

## 8. Data

- `dataset/*.csv` — the ten assets used throughout (Yahoo, committed).
- `data/raw/yahoo/` — where the **new cohort** data goes (`data/raw/yahoo/DOWNLOAD_LINKS.md` holds
  ready-to-click download links; `DOWNLOAD_LINKS.md` also lists a Stooq alternative).
- The NS reading dossier (third-party papers + an unpublished manuscript) is deliberately **not**
  in this public repository.
