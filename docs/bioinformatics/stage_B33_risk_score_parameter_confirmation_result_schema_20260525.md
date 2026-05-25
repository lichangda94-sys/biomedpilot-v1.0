# Bioinformatics B33 Risk Score Parameter Confirmation / Result Schema

Date: 2026-05-25

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `973d59f add Bioinformatics risk score contract gate`

## Scope

B33 adds the user parameter confirmation layer and future result schema gate for risk score / nomogram work.

This stage still does not execute risk score modeling, does not generate risk score values, does not generate high/low-risk groups, does not render nomogram/calibration/decision-curve plots, does not write result index v2, and does not create a risk score report-ready package.

## Parameter Confirmation Gate

New module:

- `app/bioinformatics/survival_clinical/risk_score_confirmation.py`

New exported APIs:

- `confirm_risk_score_parameters(...)`
- `load_risk_score_parameter_confirmation(...)`
- `validate_risk_score_parameter_confirmation(...)`

Saved manifest:

- `manifests/risk_score_parameter_confirmation.json`

Schemas:

- `biomedpilot.risk_score_parameter_confirmation.v1`
- `biomedpilot.risk_score_parameter_confirmation_gate.v1`

The confirmation manifest records:

- B32 contract gate digest
- source survival package id
- source clinical variable audit id
- source Cox multivariate result id
- candidate variables
- coefficient source
- cutoff policy
- missingness policy
- scaling policy
- calibration plan
- nomogram policy
- training/validation plan
- validation plan
- source dependency snapshot
- source parameters manifest
- user confirmation status
- clinical boundary acknowledgement
- future output plan
- forbidden outputs
- blockers and warnings

The confirmation gate blocks:

- missing confirmation manifest
- B32 contract gate not ready
- user did not confirm parameters
- confirmation/contract mismatch
- missing source ids
- missing candidate variables
- missing coefficient, cutoff, missingness, scaling, calibration, nomogram, training/validation, or validation policy
- source dependency snapshot not passed
- source parameters manifest missing
- clinical boundary not acknowledged
- any confirmation manifest that enables execution, writes result index, or marks report-ready
- missing future output-plan fields

The confirmation keeps:

- `formal_execution_enabled=False`
- `writes_result_index=False`
- `result_semantics=parameter_confirmation_only`
- `report_ready_eligible=False`

## Result Schema Gate

New module:

- `app/bioinformatics/survival_clinical/risk_score_result_schema.py`

New exported APIs:

- `build_risk_score_result_schema_gate(...)`
- `validate_risk_score_result_table(...)`
- `validate_risk_score_result_index_entry(...)`

Schema:

- `biomedpilot.risk_score_result_schema_gate.v1`

The gate validates the future formal result shape only. It blocks by default because B33 does not provide an executor or result bundle.

The future result index v2 entry must include:

- `task_type=risk_score`
- `result_semantics=formal_computed_result`
- source Cox multivariate result id
- risk score parameter confirmation
- parameters manifest
- dependency snapshot with status `passed`
- `risk_score_result_table` output artifact
- validation status `passed` or `warning`
- no blockers
- no plot artifacts
- no report artifacts
- `report_ready_eligible=False`

The future table schema requires:

- `sample_id`
- `case_id`
- `risk_score`
- `source_cox_multivariate_result_id`
- `model_formula`
- `coefficient_source`
- `missingness_policy`
- `scaling_policy`
- `warnings`

The schema blocks:

- non-formal/imported/testing/exploratory/preflight semantics
- missing risk score result table artifact
- invalid validation status
- formal result with blockers
- plot/report artifacts
- report-ready eligibility
- risk group fields
- nomogram score
- clinical conclusion, prognosis label, diagnosis, or treatment recommendation

## Analysis UI Integration

Analysis Center now adds two survival/clinical gate rows:

- `B33 Risk score parameter confirmation`
- `B33 Risk score result schema gate`

The `Risk score / nomogram` row now combines B32/B33 blockers and warnings.

The action matrix still disables `Generate risk score`. Its state is `confirmation_schema_gate_only` once B33 gates are present, and the disabled reason includes missing confirmation and missing future result bundle.

## Boundaries Preserved

B33 does not:

- execute risk score modeling
- compute per-sample risk score
- create high/low-risk group labels
- generate nomogram, calibration, or decision-curve artifacts
- create clinical prognosis, diagnosis, treatment recommendation, or clinical conclusion
- write result index v2
- create plot/report artifacts
- unlock full integrated report
- auto-install glmnet/R/Python modeling dependencies

## Verification

Commands intended for this stage:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_confirmation.py app/bioinformatics/survival_clinical/risk_score_result_schema.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_contract_gate.py tests/bioinformatics/test_risk_score_design_audit.py tests/bioinformatics/test_risk_score_confirmation.py tests/bioinformatics/test_risk_score_result_schema.py`
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
- risk score focused tests: 16 passed
- Analysis UI / capability focused tests: 29 passed
- broad Bioinformatics filtered tests: 73 passed, 659 deselected
- focused UI workflow tests: 8 passed, 111 deselected
- `git diff --check`: passed
- source smoke: passed, `git_head=973d59f`
- package smoke: passed, `git_head=973d59f`
- open-W smoke: passed
- codesign: passed

## Issues

Blocker: none at implementation start.

Major: B33 intentionally has no executor; risk score activation must remain blocked until a later controlled execution stage.

Minor: No persisted UI editor for risk score parameters exists yet; this stage defines and validates the manifest surface first.

## Conclusion

B33 is a gate-hardening stage only. It prepares user confirmation and result schema boundaries for future risk score execution while preserving the current disabled state and clinical interpretation boundary.
