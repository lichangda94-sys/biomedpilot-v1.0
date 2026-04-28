# Development Baseline Index

This index summarizes the current development baseline, module status, local readiness scripts, and actual `v0.*` tags in this repository.

## Module Status

- Module 4A: `RuleService` diagnostics are surfaced through smoke/check reporting.
- Module 4B: `AnalysisProfile` and `EngineReadyAnalysisConfig` provide profile rules and engine-ready export.
- Module 5: profile consumption foundation can create analysis inputs from exported profile configs.
- Module 6: reporting summary foundation includes analysis profile source metadata.
- Module 7: task/result management records tasks, results, execution logs, artifact diagnostics, task plans, materialization readiness, execution contract readiness, mock runner diagnostics, runner adapter registry diagnostics, and the first real reporting runner foundation.
- Module 7 reporting runner: `ReportingSummaryRunnerAdapter` supports `profile_reporting_summary`; dry-run is side-effect free, non-dry-run exports an analysis summary CSV and registers one `profile_reporting_summary` result, and smoke/check reports dedicated profile reporting result counts plus artifact readiness.
- Module 7 lifecycle wrapper: `execute_task_with_lifecycle(...)` explicitly handles one pending task through `running` to `completed` or `failed`; dry-run remains state-neutral and smoke/check reports dry-run lifecycle diagnostics.
- Module 7 execution logs: `TaskExecutionLogRecord` entries are stored in `task_execution_logs.json`, CLI manual runner outcomes are logged, and smoke/check reports execution log counts.
- UI: read-only summaries show reporting data, selected analysis summaries, task results, artifact diagnostics, task plans, materialization readiness, execution contract readiness, mock runner diagnostics, runner adapter diagnostics, and execution log summaries. The main window also has selected-task dry-run execution and a gated selected-task real-run path with same-task dry-run, confirmation, pending-state, and adapter checks.
- Module 9: readiness scripts cover packaging checks, requirements export/check, local environment checks, developer verification, and project status snapshots.
- v0.17: local readiness baseline documents packaging readiness, requirements export/check, environment readiness, developer verification, project status snapshot, and migration flow.
- v0.18: task results summary UI polish groups read-only sections, wraps long diagnostic text, and keeps result table cells non-editable.
- v0.19: runner adapter foundation records adapter protocol, registry, no-op adapter, smoke/check diagnostics, UI read-only diagnostics, real reporting runner adapter design audit, and the first real reporting runner baseline.
- v0.20: reporting runner smoke visibility records dedicated `profile_reporting_summary` result counts and artifact readiness in smoke/check output.
- v0.21: reporting runner visibility baseline records that generic task results UI and artifact diagnostics already cover real reporting runner results, so no dedicated runner-result UI count is added yet.
- v0.22: manual runner wrapper baseline records `execute_task_with_adapter(...)`, registry lookup, dry-run wrapper diagnostics, and the continued absence of scheduler or UI execution.
- v0.23: lifecycle runner wrapper baseline records `execute_task_with_lifecycle(...)`, explicit pending-task state transitions, dry-run diagnostics, and the continued absence of scheduler, automatic task scanning, and UI execution.
- v0.24: CLI manual runner baseline records `scripts/run_task_once.py`, default dry-run behavior, readiness/dev-check coverage, and continued absence of scheduler, automatic task scanning, and UI execution.
- v0.25: execution log baseline records `TaskExecutionLogRecord`, `task_execution_logs.json`, CLI outcome logging, smoke/check execution log summary, and UI read-only execution log summary.
- v0.28 gated real-run: selected-task UI real-run is available only through preflight-controlled gating, logs returned outcomes, and refreshes summaries without adding scheduler behavior.
- v0.29 real-run hardening and retry foundation: real-run confirmation and refresh paths are hardened, failed retry policy is audited, retry task records can be created from failed tasks, retry summaries are visible in smoke/check and UI, and the UI can create a pending retry task from one selected failed task after confirmation.
- Task plan materialize UI baseline: the UI can create one pending task from one selected ready plan after confirmation, rejects draft/disabled/archived/missing plans, and does not execute the materialized task.
- GEO readiness planning: `docs/real_geo_dataset_readiness.md` audits real GEO dataset file, mapping, sample alignment, comparison, preflight, and UI readiness risks before any real GEO analysis runner is implemented.
- Module 3 dataset readiness: `DatasetAssetReadinessReport` and `build_dataset_asset_readiness_report(...)` provide fake-input asset readiness checks for expression matrix, sample annotation, platform annotation, gene annotation, and clinical annotation.
- GEO practical readiness protocol: `docs/practical_geo_readiness_test_protocol.md` defines a manual future test plan for simple, platform-complex, and messy GEO datasets while stopping before DEG execution.
- Smoke/check: analysis preflight readiness is visible through an in-memory fake fixture summary, with no real GEO downloads, analysis execution, result creation, artifacts, or logs.
- Fake GEO preflight baseline: `scripts/run_fake_geo_preflight.py` validates asset/gene/sample/comparison/preflight readiness with in-memory fixtures and is covered by quick developer checks.
- v0.32 GEO readiness preflight baseline: the fake preflight chain, smoke/check summary, UI read-only preflight display, and dev-check coverage are documented as the last safe checkpoint before controlled practical GEO readiness testing.
- Local dataset standardization design: `docs/local_dataset_standardization.md` audits sequencing-company delivery folders, processed-file-only import, standard local asset outputs, and mock local delivery tests before implementation.
- GEO submission readiness design: `docs/geo_submission_readiness.md` audits manual GEO submission readiness signals for standardized local datasets without upload, production submission, or raw sequencing processing.
- Standard asset compatibility contract: GEO, TCGA/GTEx, sequencing-company delivery, and GEO-ready local package adapters should converge on `StandardExpressionMatrix`, `StandardSampleMetadata`, `StandardGeneAnnotation`, `StandardDatasetManifest`, `StandardValidationReport`, and optional `StandardQCReport`.
- v0.33 local dataset standardization baseline: local delivery scanner, selected import plan, local standardizer, validation report, GEO submission readiness checker, and standard asset compatibility contract are in place for processed files only.
- Controlled real GEO readiness test design: `docs/controlled_real_geo_readiness_test.md` defines the first readiness-only real GSE test plan and requires human selection of 2-3 GSE datasets before execution.
- Selected controlled PTC GEO readiness datasets: `GSE33630`, `GSE60542`, and `GSE27155` are recorded for readiness/mapping/preflight review only.
- GSE33630 readiness inspection: first controlled pass reviewed public GEO metadata only, confirmed suitability as a simple PTC vs normal benchmark, and identified the main gap as missing real accession-level readiness tooling.
- Real GEO accession readiness CLI design: proposed `scripts/run_geo_accession_readiness.py` as a read-only candidate-inventory command for GSE metadata, Series Matrix candidates, supplementary candidates, platform ids, sample metadata candidates, and expression candidates.
- Live GEO metadata fetch design: proposed explicit `--live` / `--timeout` accession-page metadata fetch only, with stable network/SSL/timeout/accession/parse errors and no Series Matrix, RAW, supplementary, or FASTQ/SRA downloads.
- GSE33630 post-live metadata audit: `--metadata-file` mode can parse saved GSE33630 accession metadata, while the first controlled `--live` attempt returned stable `ssl_error` in the local environment; the next recommended step is SSL/environment guidance or continued metadata-file mode before any Series Matrix download/parse audit.
- GEO live fetch SSL guidance: `ssl_error` is documented as a local Python/certificate/network environment issue, with browser-saved metadata plus `--metadata-file` as the controlled fallback; SSL verification should not be disabled by default and production downloader behavior remains unchanged.
- GSE33630 Series Matrix metadata-only audit design: the next controlled GEO step is scoped as an audit/fake-fixture parser design before any real Series Matrix download or parsing.
- GSE33630 metadata-only readiness implementation: saved GEO HTML parsing, sample count extraction, fake-fixture Series Matrix metadata parsing, group detection, and metadata-only preflight bridging are implemented; real Series Matrix file testing, expression values parsing, GPL570 mapping, and runnable DEG preflight remain unimplemented.
- GSE33630 real Series Matrix metadata-only retest: local manual `.txt.gz` metadata parsing succeeds with 105 samples, 49 PTC, 45 normal/control, and 11 ATC excluded; expression values parsing and GPL570 mapping remain blockers.
- GSE33630 metadata-only readiness baseline: PTC vs normal/control is identifiable from real Series Matrix metadata, but expression numeric parsing, GPL570 probe mapping, true runnable DEG preflight, and the DEG runner remain unimplemented.
- Series Matrix expression parser design: the next expression layer should parse table boundaries, header/sample ids, numeric status, missing values, negative values, feature count, and sample matching as a report only, without saving the full matrix or running DEG.
- GSE33630 expression readiness baseline: local manual `.txt.gz` expression reporting succeeds with 54675 features, 105 matrix samples, numeric values, zero missing values, zero negative values, and matched matrix-vs-metadata sample ids; GPL570 probe mapping and true runnable DEG preflight remain unimplemented.

