# Bioinformatics UI-C2f Result & Report / Report Export Split Pages

## 1. Scope

This stage implements the gated split between Bioinformatics step 6 and step 7 in the PySide UIShell:

- Step 6: `Result & Report / 结果与报告`
- Step 7: `Report Export / 报告导出`

The implementation is limited to layout, read-only gate previews, preflight log / empty result state, report draft boundary, and disabled export gate controls.

## 2. Business Logic Boundary

This stage does not enable:

- formal DEG executor
- ORA / GSEA executor
- KM / log-rank / Cox / survival executor
- formal computed result generation
- fake DEG tables
- volcano / heatmap / enrichment / survival plots
- report-ready package generation
- DOCX / HTML / PDF generation
- CSV / XLSX export
- packaged app runtime or UI-B10 icon / LaunchServices work

Existing direct legacy report methods remain available for older tests, but visible UI actions remain disabled and gated.

## 3. Result & Report Page

`BioinformaticsResultsBrowserWidget` now presents the step 6 page as a result/report gate boundary.

Added or updated UI surfaces:

- `bioinformaticsResultReportGateTable`
- `bioinformaticsPreflightLogPreview`
- `bioinformaticsResultGatePreview`
- `bioinformaticsAddToReportDisabledButton`
- `bioinformaticsResultReportGenerateReportDisabledButton`

The page shows:

- formal result missing
- `resultSemanticKey` from the gate model, with preflight log explicitly marked `preflight_only`
- `reportStatusKey=report.status.draft`
- `exportGate=disabled_missing_report_ready`
- no fake result table or fake plot
- imported/testing/preflight outputs remain non-formal

`Add to Report` and `Generate Report` are disabled. Imported DEG preview remains visible only as an imported external/testing preview surface and is not promoted to `formal_computed_result`.

## 4. Report Export Page

`BioinformaticsReportViewerWidget` now presents the step 7 page as an export gate boundary.

Added or updated UI surfaces:

- `bioinformaticsReportExportGatePreview`
- `bioinformaticsReportExportFormatGateTable`
- `bioinformaticsReportExportFormatDisabledButton`
- existing `bioinformaticsGenerateReportDisabledButton`
- existing `bioinformaticsReportExportDisabledButton`

Format readiness is shown as:

- DOCX: disabled
- HTML: disabled
- PDF: disabled / future
- CSV: disabled because formal result is missing
- XLSX: disabled because formal result is missing

Gate reasons are visible:

- formal result missing
- report not ready
- export adapter not connected

All export controls remain disabled and do not write files.

## 5. Gate Semantics Preserved

The split preserves the UI-C2b gate model:

- `result_gate.fake_result_allowed=false`
- `result_gate.fake_plot_allowed=false`
- `result_gate.result_semantic_key` is not `result.semantic.formal_computed_result`
- `report_gate.report_ready_package_allowed=false`
- `report_gate.report_status_key=report.status.draft`
- `export_gate.export_enabled=false`
- `export_gate.export_gate=disabled_missing_report_ready`

Preflight, testing, and imported outputs do not become formal results.

## 6. Tests Added

Added focused test file:

- `tests/ui/test_bioinformatics_result_report_export_split_pages.py`

Coverage:

- step 6 and step 7 remain separate 7-step IA nodes
- Result & Report page is preflight/draft only
- Add to Report and Generate Report are disabled
- Report Export page has DOCX / HTML / PDF / CSV / XLSX disabled
- export gate remains disabled
- no report/export files are written by page refresh
- gate state does not become formal result or report-ready

## 7. Verification

Commands run:

```bash
python3 -m pytest -q tests/ui/test_bioinformatics_result_report_export_split_pages.py
python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py
python3 -m pytest -q tests/ui/test_bioinformatics_analysis_tasks_gated_page.py
python3 -m pytest -q tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py
python3 -m pytest -q tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py
python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py
python3 -m pytest -q tests/shared/test_result_report_export_shell.py
python3 -m app.main --smoke-test
git diff --check
```

Results:

- `tests/ui/test_bioinformatics_result_report_export_split_pages.py`: passed
- `tests/ui/test_bioinformatics_gate_shell.py`: passed
- `tests/ui/test_bioinformatics_analysis_tasks_gated_page.py`: passed
- `tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py`: passed
- `tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py`: passed after restoring legacy-compatible status keywords
- `tests/ui/test_bioinformatics_ia_shell.py`: passed
- `tests/shared/test_result_report_export_shell.py`: passed
- `python3 -m app.main --smoke-test`: passed
- `git diff --check`: passed

`git diff --cached --check` is run after staging the scoped C2f files.

## 8. Files Changed

- `app/bioinformatics/workflow_pages.py`
- `tests/ui/test_bioinformatics_result_report_export_split_pages.py`
- `docs/ui/UI_C2f_bioinformatics_result_report_export_split_pages_20260522.md`

## 9. Not Modified

This stage did not modify:

- `assets/**`
- `scripts/**`
- `dist/**`
- App icon / Finder icon / `.icns` / iconset
- `Info.plist`
- LaunchServices / packaged app entry

No packaged app was run.
