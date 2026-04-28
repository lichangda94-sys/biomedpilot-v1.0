# v0.16 Profile-To-Reporting Baseline

The v0.16 baseline documents the current minimum closed loop from analysis profile definition to report display, task result diagnostics, task plan summaries, materialization readiness, execution contract readiness, and mock runner diagnostics:

`AnalysisProfile` -> `EngineReadyAnalysisConfig` -> Module 5 profile consumption -> Module 6 reporting summary -> Module 7 task/result registration -> artifact diagnostics -> task plan summary -> materialization readiness -> execution contract readiness -> mock runner diagnostics -> UI read-only display.

## Current Capabilities

- Module 4A: extraction rule diagnostics are surfaced through repo smoke/check reporting as a consumer-facing summary.
- Module 4B: analysis profile rules include `GenePanel`, `ComparisonRule`, `KeywordRuleSet`, `ThresholdProfile`, and `AnalysisProfile`.
- Module 4B: `AnalysisProfileService` can export an `EngineReadyAnalysisConfig`.
- Module 5: analysis can be created from an exported profile engine config.
- Module 6: reporting summaries include analysis profile source metadata.
- Module 7: task/result store, profile reporting result registration, and artifact diagnostics.
- Module 7: task plan records capture future analysis/reporting task metadata.
- Module 7: task plan states include `draft`, `ready`, `disabled`, and `archived`.
- Module 7: ready task plans can be manually materialized into pending task records.
- Module 7: task plan materialization readiness diagnostics report materializable and blocked plans.
- Module 7: task execution request/outcome models define a future executor contract.
- Module 7: task execution contract readiness diagnostics report contract-ready and blocked task records.
- Module 7: mock task runner returns contract-level outcomes without real execution.
- Module 7: runner adapter registry foundation can register and look up no-op adapters by task type.
- Smoke/check: reports task result artifact diagnostics.
- Smoke/check: reports task plan state counts without executing ready plans.
- Smoke/check: reports task plan materialization readiness without materializing plans.
- Smoke/check: reports task execution contract readiness without executing tasks.
- Smoke/check: reports mock runner dry-run diagnostics without executing tasks.
- Smoke/check: reports runner adapter registry diagnostics without executing adapters.
- UI: the main window can display a reporting summary.
- UI: the main window can select an analysis id and load the corresponding reporting summary.
- UI: the main window can display registered task results as a read-only summary.
- UI task result summaries include read-only artifact readiness counts/status values.
- UI task result summaries include read-only task plan state counts.
- UI task result summaries include read-only task plan materialization readiness counts.
- UI task result summaries include read-only task execution contract readiness counts.
- UI task result summaries include read-only mock runner dry-run diagnostics counts.
- UI task result summaries include read-only runner adapter registry diagnostics.

## Artifact Diagnostics Status

- `present`: `artifact_path` is set and the file exists.
- `missing`: `artifact_path` is set but the file is missing.
- `not_applicable`: the result has no `artifact_path`.

## TaskPlanState

- `draft`: the plan is being prepared.
- `ready`: the plan is ready for future scheduler consumption, but is not executed.
- `disabled`: the plan is intentionally inactive.
- `archived`: the plan is retained for history.

## Materialization Readiness

- `materializable`: a `ready` plan can be manually materialized.
- `blocked`: the plan cannot currently be materialized.
- `draft`: the plan is not ready.
- `disabled`: the plan is intentionally inactive.
- `archived`: the plan is retained for history.
- `missing context`: required plan metadata is missing, if applicable.

Manual materialization uses `materialize_task_plan()`. Only `ready` plans can be materialized, and materialization creates a pending `TaskRecord`. It does not execute the task, create a result, create an artifact, start a scheduler, or change workflow behavior. Readiness diagnostics do not call `materialize_task_plan()`.

The UI can now materialize one selected `ready` task plan after `MATERIALIZE PLAN <plan id>` confirmation. Draft, disabled, archived, and missing plans are rejected with stable messages. The source `TaskPlanRecord.state` remains unchanged, and the materialized pending task still requires separate dry-run or explicit manual real-run before execution. UI materialization does not create results, create artifacts, scan plans, or start scheduler behavior.

## Task Execution Contract

`TaskExecutionRequest` and `TaskExecutionOutcome` are contract-layer models for a future executor or scheduler. `build_task_execution_request()` converts an existing `TaskRecord` into a dry-run request by default, preserving source plan, analysis, profile, project, parameters, and requester metadata. Contract validation checks required fields only; it does not call Module 5 or Module 6 execution, create results, create artifacts, or change task state.

