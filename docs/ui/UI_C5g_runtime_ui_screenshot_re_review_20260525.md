# UI-C5g Runtime Screenshot Re-review

Date: 2026-05-25

## 1. Scope

This stage recaptures source-runtime PySide screenshots after the UI-C5b through UI-C5f layout and affordance work.

Strictly not performed:

- no packaging
- no packaged app run
- no `dist/**` modification
- no desktop app overwrite
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no new business feature
- no formal executor / formal result / report-ready package / export enablement

## 2. Screenshot Set

All screenshots were captured from source runtime into:

`docs/ui/runtime_screenshots/20260525_c5g_runtime_review/`

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

All 16 screenshots are `1600 x 1000`, non-empty PNG files.

## 3. Re-review Summary

Improved since UI-C5 baseline:

- Meta target IA navigation/content overlap is resolved by the C5c Workbench skeleton.
- LabTools Reagent and WB pages no longer use the most fragile four-column layout.
- Bioinformatics Result / Report and Report Export no longer expose misleading open-file/open-folder affordances while formal result/report gates are blocked.
- Settings first viewport no longer shows the full icon/resource diagnostics inventory by default.

Remaining visual risks:

- LabTools Reagent and WB remain dense operational pages and need human visual review against the high-fidelity mockups.
- Bioinformatics Analysis Tasks remains table-heavy.
- Meta Full-text / Extraction remains dense and should be reviewed separately from Screening in a future screenshot pass if product review requires more precision.
- Dashboard and General Calculator are usable but still not fully mockup-aligned.

## 4. Gate Review

No screenshot shows intentionally enabled formal result/report/export behavior:

- Bioinformatics formal DEG / ORA / GSEA / KM / Cox / survival remain disabled or gated.
- Bioinformatics report/export remains disabled.
- Meta executor, Pairwise Meta, Network Meta, pooled effect, forest plot, report-ready package, and export remain disabled.
- LabTools PDF / DOCX remains disabled.
- Settings external install/update/cloud/model actions remain disabled or detect-first.

## 5. UI-B10 Decision

Do not enter UI-B10 automatically from this stage.

Reason:

- C5g proves the source runtime is screenshot-capable and that the worst overlap/misleading affordance issues have been reduced.
- It does not prove final visual acceptance. Dense LabTools/Bio/Meta pages still need human screenshot review before App icon, packaging, Finder, Info.plist, LaunchServices, or packaged runtime work should begin.

Recommended next step:

- Human review of `docs/ui/runtime_screenshots/20260525_c5g_runtime_review/`.
- If accepted, proceed to a scoped UI-B10 plan.
- If not accepted, run a targeted C5h polish pass for the specific rejected pages only.

## 6. Verification

Verification performed:

- 16 screenshot files exist and are non-empty.
- `docs/ui/UI_C5g_runtime_screenshot_manifest_20260525.csv` is complete with 16 rows.

Final validation commands are recorded in the implementation turn and should pass before commit:

- focused UI tests across Workbench, Meta, LabTools, Bioinformatics, and Settings
- `python3 -m app.main --smoke-test`
- `git diff --check`
- `git diff --cached --check`

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
