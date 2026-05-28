# UI-B8b4c-1 P1 Bioinformatics Page Icon Active Replacement Pilot

Date: 2026-05-21

## 1. Scope

UI-B8b4c-1 activates only the nine P1 Bioinformatics page icons produced in UI-B8b3.5:

- `bio_page_project_home`
- `bio_page_data_source`
- `bio_page_data_check_preparation`
- `bio_page_group_design`
- `bio_page_analysis_tasks`
- `bio_page_result_report`
- `bio_page_report_export`
- `bio_page_settings_resources`
- `bio_page_project_logs`

Active UI surface:

- Bioinformatics target IA shell / workflow navigation.

## 2. Strict Boundary Confirmation

This stage did not process or activate:

- Meta Analysis page icons.
- Status icons.
- Settings resource icons.
- Result / Report / Export shared icons.
- Empty-state illustrations.
- App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, packaged app metadata, or desktop app entry.

No package build was run. No packaged app was run. No desktop app entry was modified.

## 3. Active Asset Additions

Only Bioinformatics page pilot assets were added under `assets/icons/bioinformatics/pages/`.

| resource_id | Active SVG | Active PNG exports |
| --- | --- | --- |
| `bio_page_project_home` | `assets/icons/bioinformatics/pages/bio_page_project_home.svg` | `24`, `32`, `48`, `64` |
| `bio_page_data_source` | `assets/icons/bioinformatics/pages/bio_page_data_source.svg` | `24`, `32`, `48`, `64` |
| `bio_page_data_check_preparation` | `assets/icons/bioinformatics/pages/bio_page_data_check_preparation.svg` | `24`, `32`, `48`, `64` |
| `bio_page_group_design` | `assets/icons/bioinformatics/pages/bio_page_group_design.svg` | `24`, `32`, `48`, `64` |
| `bio_page_analysis_tasks` | `assets/icons/bioinformatics/pages/bio_page_analysis_tasks.svg` | `24`, `32`, `48`, `64` |
| `bio_page_result_report` | `assets/icons/bioinformatics/pages/bio_page_result_report.svg` | `24`, `32`, `48`, `64` |
| `bio_page_report_export` | `assets/icons/bioinformatics/pages/bio_page_report_export.svg` | `24`, `32`, `48`, `64` |
| `bio_page_settings_resources` | `assets/icons/bioinformatics/pages/bio_page_settings_resources.svg` | `24`, `32`, `48`, `64` |
| `bio_page_project_logs` | `assets/icons/bioinformatics/pages/bio_page_project_logs.svg` | `24`, `32`, `48`, `64` |

## 4. Loader / Registry Changes

Updated `app/app_identity.py`:

- Added `BIOINFORMATICS_PAGE_ICON_DIR`.
- Added `BIOINFORMATICS_PAGE_ICON_PATHS`.
- Added `load_bioinformatics_page_icon()`.
- Added `load_bioinformatics_page_pixmap()`.
- Registered the nine Bioinformatics page icon slots in the icon asset inventory.

The loader uses stable `PageKey` semantic values and project-relative asset paths. Unknown keys return an empty `QIcon`, allowing the UI to keep labels, disabled navigation, and gating intact.

## 5. UI Wiring

Updated `app/bioinformatics/workspace.py`:

- Main-flow IA buttons now use page-level Bioinformatics icons.
- Auxiliary IA buttons now use page-level Bioinformatics icons.
- `iconSource` and `iconFallback` properties are exposed for focused tests.

The Bioinformatics IA remains unchanged:

- Main flow remains exactly 7 steps:
  1. Project Home / 项目首页
  2. Data Source / 数据来源
  3. Data Check & Preparation / 数据检查与准备
  4. Group & Design / 分组与分析设计
  5. Analysis Tasks / 分析任务
  6. Result & Report / 结果与报告
  7. Report Export / 报告导出
- Auxiliary pages remain exactly:
  - Bioinformatics Settings / 生信设置
  - Project Logs & Technical Details / 项目日志与技术详情
- No legacy diagnostic routes were removed.
- No new Bioinformatics page was added.
- No analysis executor was enabled.
- No DEG / ORA / GSEA / Survival / Clinical gate changed.
- `testing`, `planned`, `shell_only`, `developer_preview`, `preflight_only`, `draft`, `formal_computed_result`, and `report_ready` semantics were not changed.

Fallback behavior:

- If a Bioinformatics page icon fails to load, the navigation text label remains visible.
- Disabled navigation state and `formalActionEnabled=false` remain unchanged.
- Page navigation, buttons, and Result / Report / Export gating do not depend on icon loading.

## 6. Pilot Manifest

Added:

`docs/ui/UI_B8b4c_1_p1_bio_page_icon_active_pilot_manifest_20260521.csv`

The manifest keeps all 31 P1 resources visible for tracking:

- Nine `bio_pages` rows are marked `active_pilot=true`.
- Four `modules` rows and eight `labtools` rows are recorded as `prior_active_pilot=true`.
- Ten `meta_pages` rows remain `future_target=true` and `active_pilot=false`.

## 7. Focused Tests

Added:

`tests/ui/test_p1_bio_page_icon_active_pilot.py`

The test verifies:

- Nine Bioinformatics page active asset files exist and are registered.
- PageKey / semantic key to icon path mapping is complete.
- Missing icon fallback remains safe.
- Bioinformatics target IA navigation renders page icons.
- Main flow remains exactly 7 steps.
- Auxiliary pages remain exactly 2 entries.
- Disabled navigation and formal-action gates remain unchanged.
- The pilot manifest marks only Bio page icons active in this stage.
- Non-Bio icon families did not enter `assets/icons/bioinformatics/pages/`.

## 8. Verification Commands

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py tests/ui/test_p1_icon_production_manifest.py tests/ui/test_p1_module_icon_active_pilot.py tests/ui/test_p1_labtools_icon_active_pilot.py tests/ui/test_p1_bio_page_icon_active_pilot.py` | Passed: `31 passed in 2.34s`. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_bioinformatics_workflow_pages.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py` | Passed: `109 passed in 4.30s`. |
| `python3 -m app.main --smoke-test` | Passed. Source smoke reported `workspace_entries=3`, `bioinformatics_features=5`, `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | Passed: `8 passed in 0.97s`. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed after staging the Bio page icon pilot code, assets, manifest, report, and focused tests. |

## 9. Current Conclusion

The nine P1 Bioinformatics page icons are now active in a narrow page-navigation pilot scope. This is not a full icon replacement stage and does not make any Bioinformatics analysis production-ready.

Meta page icons, status icons, Settings resources, Result / Report / Export icons, empty states, and App icon work remain out of scope.
