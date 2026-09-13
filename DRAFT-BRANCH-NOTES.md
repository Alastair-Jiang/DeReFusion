# DRAFT BRANCH — NS benchmark runner (not for execution in this research line)

**Branch:** `draft/ns-benchmark-runner` · **Based on:** `main` @ `54bba97` (Gate A = FAIL)
**Added at the operator's explicit request on 2026-09-13 20:07**, who lifted — **for this artefact
only** — the project's standing "no NS module may be implemented" constraint.

## What is on this branch

| Path | Origin | Note |
|---|---|---|
| `reproduction/analysis/run_ns_hypothesis_benchmark.py` (27 KB) | authored in the external Codex clone, commit `80e6c5e` | standalone locked-protocol benchmark runner; SHA-256 verified identical to the source |
| `reproduction/configs/ns_hypothesis_benchmark.example.json` | same | manifest template (status `TEMPLATE_NOT_LOCKED`) |
| `reproduction/batches/run_ns_hypothesis_benchmark.ps1` | same | scheduling entry; requires `-Manifest`, `-Execute` for training |
| `reproduction/README.md` | same | +27 lines describing the runner |
| `20_project_evidence/` | local snapshot from `~/.openclaw/workspace/ns_dossier_raw/20_project_evidence` | **point-in-time copy** of the handoff package (4 top-level reports + `evidence_closure/00–14`, incl. the Gate A result). Duplicates material already on `main` under `reports/`; kept here only as a frozen snapshot. |

Nothing on `main` is modified by this branch. Nothing here is merged, and it should **not** be
merged while its prerequisite is unmet.

## Why it is dormant

1. **Gate A = `FAIL`** (`reports/evidence_closure/14_structural_validation_result.md`). Under the
   frozen rule, `FAIL` closes the structural-bridge direction and downgrades
   `NS_BENCHMARK_ELIGIBLE` from `CONDITIONAL`. The runner's own gate requires
   `eligibility_evidence = C1_REPLICATED`; **C1 does not run under a FAIL**, so that condition is
   unreachable in this line.
2. The runner is therefore **inert by design**: default invocation performs a **read-only preflight**
   (manifest validation) and trains nothing; `--execute` additionally requires
   `status = LOCKED`, `C1_REPLICATED`, a per-asset SHA-256 list that matches the files on disk, an
   exact model list, the frozen protocol block, and a fresh output directory.

## If it is ever run (outside this line, or after a different verdict)

- It must be run **only** from a manifest that names a pre-registered asset list; it refuses
  `status != LOCKED`.
- It must first pass a **leakage audit** (the operator consumes observed history only, but the
  runner has not been line-audited by the operating agent).
- It must be executed in a clone that has the project virtualenv (the authoring clone had none).
- Results must be reported against the frozen metrics, with the four bridges from
  `reports/ns_hypothesis_charter.md` and the decision rules from
  `reports/evidence_closure/18_ns_operator_design_draft.md`.

## Compliance statement (recorded, not hidden)

- The runner contains **no router, adaptive gate, MoE, attention or pressure term** (the only
  occurrences of those words in the file are sentences forbidding them).
- It does not modify any existing experiment definition or code path; it is additive.
- Its presence **does** constitute an implementation of a `temporal NS-inspired nonlinear operator`,
  which the project's standing constraints prohibited during the current phase. The owner lifted
  that constraint for this artefact; the constraint list in `RESEARCH-LINE.md` §7 and
  `PROJECT-BRIEF.md` §7 is **unchanged** and still applies to every other file and to any decision
  to run this code. Amending those lists is an owner decision and has not been made.
