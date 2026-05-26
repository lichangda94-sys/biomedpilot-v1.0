# B43 Risk Score Calibration / Decision Curve Input Gate

Date: 2026-05-27

## Scope

B43 defines the real input contract for future risk score calibration curve and decision curve execution.

This stage is planning and gate hardening only. It does not compute calibration statistics, net benefit, calibration curves, decision curves, report-ready packages, risk groups, clinical conclusions, prognosis labels, or treatment recommendations.

## Implemented Changes

Updated:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`

## New Gate

Public function:

- `build_risk_score_calibration_decision_curve_input_gate(project_root, result_id=None, planning_config=None)`

Schema:

- `biomedpilot.risk_score_calibration_decision_curve_input_gate.v1`

## Required Inputs

The gate checks:

- formal risk score source result
- B41 advanced visualization preflight readiness
- validation cohort id
- validation strategy
- predicted probability source, column, and 0-to-1 probability scale
- observed outcome mapping
- calibration method
- calibration bin count
- bootstrap or resampling policy
- minimum event count
- threshold probability grid
- net benefit formula policy
- treat-all / treat-none baseline policy
- clinical decision-boundary acknowledgement

## Representative Blockers

- `risk_score_advanced_visualization_preflight_not_passed`
- `validation_cohort_missing`
- `calibration_validation_strategy_missing`
- `predicted_probability_source_missing`
- `predicted_probability_column_missing`
- `predicted_probability_scale_invalid`
- `observed_outcome_mapping_missing`
- `calibration_method_missing`
- `calibration_bins_missing`
- `calibration_bins_invalid`
- `calibration_resampling_policy_missing`
- `minimum_event_count_not_met_for_advanced_visualization`
- `threshold_probability_grid_missing`
- `threshold_probability_grid_invalid`
- `net_benefit_formula_policy_missing`
- `decision_curve_treat_all_none_baselines_missing`
- `clinical_decision_boundary_acknowledgement_missing`

## Runtime Boundary

B43 remains input-review only:

- `formal_execution_enabled=False`
- `writes_result_index=False`
- `creates_plot_artifact=False`
- `creates_report_artifact=False`
- `report_ready_eligible=False`

Even when status is `ready_for_future_artifact_gate`, no calibration or decision-curve artifact is generated. That status only means the future execution gate has reviewable real input metadata.

## UI Behavior

Analysis Center now exposes:

- `Risk score calibration / decision curve input gate`

Action matrix now exposes:

- `risk_score_calibration_decision_curve_input`

When ready, the action is review-only:

- `button_behavior=enabled_input_review_only_no_artifact`

When blocked, disabled reasons show the missing validation, probability, outcome, threshold, net-benefit, or clinical-boundary inputs.

## Still Blocked

B43 does not enable:

- `risk_score_calibration_curve`
- `risk_score_decision_curve`
- net benefit calculation
- calibration statistics
- risk group generation
- report-ready unlock
- clinical interpretation

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`

Additional broader regression, app smoke, package smoke, open-W, and codesign results are recorded in the final task handoff.

## Conclusion

B43 prevents fake calibration or fake decision-curve output by requiring explicit real statistical inputs before any future execution stage can create artifacts.
