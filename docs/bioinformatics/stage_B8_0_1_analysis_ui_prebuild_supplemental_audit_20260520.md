# Bioinformatics B8.0.1: Analysis UI Prebuild and Result-System Supplemental Audit

Date: 2026-05-20

Workspace audited: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`

Branch: `dev/ui-shell`

Audited HEAD: `4f644bfc2d263f0e931b454b59e092149210731c`

Source B8 report workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Source B8 report commit: `f543904 docs(bio): audit analysis readiness and standardization`

## Executive Summary

UIShell already has a coherent Developer Preview workflow shell for Bioinformatics: source registration, recognition, readiness, standardization, analysis task center, result browser, project report draft, and settings/local-AI page are present. The current UI is therefore ready for analysis UI rebuild planning, but it is not ready to expose formal DEG, GSEA, survival, clinical association, plot generation, or report-ready export as primary runnable product actions.

The most important supplemental finding is that the current UI has mixed maturity signals. Some labels and manifests correctly say "Developer Preview", "dry-run", "preflight", "testing", and "尚未执行真实 DEG"; however, the analysis task center still exposes broad primary buttons such as `运行 GEO 差异分析`, `绘制火山图`, `表达热图`, `GSEA`, and report export placeholders close to the formal workflow. These should be governed by a stricter status model before B8.1/B8.2 UI work.

Immediate recommendation: do not rebuild the analysis center around direct run buttons. Build B8.1 first: a standardized analysis input resolver plus task-run contract that consumes only standardized repository artifacts and produces machine-checkable blockers, warnings, semantics, and result-index registrations.

## Scope and Source Documents

This audit is document and code inspection only. It did not implement analysis features, install dependencies, download large data, modify TCGA/GTEx/GEO pipelines, or copy legacy code.

Primary task brief:

- `/Users/changdali/Desktop/UI/审计/B8_0_1_analysis_ui_prebuild_supplemental_audit_task.md`

Required B8 source report:

- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B8_analysis_readiness_and_standardization_audit_20260520.md`

UIShell evidence reviewed:

- `app/bioinformatics/project_analysis_tasks.py`
- `app/bioinformatics/analysis_task_runs.py`
- `app/bioinformatics/deg_executor_preflight.py`
- `app/bioinformatics/results/project_results.py`
- `app/bioinformatics/reports/project_report_builder.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/project_workflow_orchestrator.py`
- `app/bioinformatics/project_readiness.py`
- `app/bioinformatics/services/geo_differential_expression_runner.py`
- `app/bioinformatics/services/enrichment_runner.py`
- `app/bioinformatics/services/correlation_runner.py`
- `app/bioinformatics/services/survival_service.py`
- `config/bioinformatics/analysis_defaults.yaml`
- `config/bioinformatics/enrichment_defaults.yaml`
- `config/bioinformatics/plotting_defaults.yaml`
- `config/bioinformatics/package_requirements.yaml`
- `config/bioinformatics/survival_defaults.yaml`
- `docs/stage_UI_10_bioinformatics_analysis_task_center_report.md`
- `docs/stage_UI_11_bioinformatics_results_browser_report.md`
- `docs/stage_UI_12_bioinformatics_report_viewer_report.md`
- `docs/stage_UI_13_bioinformatics_settings_local_ai_report.md`
- `docs/bioinformatics_deg_executor_readiness_audit.md`
- `tests/bioinformatics/*`

Legacy / adjacent evidence reviewed:

- `../Integration/app/bioinformatics/standardized_asset_selection.py`
- `../Integration/app/bioinformatics/analysis_task_runs.py`
- `../Integration/app/bioinformatics/deg_executor_preflight.py`
- `app/bioinformatics/legacy/geo_processing/*`
- `app/bioinformatics/legacy/geo_pipeline/process.py`
- `../ReleaseBuild/archive/legacy_sources/model9/*`

## What B8 Covered Well

B8 correctly established the main safety boundary:

- Standardization is an asset-organizing and preparation layer, not biological normalization, probe mapping, batch correction, or formal statistical design.
- Downstream analysis must consume standardized repository artifacts and analysis input packages, not recognition outputs directly.
- GEO DEG, TCGA DEG, ORA, correlation, and B7 immune/TME scoring have reusable foundations but are not a productized task-run path.
- GSEA, KM/Cox/log-rank, formal clinical association, formal plotting, and report-ready export are not implemented.
- `scipy`, `statsmodels`, R, Bioconductor packages, and plotting/survival packages need explicit dependency detection rather than implicit assumptions.
- B8.1 should build the standardized analysis input resolver and task-run contract before formal analysis execution.

## Gaps Not Covered by B8

B8 did not fully translate those backend conclusions into UI state, button state, result semantics, report gating, i18n copy readiness, and settings dependency detection rules. This supplemental audit fills that gap.

Additional UI-specific findings:

- The current task center lists many planned tasks in one table, but not every task has a strict user-facing semantic state such as `preflight_only`, `exploratory`, or `blocked_missing_resolver`.
- The `can_run` field in `analysis_task_center.json` is broader than "formal analysis can run"; it can mean "can create a plan", "can use imported result", "can run preview/testing runner", or "can proceed to a placeholder task record".
- Result browser distinguishes imported DEG and dry-run task records, but result index fields are not yet strong enough to support formal report-ready decisions.
- Report viewer produces a project Markdown draft, not a report-ready scientific package.
- Settings currently shows core local environment and GEO legacy checks, but not a structured analysis dependency registry.

## Current Runtime Capability Map

| Runtime area | Current implementation | Current capability | Audit verdict |
| --- | --- | --- | --- |
| Readiness dashboard | `project_readiness.py`, workflow pages | Detects missing expression/sample/clinical/GMT inputs and warns on TCGA+GTEx preview/testing | Useful pre-analysis UI, not formal execution proof |
| Standardized assets | `project_standardization.py`, `standardized_asset_selection.py` | Registers count, normalized expression, imported DEG, annotation, clinical-like assets; supports default asset selection | Good bridge foundation; still missing unified resolver API |
| Analysis task center | `project_analysis_tasks.py`, `workflow_pages.py` | Lists tasks, creates task records, creates DEG task plan/run records, can run DEG preflight, still has `运行 GEO 差异分析` preview path | Needs stricter button gating and semantics before B8 UI rebuild |
| DEG task runs | `analysis_task_runs.py`, `deg_executor_preflight.py` | Dry-run task records; materializes DEG input preflight with checks; no real DEG statistics | `preflight_only` |
| GEO DEG runner | `geo_differential_expression_runner.py` | Can produce local two-group summary with optional SciPy Welch p-values/fallback | Testing-level runner, not formal product path |
| TCGA DEG runner | `tcga/deg_runner.py` | Minimal tumor-normal summary with optional SciPy | Testing-level runner, not formal B6 continuation |
| ORA runner | `enrichment_runner.py` | Local GMT ORA from DEG table | Developer preview; formal only after trusted DEG/result schema |
| Correlation runner | `correlation_runner.py` | Local Pearson against target gene | Developer preview; needs resolver, parameter UI, result registration |
| Survival | `survival_service.py`, TCGA clinical readiness | Preflight only | KM/Cox/log-rank not implemented |
| Result browser | `results/project_results.py` | Reads result index, imported DEG, task-run records; previews imported DEG rows | Result browser foundation, not formal artifact schema |
| Report draft | `reports/project_report_builder.py` | Generates Markdown draft and manifest with explicit dry-run limitations | Draft only; not report-ready |
| Settings dependencies | `app/shared/environment/checks.py`, settings page | Python, PySide6, R path, storage, GEO legacy check | Missing analysis package registry/detection |

## Analysis UI Status Matrix

### Analysis Capability Matrix

