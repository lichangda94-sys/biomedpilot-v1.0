# Phase 1 Preview Startup Validation

- branch: `integration/release-bio-c1-ui-shell`
- head: `3ee1ee212b878714745fb77f640ff1bcc5dcfb26`
- screenshot_dir: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup`
- click_count: `14`
- passed_clicks: `14`
- failed_clicks: `0`
- disabled_without_reason_count: `0`

## Packaged App Launch Gate

- app_path: `/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app`
- packaged_git_head: `3ee1ee2`
- direct_launcher_smoke: `passed`
- launchservices_gui_startup_check: `passed`
- gui_startup_status: `passed`
- gui_window_visible: `True`
- gui_window_size: `{'width': 1120, 'height': 720}`
- codesign: `valid_on_disk`
- launcher_arch: `/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app/Contents/MacOS/BioMedPilotIntegrationPreview: Mach-O 64-bit executable arm64`
- cf_bundle_executable: `BioMedPilotIntegrationPreview`

## Click Results

| scope | button | expected | result |
| --- | --- | --- | --- |
| `welcome_settings` | `loginTopIconButton`  | `settings` | `passed` |
| `welcome_about` | `aboutButton` 关于 | `about` | `passed` |
| `welcome_enter` | `primaryButton` 进入本地工作台 | `dashboard` | `passed` |
| `home_bio` | `bioModuleButton` 进入模块 | `bioinformatics` | `passed` |
| `home_meta` | `metaModuleButton` 进入模块 | `meta_analysis` | `passed` |
| `home_labtools` | `labtoolsModuleButton` 进入模块 | `labtools` | `passed` |
| `sidebar_dashboard` | `appSidebarButton` 工作台 / Dashboard | `dashboard` | `passed` |
| `sidebar_bioinformatics` | `appSidebarButton` 生信分析 / Bioinformatics | `bioinformatics` | `passed` |
| `sidebar_meta_analysis` | `appSidebarButton` Meta 分析 / Meta Analysis | `meta_analysis` | `passed` |
| `sidebar_labtools` | `appSidebarButton` 实验工具 / LabTools | `labtools` | `passed` |
| `sidebar_centers` | `appSidebarButton` 管理中心 / Centers | `centers` | `passed` |
| `sidebar_settings` | `appSidebarAuxButton` 设置中心 / Settings | `settings` | `passed` |
| `sidebar_test_feedback` | `appSidebarAuxButton` 测试反馈 / Test Feedback | `test_feedback` | `passed` |
| `sidebar_about` | `appSidebarAuxButton` 关于 / About | `about` | `passed` |

## Screenshots

- `01_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/01_welcome.png`
- `02_settings_from_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/02_settings_from_welcome.png`
- `03_about_from_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/03_about_from_welcome.png`
- `04_home_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/04_home_dashboard.png`
- `05_sidebar_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/05_sidebar_dashboard.png`
- `06_bio_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/06_bio_workspace_entry.png`
- `07_meta_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/07_meta_workspace_entry.png`
- `08_labtools_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/08_labtools_workspace_entry.png`
- `09_sidebar_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_dashboard.png`
- `09_sidebar_bioinformatics`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_bioinformatics.png`
- `09_sidebar_meta_analysis`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_meta_analysis.png`
- `09_sidebar_labtools`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_labtools.png`
- `09_sidebar_centers`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_centers.png`
- `09_sidebar_settings`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_settings.png`
- `09_sidebar_test_feedback`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_test_feedback.png`
- `09_sidebar_about`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_about.png`

## Disabled Buttons Missing Reason

None detected in the visible phase-1 shell scope.
