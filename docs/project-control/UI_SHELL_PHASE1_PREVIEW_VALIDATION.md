# UI Shell Phase 1 Preview Validation

- Date: `2026-06-01`
- Branch: `integration/release-bio-c1-ui-shell`
- Scope: Welcome, Home/Dashboard, About, Settings, Sidebar route landing pages, packaged Preview launch gate.

## Launch Gate

- `python3 scripts/package_app.py --app-name "BioMedPilot Integration Preview" --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 "dist/BioMedPilot Integration Preview.app"`: passed.
- `open -W -n "dist/BioMedPilot Integration Preview.app" --args --smoke-test`: passed.
- `open -n "dist/BioMedPilot Integration Preview.app"`: stayed running for 10 seconds with no launch-log crash.
- Rebuilt package git head: `7391943`.

## Shell Route Contract

- `python3 scripts/ui_route_contract_audit.py --json-out /tmp/shell_route_contract_verify.json --markdown-out /tmp/shell_route_contract_verify.md`: passed.
- Rows: `28`
- Connected: `23`
- Disabled with reason: `5`
- Broken: `0`

## Shell UI Tests

- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_settings_shell.py tests/ui/test_shell_centers.py tests/ui/test_release_ui_button_contracts.py`: passed.
- Result: `28 passed`.

## Runtime Screenshot Evidence

Screenshots are stored under `docs/ui/runtime_screenshots/20260601_phase1_shell_baseline/`.

| Screenshot | Workspace |
| --- | --- |
| `01_welcome.png` | Welcome |
| `02_about_from_welcome.png` | About from Welcome |
| `03_settings_from_welcome.png` | Settings from Welcome |
| `04_home_dashboard.png` | Home / Dashboard |
| `05_sidebar_settings.png` | Sidebar Settings |
| `06_sidebar_centers.png` | Sidebar Centers |
| `07_sidebar_bioinformatics.png` | Sidebar Bioinformatics landing |
| `08_sidebar_meta_analysis.png` | Sidebar Meta Analysis landing |
| `09_sidebar_labtools.png` | Sidebar LabTools landing |
| `10_sidebar_test_feedback.png` | Sidebar Test Feedback |
| `11_sidebar_about.png` | Sidebar About |

## Phase 1 Conclusion

The current package launch path is valid after rebuilding the Preview at the current HEAD. The earlier flash-crash report is not reproduced in the rebuilt package: the packaged smoke gate returns `0`, code signing verifies, and a real `open -n` launch remains alive for 10 seconds.

The Shell layer is ready for user visual review. This phase does not close deeper Bioinformatics, Meta Analysis, or LabTools runtime completion; those remain under the module route-contract batches.
