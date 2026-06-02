# UI Shell Phase 1 Preview Validation

- Date: `2026-06-02`
- Branch: `integration/release-bio-c1-ui-shell`
- Scope: Welcome, Home/Dashboard, About, Settings, Sidebar route landing pages, packaged Preview launch gate.

## Launch Gate

- `python3 scripts/package_app.py --app-name "BioMedPilot Integration Preview" --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 "dist/BioMedPilot Integration Preview.app"`: passed.
- `open -W -n "dist/BioMedPilot Integration Preview.app" --args --gui-startup-check --gui-startup-check-output /tmp/biomedpilot_phase1_shell_b427a7d_gui_startup.json`: passed.
- GUI startup JSON: `status=passed`, `window_visible=true`, `window_active=true`, `window_title=BioMedPilot / 医研智析`, `window_size={'width': 1120, 'height': 720}`.
- Rebuilt package git head: `b427a7d`.
- Bundle executable: `BioMedPilotIntegrationPreview`.
- Launcher architecture: `Mach-O 64-bit executable arm64`.

## Shell Route Contract

- `QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_audit.py`: passed.
- Rows: `28`
- Connected: `23`
- Disabled with reason: `5`
- Broken: `0`

## Shell UI Tests

- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/ui/test_settings_shell.py tests/ui/test_shell_centers.py tests/ui/test_release_ui_button_contracts.py`: passed.
- Result: `29 passed`.

## Shell Live-Click Validation

- `QT_QPA_PLATFORM=offscreen python3 scripts/phase1_preview_startup_validation.py`: passed.
- Click count: `14`.
- Passed clicks: `14`.
- Failed clicks: `0`.
- Disabled visible buttons without reason: `0`.
- Evidence report: `docs/release_validation/20260602_phase1_preview_startup.md`.

## Runtime Screenshot Evidence

Screenshots are stored under `docs/ui/runtime_screenshots/20260602_phase1_preview_startup/`.

| Screenshot | Workspace |
| --- | --- |
| `01_welcome.png` | Welcome |
| `02_settings_from_welcome.png` | Settings from Welcome |
| `03_about_from_welcome.png` | About from Welcome |
| `04_home_dashboard.png` | Home / Dashboard |
| `06_bio_workspace_entry.png` | Bioinformatics adapter entry |
| `07_meta_workspace_entry.png` | Meta Analysis adapter entry |
| `08_labtools_workspace_entry.png` | LabTools adapter entry |
| `09_sidebar_centers.png` | Sidebar Centers |
| `09_sidebar_settings.png` | Sidebar Settings |
| `09_sidebar_bioinformatics.png` | Sidebar Bioinformatics landing |
| `09_sidebar_meta_analysis.png` | Sidebar Meta Analysis landing |
| `09_sidebar_labtools.png` | Sidebar LabTools landing |
| `09_sidebar_test_feedback.png` | Sidebar Test Feedback |
| `09_sidebar_about.png` | Sidebar About |

## Phase 1 Conclusion

The current package launch path is valid after rebuilding the Preview at the current HEAD. The earlier flash-crash report is not reproduced in the rebuilt package: packaged smoke returns `0`, code signing verifies, and real LaunchServices opening reports a visible active `MainWindow`.

The Shell layer is ready for user visual review after restoring the Welcome Settings entry and Sidebar Centers route. This phase does not close deeper Bioinformatics, Meta Analysis, or LabTools runtime completion; those remain under the module route-contract batches.
