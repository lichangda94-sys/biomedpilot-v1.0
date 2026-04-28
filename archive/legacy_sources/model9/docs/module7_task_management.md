# Module 7 Task And Result Management

Module 7 adds a local task and result management foundation. It records task lifecycle state and task result metadata in JSON files under the application state directory, including profile reporting result registration and artifact diagnostics.

## Current Scope

- create task records
- transition tasks through `pending`, `running`, `completed`, and `failed`
- record result metadata for completed or failed tasks
- register profile reporting summary results with analysis/profile metadata
- inspect task result artifact readiness as diagnostics
- append task execution log records as audit metadata
- filter tasks by project or state
- filter results by task or result type
- filter execution logs by task id
- summarize execution logs in repo smoke/check output
- expose execution log summaries in the read-only UI summary
- persist records in local JSON files
- expose registered task results to a read-only UI summary
- surface artifact diagnostics in repo smoke/check summary
- record future task plans as planning metadata
- surface task plan state counts in repo smoke/check summary
- expose task plan state counts in the UI as a read-only summary
- manually materialize ready task plans into task records
- report task plan materialization readiness diagnostics
- define task execution request/outcome contract models
- report task execution contract readiness diagnostics
- provide a no-op mock task runner for contract-level outcome checks
- expose mock runner dry-run diagnostics in the UI as a read-only summary
- define a runner adapter registry for future task type to adapter lookup
- provide a `NoOpRunnerAdapter` that returns not-implemented outcomes without execution
- surface runner adapter registry diagnostics in repo smoke/check summary

Persisted files:

- `state/tasks.json`
- `state/task_results.json`
- `state/task_plans.json`
- `state/task_execution_logs.json`

## Boundaries

- no workflow scheduler yet
- no background worker pool
- no production TCGA/GDC/GTEx downloader
- no `geo_workflow.py` changes
- no real-data dependency
- no UI task orchestration yet
- no task result editing from UI
- no task plan execution
- no automatic ready-plan scanning
- no task execution runner
- no scheduler-driven runner
- no runner adapter is wired into task execution
- no automatic execution log creation from runner wrappers yet

Module 7 is a foundation for later orchestration and result management. It does not execute analysis, reporting, download, or extraction workflows by itself.

## Task Execution Logs

`TaskExecutionLogRecord` records execution events as audit metadata. It captures task id, source plan id, runner type, task type, dry-run flag, outcome status, message, error code, result id, metadata, and creation time.

Execution logs are stored in `state/task_execution_logs.json`. `TaskManagementService.append_task_execution_log(...)` appends one log record, `list_task_execution_logs()` returns all logs, and `list_task_execution_logs_for_task(task_id)` filters logs by task id.

Appending a log does not run a task, change `TaskRecord.state`, create `TaskResultRecord`, create an artifact, call a runner adapter, start a scheduler, scan tasks, or connect to UI execution.

`summarize_task_execution_logs()` reports total logs, dry-run logs, real-run logs, success/accepted logs, failed/rejected logs, and logs with result ids. This summary is surfaced through `scripts/run_smoke_tests.py` and the UI task results summary as read-only diagnostics. Smoke/check and UI reporting read existing logs only; they do not append logs, execute tasks, create results, create artifacts, mutate task state, or block workflow.

## Task Plans

`TaskPlanRecord` describes a future analysis or reporting task as metadata. It can reference an analysis, analysis profile, project, requester, parameters, and notes.

Task plan states:

- `draft`: the plan is being prepared
- `ready`: the plan is ready for a future scheduler or operator
- `disabled`: the plan should not be used
- `archived`: the plan is retained for history

Task plans do not execute automatically. Creating or marking a plan `ready` does not start a scheduler, spawn a worker, run analysis, download data, create `TaskRecord`, create `TaskResultRecord`, or generate result artifacts. A later scheduler may consume task plans, but scheduler implementation is out of scope here.

Task plan summaries are surfaced through `scripts/run_smoke_tests.py`. A `ready` plan is a planning/readiness signal only; smoke/check reporting does not schedule or execute it.

