# UI-D6 Runtime Screenshot Re-review

Date: 2026-05-26

## 1. Scope

This stage recaptures source-runtime PySide screenshots after UI-D2 through UI-D5 rebuilt Dashboard, Settings, LabTools, Bioinformatics, and Meta surfaces with the D1 shared workbench component system.

Strictly not performed:

- no packaging
- no packaged app run
- no `dist/**` modification
- no desktop app overwrite
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no executor enablement
- no report generation
- no formal export enablement
- no external engine install, download, upload, update, or cloud configuration

## 2. Screenshot Set

All screenshots were captured from source runtime with `QT_QPA_PLATFORM=offscreen` at `1600 x 1000` into:

`docs/ui/runtime_screenshots/20260526_d6_runtime_review/`

Captured files:

- `dashboard_home.png`
- `labtools_home.png`
- `labtools_general_calculator.png`
- `labtools_reagent_preparation.png`
- `labtools_wb_loading.png`
- `labtools_experiment_boundaries.png`
- `bioinformatics_project_home.png`
- `bioinformatics_data_source.png`
- `bioinformatics_analysis_tasks.png`
- `bioinformatics_result_export.png`
- `meta_project_home.png`
- `meta_question_type.png`
- `meta_search_strategy.png`
- `meta_screening_extraction.png`
- `meta_result_export.png`
- `settings_home.png`

All 16 screenshots are non-empty, non-blank PNG files.

## 3. Re-review Summary

Improved since UI-C5g:

- Dashboard and Settings now use the D2 rebuilt shell and shared component hierarchy.
- LabTools Reagent and WB pages now show shared dense workbench structure, preview cards, and clearer non-formal preview semantics from UI-D3.
- Bioinformatics now shows shared workflow stepper, gated preview cards, plot placeholder, and export gate panel from UI-D4.
- Meta now shows shared workflow stepper, reference queue, extraction table, non-formal preview card, plot placeholder, and export gate panel from UI-D5.

Remaining visual risks:

- LabTools Reagent and WB are still dense operational pages and should receive human product review against the high-fidelity mockups.
- Bioinformatics Analysis Tasks remains table-heavy; the gate semantics are clearer, but the page still needs visual density review.
- Meta Full-text / Extraction remains dense and should be reviewed separately from Screening if a finer product review is requested.
- Dashboard and Settings are more consistent with the shared system but still require final product-owner acceptance before icon/package work.

## 4. Gate Review

No screenshot shows intentionally enabled formal result/report/export behavior:

- Bioinformatics formal DEG / ORA / GSEA / KM / Cox / survival remain disabled or gated.
- Bioinformatics report/export remains disabled.
- Meta Pairwise Meta, Network Meta, pooled effects, forest plot output, report-ready package, and export remain disabled.
- LabTools PDF / DOCX report export remains disabled.
- Settings external install/update/cloud/model actions remain disabled or detect-first.

## 5. UI-B10 Decision

Do not enter UI-B10 automatically from UI-D6.

Reason:

- UI-D6 proves the rebuilt source runtime can be captured and reviewed consistently.
- It does not prove final visual acceptance. Dense LabTools/Bio/Meta pages still need human screenshot review before App icon, packaging, Finder, `Info.plist`, LaunchServices, or packaged runtime work should begin.

Recommended next step:

- Human review of `docs/ui/runtime_screenshots/20260526_d6_runtime_review/`.
- If accepted, proceed to a scoped UI-B10 plan.
- If not accepted, run targeted polish only for the rejected pages.

## 6. Verification

Verification performed:

- 16 screenshot files exist, are non-empty, and are non-blank.
- `docs/ui/UI_D6_runtime_screenshot_manifest_20260526.csv` is complete with 16 rows.
- Source runtime smoke passes.
- Focused UI tests pass.
- `git diff --check` passes.
- `git diff --cached --check` passes before commit.

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