| Analysis type | Current implementation status | Main UI entry? | Recommended UI label | Recommended button state | Required prerequisites | Required blocker / warning | Follow-up stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEG recompute | DEG task plan, dry-run run record, executor preflight; GEO/TCGA runners exist outside productized resolver | No formal main entry | 仅预检查 / 需要标准化输入解析器 | Enable config and preflight only; disable formal run | Resolver, confirmed count asset, confirmed design, DEG-ready matrix, backend decision | No resolver; no formal DEG backend; TPM/FPKM cannot enter count-model DEG; probe/ID_REF must be mapped | B8.1, B8.2, B8.3 |
| Imported DEG review / imported result reuse | Imported DEG table detection, preview, threshold filtering | Yes as result review, not recompute | 导入结果复用 / imported_external_result | Enable browse/reuse; disable "BioMedPilot recomputed" language | Imported DEG schema recognition, result semantics, source provenance | Imported result is external; padj missing may use pvalue only as temporary filter | B8.4 |
| ORA enrichment | Local GMT ORA runner exists | Not as formal main entry | 开发者预览 / 需要结果结构 | Enable only developer preview or hide until DEG result schema | Formal/imported DEG result, selected GMT, gene ID mapping policy | Must not run from raw expression; MSigDB/manual resource must be explicit | B8.3, B8.4 |
| GSEA preranked | Defaults/config exist; execution not implemented | No | 暂未实现 / 需要统计后端 | Disable | Ranked gene list schema, GMT, backend/package decision | No GSEA executor; no rank metric policy | B8.5 or later |
| Correlation analysis | Local Pearson runner exists | Not formal | 开发者预览 / 需要标准化输入解析器 | Developer preview only | Standardized expression package, target gene, sample count policy | No unified task-run/result schema; p-value/FDR policy absent | B8.4 |
| Immune / TME score linkage | B7 exploratory score referenced by B8; current UIShell mostly readiness/result shell | No formal main entry | 探索性结果 | Enable browse/linkage preflight only | B7 score artifact, expression/sample mapping, semantics | Exploratory score is not deconvolution; no clinical conclusion | B8.4 |
| TCGA clinical association | Clinical import/readiness exists; no association statistics | No | 仅预检查 | Enable preflight only | TCGA clinical table, field mapping, missingness report | No association statistics or multiple-testing policy | B8.7 |
| Survival analysis | Preflight service; TCGA OS readiness | No formal main entry | 仅预检查 | Enable survival preflight only; disable KM/Cox/log-rank | Survival package, OS_time/OS_event, censoring policy, backend | KM/Cox/log-rank not implemented | B8.7 |
| Volcano plot | Plot defaults and imported DEG preview exist; no plot artifact schema | No | 需要结果结构 | Disable formal generation | Formal/imported DEG result, plot schema | No plot artifact schema; avoid fake volcano-shaped tables | B8.5 |
| Heatmap | Task template and plotting defaults exist | No | 需要结果结构 | Disable formal generation | DEG result or expression subset package, plot schema | Must not read ad hoc temp matrix as formal plot | B8.5 |
| Enrichment plot | Plot defaults exist | No | 需要结果结构 | Disable | Enrichment result artifact, plot schema | Must inherit ORA/GSEA result semantics | B8.5 |
| Correlation plot | Plot defaults exist | No | 需要结果结构 | Disable | Correlation result artifact, plot schema | No formal correlation result schema | B8.5 |
| KM plot | Survival plot defaults exist | No | 暂未实现 | Hide or disable | Survival result artifact, backend | No KM/log-rank/Cox execution | B8.7 then B8.5 |
| Markdown report draft | Project report builder exists | Yes as draft | 报告草稿 | Enable draft generation | Result index entries, upstream manifests | Draft is not report-ready; no clinical/scientific conclusion | B8.6 |
| Report-ready export | Not implemented; DOCX/HTML placeholders | No | 暂不显示 / 需要结果结构 | Disable | Stable result schemas, plot artifacts, provenance, validation status | Report-ready gate missing | B8.6 |

## Recommended Analysis Center Structure

Recommended order for the analysis center:

1. Current project / dataset summary.
2. Standardized asset status.
3. Analysis input package status.
4. Analysis capability matrix.
5. Blockers and repair actions.
6. Task configuration entry.
7. Preflight result panel.
8. Formal run entry, shown only when prerequisites pass.
9. Result index entry.
10. Report and plot entry, shown only when stable result artifacts exist.

Current UIShell already has similar pieces, but they are distributed across readiness, standardization, task center, result browser, report viewer, and settings. The rebuild should not create another parallel page that bypasses these artifacts. It should compose those existing stage outputs into one analysis center state model.

Current repeated or risky entries:

- Readiness and task center both communicate "can run" states, but with different semantics.
- Task center includes planned formal tasks beside actually available preview/dry-run actions.
- Result browser and report viewer can continue when task records exist, even when no formal computed result exists.
- Settings has general environment state but not analysis dependency state.

