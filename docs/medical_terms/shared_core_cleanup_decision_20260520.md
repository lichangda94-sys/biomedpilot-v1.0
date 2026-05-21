# Shared Core Cleanup Decision

Date: 2026-05-20

## Scope

This is Stage S5. It records a cleanup decision after S1 inventory, S2 scope schema, S3 Meta scoped mirror, and S4 scope-aware loader routing. This stage is report-only.

No cleanup action was executed:

- `data/medical_terms/mini_medical_terms_index.json` was not modified.
- `data/medical_terms/zh_term_overrides.json` was not modified.
- Loader routing was not modified.
- Meta seed files were not modified.
- Bioinformatics vocabulary files were not modified.
- No shared-core row was deleted, archived, or marked inactive.

## S1-S4 Summary

- Suspected shared-core pollution count: `177`.
- Manual review count: `50`.
- Mirrored Meta scoped count: `48`.
- Compatibility mapping count: `48`.
- Routing status: `passed` based on `docs/medical_terms/loader_routing_compatibility_20260520.md`.
- Excluded from Meta mirror: `1`.

S1 inventory category counts:

- `ambiguous_or_qualified_term`: 1
- `bioinformatics_technical_term`: 65
- `meta_effect_measure`: 27
- `meta_outcome`: 26
- `meta_research_intent`: 1
- `meta_study_design`: 15
- `needs_manual_review`: 42

## Terms Still In Shared Core But Mirrored To Meta Scope

These terms remain physically present in shared core for now, but S3/S4 have Meta scoped mirror and compatibility routing. The planned status is deprecation in a future cleanup phase, not execution in S5.

- `meta_context:follow_up` (follow-up) mirrors `mini:meta_analysis_follow_up`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_context:setting` (setting) mirrors `mini:meta_analysis_setting`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_context:subgroup` (subgroup) mirrors `mini:meta_analysis_subgroup`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_data_context:survival_data` (survival data) mirrors `mini:modality_survival_data`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:area_under_the_curve` (area under the curve) mirrors `mini:meta_analysis_area_under_curve`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:diagnostic_accuracy` (diagnostic accuracy) mirrors `mini:meta_analysis_diagnostic_accuracy`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:diagnostic_odds_ratio` (diagnostic odds ratio) mirrors `mini:meta_analysis_diagnostic_odds_ratio`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:negative_likelihood_ratio` (negative likelihood ratio) mirrors `mini:meta_analysis_negative_likelihood_ratio`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:negative_predictive_value` (negative predictive value) mirrors `mini:meta_analysis_negative_predictive_value`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:positive_likelihood_ratio` (positive likelihood ratio) mirrors `mini:meta_analysis_positive_likelihood_ratio`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:positive_predictive_value` (positive predictive value) mirrors `mini:meta_analysis_positive_predictive_value`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:receiver_operating_characteristic` (receiver operating characteristic) mirrors `mini:meta_analysis_receiver_operating_characteristic`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:sensitivity` (sensitivity) mirrors `mini:meta_analysis_sensitivity`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_diagnostic_outcome:specificity` (specificity) mirrors `mini:meta_analysis_specificity`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_effect:effect_size` (effect size) mirrors `mini:effect_size_core`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_outcome:endpoint` (endpoint) mirrors `mini:meta_analysis_endpoint`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_outcome:overall_survival` (overall survival) mirrors `mini:meta_outcomes_core`, `mini:meta_analysis_overall_survival`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_outcome:recurrence` (recurrence) mirrors `mini:meta_analysis_recurrence`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:comparator` (comparator) mirrors `mini:meta_analysis_comparator`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:control` (control) mirrors `mini:meta_analysis_control`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:intervention` (intervention) mirrors `mini:meta_analysis_intervention`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:outcome` (outcome) mirrors `mini:meta_analysis_outcome`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:patient` (patient) mirrors `mini:meta_analysis_patient`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:population` (population) mirrors `mini:meta_analysis_population`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_pico:study_design` (study design) mirrors `mini:meta_analysis_study_design`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:ahrq_checklist` (AHRQ checklist) mirrors `mini:meta_analysis_ahrq_checklist`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:cochrane_risk_of_bias` (Cochrane Risk of Bias) mirrors `mini:meta_analysis_cochrane_risk_of_bias`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:grade` (GRADE) mirrors `mini:meta_analysis_grade`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:jbi_critical_appraisal` (JBI critical appraisal) mirrors `mini:meta_analysis_jbi_critical_appraisal`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:newcastle_ottawa_scale` (Newcastle-Ottawa Scale) mirrors `mini:meta_analysis_newcastle_ottawa_scale`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:quadas_2` (QUADAS-2) mirrors `mini:meta_analysis_quadas_2`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_quality_tool:robins_i` (ROBINS-I) mirrors `mini:meta_analysis_robins_i`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_research_intent:risk` (risk) mirrors `mini:meta_analysis_risk`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_screening_marker:animal_study` (animal study) mirrors `mini:meta_analysis_animal_study`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_screening_marker:duplicate_publication` (duplicate publication) mirrors `mini:meta_analysis_duplicate_publication`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_screening_marker:in_vitro_study` (in vitro study) mirrors `mini:meta_analysis_in_vitro_study`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_screening_marker:non_human_study` (non-human study) mirrors `mini:meta_analysis_non_human_study`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_screening_marker:preprint` (preprint) mirrors `mini:meta_analysis_preprint`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:case_report` (case report) mirrors `mini:meta_analysis_case_report`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:comment` (comment) mirrors `mini:meta_analysis_comment`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:conference_abstract` (conference abstract) mirrors `mini:meta_analysis_conference_abstract`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:editorial` (editorial) mirrors `mini:meta_analysis_editorial`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:letter` (letter) mirrors `mini:meta_analysis_letter`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:meta_analysis` (meta-analysis) mirrors `mini:meta_analysis_meta_analysis`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:protocol` (protocol) mirrors `mini:meta_analysis_protocol`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:randomized_controlled_trial` (randomized controlled trial) mirrors `mini:study_design_core`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:review` (review) mirrors `mini:meta_analysis_review`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.
- `meta_study_design:systematic_review` (systematic review) mirrors `mini:meta_analysis_systematic_review`; planned shared status: `deprecated_in_shared_after_loader_routing`; cleanup executed: `false`.

