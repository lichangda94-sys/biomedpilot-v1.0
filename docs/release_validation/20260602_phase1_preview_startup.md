# Phase 1 Preview Startup Validation

- branch: `integration/release-bio-c1-ui-shell`
- head: `2b28d07daca4fac4303eba99aa22824bdbfc8dac`
- screenshot_dir: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup`
- click_count: `12`
- passed_clicks: `12`
- failed_clicks: `0`
- disabled_without_reason_count: `0`
- package_smoke: `passed`
- launchservices_gui_startup: `passed`
- launchservices_window_active: `true`
- real_open_survived_10s: `passed`
- bundle_executable: `BioMedPilotIntegrationPreview`
- bundle_icon: `biomedpilot_app_icon.icns`

## Click Results

| scope | button | expected | result |
| --- | --- | --- | --- |
| `welcome_about` | `aboutButton` 关于 | `about` | `passed` |
| `welcome_enter` | `primaryButton` 进入本地工作台 | `dashboard` | `passed` |
| `home_bio` | `bioModuleButton` 进入模块 | `bioinformatics` | `passed` |
| `home_meta` | `metaModuleButton` 进入模块 | `meta_analysis` | `passed` |
| `home_labtools` | `labtoolsModuleButton` 进入模块 | `labtools` | `passed` |
| `sidebar_dashboard` | `appSidebarButton` 工作台 / Dashboard | `dashboard` | `passed` |
| `sidebar_bioinformatics` | `appSidebarButton` 生信分析 / Bioinformatics | `bioinformatics` | `passed` |
| `sidebar_meta_analysis` | `appSidebarButton` Meta 分析 / Meta Analysis | `meta_analysis` | `passed` |
| `sidebar_labtools` | `appSidebarButton` 实验工具 / LabTools | `labtools` | `passed` |
| `sidebar_settings` | `appSidebarButton` 设置中心 / Settings | `settings` | `passed` |
| `sidebar_test_feedback` | `appSidebarAuxButton` 测试反馈 / Test Feedback | `test_feedback` | `passed` |
| `sidebar_about` | `appSidebarAuxButton` 关于 / About | `about` | `passed` |

## Screenshots

- `01_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/01_welcome.png`
- `02_about_from_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/02_about_from_welcome.png`
- `03_home_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/03_home_dashboard.png`
- `04_sidebar_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/04_sidebar_dashboard.png`
- `05_bio_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/05_bio_workspace_entry.png`
- `06_meta_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/06_meta_workspace_entry.png`
- `07_labtools_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/07_labtools_workspace_entry.png`
- `09_sidebar_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_dashboard.png`
- `09_sidebar_bioinformatics`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_bioinformatics.png`
- `09_sidebar_meta_analysis`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_meta_analysis.png`
- `09_sidebar_labtools`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_labtools.png`
- `09_sidebar_settings`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_settings.png`
- `09_sidebar_test_feedback`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_test_feedback.png`
- `09_sidebar_about`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_about.png`

## Disabled Buttons Missing Reason

None detected in the visible phase-1 shell scope.

## Preview Package Validation

- `QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --app-name 'BioMedPilot Integration Preview' --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot Integration Preview.app`: passed.
- `open -W -n dist/BioMedPilot Integration Preview.app --args --smoke-test`: passed.
- `open -W -n dist/BioMedPilot Integration Preview.app --args --gui-startup-check`: passed with `window_visible=true` and `window_active=true`.
- `open -n dist/BioMedPilot Integration Preview.app`: survived 10 seconds as `BioMedPilotIntegrationPreview`; no BioMedPilot crash report was found.
