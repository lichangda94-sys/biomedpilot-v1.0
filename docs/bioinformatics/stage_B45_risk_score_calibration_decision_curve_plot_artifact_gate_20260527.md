# B45 Risk Score Calibration / Decision Curve Plot Artifact Gate

Date: 2026-05-27

## Scope

B45 activates controlled SVG plot artifacts for risk score calibration and decision curve visualization.

The plots can only be generated from B44 statistics tables already registered on a formal risk score result. B45 must not draw plots directly from B41/B43 preflight or planning config.

## Implemented Changes

Updated:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/risk_score_result_schema.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_risk_score_result_schema.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`

## New Gate And Executor

Public functions:

- `build_risk_score_calibration_decision_curve_plot_artifact_gate(project_root, result_id=None, plot_type="risk_score_calibration_curve", renderer="builtin_svg")`
- `create_risk_score_calibration_decision_curve_plot_artifact(project_root, result_id=None, plot_type="risk_score_calibration_curve", renderer="builtin_svg")`

Schemas:

- `biomedpilot.risk_score_calibration_decision_curve_plot_gate.v1`
- `biomedpilot.risk_score_calibration_decision_curve_plot_manifest.v1`

## Source Requirements

B45 requires:

- formal `task_type=risk_score` source result
- source result semantics inherited as `formal_computed_result`
- B44 `risk_score_calibration_statistics_table`
- B44 `risk_score_decision_curve_statistics_table`
- built-in SVG renderer
- plot artifact schema validation

Representative blockers:

- `formal_risk_score_result_not_found`
- `risk_score_calibration_statistics_table_missing`
- `risk_score_decision_curve_statistics_table_missing`
- `risk_score_calibration_decision_plot_type_not_enabled_in_b45:<plot_type>`
- `risk_score_calibration_decision_renderer_not_enabled_in_b45:<renderer>`

## Enabled Outputs

B45 can create:

- `risk_score_calibration_curve` SVG plot artifact
- `risk_score_decision_curve` SVG plot artifact
- plot artifact manifest
- result index v2 `plot_artifacts` attachment on the source risk score result

The plot artifact table provenance includes:

- source risk score result table
- B44 calibration statistics table
- B44 decision curve statistics table

## Runtime Boundary

B45 still enforces:

- `creates_report_artifact=False`
- `report_ready_eligible=False`
- no risk group generation
- no clinical conclusion
- no prognosis label
- no treatment recommendation

## UI Behavior

Analysis Center now exposes:

- `Risk score calibration / decision curve plot artifact`

Action matrix now exposes:

- `risk_score_calibration_decision_curve_plot`

When the gate passes, the action is enabled only for B44-statistics-sourced SVG plot artifacts:

- `button_behavior=enabled_b45_statistics_sourced_svg_plot_only`

When blocked, disabled reasons state that no plot is created from preflight/config alone.

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/survival_clinical/risk_score_result_schema.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_risk_score_result_schema.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`

Additional broader regression, app smoke, package smoke, open-W, and codesign results are recorded in the final task handoff.

## Conclusion

B45 enables calibration and decision curve SVG artifacts only from audited B44 statistics tables while preserving report-ready and clinical interpretation boundaries.