## Button Enablement and Blocking Rules

### UI Button State Matrix

| Button / action | Should display now? | Should enable now? | Enable condition | Disabled reason | User next action |
| --- | --- | --- | --- | --- | --- |
| Enter DEG configuration | Yes | Yes, if count asset and confirmed design exist | Standardized count matrix selected; group/comparison design confirmed | Missing count asset, missing design, or multi-candidate asset unresolved | Generate standardized assets; choose default asset; confirm groups |
| Run DEG preflight | Yes | Yes, after DEG task run exists | DEG plan + task run + selected count matrix + confirmed design | Missing resolver/task run or DEG input package | Create DEG task plan and run record |
| Run formal DEG | Yes, but disabled or hidden behind developer flag | No | B8.3 formal backend, result schema, dependency snapshot, output contract | No formal DEG backend; no completed output guard | Complete B8.1-B8.3 |
| Run ORA | Yes as developer preview only | No for formal ORA | Formal/imported DEG result + GMT + gene ID mapping | Missing trusted DEG result or gene set | Select imported/formal DEG result and register GMT |
| Run GSEA preflight | Yes | No until ranked-list package exists | Ranked gene list package + GMT | No ranked-list schema | Complete B8.1/B8.4 package schema |
| Run GSEA | Hide or disabled | No | GSEA executor/backend and rank metric policy | Not implemented | Complete GSEA design/backend milestone |
| Run correlation | Yes as developer preview | No for formal run | Resolver expression package + target gene + result schema | Runner exists but not productized through resolver/result index | Build B8.1/B8.4 correlation task contract |
| Run immune score linkage | Yes as exploratory linkage | Only preflight/linkage, not formal deconvolution | B7 score artifact + sample alignment | B7 score is exploratory, not deconvolution | Register B7 result semantics and linkage preflight |
| Run clinical association | Yes as preflight only | No for formal statistics | Clinical table + field mapping + association design | No association statistics | Complete B8.7 design audit |
| Run survival preflight | Yes | Yes when clinical/survival metadata exists | OS_time/OS_event candidates and sample/case mapping | Missing survival fields or clinical table | Import/standardize clinical metadata |
| Run KM / Cox / log-rank | Hide or disabled | No | Survival backend, censoring policy, result schema | Not implemented | Complete B8.7 |
| Generate volcano plot | Yes only after result exists | No now | Formal/imported DEG result and plot schema | No plot artifact schema; fake plot risk | Complete B8.5 |
| Generate heatmap | Yes only after package/result exists | No now | DEG result or expression subset package and plot schema | No stable plot schema | Complete B8.5 |
| Generate KM plot | Hide or disabled | No | Survival result artifact | No survival execution | Complete B8.7 then B8.5 |
| Generate Markdown draft | Yes | Yes | Result index or upstream manifests available | If no result index, draft should say no result | Use as audit draft only |
| Mark report-ready | Yes but disabled | No | All results formal/imported with provenance, validation no blockers, plots from artifacts | Report-ready gate missing | Complete B8.6 |
| Export report package | Yes but disabled | No | Markdown + tables + plots + provenance + logs package schema | Export package schema missing | Complete B8.6 |

Mandatory cross-cutting blockers:

- Without resolver, do not enable formal analysis.
- If multiple candidate matrices exist and no default is selected, do not enable formal analysis.
- If GEO probe / ID_REF is unmapped, do not enable formal DEG.
- TPM / FPKM must not enter count-model DEG.
- GTEx must not be automatically used as TCGA normal control.
- Survival can be preflight only; KM/Cox/log-rank remain disabled.
- Report-ready must wait for stable result schema, provenance, validation status, and plot artifacts.

## Result Index and Task-Run Audit

Current result system:

- `results/project_results.py` creates `results/summaries/result_index.json`.
- It can include `imported_deg_result`, `analysis_task_run`, and `completed_result`.
- Imported DEG entries are labeled as imported table results.
- Dry-run task runs are represented as task records, not completed results.
- Missing result files produce warnings.

Gaps:

- `completed_result` is permissive; a future formal executor needs a validated registration function per task type.
- No stable field exists for `result_semantics`.
- No mandatory input package ID, dependency snapshot, engine version, command/log path, validation status, or blocker list exists for every entry.
- Plot and report artifact relationships are not normalized.
- Old results can be carried into the index without migration/reindex status.

