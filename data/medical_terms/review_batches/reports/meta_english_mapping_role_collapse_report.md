# Meta English Mapping Role Collapse Report

Generated: 2026-05-19

Scope: `data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl`.

This stage collapses duplicated Chinese terms before English preferred-label confirmation. It does not confirm English mappings and does not modify Meta runtime, shared core, Bioinformatics runtime, search, or PDF extraction.

## Collapse Summary

- Raw rows: 300
- Unique normalized Chinese terms: 156
- Duplicated terms collapsed: 144
- Observed candidate type patterns:
  - `["disease", "outcome"]`: 144 unique terms
  - `["disease"]`: 12 unique terms

## Output Buckets

| output file | rows | policy |
| --- | ---: | --- |
| `meta_english_mapping_disease_population_candidates.jsonl` | 0 | Disease/population candidates eligible for Meta-specific or shared-promotion discussion after English mapping confirmation. |
| `meta_english_mapping_event_outcome_candidates.jsonl` | 15 | Event, complication, injury, poisoning, bleeding, or drug-related outcome candidates. Default Meta-specific and context guarded. |
| `meta_english_mapping_condition_candidate_only.jsonl` | 121 | Long-tail condition, diagnosis, symptom, sign, or clinical-feature candidates. Candidate-only; no seed runtime concept. Includes the 2 resolved manual-review terms. |
| `meta_english_mapping_qualified_term_candidates.jsonl` | 9 | Qualified terms. Diabetic nephropathy staging collapses to base concept plus diabetes type/stage qualifier. |
| `meta_english_mapping_tcm_future_scope_candidates.jsonl` | 11 | TCM syndrome/pattern or Chinese-specific future-scope terms. |
| `meta_english_mapping_still_require_manual_review.jsonl` | 0 | Closed manual-review queue for this pass. |
| `meta_english_mapping_manual_decisions.jsonl` | 2 | Final manual decisions for the closed English-mapping queue. |

## Guardrails

- Every collapsed row includes `observed_candidate_types`.
- Every collapsed row has `runtime_promotion_allowed=false`.
- Every collapsed row has `shared_core_write_allowed=false`.
- Disease/outcome duplicated rows receive a single `primary_role` before later English mapping review.
- No row is promoted to Meta runtime or shared core in this stage.

## Diabetic Nephropathy Staging Rule

The following terms are not independent runtime concepts:

- `1型糖尿病肾病II期`
- `1型糖尿病肾病III期`
- `1型糖尿病肾病IV期`
- `2型糖尿病肾病II期`
- `2型糖尿病肾病III期`
- `2型糖尿病肾病IV期`
- `糖尿病肾病II期`
- `糖尿病肾病III期`
- `糖尿病肾病IV期`

They are represented as `base_concept=diabetic nephropathy` plus `diabetes_type` and `stage` qualifiers.

## Manual Review Closure

`meta_english_mapping_still_require_manual_review.jsonl` is now closed for this review pass and contains 0 rows.

Final decisions are recorded in `meta_english_mapping_manual_decisions.jsonl`:

- `外阴皮肤APUD癌`: condition_candidate_only; manual_mapping_required; no automatic English mapping; not runtime.
- `家族性高脂蛋白血症IV型`: condition_candidate_only; candidate mappings are `hyperlipoproteinemia type IV`, `familial type IV hyperlipoproteinemia`, and `familial hypertriglyceridemia`; not current seed runtime.
