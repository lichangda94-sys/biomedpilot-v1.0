# UI-B8b7a Result / Report / Export Icon QA Report

## 1. Scope

This QA report covers only the 14 `result_report_export` production candidate icons generated under `docs/ui/icon_production/result_report_export/`.

In scope:

- `result_overview`
- `result_chart`
- `result_table`
- `result_statistics`
- `result_summary`
- `report_generate`
- `report_template`
- `export_result`
- `export_pdf`
- `export_excel`
- `export_csv`
- `export_archive`
- `share_result`
- `result_clear`

Out of scope:

- active UI loader changes
- active asset replacement under `assets/icons/result_report_export/`
- status icons
- empty-state illustrations
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices
- report template generation
- formal result, fake result, fake chart, or report-ready package behavior

## 2. Candidate Completeness

| resource_id | svg | png 24 | png 32 | png 48 | png 64 | qa_status |
|---|---:|---:|---:|---:|---:|---|
| `result_overview` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `result_chart` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `result_table` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `result_statistics` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `result_summary` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `report_generate` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `report_template` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `export_result` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `export_pdf` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `export_excel` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `export_csv` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `export_archive` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `share_result` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |
| `result_clear` | yes | yes | yes | yes | yes | `passed_candidate_gated_affordance` |

All 14 candidates have independent SVG files and 24 / 32 / 48 / 64 px PNG exports.

## 3. Vector And Transparency QA

| check | result |
|---|---|
| SVG files are independent vector files | pass |
| SVG files do not embed placeholder PNGs | pass |
| SVG files do not contain raster `<image>` references | pass |
| PNG exports use transparent canvas | pass |
| PNG exports have expected square sizes | pass |
| Candidate files remain under `docs/ui/icon_production/result_report_export/` | pass |
| No files were written to `assets/icons/result_report_export/` | pass |

## 4. Semantic QA

| resource_id | semantic_key | guardrail |
|---|---|---|
| `result_overview` | `result.semantic.testing_summary_only` | must not imply formal computed result |
| `result_chart` | `result.semantic.testing_summary_only` | must not introduce fake charts |
| `result_table` | `result.semantic.testing_summary_only` | must not introduce fake statistical or DEG tables |
| `result_statistics` | `analysis.status.testing_level` | must stay testing-level, not formal statistics |
| `result_summary` | `result.semantic.testing_summary_only` | must not imply completed result review |
| `report_generate` | `report.status.draft` | must not imply report-ready generation |
| `report_template` | `report.status.draft` | must not imply completed report template system |
| `export_result` | `report.export_panel` | must stay behind export gating |
| `export_pdf` | `report.export_panel` | must stay behind export gating |
| `export_excel` | `export.format.xlsx` | must not enable XLSX export by itself |
| `export_csv` | `export.format.csv` | must not enable CSV export by itself |
| `export_archive` | `report.export_panel` | must not imply report-ready package/archive |
| `share_result` | `report.export_panel` | must not enable sharing workflow by itself |
| `result_clear` | `report.export_panel` | must not alter result state or deletion behavior |

No candidate uses `result.semantic.formal_computed_result` or `report.status.report_ready`.

## 5. Small-Size Limitation

The `export_pdf`, `export_excel`, and `export_csv` candidates include format text. The text is intended as an additional cue and is clearer at 48 / 64 px. At 24 px it should not be the only semantic cue in active UI.

Future active replacement should verify:

- icon-only affordance clarity at the final rendered size
- disabled export button states
- tooltip / label pairing for export formats
- no visual escalation from draft/testing to report-ready

## 6. Deferred Scope Confirmation

This stage did not process or replace:

- status icons
- empty-state illustrations
- App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices resources
- active `assets/**` resources
