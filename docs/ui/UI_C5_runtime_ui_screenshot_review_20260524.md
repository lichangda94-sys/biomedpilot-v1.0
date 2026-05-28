# UI-C5 Runtime UI Screenshot Review

Date: 2026-05-24

## 1. Scope

This stage captured real source-runtime PySide screenshots for manual UI review.

Strictly not performed:

- no packaging
- no packaged app run
- no `dist/**` modification
- no desktop app overwrite
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no formal executor, report, or export enablement
- no runtime UI code changes

The screenshots were captured from the source app with `QT_QPA_PLATFORM=offscreen` at `1600 x 1000`.

## 2. Screenshot Output

Output directory:

- `docs/ui/runtime_screenshots/20260524/`

Captured screenshots:

| Screenshot | Path | Opened |
|---|---|---|
| Dashboard / 工作台 | `docs/ui/runtime_screenshots/20260524/dashboard_home.png` | yes |
| LabTools 首页 | `docs/ui/runtime_screenshots/20260524/labtools_home.png` | yes |
| LabTools 通用计算器 | `docs/ui/runtime_screenshots/20260524/labtools_general_calculator.png` | yes |
| LabTools 试剂制备 | `docs/ui/runtime_screenshots/20260524/labtools_reagent_preparation.png` | yes |
| LabTools WB Loading | `docs/ui/runtime_screenshots/20260524/labtools_wb_loading.png` | yes |
| LabTools 实验模块边界页 | `docs/ui/runtime_screenshots/20260524/labtools_experiment_boundaries.png` | yes |
| Bioinformatics Project Home | `docs/ui/runtime_screenshots/20260524/bioinformatics_project_home.png` | yes |
| Bioinformatics Data Source | `docs/ui/runtime_screenshots/20260524/bioinformatics_data_source.png` | yes |
| Bioinformatics Analysis Tasks | `docs/ui/runtime_screenshots/20260524/bioinformatics_analysis_tasks.png` | yes |
| Bioinformatics Result / Export | `docs/ui/runtime_screenshots/20260524/bioinformatics_result_export.png` | yes |
| Meta Project Home | `docs/ui/runtime_screenshots/20260524/meta_project_home.png` | yes |
| Meta Question & Type | `docs/ui/runtime_screenshots/20260524/meta_question_type.png` | yes |
| Meta Search Strategy | `docs/ui/runtime_screenshots/20260524/meta_search_strategy.png` | yes |
| Meta Screening / Extraction representative | `docs/ui/runtime_screenshots/20260524/meta_screening_extraction.png` | yes |
| Meta Result / Export Gate | `docs/ui/runtime_screenshots/20260524/meta_result_export.png` | yes |
| Settings | `docs/ui/runtime_screenshots/20260524/settings_home.png` | yes |

## 3. Review Summary

All requested source-runtime screenshots were created and are non-empty PNG files.

No screenshot shows formal computed Bioinformatics or Meta Analysis results, fake forest plot output, report-ready success, or active formal export. LabTools Reagent and WB export affordances reflect the existing file-picker export pilot scope, not formal report export.

Primary UI polish risks:

- Several dense runtime pages require horizontal and vertical scrolling at `1600 x 1000`.
- Meta Analysis target IA and content panels overlap or compress heavily in multiple pages.
- Bioinformatics Analysis Tasks and Report Export pages are readable but table-heavy and scroll-heavy.
- LabTools Reagent Preparation and WB Loading pages are functionally informative but visually dense and cropped in the first viewport.
- Settings first viewport is dominated by raw icon inventory rows; it needs clearer hierarchy for normal users.

## 4. Page Findings

### Dashboard

- Opens successfully.
- Main module cards and sidebar are visible.
- No formal result/report/export issue.
- Needs polish for visual balance, icon scale, and recent-project empty state density.

### LabTools

- Home preserves the three-entry IA.
- General Calculator, Reagent Preparation, WB Loading, and Experiment Module boundary pages open successfully.
- Reagent Preparation and WB Loading show expected adapter/project-context boundaries.
- WB warning state is visible and does not show fake gel bands.
- Layout issue: Reagent and WB pages are too dense for the first viewport and show scroll/cropping pressure.
- No App icon/UI-B10 surface was touched.

### Bioinformatics

- Project Home, Data Source, Analysis Tasks, and Report Export pages open.
- 7-step IA is visible.
- Analysis Tasks shows gate matrix with blocked formal actions.
- Report Export shows disabled DOCX/HTML export state.
- No fake DEG table, plot, formal result, or report-ready package is visible.
- Potential misleading affordance: Report Export currently shows enabled `打开报告文件` / `打开报告文件夹` buttons even though the export gate is disabled and no report is ready. This should be reviewed in a future UI polish pass.

### Meta Analysis

- Project Home, Question & Type, Search Strategy, Full-text/Extraction representative, and Report Export Gate pages open.
- Network Meta remains planned/disabled.
- Report Export Gate shows disabled format buttons and no file-write state.
- No formal pooled effect, forest plot, heterogeneity/publication-bias result, report-ready package, or active export is visible.
- Major layout issue: target IA navigation and page content overlap/compress in the captured source runtime. Meta needs a dedicated layout polish pass before App icon / packaging work is used for visual review.

### Settings

- Settings opens successfully.
- No installation/cloud/model capability appears newly enabled by this screenshot pass.
- Layout issue: icon inventory/status rows dominate the first viewport, making Settings look like a diagnostic dump rather than a user-oriented Settings page.

## 5. Follow-up Recommendations

Recommended next UI work before UI-B10 visual sign-off:

1. UI-C5b Meta runtime layout polish for target IA nav/content overlap.
2. UI-C5c LabTools dense-page polish for Reagent Preparation and WB Loading first viewport.
3. UI-C5d Bioinformatics report/export affordance review, especially enabled open-file/open-folder controls under disabled export gates.
4. UI-C5e Settings hierarchy polish to separate user settings from developer icon inventory.

UI-B10 should remain blocked until these source runtime visuals are manually reviewed and the existing App icon packaging readiness decisions are resolved.

## 6. Verification

Commands/checks run:

- Source runtime screenshot capture with `QT_QPA_PLATFORM=offscreen`
- Screenshot existence check: 16 expected PNG files present
- Screenshot non-empty image check: all screenshots are `1600 x 1000`, non-empty, and non-blank
- CSV structure check: `docs/ui/UI_C5_runtime_screenshot_manifest_20260524.csv`
- `python3 -m app.main --smoke-test`
- `git diff --check`
- `git diff --cached --check`

No package smoke, packaged app runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
