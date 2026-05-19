# Medical Terms Vocabulary Audit Closure Report

Generated: 2026-05-19

Scope: closure report for the medical terms vocabulary audit and review-batch triage work. This report is documentation only. It does not modify shared core, Meta runtime, Bioinformatics runtime, business logic, search, PDF extraction, packaging, or desktop entry points.

## Commit Summary

| commit | stage |
| --- | --- |
| `f294c85` | Added vocabulary audit and Meta candidate pipeline. |
| `5612105` | Prepared vocabulary review batches. |
| `61f02a6` | Completed Bioinformatics GEO core terms. |
| `5287f00` | Resolved Bioinformatics GTEx tissue mappings. |
| `e55867b` | Refined Bioinformatics GEO core mappings. |
| `1f1608b` | Corrected Meta runtime seed review decisions. |
| `f7ec15a` | Refined Meta mapping conflict batch rules. |
| `ae1b691` | Recorded Meta conflict manual decisions. |
| `9bea8a6` | Layered Meta disambiguation outcome candidates. |
| `990ed4a` | Recorded Meta disambiguation manual decision. |
| `2480324` | Collapsed Meta English mapping role duplicates. |
| `8b16e17` | Recorded Meta English mapping manual decisions. |
| `15a87bb` | Collapsed Meta priority review role duplicates. |

## Stage Products

| stage | main products |
| --- | --- |
| Vocabulary audit/bootstrap | `data/medical_terms/review_batches/*`, `data/medical_terms/review_batches/reports/vocabulary_review_batches_for_discussion.md`. |
| Bioinformatics GEO core | `bioinformatics_species_terms.json`, `bioinformatics_grouping_terms.json`, `bioinformatics_data_type_terms.json`, `bioinformatics_dataset_registry_terms.json`, `bioinformatics_stop_terms.json`, `geo_core_terms_coverage_audit.json`. |
| Bioinformatics GTEx | `bioinformatics_tissue_terms.json`, `gtex_terms_coverage_audit.json`. |
| Meta runtime seed review | `meta_approved_runtime_review_batch.jsonl`, `meta_shared_promotion_review_batch.jsonl`, `meta_runtime_seed_correction_report.md`. |
| Meta conflict triage | `meta_symptom_clinical_feature_candidates.jsonl`, `meta_tcm_future_scope_candidates.jsonl`, `meta_event_adverse_outcome_candidates.jsonl`, `meta_condition_candidate_only.jsonl`, `meta_conflict_manual_decisions.jsonl`, `meta_conflict_manual_decision_report.md`. |
| Meta disambiguation triage | `meta_outcome_*_candidates.jsonl`, `meta_disambiguation_manual_decisions.jsonl`, `meta_disambiguation_outcome_layering_report.md`, `meta_disambiguation_manual_decision_report.md`. |
| Meta English mapping triage | `meta_english_mapping_*_candidates.jsonl`, `meta_english_mapping_manual_decisions.jsonl`, `meta_english_mapping_role_collapse_report.md`, `meta_english_mapping_manual_decision_report.md`. |
| Meta priority triage | `meta_priority_*_candidates.jsonl`, `meta_priority_existing_runtime_seed_terms.jsonl`, `meta_priority_review_role_collapse_report.md`. |

## Bioinformatics Final State

Bioinformatics audit is closed for the scoped GEO/GTEx/TCGA vocabulary review.

| audit | final status |
| --- | --- |
| GEO core | `total=54`, `complete=46`, `approved_with_note=8`, `missing=0`, `needs_review=0`. |
| GTEx | `total=23`, `complete=18`, `approved_with_subtype_mapping=3`, `complete_with_note=2`, `missing=0`, `needs_review=0`. |
| TCGA | `total=33`, `complete=33`, `missing=0`, `needs_review=0`. |

Bioinformatics-specific fixes were kept in dedicated Bioinformatics vocabulary/audit files. GEO-specific terms remain `shared_core_allowed=false` and `meta_scope_allowed=false`. GTEx broad tissue terms were resolved through subtype mapping rather than broad-term override. TCGA remained complete.

## Meta Candidate Pipeline Final State

The Meta candidate pipeline is now a triage pipeline, not a runtime expansion pipeline.

