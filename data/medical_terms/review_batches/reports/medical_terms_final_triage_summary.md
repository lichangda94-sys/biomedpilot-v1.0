# Medical Terms Final Triage Summary

Generated: 2026-05-19

## Decision

Do not automatically expand Meta runtime from the external Chinese vocabulary corpus.

The corpus is retained as candidate evidence and review-batch input. Direct runtime expansion is blocked because the top queues show duplicate role artifacts, missing English mappings, ambiguous disease/outcome roles, candidate-only conditions, TCM future-scope terms, and terms that require qualifiers or context guards.

## Final Triage Counts

Bioinformatics:

- GEO core audit: 54 total, 46 complete, 8 approved-with-note, 0 missing.
- GTEx audit: 23 total, 18 complete, 3 approved-with-subtype-mapping, 2 complete-with-note, 0 needs-review.
- TCGA audit: 33 total, 33 complete.

Meta:

- Approved runtime seed review: 11 rows.
- Shared promotion review: 4 rows.
- Conflict Top 200: routed into 101 symptom/clinical-feature, 36 TCM future-scope, 16 event/adverse-outcome, 41 condition-only, and 6 manual-decision rows.
- Disambiguation Top 200: routed into 34 symptom/sign, 42 clinical-feature, 62 condition-only, 21 adverse-event, 27 functional-impairment, 13 TCM future-scope, and 1 manual-decision row.
- English mapping Top 300: collapsed to 156 unique terms; 0 still-manual rows after 2 manual decisions.
- Priority Top 300: collapsed to 161 unique terms; 0 seed-expansion candidates and 0 still-manual rows.

## Seed Expansion Status

`meta_priority_seed_expansion_candidates.jsonl` intentionally contains 0 rows.

This means the Top 300 priority batch has no direct runtime additions. It does not close future Meta expansion. It only says the current corpus-derived batch must not bypass human seed design, English standard mapping, concept typing, PICO role review, and query-expansion guards.

## Candidate Pools To Keep

Highest-signal candidate pools for later manual review:

- `data/medical_terms/review_batches/meta/meta_priority_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_event_outcome_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_symptom_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_clinical_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_functional_impairment_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_qualified_term_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_event_outcome_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_qualified_term_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_adverse_event_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_functional_impairment_candidates.jsonl`

Decision/audit pools to preserve:

- `data/medical_terms/review_batches/meta/meta_approved_runtime_review_batch.jsonl`
- `data/medical_terms/review_batches/meta/meta_shared_promotion_review_batch.jsonl`
- `data/medical_terms/review_batches/meta/meta_conflict_manual_decisions.jsonl`
- `data/medical_terms/review_batches/meta/meta_disambiguation_manual_decisions.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_manual_decisions.jsonl`
- `data/medical_terms/review_batches/reports/meta_candidate_optimization_report.md`
- `data/medical_terms/review_batches/reports/meta_priority_review_role_collapse_report.md`

## Next Step

Start a new stage with a small human seed list. For each seed, require:

- English preferred label and standard-resource identifiers.
- Chinese preferred input and synonyms.
- Concept type and PICO role.
- Query expansion policy.
- Standalone search policy.
- Shared-core promotion decision.

Only after those fields are reviewed should any item move from candidate pool to Meta runtime.
