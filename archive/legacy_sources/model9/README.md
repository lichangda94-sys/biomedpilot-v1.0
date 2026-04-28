# model9

Desktop application skeleton for macOS and Windows based on Python and PySide6.

## v0.17 Local Readiness Baseline

The current baseline connects the profile-to-reporting path end to end:

`AnalysisProfile` -> `EngineReadyAnalysisConfig` -> Module 5 profile consumption -> Module 6 reporting summary -> Module 7 task/result registration -> artifact diagnostics -> task plan summary -> materialization readiness -> execution contract readiness -> UI read-only display.

Current capabilities:

- Module 4A surfaces extraction rule bundle diagnostics through smoke/check reporting.
- Module 4B defines analysis profiles, gene panels, comparison rules, keyword rule sets, threshold profiles, and engine-ready config export.
- Module 5 can create analysis inputs from exported profile configs.
- Module 6 reporting summaries include analysis profile source metadata.
- The UI can display a reporting summary and load it by selected analysis id.
- Module 7 records local task lifecycle state, task result metadata, profile reporting result registration, and artifact diagnostics.
- Smoke/check reporting includes task result artifact diagnostics.
- The UI can display task results and artifact diagnostics as read-only summaries.
- The UI task results summary uses grouped read-only sections and wrapped diagnostic text.
- Module 7 records `TaskPlanRecord` metadata with `draft`, `ready`, `disabled`, and `archived` states.
- Smoke/check reporting includes task plan state counts.
- The UI can display task plan state counts as a read-only summary.
- Module 7 can manually materialize a `ready` task plan into a pending `TaskRecord`.
- Module 7 reports task plan materialization readiness diagnostics.
- Smoke/check reporting includes task plan materialization readiness counts.
- The UI can display task plan materialization readiness as a read-only summary.
- Module 7 defines `TaskExecutionRequest` and `TaskExecutionOutcome` as a future executor contract.
- Module 7 reports task execution contract readiness diagnostics.
- Smoke/check reporting includes task execution contract readiness counts.
- The UI can display task execution contract readiness as a read-only summary.
- Module 7 provides a mock/no-op runner for contract-level dry-run checks.
- Smoke/check reporting includes mock runner diagnostics counts.
- The UI can display mock runner diagnostics as a read-only summary.
- Module 7 defines a runner adapter protocol and registry for future task-type lookup.
- Module 7 provides a `NoOpRunnerAdapter` that returns not-implemented outcomes without execution.
- Smoke/check reporting includes runner adapter registry diagnostics.
- The UI can display runner adapter registry diagnostics as a read-only summary.
- Module 7 includes the first minimal real reporting runner foundation for `profile_reporting_summary`.
- Module 7 provides a lifecycle-aware manual runner wrapper for explicit pending task execution.
- Module 7 provides `scripts/run_task_once.py` for explicit one-task CLI/manual runner execution.
- Module 7 records manual runner outcomes in `TaskExecutionLogRecord` entries stored in `task_execution_logs.json`.
- Smoke/check reporting includes execution log summary counts.
- The UI can display execution log summary counts as a read-only summary.
- `dry_run=True` keeps the reporting runner side-effect free and does not call `ReportingService`.
- `dry_run=False` calls `ReportingService.export_analysis_summary_csv(analysis_id)` and registers one `profile_reporting_summary` task result after export succeeds.
- Reporting runner results participate in existing artifact diagnostics.

Artifact diagnostics status:

- `present`: `artifact_path` is set and the file exists.
- `missing`: `artifact_path` is set but the file is missing.
- `not_applicable`: the result has no `artifact_path`.

Task plan states:

- `draft`: the plan is being prepared.
- `ready`: the plan is ready for future scheduler consumption, but is not executed.
- `disabled`: the plan is intentionally inactive.
- `archived`: the plan is retained for history.

Task plan materialization readiness:

- `materializable`: a `ready` plan can be manually materialized.
- `blocked`: the plan cannot currently be materialized.
- `draft`: the plan is not ready.
- `disabled`: the plan is intentionally inactive.
- `archived`: the plan is retained for history.
- `missing context`: required plan metadata is missing, if applicable.

Materialization behavior:

- `materialize_task_plan()` is a manual call.
- only `ready` plans can be materialized.
- materialization creates a pending `TaskRecord`.
- materialization does not execute a task, create a result, or create an artifact.
- readiness diagnostics do not call `materialize_task_plan()`.
- the UI can materialize one selected `ready` task plan after `MATERIALIZE PLAN <plan id>` confirmation.
- UI materialization does not execute the materialized task, create results, create artifacts, scan plans, or change the source plan state.

GEO readiness fake preflight baseline:

- `DatasetAssetReadinessReport` checks fake expression matrix, sample annotation, platform annotation, gene annotation, and clinical annotation asset readiness.
- `GeneMappingReadinessReport` checks fake gene/probe/symbol/Ensembl mapping readiness without querying external databases.
- `SampleMappingReadinessReport` checks fake expression matrix sample ids against fake sample metadata ids.
- `ComparisonReadinessReport` checks explicit fake case/control group availability.
- `AnalysisPreflightSummary` aggregates asset, gene mapping, sample mapping, and comparison readiness into a runnable/non-runnable preflight report.
- Smoke/check displays an in-memory analysis preflight readiness summary.
- The UI can display registered `analysis_preflight_summary` results as read-only status.
- `scripts/run_fake_geo_preflight.py` validates the readiness/preflight chain with in-memory fixtures before real GEO readiness testing.
- The fake preflight path does not download real GEO data, execute DEG/enrichment analysis, create task results, create artifacts, or write execution logs.
- Controlled GSE33630 metadata-only readiness can parse a manually supplied Series Matrix file for metadata: 105 samples, 49 PTC, 45 normal/control, and 11 ATC samples excluded from the PTC vs normal/control candidate.
- Controlled GSE33630 expression readiness can report the local Series Matrix expression table without retaining the full matrix: 54675 features, 105 matrix samples, numeric values, zero missing values, zero negative values, and matched matrix-vs-metadata sample ids.
- Controlled GSE33630 GPL570 mapping readiness is acceptable: 45782 of 54675 probes map to symbols, mapping success rate is 0.8373, and the readiness preflight has no blocking errors.
- `DegReadyMatrixReport` and `build_deg_ready_matrix_report(...)` provide a fake-fixture DEG-ready matrix builder foundation with mean collapse reporting. It does not run formal DEG statistics or add scipy/statsmodels.
- Controlled GSE33630 DEG-ready matrix reporting connects expression values, sample groups, and GPL570 mapping: 54675 features, 45782 mapped features, 8893 unmapped features, 22880 genes after mean collapse, 49 cases, 45 controls, ready yes.

Task execution contract readiness:

- `TaskExecutionRequest` is a dry-run request by default.
- `TaskExecutionOutcome` records accepted/rejected/skipped/validation-failed contract outcomes.
- contract readiness means a task can build and validate a dry-run request.
- contract readiness diagnostics do not execute tasks or call Module 5/6 execution logic.

Mock runner diagnostics:

- `run_task_execution_request_mock()` validates a `TaskExecutionRequest` and returns a no-op outcome.
- valid dry-run requests are accepted as skipped.
- invalid requests are rejected with validation-failed outcome metadata.
- mock runner diagnostics are visible in smoke/check and the UI as read-only counts.
- the mock runner does not execute tasks, call Module 5/6, create results, or create artifacts.

Runner adapter foundation:

- `TaskRunnerAdapter` defines the future adapter shape: `runner_type`, `supports(task_type)`, and `execute(request)`.
- `RunnerAdapterRegistry` can register adapters, list adapters, find adapters by `task_type`, and summarize registrations.
- `NoOpRunnerAdapter` returns `not_implemented` outcomes and does not execute tasks.
- smoke/check and UI summaries report adapter counts, adapter types, supported task types, and no-op adapter counts.
- `ReportingSummaryRunnerAdapter` supports `task_type=profile_reporting_summary`.
- `dry_run=True` validates and returns accepted/skipped without calling `ReportingService`, creating a result, or creating an artifact.
- `dry_run=False` requires configured reporting/task services plus `analysis_id` and `project_id`, exports an analysis summary CSV, and registers one `profile_reporting_summary` result.
- the reporting runner does not mutate task state, call Module 5, start a scheduler, or expose a UI execute control.
- `scripts/run_task_once.py` is the manual CLI command for one selected task.
- the CLI defaults to `dry_run=True`; `--real-run` or `--no-dry-run` is required for explicit real execution.
- the CLI requires `--task-id` and `--state-dir`, never scans tasks, and is not a scheduler.
- each CLI invocation appends one execution log after an outcome is returned.
- execution log summaries report total logs, dry-run logs, real-run logs, success/accepted logs, failed/rejected logs, and logs with result ids.
- smoke/check and UI execution log summaries are read-only and do not create logs, results, artifacts, or task state changes.
- the UI provides a selected-task dry-run execute entry point and displays the latest manual execute outcome.
- UI dry-run execution does not expose real-run, scan tasks, create scheduler behavior, create results, or create artifacts.
- the UI displays selected-task real-run preflight state as read-only status, and smoke/check reports real-run preflight diagnostics.
- UI real-run is available only through a selected-task button gated by same-task dry-run success, explicit confirmation text, pending-task state, and adapter availability.
- UI real-run appends one execution log after the gated lifecycle outcome returns.
- UI real-run still does not scan tasks, start a scheduler, execute ready plans, or bypass lifecycle guards.
- UI task plan materialization creates a pending task from one selected ready plan only after explicit confirmation.
- Materialized tasks still require a separate dry-run or explicit manual real-run path before execution.

Manual runner command examples:

```bash
python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --dry-run
python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --real-run
```

Fake GEO preflight check:

```bash
python3 scripts/run_fake_geo_preflight.py
python3 scripts/run_fake_geo_preflight.py --json
```

The fake GEO preflight command uses in-memory fixtures only. It does not download GEO data, execute DEG/enrichment analysis, create task results, create artifacts, or write execution logs.

Module 9 packaging/localization readiness:

- `scripts/check_packaging_readiness.py` checks local packaging readiness prerequisites.
- the audit verifies `pyproject.toml`, `README.md`, `scripts/run_smoke_tests.py`, `scripts/run_task_once.py`, `scripts/run_fake_geo_preflight.py`, and core package directories.
- the audit reports missing items and recommended validation commands.
- `scripts/export_requirements.py` exports a minimal `requirements.txt` from `pyproject.toml`.
- `scripts/export_requirements.py --check` reports whether `requirements.txt` is in sync.
- `scripts/check_local_environment.py` reports Python version and local bootstrap prerequisites.
- `scripts/run_dev_checks.py` runs readiness, smoke, and unittest checks in one command.
- `scripts/run_dev_checks.py --quick` runs local environment, packaging readiness, `scripts/run_task_once.py --help`, fake GEO preflight, and smoke checks only.
- `scripts/project_status_snapshot.py` reports git, tag, module directory, and check script status.
- `v0.17-local-readiness-baseline` records the local readiness and migration preparation baseline.
- `v0.18-ui-task-results-polish` records read-only task results summary UI polish.
- the audit does not build packages, generate `dist/` or `build/`, install dependencies, or create virtual environments.

Recommended manual local bootstrap:

```bash
git clone <repo-url>
cd model9
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/run_dev_checks.py
```

Current boundaries:

- no `geo_workflow.py` changes
- no production TCGA/GDC/GTEx downloader
- no package build or generated packaging artifacts
- no dependency installation or virtual environment creation
- no `.venv` creation from readiness checks
- no `.venv` creation from developer verification
- no `requirements.txt` modification from local environment checks
- no package build from developer verification
- no git state changes from project status snapshots
- no global `pip freeze`
- no scheduler
- no automatic runner adapter execution
- no scheduler-driven task execution
- no Module 5/6 execution from the task contract
- no Module 5/6 execution from the mock runner
- no Module 5 execution from the reporting runner
- no task execution from contract readiness diagnostics
- no automatic materialization
- no workflow blocking
- no background thread, queue, or timer
- no task plan execution
- no TaskResultRecord or artifact creation during materialization
- no TaskRecord creation during readiness diagnostics
- ready plans are reporting-only and do not execute
- no workflow blocking by RuleService diagnostics or missing artifacts
- no real-data dependency
- UI summaries remain read-only for task results, artifact diagnostics, and task plans
- UI task results polish remains read-only
- UI task plan materialization only creates a pending task from a selected ready plan after confirmation
- UI does not provide execution or runner controls
- UI does not execute runner adapters

Recommended validation:

```bash
python3 scripts/run_smoke_tests.py
python3 -m unittest tests.test_task_plan_service
python3 -m unittest tests.test_task_management_service
python3 -m unittest tests.test_task_results_summary_widget
python3 -m unittest tests.test_main_window_reporting_summary
python3 -m unittest tests.test_packaging_readiness
python3 -m unittest tests.test_requirements_export
python3 -m unittest tests.test_local_environment_check
python3 -m unittest tests.test_dev_checks_script
python3 -m unittest tests.test_project_status_snapshot
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

Status audit:

- `docs/v0_15_status_audit.md`
- `docs/module9_packaging_readiness.md`
- `docs/development_baseline_index.md`

Baseline tags:

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
- `v0.32-geo-readiness-preflight-baseline`
- `v0.33-local-dataset-standardization`
- `v0.38-gse33630-exploratory-deg-summary`
- `v0.39-descriptive-volcano-table`
- `v0.40-real-dataset-harness`

`v0.11-module7-artifact-diagnostics` marks Module 7 artifact diagnostics service and smoke/check summary. `v0.12-ui-artifact-diagnostics` marks UI read-only display for task result artifact diagnostics. `v0.13-ui-task-plan-summary` marks TaskPlan foundation, smoke/check summary, and UI read-only task plan summary. `v0.14-ui-task-plan-materialization-readiness` marks manual plan materialization and materialization readiness diagnostics in smoke/check and UI. `v0.15-ui-execution-contract-readiness` marks task execution contract readiness diagnostics in smoke/check and UI. `v0.16-ui-mock-runner-diagnostics` marks mock/no-op runner diagnostics in smoke/check and UI. `v0.17-local-readiness-baseline` marks Module 9 packaging readiness, requirements export/check, local environment readiness, developer verification, project status snapshot, and documented migration flow. `v0.18-ui-task-results-polish` marks grouped read-only task results summary UI polish. `v0.19-runner-adapter-foundation` marks the runner adapter protocol, registry, no-op adapter, smoke/check diagnostics, UI read-only diagnostics, and real reporting runner adapter design audit. `v0.19-first-real-reporting-runner` marks the first real `profile_reporting_summary` runner foundation. `v0.20-reporting-runner-smoke-visibility` marks dedicated smoke/check visibility for `profile_reporting_summary` result counts and artifact readiness. `v0.21-reporting-runner-visibility-baseline` marks the UI visibility audit: `TaskResultsSummaryWidget` and artifact diagnostics already expose runner result rows and artifacts, so no dedicated runner-result UI count is added yet. `v0.22-manual-runner-wrapper` marks the manual service-level runner wrapper and smoke/check diagnostics; it remains explicit, dry-run by default, state-neutral, and non-scheduler. `v0.23-lifecycle-runner-wrapper` marks `execute_task_with_lifecycle(...)`: dry-run stays state-neutral, explicit non-dry-run can move one pending task through `running` to `completed` or `failed`, and smoke/check reports dry-run lifecycle diagnostics without real execution. `v0.24-cli-manual-runner` marks `scripts/run_task_once.py`, default dry-run CLI execution for one explicit task, readiness/dev-check coverage, and continued absence of scheduler, automatic task scan, UI execute button, production downloader, and `geo_workflow.py` changes. `v0.25-execution-log-baseline` marks `TaskExecutionLogRecord`, `task_execution_logs.json`, CLI outcome logging, smoke/check execution log summary, UI read-only execution log summary, and continued absence of scheduler, automatic task scan, UI execute button, production downloader, and `geo_workflow.py` changes.

`v0.28-ui-gated-real-run` marks selected-task gated UI real-run. The UI requires preflight, same-task dry-run success, explicit confirmation, pending task state, and adapter availability, then logs the returned outcome and refreshes summaries. It still has no scheduler, no automatic task scan, no production downloader, no Module 4/5/6 schema changes, and no `geo_workflow.py` changes.

`v0.29-real-run-hardening-retry-foundation` marks the UI real-run hardening and retry foundation baseline. It records the gated real-run behavior audit, hardened confirmation gate, hardened outcome refresh, failed-task retry policy audit, `create_retry_task(...)`, smoke/check retry task summary, and UI read-only retry task summary.

The retry creation UI baseline lets the UI create a new pending retry task from one selected failed task after task-bound confirmation (`CREATE RETRY <task id>`). The original failed task is unchanged, and the UI does not execute the retry, create results, create artifacts, add a retry execute button, scan tasks, or start scheduler behavior. The retry still needs a separate dry-run or explicit manual real-run path.

The task plan materialize UI baseline lets the UI create a pending task from one selected ready task plan after task-bound confirmation (`MATERIALIZE PLAN <plan id>`). Draft, disabled, archived, and missing plans are rejected with stable messages. The source plan remains unchanged, and the UI does not execute the materialized task, create results, create artifacts, scan plans, or start scheduler behavior.

The retry foundation still has no scheduler, no automatic task scan, no production downloader, no retry execute button, no Module 4/5/6 schema changes, and no `geo_workflow.py` changes.

`v0.30-artifact-preview-baseline` marks the read-only artifact preview baseline. It records `ArtifactPreviewRecord`, `preview_result_artifact(result_id, max_chars=4000)`, and the UI artifact preview panel. Preview is limited to text artifacts (`.csv`, `.json`, `.txt`, `.md`) and does not edit, delete, execute, or open artifacts in external programs. The next implementation target is the result detail viewer.

`v0.31-result-detail-viewer` marks the read-only result detail baseline. It records `TaskResultDetailRecord`, `get_task_result_detail(result_id)`, and the UI result detail viewer. Result detail shows result metadata and artifact status, while artifact content remains in the artifact preview panel. It still has no result edit/delete/rerun behavior, no scheduler, no production downloader, and no `geo_workflow.py` changes.

`v0.32-geo-readiness-preflight-baseline` marks the GEO readiness and fake preflight baseline. It records `DatasetAssetReadinessReport`, `GeneMappingReadinessReport`, `SampleMappingReadinessReport`, `ComparisonReadinessReport`, `AnalysisPreflightSummary`, UI read-only preflight summary display, `scripts/run_fake_geo_preflight.py`, and quick dev-check coverage for the fake preflight command. It still has no real GEO download, no production downloader, no DEG runner, no enrichment runner, and no `geo_workflow.py` changes. The next recommended step is a controlled practical GEO readiness test that stops at readiness/preflight review.

`v0.33-local-dataset-standardization` marks the local dataset standardization baseline. It records the local delivery scanner, selected import plan, local standardizer, validation report, GEO submission readiness checker, and standard asset compatibility contract. It remains processed-file-only: no FASTQ/BAM/CRAM parsing, no alignment, no FastQC/MultiQC, no DESeq2/edgeR/limma, no GEO auto submission, no production downloader changes, and no `geo_workflow.py` changes. Recommended next work is a mock local delivery practical test, controlled real GEO readiness test design, or UI local dataset import readiness display.

GPL570 mapping readiness baseline:

- `PlatformAnnotationMappingReport` records probe-to-symbol readiness counts for fake/local platform annotation fixtures.
- `parse_platform_annotation_mapping_report(...)` supports small local CSV/TSV fixtures with common probe and gene symbol columns.
- GEO Series Matrix preflight can consume an acceptable platform mapping report to clear the default GPL570/probe mapping readiness blocker.
- A GSE33630 GPL570 manual-test template is documented for a future locally supplied annotation file.
- This baseline does not download GPL570, run DEG/enrichment/survival, change production downloader behavior, or modify `geo_workflow.py`.

`v0.36-gse33630-deg-readiness` marks the GSE33630 DEG readiness baseline. It records runnable readiness/preflight status for GSE33630, acceptable GPL570 probe-to-symbol mapping, and the DEG-ready matrix builder foundation. It still has no formal DEG statistics, no limma/DESeq2/edgeR, no enrichment, no production downloader changes, and no `geo_workflow.py` changes. Recommended next work is a real GSE33630 DEG-ready matrix manual test or a minimal two-group DEG statistical runner audit.

The GSE33630 DEG-ready matrix baseline records a successful read-only manual report from local untracked files. Expression matrix, sample group labels, and GPL570 mapping are connected into `DegReadyMatrixReport`; no p-values, formal logFC, DEG result table, limma/DESeq2/edgeR, enrichment, production downloader change, or `geo_workflow.py` change is included. The next recommended step is a minimal two-group DEG statistical runner audit.

`v0.37-minimal-deg-summary-foundation` marks the minimal DEG summary foundation. It records `DegSummaryReport`, `DegSummaryRow`, mean/log2FC effect-size summaries, and `write_deg_summary_table(...)` for an effect-size-only CSV artifact. It is not formal DEG: no p-value, no FDR, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes. Next options are GSE33630 real minimal DEG summary manual test, scipy/statsmodels dependency audit, or formal DEG runner design.

`v0.38-gse33630-exploratory-deg-summary` marks the controlled GSE33630 exploratory DEG summary baseline. The read-only manual test successfully built the gene-level collapsed matrix and computed descriptive mean/log2FC summaries for 22880 genes, with 49 PTC cases and 45 normal/control samples. This remains non-formal DEG: no p-value, no FDR, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes. The formal DEG dependency audit recommends a dedicated scipy/statsmodels decision before changing requirements or implementing formal statistics.

`v0.39-descriptive-volcano-table` marks the descriptive volcano-ready table baseline. It records `write_volcano_ready_descriptive_table(...)`, the GSE33630 descriptive volcano table manual test, and explicit no-significance semantics: no p-value, no FDR, no formal DEG, no scipy/statsmodels, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes. The next decision point is whether to allow formal DEG dependencies.

`v0.40-real-dataset-harness` marks the Real Dataset Test Harness MVP. It records `RealDatasetReadinessReport`, the `RealDatasetGap` taxonomy, and `scripts/run_real_geo_readiness_test.py` for local-file controlled readiness tests. The GSE33630 harness smoke reports `gap_count=0`, `preflight_runnable=True`, `feature_count=54675`, `sample_count=105`, `mapping_success_rate=0.8373`, detected groups `['ptc', 'normal']`, and 11 excluded ATC samples. It still has no formal DEG, enrichment, survival, production downloader, automatic real dataset download, or `geo_workflow.py` changes. Next work is UI readiness report display and GSE60542/GSE27155 local-file testing.

`docs/gse33630_demo_readiness_report.md` is the current demo-facing readiness summary. It records GSE33630 as a PTC vs normal/control readiness benchmark with preflight runnable, zero harness gaps, 54675 features, 105 samples, mapping success rate 0.8373, 49 PTC samples, 45 normal/control samples, and 11 excluded ATC samples. It remains non-formal: no p-value, no FDR, no limma/DESeq2/edgeR, and no enrichment.
