# B40 Risk Score Advanced Visualization Runtime Planning

Date: 2026-05-26

## Scope

B40 defines runtime policy and validation gates for future advanced risk score visualization execution.

This stage remains planning only. It does not create nomogram, calibration curve, decision curve, risk group, report-ready package, or clinical interpretation.

## Implemented Changes

Updated:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`

## New Runtime Planning Gate

New public function:

- `build_risk_score_advanced_visualization_runtime_plan(project_root, result_id=None)`

Schema:

- `biomedpilot.risk_score_advanced_visualization_runtime_plan.v1`

The gate selects a formal risk score result if available, then remains blocked with:

- `b41_risk_score_advanced_visualization_execution_required`

## Runtime Policy

B40 records these policies:

- renderer detection is detect-first
- no auto-install
- no download
- external R is system `Rscript` only and not bundled
- Python renderers may use only built-in SVG or already available packages
- future artifacts must attach to the formal risk score source result
- report-ready remains a separate future gate

## Artifact Runtime Plans

Nomogram:

- renderer candidates: external `r_rms_nomogram` and future built-in SVG nomogram spec
- both remain blocked
- requires coefficient provenance, coefficient units, nomogram scale policy, axis label policy and clinical-boundary acknowledgement

Calibration curve:

- renderer candidate: future `builtin_svg_calibration`
- remains blocked because calibration statistics are not activated
- requires time horizon, observed outcome mapping, predicted probability policy, bootstrap or validation policy and minimum event count policy

Decision curve:

- renderer candidate: future `builtin_svg_decision_curve`
- remains blocked because net-benefit statistics are not activated
- requires threshold probability grid, net-benefit formula policy, treat-all/none baselines and explicit prohibition of clinical decision recommendations

## Validation Gates

B40 defines future blockers:

- low event count
- missing outcome mapping
- missing prediction time horizon
- invalid threshold grid
- source containing clinical conclusion
- any report-ready unlock attempt

## UI Behavior

Analysis Center now exposes:

- `Risk score advanced visualization runtime plan`

Action matrix now exposes:

- `risk_score_advanced_runtime_plan`

The action is always disabled in B40. The disabled reason includes `b41_risk_score_advanced_visualization_execution_required`.

## Boundaries Preserved

B40 does not:

- generate nomogram, calibration curve or decision curve
- generate high/low risk groups or clinical risk groups
- write result index v2
- create report artifacts
- set `report_ready_eligible=True`
- output prognosis, diagnosis, treatment recommendation or clinical conclusion
- change B38 distribution SVG behavior

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
- focused risk score tests: 21 passed
- Analysis UI / plot schema focused tests: 30 passed
- broader Bioinformatics filtered tests: 104 passed, 649 deselected
- focused UI workflow tests: 8 passed, 112 deselected
- git diff check: passed

Broader package validation is recorded in the final handoff after commit so packaged `git_head` matches source.

## Conclusion

B40 passes as a runtime planning gate. It makes renderer and validation requirements explicit while preserving the current boundary: only B38 risk score distribution SVG is active, and advanced clinical visualizations remain blocked.

Recommended next step: B41 Advanced Risk Score Visualization Preflight Gate, still without artifact creation, to validate time horizon, outcome mapping, event count and threshold-grid inputs before considering runtime execution.