## Current Boundaries

- no scheduler
- no scheduler-driven task execution
- no automatic task scanning
- no automatic runner adapter execution
- no Module 5 execution from reporting runner
- no production TCGA/GDC/GTEx downloader
- no workflow blocking by diagnostics
- no ungated UI execute behavior
- no UI edit/delete behavior
- no UI automatic execution behavior
- no `geo_workflow.py` changes
- no retry execute button
- no retry execution UI
- no real GEO/TCGA data dependency
- no real GEO expression matrix ingestion yet
- no real GEO file ingestion yet
- no Series Matrix / RAW / supplementary file download yet
- no Series Matrix / RAW / supplementary automatic downloader yet
- no full Series Matrix expression matrix persistence yet
- no GPL570 probe-to-symbol mapping yet
- no real GEO DEG runner
- no real GEO files downloaded for the selected PTC readiness datasets yet
- no source-specific adapter execution into Module 5 through the standard asset contract yet
- no GEO automatic submission
- no FASTQ/BAM/CRAM content parsing
- no alignment, quantification, FastQC/MultiQC, DESeq2/edgeR/limma execution
- no UI local dataset import readiness display yet
- no package build
- no `dist/` or `build/` generation
- no dependency installation from readiness scripts
- no virtual environment creation from readiness scripts
- no real analysis execution from readiness scripts

