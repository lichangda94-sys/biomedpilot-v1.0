# Bioinformatics B32 Risk Score Source / Contract Gate

Date: 2026-05-25

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `8820b26 docs(bio): plan formal analysis production report roadmap`

## Scope

B32 implements the first risk score / nomogram gate after B31 planning.

This stage validates source and design readiness only. It does not compute a risk score, does not generate risk groups, does not render a nomogram, does not write result index v2, and does not create a risk score report package.

## Implemented Contract Gate

New module:

- `app/bioinformatics/survival_clinical/risk_score_contract_gate.py`

New exported API:

- `build_risk_score_nomogram_contract_gate(...)`

Schema:

- `biomedpilot.risk_score_nomogram_contract_gate.v1`

Passing status:

- `ready_for_parameter_confirmation`

Non-passing status:

- `blocked`

The gate keeps:

- `formal_execution_enabled=False`
- `writes_result_index=False`
- `result_semantics=contract_gate_only`
- `report_ready_eligible=False`

## Required Inputs

The gate accepts only audited contract inputs:

- B12 survival/clinical package
- B12 clinical variable audit
- model specification
- formal Cox multivariate result source

The source Cox result must be:

- `task_type=cox_multivariate`
- `result_semantics=formal_computed_result`
- `validation_status=passed` or `warning`
- dependency snapshot status `passed`
- parameters manifest present
- task-run log artifact present
- `cox_multivariate_result_table` output artifact present
- no blockers

## B32 Fields

The gate records:

- source survival package id
- source clinical variable audit id
- source Cox multivariate result id
- source result semantics
- source validation status
- source dependency snapshot
- source parameters manifest
- candidate variables
- coefficient source
- training/validation plan
- cutoff policy
- overfitting protection plan
- external validation plan
- validation plan
- missingness policy
- scaling policy
- calibration plan
- nomogram policy
- interpretation boundary
- forbidden outputs
- checks
- blockers
- warnings

## Blockers

The gate blocks:

- missing survival/clinical input
- missing clinical variable audit
- missing formal Cox multivariate result
- source result not Cox multivariate
- source result not formal computed result
- source validation not passed/warning
- source result has blockers
- source dependency snapshot missing/failed
- source parameters manifest missing
- source task-run log missing
- source Cox multivariate table artifact missing
- candidate variables missing
- candidate variable not in clinical variable audit
- model formula missing
- coefficient provenance missing
- training/validation plan missing
- cutoff strategy missing
- cutoff policy missing
- data-leakage-prone cutoff policy
- missingness policy missing
- scaling policy missing
- calibration plan missing
- nomogram policy missing
- external validation required but missing
- requested clinical conclusion, prognosis label, diagnosis, clinical risk group, or treatment recommendation

## Analysis UI Integration

Analysis Center now builds `risk_score_contract_gate` in survival/clinical state.

UI changes:

- survival/clinical rows show `Risk score / nomogram` with B32 source/contract status.
- action matrix still disables `Generate risk score`.
- disabled reason now comes from B32 source/contract blockers.
- capability map wording now describes B32 contract readiness instead of only B21 design audit.

The UI still does not expose a normal-user execution button for risk score.

## Boundaries Preserved

B32 does not:

- compute risk score values
- write result index v2
- generate risk group labels
- generate nomogram, calibration curve, or decision curve
- create plot artifacts
- create report-ready package
- unlock full integrated report
- create clinical diagnosis, prognosis, or treatment recommendation
- auto-install glmnet/R/Python modeling dependencies

## Tests

Added:

- `tests/bioinformatics/test_risk_score_contract_gate.py`

Updated:

- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `app/bioinformatics/analysis_ui/capability_map.py`

## Verification

Commands run during implementation:

- `python3 -m py_compile app/bioinformatics/survival_clinical/risk_score_contract_gate.py app/bioinformatics/survival_clinical/__init__.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_contract_gate.py tests/bioinformatics/test_risk_score_design_audit.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_capability_map.py`
- `git diff --check`
- `python3 -m pytest tests/bioinformatics -q -k "risk_score or cox_multivariate or survival_clinical or analysis_ui"`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "survival or cox or risk or analysis_task"`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Observed results:

- risk score contract/design focused tests: 8 passed
- Analysis UI / capability focused tests: 29 passed
- broad Bioinformatics filtered tests: 65 passed
- focused UI workflow tests: 8 passed
- source smoke: passed
- package smoke: passed
- open-W smoke: passed
- codesign: passed

## Issues

Blocker: none.

Major: none.

Minor: B32 still has no persisted user model-spec editor; B33 should define parameter confirmation and saved manifest behavior.

## Conclusion

B32 passes as a non-executing source/contract gate. The next stage should be B33 Risk Score Parameter Confirmation / Result Schema. Risk score execution remains disabled until B34.
