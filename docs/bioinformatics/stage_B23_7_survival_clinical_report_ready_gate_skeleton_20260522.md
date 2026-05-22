# Bioinformatics B23.7 Survival / Clinical Report-Ready Gate Skeleton

Date: 2026-05-22

## Scope

B23.7 adds gate-only skeletons for KM/log-rank and Cox univariate section report-ready checks.

This stage does not create survival/clinical report packages and does not enable the full integrated report export.

## Implemented Files

- `app/bioinformatics/reports/survival_clinical.py`
- `app/bioinformatics/reports/__init__.py`
- `app/bioinformatics/reports/integrated.py`
- `tests/bioinformatics/test_survival_clinical_report_ready_gate.py`
- `docs/bioinformatics/stage_B23_7_survival_clinical_report_ready_gate_skeleton_20260522.md`

## New APIs

- `evaluate_km_logrank_report_ready_gate(project_root, result_id=None, allow_table_only_report=False)`
- `evaluate_cox_report_ready_gate(project_root, result_id=None, allow_table_only_report=False)`

The gates read from result index v2 and registered artifacts only. They do not execute KM/Cox, do not render plots, do not write section packages, and do not set `report_ready_eligible=True`.

## KM/log-rank Gate

The KM gate requires:

- `task_type=survival_km_logrank`
- `result_semantics=formal_computed_result`
- passed dependency snapshot
- passed/warning validation status
- no source blockers
- parameters manifest with survival input, outcome gate, time/event fields, grouping rule, group labels, censoring policy, and missingness policy
- registered `km_curve_table`
- registered `logrank_result_table`
- present task-run log artifact
- KM/log-rank result schema validation
- KM/log-rank table validation
- formal KM plot artifact, unless explicit table-only mode is requested
- no clinical conclusion/prognosis/treatment recommendation/risk-score text

Passing status:

- `eligible_for_km_logrank_report_ready`

## Cox Gate

The Cox gate requires:

- `task_type=cox_univariate`
- `result_semantics=formal_computed_result`
- passed dependency snapshot
- passed/warning validation status
- no source blockers
- parameters manifest with survival input, outcome gate, time/event fields, covariate, covariate type, missing value policy, and minimum event policy
- registered `cox_result_table`
- present task-run log artifact
- Cox result schema validation
- Cox result table validation
- formal Cox plot artifact, unless explicit table-only mode is requested
- no Cox multivariate substitution
- no clinical conclusion/prognosis/treatment recommendation/risk-score text

Passing status:

- `eligible_for_cox_report_ready`

## Full Integrated Gate Integration

`evaluate_full_integrated_report_gate` now calls the real KM and Cox section gates instead of placeholder gates.

The full integrated report remains blocked because:

- B23.7 does not implement section package creation.
- section-only scopes are not full integrated report scopes.
- the existing full integrated export activation blocker remains in place.

Expected blockers can still include:

- `survival_clinical_report_ready_not_implemented`
- `full_integrated_report_export_not_enabled_in_b23_1`
- `full_integrated_prerequisite_forbids_section_package_as_full_report:<section>`

## Preserved Boundaries

- No survival/clinical report package is written.
- No full integrated report package is enabled.
- No clinical diagnosis, prognosis, treatment recommendation, or validated risk score is generated.
- No Cox multivariate report-ready activation.
- No dependency auto-install.
- Imported/testing/exploratory/preflight sources are blocked.

## Validation

Focused validation completed:

- `python3 -m py_compile app/bioinformatics/reports/survival_clinical.py app/bioinformatics/reports/integrated.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_survival_clinical_report_ready_gate.py tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_integrated_report_package.py -q`
  - 15 passed
- `python3 -m pytest tests/bioinformatics/test_km_result_schema.py tests/bioinformatics/test_cox_result_schema.py tests/bioinformatics/test_km_plot_artifact.py tests/bioinformatics/test_cox_plot_artifact.py -q`
  - 8 passed

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "survival_clinical_report_ready or integrated or report or km or cox or survival or clinical or plot or analysis_ui"`
  - 204 passed, 444 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task or survival or cox"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 648 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 269 passed
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Conclusion

B23.7 replaces the survival/clinical placeholder section gates with auditable KM and Cox gate-only checks. The gates can prove section readiness, but package creation and full integrated export remain blocked for later audited stages.
