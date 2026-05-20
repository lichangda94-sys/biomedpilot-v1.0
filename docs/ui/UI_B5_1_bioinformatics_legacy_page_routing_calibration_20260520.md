# UI-B5.1 Bioinformatics Legacy Page Routing Calibration

Date: 2026-05-20

Goal: calibrate current Bioinformatics legacy workflow pages against the target IA shell without deleting legacy pages, enabling formal analysis executors, generating fake results, replacing resources, packaging, or running the packaged app.

## 1. Scope

Allowed:

- Add explicit route metadata for legacy Bioinformatics pages.
- Map each legacy page to a target IA page or developer-diagnostic destination.
- Keep current workflow pages available for existing focused tests and developer validation.
- Add focused UI tests for route calibration metadata.
- Add this checkpoint document.

Forbidden in this stage:

- No formal DEG / GSEA / survival / clinical association execution.
- No fake figures, fake results, or report-ready package.
- No resource or icon replacement.
- No packaging, no packaged app run, no desktop `.app` overwrite.
- No rewrite of Bioinformatics business workflow pages.

## 2. Target IA Adjustment

UI-B5 previously exposed these target shell items:

```text
Project Home
Data Source
Data Check & Preparation
Group & Design
Analysis Tasks
Results
Report / Export
Settings Resources
```

UI-B5.1 adds the missing auxiliary destination:

```text
Project Logs & Technical Details
```

This makes the target shell align with the MasterPlan rule that logs, manifests, workflow status, raw JSON viewers, and feedback package details must not remain ordinary user-facing primary pages.

## 3. Legacy Route Mapping

| legacy_route | legacy_widget | target_page | status | visibility | decision |
|---|---|---|---|---|---|
| `project_home` | `bioinformaticsProjectHomePage` | `project_home` | `target_page` | `primary` | Keep as target Project Home shell. |
| `data_source` | `bioinformaticsDataSourcePage` | `data_source` | `target_page` | `primary` | Keep as target Data Source testing shell. |
| `chinese_search` | `bioinformaticsChineseDatasetSearchPage` | `data_source` | `folded_into_target` | `secondary` | Fold into Data Source; it must not bypass source registration or preflight. |
| `acquisition_status` | `bioinformaticsAcquisitionStatusPage` | `data_source` | `legacy_support` | `developer_diagnostic` | Keep only as technical detail for source registration. |
| `recognition` | `bioinformaticsRecognitionPage` | `data_check_preparation` | `folded_into_target` | `secondary` | Fold into Data Check & Preparation with preflight-only semantics. |
| `readiness` | `bioinformaticsReadinessDashboardPage` | `data_check_preparation` | `legacy_support` | `developer_diagnostic` | Keep as data-preparation diagnostic, not ordinary primary flow. |
| `standardized_assets` | `bioinformaticsStandardizedAssetsPage` | `data_check_preparation` | `folded_into_target` | `secondary` | Fold into Data Check & Preparation; resolver/input package remains gated. |
| `group_design` | `bioinformaticsGroupComparisonDesignPage` | `group_design` | `target_page` | `primary` | Keep as target Group & Design; not DEG-only. |
| `workflow_status` | `bioinformaticsWorkflowStatusPage` | `project_logs_technical_details` | `developer_diagnostic` | `developer_diagnostic` | Move to logs/technical details; not ordinary main flow. |
| `analysis_tasks` | `bioinformaticsAnalysisTaskCenterPage` | `analysis_tasks` | `gated_target` | `primary_gated` | Keep as gated target shell; formal executors remain blocked. |
| `results_browser` | `bioinformaticsResultsBrowserPage` | `results` | `testing_summary` | `secondary` | Keep as testing summary / imported external result surface. |
| `report_viewer` | `bioinformaticsReportViewerPage` | `report_export` | `report_draft` | `secondary` | Keep as report draft / testing summary only. |
| `settings` | `bioinformaticsSettingsAndLocalAIPage` | `settings_resources` | `settings_redirect` | `secondary` | Keep as module-level shell pointer to global Settings resources. |

## 4. Runtime Changes

Implemented:

- Added `BioinformaticsLegacyRoute` registry in `app/bioinformatics/workspace.py`.
- Added `bioinformatics_legacy_routes()` as the single route calibration source.
- Added target shell item `project_logs_technical_details`.
- Added disabled route calibration chips in the Bioinformatics target IA shell.
- Added per-page Qt properties:
  - `legacyRouteKey`
  - `targetPageKey`
  - `legacyRouteStatus`
  - `routeVisibility`
  - `developerDiagnostic`
  - `formalActionEnabled=False`
- Added public workspace helpers:
  - `legacy_route_keys()`
  - `legacy_route_calibration()`
  - `current_route_key()`
  - `current_target_page_key()`
  - `current_route_status()`
  - `current_route_visibility()`

Not changed:

- Existing legacy page classes remain mounted in the stack.
- Existing workflow navigation can still run for testing and developer validation.
- No business analysis behavior changed.

## 5. Acceptance

UI-B5.1 is accepted when:

- Target IA shell includes `Project Logs & Technical Details`.
- Legacy route mapping is visible as disabled calibration items.
- `recognition` routes to `data_check_preparation`.
- `workflow_status` routes to `project_logs_technical_details` and is marked developer diagnostic.
- `analysis_tasks` remains gated.
- `report_viewer` remains draft/testing-only.
- Existing full-stack workflow navigation still reaches legacy pages for tests.

## 6. Command Log

| command | result |
|---|---|
| `git status --short` | clean before UI-B5.1 edits. |
| `sed -n '1,380p' app/bioinformatics/workspace.py` | read current Bioinformatics target shell and legacy page stack. |
| `sed -n '1,220p' tests/ui/test_bioinformatics_ia_shell.py` | read focused Bioinformatics IA tests. |
| `rg -n "show_acquisition\|show_recognition\|show_readiness\|show_standardization\|show_workflow_status\|show_analysis_tasks\|show_results_browser\|show_report_viewer\|current_page_object_name" app/bioinformatics tests/ui tests/integration docs/ui` | identified direct legacy route usages and tests. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py` | passed after adding route registry tests. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py::test_workspace_navigation_reaches_full_stack` | passed; legacy stack navigation remains intact. |

## 7. Verification

Completed verification:

| command | result |
|---|---|
| `python3 -m app.main --smoke-test` | passed; source launch smoke reports `workspace_entries=3` and `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_bioinformatics_workflow_pages.py::test_workspace_navigation_reaches_full_stack` | passed; `8 passed in 1.40s`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | passed; `170 passed in 17.95s`. |
| `git diff --check` | passed, no whitespace errors. |
| `git status --short` | only `app/bioinformatics/workspace.py`, `tests/ui/test_bioinformatics_ia_shell.py`, and this document changed before staging. |

Full Bioinformatics workflow tests are not required for this routing calibration, because this stage does not rewrite business workflow pages.