## Common Commands

```bash
python3 scripts/run_smoke_tests.py
python3 scripts/run_dev_checks.py --quick
python3 scripts/run_dev_checks.py
python3 scripts/project_status_snapshot.py
python3 -m unittest discover -s tests
```

## Recommended Migration Flow

```bash
git clone <repo-url>
cd model9
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/run_dev_checks.py
```

## Module 9 Scripts

- `scripts/check_packaging_readiness.py`: checks baseline packaging/localization readiness files and directories.
- `scripts/export_requirements.py`: exports `requirements.txt` from `pyproject.toml`.
- `scripts/export_requirements.py --check`: verifies `requirements.txt` is in sync.
- `scripts/check_local_environment.py`: checks local bootstrap prerequisites and prints recommended manual setup commands.
- `scripts/run_dev_checks.py`: runs readiness, smoke, and unittest checks.
- `scripts/run_dev_checks.py --quick`: runs local environment, packaging readiness, manual runner `--help`, and smoke checks.
- `scripts/run_task_once.py`: manually runs one selected task through the lifecycle wrapper; defaults to dry-run and requires explicit `--real-run` for non-dry-run execution.
- `scripts/project_status_snapshot.py`: prints git, tag, module directory, and check script status.

## Runner Planning

- `docs/module7_real_runner_audit.md`: audits the minimum input/output contract for a future real runner.
- First real runner type: `profile_reporting_summary`.
- Recommended first real adapter: `ReportingSummaryRunnerAdapter` with `runner_type=reporting_summary_runner`.
- Input contract: `task_id`, `task_type=profile_reporting_summary`, existing `analysis_id`, `project_id`, and optional `format=analysis_summary_csv`.
- Output contract: exported analysis summary CSV plus a registered `profile_reporting_summary` task result.
- Module 5 is not called by the first adapter; Module 6 reporting export is called only for validated `dry_run=False` requests.
- The first real adapter does not mutate task state; lifecycle transitions are owned by `TaskManagementService.execute_task_with_lifecycle(...)`.
- Task state transition audit recommends lifecycle ownership in a service-level wrapper rather than inside `ReportingSummaryRunnerAdapter`.
- Manual runner wrapper foundation can explicitly call one adapter for one task through `TaskManagementService.execute_task_with_adapter(...)`; it defaults to dry-run and stays state-neutral.
- Lifecycle runner wrapper foundation can explicitly call one adapter for one pending task through `TaskManagementService.execute_task_with_lifecycle(...)`; dry-run keeps state unchanged, successful non-dry-run moves to `completed`, failed non-dry-run moves to `failed`, and missing adapter keeps the task `pending`.
- Task state lifecycle hardening audit recommends `pending` as the only executable state; `running`, `completed`, and `failed` should be blocked by default, with failed-task retry left for a separate explicit policy.
- Lifecycle smoke/check diagnostics call dry-run only and report state mutations as `0`.
- UI manual execute button prerequisites are documented: the lifecycle wrapper is sufficient as a service prerequisite, but any future UI action must require one selected pending task, explicit confirmation, dry-run preflight, and no scheduler behavior.
- UI execute button readiness has been re-audited after lifecycle hardening: guards, execution logs, and CLI fallback are sufficient prerequisites for a selected-task-only UI foundation, with dry-run default and explicit confirmation for real-run.
- UI manual dry-run execute foundation is implemented for one selected task id and calls the lifecycle wrapper with `dry_run=True`; it refreshes summaries after outcome and does not expose real-run.
- UI real-run preflight state is displayed read-only for the selected task id: task existence, task state, pending eligibility, adapter availability, dry-run recommendation, UI real-run availability, and blocked reason.
- UI real-run button foundation is implemented with same-task dry-run gating, task-bound confirmation text, duplicate-click prevention, and refresh of task/result/artifact/log/preflight summaries.
- UI gated real-run behavior has been audited and hardened: it is selected-task-only, pending-only, preflight-gated, same-task dry-run gated, task-bound confirmation gated, and logs returned outcomes through `TaskExecutionLogRecord`.
- Failed task retry policy audit recommends creating a new pending retry `TaskRecord` with `retry_of_task_id` / `original_task_id` metadata rather than rerunning a failed task in place.
- Retry task record foundation implements `create_retry_task(original_task_id)` for failed originals only; it creates a pending retry task and does not execute it.
- Retry creation UI audit recommends selected-task retry creation for failed tasks only, with task-bound confirmation, stable rejection for non-failed tasks, summary refresh, and no retry execution.
- Retry creation UI foundation implements that selected-task flow: `CREATE RETRY <task id>` confirmation creates a pending retry task, keeps the original failed task unchanged, refreshes summaries, and does not execute the retry or create results/artifacts.
- Task plan materialize UI audit recommends selected-plan materialization for `ready` plans only, with task-bound confirmation, stable rejection for `draft`/`disabled`/`archived`/missing plans, summary refresh, unchanged source plan state, and no execution or result/artifact creation.
- Task plan materialize UI foundation implements that selected-plan flow: `MATERIALIZE PLAN <plan id>` confirmation creates a pending task from a ready plan, leaves the source plan unchanged, refreshes summaries, and does not execute the task or create results/artifacts.
- Artifact preview minimal UI audit recommends a read-only `result_id`-driven preview for `.csv`, `.json`, `.txt`, and `.md` artifacts, showing path, existence, type, size, and bounded text without modifying or opening files externally.
- Result detail viewer audit recommends a read-only `result_id` lookup for scalar `TaskResultRecord` fields, metadata, artifact path, and created timestamp, with artifact preview kept adjacent or embedded as a bounded sub-section.
- CLI manual runner command is implemented as `scripts/run_task_once.py`: default `dry_run=True`, one required `--task-id`, explicit `--real-run`, local state loading, registry construction, and lifecycle wrapper invocation.
- CLI examples: `python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --dry-run` and `python3 scripts/run_task_once.py --task-id <id> --state-dir <path> --real-run`.
- Task execution log foundation stores manual `TaskExecutionLogRecord` entries in `task_execution_logs.json`; logs are append/list metadata only.
- CLI manual runner invocations append one execution log after the lifecycle outcome is returned.
- Smoke/check execution log summary reports total logs, dry-run logs, real-run logs, success/accepted logs, failed/rejected logs, and logs with result ids.
- UI execution log summary displays the same counts in the read-only task results summary and does not trigger execution.
- Visibility audit: generic task result UI and artifact diagnostics already display `profile_reporting_summary` runner results; smoke/check now also reports dedicated `profile_reporting_summary` result counts and artifact readiness.
- UI visibility audit: a dedicated UI runner-result count is not recommended yet because the read-only result table already shows result type, analysis id, profile, artifact path, and artifact status.
- Still out of scope: scheduler, background queue, production downloads, automatic task scanning, and `geo_workflow.py` changes.

