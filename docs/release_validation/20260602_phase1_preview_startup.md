# Phase 1 Preview Startup Validation

- branch: `integration/release-bio-c1-ui-shell`
- head: `8755673a420b8745c00b0015892812869726a279`
- screenshot_dir: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup`
- click_count: `13`
- passed_clicks: `13`
- failed_clicks: `0`
- disabled_without_reason_count: `0`

## Click Results

| scope | button | expected | result |
| --- | --- | --- | --- |
| `welcome_about` | `aboutButton` 关于 | `about` | `passed` |
| `welcome_settings` | `loginTopIconButton`  | `settings` | `passed` |
| `welcome_enter` | `primaryButton` 进入本地工作台 | `dashboard` | `passed` |
| `home_bio` | `bioModuleButton` 进入模块 | `bioinformatics` | `passed` |
| `home_meta` | `metaModuleButton` 进入模块 | `meta_analysis` | `passed` |
| `home_labtools` | `labtoolsModuleButton` 进入模块 | `labtools` | `passed` |
| `sidebar_dashboard` | `appSidebarButton` 工作台 / Dashboard | `dashboard` | `passed` |
| `sidebar_bioinformatics` | `appSidebarButton` 生信分析 / Bioinformatics | `bioinformatics` | `passed` |
| `sidebar_meta_analysis` | `appSidebarButton` Meta 分析 / Meta Analysis | `meta_analysis` | `passed` |
| `sidebar_labtools` | `appSidebarButton` 实验工具 / LabTools | `labtools` | `passed` |
| `sidebar_settings` | `appSidebarAuxButton` 设置中心 / Settings | `settings` | `passed` |
| `sidebar_test_feedback` | `appSidebarAuxButton` 测试反馈 / Test Feedback | `test_feedback` | `passed` |
| `sidebar_about` | `appSidebarAuxButton` 关于 / About | `about` | `passed` |

## Screenshots

- `01_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/01_welcome.png`
- `02_about_from_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/02_about_from_welcome.png`
- `03_settings_from_welcome`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/03_settings_from_welcome.png`
- `04_home_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/04_home_dashboard.png`
- `05_sidebar_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/05_sidebar_dashboard.png`
- `06_bio_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/06_bio_workspace_entry.png`
- `07_meta_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/07_meta_workspace_entry.png`
- `08_labtools_workspace_entry`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/08_labtools_workspace_entry.png`
- `09_sidebar_dashboard`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_dashboard.png`
- `09_sidebar_bioinformatics`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_bioinformatics.png`
- `09_sidebar_meta_analysis`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_meta_analysis.png`
- `09_sidebar_labtools`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_labtools.png`
- `09_sidebar_settings`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_settings.png`
- `09_sidebar_test_feedback`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_test_feedback.png`
- `09_sidebar_about`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_startup/09_sidebar_about.png`

## Disabled Buttons Missing Reason

None detected in the visible phase-1 shell scope.

## LaunchServices Gate

- package command: `QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --app-name 'BioMedPilot Integration Preview' --smoke-test`
- package result: `passed`
- package git_head: `8755673`
- package mode: `local-python-native-launcher`
- codesign result: `passed`
- LaunchServices smoke: `open -W -n 'dist/BioMedPilot Integration Preview.app' --args --smoke-test` -> `passed`
- GUI startup: `open -W -n 'dist/BioMedPilot Integration Preview.app' --args --gui-startup-check --gui-startup-check-output /tmp/biomedpilot_phase1_gui_startup_check_8755673.json` -> `passed`
- GUI window: `window_visible=true`, `window_size=1120x720`
- macOS foreground activation: `window_active=false`
- activation diagnostic: `appkit_activation_rejected; application_services_rejected:transform=-50;front=-13066`
- real open: `open -n 'dist/BioMedPilot Integration Preview.app'`
- real open 10s check: process remained alive as PID `99365`; no new `BioMedPilot` or `Python` DiagnosticReports crash file was detected.

## Phase 1 Conclusion

The current local Preview does not reproduce a process crash under LaunchServices. The bundle starts, creates the main window, and remains alive after a real open. The remaining macOS-specific symptom is foreground activation rejection in the command-driven launch context, which can make the app appear not to come forward even though it is running.