| batch | final disposition |
| --- | --- |
| Approved runtime seed review | 11 reviewed seed items, with corrected review statuses, query guards, and shared-promotion decisions. |
| Shared promotion review | 4 reviewed decisions; approved disease concepts align to existing shared concepts, obesity is blocked from shared promotion. |
| Mapping conflicts Top 200 | 194 rows bulk-routed, 6 high-risk terms recorded with manual decisions. |
| Disambiguation Top 200 | 199 rows layered into outcome candidate buckets, 1 manual decision recorded for `结节`. |
| English mapping Top 300 | 300 rows collapsed to 156 unique terms; manual queue closed with 2 decisions. |
| Priority review Top 300 | 300 rows collapsed to 161 unique terms; seed expansion candidates are 0. |

The external Chinese corpus remains useful as a candidate source and review signal. It is not reliable enough to automatically expand Meta runtime because it contains duplicate role artifacts, missing English preferred labels, ambiguous PICO roles, TCM/future-scope terms, long-tail condition labels, and outcome/condition boundary ambiguity.

## Seed Expansion Candidates Equals 0

`seed_expansion_candidates=0` means no item from `meta_priority_review_batch_top_300.jsonl` is approved for direct insertion into Meta runtime in this pass.

It does not mean the corpus has no value. It means every priority item either:

- already exists in the reviewed seed list,
- requires qualified-term handling,
- belongs in condition/symptom/clinical-feature/event/functional-impairment candidate pools,
- belongs in TCM future scope,
- or has already been resolved by manual decision as candidate-only.

## Remaining Candidate Pools

Bioinformatics review/audit paths:

- `data/medical_terms/review_batches/bioinformatics/geo_core_missing_review_batch.jsonl`
- `data/medical_terms/review_batches/bioinformatics/gtex_needs_review_batch.jsonl`
- `data/medical_terms/bioinformatics/audits/geo_core_terms_coverage_audit.json`
- `data/medical_terms/bioinformatics/audits/gtex_terms_coverage_audit.json`
- `data/medical_terms/bioinformatics/audits/tcga_terms_coverage_audit.json`

Meta source and candidate pools:

- `data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_existing_runtime_seed_terms.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_event_outcome_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_symptom_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_clinical_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_functional_impairment_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_qualified_term_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_tcm_future_scope_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_seed_expansion_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_priority_still_require_manual_review.jsonl`
- `data/medical_terms/review_batches/meta/meta_mapping_conflicts_top_200.jsonl`
- `data/medical_terms/review_batches/meta/meta_symptom_clinical_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_tcm_future_scope_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_event_adverse_outcome_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_conflicts_still_require_manual_review.jsonl`
- `data/medical_terms/review_batches/meta/meta_conflict_manual_decisions.jsonl`
- `data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_symptom_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_clinical_feature_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_adverse_event_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_functional_impairment_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_tcm_future_scope_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_outcome_still_requires_manual_review.jsonl`
- `data/medical_terms/review_batches/meta/meta_disambiguation_manual_decisions.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_disease_population_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_condition_candidate_only.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_event_outcome_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_qualified_term_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_tcm_future_scope_candidates.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_manual_decisions.jsonl`
- `data/medical_terms/review_batches/meta/meta_english_mapping_still_require_manual_review.jsonl`
- `data/medical_terms/review_batches/meta/meta_evidence_only_candidates_optimized.jsonl`
- `data/medical_terms/review_batches/meta/meta_future_scope_candidates_optimized.jsonl`
- `data/medical_terms/review_batches/meta/meta_auto_reject_candidates.jsonl`

## Boundaries

This closure stage only adds documentation. It does not edit:

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- Meta runtime files
- shared core vocabulary files
- Bioinformatics runtime/business logic
- search, PDF extraction, packaging, or desktop workflow code

The previous scoped Bioinformatics stages updated dedicated files under `data/medical_terms/bioinformatics/` and their audits. The Meta stages updated review-batch derivatives and reports only; they did not promote external-corpus candidates into Meta runtime.

## Recommendation

Next vocabulary expansion should be deliberate, not automatic:

- Build a small human-curated Meta seed list from concrete product needs.
- Confirm each seed against English standard resources such as MeSH, Emtree, ICD/SNOMED where applicable, drug vocabularies, and trial/PICO terminology.
- Add Chinese input mappings separately from runtime concepts, so Chinese queries can map to stable English concepts without letting noisy corpus terms become runtime seeds.
- Keep candidate pools as review queues until a later explicit implementation stage defines English preferred label, synonyms, concept type, PICO role, query expansion behavior, and shared-promotion policy.

## Validation

Closure validation used existing review-batch tests only:

- `git diff --check`
- `python3 -m pytest tests/shared/test_medical_terms_review_batches.py -q`
- `python3 -m pytest tests/shared/test_medical_terms_stage_pipeline.py -q`