## Baseline Tags

- `v0.3-module4-rule-consumer`: Module 4 RuleService diagnostics consumer integration.
- `v0.4-module4-analysis-profiles`: Module 4 analysis profiles foundation.
- `v0.5-module5-profile-consumption`: Module 5 profile consumption foundation.
- `v0.6-module6-profile-reporting`: Module 6 profile reporting summary foundation.
- `v0.7-ui-reporting-summary-data`: UI reporting summary data foundation.
- `v0.8-ui-analysis-result-selection`: UI selected analysis id reporting summary loading.
- `v0.9-module7-task-results`: Module 7 task/result management foundation.
- `v0.10-ui-task-results-summary`: UI read-only task results summary.
- `v0.11-module7-artifact-diagnostics`: Module 7 artifact diagnostics service and smoke/check summary.
- `v0.12-ui-artifact-diagnostics`: UI read-only artifact diagnostics display.
- `v0.13-ui-task-plan-summary`: TaskPlan foundation, smoke/check summary, and UI read-only summary.
- `v0.14-ui-task-plan-materialization-readiness`: manual materialization and readiness diagnostics in smoke/check and UI.
- `v0.15-ui-execution-contract-readiness`: execution contract readiness diagnostics in smoke/check and UI.
- `v0.16-ui-mock-runner-diagnostics`: mock/no-op runner diagnostics in smoke/check and UI.
- `v0.17-local-readiness-baseline`: Module 9 local readiness scripts and migration documentation.
- `v0.18-ui-task-results-polish`: grouped read-only task results summary UI polish.
- `v0.19-runner-adapter-foundation`: runner adapter protocol, registry, no-op adapter, smoke/check diagnostics, UI read-only diagnostics, and real reporting runner adapter design audit.
- `v0.19-first-real-reporting-runner`: first real `profile_reporting_summary` runner foundation.
- `v0.20-reporting-runner-smoke-visibility`: dedicated smoke/check visibility for `profile_reporting_summary` result counts and artifact readiness.
- `v0.21-reporting-runner-visibility-baseline`: reporting runner UI visibility audit and baseline documentation.
- `v0.22-manual-runner-wrapper`: manual service-level runner wrapper and smoke/check diagnostics.
- `v0.23-lifecycle-runner-wrapper`: lifecycle-aware manual runner wrapper, explicit pending-task state transitions, dry-run smoke/check diagnostics, and UI execute button prerequisite audit.
- `v0.24-cli-manual-runner`: CLI/manual runner command, default dry-run behavior, one selected task execution path, and readiness/dev-check coverage.
- `v0.25-execution-log-baseline`: task execution log store, CLI outcome logging, smoke/check execution log summary, and UI read-only execution log summary.
- `v0.27-ui-dry-run-execute`: UI selected-task dry-run execute entry point, latest manual execute outcome display, and real-run preflight audit. Real-run remains CLI-only.
- `v0.28-ui-real-run-preflight`: UI selected-task real-run preflight state, smoke/check preflight diagnostics, and UI real-run button decision audit. Real-run remains CLI-only.
- `v0.28-ui-gated-real-run`: selected-task gated UI real-run baseline with same-task dry-run gating, task-bound confirmation, pending-task and adapter checks, outcome logging, and summary refresh.
- `v0.29-real-run-hardening-retry-foundation`: UI gated real-run behavior audit, hardened confirmation gate, hardened outcome refresh, failed retry policy audit, retry task record foundation, smoke/check retry task summary, UI read-only retry task summary, and selected-task retry creation UI. Retry execution remains a separate manual dry-run/real-run path.
- `v0.30-artifact-preview-baseline`: `ArtifactPreviewRecord`, `preview_result_artifact(...)`, and UI read-only artifact preview for `.csv`, `.json`, `.txt`, and `.md` artifacts.
- `v0.31-result-detail-viewer`: `TaskResultDetailRecord`, `get_task_result_detail(...)`, and UI read-only result detail viewer with artifact preview kept as a separate bounded content panel.
- `v0.32-geo-readiness-preflight-baseline`: dataset asset, gene mapping, sample mapping, comparison, and analysis preflight readiness reports; fake GEO preflight CLI; UI read-only preflight summary; and dev-check coverage without real GEO download or analysis execution.
- `v0.33-local-dataset-standardization`: local delivery scanner, selected import plan, local standardizer, validation report, GEO submission readiness checker, and standard asset compatibility contract for processed local delivery files.
- `v0.36-gse33630-deg-readiness`: runnable GSE33630 readiness/preflight status, acceptable GPL570 mapping, DEG-ready matrix builder foundation, and explicit deferral of formal DEG statistics.
- `v0.40-real-dataset-harness`: Real Dataset Test Harness MVP with `RealDatasetReadinessReport`, `RealDatasetGap` taxonomy, local-file `scripts/run_real_geo_readiness_test.py`, GSE33630 smoke readiness, and continued exclusion of formal DEG, enrichment, survival, production downloader changes, automatic real dataset downloads, and `geo_workflow.py` changes.

