# B37 Risk Score Plot Artifact Schema / Renderer Gate

Date: 2026-05-26

## Scope

B37 adds the schema and renderer gate that must exist before any real risk score visualization work can be activated. It is intentionally not a renderer execution stage.

This stage covers:

- formal risk score result source eligibility
- risk score visualization artifact schema
- renderer dependency detection policy
- Analysis UI disabled reason exposure
- result-index and report-ready boundary preservation

## Implemented Files

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/plots/models.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`

## Gate API

New public functions:

- `check_risk_score_plot_renderer_dependencies(renderer="builtin_svg")`
- `build_risk_score_plot_artifact_schema_candidate(...)`
- `validate_risk_score_plot_artifact_schema(...)`
- `build_risk_score_plot_artifact_activation_gate(...)`

New schema ids:

- `biomedpilot.risk_score_plot_artifact_activation_gate.v1`
- `biomedpilot.risk_score_plot_artifact.v1`

## Supported Future Plot Types

B37 reserves schema-level plot types only:

- `risk_score_distribution_plot`
- `risk_score_nomogram`
- `risk_score_calibration_curve`
- `risk_score_decision_curve`

These are added to the generic plot artifact type allow-list so future validation can be consistent with the existing plot artifact schema.

## Source Eligibility

The activation gate accepts only registered result-index entries with:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- `validation_status=passed` or `warning`
- no source blockers
- `dependency_snapshot.status=passed`
- `risk_score_parameter_confirmation` present
- `risk_score_result_table` in `output_artifacts`
- `report_ready_eligible` not true
- no report artifacts

The gate does not accept imported, exploratory, testing, preflight, non-risk-score, missing-table, missing-confirmation, failed-validation, or report-ready sources.

## Renderer Policy

B37 uses detect-first renderer dependency snapshots:

- `builtin_svg`: passed, no external dependency, no install action
- `matplotlib_png`: detect-only optional dependency, no install action
- `r_rms_nomogram`: blocked, external R renderer not enabled or bundled
- unknown renderer: blocked

No renderer is invoked in B37.

## UI Changes

Analysis Center now shows a separate B37 row:

- `Risk score plot artifact schema / renderer gate`

The row exposes:

- selected source result id
- planned plot type
- renderer id
- `creates_plot_artifact=False`
- disabled reason including `b38_risk_score_plot_renderer_execution_required`

Action matrix now includes:

- `risk_score_plot_artifact`

It is always disabled in B37, even when source/schema/renderer checks are otherwise ready.

## Boundary Preservation

B37 does not:

- create SVG, PNG, PDF, or other image artifacts
- generate nomogram, calibration curve, or decision curve
- write plot artifacts to result index v2
- change `report_ready_eligible`
- create report artifacts
- create high/low risk groups or clinical risk groups
- output prognosis labels, diagnosis, treatment recommendations, or clinical conclusions
- activate report-ready or full integrated clinical interpretation

The required future blocker is:

- `b38_risk_score_plot_renderer_execution_required`

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/plots/models.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_risk_score_result_review.py tests/bioinformatics/test_risk_score_result_schema.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_plot_artifact_schema.py`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or survival_clinical or analysis_ui"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "risk or analysis_task"`
- `git diff --check`

Observed results:

- py_compile: passed
- focused risk score tests: 12 passed
- Analysis UI / plot schema focused tests: 30 passed
- broader Bioinformatics filtered tests: 73 passed, 671 deselected
- focused UI workflow tests: 8 passed, 112 deselected
- git diff check: passed

Package, `open -W`, and codesign validation are recorded in the final task handoff after commit so the packaged `git_head` matches the committed source.

## Conclusion

B37 passes as a schema and renderer-gate hardening stage. It prepares the risk score visualization artifact contract but deliberately keeps real visualization execution blocked until B38.

Recommended next step: B38 Risk Score Plot Renderer Execution MVP, limited to a real statistical visualization artifact from a formal risk score source, with no risk grouping, no clinical interpretation, and no report-ready unlock.
