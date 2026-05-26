# Bioinformatics B34 Controlled Risk Score Execution MVP

Date: 2026-05-26

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `becf9bb add Bioinformatics risk score confirmation gates`

## Scope

B34 activates a controlled risk score table-only MVP.

This stage computes per-sample risk score values only after B32 source/contract gate and B33 user parameter confirmation pass. It writes a formal result index v2 entry for `task_type=risk_score`, but it does not generate high/low-risk groups, nomogram, calibration curve, decision curve, plot artifacts, report-ready package, prognosis labels, diagnosis, treatment recommendation, or clinical conclusions.

## Executor

New module:

- `app/bioinformatics/survival_clinical/risk_score_executor.py`

New exported API:

- `run_controlled_risk_score(project_root, contract_gate, confirmation)`

Engine metadata:

- `engine_name=biomedpilot_controlled_risk_score`
- `engine_version=0.1.0`

The executor reads:

- B32 `risk_score_contract_gate`
- B33 `risk_score_parameter_confirmation`
- source formal Cox multivariate result table artifact
- source Cox multivariate parameter manifest provenance
- clinical table from the B12/B20 provenance path

It computes:

- `risk_score = sum(log(hazard_ratio) * encoded_covariate_value)`

Encoding policy:

- continuous numeric covariates are used as-is
- binary/categorical/ordinal covariates use the same lexicographic reference encoding as the controlled Cox MVP
- rows with missing required covariates are excluded from the risk score table

## Output Table

The controlled result table uses the B33 schema:

- `sample_id`
- `case_id`
- `risk_score`
- `source_cox_multivariate_result_id`
- `model_formula`
- `coefficient_source`
- `missingness_policy`
- `scaling_policy`
- `warnings`

Forbidden fields remain blocked:

- risk group labels
- high/low-risk groups
- nomogram score
- prognosis label
- clinical conclusion
- diagnosis
- treatment recommendation

## Result Index

On success, B34 registers result index v2 with:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- source survival package id
- B32 contract parameters manifest
- B33 parameter confirmation
- source Cox multivariate result id
- source dependency snapshot
- risk score result table artifact
- task-run log artifact
- `plot_artifacts=[]`
- `report_artifacts=[]`
- `report_ready_eligible=False`

On failure, B34 writes only the task-run log and does not write result index v2.

## UI Integration

Analysis action matrix now enables `Generate risk score` only when:

- B32 contract gate status is `ready_for_parameter_confirmation`
- B33 parameter confirmation gate status is `passed`
- result schema gate has no blocker other than the expected pre-run `risk_score_result_bundle_missing`

The button state is:

- `enabled_controlled_risk_score_mvp`

Button behavior:

- `enabled_controlled_risk_score_table_only`

The desktop Analysis Task Center includes a `运行 controlled risk score` button. The button remains disabled unless the Analysis Center action matrix enables `risk_score`.

Capability map now reports risk score as:

- `implementation_status=b34_controlled_table_only_mvp`

It still cannot display as completed until a validated result entry exists.

## Boundaries Preserved

B34 does not:

- create risk groups or cutpoint-derived labels
- render nomogram, calibration, or decision curve
- generate plot artifacts
- generate report artifacts
- mark report-ready
- create clinical diagnosis, prognosis, treatment recommendation, or clinical conclusion
- execute glmnet or automatic model training
- bypass B32/B33 gates
- consume imported/testing/exploratory/preflight sources as formal risk score input

## Verification

Commands intended for this stage:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_executor.py app/bioinformatics/survival_clinical/risk_score_contract_gate.py app/bioinformatics/survival_clinical/risk_score_result_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py app/bioinformatics/workflow_pages.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_contract_gate.py tests/bioinformatics/test_risk_score_confirmation.py tests/bioinformatics/test_risk_score_result_schema.py tests/bioinformatics/test_risk_score_execution.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_capability_map.py`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or cox_multivariate or survival_clinical or analysis_ui"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "survival or cox or risk or analysis_task"`
- `git diff --check`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Observed results:

- py_compile: passed
- risk score focused tests: 15 passed
- Analysis UI / capability focused tests: 30 passed
- broad Bioinformatics filtered tests: 77 passed, 659 deselected
- focused UI workflow tests: 8 passed, 111 deselected
- `git diff --check`: passed
- source smoke: passed
- package smoke: passed
- open-W smoke: passed
- codesign: passed

## Issues

Blocker: none at implementation start.

Major: none.

Minor: B34 is table-only; risk group, nomogram, calibration, decision-curve, report-ready, and interpretation layers remain future gated stages.

## Conclusion

B34 provides controlled risk score execution as a table-only formal statistical result, while preserving all clinical interpretation, plotting, and report-ready boundaries.
