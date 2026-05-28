# UI-C2a Bioinformatics State And Action Gate Contract

## 1. Purpose

This contract defines the state model, action gates, disabled-action rules, and result/report/export gates required before Bioinformatics mockups can be implemented safely in the UIShell runtime.

## 2. Required State Model

Every Bioinformatics target page should expose stable properties for tests and future i18n:

| Field | Required values / shape | Purpose |
| --- | --- | --- |
| `pageKey` | `bio.page.project_home`, `bio.page.data_source`, `bio.page.data_check_preparation`, `bio.page.group_design`, `bio.page.analysis_tasks`, `bio.page.result_report`, `bio.page.report_export` | Stable page identity |
| `moduleKey` | `module.bioinformatics` | Stable module identity |
| `statusKey` | `testing`, `planned`, `shell_only`, `developer_preview`, `blocked`, `preflight_only`, `draft` | Visible status chip |
| `statusSemanticKey` | `feature.status.*`, `analysis.status.*`, `report.status.*`, `resource.status.*` | Source of truth for status meaning |
| `dataStateKey` | `no_project`, `source_registered`, `input_preflight_ready`, `design_preflight_ready`, `task_preflight_ready`, `result_available`, `empty_result` | Current page data state |
| `gateState` | `enabled`, `disabled`, `blocked`, `hidden_until_ready`, `developer_diagnostics_only` | Determines action behavior |
| `disabledReasonKey` | Stable blocker key such as `blocked_missing_resolver` | Testable reason for disabled state |
| `resultSemanticKey` | `preflight_only`, `testing_level`, `exploratory`, `imported_external_result`, `formal_computed_result`, `not_a_result` | Result truth source |
| `reportStatusKey` | `draft`, `testing_summary`, `blocked`, `report_ready_future`, `report_ready` | Report boundary |
| `exportGate` | `disabled_empty_result`, `disabled_missing_report_ready`, `disabled_missing_file_picker`, `enabled_report_ready_package` | Export truth source |

## 3. Page State Defaults

| Page | Default status | Default result semantic | Default report status | Default export gate |
| --- | --- | --- | --- | --- |
| Project Home | `feature.status.developer_preview` | `not_a_result` | `draft` | `disabled_empty_result` |
| Data Source | `feature.status.testing` | `not_a_result` | `draft` | `disabled_empty_result` |
| Data Check & Preparation | `analysis.status.preflight_only` | `preflight_only` | `draft` | `disabled_empty_result` |
| Group & Design | `analysis.status.preflight_only` | `preflight_only` | `draft` | `disabled_empty_result` |
| Analysis Tasks | `analysis.status.preflight_only` or `analysis.status.blocked` | `preflight_only` | `draft` | `disabled_empty_result` |
| Result & Report | `feature.status.testing` | `testing_level` unless result registry says otherwise | `draft` | `disabled_missing_report_ready` |
| Report Export | `report.status.draft` | Must mirror selected result | `draft` | `disabled_missing_report_ready` |

## 4. Action Gate Model

Every user-facing action row should be represented as:

```text
action_id
label
page_key
visible
enabled
gate_state
button_behavior
required_gates
disabled_reason_key
normal_user_visible
developer_diagnostics_allowed
preserves_result_semantic_key
preserves_report_status_key
preserves_export_gate
```

Allowed `button_behavior` values:

| Behavior | Meaning |
| --- | --- |
| `enabled_navigation_only` | Page navigation, no backend execution |
| `enabled_preflight_only` | Runs or opens preflight/checking only |
| `enabled_copy_only` | Copies existing text/table only |
| `enabled_review_only` | Opens existing result/review only |
| `disabled_missing_resolver` | Missing standardized repository or resolver package |
| `disabled_missing_storage_adapter` | UI cannot persist safely |
| `disabled_missing_file_picker` | Export requires file picker adapter |
| `blocked_until_backend` | Backend or executor not implemented in current runtime |
| `hidden_until_ready` | Hide from normal UI until product gate lands |
| `developer_diagnostics_only` | May exist under diagnostics, not normal workflow |

