# UI-B8b8b Status Icon Semantic Gating Review

## 1. Scope

This stage reviews the 10 UI-B8b8a `status` production candidates for possible future active replacement pilot eligibility.

Inputs reviewed:

- `docs/ui/UI_B8b8a_status_icon_final_asset_production_report_20260521.md`
- `docs/ui/UI_B8b8a_status_icon_QA_report_20260521.md`
- `docs/ui/icon_production/UI_B8b8a_status_icon_production_manifest_20260521.csv`
- `docs/ui/icon_production/status/`
- `tests/ui/test_status_icon_production_manifest.py`
- `tests/ui/test_ui_primitives.py`
- `tests/shared/test_semantic_keys.py`

Output manifest:

- `docs/ui/UI_B8b8b_status_icon_semantic_gating_manifest_20260521.csv`

## 2. Boundary Statement

This is a semantic gating review only.

Not changed:

- `app/**` active UI code
- active UI loader
- `assets/icons/status/`
- status chip implementation
- semantic key registry
- feature availability
- analysis execution gates
- report-ready gates
- export gates
- Result / Report / Export icon state
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices

No packaged app was run. No packaging, codesigning, or desktop app replacement was performed.

## 3. Current Status Semantics Review

The current shell already carries status semantics through `statusKey` and `semanticKey` properties. The icon candidates must not become a second source of truth.

| area | current semantic boundary |
|---|---|
| feature status | `testing`, `planned`, `shell_only`, `developer_preview`, and `blocked` remain non-production status keys |
| resource status | `available`, `not_configured`, and `failed` remain detect-first resource state markers |
| analysis status | `preflight_only` does not imply formal analysis execution |
| report status | `draft` does not imply report-ready package or formal export |
| active status assets | no `assets/icons/status/` active replacement exists in this stage |
| active loader | unchanged |

## 4. Gating Decisions

| resource_id | decision | pilot_allowed | active_usage_allowed | allowed_surface |
|---|---|---:|---:|---|
| `status_testing` | `pilot_allowed` | true | true | `status_chip_only` |
| `status_planned` | `pilot_allowed` | true | true | `status_chip_only` |
| `status_shell_only` | `pilot_allowed` | true | true | `status_chip_only` |
| `status_developer_preview` | `pilot_allowed` | true | true | `status_chip_only` |
| `status_blocked` | `pilot_allowed` | true | true | `blocked_status_chip_only` |
| `status_available` | `conditional_pilot_allowed` | true | true | `detected_resource_status_chip_only` |
| `status_not_configured` | `pilot_allowed` | true | true | `resource_status_chip_only` |
| `status_failed` | `pilot_allowed` | true | true | `resource_status_chip_only` |
| `status_preflight_only` | `pilot_allowed` | true | true | `analysis_status_chip_only` |
| `status_draft` | `pilot_allowed` | true | true | `report_status_chip_only` |

## 5. Initial Pilot Allow List

All 10 status icons may enter a future active replacement pilot only under status-chip constraints.

Allowed usage:

- inline status chip marker
- resource row status marker
- analysis status marker
- report draft status marker
- blocked/developer-preview/planned/testing marker where visible text remains present

Required constraints:

- visible text label must remain
- tooltip or nearby copy must preserve status meaning when the icon appears alone or near a gated action
- `statusKey` must not change
- `semanticKey` must not change
- disabled/gated state must remain when the surrounding action is disabled
- icon must not become proof of analysis completion, report readiness, export readiness, local installation, cloud availability, or formal result availability

## 6. Conditional Resource-Available Rule

`status_available` is the only conditional allow decision.

It may be used only when the existing runtime state has already set `resource.status.available` through detect-first logic. It must not be used as:

- install success indicator unless install logic already exists and separately proves success
- cloud connection indicator
- model inference availability indicator
- ImageJ/Fiji activation indicator outside Settings external capability state
- LabTools feature availability indicator

## 7. Blocked And Formal-State Risks

No candidate is allowed to represent:

- `result.semantic.formal_computed_result`
- `report.status.report_ready`
- `report.status.report_ready_future`
- enabled export
- formal analysis execution
- fake DEG, GSEA, survival, clinical association, chart, table, statistics, or report-ready package

The future active pilot must remain visual-only and must not change any feature availability or analysis/report gate.

## 8. Test Coverage

Added focused test:

- `tests/ui/test_status_icon_semantic_gating_review.py`

The test verifies:

- all 10 status icons have a semantic gating decision
- all candidate paths remain under `docs/ui/icon_production/status/svg/`
- no row points to `assets/icons/status/`
- active `assets/icons/status/` remains absent in this review stage
- every allowed row requires visible label, semantic key preservation, status key preservation, and gate preservation
- `status_available` remains conditional and detect-first
- no formal computed result or report-ready semantics enter the gating manifest
- current status chip primitive still exposes existing `statusKey` and `semanticKey` properties

## 9. Verification

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui/test_status_icon_semantic_gating_review.py` | passed, 7 tests |
| `python3 -m pytest -q tests/ui/test_status_icon_production_manifest.py` | passed, 6 tests |
| `python3 -m pytest -q tests/ui/test_ui_primitives.py tests/shared/test_semantic_keys.py` | passed, 9 tests |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 10. Recommendation

UI-B8b8c may proceed as a status active pilot only if it remains limited to status-chip and status-row surfaces.

The active pilot must not:

- write status icons into action buttons as proof of availability
- make planned/shell-only/developer-preview/testing states appear completed
- make `preflight_only` appear as formal analysis output
- make `draft` appear as report-ready
- use `available` outside detect-first resource status context
- touch App icon, Finder icon, `.icns`, iconset, Info.plist, or LaunchServices
