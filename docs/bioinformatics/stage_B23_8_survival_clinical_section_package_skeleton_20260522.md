# Bioinformatics B23.8 Survival / Clinical Section-Only Report Package Skeleton

Date: 2026-05-22

## Scope

B23.8 adds section-only report package skeletons for KM/log-rank and Cox univariate outputs.

The package writers run only after the B23.7 section report-ready gate passes. They do not enable the full integrated report export and do not generate clinical diagnosis, prognosis, treatment recommendation, or validated risk score interpretation.

## Implemented Files

- `app/bioinformatics/reports/survival_clinical.py`
- `app/bioinformatics/reports/__init__.py`
- `tests/bioinformatics/test_survival_clinical_report_ready_gate.py`
- `docs/bioinformatics/stage_B23_8_survival_clinical_section_package_skeleton_20260522.md`

## New APIs

- `create_km_logrank_report_ready_package(project_root, result_id=None, allow_table_only_report=False)`
- `create_cox_report_ready_package(project_root, result_id=None, allow_table_only_report=False)`

The existing gates now expose `package_creation_enabled=True` when they reach:

- `eligible_for_km_logrank_report_ready`
- `eligible_for_cox_report_ready`

## Package Layout

Packages are written under:

- `survival_clinical_report_package/survival_km_logrank_only/<timestamp>_<result_id>/`
- `survival_clinical_report_package/cox_univariate_only/<timestamp>_<result_id>/`

Required layout:

- section report markdown
- `README_limitations.md`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`

Required manifests:

- `gate_snapshot.json`
- `result_index_snapshot.json`
- `source_result_entry.json`
- `parameters_manifest.json`
- `dependency_snapshot.json`
- `table_validation.json`
- `plot_artifacts.json`
- `warnings_limitations.json`
- `package_inventory.json`
- `provenance/provenance.json`

## Result Index Write-Back

After package creation, the source result is updated with:

- `report_ready_eligible=True`
- a section-only `report_artifacts` entry

Allowed section scopes:

- `survival_km_logrank_only`
- `cox_univariate_only`

These scopes remain section-only and are explicitly not full integrated report scopes.

## Full Integrated Boundary

B23.8 does not remove the full integrated report blockers:

- `survival_clinical_report_ready_not_implemented`
- `full_integrated_report_export_not_enabled_in_b23_1`

The full integrated prerequisite gate still blocks section-only package substitution with:

- `full_integrated_prerequisite_forbids_section_package_as_full_report:<section>`

## Preserved Boundaries

- No full integrated report package is enabled.
- No Cox multivariate report-ready package is enabled.
- No clinical conclusion, prognosis, treatment recommendation, or validated risk score is generated.
- No imported/testing/exploratory/preflight source can create a section package.
- No dependency installation action is added.

## Validation

Focused validation completed:

- `python3 -m py_compile app/bioinformatics/reports/survival_clinical.py app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_survival_clinical_report_ready_gate.py tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_integrated_report_package.py -q`
  - 18 passed

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "survival_clinical_report_ready or integrated or report or km or cox or survival or clinical or plot or analysis_ui"`
  - 207 passed, 444 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task or survival or cox"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 651 passed
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

B23.8 enables audited section-only KM/log-rank and Cox univariate package skeletons after their report-ready gates pass. These packages write stable manifests and result-index section artifacts, but they remain distinct from full integrated report export.
