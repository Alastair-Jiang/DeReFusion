# Reports index

Entry point for the research line: [`../RESEARCH-LINE.md`](../RESEARCH-LINE.md).
All documents below are part of the audit trail; where a document states a claim, the raw numbers
it relies on are in `reproduction/results/`.

## Evidence closure (audit → gate)

| File | What it is |
|---|---|
| `evidence_closure/00_repo_audit.md` | branch/HEAD/dirty state, directory map, reproducibility-gap register |
| `evidence_closure/01_experiment_inventory.md` | experiments E1–E8: scripts, protocol, seeds, outputs, status; declared coverage holes |
| `evidence_closure/02_experiment_integrity.md` | integrity matrix: same-protocol / raw output / seeds / leakage / post-hoc selection |
| `evidence_closure/03_asset_summary.md` | per-asset table (N=10): interaction, CI, capacity sensitivity, structural features, LOO |
| `evidence_closure/04_structural_association.md` | Spearman + LOO over 8 pre-registered features; GSPC seed-merge sensitivity |
| `evidence_closure/05_capacity_sensitivity.md` | widths 23/64/128 and the three checks; why "representation bottleneck" is not claimed |
| `evidence_closure/06_final_diagnosis.md` | Q1–Q5 with evidence/interpretation/confidence/uncertainty + the six-condition PATH gate |
| `evidence_closure/07_evidence_matrix.md` | R1–R9 status matrix (Supported / Partially / Directional only / Not supported) |
| `evidence_closure/08_evidence_chain.md` | the chain, support per step, and the arrows deliberately *not* drawn |
| `evidence_closure/09_next_stage_gate.md` | `NS_BENCHMARK_ELIGIBLE = CONDITIONAL` + the conditions to upgrade |

## Structural validation (current phase)

| File | What it is |
|---|---|
| `evidence_closure/10_structural_validation_blocked.md` | the acquisition blocker as first encountered + the first robustness pass |
| `evidence_closure/11_structural_validation_preregistration.md` | **locked before any run**: new assets, selection rule, expected directions |
| `evidence_closure/12a_gate_a_decision_rule_addendum.md` | **frozen verdict rule** (incl. the accuracy-corrected label for the ≥3/4 rule) |
| `evidence_closure/12b_reviewer_response_and_corrections.md` | adopted reviewer corrections: labels, `CONDITIONAL` cap, contemporaneous-not-leakage wording, capacity wording, multiplicity |
| `evidence_closure/13_external_review.md` | external review, round 1 (archived verbatim) |
| `evidence_closure/13b_external_review_round2.md` | external review, round 2 (archived verbatim) |
| `evidence_closure/14_*` | **result + Gate A verdict** (written when the framework runs complete) |
| `evidence_closure/15_data_acquisition_diagnosis.md` | network diagnosis: why Yahoo is unreachable here, and the source policy for the new cohort |

## Reviewer / handoff material

| File | What it is |
|---|---|
| `REVIEW_REQUEST.md` | paste-ready external review request (project, evidence, the crux question, the asks) |
| `CHATGPT_BRIEF.md` | self-contained briefing for an outside planner |
| `ns_hypothesis_charter.md` | thinking-only charter for the NS frame: bridge requirements, prohibitions, open questions |
| `ns_related_work_map.md` | what already exists (neural ODEs, FNO/DeepONet, SSMs, invariant nets, finance precedents); **citations unverified** |

## Reading order

1. `../RESEARCH-LINE.md` — the whole picture in one page.
2. `evidence_closure/07_evidence_matrix.md` + `08_evidence_chain.md` — what is supported and what is not.
3. `evidence_closure/11_*` → `12a` → `12b` — how the current verdict is being reached, and under which frozen rules.
4. `evidence_closure/14_*` — the verdict (when written).