Task plan summaries are also visible in the UI task results summary. The summary display remains read-only: it does not edit, delete, archive, schedule, or execute task plans.

Task plan materialization is a manual metadata conversion step. Only a `ready` plan can be materialized, and materialization creates a `TaskRecord` with source plan metadata such as `source_plan_id`, `analysis_id`, `analysis_profile_id`, `project_id`, and `parameters`. It does not execute the task, create `TaskResultRecord`, generate artifacts, start a scheduler, scan for ready plans, or change workflow behavior. The source `TaskPlanRecord` state remains unchanged.

Task plan materialization readiness diagnostics report which plans are eligible for manual materialization. A `ready` plan is reported as materializable; `draft`, `disabled`, and `archived` plans are reported as blocked with a reason code. Diagnostics are reporting-only: they do not create tasks, execute tasks, create results or artifacts, start a scheduler, scan and materialize plans, or change plan state.

Materialization readiness is visible in repo smoke/check output and in the UI task results summary as a read-only diagnostic summary. A materializable plan is not automatically materialized. UI materialization is an explicit selected-plan action with confirmation, and the project still has no scheduler.

Task plan materialize UI has been audited. The recommended first UI uses one selected plan id, requires task-bound confirmation such as `MATERIALIZE PLAN <plan id>`, and calls `materialize_task_plan(plan_id)` only for a `ready` plan. Materialization creates one pending `TaskRecord` with source plan metadata and leaves the source `TaskPlanRecord.state` unchanged. `draft`, `disabled`, `archived`, and missing plans should be rejected with stable messages. After successful materialization, the UI should show the new task id and refresh task summary, task plan summary, and materialization readiness. The UI must not execute the materialized task, create results, create artifacts, scan plans, start scheduler behavior, or change Module 4/5/6 schemas.

The task plan materialize UI foundation follows that boundary. Users enter one selected plan id and task-bound confirmation `MATERIALIZE PLAN <plan id>`. A ready plan can be materialized into a pending `TaskRecord`, with the new task id shown in the status area and summaries refreshed. Non-ready or missing plans are rejected with stable messages. The UI does not execute the materialized task, create results, create artifacts, change the original `TaskPlanRecord.state`, scan plans, or add scheduler behavior.

Materialized tasks remain normal pending tasks. They require the same separate dry-run or explicit manual real-run flow as any other task before execution. The materialize UI does not bypass lifecycle guards, does not append execution logs, and does not create `TaskResultRecord` entries or artifacts.

## Task Execution Contract

`TaskExecutionRequest` and `TaskExecutionOutcome` define the minimum contract a future executor or scheduler can use. The contract captures task id/type, source plan id, analysis/profile/project context, parameters, requester, dry-run intent, outcome status, messages, result id, error code, and metadata.

`build_task_execution_request()` converts an existing `TaskRecord` into a request object. It does not execute the task, call analysis or reporting services, create `TaskResultRecord`, create artifacts, start a scheduler, or mutate task state. `validate_task_execution_request()` only checks contract field completeness and does not call an analysis engine. The project still has no scheduler, runner, background queue, or timer.

Task execution contract readiness diagnostics report whether existing task records can build a dry-run `TaskExecutionRequest` and pass contract validation. A ready task is contract-ready only; diagnostics do not execute tasks, call Module 5 or Module 6, create results or artifacts, start a scheduler/runner, or mutate task state. Blocked tasks are reported with reason codes such as missing task id, missing task type, or validation failure.

Execution contract readiness is also visible in the UI task results summary as a read-only diagnostic summary. The UI does not provide run, execute, retry, or contract execution controls.

`run_task_execution_request_mock()` is a contract-level no-op runner helper. It validates a `TaskExecutionRequest` and returns a `TaskExecutionOutcome`: valid dry-run requests are accepted as skipped, and invalid requests are rejected with a contract validation error. The mock runner does not execute tasks, call Module 5 or Module 6, create `TaskResultRecord`, create artifacts, mutate task state, start a scheduler, or start a real runner.

