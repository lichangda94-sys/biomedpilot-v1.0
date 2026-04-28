# Module 7 Real Runner Entrypoint Audit

This audit captures the minimum requirements and current baseline for moving from `TaskExecutionRequest` to the first real reporting runner. It is documentation only for the remaining runner roadmap; the current implementation includes the minimal `profile_reporting_summary` runner foundation.

The current runner adapter registry foundation adds lookup structure only. `RunnerAdapterRegistry` can register and find adapters by `task_type`; `NoOpRunnerAdapter` returns `not_implemented` outcomes without executing requests. Smoke/check reporting now exposes the registry summary without invoking adapters.

The `v0.19-runner-adapter-foundation` baseline covers the adapter protocol, registry, no-op adapter, smoke/check adapter diagnostics, UI read-only adapter diagnostics, and this real reporting runner adapter design audit. It still does not implement a real runner.

The post-v0.19 contract validation step added `validate_reporting_summary_runner_request()`. It validates the `profile_reporting_summary` adapter input contract before export or registration.

The first real runner foundation extends `ReportingSummaryRunnerAdapter`. It supports `profile_reporting_summary`, preserves dry-run accepted/skipped behavior, and calls `ReportingService.export_analysis_summary_csv(analysis_id)` only for validated `dry_run=False` requests with configured services.

Smoke/check reporting now includes reporting runner dry-run diagnostics. It summarizes supported task types, accepted dry-run outcomes, rejected outcomes, and not-implemented outcomes. This is readiness reporting only; it does not call `ReportingService` or create task results/artifacts.

`v0.20-reporting-runner-smoke-visibility` marks dedicated smoke/check visibility for `profile_reporting_summary` result counts and artifact readiness.

`v0.21-reporting-runner-visibility-baseline` marks the UI visibility audit. The existing read-only `TaskResultsSummaryWidget` and artifact diagnostics already expose `profile_reporting_summary` runner results, so this baseline does not add a dedicated runner-result UI count.

`v0.22-manual-runner-wrapper` marks the manual service-level runner wrapper and its smoke/check diagnostics. It does not add scheduler behavior, automatic task scanning, UI execution, task state mutation, production downloads, or `geo_workflow.py` changes.

`v0.23-lifecycle-runner-wrapper` marks the lifecycle-aware service-level wrapper, lifecycle dry-run smoke/check diagnostics, and this UI manual execute button prerequisite audit. It does not add scheduler behavior, automatic task scanning, UI execution, production downloads, or `geo_workflow.py` changes.

`v0.27-ui-dry-run-execute` marks the UI selected-task dry-run execute baseline. The UI can trigger a dry-run preflight for one selected task and display the latest outcome, while real-run remains unavailable in UI and controlled through CLI.

Real-run preflight diagnostics are now visible in smoke/check. They report eligible, blocked, and adapter-missing tasks without invoking dry-run execution, real-run execution, task result registration, artifact creation, execution logging, or task state mutation.

`v0.28-ui-real-run-preflight` marks the combined UI/smoke preflight baseline and the post-preflight UI real-run button decision audit. UI real-run remains unavailable; CLI real-run remains the controlled explicit path.

`v0.28-ui-gated-real-run` marks the selected-task gated UI real-run baseline. The main window can call the lifecycle wrapper with `dry_run=False` only after the selected task exists, remains `pending`, has an available adapter, has accepted same-task dry-run preflight, and has explicit task-bound confirmation text. Returned outcomes are logged through `TaskExecutionLogRecord` and summaries are refreshed. This still does not add scheduler behavior, automatic task scanning, production downloads, Module 4/5/6 schema changes, or `geo_workflow.py` changes.

`v0.29-real-run-hardening-retry-foundation` marks the real-run hardening and retry foundation baseline. It includes the UI gated real-run behavior audit, hardened real-run confirmation gate, hardened real-run outcome refresh, failed retry policy audit, retry task record foundation, retry summary in smoke/check, and UI read-only retry summary. It still does not add scheduler behavior, automatic task scanning, production downloads, retry execution controls, retry creation UI, Module 4/5/6 schema changes, or `geo_workflow.py` changes.

## Current Contract State

`TaskExecutionRequest` currently carries:

- `task_id`
- `task_type`
- `source_plan_id`
- `analysis_id`
- `analysis_profile_id`
- `project_id`
- `parameters`
- `requested_by`
- `dry_run`
- `created_at`

This is enough for a narrow first real runner if the runner consumes an existing analysis/reporting context. It is not yet enough for a general analysis creation runner unless required runtime inputs are standardized inside `parameters`.

## TaskRecord Execution Context

`TaskRecord` provides:

- `task_id`
- `task_type`
- `title`
- `state`
- `project_id`
- `source_id`
- `metadata`

Task plans materialized through `materialize_task_plan()` preserve source plan context in task metadata:

- `source_plan_id`
- `plan_type`
- `analysis_id`
- `analysis_profile_id`
- `project_id`
- `requested_by`
- `parameters`
- `notes`

This gives a future runner a stable bridge from plan metadata to execution request metadata without changing `TaskRecord` semantics.

## Module 5 Input Surface

Module 5 profile consumption currently supports:

- `AnalysisService.create_analysis_from_profile_config(config, outcome_record_ids)`
- `build_profile_analysis_input(config, outcome_record_ids)`
- `AnalysisService.run_analysis(analysis_id)`

`create_analysis_from_profile_config()` requires an `EngineReadyAnalysisConfig` and explicit `outcome_record_ids`. A generic `analysis.run` task therefore needs either:

- an existing `analysis_id`, for running an already created analysis, or
- `analysis_profile_id` plus `outcome_record_ids` in `parameters`, with a service path to export the engine config before creating the analysis.

Current `TaskExecutionRequest` can carry these values through `analysis_profile_id` and `parameters`, but the expected parameter schema is not yet formalized.

## Module 6 Input Surface

Module 6 reporting currently supports:

- `ReportingService.generate_analysis_summary_table(analysis_id)`
- `ReportingService.export_analysis_summary_csv(analysis_id)`
- `TaskManagementService.register_profile_reporting_result(...)`

Reporting summary generation requires an existing `analysis_id` with the analysis and result data already available. It can then export an analysis summary CSV and register a `TaskResultRecord` with profile source metadata.

## Recommended First Real Runner Type

Recommended first task type:

```text
profile_reporting_summary
```

Recommended first adapter name:

```text
reporting_summary_runner
```

Rationale:

- It can use an existing `analysis_id`.
- It avoids creating a new analysis.
- It avoids defining the full `analysis.run` parameter schema first.
- It has a clear output: a reporting summary artifact plus a registered task result.
- Existing tests already cover profile reporting result registration and reporting summary export behavior.

## Real Reporting Runner Adapter Design

The first real adapter is a narrow `profile_reporting_summary` adapter. It is not a general `analysis.run` adapter and does not create a new analysis. Its job is to consume an existing analysis context and produce a reporting summary result.

Recommended adapter identity:

- adapter class/name: `ReportingSummaryRunnerAdapter`
- adapter `runner_type`: `reporting_summary_runner`
- supported `task_type`: `profile_reporting_summary`

Required input fields:

- `task_id`: source task record id.
- `task_type`: must equal `profile_reporting_summary`.
- `analysis_id`: required; the reporting service needs an existing analysis.
- `dry_run`: supported. A dry-run request should validate contract and dependency readiness without exporting a file or registering a result.

Optional input fields:

- `source_plan_id`: copied to result metadata when present.
- `analysis_profile_id`: copied to result metadata when present or used for consistency checks if profile metadata is available.
- `project_id`: copied to result metadata when present or derived from the generated summary table when possible.
- `requested_by`: copied to result metadata for auditability.
- `parameters.format`: initially only `analysis_summary_csv`.
- `parameters.output_dir`: optional future path control. If omitted, the adapter should use the reporting service's existing export location rules.

Required output on success:

- `TaskExecutionOutcome.accepted`: `true`.
- `TaskExecutionOutcome.status`: `accepted`.
- `TaskExecutionOutcome.result_id`: id of the registered result.
- `TaskResultRecord.result_type`: `profile_reporting_summary`.
- `TaskResultRecord.state`: `available`.
- `TaskResultRecord.artifact_path`: path to the generated CSV summary.
- `TaskResultRecord.metadata.task_type`: `profile_reporting_summary`.
- `TaskResultRecord.metadata.analysis_id`: source analysis id.
- `TaskResultRecord.metadata.source_plan_id`: source plan id when present.
- `TaskResultRecord.metadata.analysis_profile_id`: profile id when present.
- `TaskResultRecord.metadata.project_id`: project id when present or derivable.

Artifact format:

- first supported format: CSV from `ReportingService.export_analysis_summary_csv(analysis_id)`.
- unsupported formats should be rejected before artifact creation.
- no production downloader or real-data fetch should be involved.

Module calls:

- Module 5 should not be called by the first adapter. It should not create or run an analysis.
- Module 6 may be called through `ReportingService.export_analysis_summary_csv(analysis_id)` once request validation succeeds and `dry_run` is false.
- `TaskManagementService.register_profile_reporting_result(...)` may register the resulting CSV artifact after export succeeds.

Rejection and validation failures:

- `missing_task_id`: request has no `task_id`.
- `unsupported_task_type`: request task type is not `profile_reporting_summary`.
- `missing_analysis_id`: request has no `analysis_id`.
- `unsupported_format`: `parameters.format` is not `analysis_summary_csv`.
- `dry_run`: request is valid but intentionally does not export or register a result.
- `reporting_export_failed`: reporting export raised or returned no artifact path.
- `result_registration_failed`: artifact export succeeded but result registration failed.

For rejected or failed contract validation outcomes, the adapter should not create `TaskResultRecord` and should not create an artifact after the failure is known.

Current validation-only helper:

- accepts `task_type=profile_reporting_summary`
- requires non-empty `task_id`
- requires non-empty `analysis_id`
- accepts omitted `parameters.format` as `analysis_summary_csv`
- accepts explicit `parameters.format=analysis_summary_csv`
- rejects unsupported formats before any export or registration path exists

Current dry-run adapter behavior:

- `dry_run=True`: validate the request and return accepted/skipped outcome.
- `dry_run=False`: validate the request, call `ReportingService.export_analysis_summary_csv(analysis_id)`, and register one `profile_reporting_summary` result after export succeeds.
- invalid request: return rejected outcome with the validation reason.
- smoke/check only uses dry-run requests.
- dry-run path makes no `ReportingService` call.
- dry-run path creates no `TaskResultRecord`.
- dry-run path creates no artifact.

## Input Contract

Minimum `profile_reporting_summary` request fields:

- `task_id`: required
- `task_type`: `profile_reporting_summary`
- `analysis_id`: required
- `project_id`: optional if derivable from the generated summary table
- `analysis_profile_id`: optional, used for consistency checks or metadata
- `source_plan_id`: optional
- `parameters`: optional, initially limited to stable reporting options such as `format`
- `dry_run`: should remain supported for validation-only behavior

Suggested first parameter shape:

```json
{
  "format": "analysis_summary_csv"
}
```

The runner should reject unsupported `format` values rather than guessing.

## Output Contract

Minimum successful output:

- `TaskExecutionOutcome.accepted`: `true`
- `TaskExecutionOutcome.status`: `accepted`
- `TaskExecutionOutcome.result_id`: populated with the registered result id
- `TaskResultRecord.result_type`: `profile_reporting_summary`
- `TaskResultRecord.state`: `available`
- `TaskResultRecord.artifact_path`: exported analysis summary CSV path
- `TaskResultRecord.metadata.analysis_id`: source analysis id
- `TaskResultRecord.metadata.project_id`: source project id
- `TaskResultRecord.metadata.analysis_profile_id`: profile id when available
- `TaskResultRecord.metadata.analysis_profile_name`: profile name when available

Minimum failed output:

- `TaskExecutionOutcome.accepted`: `false`
- `TaskExecutionOutcome.status`: `rejected`
- `TaskExecutionOutcome.error_code`: stable failure code
- `TaskExecutionOutcome.metadata.failure_result_policy`: `no_failed_result`
- no `TaskResultRecord`
- no artifact creation after validation failure

## Real Reporting Runner Implementation Baseline

Recommended next real runner:

- adapter class/name: `ReportingSummaryRunnerAdapter`
- `runner_type`: `reporting_summary_runner`
- `task_type`: `profile_reporting_summary`
- result type: `profile_reporting_summary`

The first real implementation keeps the existing dry-run behavior. Only `dry_run=False` enters the guarded real execution path, and only after `validate_reporting_summary_runner_request()` succeeds.

Reporting service usage:

- The real runner should call `ReportingService.export_analysis_summary_csv(analysis_id)` after validation.
- It should not call Module 5. The first runner consumes an existing analysis and does not create or run one.
- It should not call production downloaders or read real external datasets.
- It should reject unsupported `parameters.format` values before calling `ReportingService`.

Fields read from `TaskExecutionRequest`:

- `task_id`: required for result registration.
- `task_type`: must be `profile_reporting_summary`.
- `analysis_id`: required for `ReportingService`.
- `analysis_profile_id`: optional metadata for result registration.
- `project_id`: required for result registration.
- `source_plan_id`: optional metadata.
- `requested_by`: optional metadata.
- `parameters.format`: optional, defaults to `analysis_summary_csv`.

Task result registration:

- Register exactly one `TaskResultRecord` after export succeeds.
- `TaskResultRecord.result_type` should be `profile_reporting_summary`.
- `TaskResultRecord.state` should be `available`.
- `TaskResultRecord.artifact_path` should point to the exported CSV.
- `TaskResultRecord.metadata` should include `task_type`, `analysis_id`, and any present `source_plan_id`, `analysis_profile_id`, `project_id`, and `requested_by`.

Artifact requirements:

- The first artifact format should be CSV.
- `artifact_path` should be required for a successful outcome.
- Missing or empty export paths should return a failed/rejected outcome and should not register a result.
- The runner should not create extra sidecar files in this phase.

Task state policy:

- The first real runner implementation should not mutate `TaskRecord.state`.
- State transitions can be added later by an explicit orchestration layer or runner lifecycle task.
- This keeps the adapter callable in tests without implying scheduler behavior.

## Reporting Runner Task State Transition Audit

Current task states:

- `pending`
- `running`
- `completed`
- `failed`

Current service capabilities:

- `TaskManagementService.start_task()` transitions a task to `running`.
- `TaskManagementService.complete_task()` transitions a task to `completed` and can record a result.
- `TaskManagementService.fail_task()` transitions a task to `failed` and records a failed result.

Current runner behavior:

- `ReportingSummaryRunnerAdapter` does not call `start_task()`, `complete_task()`, or `fail_task()`.
- A successful non-dry-run adapter call registers a `profile_reporting_summary` result but leaves `TaskRecord.state` unchanged.
- A failed adapter call returns a rejected `TaskExecutionOutcome` and leaves `TaskRecord.state` unchanged.

Future minimal transition design:

- Success path: `pending -> running -> completed`.
- Failure path after execution starts: `pending -> running -> failed`.
- Contract validation failures and missing adapter failures should remain rejected outcomes before `running`.
- Export failures after a task enters `running` should become task failures if a lifecycle wrapper owns state transitions.

Recommended ownership:

- State transitions should be owned by a `TaskManagementService` wrapper, not by `ReportingSummaryRunnerAdapter`.
- The adapter should remain focused on validating/executing a single request and returning `TaskExecutionOutcome`.
- A future wrapper can build the request, select the adapter, call `start_task()`, execute the adapter, and then call `complete_task()` or `fail_task()` according to outcome.

Why not implement state transitions now:

- There is still no scheduler, background queue, or UI execute control.
- Direct adapter tests rely on state-neutral execution.
- Failure result policy is currently outcome-only; adding task failure records should be a separate lifecycle change.
- Keeping state unchanged avoids implying automatic task execution semantics.

Recommended next minimal implementation:

- Add a manual service-level execution wrapper that explicitly receives `task_id`, registry, and `dry_run`.
- Default the wrapper to `dry_run=True`.
- Keep task state unchanged in the first wrapper foundation.
- Add state transitions later only after wrapper semantics and failure result policy are stable.

## Manual Runner Execution Wrapper

`TaskManagementService.execute_task_with_adapter(task_id, adapter_registry, dry_run=True)` is the first manual wrapper foundation.

Behavior:

- reads one explicit `TaskRecord`
- builds a `TaskExecutionRequest`
- looks up an adapter from `RunnerAdapterRegistry` by `task_type`
- returns a rejected outcome with `error_code=missing_runner_adapter` when no adapter is registered
- calls the matching adapter only for the requested task
- preserves the adapter's existing dry-run and non-dry-run behavior

Boundaries:

- no scheduler
- no automatic task scanning
- no UI execute button
- no task state mutation
- no background queue
- no production downloader

For `dry_run=True`, the wrapper remains side-effect free when the adapter is side-effect free. For `dry_run=False`, result registration remains the adapter's responsibility; the current `ReportingSummaryRunnerAdapter` can register a `profile_reporting_summary` result after export succeeds. Lifecycle transitions remain out of scope for this wrapper foundation.

Manual runner wrapper diagnostics are visible in smoke/check output. They run dry-run wrapper checks only and summarize total dry-run checks, accepted outcomes, rejected outcomes, and missing-adapter outcomes. This diagnostics path does not call `dry_run=False`, does not create `TaskResultRecord`, does not create artifacts, and does not mutate task state.

## Task State Transition Implementation Prerequisites

This section is an implementation readiness audit only. It does not change runner behavior.

Minimum wrapper shape:

- add a separate lifecycle-aware wrapper instead of changing `ReportingSummaryRunnerAdapter` directly
- keep `execute_task_with_adapter(...)` state-neutral for compatibility
- require explicit `task_id`, adapter registry, and `dry_run` inputs
- default any new lifecycle wrapper to `dry_run=True` unless a caller explicitly requests real execution

Success prerequisites:

- the task must exist
- the adapter must exist for the task type
- request validation must pass before the task enters `running`
- `dry_run=False` must be explicit
- after adapter success, the wrapper may transition `running -> completed`

Failure prerequisites:

- missing task, invalid request, and missing adapter should return rejected outcomes before `running`
- failures after entering `running` may transition to `failed`
- failed task result registration should be decided together with lifecycle implementation
- failure paths must not create reporting artifacts after validation failure

Recommended minimum tests before implementation:

- valid dry-run wrapper call keeps task `pending`
- missing adapter keeps task `pending`
- valid non-dry-run success transitions `pending -> running -> completed`
- export failure after `running` transitions `running -> failed`
- contract validation failure does not transition to `running`
- no other queued or ready task is executed

Still out of scope for the transition implementation:

- scheduler
- background queue
- automatic task scanning
- UI execute button
- production downloader
- `geo_workflow.py` changes

## Lifecycle-Aware Manual Runner Wrapper

`TaskManagementService.execute_task_with_lifecycle(task_id, adapter_registry, dry_run=False)` adds explicit lifecycle management around one runner adapter call.

State policy:

- `dry_run=True`: delegate to `execute_task_with_adapter(..., dry_run=True)` and keep task state unchanged.
- missing task: return rejected outcome with `error_code=task_not_found`.
- non-pending task: return rejected outcome with `error_code=task_not_pending` and do not execute.
- missing adapter: return rejected outcome with `error_code=missing_runner_adapter` and keep task `pending`.
- real success: `pending -> running -> completed` when the adapter returns accepted outcome with `result_id`.
- real failure after entering `running`: `running -> failed`.
- adapter exception after entering `running`: catch the exception, return rejected outcome with `error_code=runner_adapter_exception`, and mark task `failed`.

Boundaries:

- no scheduler
- no automatic task scanning
- no UI execute button
- no production downloader
- no Module 5 execution
- no `geo_workflow.py` changes

The state-neutral `execute_task_with_adapter(...)` remains available for dry-run checks and compatibility. Lifecycle behavior is opt-in through the lifecycle wrapper.

Smoke/check lifecycle diagnostics call the wrapper in dry-run mode only. They report dry-run checks, accepted outcomes, rejected outcomes, and state mutations. The expected state mutation count is zero; diagnostics do not call `dry_run=False`, create results, create artifacts, or execute real reporting.

## Task State Lifecycle Hardening Audit

Current states:

- `pending`: the only state eligible for explicit lifecycle execution.
- `running`: an execution is already in progress or was left in progress; a second execution must be blocked.
- `completed`: the task already produced a completed outcome; repeated execution must be blocked by default.
- `failed`: the task already failed; retry requires a separate explicit retry policy and is blocked by default.

Allowed transitions:

- `pending -> running`: only for explicit `dry_run=False` lifecycle execution after request build and adapter lookup pass.
- `running -> completed`: only when the adapter returns an accepted outcome with a `result_id`.
- `running -> failed`: when the adapter rejects/fails after the task entered `running`, or when the adapter raises an exception.

Blocked transitions:

- `running -> running`: blocked to prevent duplicate execution.
- `completed -> running`: blocked to prevent accidental rerun and duplicate result registration.
- `failed -> running`: blocked until a dedicated retry policy exists.
- `pending -> completed` without `running`: blocked; lifecycle execution should always enter `running` before completion.
- any transition during `dry_run=True`: blocked; dry-run is state-neutral.

Retry policy recommendation:

- Do not retry failed tasks implicitly.
- Do not overload `execute_task_with_lifecycle(...)` with retry behavior in the next implementation.
- Add retry later as a separate explicit API, with a clear operator action, new execution log entry, and documented handling for previous failed outcomes.

## Failed Task Retry Policy Audit

Current behavior:

- Failed tasks are blocked by lifecycle guards.
- `execute_task_with_lifecycle(...)` does not retry failed tasks and should remain focused on executing one eligible `pending` task.
- UI real-run preflight also blocks failed tasks because they are not `pending`.

Retry model recommendation:

- Prefer creating a new `TaskRecord` as the retry task instead of reusing the failed task.
- The new retry task should start in `pending` state and copy the original `task_type`, execution-relevant metadata, `analysis_id`, `analysis_profile_id`, `project_id`, and parameters.
- The retry task should record `retry_of_task_id` and `original_task_id` in metadata so the lineage remains explicit.
- The original failed task should remain `failed`; retry creation must not mutate its state.

Retry logging and artifacts:

- Retry creation should be auditable, but the existing `TaskExecutionLogRecord` is execution-oriented. A first retry foundation may document retry creation in task metadata and avoid appending execution logs until an actual retry run occurs.
- Each retry execution should create its own execution log entry.
- Retry results and artifacts should be distinct from the failed task result/artifact path. A retry should not overwrite earlier artifact paths or assume failed attempts produced a usable artifact.

UI and CLI policy:

- UI retry should not be introduced until retry task creation is explicit and tested.
- CLI may remain the first controlled execution path for retry tasks after they are created.
- Any future UI retry action should require confirmation and should create a new retry task rather than rerun the failed task in place.

Next minimum implementation:

- Add `create_retry_task(original_task_id)` on `TaskManagementService`.
- Allow only original tasks in `failed` state.
- Copy execution-relevant context into a new pending retry task.
- Do not execute the retry task, create results, create artifacts, or add scheduler behavior.

Implemented retry record foundation:

- `TaskManagementService.create_retry_task(original_task_id)` creates a new pending retry task only from a failed original task.
- Retry metadata includes `retry_of_task_id`, `original_task_id`, and `original_task_state`.
- The original failed task remains failed.
- Retry creation does not execute the task, append execution logs, create results, create artifacts, scan tasks, or add retry execution controls.

## Retry Creation UI Design Audit

Current service capability:

- `TaskManagementService.create_retry_task(original_task_id)` can create a new retry `TaskRecord`.
- Only original tasks in `failed` state are eligible.
- The retry task starts in `pending` state.
- Retry task metadata includes `retry_of_task_id`, `original_task_id`, and `original_task_state`.
- The original failed task remains unchanged.
- Retry creation does not execute the retry task, create results, create artifacts, append execution logs, scan tasks, or start scheduler behavior.

Recommended UI behavior:

- use the existing selected task id as the original failed task id.
- require explicit confirmation before retry creation, such as `CREATE RETRY <task id>`.
- reject missing tasks with a stable message.
- reject `pending`, `running`, and `completed` tasks because retry creation is only valid for failed tasks.
- after retry creation, display the new retry task id and a stable message.
- refresh task summary, retry task summary, task result summary, and execution log summary so the new pending retry task is visible.
- show retry lineage, especially `retry_of_task_id`, in summaries or result/task detail surfaces where available.

Still out of scope:

- executing the retry task
- creating retry results or artifacts
- creating execution logs for retry creation
- adding scheduler or automatic task scanning
- adding retry edit/delete controls

Next minimal implementation:

- add a UI create retry action for the selected failed task id.
- add a confirmation input or reuse a task-bound confirmation pattern.
- call `create_retry_task(original_task_id)` only after the gate passes.
- refresh summaries after accepted and rejected attempts.
- test failed, missing, pending, running, and completed task behavior.

Missing adapter policy:

- Keep the task `pending`.
- Return a rejected outcome with `error_code=missing_runner_adapter`.
- Do not transition to `failed`, because no execution started and no adapter-owned side effect occurred.

Dry-run policy:

- `dry_run=True` should never mutate task state, create results, create artifacts, or append execution logs through smoke/check diagnostics.
- Dry-run may return accepted or rejected outcomes for visibility, but it remains a preflight path only.

Next implementation checklist:

- Explicit tests cover `running`, `completed`, and `failed` tasks being rejected by lifecycle execution.
- `pending` success and failure tests remain in place for `completed` and `failed` transitions.
- Missing-adapter behavior remains state-neutral.
- Adapter exception behavior remains `running -> failed`.
- Dry-run preserves state and returns a clear rejected outcome for non-pending tasks.
- Preserve no scheduler, no automatic scanning, no UI execute button, no production downloader, and no `geo_workflow.py` changes.

