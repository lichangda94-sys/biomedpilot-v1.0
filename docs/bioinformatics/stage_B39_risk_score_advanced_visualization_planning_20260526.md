# B39 Risk Score Nomogram / Calibration / Decision Curve Planning

Date: 2026-05-26

## Scope

B39 defines the next planning gate for advanced risk score visualizations:

- nomogram
- calibration curve
- decision curve

This stage is planning only. It does not generate advanced visualization artifacts and does not unlock report-ready or clinical interpretation.

## Implemented Changes

Updated:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`

## New Gate

New public function:

- `build_risk_score_advanced_visualization_planning_gate(project_root, result_id=None)`

Schema:

- `biomedpilot.risk_score_advanced_visualization_planning_gate.v1`

The gate selects a formal risk score source if available, then remains blocked with:

- `b40_risk_score_advanced_visualization_activation_required`

## Planned Artifacts

B39 records planned descriptors only:

- `risk_score_nomogram`
- `risk_score_calibration_curve`
- `risk_score_decision_curve`

No SVG, PNG, PDF, DOCX, JSON result artifact, report package, or result-index plot artifact is written by B39.

## Minimum Conditions Captured

Nomogram future conditions:

- formal risk score result
- source Cox multivariate coefficients
- coefficient provenance
- nomogram scale policy
- external renderer runtime acceptance
- clinical boundary acknowledgement

Calibration curve future conditions:

- formal risk score result
- time horizon policy
- observed outcome mapping
- calibration method policy
- validation or bootstrap policy
- low event count blocker

Decision curve future conditions:

- formal risk score result
- threshold probability grid
- net benefit formula policy
- clinical utility boundary acknowledgement
- decision recommendation forbidden

## UI Behavior

Analysis Center now exposes:

- `Risk score nomogram / calibration / decision curve planning`

Action matrix now exposes:

- `risk_score_advanced_visualization`

The action is always disabled in B39 and shows the explicit activation blocker.

## Boundaries Preserved

B39 does not:

- generate a nomogram
- generate a calibration curve
- generate a decision curve
- create risk groups
- output prognosis labels
- create diagnosis or treatment recommendation text
- unlock report-ready
- create full integrated clinical interpretation
- write result index v2

B38 remains the only active risk score visualization renderer path, and it remains limited to a formal risk score distribution SVG artifact.

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_risk_score_result_review.py tests/bioinformatics/test_risk_score_result_schema.py tests/bioinformatics/test_risk_score_execution.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_plot_artifact_schema.py`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or survival_clinical or analysis_ui or plot_artifact"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "risk or analysis_task"`
- `git diff --check`

Observed results:

- py_compile: passed
- focused risk score tests: 19 passed
- Analysis UI / plot schema focused tests: 30 passed
- broader Bioinformatics filtered tests: 102 passed, 646 deselected
- focused UI workflow tests: 8 passed, 112 deselected
- git diff check: passed

Broader package validation is recorded in the final handoff after commit so packaged `git_head` matches source.

## Conclusion

B39 passes as a planning-only gate. It makes nomogram, calibration curve and decision curve prerequisites visible without expanding formal clinical interpretation or report-ready scope.

Recommended next step: B40 Advanced Risk Score Visualization Runtime Planning, still starting with renderer/runtime policy and validation conditions before any artifact creation.
