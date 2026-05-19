# Meta Candidate Optimization Report

Generated: 2026-05-18

- raw_candidates_total: 88629
- normalized_candidates_total: 47357
- review_queue_total: 47362
- auto_reject_total: 35

## Rules

High-value batches prioritize mapped disease, exposure, intervention, outcome, effect measure, study design, and research intent terms, then short stable phrases and multi-source terms.

Conflict batches no longer treat every empty-mapping disease/symptom overlap as a high-priority manual review item. Empty `conflict_types=["disease","symptom"]` rows are bulk-routed into symptom/clinical-feature, TCM future-scope, event/adverse-outcome, condition candidate-only, or still-manual-review buckets.

Truly high-risk conflict terms remain in manual review when the term is short or semantically overloaded across disease, phenotype, exposure, intervention, or shared-core meanings.

Disambiguation and English-mapping batches prioritize terms likely to become runtime candidates after human review.

Disambiguation outcome candidates must be layered before any runtime consideration. `meta_disambiguation_top_200.jsonl` is now treated as an outcome-layering review queue, not as a Meta outcome runtime input.

English-mapping candidates must be role-collapsed by `normalized_zh_term` before English preferred-label confirmation. Duplicated disease/outcome rows are review artifacts, not multiple runtime concepts.

Auto-reject candidates include single-character non-abbreviations, generic medical words, colloquial terms, long sentence-like strings, Chinese PDF section terms, and out-of-scope TCM terms.

## Top Batch Files

- data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl
- data/medical_terms/review_batches/meta/meta_mapping_conflicts_top_200.jsonl
- data/medical_terms/review_batches/meta/meta_symptom_clinical_feature_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_tcm_future_scope_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_event_adverse_outcome_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_condition_candidate_only.jsonl
- data/medical_terms/review_batches/meta/meta_conflicts_still_require_manual_review.jsonl
- data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_symptom_feature_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_clinical_feature_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_condition_candidate_only.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_adverse_event_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_functional_impairment_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_tcm_future_scope_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_outcome_still_requires_manual_review.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_disease_population_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_event_outcome_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_condition_candidate_only.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_qualified_term_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_tcm_future_scope_candidates.jsonl
- data/medical_terms/review_batches/meta/meta_english_mapping_still_require_manual_review.jsonl

## Conflict Batch Rule Refinement

The original `meta_mapping_conflicts_top_200.jsonl` contains 200 disease/symptom conflicts, all with empty `candidate_mappings`. These are not reliable enough to keep as a uniformly high-priority manual queue.

- `meta_symptom_clinical_feature_candidates.jsonl`: 101 rows, downgraded symptom/sign/clinical-feature candidates.
- `meta_tcm_future_scope_candidates.jsonl`: 36 rows, likely TCM syndrome or pattern terms deferred out of current Meta runtime scope.
- `meta_event_adverse_outcome_candidates.jsonl`: 16 rows, event, adverse outcome, injury, bleeding, or acute episode candidates.
- `meta_condition_candidate_only.jsonl`: 41 rows, likely condition/disease candidates that need English/PICO evidence before any runtime use.
- `meta_conflicts_still_require_manual_review.jsonl`: 6 rows, still high-risk semantically overloaded terms: 疱疹, 结石, 肥胖, 脚气, 镇静, 风团.

## Disambiguation Outcome Layering

The original `meta_disambiguation_top_200.jsonl` contains 200 rows with `possible_roles=["outcome"]`. These rows are not automatically approved Meta outcome runtime terms. They are layered first:

- `meta_outcome_symptom_feature_candidates.jsonl`: 34 rows.
- `meta_outcome_clinical_feature_candidates.jsonl`: 42 rows.
- `meta_outcome_condition_candidate_only.jsonl`: 62 rows.
- `meta_outcome_adverse_event_candidates.jsonl`: 21 rows.
- `meta_outcome_functional_impairment_candidates.jsonl`: 27 rows.
- `meta_outcome_tcm_future_scope_candidates.jsonl`: 13 rows.
- `meta_outcome_still_requires_manual_review.jsonl`: 1 row, `结节`.

All layered rows are review-batch derivatives with `runtime_promotion_allowed=false`, `query_expansion_allowed=false`, and `requires_context_rule=true`.

## English Mapping Role Collapse

The original `meta_english_mapping_top_300.jsonl` contains 300 rows but only 156 unique normalized Chinese terms. The role-collapse stage groups duplicate disease/outcome candidates before any English preferred-label confirmation.

- `meta_english_mapping_disease_population_candidates.jsonl`: 0 rows.
- `meta_english_mapping_event_outcome_candidates.jsonl`: 15 rows.
- `meta_english_mapping_condition_candidate_only.jsonl`: 119 rows.
- `meta_english_mapping_qualified_term_candidates.jsonl`: 9 rows.
- `meta_english_mapping_tcm_future_scope_candidates.jsonl`: 11 rows.
- `meta_english_mapping_still_require_manual_review.jsonl`: 2 rows, `外阴皮肤APUD癌` and `家族性高脂蛋白血症IV型`.

Diabetic nephropathy staging terms are represented as `base_concept=diabetic nephropathy` plus diabetes type and stage qualifiers; they are not independent runtime concepts.

## Remaining Manual Review Reason

Most external corpus rows still lack reliable English preferred labels, MeSH/Emtree candidates, and unambiguous PICO/PECO roles.
