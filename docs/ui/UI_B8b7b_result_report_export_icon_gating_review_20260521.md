# UI-B8b7b Result / Report / Export Icon Gating Review

## 1. Scope

This stage reviews the 14 UI-B8b7a `result_report_export` production candidates for possible future active replacement pilot eligibility.

Inputs reviewed:

- `docs/ui/UI_B8b7a_result_report_export_icon_final_asset_production_report_20260521.md`
- `docs/ui/UI_B8b7a_result_report_export_icon_QA_report_20260521.md`
- `docs/ui/icon_production/UI_B8b7a_result_report_export_icon_production_manifest_20260521.csv`
- `docs/ui/icon_production/result_report_export/`
- `tests/ui/test_result_report_export_icon_production_manifest.py`
- `tests/shared/test_result_report_export_shell.py`
- `tests/ui/test_result_report_export_shell.py`

Output manifest:

- `docs/ui/UI_B8b7b_result_report_export_icon_gating_manifest_20260521.csv`

## 2. Boundary Statement

This is a gating review only.

Not changed:

- `app/**` active UI code
- active UI loader
- `assets/icons/result_report_export/`
- status icons
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices
- result/report/export business behavior
- `exportGate`
- `reportStatusKey`
- `resultSemanticKey`

No packaged app was run. No packaging, codesigning, or desktop app replacement was performed.

## 3. Current Shell Semantics Review

The current Result / Report / Export shell remains conservative:

| surface | current state |
|---|---|
| empty result preview | `result.semantic.testing_summary_only` |
| empty result report status | `report.status.draft` |
| empty result export gate | `disabled_empty_result` |
| report-ready package | not allowed |
| formal result generation | not enabled |
| fake chart / fake table / fake statistics | not present |
| empty result illustration | decorative empty-state only; does not change result semantics |

Existing tests confirm export buttons stay disabled for empty result state and report-ready future remains blocked.

## 4. Gating Decisions

| resource_id | decision | pilot_allowed | active_usage_allowed | allowed_surface |
|---|---|---:|---:|---|
| `result_overview` | `pilot_allowed` | true | true | `page_region_marker_only` |
| `result_chart` | `disabled_affordance_only` | false | false | `future_chart_placeholder_only` |
| `result_table` | `pilot_allowed` | true | true | `page_region_marker_only` |
| `result_statistics` | `disabled_affordance_only` | false | false | `future_statistics_placeholder_only` |
| `result_summary` | `pilot_allowed` | true | true | `page_region_marker_only` |
| `report_generate` | `blocked_until_function_ready` | false | false | `none` |
| `report_template` | `pilot_allowed` | true | true | `draft_template_marker_only` |
| `export_result` | `blocked_until_function_ready` | false | false | `none` |
| `export_pdf` | `blocked_until_function_ready` | false | false | `none` |
| `export_excel` | `blocked_until_function_ready` | false | false | `none` |
| `export_csv` | `blocked_until_function_ready` | false | false | `none` |
| `export_archive` | `future_only` | false | false | `none` |
| `share_result` | `future_only` | false | false | `none` |
| `result_clear` | `pilot_allowed` | true | true | `disabled_helper_icon_only` |

## 5. Initial Pilot Allow List

The following 5 icons may enter a future active replacement pilot, but only under strict usage limits:

- `result_overview`
- `result_table`
- `result_summary`
- `report_template`
- `result_clear`

Allowed usage:

- page-region marker
- draft-template marker
- disabled/gated helper icon

Required constraints:

- visible text label must remain
- tooltip or nearby copy must preserve testing/draft/gated semantics
- disabled/gated visual state must remain
- `exportGate`, `reportStatusKey`, and `resultSemanticKey` must not change
- icon must not be used as proof of formal result, formal report, export readiness, sharing, or archive delivery

## 6. Blocked Or Deferred Icons

The following icons are not allowed for initial active action usage:

- `report_generate`
- `export_result`
- `export_pdf`
- `export_excel`
- `export_csv`
- `export_archive`
- `share_result`

Reason:

- These icons strongly imply enabled actions, generated reports, downloadable exports, sharing, archive delivery, or report-ready packages.
- They can only be reconsidered once their buttons already have strict disabled/gated state, labels, tooltips, and tests proving gate preservation.

## 7. Chart And Statistics Review

`result_chart` and `result_statistics` remain `disabled_affordance_only`.

Reason:

- Current shell does not generate charts, formal statistics, volcano plots, heatmaps, DEG tables, or publication-ready outputs.
- Active chart/statistics imagery could be read as fake result availability.
- Future active use must remain visually disabled or placeholder-only until actual result semantics and data provenance are implemented.

## 8. Test Coverage

Added focused test:

- `tests/ui/test_result_report_export_icon_gating_review.py`

The test verifies:

- all 14 icons have a gating decision
- only the 5 low-risk icons are `pilot_allowed=true`
- report generation, export, share and archive icons are not pilot-allowed
- chart/statistics icons remain disabled-affordance-only
- manifest paths stay under `docs/ui/icon_production/result_report_export/svg/`
- no status icons or App icon enter this stage
- no formal computed result or report-ready semantics enter the gating manifest
- current shell state remains `testing_summary_only`, `draft`, and `disabled_empty_result`

## 9. Verification

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui/test_result_report_export_icon_gating_review.py` | passed, 7 tests |
| `python3 -m pytest -q tests/ui/test_result_report_export_icon_production_manifest.py` | passed, 6 tests |
| `python3 -m pytest -q tests/shared/test_result_report_export_shell.py tests/ui/test_result_report_export_shell.py` | passed, 10 tests |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 10. Recommendation

The next active pilot, if requested, should be limited to the 5 allow-listed marker/helper icons only. It must not activate report generation, export, sharing, archive, chart, or statistics action icons.

Status icons and App icon resources remain deferred.
