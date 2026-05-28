# UI-B8b4b P1 LabTools Icon Active Replacement Pilot

Date: 2026-05-21

## 1. Scope

UI-B8b4b is the second active replacement pilot for P1 icons. It activates only the eight LabTools icons produced in UI-B8b3.5:

- `labtools_general_calculator`
- `labtools_reagent_preparation`
- `labtools_experiment_modules`
- `labtools_cell_experiments`
- `labtools_protein_experiments`
- `labtools_nucleic_acid_experiments`
- `labtools_immuno_absorbance`
- `labtools_ihc`

Active UI surface:

- LabTools home / IA shell.

## 2. Strict Boundary Confirmation

This stage did not process or activate:

- Bioinformatics page icons.
- Meta Analysis page icons.
- Status icons.
- Settings resource icons.
- Result / Report / Export icons.
- Empty-state illustrations.
- App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, packaged app metadata, or desktop app entry.

No package build was run. No packaged app was run. No desktop app entry was modified.

## 3. Active Asset Additions

Only LabTools pilot assets were added under `assets/icons/labtools/`.

| resource_id | Active SVG | Active PNG exports |
| --- | --- | --- |
| `labtools_general_calculator` | `assets/icons/labtools/labtools_general_calculator.svg` | `24`, `32`, `48`, `64` |
| `labtools_reagent_preparation` | `assets/icons/labtools/labtools_reagent_preparation.svg` | `24`, `32`, `48`, `64` |
| `labtools_experiment_modules` | `assets/icons/labtools/labtools_experiment_modules.svg` | `24`, `32`, `48`, `64` |
| `labtools_cell_experiments` | `assets/icons/labtools/labtools_cell_experiments.svg` | `24`, `32`, `48`, `64` |
| `labtools_protein_experiments` | `assets/icons/labtools/labtools_protein_experiments.svg` | `24`, `32`, `48`, `64` |
| `labtools_nucleic_acid_experiments` | `assets/icons/labtools/labtools_nucleic_acid_experiments.svg` | `24`, `32`, `48`, `64` |
| `labtools_immuno_absorbance` | `assets/icons/labtools/labtools_immuno_absorbance.svg` | `24`, `32`, `48`, `64` |
| `labtools_ihc` | `assets/icons/labtools/labtools_ihc.svg` | `24`, `32`, `48`, `64` |

## 4. Loader / Registry Changes

Updated `app/app_identity.py`:

- Added `LABTOOLS_ICON_DIR`.
- Added `LABTOOLS_ICON_PATHS`.
- Added `load_labtools_icon()`.
- Added `load_labtools_pixmap()`.
- Registered the eight LabTools icon slots in the icon asset inventory.

The loader uses stable `PageKey` semantic values and relative project asset paths. Unknown keys return an empty `QIcon`, allowing the UI to keep labels and fallback rendering.

## 5. UI Wiring

Updated `app/shell/main_window.py`:

- Added LabTools icon labels to the three existing top-level LabTools cards:
  - 通用计算器
  - 试剂制备
  - 实验模块
- Added a nested icon row inside the existing `实验模块` card for:
  - 细胞实验
  - 蛋白实验
  - 核酸实验
  - 免疫与吸光度
  - 免疫组化

The LabTools IA remains unchanged:

- The home page still has only three first-level entries.
- The five experiment categories remain nested under `实验模块`.
- ImageJ/Fiji remains out of LabTools primary IA and belongs to Settings / external capability configuration.
- No real calculator, reagent, WB, PCR, ELISA, cell experiment, or other business logic was changed.
- No feature status or availability semantics were changed.

Fallback behavior:

- If a LabTools icon fails to load, text labels remain visible.
- Cards and disabled shell buttons keep their existing properties and state.
- No page switching, button behavior, status chip, or IA ordering depends on icon loading.

## 6. Pilot Manifest

Added:

`docs/ui/UI_B8b4b_p1_labtools_icon_active_pilot_manifest_20260521.csv`

The manifest keeps all 31 P1 resources visible for tracking:

- Eight `labtools` rows are marked `active_pilot=true`.
- Four `modules` rows are recorded as `prior_active_pilot=true` from UI-B8b4a, not changed by this stage.
- `bio_pages` and `meta_pages` remain `active_pilot=false`.

## 7. Focused Tests

Added:

`tests/ui/test_p1_labtools_icon_active_pilot.py`

The test verifies:

- Eight LabTools active asset files exist and are registered.
- Semantic key to icon path mapping is complete.
- Missing icon fallback remains safe.
- LabTools home renders three primary entry icons.
- LabTools experiment category icons are nested, not primary entries.
- Text labels and disabled shell buttons remain intact when icons fail.
- The pilot manifest marks only LabTools as active in this stage.
- Non-LabTools icon families did not enter `assets/icons/labtools/`.

## 8. Verification Commands

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py tests/ui/test_p1_icon_production_manifest.py tests/ui/test_p1_module_icon_active_pilot.py tests/ui/test_p1_labtools_icon_active_pilot.py` | Passed: `24 passed in 1.90s`. |
| `python3 -m pytest -q tests/ui/test_labtools_shell.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py` | Passed: `19 passed in 3.50s`. |
| `python3 -m app.main --smoke-test` | Passed. Source smoke reported `workspace_entries=3`, `labtools_features=4`, `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | Passed: `8 passed in 1.16s`. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed after staging the LabTools icon pilot code, assets, manifest, report, and focused tests. |

## 9. Current Conclusion

The eight P1 LabTools icons are now active in a narrow pilot scope. This is not a full icon replacement stage and does not make any LabTools feature production-ready.

Bioinformatics page icons, Meta page icons, status icons, Settings resources, Result / Report / Export icons, empty states, and App icon work remain out of scope.