### Result Artifact / Schema Gap Matrix

| Artifact type | Current existence | Stable schema? | Required semantics | Main gap |
| --- | --- | --- | --- | --- |
| DEG dry-run task record | Yes, `analysis_runs/deg/<run_id>/task_run.json` | Partial | `preflight_only` / `testing_level` | Not a computed DEG result |
| DEG executor preflight | Yes, `executor_preflight.json` | Partial | `preflight_only` | Needs resolver package ID and dependency snapshot |
| Imported DEG table | Yes via standardized asset/result browser | Partial | `imported_external_result` | Needs formal imported-result schema and provenance |
| Formal DEG result | No | No | `formal_computed_result` | Backend, schema, p/FDR policy, registration missing |
| ORA result | Runner writes CSV/JSON when invoked | Partial | `developer_preview` until registered | Not wired to resolver/result index contract |
| GSEA result | No | No | `not_implemented` | Executor absent |
| Correlation result | Runner writes CSV/JSON when invoked | Partial | `developer_preview` | Not wired to resolver/result index contract |
| Survival result | No | No | `not_implemented` | KM/Cox/log-rank absent |
| Plot artifact | Config defaults only | No | Inherit source result semantics | Plot artifact schema missing |
| Markdown report draft | Yes | Partial | `draft` | Not report-ready export package |

Minimum result index fields recommended:

- `result_id`
- `task_type`
- `result_semantics`
- `input_package_id`
- `source_dataset_id`
- `source_repository_manifest`
- `parameters_manifest`
- `engine_name`
- `engine_version`
- `dependency_snapshot`
- `output_artifacts`
- `plot_artifacts`
- `report_artifacts`
- `validation_status`
- `warnings`
- `blockers`
- `created_at`

Additional recommended fields:

- `source_task_run_id`
- `source_task_run_manifest`
- `input_checksums`
- `output_checksums`
- `logs`
- `failure_reason`
- `migration_status`
- `schema_version`

## Plotting System Audit

Current state:

- `config/bioinformatics/plotting_defaults.yaml` contains defaults for volcano, expression, correlation, enrichment, and survival plots.
- Task templates include `volcano_plot`, `heatmap`, and plot-like downstream tasks.
- Result browser can preview imported DEG rows, but it does not generate formal plot artifacts.
- Report builder explicitly says it does not create fake DEG tables, volcano plots, or enrichment results.

Audit conclusion: do not develop scattered plotting buttons now. Plotting should be a result-system stage after result schemas are stable.

Required plot bindings:

- Volcano plot -> formal/imported DEG result.
- Heatmap -> DEG result or expression subset package.
- ORA plot -> enrichment result.
- GSEA plot -> GSEA result.
- Correlation plot -> correlation result.
- KM plot -> survival result.

Rules:

- Plot generation must read result artifacts, not recognition reports, raw expression matrices, or runner temp files.
- If source result is `exploratory` or `testing_level`, the plot must inherit the same warning.
- Plot artifacts need schema fields: `plot_id`, `source_result_id`, `plot_type`, `parameters`, `artifact_path`, `format`, `created_at`, `warnings`, and `validation_status`.

## Report-Ready System Audit

Current report system:

- `reports/project_report_builder.py` generates `reports/project_report_draft.md`, `reports/project_analysis_report.md`, and `reports/project_report_manifest.json`.
- It links recognition, standardized assets, asset selection, group design, imported DEG results, and analysis task runs.
- It explicitly describes dry-run task records as not real DEG completion.
- UI has DOCX/HTML export placeholder buttons and says PDF is not formally supported.

Audit conclusion: current Markdown is a report draft, not report-ready scientific or clinical output.

Report-ready minimum conditions:

- All report results come from result index.
- `result_semantics` is not `testing_level` unless the report is explicitly labeled as a test report.
- Input package has provenance.
- Parameters and dependency versions are traceable.
- Plots come from plot artifacts, not temporary preview tables.
- `validation_status` has no blockers.
- Warnings are displayed and persisted.
- No clinical diagnosis or medical advice is produced.

Recommended export package structure:

- `report.md`
- `tables/`
- `plots/`
- `provenance/`
- `parameters/`
- `logs/`
- `result_index.json`
- `report_manifest.json`
- `limitations.md`

## Dependency and Settings Integration Audit

Current `pyproject.toml` runtime dependency is only `PySide6`. Settings currently checks Python, PySide6, R path, storage root, and GEO legacy environment, but not analysis package availability.

The future Settings path should be:

`Settings -> 外部引擎、模型与分析资源 -> 分析资源与工具`

Rules:

- Detect-first; do not auto-install.
- Missing dependencies must be shown before execution, not hidden in stack traces.
- R backend must be optional and explicit if adopted later.

### Dependency Detection Matrix

| Dependency / resource | Purpose | Current detection | Recommended detection | Action planning |
| --- | --- | --- | --- | --- |
| pandas | Table IO and data frame operations | Not declared | Python import + version + path | Install/update/remove plan only |
| numpy | Numeric matrix operations | Not declared | Python import + version + path | Detect before analysis |
| scipy | Welch t-test, statistics helpers | Optional import in runners | Python import + version + test t-test | Required for Python DEG MVP if chosen |
| statsmodels | Multiple testing, regression helpers | Not declared | Python import + version + BH test action | Required for formal Python DEG/correlation |
| matplotlib | Plot output | Not declared | Python import + backend test | Required for Python plotting |
| lifelines | KM/Cox/log-rank if Python path | Not declared | Python import + version + sample survival fit | Optional survival backend |
| R | External backend | `shutil.which("R")` only | executable path + `R --version` + package probe | Optional backend |
| limma | log-expression DEG | Config reference only | `Rscript -e packageVersion("limma")` | Optional R DEG backend |
| DESeq2 | count DEG | Config reference only | `Rscript -e packageVersion("DESeq2")` | Optional R DEG backend |
| edgeR | count DEG | Config reference only | `Rscript -e packageVersion("edgeR")` | Optional R DEG backend |
| clusterProfiler | GO/KEGG/GSEA and ID mapping | Config reference only | R package version probe | Optional enrichment/GSEA backend |
| fgsea | GSEA alternative | Not declared | R package version probe | Optional GSEA backend |
| enrichplot | Enrichment/GSEA plots | Config reference only | R package version probe | Optional plot backend |
| GO / KEGG / Reactome resources | Gene set/reference resources | Config only | Local resource registry with license/source/version | Manual resource management |
| MSigDB manual resource | GMT gene sets | GMT upload path only | File registry + checksum + license note | User-provided only |
| plotting packages | ggplot2/survminer/seaborn etc. | Config/docs only | Backend-specific probes | Optional; tied to plot schema |

## Real-Format Fixture and Validation Coverage

### Real-Format Validation Coverage Matrix

| Format | Test fixture exists? | Real sample validation? | Enters standardized repository? | Generates analysis input package? | Formal analysis usable now? | Current blocker |
| --- | --- | --- | --- | --- | --- | --- |
| GEO Series Matrix | Yes, synthetic tests; prior real audits | Some controlled real audit evidence in docs | Yes as recognition/standardization candidate | Partial | No | Needs controlled cross-format standardization proof and probe mapping |
| GEO family SOFT | Yes, synthetic tests | Some real metadata audits | Metadata/expression hints only | Partial | No | Often metadata-only; platform/probe mapping needed |
| GEO supplementary expression matrix | Download planning tests exist | Gap remains for broad controlled validation | Can be recognized/standardized if local file acquired | Partial | No | Selection, size, decompression, and real-format fixture gaps |
| GEO platform annotation / GPL | Platform hints exist in legacy/current scanners | Partial | Not yet final mapping package | No | No | Probe-to-gene mapping contract missing |
| Local CSV/TSV expression | Yes | Synthetic/local | Yes | Partial | No | Resolver and formal task-run contract missing |
| Local XLSX expression | Yes, custom fixture writer; openpyxl dependency boundary exists | Synthetic/local | Yes | Partial | No | XLSX layout/dependency variability |
| Imported DEG table | Yes | Synthetic/local | Yes as `deg_result_table` | Review/reuse partial | Only as imported external review | Imported schema/provenance needs hardening |
| TCGA STAR counts | Yes via TCGA tests | Stronger than GEO per B8 | Yes via TCGA prepared assets | Partial | No | Formal B6 continuation and DEG backend missing |
| TCGA clinical metadata | Yes | Stronger than GEO per B8 | Yes/partial | Survival/clinical preflight partial | No | Association/survival design and backend missing |
| GTEx expression matrix | Tests/source adapter evidence | Stronger than GEO per B8 | Yes via GTEx prepared assets | Partial | No | Must not auto-merge with TCGA; batch correction absent |
| GMT gene set | Tests/config path implied | User-provided only | Resource asset not yet standardized | Partial for ORA runner | Developer preview only | Gene set registry/license/version missing |
| Clinical/survival table | TCGA clinical tests; generic survival preflight service | Partial | Partial | Preflight only | No | KM/Cox/log-rank backend and censoring policy missing |