Mock runner diagnostics are surfaced in repo smoke/check output and in the UI task results summary as dry-run checks. They report total checks, accepted dry-run outcomes, rejected outcomes, and validation-failed outcomes without executing tasks or creating results/artifacts. The UI is read-only and does not provide a mock runner execute button.

## Runner Adapter Registry

`TaskRunnerAdapter` defines the future adapter shape: `runner_type`, `supports(task_type)`, and `execute(request)`.

`RunnerAdapterRegistry` can register adapters, list adapters, find an adapter by `task_type`, and summarize adapter registration. This is lookup infrastructure only. It is not a scheduler, does not scan tasks, does not invoke adapters automatically, and is not wired into `TaskManagementService` execution.

`NoOpRunnerAdapter` supports explicit task types or a wildcard. Its `execute()` method returns a rejected `TaskExecutionOutcome` with `error_code="not_implemented"`. It does not execute tasks, call Module 5 or Module 6, create `TaskResultRecord`, create artifacts, mutate task state, start a scheduler, or start a real runner.

Runner adapter registry diagnostics are surfaced through `scripts/run_smoke_tests.py`. Smoke/check reporting lists registered adapter counts, adapter types, supported task types, and no-op adapter counts only. It does not call `execute()`, does not require a real runner, and does not fail because no real adapter exists.

Runner adapter registry diagnostics are also visible in the UI task results summary as read-only counts and type lists. The UI does not call adapter `execute()`, does not create results or artifacts, and does not provide an execute button.

`validate_reporting_summary_runner_request()` validates the `profile_reporting_summary` adapter input contract. It checks task id, task type, analysis id, and supported summary format only. It does not call Module 5, register a result, or create artifacts.

`ReportingSummaryRunnerAdapter` is the first minimal real runner foundation for `profile_reporting_summary`. It validates the request contract and returns a skipped/accepted dry-run outcome when `dry_run=True` without calling `ReportingService`, registering `TaskResultRecord`, or creating artifacts.

When `dry_run=False`, `ReportingSummaryRunnerAdapter` requires configured `ReportingService` and `TaskManagementService` dependencies plus `analysis_id` and `project_id`. It calls `ReportingService.export_analysis_summary_csv(analysis_id)` and registers one `profile_reporting_summary` `TaskResultRecord` after export succeeds. Result metadata includes `analysis_id`, `analysis_profile_id`, `project_id`, `source_task_id`, and `runner_type`. It does not call Module 5 and does not mutate task state.

Reporting runner failure policy is explicit: validation failure, missing runner dependencies, missing `project_id`, export failure, empty artifact path, or result registration failure return `accepted=False` with `status=rejected`, a stable `error_code`, and metadata `failure_result_policy=no_failed_result`. The adapter does not register a successful or failed `TaskResultRecord` for these failures, does not create an artifact after validation failure, and does not mutate `TaskRecord.state`.

Reporting runner task state transitions are owned by service-level wrappers. Current task states are `pending`, `running`, `completed`, and `failed`, and `TaskManagementService` exposes `start_task()`, `complete_task()`, and `fail_task()`. `ReportingSummaryRunnerAdapter` does not call those methods.

`execute_task_with_adapter(task_id, adapter_registry, dry_run=True)` is a manual service-level runner execution wrapper. It builds a `TaskExecutionRequest`, looks up the matching adapter by `task_type`, and calls that adapter only for the explicitly requested task. Missing adapters return a rejected outcome. The wrapper defaults to dry-run, does not scan tasks, does not start a scheduler, does not connect to UI execution, and does not mutate `TaskRecord.state`.

Manual runner wrapper diagnostics are surfaced through `scripts/run_smoke_tests.py`. Smoke/check runs dry-run wrapper checks only, reports accepted, rejected, and missing-adapter outcomes, and does not call `dry_run=False`, create results, create artifacts, mutate task state, or block workflow.

