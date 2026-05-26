# B38 Risk Score Plot Renderer Execution MVP

Date: 2026-05-26

## Scope

B38 activates the first real risk score visualization artifact path. The MVP is intentionally narrow:

- source must be a registered `task_type=risk_score` result
- source semantics must be `formal_computed_result`
- source result table must be `risk_score_result_table`
- renderer must be `builtin_svg`
- plot type must be `risk_score_distribution_plot`

This stage does not activate nomogram, calibration curve, decision curve, risk grouping, report-ready, or clinical interpretation.

## Implemented Changes

Updated:

- `app/bioinformatics/survival_clinical/risk_score_plot_schema.py`
- `app/bioinformatics/survival_clinical/risk_score_result_schema.py`
- `app/bioinformatics/survival_clinical/risk_score_review.py`
- `app/bioinformatics/survival_clinical/__init__.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/bioinformatics/test_risk_score_plot_gate.py`
- `tests/bioinformatics/test_risk_score_result_schema.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`

## New Execution API

New public function:

- `create_risk_score_plot_artifact(project_root, result_id=None, plot_type="risk_score_distribution_plot", renderer="builtin_svg")`

The function:

1. Runs the B37/B38 activation gate.
2. Reads only the registered risk score result table.
3. Creates a real SVG risk score distribution plot.
4. Writes a plot manifest.
5. Registers the plot artifact on the source result entry in result index v2.
6. Keeps `report_ready_eligible=False`.

## Output Paths

For a valid source result:

- SVG image: `results/plots/risk_score/<plot_id>.svg`
- plot manifest: `results/plots/risk_score/<plot_id>_manifest.json`
- result index update: `results/summaries/result_index.json`

## Result Index Semantics

The plot artifact inherits source semantics:

- `source_result_semantics=formal_computed_result`
- `plot_semantics=formal_computed_result`
- `plot_artifact_scope=formal_risk_score_plot_artifact`

The source result remains:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- `report_ready_eligible=False`

B38 updates `validate_risk_score_result_index_entry` so a formal risk score result may contain a valid `risk_score_distribution_plot` artifact. It still blocks unsupported plot types such as nomogram and any non-formal or mismatched plot artifact.

## UI Behavior

The Analysis UI action `risk_score_plot_artifact` can become enabled only when the B38 gate passes.

Enabled action copy:

- real SVG risk score distribution artifact only
- no risk groups
- no nomogram
- no report-ready output
- no clinical interpretation

If the source is missing or invalid, the action remains disabled with explicit blockers.

## Explicitly Still Blocked

B38 does not implement:

- `risk_score_nomogram`
- `risk_score_calibration_curve`
- `risk_score_decision_curve`
- high/low risk group generation
- clinical risk groups
- prognosis labels
- diagnosis
- treatment recommendations
- clinical conclusions
- risk score report-ready package
- full integrated clinical interpretation

Unsupported requests block with:

- `risk_score_plot_type_not_enabled_in_b38:<plot_type>`
- `risk_score_plot_renderer_not_enabled_in_b38:<renderer>`

## Verification

Commands run:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_plot_schema.py app/bioinformatics/survival_clinical/risk_score_result_schema.py app/bioinformatics/survival_clinical/risk_score_review.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_plot_gate.py tests/bioinformatics/test_risk_score_result_review.py tests/bioinformatics/test_risk_score_result_schema.py tests/bioinformatics/test_risk_score_execution.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_plot_artifact_schema.py`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or survival_clinical or analysis_ui or plot_artifact"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "risk or analysis_task"`
- `git diff --check`

Observed results:

- py_compile: passed
- focused risk score tests: 17 passed
- Analysis UI / plot schema focused tests: 30 passed
- broader Bioinformatics filtered tests: 100 passed, 646 deselected
- focused UI workflow tests: 8 passed, 112 deselected
- git diff check: passed

Broader package validation is recorded in the final handoff after commit so packaged `git_head` matches source.

## Conclusion

B38 passes as a controlled risk score plot renderer MVP. The only real artifact enabled is a formal risk score distribution SVG. Risk grouping, nomogram, report-ready, and clinical interpretation remain blocked.

Recommended next step: B39 Risk Score Nomogram / Calibration / Decision Curve Planning, keeping nomogram and clinical interpretation disabled until separate validation and clinical-boundary gates exist.