## Legacy / Integration / ReleaseBuild Reuse Boundary

### Legacy Reuse Boundary Matrix

| Source | Reusable concepts | Reusable code? | Must rewrite/adapt | Must not expose in current UI | Schema incompatibility |
| --- | --- | --- | --- | --- | --- |
| `../Integration/app/bioinformatics/standardized_asset_selection.py` | Default asset selection, multi-candidate blocking | Yes, already similar/current | Adapt names to current repository schema and resolver API | Do not bypass current standardization | Old/current asset naming can diverge |
| `../Integration/app/bioinformatics/analysis_task_runs.py` | Task-run manifest directory, status model, atomic writes | Yes, current UIShell already has equivalent | Add formal completed-output guard and dependency snapshot | Do not mark dry-run completed | Run outputs schema incomplete |
| `../Integration/app/bioinformatics/deg_executor_preflight.py` | Preflight manifest and task-run link | Partial; current version is stronger | Resolver-backed input package, checksums, dependency preflight | Do not imply DEG execution | Older version saved references more than materialized inputs |
| `app/bioinformatics/legacy/geo_processing/*` | Download validation, RAW suppression, matrix/metadata/platform scoring | Selectively as reference | Re-wrap behind current recognition contracts | Do not expose legacy sandbox as production | Legacy payload shapes differ |
| `app/bioinformatics/legacy/geo_pipeline/process.py` | SOFT processing, phenotype extraction, GPL annotation, aggregation ideas | Reference only | Reimplement through standardized repository and mapping reports | Do not auto-run GEOparse pipeline in current UI | Pandas/numpy/GEOparse assumptions |
| `../ReleaseBuild/archive/legacy_sources/model9/analysis/*` | DEG-ready matrix, comparison readiness, preflight, reporting/profile ideas | Reference only | Port concepts, not files | Do not revive old preview cards as formal UI | Model9 profile/store schemas differ |
| `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/*` | Series Matrix/SOFT/GPL real-readiness parser ideas | Reference only | Adapt to current recognizer and tests | Do not treat old readiness as current runtime proof | Legacy readiness schemas differ |
| `../ReleaseBuild/archive/legacy_sources/model9/reporting/*` | Report provenance/profile readiness patterns | Reference only | Rebuild report-ready gate over current result index | Do not use as clinical/scientific final report | Reporting models differ |

## i18n and UI Copy Readiness

Current UI copy is mostly hard-coded Chinese. Future Bioinformatics UI rebuild should introduce status and action i18n keys before expanding the analysis center.

Recommended semantic keys:

- `analysis.status.available`
- `analysis.status.config_only`
- `analysis.status.preflight_only`
- `analysis.status.exploratory`
- `analysis.status.developer_preview`
- `analysis.status.blocked_missing_resolver`
- `analysis.status.blocked_missing_backend`
- `analysis.status.blocked_missing_result_schema`
- `analysis.status.not_implemented`
- `analysis.status.hidden_until_ready`
- `result.semantic.preflight_only`
- `result.semantic.testing_level`
- `result.semantic.exploratory`
- `result.semantic.formal_computed_result`
- `result.semantic.imported_external_result`

Translation rule: do not translate `exploratory`, `preflight`, or `testing-level` into phrases that imply "analysis complete". Use explicit Chinese such as `探索性结果`, `仅预检查`, `测试级`, and pair each with a blocker/next action.

## Risk Register