Task state transition implementation prerequisites are documented and implemented through a separate lifecycle-aware wrapper. `execute_task_with_adapter(...)` remains state-neutral. `execute_task_with_lifecycle(...)` validates before entering `running`, transitions successful explicit non-dry-run executions to `completed`, and treats post-running failures as `failed`. Scheduler, background queue, automatic scanning, UI execution, production downloads, and `geo_workflow.py` changes remain out of scope.

`execute_task_with_lifecycle(task_id, adapter_registry, dry_run=False)` is the lifecycle-aware manual runner wrapper. It only operates on one explicit task. `dry_run=True` delegates to the state-neutral wrapper and keeps the task `pending`. `dry_run=False` requires a `pending` task, moves it to `running`, calls the matching adapter, and marks it `completed` only when the adapter returns an accepted outcome with a registered result id. Rejected outcomes and adapter exceptions after entering `running` mark the task `failed`. Missing adapters and non-pending tasks return rejected outcomes without execution; the missing-adapter path keeps the task `pending`.

Task state lifecycle guards keep the safety boundary explicit: `pending` is the only executable state; `running`, `completed`, and `failed` are blocked by default. Completed tasks are not rerun implicitly, failed tasks require explicit retry task creation, and running tasks cannot be executed twice. Missing adapters keep the task `pending` because no execution has started. Dry-run remains state-neutral and returns a clear rejected outcome for non-pending tasks.

Lifecycle guard diagnostics are surfaced through `scripts/run_smoke_tests.py`. They report the guard policy for `pending`, `running`, `completed`, and `failed` tasks plus expected dry-run mutations. This diagnostics path is static/read-only: it does not execute tasks, create fake tasks, mutate task state, append logs, create results, or create artifacts.

UI execute button readiness has been re-audited after lifecycle hardening. The current prerequisites are sufficient for a future selected-task-only UI foundation: a single selected `pending` task, dry-run as the default path, explicit confirmation for real-run, hidden or disabled execution for `running`, `completed`, and `failed` tasks, and refresh of task state, results, artifact diagnostics, and execution logs after outcome. The UI execute button itself is still not implemented in this baseline.

The UI now includes a minimal manual dry-run execute entry point. Users can enter one selected task id and run a dry-run check through the existing lifecycle wrapper. The UI does not expose real-run execution, does not scan tasks, does not execute ready plans, does not create scheduler behavior, and refreshes task result, artifact, task plan, and execution log summaries after the dry-run outcome.

The UI also shows the most recent manual execute outcome as a read-only summary. The summary includes the dry-run flag, outcome status, message, error code, and result id when present. Missing task selection and rejected or blocked outcomes are displayed as stable text only; this view does not add a real-run button, change lifecycle wrapper behavior, create extra logs, create results, or create artifacts.

UI real-run preflight has been audited after the dry-run execute foundation. Real-run should remain CLI-only for now through `scripts/run_task_once.py --real-run`. A future UI real-run control should require a successful same-task dry-run preflight, a still-pending selected task, explicit confirmation, disabled controls during execution, and refresh of task state, results, artifact diagnostics, execution logs, and the latest outcome summary.

The UI now shows selected-task real-run preflight state as read-only text. It reports the selected task id, whether the task exists, current task state, pending eligibility, adapter availability, dry-run recommendation, UI real-run availability, and blocked reason for missing, non-pending, or unsupported-adapter tasks. This preflight display does not call dry-run or real-run execution, create logs, create results, create artifacts, mutate task state, or expose a real-run button.

Real-run preflight diagnostics are also surfaced through `scripts/run_smoke_tests.py`. The smoke/check summary reports checked tasks, eligible tasks, blocked tasks, missing adapters, and state mutations. This diagnostics path does not call dry-run execution, call real-run execution, append logs, create results, create artifacts, mutate task state, or block workflow.

The UI real-run button foundation is intentionally narrow. The real-run button stays disabled unless the selected task is still `pending`, an adapter is available, the same task has an accepted dry-run outcome, and the user enters the task-bound confirmation text `REAL-RUN <task id>`. When clicked, it calls `execute_task_with_lifecycle(..., dry_run=False)` once for the selected task, disables the control during the call, clears the dry-run gate afterward, and refreshes task state, results, artifact diagnostics, execution logs, preflight state, and latest outcome display. It does not scan tasks, start a scheduler, execute ready plans, or bypass lifecycle guards.

