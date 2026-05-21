# UI-B8b4a P1 Module Icon Active Replacement Pilot

Date: 2026-05-21

## 1. Scope

UI-B8b4a is the minimum active replacement pilot for P1 module icons only. It wires the four module-level candidates from UI-B8b3.5 into active UI surfaces:

- `module_bioinformatics`
- `module_meta_analysis`
- `module_labtools`
- `module_settings`

Active UI surfaces:

- Dashboard module entry cards.
- Sidebar module navigation entries.
- Module icon registry / loader.

## 2. Strict Boundary Confirmation

This stage did not process or activate:

- LabTools page/category icons.
- Bioinformatics page icons.
- Meta Analysis page icons.
- Status icons.
- Settings resource icons.
- Result / Report / Export icons.
- Empty-state illustrations.
- App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, packaged app metadata, or desktop app entry.

No package build was run. No packaged app was run. No desktop app entry was modified.

## 3. Active Asset Additions

Only module-level pilot assets were added under `assets/icons/modules/`.

| resource_id | Active SVG | Active PNG exports |
| --- | --- | --- |
| `module_bioinformatics` | `assets/icons/modules/module_bioinformatics.svg` | `24`, `32`, `48`, `64` |
| `module_meta_analysis` | `assets/icons/modules/module_meta_analysis.svg` | `24`, `32`, `48`, `64` |
| `module_labtools` | `assets/icons/modules/module_labtools.svg` | `24`, `32`, `48`, `64` |
| `module_settings` | `assets/icons/modules/module_settings.svg` | `24`, `32`, `48`, `64` |

Existing legacy module PNG files were left in place and were not deleted.

## 4. Loader / Registry Changes

Updated `app/app_identity.py`:

- Added `MODULE_ICON_PATHS`.
- Bound module icons by `ModuleKey` semantic values.
- Kept short aliases for existing callers: `bioinformatics`, `meta_analysis`, `labtools`, `settings`.
- Kept missing icon behavior safe: unknown keys return an empty `QIcon`.

Fallback behavior:

- Dashboard module cards keep their text label and fall back to the existing UI02 workspace icon if a module icon cannot load.
- Sidebar module buttons keep text labels even if an icon is missing.

## 5. UI Wiring

Updated Dashboard / module entry cards:

- Module icon labels now load by semantic `moduleKey`.
- `moduleKey`, `iconSource`, and `iconFallback` properties are exposed for focused tests.
- No IA, order, callbacks, page routing, availability, or status semantics changed.

Updated Sidebar:

- Bioinformatics, Meta Analysis, LabTools, and Settings navigation buttons now use the active pilot module icons.
- Dashboard, Test Feedback, and About entries remain unchanged.
- Text labels remain the primary fallback.

## 6. Pilot Manifest

Added:

`docs/ui/icon_production/UI_B8b4a_p1_module_icon_active_pilot_manifest_20260521.csv`

The manifest keeps all 31 P1 resources visible for tracking. Only the four `modules` rows are marked:

- `active_pilot=true`
- `replacement_state=pilot_only`
- `replacement_ready=pilot_only`

The remaining `labtools`, `bio_pages`, and `meta_pages` rows remain:

- `active_pilot=false`
- `replacement_ready=false`

## 7. Focused Tests

Added:

`tests/ui/test_p1_module_icon_active_pilot.py`

The test verifies:

- Four active module SVG files exist and are registered.
- Module key to icon path mapping is complete.
- Missing icon fallback remains safe.
- Dashboard module cards render with active icons.
- Dashboard fallback preserves text labels.
- Sidebar module entries render with active icons.
- Pilot manifest marks only modules active.
- Non-P1 icon families did not enter active pilot assets.

## 8. Verification Commands

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py tests/ui/test_p1_icon_production_manifest.py tests/ui/test_p1_module_icon_active_pilot.py` | Passed: `17 passed in 0.97s`. |
| `python3 -m app.main --smoke-test` | Passed. Source smoke reported `workspace_entries=3`, `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_app_identity.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py` | Passed: `21 passed in 2.08s`. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed after staging the module icon pilot code, assets, manifest, report, and focused tests. |

## 9. Current Conclusion

The four P1 module icons are now active in a narrow pilot scope. This is not a full icon replacement stage. P1 LabTools category icons, Bio page icons, Meta page icons, all P2/P3/P4 resources, and App icon work remain out of scope.

The pilot is intentionally reversible through the loader fallback: if a module icon is absent or fails to load, navigation still renders text labels and existing fallback imagery without changing module availability or routing.
