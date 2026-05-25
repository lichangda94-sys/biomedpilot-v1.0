# Bioinformatics B28 Cox Multivariate Review / Report-Ready Integration

Date: 2026-05-25

## Scope

B28 integrates B20 controlled multivariate Cox results into the review and section report-ready package layer.

Implemented scope:

- Multivariate Cox result review and table export.
- Cox section report-ready gate accepts either Cox univariate or Cox multivariate formal results.
- Multivariate Cox section package with `section_scope=cox_multivariate_only`.
- Full integrated prerequisite validation accepts a valid Cox multivariate section-only package for the Cox section.
- Analysis UI copy clarifies Cox section package supports univariate or multivariate Cox.

Out of scope:

- No risk score.
- No nomogram.
- No prognosis label.
- No treatment recommendation.
- No clinical conclusion.
- No automatic variable selection.
- No full integrated report export unlock by Cox alone.

## Review Contract

Added multivariate review APIs:

- `build_cox_multivariate_result_review(...)`
- `export_cox_multivariate_review_table(...)`

The review shows:

- covariate count
- sample count
- event count
- significant covariate count
- HR / CI / p-value rows
- adjustment policy
- engine/version
- dependency snapshot
- guard copy

The export writes only the multivariate Cox table fields and does not include risk score, clinical risk group, prognosis, or treatment recommendation.

## Report-Ready Gate

`evaluate_cox_report_ready_gate(...)` now selects:

- `cox_univariate` -> existing univariate gate
- `cox_multivariate` -> new multivariate gate

The multivariate gate requires:

- `result_semantics=formal_computed_result`
- `task_type=cox_multivariate`
- dependency snapshot passed
- validation passed/warning
- no source blockers
- parameters manifest
- task-run log
- `cox_multivariate_result_table`
- table/schema validation
- formal Cox forest plot artifact or explicit table-only mode
- no forbidden clinical conclusion text

Passing status remains `eligible_for_cox_report_ready`, with schema:

- `biomedpilot.cox_multivariate_report_ready_gate.v1`

## Package Contract

`create_cox_report_ready_package(...)` now writes either:

- `cox_univariate_only`
- `cox_multivariate_only`

For multivariate Cox, package files include:

- `cox_multivariate_report.md`
- `tables/cox_mv.tsv`
- `manifests/gate_snapshot.json`
- `manifests/source_result_entry.json`
- `manifests/parameters_manifest.json`
- `manifests/dependency_snapshot.json`
- `manifests/table_validation.json`
- `manifests/plot_artifacts.json`
- `manifests/warnings_limitations.json`
- `provenance/provenance.json`
- `README_limitations.md`

The package sets:

- `clinical_conclusion_enabled=False`
- `full_integrated_report_enabled=False`
- `report_ready_eligible=True` only after the B28 Cox section package is created
- `report_artifacts[].section_scope=cox_multivariate_only`

## Integrated Report Boundary

The full integrated gate can treat a validated `cox_multivariate_only` package as satisfying the Cox section prerequisite.

This does not by itself enable full integrated export. Missing DEG/ORA/GSEA/KM sections, renderer gates, or other prerequisites still block full integrated report export.

## UI Boundary

UI copy now says Cox section package accepts formal Cox univariate or multivariate results. The generated package message still says:

- section-only
- no full integrated report
- no risk score
- no prognosis
- no treatment advice

## Tests

Commands run during implementation:

```text
python3 -m py_compile app/bioinformatics/reports/survival_clinical.py app/bioinformatics/reports/integrated.py app/bioinformatics/survival_clinical/cox_review.py app/bioinformatics/survival_clinical/cox_multivariate_result_schema.py
python3 -m pytest tests/bioinformatics/test_cox_multivariate_review_report_ready.py tests/bioinformatics/test_cox_multivariate_result_schema.py tests/bioinformatics/test_survival_clinical_report_ready_gate.py tests/bioinformatics/test_integrated_report_gate.py -q
python3 -m pytest tests/bioinformatics -q -k "cox or survival_clinical or integrated or report or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "survival or cox or report or analysis_task or results_browser"
git diff --check
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Results:

- compile: passed
- focused Cox/report/integrated tests: 18 passed
- broad bioinformatics tests: 158 passed, 551 deselected
- focused UI workflow tests: 20 passed, 96 deselected
- `git diff --check`: passed
- full bioinformatics tests: 709 passed, 1 scipy precision warning
- full UI tests: 273 passed
- source smoke: passed
- package smoke: passed
- open-W packaged smoke: passed
- codesign verify: passed

## Conclusion

B28 connects B20 multivariate Cox to review and section package workflows while preserving strict clinical boundaries. Cox multivariate can now become a section-ready package, but it remains a statistical research section only and does not activate risk score, nomogram, clinical conclusions, or full integrated report export by itself.
