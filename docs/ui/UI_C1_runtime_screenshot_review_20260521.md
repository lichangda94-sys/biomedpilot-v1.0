# UI-C1 Runtime Screenshot Review

## 1. Scope

- Review date: 2026-05-21
- Source runtime: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- Concept image folder: `/Users/changdali/Desktop/UI/界面示意图`
- Runtime screenshot output: `docs/ui/runtime_screenshots/UI_C1_20260521/`
- This review used source PySide runtime screenshots only. It did not run the packaged app, repackage the app, replace active icons/assets, touch App icon/Finder icon/Info.plist icon binding/LaunchServices, or overwrite any desktop `.app`.

## 2. Concept Inputs

| Concept | Runtime screenshot |
| --- | --- |
| IMG-01 Welcome / 欢迎页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-01_welcome_runtime.png` |
| IMG-02 Dashboard / 工作台首页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-02_dashboard_runtime.png` |
| IMG-03 Settings / 设置中心 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-03_settings_runtime.png` |
| IMG-04 LabTools / 实验工具首页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-04_labtools_home_runtime.png` |
| IMG-05 Bioinformatics 首页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-05_bioinformatics_home_runtime.png` |
| IMG-06 Meta Question & Type | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-06_meta_question_type_runtime.png` |
| IMG-07 Bio Data Source | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-07_bio_data_source_runtime.png` |
| IMG-08 Bio Data Check & Preparation | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-08_bio_data_check_preparation_runtime.png` |
| IMG-09 Meta Search Strategy | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-09_meta_search_strategy_runtime.png` |
| IMG-10 Bio Result & Report | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-10_bio_result_report_runtime.png` |
| IMG-11 Bio Group & Design | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-11_bio_group_design_runtime.png` |
| IMG-12 Meta Full-text Management | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-12_meta_fulltext_management_runtime.png` |
| IMG-13 Meta Extraction Form Design | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-13_meta_extraction_form_design_runtime.png` |

## 3. Review Results

| Area | Result | Notes |
| --- | --- | --- |
| Welcome | Pass for UI-C1 shell review | Brand welcome direction is present. High-fidelity brand art and active App icon remain out of scope until later resource stages. |
| Dashboard | Pass | Dashboard keeps three module entries and recent projects. The prior bottom explanatory strip is not present. |
| Settings | Pass | Settings keeps second-level navigation, external capability status cards, detect-first posture, and developer diagnostics folding. |
| LabTools Home | Pass | LabTools home shows only the three first-level entries: 通用计算器, 试剂制备, 实验模块. The five experiment classes are not promoted as home cards. |
| Bioinformatics Home | Pass with residual visual debt | The 7 main-flow + 2 auxiliary structure and bottom quick access are present. Development boundary copy is not shown on the module home. Some long flow labels remain visually tight. |
| Bioinformatics Result & Report | Pass with residual visual debt | The page remains in Bioinformatics context, keeps the 7-step Bio flow, and does not show Meta/PubMed/forest plot/fake p-value/fake DEG/formal report-ready package. Current-step highlight is still low-fidelity. |
| Meta Question & Type | Pass with residual visual debt | Ten active Meta types are grouped. Network Meta remains planned/disabled, not an active type. Cards are low-fidelity and not yet concept-polished. |
| Meta Search Strategy | Pass | The shell remains testing-level and does not claim production systematic review capability. |
| Meta Full-text Management | Pass after calibration | Full-text management is now a distinct tab state with shell-only status copy and no automatic full-text extraction claim. |
| Meta Extraction Form Design | Pass after calibration | Internal tabs are `全文管理`, `提取表设计`, `提取完成核查`, `历史记录`; there is no independent `数据提取` tab. `确认本次提取` is disabled and marked as advancing to extraction stage. The page shows type-specific field structure instead of a generic drag/drop field library. |

## 4. Runtime Finding Fixed In This Review

The first Meta Full-text/Extraction screenshots showed the full-text/extraction panel squeezed under the active Meta type section. During review, the Meta target IA shell was calibrated so page-specific sections are visible only for their matching `pageKey`:

- `question_meta_type`: active Meta type grouping and Network Meta planned boundary.
- `fulltext_extraction`: full-text/extraction tab panel.
- `result_report` / `report_export`: shared Result / Report / Export adoption panel.

The full-text/extraction panel also now has shell-level tab switching between full-text management and extraction-form design. This is still UI shell behavior only; it does not enable full-text parsing, data extraction, statistics, or report generation.

## 5. Residual Visual Gaps

- UI-C1 screenshots are low-to-mid fidelity source renders, not pixel-matched Figma output.
- Some long navigation labels remain tight in Bioinformatics and Meta flow buttons.
- Current-step visual emphasis is still weak in several flow bars.
- Several cards/buttons still use placeholder-level Qt styling rather than a completed Visual Style Guide.
- App icon, Finder icon, package icon binding, and formal image/icon resources remain out of scope for this review.

## 6. Commands Run

| Command | Result |
| --- | --- |
| `find /Users/changdali/Desktop/UI/界面示意图 -maxdepth 1 -type f ...` | Found App icon concept plus IMG-01 through IMG-13 concept images. |
| Source PySide offscreen screenshot generation script | Generated 13 runtime screenshots under `docs/ui/runtime_screenshots/UI_C1_20260521/`. |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed: 10 tests. |
| `python3 -m app.main --smoke-test` | Passed. Source launch mode, PySide6 available, no packaged app used. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed: 180 tests. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed. |

## 7. No Packaged App / Resource Replacement Statement

This review did not run packaged app, did not build or package the app, did not replace active icons/assets, did not modify App icon/Finder icon/Info.plist icon binding/LaunchServices, and did not overwrite any desktop entry.