## Cleanup Recommendations By Category

Default recommendation for every category below: Strategy A, after explicit user confirmation only.

- `meta_outcome`: 13 terms. Recommendation: Strategy A only after confirmation. Terms: area under the curve, diagnostic accuracy, diagnostic odds ratio, negative likelihood ratio, negative predictive value, positive likelihood ratio, positive predictive value, receiver operating characteristic, sensitivity, specificity, endpoint, overall survival, recurrence.
- `meta_effect_measure`: 1 terms. Recommendation: Strategy A only after confirmation. Terms: effect size.
- `meta_study_design`: 4 terms. Recommendation: Strategy A only after confirmation. Terms: meta-analysis, protocol, randomized controlled trial, systematic review.
- `meta_research_intent`: 1 terms. Recommendation: Strategy A only after confirmation. Terms: risk.
- `meta_quality_tool`: 7 terms. Recommendation: Strategy A only after confirmation. Terms: AHRQ checklist, Cochrane Risk of Bias, GRADE, JBI critical appraisal, Newcastle-Ottawa Scale, QUADAS-2, ROBINS-I.
- `meta_publication_type_screening_marker`: 11 terms. Recommendation: Strategy A only after confirmation. Terms: animal study, duplicate publication, in vitro study, non-human study, preprint, case report, comment, conference abstract, editorial, letter, review.
- `meta_data_context`: 4 terms. Recommendation: Strategy A only after confirmation. Terms: follow-up, setting, subgroup, survival data.
- `meta_pico_framework`: 7 terms. Recommendation: Strategy A only after confirmation. Terms: comparator, control, intervention, outcome, patient, population, study design.

## Strategy Comparison

### Strategy A: Deprecated / `active_in_shared=false`

Recommended default, not executed in S5. This preserves legacy rows and compatibility routing while preventing future active shared-core use once the cleanup is explicitly approved. It is the safest next step because rollback is straightforward and S4 routing already provides the replacement path.

### Strategy B: Move To `archive/shared_core_deprecated_terms.json`

Deferred. This can reduce active shared-core file size after Strategy A has been proven safe, but it changes file location and requires all consumers to use loader routing or compatibility mapping.

### Strategy C: Physical Delete

Not recommended as the default. This is destructive and can break direct legacy references if any consumer bypasses S4 routing. It should only be considered after a separate downstream-consumer audit.

## Non-Meta Routing Item

`gene expression profiling` remains a non-Meta routing item with status `bioinformatics_candidate_migration_required`. It was not mirrored into Meta scoped vocabulary. Future work should decide whether to route it to Bioinformatics scoped vocabulary or keep it as a manual routing item.

## Decision

The S5 decision is: recommend Strategy A as the default cleanup path, but do not execute it in this stage.

Any cleanup action requires explicit user confirmation, including marking shared-core rows deprecated, setting `active_in_shared=false`, moving rows to archive, or physically deleting rows.

## Validation Completed

The decision JSON loads successfully, matches S1-S4 counts, includes the Meta mirrored terms and non-Meta routing item, and confirms S5 did not modify mini or zh override files.

```bash
git diff --check
# passed
python3 -m pytest tests/shared/test_medical_terms_scope_routing.py -q
# 6 passed
python3 -m pytest tests/shared/test_meta_scoped_mirror_from_shared.py -q
# 7 passed
python3 -m pytest tests/shared/test_medical_terms_integration_audit.py -q
# 5 passed
python3 -m pytest tests/meta_analysis -q
# 17 passed
python3 -m pytest tests/bioinformatics -q
# 238 passed
python3 -m app.main --smoke-test
# passed
```
