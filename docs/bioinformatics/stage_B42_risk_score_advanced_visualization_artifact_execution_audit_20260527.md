# B42 Risk Score Advanced Visualization Artifact Execution Audit

Date: 2026-05-27

## Scope

B42 activates one controlled advanced risk score visualization artifact path:

- `risk_score_nomogram`

This is a BioMedPilot-controlled SVG nomogram-scale artifact generated only from a formal risk score result after the B41 preflight gate passes. It remains a statistical visualization artifact, not a clinical nomogram interpretation.

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

- `build_risk_score_advanced_visualization_artifact_gate(project_root, result_id=None, plot_type="risk_score_nomogram", renderer="builtin_svg", preflight_config=None)`
- `create_risk_score_advanced_visualization_artifact(project_root, result_id=None, plot_type="risk_score_nomogram", renderer="builtin_svg", preflight_config=None)`

Schemas:

- `biomedpilot.risk_score_advanced_visualization_artifact_gate.v1`
- `biomedpilot.risk_score_advanced_visualization_manifest.v1`

## Gate Requirements

The artifact gate requires:

- formal `task_type=risk_score` source result
- source result semantics inherited as `formal_computed_result`
- B41 preflight status `passed_preflight_only`
- passed dependency snapshot on the source result
- risk score result table artifact
- built-in SVG renderer
- plot artifact schema validation

## Enabled Output

B42 can create:

- a controlled SVG `risk_score_nomogram` artifact
- a plot artifact manifest
- a result index v2 `plot_artifacts` attachment on the source risk score result

The plot artifact inherits:

- `source_result_id`
- `source_result_semantics`
- `input_package_id`
- `task_run_id`
- `parameters_manifest`
- dependency snapshot

## Still Blocked

B42 continues to block:

- `risk_score_calibration_curve`
- `risk_score_decision_curve`
- risk group generation
- prognosis labels
- treatment recommendations
- clinical conclusions
- report-ready unlock

Representative blocker:

- `risk_score_advanced_plot_type_not_enabled_in_b42:risk_score_calibration_curve`

## UI Behavior

Analysis Center now exposes:

- `Risk score advanced visualization artifact`

Action matrix now exposes:

- `risk_score_advanced_artifact`

When the gate passes, the action is enabled only for the controlled nomogram-scale SVG artifact:

- `button_behavior=enabled_nomogram_scale_svg_artifact_only`

When blocked, the disabled reason includes missing B41 preflight/source/schema blockers and states that calibration, decision curve, report-ready output, and clinical conclusion are not generated.

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/survival_clinical/risk_score_result_schema.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_risk_score_result_schema.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`

Additional broader regression, app smoke, package smoke, open-W, and codesign results are recorded in the final task handoff.

## Conclusion

B42 enables a narrowly audited advanced risk score visualization artifact path while preserving the clinical and report boundaries. Calibration and decision curve execution remain future gated work.
