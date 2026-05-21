# Meta Priority Review Role Collapse Report

Generated: 2026-05-19

Scope: `data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl`.

This stage collapses duplicated priority candidates before any seed-expansion decision. It does not modify Meta runtime, shared core, Bioinformatics runtime, English search, or PDF extraction.

## Collapse Summary

- Raw rows: 300
- Unique normalized Chinese terms: 161
- Duplicated terms collapsed: 139
- Seed expansion candidates: 0
- Still manual review: 0
- Observed candidate type patterns:
  - `["disease", "outcome"]`: 139 unique terms
  - `["disease"]`: 14 unique terms
  - `["intervention"]`: 2 unique terms
  - `["research_intent"]`: 2 unique terms
  - `["risk_factor"]`: 1 unique term
  - `["exposure"]`: 1 unique term
  - `["study_design"]`: 1 unique term
  - `["outcome"]`: 1 unique term

## Output Buckets

| output file | rows | policy |
| --- | ---: | --- |
| `meta_priority_seed_expansion_candidates.jsonl` | 0 | Empty by design; no Top 300 priority item is approved for seed expansion in this pass. |
| `meta_priority_existing_runtime_seed_terms.jsonl` | 11 | Existing Meta runtime seed review items; do not duplicate as seed expansion. |
| `meta_priority_event_outcome_candidates.jsonl` | 14 | Event, complication, bleeding, poisoning, injury, or drug-related outcome candidates. |
| `meta_priority_symptom_feature_candidates.jsonl` | 19 | Symptom/sign candidates; no direct runtime promotion. |
| `meta_priority_clinical_feature_candidates.jsonl` | 25 | Clinical feature or phenotype candidates; candidate-only. |
| `meta_priority_functional_impairment_candidates.jsonl` | 23 | Functional impairment outcome-layer candidates; candidate-only. |
| `meta_priority_condition_candidate_only.jsonl` | 49 | Long-tail condition/diagnosis candidates and resolved English-mapping manual decisions. |
| `meta_priority_qualified_term_candidates.jsonl` | 9 | Qualified diabetic nephropathy stage terms; not independent runtime concepts. |
| `meta_priority_tcm_future_scope_candidates.jsonl` | 11 | TCM or Chinese-specific future-scope terms. |
| `meta_priority_still_require_manual_review.jsonl` | 0 | Empty by design; all priority unique terms are covered by existing review-batch rules. |

## Guardrails

- Every collapsed row includes `observed_candidate_types`.
- Every collapsed row has `runtime_promotion_allowed=false`.
- Every collapsed row has `seed_expansion_allowed=false`.
- Every collapsed row has `shared_core_write_allowed=false`.
- No row is promoted to Meta runtime or shared core in this stage.
- The 11 first-pass Meta runtime seed terms are represented only as already-reviewed items, not as new seed-expansion candidates.

## Decision

`meta_priority_review_batch_top_300.jsonl` should continue through rule-based review buckets. It is not ready to be consumed as a seed expansion batch.
