# UI-B8b8c Status Icon Active Replacement Pilot

## 1. Scope

This stage connects the 10 UI-B8b8a/B8b8b status icon candidates to the active shared status chip display layer.

Inputs reviewed:

- `docs/ui/UI_B8b8a_status_icon_final_asset_production_report_20260521.md`
- `docs/ui/UI_B8b8a_status_icon_QA_report_20260521.md`
- `docs/ui/icon_production/UI_B8b8a_status_icon_production_manifest_20260521.csv`
- `docs/ui/UI_B8b8b_status_icon_semantic_gating_review_20260521.md`
- `docs/ui/UI_B8b8b_status_icon_semantic_gating_manifest_20260521.csv`
- `docs/ui/icon_production/status/`
- `tests/ui/test_status_icon_production_manifest.py`
- `tests/ui/test_status_icon_semantic_gating_review.py`
- `tests/ui/test_ui_primitives.py`
- `tests/shared/test_semantic_keys.py`

Outputs:

- `assets/icons/status/`
- `docs/ui/UI_B8b8c_status_icon_active_pilot_manifest_20260522.csv`
- `tests/ui/test_status_icon_active_pilot.py`

## 2. Boundary Statement

This active pilot only adds auxiliary status icons to existing status chip rendering.

Preserved:

- status text label
- status chip primitive
- tooltip / explanation
- `statusKey`
- `semanticKey`
- existing status judgement logic
- feature availability
- resource detect-first state
- analysis gates
- report gates
- export gates

Not changed:

- business page IA
- analysis execution
- report generation
- export behavior
- active App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices
- packaging scripts
- `dist/**`
- desktop entry

No packaged app was run. No packaging, codesigning, or desktop app replacement was performed.

## 3. Active Asset Scope

Copied status candidate SVG and PNG exports into:

- `assets/icons/status/`

Active resources:

| resource_id | semantic_key | active usage |
|---|---|---|
| `status_testing` | `feature.status.testing` | auxiliary status chip marker only |
| `status_planned` | `feature.status.planned` | auxiliary status chip marker only |
| `status_shell_only` | `feature.status.shell_only` | auxiliary status chip marker only |
| `status_developer_preview` | `feature.status.developer_preview` | auxiliary status chip marker only |
| `status_blocked` | `feature.status.blocked` | auxiliary status chip marker only |
| `status_available` | `resource.status.available` | only after existing confirmed `resource.status.available` |
| `status_not_configured` | `resource.status.not_configured` | auxiliary status chip marker only |
| `status_failed` | `resource.status.failed` | auxiliary status chip marker only |
| `status_preflight_only` | `analysis.status.preflight_only` | auxiliary status chip marker only |
| `status_draft` | `report.status.draft` | auxiliary status chip marker only |

## 4. Loader And Rendering Changes

Updated:

- `app/app_identity.py`
- `app/shared/ui_components/primitives.py`

Implementation:

- status icons are registered by full semantic key, not by short display key
- unknown keys return an empty `QIcon` / `QPixmap`
- `make_status_chip` keeps returning the same `QLabel` status chip primitive
- the visible label remains present in the chip
- tooltip text explains the non-final status meaning
- fallback keeps the text label and tooltip if icon loading fails

## 5. `status_available` Guard

`status_available` is loaded only through `resource.status.available`.

The active pilot does not:

- run resource detection
- install or configure a resource
- enable cloud service
- enable local model inference
- move ImageJ/Fiji into LabTools
- mark planned or not-configured resources as available

The existing runtime status must already be `resource.status.available` for the available icon to appear.

## 6. Test Coverage

Added focused test:

- `tests/ui/test_status_icon_active_pilot.py`

Updated prior read-only tests to allow the new active status directory while still rejecting non-status families and App icon entries:

- `tests/ui/test_status_icon_production_manifest.py`
- `tests/ui/test_status_icon_semantic_gating_review.py`

The tests verify:

- 10 active status SVG assets are registered by semantic key
- 24 / 32 / 48 / 64 PNG exports are present in `assets/icons/status/`
- unknown keys use safe fallback
- status chips keep label, tooltip, `statusKey`, and `semanticKey`
- icon fallback preserves label and tooltip
- `status_available` requires confirmed `resource.status.available`
- no Result / Report / Export, empty state, Settings resource, or App icon assets enter the status directory

## 7. Verification

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui/test_status_icon_active_pilot.py` | passed, 7 tests |
| `python3 -m pytest -q tests/ui/test_status_icon_production_manifest.py tests/ui/test_status_icon_semantic_gating_review.py` | passed, 13 tests |
| `python3 -m pytest -q tests/ui/test_ui_primitives.py tests/shared/test_semantic_keys.py` | passed, 9 tests |
| `python3 -m pytest -q tests/ui/test_settings_shell.py tests/ui/test_labtools_shell.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_result_report_export_shell.py tests/shared/test_result_report_export_shell.py` | passed, 39 tests |
| `python3 -m pytest -q tests/ui/test_p1_module_icon_active_pilot.py tests/ui/test_p1_labtools_icon_active_pilot.py tests/ui/test_p1_bio_page_icon_active_pilot.py tests/ui/test_p1_meta_page_icon_active_pilot.py tests/ui/test_p2_settings_resource_icon_active_pilot.py tests/ui/test_result_report_export_icon_active_pilot.py tests/ui/test_empty_state_active_pilot.py` | passed, 52 tests |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 8. Recommendation

UI-B8b8d should perform status closure audit before moving to B8b9 overall icon system closure.

App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, and LaunchServices remain deferred to UI-B10.
