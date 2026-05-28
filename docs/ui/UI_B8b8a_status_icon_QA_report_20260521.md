# UI-B8b8a Status Icon QA Report

## 1. Scope

This QA report covers only the 10 `status` production candidate icons generated under `docs/ui/icon_production/status/`.

In scope:

- `status_testing`
- `status_planned`
- `status_shell_only`
- `status_developer_preview`
- `status_blocked`
- `status_available`
- `status_not_configured`
- `status_failed`
- `status_preflight_only`
- `status_draft`

Out of scope:

- active UI loader changes
- active asset replacement under `assets/icons/status/`
- Result / Report / Export icons
- empty-state illustrations
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices
- status chip behavior changes
- feature availability, report-ready, formal result, export, install, or analysis state changes

## 2. Candidate Completeness

| resource_id | svg | png 24 | png 32 | png 48 | png 64 | qa_status |
|---|---:|---:|---:|---:|---:|---|
| `status_testing` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_planned` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_shell_only` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_developer_preview` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_blocked` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_available` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_not_configured` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_failed` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_preflight_only` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |
| `status_draft` | yes | yes | yes | yes | yes | `passed_candidate_status_semantic_review_required` |

All 10 candidates have independent SVG files and 24 / 32 / 48 / 64 px PNG exports.

## 3. Vector And Transparency QA

| check | result |
|---|---|
| SVG files are independent vector files | pass |
| SVG files do not embed placeholder PNGs | pass |
| SVG files do not contain raster `<image>` references | pass |
| PNG exports use transparent canvas | pass |
| PNG exports have expected square sizes | pass |
| Candidate files remain under `docs/ui/icon_production/status/` | pass |
| No files were written to `assets/icons/status/` | pass |

## 4. Semantic QA

| resource_id | semantic_key | guardrail |
|---|---|---|
| `status_testing` | `feature.status.testing` | must not imply production readiness |
| `status_planned` | `feature.status.planned` | must remain visually future/disabled |
| `status_shell_only` | `feature.status.shell_only` | must not imply implemented business capability |
| `status_developer_preview` | `feature.status.developer_preview` | must stay preview/testing-level |
| `status_blocked` | `feature.status.blocked` | must indicate prerequisite gate rather than user blame |
| `status_available` | `resource.status.available` | must not imply auto-install or formal analysis readiness |
| `status_not_configured` | `resource.status.not_configured` | must be distinct from failed |
| `status_failed` | `resource.status.failed` | must not imply data loss |
| `status_preflight_only` | `analysis.status.preflight_only` | must not imply formal analysis completed |
| `status_draft` | `report.status.draft` | must not imply report-ready output |

All status candidates remain high risk until UI-B8b8b semantic gating review.

## 5. Deferred Scope Confirmation

This stage did not process or replace:

- Result / Report / Export active icons
- empty-state active illustrations
- App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices resources
- active `assets/**` status resources