Task execution contract readiness diagnostics report whether existing task records can build and validate a dry-run request. Ready tasks are only contract-ready; diagnostics do not execute them. Blocked tasks report missing context or validation failure.

`run_task_execution_request_mock()` validates a `TaskExecutionRequest` and returns a no-op `TaskExecutionOutcome`. Dry-run requests are accepted as skipped, invalid requests are rejected, and no task, analysis, reporting, result, or artifact execution occurs.

Mock runner diagnostics summarize dry-run checks in smoke/check output and in the UI task results summary: total checks, accepted dry-run outcomes, rejected outcomes, and validation-failed outcomes. The UI does not provide a mock runner execute control.

`RunnerAdapterRegistry` and `NoOpRunnerAdapter` provide a future adapter lookup foundation. The registry is not wired into execution, and the no-op adapter only returns `not_implemented` outcomes.

Runner adapter registry diagnostics summarize registered adapter counts, adapter types, supported task types, and no-op adapter counts in smoke/check output and in the UI task results summary. These diagnostics do not call adapter `execute()` and do not require a real runner.

The first real adapter foundation is `ReportingSummaryRunnerAdapter` for `task_type=profile_reporting_summary`. Its expected input is an existing `analysis_id`, `project_id`, and optional `format=analysis_summary_csv`; its output is an exported reporting summary CSV registered as a `profile_reporting_summary` result.

`validate_reporting_summary_runner_request()` is the first validation-only step toward that adapter. It checks the request contract without calling Module 5, calling Module 6, exporting a CSV, registering a result, creating an artifact, or executing a task.

`ReportingSummaryRunnerAdapter` keeps dry-run behavior side-effect free. It supports `profile_reporting_summary`, returns accepted/skipped outcomes for valid dry-run requests, and only calls `ReportingService` for validated `dry_run=False` requests with configured services.

For `dry_run=False`, the adapter validates first, calls `ReportingService.export_analysis_summary_csv(analysis_id)`, registers one `profile_reporting_summary` task result after export succeeds, and returns a `TaskExecutionOutcome` with the registered result id. It does not mutate task state, start a scheduler, expose a UI execute button, call Module 5, or use production downloads.

Visibility audit: generated `profile_reporting_summary` results appear in generic task result lists, artifact diagnostics, the read-only task result UI, and a dedicated smoke/check result summary. The dedicated smoke/check summary reports total profile reporting summary results plus present, missing, and not-applicable artifacts without invoking the runner or creating new results. The read-only UI table already shows result type, analysis id, profile, artifact path, and artifact status, so a dedicated UI runner-result count is not necessary yet.

Version markers: `v0.19-first-real-reporting-runner` marks the first real `profile_reporting_summary` runner foundation, `v0.20-reporting-runner-smoke-visibility` marks dedicated smoke/check visibility, and `v0.21-reporting-runner-visibility-baseline` marks the UI visibility audit.

Manual wrapper foundation: `TaskManagementService.execute_task_with_adapter(...)` can explicitly build a request for one task, find a runner adapter by task type, and call the adapter. It defaults to dry-run, does not scan tasks, does not start a scheduler, does not connect a UI execute button, and does not mutate task state. `v0.22-manual-runner-wrapper` marks this wrapper plus smoke/check diagnostics for dry-run checks and missing adapters.

Lifecycle wrapper foundation: `TaskManagementService.execute_task_with_lifecycle(...)` adds explicit lifecycle handling for one task. Dry-run calls keep state unchanged. Explicit non-dry-run calls require a pending task and can move it through `pending -> running -> completed` or `pending -> running -> failed`. Smoke/check reports lifecycle dry-run checks and state mutations without calling `dry_run=False`, creating results, creating artifacts, or executing real reporting. It does not scan tasks, start a scheduler, add UI execution, call Module 5, or change `geo_workflow.py`.

UI manual execute prerequisites are documented but not implemented. A future button would need one selected pending task, explicit confirmation, a dry-run preflight path, visible rejected outcome/error handling, and summary refresh after execution. The current baseline still has no UI execute button and no scheduler.

Execution log baseline: `TaskExecutionLogRecord` entries are stored in `task_execution_logs.json`. `scripts/run_task_once.py` appends one log per CLI invocation after the lifecycle outcome is returned. Smoke/check and the UI task results summary report total logs, dry-run logs, real-run logs, success/accepted logs, failed/rejected logs, and logs with result ids. These summaries are read-only and do not execute tasks, scan tasks, create results, create artifacts, or mutate task state. `v0.25-execution-log-baseline` marks this execution log store, CLI logging, smoke/check summary, and UI summary.

