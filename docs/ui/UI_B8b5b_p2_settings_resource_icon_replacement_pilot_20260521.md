# UI-B8b5b P2 Settings Resource Icon Active Replacement Pilot

Date: 2026-05-21

## 1. Scope

UI-B8b5b activates only the 13 P2 `settings_resources` icon candidates produced in UI-B8b5a. This is an active pilot for Settings resource category icons only.

In scope:

- `resource_external_engine`
- `resource_image_analysis_engine`
- `resource_imagej_fiji`
- `resource_pdf_ocr`
- `resource_local_model`
- `resource_cloud_ai`
- `resource_python`
- `resource_r`
- `resource_go`
- `resource_kegg`
- `resource_analysis_package`
- `resource_plotting_package`
- `resource_developer_diagnostics`

Out of scope:

- status icons
- Result / Report / Export icons
- empty-state icons
- App icon, Finder icon, `.icns`, iconset, Info.plist, LaunchServices
- packaging, package smoke, packaged app runtime, desktop app replacement

## 2. Active Asset Additions

Added active pilot files under:

- `assets/icons/settings/resources/`

Each resource has:

- one active SVG file
- PNG exports at 24, 32, 48, and 64 px

No active status, result/report/export, empty-state, App icon, Finder icon, `.icns`, iconset, Info.plist, LaunchServices, `dist/**`, or desktop entry files were touched.

## 3. Registry And Loader

Updated `app/app_identity.py` with:

- `SETTINGS_RESOURCE_ICON_DIR`
- `SETTINGS_RESOURCE_ICON_PATHS`
- 13 Settings resource `IconAssetSlot` entries
- `load_settings_resource_icon`
- `load_settings_resource_pixmap`

The registry uses stable `resource_id` keys. It does not hard-code absolute paths. Unknown keys return an empty `QIcon`.

## 4. Settings UI Wiring

Updated `app/shell/main_window.py` so Settings resource category markers render in existing Settings shell surfaces:

- External capabilities
- Analysis resources
- Model and engine
- Developer diagnostics

Resource icons are rendered as category markers through `QLabel#settingsResourceIcon`. Properties exposed for tests:

- `resourceKey`
- `semanticKey`
- `moduleKey`
- `statusKey`
- `iconSource`
- `iconFallback`

The icon wiring does not add new Settings pages, external capability cards, installation flows, update flows, cloud configuration flows, model calls, or OCR execution.

## 5. Behavior And Semantic Boundaries

Preserved behavior:

- Detect buttons remain enabled for detect-first UX.
- Install / update buttons remain disabled.
- Cloud configuration buttons remain disabled.
- Existing status chips remain unchanged.
- Settings secondary IA remains unchanged.
- ImageJ/Fiji remains a Settings external image-analysis configuration resource and does not become a LabTools first-level entry.
- Cloud AI remains a configuration category and is not shown as enabled cloud service.
- Local model remains a configuration category and is not shown as ready for direct inference.
- PDF/OCR remains a resource category marker and is not shown as runnable OCR.

This pilot does not change:

- `planned`
- `not_configured`
- `preflight_only`
- `developer_preview`
- `blocked`
- `shell_only`
- detect-first / user-triggered semantics

## 6. Fallback

Fallback behavior:

- Missing Settings resource icons keep text labels visible.
- Status chips remain visible.
- Detect buttons, disabled install/update buttons, disabled cloud configuration buttons, and page navigation remain unchanged.
- `iconFallback=true` records the fallback state.

## 7. Active Pilot Manifest

Generated:

- `docs/ui/UI_B8b5b_p2_settings_resource_icon_active_pilot_manifest_20260521.csv`

Manifest state:

- 13 rows total
- all rows `resource_family=settings_resources`
- all rows `active_pilot=true`
- all rows `replacement_state=pilot_only`
- all rows `replacement_ready=pilot_only`

This does not mark the resources as full final replacement.

## 8. Focused Tests

Added:

- `tests/ui/test_p2_settings_resource_icon_active_pilot.py`

Coverage:

- 13 active asset files exist and are registered.
- loader fallback is safe for unknown keys and non-P2 families.
- Settings shell renders resource icons.
- Settings resource icon properties preserve resource and semantic keys.
- detect/install/cloud gating is unchanged.
- missing-icon fallback preserves labels, chips, and button gates.
- ImageJ/Fiji remains out of LabTools first-level entries.
- active pilot manifest marks only Settings resources active.
- status, result/report/export, empty-state, and App icon resources are not copied into the Settings resource active directory.

## 9. Verification

Commands run:

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_p2_settings_resource_icon_active_pilot.py` | Passed: 8 passed |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py tests/ui/test_p1_icon_production_manifest.py tests/ui/test_p2_settings_resource_icon_production_manifest.py` | Passed: 16 passed |
| `python3 -m pytest -q tests/ui/test_settings_shell.py tests/ui/test_labtools_shell.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py` | Passed: 23 passed |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | Passed: 8 passed |
| `python3 -m app.main --smoke-test` | Passed |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |

## 10. Boundary Confirmation

This stage did not:

- run package smoke
- run packaged app
- codesign
- modify `dist/**`
- modify desktop entries
- touch App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices
- process status icons
- process Result / Report / Export icons
- process empty-state icons
- implement installation, download, update, cloud configuration, model calling, or OCR runtime logic
