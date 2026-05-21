# UI-B8b7c Result / Report / Export Icon Active Replacement Pilot

## 1. Scope

This stage activates only the 5 UI-B8b7b allow-listed low-risk Result / Report / Export marker/helper icons:

- `result_overview`
- `result_table`
- `result_summary`
- `report_template`
- `result_clear`

Active asset directory:

- `assets/icons/result_report_export/`

Active pilot manifest:

- `docs/ui/UI_B8b7c_result_report_export_icon_active_pilot_manifest_20260521.csv`

## 2. Boundary Statement

This active pilot does not activate:

- `result_chart`
- `result_statistics`
- `report_generate`
- `export_result`
- `export_pdf`
- `export_excel`
- `export_csv`
- `export_archive`
- `share_result`
- status icons
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices

No result, chart, statistics, report generation, export, sharing, archive, delete, or clear behavior was added. No packaged app was run. No packaging, codesigning, desktop app replacement, `dist/**` change, or desktop entry change was performed.

## 3. Active Resource Copy

The 5 allowed SVGs and PNG exports were copied from `docs/ui/icon_production/result_report_export/` to `assets/icons/result_report_export/`.

| resource_id | active SVG | active PNG exports |
|---|---|---|
| `result_overview` | `assets/icons/result_report_export/result_overview.svg` | 24 / 32 / 48 / 64 |
| `result_table` | `assets/icons/result_report_export/result_table.svg` | 24 / 32 / 48 / 64 |
| `result_summary` | `assets/icons/result_report_export/result_summary.svg` | 24 / 32 / 48 / 64 |
| `report_template` | `assets/icons/result_report_export/report_template.svg` | 24 / 32 / 48 / 64 |
| `result_clear` | `assets/icons/result_report_export/result_clear.svg` | 24 / 32 / 48 / 64 |

Blocked/future icons were not copied.

## 4. Registry And Loader

Added active Result / Report / Export marker registry and loader in `app/app_identity.py`:

- `RESULT_REPORT_EXPORT_ICON_DIR`
- `RESULT_REPORT_EXPORT_ICON_PATHS`
- `load_result_report_export_icon`
- `load_result_report_export_pixmap`

Registry constraints:

- Only the 5 allow-listed marker/helper icons are registered.
- Blocked/future icons are not registered.
- Unknown keys return empty `QIcon` / `QPixmap`.
- Loader fallback does not affect labels, tooltips, disabled state, export gate, or page navigation.

## 5. Shell Integration

Updated `app/shared/result_report_export_shell.py` with small marker-only UI:

- `result_overview`: page-region marker only.
- `result_table`: page-region marker only.
- `result_summary`: page-region marker only.
- `report_template`: draft/template marker only.
- `result_clear`: disabled/gated helper marker only.

The markers are displayed in the shared adoption panel and report draft boundary. They are not attached to export buttons or action execution.

## 6. Preserved Semantics

Preserved unchanged:

- `exportGate`
- `reportStatusKey`
- `resultSemanticKey`
- `reportReadyPackageAllowed=false`
- export buttons remain disabled for empty result state
- `testing_summary_only` remains testing-summary-only
- `draft` remains draft
- no formal computed result
- no report-ready package
- no fake chart, fake table, or fake statistics

The existing `empty_result` illustration remains unchanged.

## 7. Deferred Icons

| resource_id | retained state |
|---|---|
| `result_chart` | `disabled_affordance_only` |
| `result_statistics` | `disabled_affordance_only` |
| `report_generate` | `blocked_until_function_ready` |
| `export_result` | `blocked_until_function_ready` |
| `export_pdf` | `blocked_until_function_ready` |
| `export_excel` | `blocked_until_function_ready` |
| `export_csv` | `blocked_until_function_ready` |
| `export_archive` | `future_only` |
| `share_result` | `future_only` |

## 8. Tests

Added focused test:

- `tests/ui/test_result_report_export_icon_active_pilot.py`

Updated compatibility assertions in:

- `tests/ui/test_result_report_export_icon_production_manifest.py`
- `tests/ui/test_result_report_export_icon_gating_review.py`

The updated tests allow the B8b7c active pilot directory to exist only when it contains the 5 allow-listed marker/helper icons.

## 9. Verification

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui/test_result_report_export_icon_active_pilot.py` | passed, 8 tests |
| `python3 -m pytest -q tests/ui/test_result_report_export_icon_production_manifest.py` | passed, 6 tests |
| `python3 -m pytest -q tests/ui/test_result_report_export_icon_gating_review.py` | passed, 7 tests |
| `python3 -m pytest -q tests/shared/test_result_report_export_shell.py tests/ui/test_result_report_export_shell.py` | passed, 10 tests |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | passed, 8 tests |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 10. Closure

UI-B8b7c is an active marker/helper pilot only. It does not make Result / Report / Export production-ready and does not enable report-ready, formal analysis, chart, statistics, export, sharing, archive, clear or delete behavior.
