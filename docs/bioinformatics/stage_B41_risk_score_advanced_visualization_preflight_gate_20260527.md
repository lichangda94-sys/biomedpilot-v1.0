# B41 Risk Score Advanced Visualization Preflight Gate

Date: 2026-05-27

## Scope

B41 adds a preflight-only gate for future advanced risk score visualization work.

The goal is to validate whether a formal risk score result has enough configured context for later nomogram, calibration curve, and decision curve execution. B41 does not create any artifact, write result index v2, unlock report-ready export, generate risk groups, or output clinical interpretation.

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

- `build_risk_score_advanced_visualization_preflight_gate(project_root, result_id=None, preflight_config=None)`

Schema:

- `biomedpilot.risk_score_advanced_visualization_preflight_gate.v1`

The gate checks:

- formal risk score source availability
- source dependency snapshot and report-ready boundary
- prediction time horizon
- outcome time/event mapping
- minimum event count
- threshold probability grid bounds and ordering
- explicit clinical-boundary acknowledgement

## Blockers

Representative blockers:

- `formal_risk_score_result_not_found`
- `time_horizon_missing`
- `time_horizon_invalid`
- `outcome_time_field_missing`
- `outcome_event_field_missing`
- `event_count_missing`
- `minimum_event_count_not_met_for_advanced_visualization`
- `threshold_probability_grid_missing`
- `threshold_probability_grid_invalid`
- `clinical_boundary_acknowledgement_missing`

## Runtime Boundary

B41 remains preflight only:

- `formal_execution_enabled=False`
- `writes_result_index=False`
- `creates_plot_artifact=False`
- `creates_report_artifact=False`
- `report_ready_eligible=False`

Passing B41 means the future advanced visualization inputs are reviewable. It does not mean nomogram, calibration, decision-curve, risk grouping, prognosis labeling, treatment recommendation, or clinical decision support is enabled.

## UI Behavior

Analysis Center now exposes:

- `Risk score advanced visualization preflight`

Action matrix now exposes:

- `risk_score_advanced_preflight`

When the preflight passes, the action is enabled only as review-only:

- `button_behavior=enabled_preflight_review_only_no_artifact`

When blocked, the disabled reason surfaces the missing source, time horizon, outcome mapping, event count, threshold grid, or clinical-boundary acknowledgement.

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`

Additional package and broader regression commands are recorded in the final task handoff.

## Conclusion

B41 closes the advanced visualization input preflight gap while preserving the B40 boundary. Advanced risk score visualization artifacts remain blocked until a later audited execution stage.