## 5. Formal DEG Gate

Formal DEG can only be enabled when all gates pass:

1. Standardized repository and analysis input package exists.
2. `deg_recompute` package exists and has no blockers.
3. DEG-ready package passes value type, sample metadata, group design, and identifier mapping checks.
4. Backend dependencies pass.
5. Parameter manifest passes.
6. User confirmation passes.
7. Result schema gate passes.
8. Result registry is available.
9. Output plan writes through approved project storage, not an implicit runtime path.

If any gate is missing in UIShell, `Run controlled two-group DEG` must be disabled.

## 6. ORA / GSEA Gate

Current UIShell has a local ORA-style enrichment runner and preflight services. This does not prove a product-ready ORA/GSEA workflow.

Required future gates:

- Validated DEG or ranked input result.
- Gene set resource manager and resource status.
- Rank metric validation for preranked GSEA.
- Result schema for ORA/GSEA.
- Plot/report semantics.
- Report-ready exclusion for testing/exploratory outputs.

`dev/bioinformatics` explicitly marks `formal_gsea` as `hidden_until_ready`; UIShell should follow that boundary.

## 7. Survival / Cox Gate

KM/log-rank and Cox can only be enabled after scoped carry-over confirms:

- Survival clinical input package.
- Survival dependency snapshot passed.
- Parameter manifest passed.
- User confirmation passed.
- Result schema validation passed.
- Result registry write path approved.
- Report-ready remains false unless a later report gate exists.

Clinical variable audit and survival input preflight may be visible as preflight/testing pages. They must not produce clinical conclusions.

## 8. Result / Report / Export Gate

| Gate | Requirement |
| --- | --- |
| Result display | Result entry must have normalized `resultSemanticKey` |
| Formal result display | Only allowed for `formal_computed_result` from result registry |
| Imported result display | Must show `imported_external_result`, not BioMedPilot recomputed result |
| Testing/preflight display | Must show testing/preflight label and cannot feed report-ready by default |
| Report draft | Allowed for summary/draft text |
| Report-ready | Requires explicit report-ready gate and eligible result |
| Export | Requires report-ready package gate plus file picker/export adapter |

Default export buttons must keep:

- `enabled=false`
- `exportGate=disabled_missing_report_ready`
- `reportStatusKey=draft`
- `resultSemanticKey` matching selected result or `testing_level`

## 9. Button Disable Rules By Page

| Page | Enabled now | Disabled now |
| --- | --- | --- |
| Project Home | open existing page, create/open project if existing runtime supports it | formal run, report-ready, export |
| Data Source | source selection, local/GEO/TCGA/GTEx card navigation | auto merge TCGA+GTEx, direct analysis run |
| Data Check & Preparation | run/view preflight where existing runtime supports it, copy summary | save formal report, execute analysis |
| Group & Design | edit/review in-memory design, copy summary | persistent save, multifactor DEG, Cox modeling |
| Analysis Tasks | open preflight panels, developer diagnostics if explicitly exposed | formal DEG, formal ORA/GSEA, KM/log-rank, Cox, clinical conclusion |
| Result & Report | view testing/imported/preflight entries, draft preview | fake plots, report-ready generation |
| Report Export | view gate status | PDF/DOCX/ZIP/export package |

## 10. Test Requirements For Implementation

Focused UI tests should assert:

- Page keys and module keys are stable.
- Seven main-flow pages remain present and ordered.
- Result & Report and Report Export are separate pages.
- All formal task buttons are disabled unless gates are imported and passing.
- TCGA+GTEx auto-merge is not default.
- Preflight rows are not treated as formal results.
- `resultSemanticKey`, `reportStatusKey`, and `exportGate` are preserved on result/report/export surfaces.
- No fake chart, fake table, fake p-value, fake formal report, or fake export package appears.

## 11. Implementation Decision

UIShell should first adopt the state/action/result/report gate contract before any formal executor carry-over. This keeps the mockup implementation visually useful while preventing accidental activation of unreviewed analysis capability.
