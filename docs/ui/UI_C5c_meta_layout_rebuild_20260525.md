# UI-C5c Meta Layout Rebuild

Date: 2026-05-25

## 1. Scope

This stage rebuilds the Meta Analysis runtime layout skeleton on top of the shared Workbench layout primitives introduced in UI-C5b.

Strictly not performed:

- no Meta executor enablement
- no Pairwise Meta enablement
- no Network Meta enablement
- no Chinese database direct retrieval
- no Chinese PDF extraction
- no formal pooled effect
- no forest plot generation
- no heterogeneity or publication-bias result generation
- no report-ready package
- no DOCX / HTML / PDF / CSV / XLSX / ZIP export enablement
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no packaging or packaged app run

## 2. Changes

The previous Meta C5b polish reduced overlap by introducing a target runtime stack. This C5c stage keeps that stack and moves the outer skeleton to shared Workbench primitives:

- `metaTargetIAShell` now uses `uiPrimitive=workbench_shell`.
- `metaWorkflowNavigationPanel` now uses `uiPrimitive=workbench_secondary_nav`.
- `metaRuntimeContentPanel` now uses `uiPrimitive=workbench_content_panel`.
- `resultReportExportAdoptionPanel` remains the gated right-side panel and carries `uiPrimitive=workbench_right_gate_panel`.
- Existing target IA object names and properties are preserved for compatibility:
  - `metaTargetIANavItem`
  - `metaRuntimeContentPanel`
  - `metaTargetRuntimeStack`
  - `resultReportExportAdoptionPanel`

No page key, navigation key, or gate semantic was changed.

## 3. Preserved Gates

- `Network Meta` remains `planned_disabled`.
- `resultSemanticKey` remains non-formal.
- `reportStatusKey` remains draft / not ready.
- `exportGate` remains `disabled_empty_result`.
- `fileWriteAllowed=false` remains enforced on export-gated buttons.
- Shared Result / Report / Export adoption panel remains hidden outside `result_report` and `report_export`.

## 4. Screenshots

New source-runtime screenshots were captured under:

- `docs/ui/runtime_screenshots/20260525_c5c_meta_layout_rebuild/meta_project_home.png`
- `docs/ui/runtime_screenshots/20260525_c5c_meta_layout_rebuild/meta_question_type.png`
- `docs/ui/runtime_screenshots/20260525_c5c_meta_layout_rebuild/meta_search_strategy.png`
- `docs/ui/runtime_screenshots/20260525_c5c_meta_layout_rebuild/meta_screening_extraction.png`
- `docs/ui/runtime_screenshots/20260525_c5c_meta_layout_rebuild/meta_result_export.png`

All five screenshots are non-empty PNG files. The captured widget height is larger than the requested 1000 px because the current Meta page stack still has minimum content height pressure; this remains acceptable for C5c skeleton migration but should be reviewed again during C5g.

## 5. Verification

Commands/checks run:

- `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py tests/ui/test_meta_analysis_result_report_export_gates.py tests/ui/test_meta_analysis_runtime_layout_polish.py tests/ui/test_workbench_layout_primitives.py`
  - Result: 32 passed
- `python3 -m app.main --smoke-test`
  - Result: passed
- Meta screenshot generation
  - Result: 5 non-empty PNG files created

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