After a gated UI real-run call returns, the main window appends one `TaskExecutionLogRecord` with source `main_window`, outcome status, message, error code, result id when present, task type, runner type, and `dry_run=False`. Blocked preflight clicks do not create logs because no lifecycle execution occurs. UI logging does not change outcome semantics, create extra results, create artifacts, scan tasks, or start scheduler behavior.

The current UI gated real-run behavior has been audited and hardened. It is a real-run button, but only for one selected task id and only after the selected task exists, remains `pending`, has an available adapter, has already passed a same-task dry-run, and has task-bound confirmation text. The UI logs returned real-run outcomes and refreshes task state/results, artifact diagnostics, execution logs, preflight state, and the latest outcome display. Repeated clicks, completed-task reruns, failed-task retries, missing adapters, and export failures remain governed by the lifecycle guards and explicit retry task creation policy.

Real-run outcome refresh is hardened. Accepted real-run outcomes and rejected/preflight-blocked real-run attempts refresh the task result summary, artifact diagnostics, task plan summary, materialization readiness, execution contract readiness, execution logs, mock runner diagnostics, runner adapter diagnostics, preflight state, and latest outcome display. Refresh failures are reported as stable UI status text and do not trigger retries, additional task execution, extra result registration, or artifact creation.

Failed task retry policy has been audited. Failed tasks remain blocked by lifecycle guards and are not retried through `execute_task_with_lifecycle(...)`. The retry model is to create a new pending `TaskRecord` with copied execution context and explicit `retry_of_task_id` / `original_task_id` metadata, leaving the original failed task unchanged. Retry creation does not execute the task, create `TaskResultRecord`, create artifacts, start a scheduler, or add retry execution controls.

`create_retry_task(original_task_id)` implements the retry record foundation. It only accepts an original task in `failed` state, creates a new `pending` task with the original task type, project/source context, copied metadata, and retry lineage metadata, and leaves the original failed task unchanged. It does not execute the retry, append execution logs, create results, create artifacts, scan tasks, or connect to retry execution controls.

`summarize_retry_tasks()` reports retry task counts by state: total retry tasks, pending retry tasks, completed retry tasks, and failed retry tasks. The summary is visible in repo smoke/check output as read-only reporting. Smoke/check does not create retry tasks, execute retry tasks, append logs, create results, create artifacts, or mutate task state.

Retry task summaries are also visible in the UI task results summary as read-only counts. The UI now provides a narrow retry creation entry for the selected task id, but still does not provide retry execution, retry edit/delete, or scheduler controls.

Retry creation UI has been audited. The recommended first UI uses the selected task id as the failed original task id, requires task-bound confirmation, and calls `create_retry_task(original_task_id)` only for failed tasks. Missing, pending, running, and completed tasks should be rejected with stable messages. A successful retry creation should display the new retry task id and refresh task summary, retry summary, task results, and execution logs. The UI must not execute the retry, create results, create artifacts, mutate the original failed task, scan tasks, or add scheduler behavior.

The retry creation UI foundation follows that boundary. The selected task id is treated as the failed original task id, the user must enter `CREATE RETRY <task id>`, and successful creation returns a new pending retry `TaskRecord` with retry lineage metadata. Rejected attempts and successful creation refresh the existing summaries and preflight state. The retry task still requires a separate dry-run or explicit manual real-run path before execution; creation alone does not execute the retry, create results, create artifacts, append execution logs, mutate the original failed task, scan tasks, or start scheduler behavior.

Lifecycle runner wrapper diagnostics are surfaced through `scripts/run_smoke_tests.py`. Smoke/check uses dry-run calls only and reports dry-run checks, accepted outcomes, rejected outcomes, and state mutations. It does not call `dry_run=False`, does not create results or artifacts, and keeps task state unchanged.