## Recommended Next Baseline

The reporting runner foundation now has smoke/check visibility, a documented UI visibility assessment, an explicit failure-path policy, a manual runner wrapper, lifecycle-aware state transitions, dry-run lifecycle diagnostics, a CLI manual runner command, readiness coverage for that command, execution log summaries in smoke/check and UI, lifecycle guard hardening, lifecycle guard diagnostics, a selected-task-only UI dry-run execute entry point, latest execute outcome display, UI real-run preflight state, smoke/check preflight diagnostics, a strictly gated UI real-run button foundation, UI real-run execution log persistence, hardened real-run confirmation/refresh behavior, retry task summaries in smoke/check and UI, selected-task retry creation UI, selected-plan materialize UI, artifact preview service/UI foundations, result detail service/UI foundations, GEO readiness fake preflight coverage, local dataset standardization foundations, GEO submission readiness checking, a standard asset compatibility contract, controlled real GEO readiness test design, selected PTC GEO datasets, and a first GSE33630 metadata-only readiness inspection. Recommended next action is a narrow real GEO accession readiness CLI or, if manually comparing dataset complexity first, continue with `GSE60542`.

## GPL570 Annotation Parser Design

The next readiness layer should inspect a locally provided GPL570-style platform annotation fixture and produce a probe-to-symbol mapping report. This is a parser/readiness design only; it does not download GPL570, query GEO, run DEG, or modify `geo_workflow.py`.