Local dataset standardization planning: `docs/local_dataset_standardization.md` and `docs/geo_submission_readiness.md` define the processed-file-only path for local sequencing-company deliveries. The planned path standardizes count/TPM/FPKM/normalized expression matrices, sample metadata, gene annotation, QC reports, and DEG result files into project-local standard assets. It explicitly excludes FASTQ/BAM/CRAM content parsing, alignment, quantification, FastQC/MultiQC, DESeq2/edgeR/limma, GEO auto submission, production downloader changes, and `geo_workflow.py` changes.

Standard asset compatibility contract: GEO, TCGA/GTEx, sequencing-company delivery, and GEO-ready local package adapters should normalize into `StandardExpressionMatrix`, `StandardSampleMetadata`, `StandardGeneAnnotation`, `StandardDatasetManifest`, `StandardValidationReport`, and optional `StandardQCReport`. Module 5 can then reuse the same asset contract for future analysis planning, and the UI can display validation/GEO readiness without depending on source-specific directory structures.

`v0.33-local-dataset-standardization` records the processed-file-only local standardization baseline: local delivery scanner, selected import plan, standardizer output, validation report, GEO submission readiness checker, and standard asset compatibility contract. It still excludes FASTQ/BAM/CRAM parsing, alignment, FastQC/MultiQC, DESeq2/edgeR/limma, GEO automatic submission, production downloader changes, and `geo_workflow.py` changes.

## Current Boundaries

- no `geo_workflow.py` changes
- no production TCGA/GDC/GTEx downloader
- no scheduler
- no scheduler-driven runner
- no scheduler-driven reporting runner
- no automatic runner adapter execution
- no runner adapter execution from smoke/check or UI summaries
- no task execution
- no Module 5/6 execution from the task contract
- no Module 5/6 execution from the mock runner
- no task execution from contract readiness diagnostics
- no automatic materialization
- no workflow blocking
- no background thread, queue, or timer
- no automatic ready-plan scanning
- no task plan execution
- no task plan create/edit/delete UI
- no task plan edit/delete UI
- no task execution contract action UI
- no mock runner action UI
- no TaskResultRecord creation during task plan materialization
- no TaskRecord creation during task plan materialization readiness diagnostics
- no TaskResultRecord or artifact creation during materialization
- no smoke/check scheduling of ready plans
- no UI scheduling or execution of ready plans
- ready plans are reporting-only and do not execute
- no workflow blocking by RuleService diagnostics or missing artifacts
- no real-data dependency
- no task result editing from UI
- no artifact creation or deletion during diagnostics
- UI summaries remain read-only for task results, artifact diagnostics, and task plans
- UI task plan materialization only creates a pending task from a selected ready plan after confirmation
- UI execution paths remain selected-task gated and do not schedule or scan tasks

## Validation

Recommended baseline checks:

```bash
python3 scripts/run_smoke_tests.py
python3 -m unittest tests.test_task_plan_service
python3 -m unittest tests.test_task_management_service
python3 -m unittest tests.test_task_results_summary_widget
python3 -m unittest tests.test_main_window_reporting_summary
python3 -m unittest discover -s tests
```

Optional focused checks:

```bash
python3 -m unittest tests.test_analysis_profile_service
python3 -m unittest tests.test_analysis_profile_consumption
python3 -m unittest tests.test_reporting_service
python3 -m unittest tests.test_main_window_reporting_summary
```

If PySide6 is not installed, related UI tests skip by test design.

## Status Audit

- `docs/v0_15_status_audit.md`
- `docs/development_baseline_index.md`
- `docs/real_geo_dataset_readiness.md`

## Real GEO Readiness Planning

`docs/real_geo_dataset_readiness.md` documents the next readiness layer needed before applying the analysis/reporting path to real GEO datasets. It covers unreliable GEO file candidates, expression matrix detection, sample metadata completeness, gene/probe/symbol/Ensembl mapping risks, sample id alignment, comparison detection, preflight checks, UI warnings, and practical readiness-test records.

This is currently an audit-only baseline. It does not implement a GEO DEG runner, download real GEO data, connect a production downloader, change `geo_workflow.py`, or alter Module 4/5/6 schemas.