`scripts/run_task_once.py` is the CLI/manual runner command. It defaults to `dry_run=True`, requires one explicit `--task-id`, accepts a `--state-dir`, constructs a local `RunnerAdapterRegistry`, and calls `execute_task_with_lifecycle(...)`. `--real-run` or `--no-dry-run` is required for `dry_run=False`. The command does not scan tasks, act as a scheduler, connect to UI execution, or use production downloaders.

Each CLI invocation appends one `TaskExecutionLogRecord` after the lifecycle outcome is returned. Dry-run, real-run, missing task, missing adapter, and validation failure outcomes are logged with outcome status, message, error code, result id when present, task type, runner type when available, and dry-run flag. Logging does not alter outcome semantics, task state rules, result registration, or artifact diagnostics.

Example usage:

```bash
python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --dry-run
python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --real-run
```

Results created by `ReportingSummaryRunnerAdapter` are ordinary task results. They can be read through `list_results()` and inspected by `inspect_result_artifacts()`. Existing artifact diagnostics report the exported summary path as `present` when the file exists and `missing` when the registered path is absent.

Profile reporting summary result visibility is surfaced through `scripts/run_smoke_tests.py`. The smoke/check summary filters `result_type=profile_reporting_summary` and reports total registered results plus present, missing, and not-applicable artifacts. This is read-only reporting and does not invoke the runner, create results, create artifacts, mutate task state, or block workflow.

Reporting runner dry-run diagnostics are surfaced through `scripts/run_smoke_tests.py`. The smoke/check summary reports supported task types, accepted dry-run outcomes, rejected outcomes, and not-implemented outcomes. This diagnostics path does not call `ReportingService`, does not execute real reporting, does not create results, and does not create artifacts.

## Artifact Diagnostics

Task result artifact diagnostics report whether a registered result artifact is `present`, `missing`, or `not_applicable`.

- `present`: `artifact_path` is set and the file exists
- `missing`: `artifact_path` is set but the file does not exist
- `not_applicable`: no `artifact_path` is registered for the result

Diagnostics are reporting-only. They do not execute tasks, download data, create or delete artifact files, or change task/result state.

Artifact diagnostics are also surfaced through `scripts/run_smoke_tests.py` as a compact summary and through the UI task results summary as read-only counts/status values. Missing artifacts are reported for developer visibility only and do not block ordinary workflow execution.

Artifact preview has been audited for a minimal future UI. The recommended first scope is a read-only preview for result artifacts selected by `result_id`, limited to text-oriented files (`.csv`, `.json`, `.txt`, `.md`). The preview should report file existence, type, size, and a bounded first chunk of text. It should not modify, delete, write, execute, or open artifacts in external programs, and should not attempt large-file, image, PDF, Excel, or complex spreadsheet rendering in the first phase.

`preview_result_artifact(result_id, max_chars=4000)` implements the read-only service foundation. It resolves a `TaskResultRecord` by result id, handles missing results, missing artifact paths, missing files, and unsupported extensions with stable preview records, and reads only a bounded text preview for `.csv`, `.json`, `.txt`, and `.md` files. It does not mutate results, modify artifact files, create logs, create results, create artifacts, execute tasks, or open external programs.

The UI now includes a minimal read-only artifact preview panel. Users can enter a result id and request a preview of the registered artifact. The panel displays the artifact path, existence/status, file type, size, and bounded preview text when supported. It does not modify artifacts, delete artifacts, open external programs, execute artifacts, create results, append logs, or trigger task execution.

`v0.30-artifact-preview-baseline` marks the artifact preview service and UI baseline. It includes `ArtifactPreviewRecord`, `preview_result_artifact(result_id, max_chars=4000)`, and the UI artifact preview panel. The first supported preview formats are `.csv`, `.json`, `.txt`, and `.md`; image, PDF, Excel, large-file full rendering, external opening, editing, deletion, and execution remain out of scope. The next planned capability is a read-only result detail viewer.