Minimum input forms:

- a local platform annotation text/CSV/TSV fixture with probe id and gene symbol columns.
- optional aliases for common Affymetrix/GEO columns such as `ID`, `ID_REF`, `Probe Set ID`, `Gene Symbol`, `Gene symbol`, `GENE_SYMBOL`, and `Symbol`.
- fake/minimal fixtures for unit tests before any real GPL570 file is inspected.

Minimum report fields should include:

- platform id, expected `GPL570` for the first controlled GSE33630 path.
- probe count.
- mapped probe count.
- unmapped probe count.
- duplicated symbol count.
- mapping success rate.
- acceptable yes/no.
- warnings and errors.

Parser behavior:

- identify the probe id column.
- identify the gene symbol column.
- strip empty symbols and common placeholder values.
- split multi-symbol cells only when the delimiter strategy is explicit; the first foundation can use the first non-empty symbol and warn.
- count duplicated target symbols because multiple probes may map to one gene.
- mark mapping unacceptable if success rate is below a conservative threshold.
- never infer biology from probe ids alone.

Preflight integration design:

- `AnalysisPreflightSummary` should continue to accept metadata and expression reports independently.
- a future `PlatformAnnotationMappingReport` can be passed into the GEO Series Matrix preflight helper.
- if platform mapping is acceptable, the GPL570/probe mapping blocker can be cleared.
- if platform mapping is missing or unacceptable, DEG preflight remains blocked or warning-only according to the explicit policy implemented in the bridge.

Boundaries:

- no real GPL570 download in this design task.
- no production downloader changes.
- no DEG, enrichment, or survival.
- no full expression matrix persistence.
- no GEO/TCGA/GTEx integration changes.
- no `geo_workflow.py` changes.

Next minimal implementation should add a small report model and fake-fixture parser, then wire the report into preflight without touching DEG execution.

- GPL570 annotation readiness manual-test plan: a future controlled test can use a locally supplied untracked GPL570 annotation file to evaluate probe id and gene symbol mapping counts, duplicated symbols, mapping success rate, and acceptable status. It does not download GPL570 or run DEG.