Module 5 comparison readiness now has a fake-input foundation through `ComparisonReadinessReport` and `build_comparison_readiness_report(...)`. It checks explicit case/control availability before analysis but does not execute DEG or infer groups from real GEO metadata.

`AnalysisPreflightSummary` and `build_analysis_preflight_summary(...)` aggregate dataset assets, gene mapping, sample mapping, and comparison readiness into a runnable/non-runnable analysis preflight report. The summary is still pre-execution only and does not run Module 5 analysis.

`scripts/run_fake_geo_preflight.py` is the fake-data CLI baseline for the readiness path. It validates asset readiness, gene mapping readiness, sample mapping readiness, comparison readiness, and analysis preflight summary construction using in-memory fixtures only. It is included in quick developer checks and does not download GEO data, execute analysis, create task results, create artifacts, or write execution logs.

## Baseline Tags

- `v0.3-module4-rule-consumer`
- `v0.4-module4-analysis-profiles`
- `v0.5-module5-profile-consumption`
- `v0.6-module6-profile-reporting`
- `v0.7-ui-reporting-summary-data`
- `v0.8-ui-analysis-result-selection`
- `v0.9-module7-task-results`
- `v0.10-ui-task-results-summary`
- `v0.11-module7-artifact-diagnostics`
- `v0.12-ui-artifact-diagnostics`
- `v0.13-ui-task-plan-summary`
- `v0.14-ui-task-plan-materialization-readiness`
- `v0.15-ui-execution-contract-readiness`
- `v0.16-ui-mock-runner-diagnostics`
- `v0.17-local-readiness-baseline`
- `v0.18-ui-task-results-polish`
- `v0.19-runner-adapter-foundation`
- `v0.19-first-real-reporting-runner`
- `v0.20-reporting-runner-smoke-visibility`
- `v0.21-reporting-runner-visibility-baseline`
- `v0.22-manual-runner-wrapper`
- `v0.23-lifecycle-runner-wrapper`
- `v0.24-cli-manual-runner`
- `v0.25-execution-log-baseline`
- `v0.29-real-run-hardening-retry-foundation`
- `v0.30-artifact-preview-baseline`
- `v0.31-result-detail-viewer`

## v0.13 And v0.14

- `v0.13-ui-task-plan-summary`: TaskPlan foundation, smoke/check summary, and UI read-only task plan summary.
- `v0.14-ui-task-plan-materialization-readiness`: manual plan materialization and materialization readiness diagnostics in smoke/check and UI.
- `v0.15-ui-execution-contract-readiness`: TaskExecutionRequest/TaskExecutionOutcome and execution contract readiness diagnostics in smoke/check and UI.
- `v0.16-ui-mock-runner-diagnostics`: mock/no-op runner diagnostics in smoke/check and UI.
- `v0.25-execution-log-baseline`: task execution log store, CLI outcome logging, smoke/check execution log summary, and UI read-only execution log summary.
- `v0.29-real-run-hardening-retry-foundation`: UI gated real-run behavior audit, hardened confirmation gate, hardened outcome refresh, failed retry policy audit, retry task record foundation, smoke/check retry summary, UI read-only retry task summary, and selected-task retry creation UI. Retry creation makes a new pending retry task from a failed task after confirmation, leaves the original failed task unchanged, and does not execute the retry or create results/artifacts. It still has no scheduler, no automatic task scan, no production downloader, no retry execute button, no Module 4/5/6 schema changes, and no `geo_workflow.py` changes.
- `v0.30-artifact-preview-baseline`: `ArtifactPreviewRecord`, `preview_result_artifact(result_id, max_chars=4000)`, and UI read-only artifact preview panel for `.csv`, `.json`, `.txt`, and `.md` artifacts. Preview does not edit, delete, execute, or open artifacts externally; result detail viewer is the next planned capability.
- `v0.31-result-detail-viewer`: `TaskResultDetailRecord`, `get_task_result_detail(result_id)`, and UI read-only result detail viewer. Result detail displays metadata and artifact status; artifact content remains in the artifact preview panel. Result edit/delete/rerun, scheduler, production downloads, and `geo_workflow.py` changes remain out of scope.

## v0.35 GPL570 Mapping Readiness Baseline

GSE33630 readiness now has a fake/local fixture foundation for GPL570 probe-to-symbol mapping readiness. `PlatformAnnotationMappingReport` and the preflight bridge can represent whether platform mapping is acceptable before any DEG runner is considered. No real GPL570 download, DEG execution, production downloader change, or `geo_workflow.py` change is included.