| Risk | Severity | Evidence | Impact | Recommended mitigation |
| --- | --- | --- | --- | --- |
| `can_run` reads as formal run readiness | High | Task center uses `can_run` for mixed states | Users may believe formal DEG/GSEA/survival is available | Rename UI state to `available_action` plus semantic state |
| Primary `运行 GEO 差异分析` button | High | Workflow page exposes preview runner button | Bypasses B8 resolver-first recommendation | Gate as developer preview or remove until B8.1/B8.3 |
| Imported DEG mistaken for recomputed DEG | High | Imported preview and DEG task center colocated | Misleading provenance | Label `imported_external_result` everywhere |
| Plot tasks shown before plot schema | Medium | Volcano/heatmap task templates and plotting defaults exist | Fake-formal plot risk | Hide/disable formal plot buttons until B8.5 |
| Report draft mistaken for report-ready output | Medium | Report viewer writes `project_analysis_report.md` | Overclaiming scientific/clinical output | Add report-ready gate and explicit draft label |
| Dependency failures surface late | Medium | Only PySide6 declared; scipy optional imports | Users hit runtime errors after clicking | Settings dependency registry and preflight |
| TCGA+GTEx normal control misuse | High | Task template exists for joint analysis | Invalid biological/statistical interpretation | Keep fixed warning and block formal joint DEG |
| Probe/ID_REF unmapped formal DEG | High | GEO Series Matrix/family SOFT can expose probes | Invalid gene-level results | Require mapping report before formal DEG |
| Old result/index schema drift | Medium | Legacy/integration assets have divergent schemas | Result browser/report may mix incompatible artifacts | Add migration/regenerate/reindex mechanism |
| Survival overexposure | High | Survival task is visible; only preflight exists | Users expect KM/Cox/log-rank | Preflight-only label and disabled formal buttons |

## Recommended Follow-up Milestones

### B8.1 Standardized analysis input resolver and task-run contract

Goal: establish the unified entry for every downstream analysis. Resolver must consume standardized repository artifacts only and produce task-ready input packages, blockers, warnings, semantics, and provenance.

### B8.2 DEG-ready matrix and formal DEG preflight

Goal: create DEG-ready matrix, sample alignment, gene ID/mapping report, and parameter manifest. Formal DEG remains disabled if probe/ID_REF is unmapped, multi-candidate matrix selection is unresolved, or value type is TPM/FPKM for count models.

### B8.3 Controlled DEG MVP backend decision

Goal: choose Python-first `scipy`/`statsmodels` or explicit optional R backend, then define the formal DEG result schema. No fake p-values or significance claims without adjusted p-values.

### B8.4 Result index and result browser foundation

Goal: all results register through result index with semantic labels, parameters, inputs, dependencies, logs, warnings, blockers, and artifact references. Add migration/reindex handling for old results.

### B8.5 Plot artifact schema and basic plots

Goal: generate volcano, heatmap, enrichment, correlation, and later KM plots only from result artifacts. Plots inherit result semantics and warnings.

### B8.6 Report-ready gate and export package

Goal: define report-ready conditions, export package layout, limitations text, provenance capture, and validation status gate.

### B8.7 Survival and clinical association design audit

Goal: complete KM/Cox/log-rank and clinical association design/dependency audit before executor implementation. Survival remains preflight-only until censoring policy, backend, and schema are validated.

## Immediate Next Recommendation

Start with B8.1 and make it UI-visible before adding formal analysis buttons:

1. Add an `analysis_input_resolver` layer over standardized repository artifacts.
2. Replace broad `can_run` UI language with semantic status and explicit next action.
3. Disable or demote `运行 GEO 差异分析` to a clearly labeled developer preview until the resolver/result schema path exists.
4. Define minimal result index fields and result semantics before plot/report work.
5. Add Settings dependency registry detection for analysis resources and optional backends.

Validation note for this supplemental audit: this task only added documentation. Full Bioinformatics/UI test suites were not required by the task brief because no runtime code, tests, or UI implementation files were modified. Verification completed on 2026-05-20:

- `git diff --check` passed.
- `python3 -m app.main --smoke-test` passed; the smoke output reported `git_head=4f644bf`, `bioinformatics_features=5`, `meta_analysis_features=9`, and `pyside6_available=True`.