- v0.35 GPL570 mapping readiness baseline: records `PlatformAnnotationMappingReport`, fake/local fixture parsing, preflight bridge support for acceptable platform mapping, and a GSE33630 GPL570 manual-test plan. It still has no real GPL570 download, no DEG runner, no production downloader changes, and no `geo_workflow.py` changes.

- GSE33630 preflight after GPL570 mapping: local manual Series Matrix and GPL570 annotation checks now produce a runnable readiness/preflight summary with 54675 features, 105 samples, 49 PTC, 45 normal/control, mapping success rate 0.8373, and no blocking errors. DEG execution is still not implemented.

- GSE33630 DEG runner readiness decision: readiness evidence now supports starting a DEG runner design audit, because expression reporting, sample mapping, PTC vs normal/control grouping, ATC exclusion, and GPL570 mapping are acceptable. DEG execution remains unimplemented.

- GSE33630 DEG runner design audit: `docs/geo_deg_runner_design.md` recommends a DEG-ready matrix builder before formal DEG statistics, because current runtime dependencies do not include scipy/statsmodels. Scope remains GSE33630-like, two-group PTC vs normal/control, no enrichment, no survival, no downloader changes, and no `geo_workflow.py` changes.

- v0.36 GSE33630 DEG readiness baseline: GSE33630 preflight is runnable at readiness level, GPL570 mapping is acceptable, and `DegReadyMatrixReport` / `build_deg_ready_matrix_report(...)` provide the first DEG-ready matrix builder foundation. Formal DEG statistics, limma/DESeq2/edgeR, enrichment, production downloader changes, and `geo_workflow.py` changes remain unimplemented.

- GSE33630 DEG-ready matrix manual report: expression values, sample groups, and GPL570 mapping now feed a read-only `DegReadyMatrixReport` with 54675 features, 45782 mapped features, 8893 unmapped features, 22880 genes after mean collapse, 49 cases, 45 controls, and ready = yes. Formal DEG statistics remain unimplemented.

- Minimal two-group DEG runner design audit: recommends either a standard-library effect-size-only runner without p-values/FDR, or a separate scipy/statsmodels dependency audit before formal statistics. Scope remains PTC vs normal/control only, with no limma/DESeq2/edgeR, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

- v0.37 minimal DEG summary foundation: records `DegSummaryReport`, `DegSummaryRow`, mean/log2FC summary computation, and `write_deg_summary_table(...)` for effect-size-only CSV output. It explicitly has no p-value, no FDR, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes.

- Formal DEG statistical dependency audit: current minimal DEG summaries remain descriptive only. Formal DEG requires a statistical test, multiple-testing correction, p-value, adjusted p-value, logFC semantics, and dependency policy. Recommended next step is a dedicated scipy/statsmodels audit before changing requirements or implementing formal DEG.

- v0.38 GSE33630 exploratory DEG summary baseline: records the read-only real-file manual exploratory mean/log2FC summary, successful gene-level collapsed matrix construction for 22880 genes, 49 case samples, 45 control samples, and the dependency-audit conclusion that formal p-values/FDR require a separate scipy/statsmodels decision. It remains non-formal DEG with no p-value, no FDR, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes.

- Volcano-ready descriptive table design: defines a no-dependency `volcano_ready_descriptive_table.csv` shape built from `DegSummaryReport.rows`. It includes log2FC and `abs_log2fc` but leaves `pvalue` and `padj` empty, with `pvalue_available=false`, `fdr_available=false`, and `method=descriptive_mean_log2fc`. It is exploratory/descriptive only and not valid for formal significance thresholds.

- v0.39 descriptive volcano table baseline: records `write_volcano_ready_descriptive_table(...)` and the GSE33630 descriptive volcano table manual test. The table is plot-shaped but descriptive only: no p-value, no FDR, no formal DEG, no statistical significance claim, no scipy/statsmodels, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes. Next step is a formal DEG dependency decision.

- Formal DEG dependency decision: formal DEG requires a two-group statistical test, p-value, adjusted p-value, log2FC, and stable result table policy. If new dependencies are allowed, the recommended first formal stack is scipy for the test plus statsmodels for FDR correction. If dependencies remain disallowed, the project should continue descriptive DEG reporting/UI only. No dependencies were added in this audit.

