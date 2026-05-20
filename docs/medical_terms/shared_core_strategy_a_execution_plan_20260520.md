# Shared Core Strategy A Execution Plan

Date: 2026-05-20

## Scope

This plan defines how Strategy A should be executed in a future user-approved phase. It does not modify `mini_medical_terms_index.json`, does not set `active_in_shared=false`, and does not delete shared-core rows.

## Summary

- Strategy: `A_deprecate_in_shared`
- Execution status: `not_executed`
- User confirmation required: `true`
- Terms to mark in a future phase: `48`
- Compatibility mappings present: `48`

Category counts:

- `Diagnostic outcome / accuracy`: 10
- `Meta PICO framework`: 7
- `Meta analysis context`: 4
- `Meta design / filter`: 9
- `Meta outcome`: 2
- `Meta quality tools`: 7
- `Meta screening/exclusion marker`: 5
- `meta_analysis_context`: 1
- `meta_data_context_or_extraction_context`: 1
- `meta_design_filter`: 1
- `meta_outcome`: 1

## Planned Row Changes

Future approved execution should mark only mapped legacy rows with:

```json
{
  "deprecated": true,
  "active_in_shared": false,
  "redirect_to": "meta_* canonical concept id",
  "deprecation_reason": "migrated_to_meta_scoped_vocabulary"
}
```

## Candidate Rows