Outcome policy:

- successful export and result registration: `accepted=True`, `status=accepted`, `result_id=<registered result id>`.
- invalid contract: `accepted=False`, `status=rejected`, stable validation `error_code`, no result registration.
- unsupported format: `accepted=False`, `status=rejected`, `error_code=unsupported_format`.
- reporting export failure: `accepted=False`, `status=rejected`, `error_code=reporting_export_failed`, no result registration.
- result registration failure: `accepted=False`, `status=rejected`, `error_code=result_registration_failed`.

Failure result policy:

- The first real reporting runner does not register failed `TaskResultRecord` entries for adapter failures.
- This keeps the failure path narrow while task lifecycle ownership stays in `TaskManagementService`.
- Failed result registration can be reconsidered with a dedicated failed-result policy, but this baseline keeps adapter failures in `TaskExecutionOutcome` only.

Implemented foundation:

- constructor injection for `ReportingService` and `TaskManagementService` dependencies.
- dependency-free construction remains valid for dry-run tests.
- validation runs before any service call.
- `dry_run=True` behavior remains accepted/skipped and side-effect free.
- `dry_run=False` calls reporting export, then registers the result.
- fake-service tests cover success, export failure, missing project id, and task state preservation.
- generated results are visible through `list_results()` and participate in existing artifact diagnostics.

## Still Out Of Scope

- no scheduler
- no background queue
- no automatic adapter execution
- no automatic ready-plan scanning
- no smoke/check adapter execution
- no production TCGA/GDC/GTEx downloader
- no UI execute button
- no `geo_workflow.py` changes
- no task state mutation by the first real adapter
- no broad `analysis.run` implementation
- no new Module 4/5/6/7 schema changes
- no real data dependency

## Real Reporting Runner Visibility Audit

Current visibility:

- `ReportingSummaryRunnerAdapter` registers successful `dry_run=False` output as a normal `TaskResultRecord`.
- The generated result uses `result_type=profile_reporting_summary`.
- Result metadata includes analysis/profile/project context plus `source_task_id` and `runner_type`.
- Existing `TaskManagementService.list_results()` can read the generated result.
- Existing artifact diagnostics can report the runner artifact as `present` or `missing`.
- Existing UI task result summary can display the result row, result type, artifact path, and artifact status through the generic task result table.
- Existing `TaskResultsSummaryWidget` columns already expose the relevant runner output surface: result id, type, state, title, analysis id, profile, artifact path, and artifact status.
- Existing `MainWindow.refresh_task_results_summary()` loads task results and artifact diagnostics into that read-only widget without calling runner execution.

Gaps:

- UI does not currently show a dedicated count of real reporting runner results.
- Smoke/check now shows a dedicated reporting-only count of `profile_reporting_summary` results and their artifact readiness.
- The existing generic result summary is enough for basic UI visibility, but it does not distinguish runner-created profile reporting summaries from manually registered profile reporting summaries.

UI visibility assessment:

- A successful real reporting runner result is visible in the UI as a normal `profile_reporting_summary` result row.
- Artifact readiness for that result is visible through the existing artifact status column and aggregate artifact count.
- The UI remains read-only: no execute, rerun, materialize, edit, or delete controls are required for this baseline.
- A dedicated UI count for `profile_reporting_summary` results would duplicate the smoke/check summary unless users need a separate dashboard-level signal later.

Implemented smoke/check visibility:

- `TaskManagementService.summarize_profile_reporting_results()` reuses existing artifact diagnostics filtered to `result_type="profile_reporting_summary"`.
- `scripts/run_smoke_tests.py` reports total profile reporting summary results plus present, missing, and not-applicable artifacts.
- This is reporting-only: no scheduler, no UI execute button, no runner invocation, and no new result creation.

Not recommended now:

- Do not add a separate UI runner-result summary until the smoke/check result summary proves useful.
- Do not add UI execute controls.
- Do not add scheduler or background queue behavior.
- Do not create a new result schema only for runner-created outputs; current `TaskResultRecord` metadata is sufficient.

## UI Manual Execute Button Prerequisites Audit

Current service readiness after lifecycle hardening:

- `TaskManagementService.execute_task_with_lifecycle(task_id, adapter_registry, dry_run=False)` is the minimum service method a future UI button would need.
- The lifecycle wrapper can build a request, find an adapter, call one adapter for one explicit pending task, and move it through `running` to `completed` or `failed`.
- Lifecycle guards are sufficient for the first UI foundation: `pending` is the only executable state, while `running`, `completed`, and `failed` are rejected before execution.
- `dry_run=True` remains state-neutral and can be used for UI preflight checks. For non-pending tasks it returns a clear rejected outcome without mutation.
- Missing adapter returns a rejected outcome and keeps the task `pending`.
- Non-pending tasks are rejected without execution and without result/artifact creation.
- Execution logs are sufficient for the first UI foundation because CLI execution already records dry-run, real-run, missing task, missing adapter, validation failure, outcome status, error code, and result id when present.
- `scripts/run_task_once.py` remains a CLI/manual fallback for one selected task id and is useful for validating task state and runner behavior before UI work.

Required UI inputs:

- a selected `TaskRecord`
- visible task state, task type, title, analysis id, project id, and profile id
- an adapter registry containing a runner for the selected task type
- clear distinction between dry-run preflight and real execution

Mis-execution controls required before any button implementation:

- only enable real execution for one selected `pending` task
- hide or disable real execution controls for `running`, `completed`, and `failed` tasks
- require explicit confirmation before `dry_run=False`
- default the UI action to dry-run/preflight, not real-run
- keep real-run behind an explicit advanced option or confirmation path
- show that the action is manual and not scheduler-driven
- show expected state transition before execution
- refresh task state, task results, artifact diagnostics, and execution log summaries after outcome
- display rejected outcomes and error codes without retry loops

Display requirements:

- pending tasks may show an available manual action in a future UI, but not in this baseline
- running/completed/failed states should be refreshed from `TaskManagementService`
- completed reporting runner tasks should show their registered `profile_reporting_summary` result through the existing result table
- failed execution should show the `TaskExecutionOutcome` message/error and task `failed` state, without assuming a failed `TaskResultRecord`
- execution logs should show the latest manual execution outcome after refresh

Readiness assessment:

- Lifecycle guards are now sufficient to prevent duplicate execution of running/completed/failed tasks.
- Execution logs are sufficient to preserve a lightweight audit trail for UI-triggered outcomes.
- CLI manual runner remains a safe fallback and operator reference.
- The recommended next implementation is a UI manual execute button foundation limited to one selected pending `profile_reporting_summary` task, with dry-run as the default path and explicit confirmation for real-run.
- Retry remains out of scope; failed tasks should stay blocked until a separate retry policy exists.

Recommendation:

- The lifecycle wrapper, lifecycle guards, execution logs, and CLI fallback are sufficient prerequisites for a first UI manual execute button foundation.
- Implementing that foundation is reasonable next, provided it stays selected-task-only, defaults to dry-run, requires confirmation for real-run, refreshes summaries after outcome, and does not introduce scheduler behavior.

## UI Manual Dry-Run Execute Foundation

Implemented surface:

- the main window provides one selected task id input.
- the main window provides a dry-run task button only.
- the button calls `TaskManagementService.execute_task_with_lifecycle(task_id, registry, dry_run=True)`.
- the runner registry includes the `profile_reporting_summary` adapter, but the UI path remains dry-run only.
- after the dry-run outcome, the UI refreshes task result summary, artifact diagnostics, task plan summary, execution contract readiness, execution logs summary, mock runner diagnostics, and runner adapter diagnostics.

Current UI behavior:

- no selected task id: no execution call is made and a stable status message is displayed.
- accepted dry-run outcome: the UI reports accepted/skipped status and refreshes summaries.
- rejected or blocked outcome: the UI reports rejected status and error code, including lifecycle guard rejections such as `task_not_pending`.
- dry-run does not mutate task state and does not create results or artifacts.

Still not implemented:

- no UI real-run button.
- no UI scheduler or automatic task scanning.
- no automatic ready-plan execution.
- no retry controls for failed tasks.
- no production downloader or `geo_workflow.py` change.

Still prohibited:

- no scheduler
- no automatic task scanning
- no background queue
- no production downloader
- no `geo_workflow.py` changes
- no UI execute button in this audit task
- no execution without explicit user-selected task

## UI Real-Run Preflight Design

Current UI state:

- the main window accepts one selected task id.
- the main window exposes only dry-run execution.
- the latest dry-run outcome is displayed with status, message, error code, result id, and dry-run flag.
- the main window displays selected-task real-run preflight state without executing anything.
- lifecycle guards already block `running`, `completed`, and `failed` tasks.
- execution logs, result summary, artifact diagnostics, and task state summaries can be refreshed after a manual outcome.

Real-run exposure requirements:

- real-run must require explicit opt-in; it should not replace the current dry-run default.
- the UI should require a successful dry-run preflight for the same selected task before enabling real-run.
- the selected task must still be `pending` at real-run time.
- real-run must show a confirmation step that names the task id, task type, analysis id, profile id, and expected runner.
- the real-run control should be disabled while an execution call is in progress to prevent repeated clicks.
- the execution path must call the lifecycle wrapper for one selected task only and must not scan for additional tasks.

Refresh requirements after real-run:

- refresh task state so `running`, `completed`, and `failed` are visible.
- refresh task result summary so a successful `profile_reporting_summary` result appears.
- refresh artifact diagnostics so the exported CSV is reported as present or missing.
- refresh execution log summary so the real-run outcome is visible.
- refresh the latest outcome display with status, message, error code, result id, and dry-run flag.

Failure display requirements:

- validation or lifecycle guard failures should show the rejected outcome and error code.
- adapter/export failures should show a failed or rejected outcome and preserve the failed task state handled by the lifecycle wrapper.
- failed tasks should remain blocked until a separate retry policy exists.
- a failed real-run should not assume a successful `TaskResultRecord` exists.

Recommendation:

- Do not add UI real-run in the immediate next step.
- Keep CLI `scripts/run_task_once.py --real-run` as the controlled real-run entry point until UI confirmation, button disablement, and same-task dry-run preflight state are implemented.
- The next UI-safe task should connect this preflight state to smoke/check diagnostics and then re-audit whether a real-run button is warranted.

## UI Real-Run Button Decision After Preflight

Implemented decision:

- The UI real-run button foundation is implemented with strict gating.
- Real-run remains selected-task-only and does not introduce scheduler behavior.
- CLI `scripts/run_task_once.py --real-run` remains the operator-oriented real-run path.

Readiness assessment:

- preflight state is now sufficient to identify task existence, current state, pending eligibility, adapter availability, dry-run recommendation, and whether UI real-run is available.
- smoke/check preflight diagnostics are sufficient to report eligible, blocked, and adapter-missing tasks without execution.
- lifecycle guards are sufficient to block `running`, `completed`, and `failed` tasks.
- execution logs are sufficient to record CLI real-run outcomes and gated UI real-run outcomes after lifecycle execution returns.

Required policy for the UI real-run button:

- a successful dry-run for the same selected task is required before real-run.
- the selected task must still exist and remain `pending` at the moment of real-run.
- an adapter must be available for the selected task type.
- explicit task-bound confirmation text is required before the real-run button is enabled.
- the real-run control is disabled while execution is in progress to prevent duplicate clicks.
- failed tasks remain blocked until a separate retry policy is implemented.

Refresh requirements after any future UI real-run:

- task state summary and selected task preflight state.
- task result table and profile reporting result counts.
- artifact diagnostics.
- execution log summary.
- latest manual execute outcome display.

Implemented UI real-run foundation scope:

- one selected `pending` `profile_reporting_summary` task only.
- requires prior same-task dry-run acceptance.
- requires explicit confirmation.
- calls `execute_task_with_lifecycle(..., dry_run=False)` exactly once.
- appends one `TaskExecutionLogRecord` for the returned UI real-run outcome.
- refresh all task/result/artifact/log/preflight summaries after outcome.
- no scheduler, no automatic task scan, no production downloader, and no `geo_workflow.py` change.

## UI Gated Real-Run Behavior Audit

Current trigger conditions:

- The UI real-run path is selected-task-only. It reads the task id from the main window task id input and never scans all tasks.
- The selected task must exist and must still be `pending`.
- A runner adapter must be available for the selected task type.
- The same selected task must have an accepted dry-run outcome before the real-run button is enabled.
- The user must enter the explicit task-bound confirmation text `REAL-RUN <task id>` before the button is enabled.
- The real-run button is disabled while the explicit call is in progress.

Current execution behavior:

- The UI real-run path is a real-run button, but it is gated by preflight state, same-task dry-run success, task state, adapter availability, and confirmation.
- A gated click calls `execute_task_with_lifecycle(..., dry_run=False)` once for the selected task.
- The lifecycle wrapper owns task state transitions and blocks non-`pending` tasks.
- After the lifecycle outcome returns, the UI appends one execution log with source `main_window`, task type, runner type, outcome status, message, error code, result id when present, and `dry_run=False`.
- The UI refreshes task state/results, artifact diagnostics, execution logs, preflight state, and the latest outcome display after the call.

Risk review:

- Repeated click risk is reduced by disabling the control during execution and clearing the same-task dry-run gate afterward.
- Completed task rerun is blocked by lifecycle state guards and preflight state.
- Failed task retry remains blocked until a separate retry policy exists.
- Missing adapter blocks before execution and does not mutate task state.
- Export failure is reported through the lifecycle outcome and execution log; the lifecycle wrapper marks the task failed after execution has started.

Next recommendation:

- Tag the current gated real-run baseline.
- Then harden confirmation behavior and rejected-path refresh if further UI real-run safeguards are needed.
- Keep retry policy as a separate design and implementation track.

## v0.29 Real-Run Hardening And Retry Foundation

Current baseline:

- UI gated real-run behavior has been audited.
- The real-run confirmation gate requires a selected task, pending state, adapter availability, preflight eligibility, same-task dry-run success, and task-bound confirmation.
- Real-run outcome refresh covers task results, artifact diagnostics, task plan summaries, materialization readiness, execution contract readiness, execution logs, preflight state, and latest outcome display.
- Failed task retry policy recommends creating a new pending retry task instead of rerunning the failed task in place.
- `create_retry_task(original_task_id)` creates retry task records from failed originals only.
- Retry task summaries are visible in smoke/check and in the UI as read-only reporting.
- The UI can create a pending retry task from one selected failed task after task-bound `CREATE RETRY <task id>` confirmation.
- The original failed task remains unchanged, and retry creation does not execute the retry, create results, create artifacts, append execution logs, scan tasks, or start scheduler behavior.

Still out of scope:

- no scheduler
- no automatic task scan
- no production downloader
- no retry execute button
- no retry execution UI
- no Module 4/5/6 schema changes
- no `geo_workflow.py` changes

Next recommended work:

- task plan materialize UI audit
- scheduler audit later
- retry creation UI audit
- scheduler audit later

## Task Plan Materialize UI Design Audit

Current materialization capability:

- `TaskManagementService.materialize_task_plan(plan_id)` converts one task plan into one task record.
- Only a `ready` plan can be materialized.
- The materialized task starts in `pending` state.
- The materialized task preserves source plan context in metadata, including `source_plan_id`, `analysis_id`, `analysis_profile_id`, `project_id`, `requested_by`, `parameters`, and notes when present.
- The source `TaskPlanRecord` state remains unchanged; a `ready` plan stays `ready` after materialization.
- Materialization does not execute the new task, create results, create artifacts, scan plans, or start scheduler behavior.

Recommended first UI:

- Use a selected plan id input or the nearest existing plan selection surface.
- Require explicit task-bound confirmation, for example `MATERIALIZE PLAN <plan id>`.
- Call `materialize_task_plan(plan_id)` only after the selected plan exists and is `ready`.
- Display the new materialized task id and a stable success message.
- Refresh task summary, task plan summary, and materialization readiness after success or rejection.

Blocked plans:

- `draft` plans should be rejected as not ready.
- `disabled` plans should be rejected as intentionally inactive.
- `archived` plans should be rejected as historical records.
- missing plan ids should return a stable missing-plan message.

Still out of scope:

- executing the materialized task
- creating `TaskResultRecord`
- creating artifacts
- automatically scanning or materializing ready plans
- adding scheduler behavior
- changing the source task plan state
- changing Module 4/5/6 schemas
- changing `geo_workflow.py`

Next minimal implementation:

- Add a selected-plan-id input or reuse the most local UI input pattern.
- Add a confirmation input and a materialize action.
- Add tests for ready plan success, non-ready rejection, missing-plan rejection, no task execution, no result/artifact creation, and summary refresh.

Implemented task plan materialize UI baseline:

- the main window accepts one selected plan id.
- the user must enter `MATERIALIZE PLAN <plan id>`.
- a `ready` plan can be materialized into one pending task.
- `draft`, `disabled`, `archived`, and missing plans are rejected with stable UI messages.
- the source `TaskPlanRecord.state` remains unchanged.
- summary refresh covers task counts, task plan counts, and materialization readiness.
- materialization does not execute the task, append execution logs, create results, create artifacts, scan plans, or add scheduler behavior.

Next consideration:

- materialized tasks should continue through the existing dry-run or explicit manual real-run path.
- scheduler audit remains separate and later.

## Artifact Preview Minimal UI Design Audit

Current artifact model:

- `TaskResultRecord.artifact_path` stores the path to a generated or registered artifact.
- `ReportingSummaryRunnerAdapter` stores the exported analysis summary CSV path as the successful `profile_reporting_summary` result artifact.
- Existing artifact diagnostics classify registered result artifacts as `present`, `missing`, or `not_applicable`.

Recommended first preview scope:

- support text-oriented artifacts only: `.csv`, `.json`, `.txt`, and `.md`.
- select the artifact through a `result_id` first; the service can resolve the corresponding `TaskResultRecord.artifact_path`.
- show file existence, artifact path, file type/extension, file size, and the first bounded chunk of text.
- use a conservative preview limit such as first N characters or first N lines to avoid rendering large files in full.

Explicitly out of scope for the first preview:

- large file full rendering
- image preview
- PDF preview
- Excel or complex spreadsheet preview
- opening external programs
- editing, deleting, writing, or executing artifacts

Recommended safety boundary:

- preview must be read-only.
- preview must not mutate `TaskResultRecord`.
- preview must not modify artifact contents.
- preview must not create result records, logs, or artifacts.
- missing or unsupported artifacts should return stable messages instead of raising UI-level exceptions.

Recommended next minimal implementation:

- add a service/helper such as `preview_result_artifact(result_id, max_chars=4000)`.
- return a small structured preview record with path, existence, extension, size, preview availability, preview text, message, and error code.
- add tests for existing CSV/JSON artifacts, missing artifact, no artifact path, unsupported extension, max-char truncation, and no file mutation.

Implemented service foundation:

- `ArtifactPreviewRecord` captures artifact path, existence, file name, extension, size, preview availability, preview text, message, and error code.
- `TaskManagementService.preview_result_artifact(result_id, max_chars=4000)` resolves the task result and returns stable records for missing result, no artifact path, missing artifact, unsupported extension, read failure, or available preview.
- Supported first-phase preview extensions are `.csv`, `.json`, `.txt`, and `.md`.
- The helper reads only the first bounded character chunk, does not modify result records or artifact files, does not create logs/results/artifacts, does not execute tasks, and does not open external programs.

Implemented UI foundation:

- the main window has a result id input and preview action.
- `TaskResultsSummaryWidget` displays artifact path, preview status, existence, file type, size, message, and bounded preview text.
- the UI preview path calls only `preview_result_artifact(...)`.
- it does not execute tasks, append logs, create results, create artifacts, modify files, delete files, open external programs, or provide rich binary preview.

Baseline:

- `v0.30-artifact-preview-baseline` marks the read-only artifact preview service and UI foundation.
- Supported formats are `.csv`, `.json`, `.txt`, and `.md`.
- The next implementation target is the result detail viewer.

## Result Detail Viewer Design Audit

Recommended first detail fields:

- `result_id`
- `result_type`
- `state`
- `title`
- `task_id`
- `metadata.source_task_id`
- `metadata.analysis_id`
- `metadata.analysis_profile_id`
- `metadata.project_id`
- `artifact_path`
- `summary`
- `metadata`
- `created_at`

Lookup modes:

- by `result_id` should be the first implementation because it maps directly to one `TaskResultRecord`.
- by `task_id` can be added later as a filtered list or result selector when a task has multiple results.

Relationship to artifact preview:

- result detail and artifact preview should stay related but not fully merged.
- result detail should show record metadata and artifact path.
- artifact preview should render only the bounded artifact content for supported text files.
- a result detail panel can include a preview action for the selected result, but metadata display should remain useful even when preview is missing or unsupported.

Recommended first UI shape:

- reuse the existing selected result id field if possible.
- show a read-only detail block or panel with scalar result fields and formatted metadata.
- keep artifact preview as a sub-section or adjacent read-only panel.
- no edit, delete, rerun, retry, or artifact modification controls.

Out of scope:

- editing result metadata
- deleting result records
- rerunning or retrying from the result detail view
- opening artifacts in external programs
- complex binary artifact rendering

Recommended next minimal implementation:

- add a service/helper such as `load_task_result_detail(result_id)` only if the UI needs a stable DTO; otherwise the existing `list_results()` records are sufficient for a first read-only panel.
- add widget tests for result detail display by `result_id`, missing result handling, metadata display, and no artifact/task execution side effects.

Implemented service foundation:

- `TaskResultDetailRecord` provides a stable read-only DTO for result details.
- `TaskManagementService.get_task_result_detail(result_id)` returns detail fields from the matching `TaskResultRecord`, includes artifact status from existing diagnostics, and returns a stable `result_not_found` detail when the id is missing.
- Because `TaskResultRecord` has no separate `updated_at`, result detail uses `created_at` as the compatible `updated_at` value.
- Detail lookup does not preview artifact content, create logs, create results, create artifacts, mutate records, execute tasks, or open files.

Implemented UI foundation:

- the UI result detail viewer uses the existing result id input.
- it shows result identity, type, state, title, task/source task ids, analysis/profile/project ids, artifact path, artifact status, and metadata summary.
- artifact content remains in the artifact preview panel.
- `v0.31-result-detail-viewer` marks this baseline.
- result edit, delete, rerun, scheduler behavior, production downloads, and `geo_workflow.py` changes remain out of scope.

## CLI Manual Runner Command Design Audit

Implemented command:

```bash
python3 scripts/run_task_once.py --task-id <task-id> --state-dir <path> --dry-run
python3 scripts/run_task_once.py --task-id <task-id> --state-dir <path> --real-run
```

Script name:

- `scripts/run_task_once.py`

Recommended inputs:

- `--task-id`: required. The command must operate on exactly one explicit task id.
- `--state-dir`: required or defaulted to `state`; it should point to the local state directory used by `TaskManagementService.from_state_dir(...)`.
- `--dry-run`: explicit dry-run flag.
- `--real-run` or `--no-dry-run`: explicit opt-in for `dry_run=False`.

Default behavior:

- default to `dry_run=True`.
- reject missing `--task-id` with non-zero exit code.
- reject unknown task id with a stable rejected outcome summary.
- never scan all tasks.

Service loading:

- construct `TaskManagementService.from_state_dir(Path(state_dir))`.
- construct a local `RunnerAdapterRegistry`.
- register `ReportingSummaryRunnerAdapter` for `profile_reporting_summary`.
- for dry-run, the adapter can be dependency-free because it must not call `ReportingService`.
- for real-run, the command must provide configured `ReportingService` and `TaskManagementService` dependencies before calling the lifecycle wrapper.

Execution call:

```python
outcome = task_service.execute_task_with_lifecycle(
    task_id,
    registry,
    dry_run=dry_run,
)
```

Recommended output fields:

- `task_id`
- `dry_run`
- `outcome status`
- `accepted`
- `message`
- `result_id`
- `error_code`

Text output is acceptable for the first command if it is stable and line-oriented. JSON can be added later if machine consumption becomes necessary.

Current output is stable line-oriented text:

```text
Task runner outcome:
- task_id: <task-id>
- dry_run: true|false
- accepted: true|false
- status: accepted|rejected|skipped|failed_contract_validation
- message: <message>
- result_id: <result-id-or-empty>
- error_code: <error-code-or-empty>
```

Real-run constraints:

- only uses existing `profile_reporting_summary` runner behavior.
- requires a pending task with valid `analysis_id`, `project_id`, and supported format.
- may create a `profile_reporting_summary` result only through `ReportingSummaryRunnerAdapter`.
- may mutate only the selected task through lifecycle transitions.
- must not execute any other task.

Still prohibited:

- no scheduler
- no automatic task scan
- no background queue
- no UI execute button
- no production downloader
- no `geo_workflow.py` changes
- no Module 5 execution
- no real-data dependency

Implementation status:

- `scripts/run_task_once.py` is implemented as the first manual command surface for the lifecycle wrapper.
- CLI default is dry-run so local operators can verify request/adapter wiring before an explicit real-run.
- readiness checks cover command existence and `--help`, but do not run a task.

## Next Development Recommendation

The CLI/manual runner command baseline is implemented and documented. A UI manual execute button foundation can be considered later only if it keeps explicit selected-task gating, confirmation, dry-run preflight, and no scheduler behavior.

Only after that should `analysis.run` be considered. `analysis.run` needs a clearer parameter contract for `outcome_record_ids`, profile config export, and existing-vs-new analysis behavior.