Result detail viewer design has been audited. The recommended first version is a read-only result-id lookup that displays `TaskResultRecord` fields such as result id, result type, state, title, task id/source task id, analysis id, analysis profile id, project id, artifact path, summary, metadata, and created timestamp. Artifact preview can remain adjacent or embedded as a bounded read-only sub-section. Editing, deleting, rerunning, retrying, and artifact modification remain out of scope.

`get_task_result_detail(result_id)` implements the read-only result detail service foundation. It returns `TaskResultDetailRecord` with result identity, task/source task context, analysis/profile/project metadata, artifact path and artifact status, summary, metadata, and created/updated timestamps. Current `TaskResultRecord` values do not have a separate `updated_at`, so detail records use `created_at` as the compatible `updated_at` value. Missing results return a stable detail record with `error_code="result_not_found"`. Result detail does not preview artifact contents, mutate results, create results, create artifacts, append logs, or execute tasks.

The UI now includes a read-only result detail viewer driven by the existing result id input. It displays result identity, type, state, title, task/source task ids, analysis/profile/project ids, artifact path, artifact status, and metadata summary. Artifact content remains in the separate artifact preview panel. The result detail viewer does not edit, delete, rerun, execute tasks, open artifacts, create results, create artifacts, or append logs.

`v0.31-result-detail-viewer` marks the result detail baseline. It includes `TaskResultDetailRecord`, `get_task_result_detail(result_id)`, and the UI result detail viewer. Result detail is metadata/status oriented; artifact content preview remains in the separate artifact preview panel. Result edit, result delete, result rerun, scheduler behavior, production downloads, and `geo_workflow.py` changes remain out of scope.

## v0.19 Baseline

The v0.19 baseline includes:

- task/result store
- profile reporting result registration
- artifact diagnostics service
- artifact diagnostics smoke/check summary
- UI task results summary
- UI artifact diagnostics read-only display
- TaskPlan foundation
- TaskPlan smoke/check summary
- TaskPlan UI read-only summary
- manual plan-to-task materialization
- materialization readiness diagnostics
- materialization readiness smoke/check summary
- materialization readiness UI read-only summary
- TaskExecutionRequest / TaskExecutionOutcome contract models
- execution contract readiness diagnostics
- execution contract readiness smoke/check summary
- execution contract readiness UI read-only summary
- mock/no-op runner foundation
- mock runner diagnostics smoke/check summary
- mock runner diagnostics UI read-only summary
- runner adapter protocol and registry
- `NoOpRunnerAdapter`
- runner adapter registry smoke/check diagnostics
- runner adapter registry UI read-only diagnostics
- real `profile_reporting_summary` runner adapter foundation
- dedicated `profile_reporting_summary` result counts in smoke/check
- manual runner execution wrapper and smoke/check diagnostics

`v0.14-ui-task-plan-materialization-readiness` marks manual plan materialization and materialization readiness diagnostics in smoke/check and UI. `v0.15-ui-execution-contract-readiness` marks task execution contract readiness diagnostics in smoke/check and UI. `v0.16-ui-mock-runner-diagnostics` marks mock/no-op runner diagnostics in smoke/check and UI.

`v0.19-runner-adapter-foundation` marks the runner adapter protocol, registry, no-op adapter, smoke/check adapter diagnostics, UI read-only adapter diagnostics, and the real reporting runner adapter design audit. `v0.19-first-real-reporting-runner` marks the first real `profile_reporting_summary` runner foundation. The current smoke/check path also reports dedicated profile reporting result counts and artifact readiness without invoking the runner, scheduler, production downloader, or UI execute control.

`v0.22-manual-runner-wrapper` marks the manual service-level runner wrapper. The wrapper can find an adapter through the registry and execute one explicitly requested task; it defaults to dry-run, remains state-neutral, and has smoke/check diagnostics for dry-run checks, accepted outcomes, rejected outcomes, and missing adapter outcomes.