- `meta_context:follow_up` <- `mini:meta_analysis_follow_up`; category=`Meta analysis context`; status=`not_executed_requires_user_confirmation`.
- `meta_context:setting` <- `mini:meta_analysis_setting`; category=`Meta analysis context`; status=`not_executed_requires_user_confirmation`.
- `meta_context:subgroup` <- `mini:meta_analysis_subgroup`; category=`Meta analysis context`; status=`not_executed_requires_user_confirmation`.
- `meta_data_context:survival_data` <- `mini:modality_survival_data`; category=`meta_data_context_or_extraction_context`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:area_under_the_curve` <- `mini:meta_analysis_area_under_curve`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:diagnostic_accuracy` <- `mini:meta_analysis_diagnostic_accuracy`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:diagnostic_odds_ratio` <- `mini:meta_analysis_diagnostic_odds_ratio`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:negative_likelihood_ratio` <- `mini:meta_analysis_negative_likelihood_ratio`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:negative_predictive_value` <- `mini:meta_analysis_negative_predictive_value`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:positive_likelihood_ratio` <- `mini:meta_analysis_positive_likelihood_ratio`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:positive_predictive_value` <- `mini:meta_analysis_positive_predictive_value`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:receiver_operating_characteristic` <- `mini:meta_analysis_receiver_operating_characteristic`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:sensitivity` <- `mini:meta_analysis_sensitivity`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_diagnostic_outcome:specificity` <- `mini:meta_analysis_specificity`; category=`Diagnostic outcome / accuracy`; status=`not_executed_requires_user_confirmation`.
- `meta_effect:effect_size` <- `mini:effect_size_core`; category=`meta_analysis_context`; status=`not_executed_requires_user_confirmation`.
- `meta_outcome:endpoint` <- `mini:meta_analysis_endpoint`; category=`Meta outcome`; status=`not_executed_requires_user_confirmation`.
- `meta_outcome:overall_survival` <- `mini:meta_outcomes_core`, `mini:meta_analysis_overall_survival`; category=`meta_outcome`; status=`not_executed_requires_user_confirmation`.
- `meta_outcome:recurrence` <- `mini:meta_analysis_recurrence`; category=`Meta outcome`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:comparator` <- `mini:meta_analysis_comparator`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:control` <- `mini:meta_analysis_control`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:intervention` <- `mini:meta_analysis_intervention`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:outcome` <- `mini:meta_analysis_outcome`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:patient` <- `mini:meta_analysis_patient`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:population` <- `mini:meta_analysis_population`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_pico:study_design` <- `mini:meta_analysis_study_design`; category=`Meta PICO framework`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:ahrq_checklist` <- `mini:meta_analysis_ahrq_checklist`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:cochrane_risk_of_bias` <- `mini:meta_analysis_cochrane_risk_of_bias`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:grade` <- `mini:meta_analysis_grade`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:jbi_critical_appraisal` <- `mini:meta_analysis_jbi_critical_appraisal`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:newcastle_ottawa_scale` <- `mini:meta_analysis_newcastle_ottawa_scale`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:quadas_2` <- `mini:meta_analysis_quadas_2`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_quality_tool:robins_i` <- `mini:meta_analysis_robins_i`; category=`Meta quality tools`; status=`not_executed_requires_user_confirmation`.
- `meta_research_intent:risk` <- `mini:meta_analysis_risk`; category=`Meta analysis context`; status=`not_executed_requires_user_confirmation`.
- `meta_screening_marker:animal_study` <- `mini:meta_analysis_animal_study`; category=`Meta screening/exclusion marker`; status=`not_executed_requires_user_confirmation`.
- `meta_screening_marker:duplicate_publication` <- `mini:meta_analysis_duplicate_publication`; category=`Meta screening/exclusion marker`; status=`not_executed_requires_user_confirmation`.
- `meta_screening_marker:in_vitro_study` <- `mini:meta_analysis_in_vitro_study`; category=`Meta screening/exclusion marker`; status=`not_executed_requires_user_confirmation`.
- `meta_screening_marker:non_human_study` <- `mini:meta_analysis_non_human_study`; category=`Meta screening/exclusion marker`; status=`not_executed_requires_user_confirmation`.
- `meta_screening_marker:preprint` <- `mini:meta_analysis_preprint`; category=`Meta screening/exclusion marker`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:case_report` <- `mini:meta_analysis_case_report`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:comment` <- `mini:meta_analysis_comment`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:conference_abstract` <- `mini:meta_analysis_conference_abstract`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:editorial` <- `mini:meta_analysis_editorial`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:letter` <- `mini:meta_analysis_letter`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:meta_analysis` <- `mini:meta_analysis_meta_analysis`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:protocol` <- `mini:meta_analysis_protocol`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:randomized_controlled_trial` <- `mini:study_design_core`; category=`meta_design_filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:review` <- `mini:meta_analysis_review`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.
- `meta_study_design:systematic_review` <- `mini:meta_analysis_systematic_review`; category=`Meta design / filter`; status=`not_executed_requires_user_confirmation`.

## Execution Order

1. Confirm user approval for Strategy A.
2. Create backup or checkpoint of mini_medical_terms_index.json.
3. Apply deprecated=true, active_in_shared=false, and redirect_to for mapped legacy rows only.
4. Run scope routing, Meta, Bioinformatics, and smoke tests.
5. Verify legacy Meta IDs resolve through compatibility map in Meta scope and are inactive outside Meta scope.
6. Commit only after validation passes.

## Rollback Strategy

- Revert the Strategy A commit if scope routing or downstream tests fail.
- Restore active_in_shared fields to previous values from the checkpoint.
- Keep meta_migrated_from_shared_terms.json and legacy_meta_compatibility_map.json unchanged during rollback unless separately approved.

## Required Tests

- `git diff --check`
- `python3 -m pytest tests/shared/test_medical_terms_scope_routing.py -q`
- `python3 -m pytest tests/shared/test_meta_scoped_mirror_from_shared.py -q`
- `python3 -m pytest tests/shared/test_medical_terms_integration_audit.py -q`
- `python3 -m pytest tests/meta_analysis -q`
- `python3 -m pytest tests/bioinformatics -q`
- `python3 -m app.main --smoke-test`

## Explicit Non-Actions

- No shared-core deprecation was executed in this phase.
- No shared-core row was deleted.
- No archive move was performed.
