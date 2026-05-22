# Bioinformatics B23.3 Full Integrated Report UI Preview and Disabled Reasons

Date: 2026-05-22

## Scope

B23.3 exposes the B23 full integrated report gate and package skeleton in the user UI without enabling full integrated report export.

The implementation adds a visible Results Browser preview for:

- full integrated report gate status
- package layout plan
- section coverage
- disabled reasons
- export format gate

## Implemented Files

- `app/bioinformatics/workflow_pages.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B23_3_full_integrated_report_ui_preview_disabled_reasons_20260522.md`

## UI Behavior

Results Browser now includes `Full integrated report preview`.

Visible controls:

- format selector: `markdown`, `pdf`, `docx`
- disabled `Generate full integrated report package` button unless B23 gate passes
- status label with explicit blockers
- package plan table
- section coverage table

Object names:

- `fullIntegratedReportFormat`
- `fullIntegratedReportButton`
- `fullIntegratedReportStatus`
- `fullIntegratedReportPlanTable`
- `fullIntegratedReportSectionTable`

## Disabled Reasons

Current runtime is expected to display:

- `survival_clinical_report_ready_not_implemented`
- missing section blockers when section results do not exist
- blocked package plan status

PDF/DOCX remain blocked through the package skeleton format gate. No renderer is invoked.

## Package Preview

The UI shows the planned package layout:

- `report_package/integrated/<timestamp>_<project_name>`
- `integrated_report.md`
- `sections/`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`
- `README_limitations.md`

The preview is read-only when the gate is blocked.

## Preserved Boundaries

- No full integrated report package is generated from real current project state.
- Section-only DEG/ORA/GSEA packages remain separate.
- KM/Cox real plot artifacts do not enable survival/clinical report-ready.
- Imported/testing/exploratory/preflight results remain excluded from formal integrated report sections.
- No clinical diagnosis, prognosis, treatment recommendation, or risk score interpretation is produced.
- No PDF/DOCX renderer is activated.
- No dependency installation action is added.

## Validation

Focused validation completed:

- `python3 -m py_compile app/bioinformatics/workflow_pages.py`
  - passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "formal_deg_report_ready_package_gate"`
  - 1 passed, 111 deselected

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or formal_deg or ora or gsea or survival or cox or plot or analysis_ui or capability_map"`
  - 247 passed, 390 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 637 passed
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

B23.3 makes full integrated report readiness visible and auditable in the UI while keeping export blocked until the B23 gate can pass in a later audited stage.