`v0.23-lifecycle-runner-wrapper` marks the lifecycle-aware service-level wrapper. It keeps dry-run state-neutral, allows explicit non-dry-run `pending -> running -> completed` or `pending -> running -> failed` transitions for one selected task, surfaces lifecycle dry-run diagnostics in smoke/check, and documents UI manual execute button prerequisites. It still has no scheduler, no automatic task scan, no UI execute button, no production downloader, and no `geo_workflow.py` changes.

`v0.24-cli-manual-runner` marks `scripts/run_task_once.py`. The command defaults to dry-run, supports explicit `--real-run` / `--no-dry-run`, runs one selected task id through the lifecycle wrapper, and is covered by readiness/dev checks through command existence and `--help`. It still has no scheduler, no automatic task scan, no UI execute button, no production downloader, and no `geo_workflow.py` changes.

`v0.25-execution-log-baseline` marks `TaskExecutionLogRecord`, `task_execution_logs.json`, CLI outcome logging, smoke/check execution log summary, and UI read-only execution log summary. Execution log summaries are reporting-only. They do not execute tasks, scan tasks, create results, create artifacts, mutate task state, or provide a UI execute button.

`v0.27-ui-dry-run-execute` marks the UI selected-task dry-run execute baseline. The main window can accept one selected task id, call the lifecycle wrapper with `dry_run=True`, display the latest manual execute outcome, and refresh task/result/artifact/plan/log summaries. It still has no scheduler, no automatic task scan, no UI real-run button, no production downloader, and no `geo_workflow.py` changes. CLI `scripts/run_task_once.py --real-run` remains the controlled explicit real-run entry point.

`v0.28-ui-real-run-preflight` marks the real-run preflight baseline. The UI shows selected-task preflight state as read-only status, smoke/check reports real-run preflight diagnostics, and the real-run button decision audit keeps UI real-run unavailable for now. It still has no scheduler, no automatic task scan, no UI real-run button, no production downloader, and no `geo_workflow.py` changes. CLI `scripts/run_task_once.py --real-run` remains the controlled explicit real-run entry point.

`v0.28-ui-gated-real-run` marks the selected-task gated UI real-run baseline. UI dry-run execution, preflight/gating, and gated real-run outcome logging are present. Real-run remains selected-task-only, requires the selected task to exist and remain `pending`, requires an available adapter, requires accepted same-task dry-run, and requires explicit confirmation text. Returned outcomes are logged and summaries are refreshed. The baseline still has no scheduler, no automatic task scan, no production downloader, no Module 4/5/6 schema changes, and no `geo_workflow.py` changes.

`v0.29-real-run-hardening-retry-foundation` marks the real-run hardening and retry foundation baseline. UI gated real-run behavior has been audited, the real-run confirmation gate is hardened, real-run outcome refresh is hardened, failed retry policy is audited, retry task record creation is implemented, retry task summary is visible in smoke/check, and retry task summary is visible in the UI as read-only counts. The UI can also create a pending retry task from one selected failed task after `CREATE RETRY <task id>` confirmation. The original failed task remains unchanged, and the retry task is not executed by creation. The baseline still has no scheduler, no automatic task scan, no production downloader, no retry execute button, no retry edit/delete UI, no Module 4/5/6 schema changes, and no `geo_workflow.py` changes.

Analysis preflight summaries can be registered as `analysis_preflight_summary` task results. The registration metadata records dataset id, profile id, runnable status, blocking error count, warning count, and recommended action. This does not execute analysis, change task state, create an artifact, or modify `geo_workflow.py`.

The UI task results summary can display registered `analysis_preflight_summary` results as read-only preflight status. It shows dataset id, profile id, runnable status, blocking error count, warning count, recommended action, and result id. The UI does not generate preflight, execute analysis, create artifacts, or create logs.

## Validation

```bash
python3 scripts/run_smoke_tests.py
python3 -m unittest tests.test_task_plan_service
python3 -m unittest tests.test_task_management_service
python3 -m unittest tests.test_task_results_summary_widget
python3 -m unittest tests.test_main_window_reporting_summary
python3 -m unittest discover -s tests
```

If PySide6 is not installed, related UI tests skip by test design.