- Real dataset test registry: `docs/real_dataset_test_registry.md` records controlled real-dataset readiness benchmarks, starting with GSE33630, GSE60542, and GSE27155. The registry tracks purpose, expected groups, expected challenges, current status, blocking gaps, and next action without downloading data or running formal analysis.

- Real dataset readiness report foundation: `RealDatasetReadinessReport` and `RealDatasetGap` normalize real-dataset readiness outputs and classify failures into stable categories such as metadata parsing, Series Matrix parsing, expression matrix, sample mapping, gene mapping, group detection, comparison readiness, preflight, UI display, and manual-confirmation gaps.

- Local-file real GEO readiness runner: `scripts/run_real_geo_readiness_test.py` connects saved accession metadata, local Series Matrix files, optional platform annotation files, group detection, expression reporting, platform mapping, preflight, and gap classification into a structured JSON/Markdown report. It does not network, download data, run analysis, create task results/logs, or modify `geo_workflow.py`.

- Real dataset fixture regression policy: `docs/real_dataset_fixture_policy.md` defines how real-data failures become small committed fixtures. Full local GEO/GPL files and generated `real_dataset_tests/` reports stay untracked by default.

- Real dataset harness readiness checks: Module 9 readiness/dev checks now verify that `scripts/run_real_geo_readiness_test.py` exists and that its `--help` path runs. They do not execute a dataset test or read manual real files.

- v0.40 real dataset harness baseline: records the harness MVP and the controlled GSE33630 smoke result: `gap_count=0`, `preflight_runnable=True`, `feature_count=54675`, `sample_count=105`, `mapping_success_rate=0.8373`, detected groups `['ptc', 'normal']`, and 11 excluded ATC samples. Next recommended work is UI readiness report display and GSE60542/GSE27155 local-file testing.

- GSE33630 demo readiness report: `docs/gse33630_demo_readiness_report.md` records the demo-facing readiness state for PTC vs normal/control, including preflight runnable, zero harness gaps, expression readiness, GPL570 mapping readiness, DEG-ready matrix readiness, and explicit non-formal DEG boundaries.

- UI real dataset readiness summary: `TaskResultsSummaryWidget` can display a precomputed `RealDatasetReadinessReport` summary in read-only form. MainWindow only reads an already available summary from the task service and does not run the harness, read local manual data, create results/artifacts/logs, or execute analysis.

- Real dataset gap fixture workflow audit: `docs/real_dataset_fixture_policy.md` maps harness gap categories to small regression fixture types, naming conventions, size limits, required source/purpose metadata, and mandatory unit-test coverage. It does not implement a fixture generator.

- Next real dataset decision brief: recommends GSE60542 as the next local-file harness target to stress complex primary/metastasis/N0-N1 sample metadata. GSE27155 remains the platform/multi-class alternative, while GSE33630 should continue only for formal DEG dependency decision or descriptive demo polish.

- GSE60542 local-file harness inspection: expression readiness, sample id matching, GPL570 mapping, and PTC-vs-normal preflight are usable. The first pass exposed 22 ambiguous LNM/recurrence/N1-related samples; after choosing the PTC-vs-normal exclusion policy, 24 non-target LNM/recurrence samples are excluded, ambiguous samples are 0, gap count is 0, and the comparison has 34 PTC and 34 normal samples.

- GSE60542 PTC-vs-normal readiness baseline: marks GSE60542 complete for the selected PTC-vs-normal readiness path with runnable preflight and no gaps. Primary-vs-LNM and N0-vs-N1 remain unimplemented future comparison designs.

- GSE27155 SOFT readiness: local `family.soft.gz` parsing is supported through `--soft-file`. The inspection parsed GPL96 metadata for 99 samples, reported 22283 numeric expression features with matched sample ids, mapped 21225 of 22283 GPL96 probes with mapping success rate 0.9525, detected 51 PTC samples and 4 normal samples, excluded 44 non-target thyroid tumor samples, and cleared ambiguous grouping. GSE27155 is a multi-class/platform readiness benchmark; the PTC-vs-normal/control comparison is a readiness candidate, but normal n=4 requires a small-control warning and is not recommended as the primary formal DEG demo benchmark. Remaining scoped work is comparison-policy review; no DEG, enrichment, downloader, or `geo_workflow.py` changes were made.
