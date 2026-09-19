# Reproduction guide / 复现指南

Run every command from the repository root. Research-specific code and retained
outputs live here; the core training harness remains in `run.py`, `exp/`,
`models/`, `layers/` and `data_provider/`.

## Layout

```text
reproduction/
  analysis/       deterministic audits and result recomputation
  batches/        bounded experiment launchers
  data/           acquisition and conversion helpers
  results/        tracked small tables, JSON/TXT summaries and registries
  c1_handoff/     C1 predictions/targets, commands, manifests and hash inventory
```

## Environment

- Recommended: Python 3.11 and torch 2.5.1.
- Install `requirements/core.txt` after a machine-appropriate PyTorch build.
- CPU runs require `--no_use_gpu`.
- On Windows, set `PYTHONIOENCODING=utf-8` when replaying scripts that print
  Chinese or mathematical symbols.
- C1 execution provenance records Python 3.11.9 / torch 2.5.1+cpu. Some
  receiving-side tabular analyses used an existing Python 3.13 environment;
  the frozen scripts and input hashes anchor the comparison.

## Core checks

```bash
# 61-file schema, chronology, hash and OHLC audit
python reproduction/analysis/dataset_audit.py

# Recompute F1 summaries from the retained 792-row table
python reproduction/analysis/f1_analysis.py

# Verify and rebuild the result-free C1 Stage-1 handoff manifest
python reproduction/analysis/build_c1_blind_manifest.py

# Validate the frozen Phase 1 grid without starting training
python reproduction/analysis/build_phase1_manifest.py
```

The canonical single-model training command is in the root README. Analysis
scripts no longer write to the former sibling `05_research_intelligence`
directory; all active outputs stay under `reproduction/results/`.

## C1 evidence package

`c1_handoff/` contains the complete 20-asset × 2-arm × 3-seed panel:

- 120 run directories;
- 120 `pred.npy` and 120 `true.npy` files;
- commands and log tails;
- executor and receiver manifests;
- frozen analysis and predictor code;
- per-file SHA-256 inventories;
- `BLIND_STAGE1_MANIFEST.csv`, which intentionally excludes analyst results.

The first handoff message mistakenly supplied the SHA-256 of the pre-commit
Windows working-tree manifest. Git line-ending normalization changed the stored
blob. The correct Git-object hash was recomputed and the discrepancy was logged
before the independent reviewer opened the result inputs. This operational
mistake is part of the audit trail, not hidden metadata.

## Data caveats

See [`../dataset/README.md`](../dataset/README.md). In particular, WTI's
non-positive April 2020 prices make log-return features undefined locally, and
five FX feeds contain small OHLC envelope inconsistencies. Scripts must disclose
their handling; they must not mutate source rows in place.

## Output discipline

- Never overwrite an earlier experiment family; use explicit suffixes.
- Keep prediction/target arrays, configuration, logs and hashes for every
  headline result.
- A summary table without its raw inputs is incomplete.
- Test data is evaluated only after validation-selected training is complete.
- Do not add an asset, seed, feature or threshold to rescue a failed frozen
  result.

## Phase 1 modern-baseline programme

The frozen protocol is [`../docs/PHASE1_PREREGISTRATION.md`](../docs/PHASE1_PREREGISTRATION.md),
with machine-readable settings in `configs/phase1_modern_baselines.json`.
Generated manifests live in `results/phase1/`. The manifest builder performs
data-hash and model-availability checks and never launches training. Stage D is
deliberately marked blocked until explicit date-boundary rolling splits exist.
