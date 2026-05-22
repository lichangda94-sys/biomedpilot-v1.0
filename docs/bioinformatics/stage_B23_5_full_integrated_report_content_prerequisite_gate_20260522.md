# Bioinformatics B23.5 Full Integrated Report Content Prerequisite Gate

Date: 2026-05-22

## Scope

B23.5 hardens the full integrated report content gate by making section-level prerequisites explicit and reviewable.

This stage does not enable full integrated report export. It does not implement survival/clinical report-ready, and it does not treat section-only packages as a completed full integrated report.

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_integrated_report_gate.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B23_5_full_integrated_report_content_prerequisite_gate_20260522.md`

## Prerequisite Matrix

`evaluate_full_integrated_report_gate` now returns:

- `prerequisite_rows`
- `prerequisite_summary`
- `survival_clinical_report_ready_required`
- `export_activation_status`

Each prerequisite row records:

- section id and label
- required result semantics
- observed result semantics
- result index v2 status
- validation status
- dependency status
- task-run log status
- source table status
- plot requirement
- plot artifact status
- section report-ready status
- section report-ready schema
- section package scope
- registered report scopes
- full integrated scope requirement
- whether section-only package is sufficient
- disabled reason and blockers

## Required Sections

The full integrated report still requires all five sections:

- formal DEG
- ORA enrichment
- preranked GSEA
- KM/log-rank survival
- Cox clinical association

Each section must remain `formal_computed_result`, passed/warning validation, passed dependency snapshot, present source table, present task-run log, and passed section report-ready gate.

## Survival / Clinical Boundary

KM/log-rank and Cox sections are still blocked by:

- `survival_clinical_report_ready_not_implemented`
- `full_integrated_prerequisite_survival_clinical_report_ready_missing:<section>`

Real KM/Cox plot artifacts remain insufficient to enable survival/clinical report-ready or full integrated export.

## Section-Only Package Boundary

Registered section-only report scopes such as `formal_deg_only`, `formal_ora_only`, and `formal_gsea_only` are now explicitly marked as not sufficient for full integrated report completion.

The gate blocks section-only package substitution with:

- `full_integrated_prerequisite_forbids_section_package_as_full_report:<section>`

## UI Changes

The Results Browser full integrated report preview now includes:

- `prerequisite_summary` in the package plan table
- a `Prerequisite` column in the section coverage table

The user can see that the full integrated report is blocked because the section content prerequisites are not complete, not because the export button is hidden.

## Preserved Boundaries

- No full integrated report export is enabled.
- No survival/clinical report-ready gate is implemented.
- No clinical diagnosis, prognosis, treatment recommendation, or risk score interpretation is generated.
- No PDF/DOCX renderer is invoked.
- No GSEA, survival, clinical statistics, or report-ready scope is expanded.
- Imported/testing/exploratory/preflight results remain excluded.

## Validation

Focused validation completed:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/workflow_pages.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py -q`
  - 13 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "formal_deg_report_ready_package_gate"`
  - 1 passed, 111 deselected

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or formal_deg or ora or gsea or survival or cox or plot or analysis_ui or capability_map"`
  - 252 passed, 390 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 642 passed
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

B23.5 makes full integrated report content readiness auditable at the section prerequisite level. Export remains blocked until all required sections, including survival/clinical report-ready, can satisfy the full integrated report content gate and the renderer gate.
