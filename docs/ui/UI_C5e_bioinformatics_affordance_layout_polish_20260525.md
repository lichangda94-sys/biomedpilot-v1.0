# UI-C5e Bioinformatics Affordance / Layout Polish

Date: 2026-05-25

## 1. Scope

This stage polishes Bioinformatics gated runtime surfaces identified by UI-C5a, focusing on misleading affordances in Result / Report and Report Export and adding stable Workbench-level layout markers to dense gated pages.

Strictly not performed:

- no formal DEG executor enablement
- no ORA / GSEA executor enablement
- no KM / Cox / survival executor enablement
- no fake DEG table, fake plot, formal result, report-ready package, or export
- no DOCX / HTML / PDF / CSV / XLSX export enablement
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no packaging or packaged app run

## 2. Changes

### Analysis Tasks

- `bioinformaticsAnalysisTaskCenterPage` now carries:
  - `uiPrimitive=workbench_gated_page`
  - `layoutPolishNoOverlap=true`
  - `formalActionEnabled=false`
- `bioinformaticsAnalysisTaskGateCard` now carries:
  - `uiPrimitive=workbench_section`
  - `layoutPolishNoOverlap=true`

No task action changed from disabled/gated to enabled.

### Result & Report

The previously visible "open result folder" and "open parameter JSON" controls could read as available result artifacts even when no formal result exists. They are now explicitly gated:

- `bioinformaticsOpenResultFolderGatedButton`
- `bioinformaticsOpenResultParamsGatedButton`

Both are disabled and carry `disabledState=formal_result_missing`.

### Report Export

The previously visible "open report file" and "open report folder" controls could read as available report artifacts even when report-ready is blocked. They are now explicitly gated:

- `bioinformaticsOpenReportFileGatedButton`
- `bioinformaticsOpenReportFolderGatedButton`

Both are disabled and carry `disabledState=report_not_ready`.

## 3. Preserved Gates

- `formalActionEnabled=false` remains on formal analysis/report/export actions.
- `resultSemanticKey` remains non-formal / preflight-only.
- `reportStatusKey` remains draft / not ready.
- `exportGate` remains `disabled_missing_report_ready`.
- Existing Result & Report and Report Export pages remain separate IA nodes.

## 4. Screenshots

New source-runtime screenshots were captured under:

- `docs/ui/runtime_screenshots/20260525_c5e_bioinformatics_polish/bioinformatics_project_home.png`
- `docs/ui/runtime_screenshots/20260525_c5e_bioinformatics_polish/bioinformatics_data_source.png`
- `docs/ui/runtime_screenshots/20260525_c5e_bioinformatics_polish/bioinformatics_analysis_tasks.png`
- `docs/ui/runtime_screenshots/20260525_c5e_bioinformatics_polish/bioinformatics_result_export.png`

All four screenshots are `1600 x 1000`, non-empty PNG files.

## 5. Verification

Commands/checks run:

- `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py tests/ui/test_bioinformatics_analysis_tasks_gated_page.py tests/ui/test_bioinformatics_result_report_export_split_pages.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_bioinformatics_workflow_pages.py`
  - Result: 125 passed
- `python3 -m app.main --smoke-test`
  - Result: passed
- Bioinformatics screenshot generation
  - Result: 4 non-empty PNG files created

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
