# UI-B8b6b Empty State Active Replacement Pilot

## 1. Scope

This pilot connected only the 6 UI-B8b6a empty-state illustration candidates to the active shared empty-state display layer.

Active pilot resources:

- `empty_project`
- `empty_result`
- `empty_missing_resource`
- `empty_blocked`
- `empty_shell_only`
- `empty_preflight_only`

Active asset directory:

- `assets/images/empty_states/`

Active pilot manifest:

- `docs/ui/UI_B8b6b_empty_state_active_pilot_manifest_20260521.csv`

## 2. Boundary Statement

This stage did not process or replace:

- status icons
- result / report / export icons
- App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices resources
- packaged app resources
- desktop entry points

No packaged app was run. No packaging, codesigning, or desktop app replacement was performed.

## 3. Active Resource Copy

The UI-B8b6a candidate SVG and PNG exports were copied into `assets/images/empty_states/`.

| resource_id | active SVG | active PNG exports |
|---|---|---|
| `empty_project` | `assets/images/empty_states/empty_project.svg` | 24 / 32 / 48 / 64 |
| `empty_result` | `assets/images/empty_states/empty_result.svg` | 24 / 32 / 48 / 64 |
| `empty_missing_resource` | `assets/images/empty_states/empty_missing_resource.svg` | 24 / 32 / 48 / 64 |
| `empty_blocked` | `assets/images/empty_states/empty_blocked.svg` | 24 / 32 / 48 / 64 |
| `empty_shell_only` | `assets/images/empty_states/empty_shell_only.svg` | 24 / 32 / 48 / 64 |
| `empty_preflight_only` | `assets/images/empty_states/empty_preflight_only.svg` | 24 / 32 / 48 / 64 |

The active pilot uses SVG as the primary resource. PNG exports remain available for size-specific fallback or future review, but this stage does not force a page-level raster rendering strategy.

## 4. Registry And Loader

Added active empty-state illustration registry and loader in `app/app_identity.py`:

- `EMPTY_STATE_IMAGE_PATHS`
- `EMPTY_STATE_SEMANTIC_IMAGE_KEYS`
- `empty_state_image_key_for`
- `load_empty_state_illustration`
- `load_empty_state_pixmap`

Loader behavior:

- Uses stable `empty_state_key` first.
- Supports guarded semantic-key aliases for the 6 active pilot resources.
- Returns an empty `QIcon` / `QPixmap` for missing or out-of-scope keys.
- Does not load status, result_report_export, or App icon resources.

## 5. Shared Empty State Primitive

Updated `app/shared/ui_components/primitives.py` so `make_empty_state()` can optionally render an illustration when `empty_state_key` or a recognized `semantic_key` is supplied.

Preserved behavior:

- Existing title text remains unchanged.
- Existing body text remains unchanged.
- Existing action button text and role remain unchanged.
- Missing image fallback omits the illustration but keeps title, body, action button, navigation, and gating intact.
- Calls without an empty-state key continue to render text-only empty states.

## 6. Result / Report / Export Boundary

Updated `app/shared/result_report_export_shell.py` so `make_result_preview_empty_state()` uses:

- `empty_state_key=empty_result`
- `semantic_key=result.semantic.testing_summary_only`

No result/report/export semantics changed:

- `empty_result` still maps to `result.semantic.testing_summary_only`.
- `exportGate` remains `disabled_empty_result`.
- `reportStatusKey` remains `report.status.draft` for empty result preview.
- No formal computed result, report-ready package, fake chart, fake result, or export capability was enabled.

## 7. Mapping Notes

| requested empty state area | current mapping | note |
|---|---|---|
| `empty_project` | `empty_project` | active pilot available |
| `empty_data` | no dedicated active resource | `future_mapping_needed`; no forced replacement |
| `empty_result` | `empty_result` | active in shared Result / Report / Export empty preview |
| `empty_report` | no dedicated active resource | `future_mapping_needed`; no report-ready implication |
| `empty_search` | no dedicated active resource | `future_mapping_needed`; no forced replacement |
| `empty_history` | no dedicated active resource | `future_mapping_needed`; no forced replacement |

The pilot intentionally does not invent new resources or new pages for missing mappings.

## 8. Tests

Added focused test:

- `tests/ui/test_empty_state_active_pilot.py`

Updated existing production-manifest test:

- `tests/ui/test_empty_state_illustration_production_manifest.py`

The updated test keeps UI-B8b6a production paths docs-only while allowing the later UI-B8b6b active pilot directory to exist.

## 9. Verification

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui/test_empty_state_active_pilot.py` | passed, 8 tests |
| `python3 -m pytest -q tests/ui/test_empty_state_illustration_production_manifest.py` | passed, 6 tests |
| `python3 -m pytest -q tests/ui/test_ui_primitives.py tests/shared/test_result_report_export_shell.py` | passed, 9 tests |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py` | passed, 5 tests |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | passed, 8 tests |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 10. Closure

UI-B8b6b is an active replacement pilot only. The 6 empty-state illustrations are not marked as full final replacement, and status / result_report_export / App icon resources remain deferred.
