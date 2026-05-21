# Bioinformatics B8.0.1: Analysis UI Prebuild and Result-System Supplemental Audit

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Audited HEAD: `f543904 docs(bio): audit analysis readiness and standardization`

## Executive Summary

Bioinformatics can proceed to analysis UI redesign only if the UI is explicitly framed around readiness, preflight, blockers, result semantics, and provenance. The current runtime has useful preparation surfaces, but no formal product path for DEG recompute, GSEA, survival statistics, formal plotting, or report-ready export.

The safest next step is still B8.1: build a standardized analysis input resolver and task-run contract. Until that exists, the Analysis Center should not present "Run DEG", "Run GSEA", "Run Survival", "Generate volcano", or "Export report-ready package" as enabled primary actions.

Current UI already contains several good boundary protections: DEG configuration is labeled as preflight only, imported DEG is shown as external/imported, result browser distinguishes imported/testing/dry-run semantics, and B7 immune/TME scoring is labeled exploratory. The main remaining UI risk is that some top-level actions still look runnable before a resolver/result-schema gate exists, especially "进入差异分析配置", "免疫浸润 / TME评分", and the developer-only "生成测试级 GEO 差异结果".

## Scope and Source Documents

Required source document reviewed:

- `docs/bioinformatics/stage_B8_analysis_readiness_and_standardization_audit_20260520.md`

Runtime files reviewed:

- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/project_readiness.py`
- `app/bioinformatics/project_standardization.py`
- `app/bioinformatics/project_analysis_tasks.py`
- `app/bioinformatics/deg_task_plan.py`
- `app/bioinformatics/results/project_results.py`
- `app/bioinformatics/reports/project_report_builder.py`
- `app/bioinformatics/immune_infiltration/*`
- `app/bioinformatics/services/enrichment_runner.py`
- `app/bioinformatics/services/correlation_runner.py`
- `app/bioinformatics/services/survival_service.py`
- `config/bioinformatics/package_requirements.yaml`
- `config/bioinformatics/plotting_defaults.yaml`
- `config/bioinformatics/enrichment_defaults.yaml`
- `config/bioinformatics/survival_defaults.yaml`

Legacy / adjacent assets reviewed:

- `../Integration/app/bioinformatics/standardized_asset_selection.py`
- `../Integration/app/bioinformatics/analysis_task_runs.py`
- `../Integration/app/bioinformatics/deg_executor_preflight.py`
- `app/bioinformatics/legacy/geo_processing/*`
- `app/bioinformatics/legacy/geo_pipeline/process.py`
- `../ReleaseBuild/archive/legacy_sources/model9/analysis/*`
- `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/*`
- `../ReleaseBuild/archive/legacy_sources/model9/local_data/standardizer.py`

This is a documentation-only audit. It does not implement analysis engines, UI rewrites, dependency installation, plotting, or report export.

Validation note for this audit: because this task only adds a documentation report and does not modify Bioinformatics runtime, UI, or test code, full `tests/bioinformatics` and `tests/ui` suites were not run. Required checks run for this report were `git diff --check` and `python3 -m app.main --smoke-test`.

## What B8 Covered Well

B8 correctly establishes that current standardization is an asset-organizing and lightweight validation engine, not a biological normalization, probe mapping, batch correction, or formal statistical design engine.

B8 also correctly blocks direct wiring from recognition outputs to downstream runners. Existing runners are reusable only after a standardized repository artifact has been resolved into a stable analysis input package.

B8's strongest product guidance is still valid: B8.1 must build the analysis input resolver and task-run contract before formal DEG/GSEA/survival/plot/report UI is opened.

## Gaps Not Covered by B8

B8 did not fully translate capability boundaries into UI states, button enablement rules, result schema rules, or report-ready gates.

The current Analysis Task Center uses readiness rows and task templates to show "can_run" and "可配置", but these states are not equivalent to formal execution readiness. They should be renamed or mapped to `config_only`, `preflight_only`, or `exploratory` until the resolver/task-run layer exists.

The current result index is useful but minimal. It can distinguish some semantics, but it does not yet require a stable input package id, dependency snapshot, parameters manifest, validation status, logs, failure reason, plot artifacts, or report artifacts for every result.

Settings does not yet provide a detect-first analysis dependency registry. It has Python path, package manifest placeholder, GEO legacy environment check, default project settings placeholders, and local AI settings, but not a formal "analysis resources and tools" panel.

## Current Runtime Capability Map

Current positive controls:

- Data readiness and capability matrix are generated by `project_readiness.py`.
- Standardized repositories and analysis input package JSON files are generated by `project_standardization.py`.
- DEG preflight exists in `deg_task_plan.py` and writes a manifest explicitly marked `input_preflight_only_not_deg_result`.
- Imported DEG browser clearly states imported DEG is not BioMedPilot recomputation.
- Result browser distinguishes imported result, testing-level, dry-run, configured-not-run, and real computed result labels.
- B7 immune/TME scoring writes artifacts and registers a testing-level exploratory score.

Current hard boundaries:

- No formal DEG engine is productized.
- No GSEA executor is implemented.
- No KM/Cox/log-rank engine is implemented.
- No formal clinical association statistics are implemented.
- No plot artifact schema exists.
- No report-ready export package exists.
- No scipy/statsmodels/R/Bioconductor/lifelines detection registry exists.

## Analysis UI Status Matrix

### Analysis Capability Matrix

| Analysis type | Current implementation status | UI main entry? | Recommended UI label | Recommended button state | Required prerequisites | Required blocker / warning | Follow-up phase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEG recompute | DEG config/preflight exists; testing GEO runner exists; no formal task-run path | Config only, not formal run | `需要标准化输入解析器` | Show configure/preflight; disable formal run | resolver, selected expression, sample metadata, group design, value type, gene mapping, backend | Preflight is not DEG result; imported DEG is not recompute; TPM/FPKM not count-model input | B8.1, B8.2, B8.3 |
| Imported DEG review / imported result reuse | Implemented browser and result candidate marking | Yes, as result review | `已可用：导入结果浏览` | Enable review; disable recompute claims | imported DEG table, column mapping, source label | Must display imported/external result warning | B8.4 |
| ORA enrichment | Local runner exists; no product task-run UI | Developer preview only | `需要结果结构` | Disable primary run | formal/imported DEG result, selected GMT, result schema | Do not run from raw expression; require DEG semantics | B8.4, B8.5 |
| GSEA preranked | Gene set resource manager/readiness exists; executor absent | Preflight only | `暂未实现` / `仅预检查` | Show resource/preflight; disable run | ranked gene list policy, GMT, backend, result schema | No real GSEA execution; MSigDB cannot be bundled/downloaded silently | B8.5 |
| Correlation analysis | Pearson runner exists; needs resolver/UI parameterization | Developer preview only | `开发者预览` | Disable formal run; allow later preflight | normalized expression package, target gene, sample threshold | Reads expression directly today; should consume package | B8.1, B8.4 |
| Immune / TME score linkage | B7 exploratory bulk signature scoring implemented | Yes, but exploratory | `探索性结果` | Enable only with TPM/normalized input; downstream disabled | expression matrix, value type policy, signature coverage | Not deconvolution; not CIBERSORT/xCell/ESTIMATE; not clinical conclusion | B8.4 |
| TCGA clinical association | Clinical build/readiness exists; statistics absent | Preflight only | `仅预检查` | Disable run | clinical package, case/sample mapping, variable policy, backend | No formal association statistics | B8.7 |
| Survival analysis | Basic OS readiness/preflight only | Preflight only | `仅预检查` | Enable preflight; disable KM/Cox/log-rank | survival table, expression grouping policy, event thresholds, backend | KM/Cox/log-rank not implemented; low event counts block formal run | B8.7 |
| Volcano plot | Old/descriptive/testing tables may be volcano-shaped; no plot artifact schema | Hidden until result ready | `需要结果结构` | Disable | formal/imported DEG result, plot schema | Do not plot from preflight or descriptive-only table as formal volcano | B8.5 |
| Heatmap | Config defaults and expression packages exist; no plot artifact schema | Hidden until ready | `需要结果结构` | Disable | DEG result or expression subset package, plot schema | Must inherit source result semantics | B8.5 |
| Enrichment plot | Config defaults exist; no plot artifact schema | Hidden until ready | `需要结果结构` | Disable | enrichment result artifact | No result artifact, no plot | B8.5 |
| Correlation plot | Config defaults exist; no plot artifact schema | Hidden until ready | `需要结果结构` | Disable | correlation result artifact | Do not read runner temp output directly | B8.5 |
| KM plot | Defaults exist; no survival engine/result | Hidden until ready | `暂未实现` | Disable | survival result artifact | No KM/log-rank result exists | B8.7 |
| Markdown report draft | Implemented project draft and immune draft | Yes, draft only | `报告草稿` | Enable draft generation only | result index entries or project state | Not report-ready; no Word/PDF/export package | B8.6 |
| Report-ready export | Not implemented | No | `暂不显示` | Hide/disable | stable result schema, provenance, validation, plots, logs | No clinical advice; wait for report-ready gate | B8.6 |

## Recommended Analysis Center Structure

Recommended first-screen order:

1. Current project / dataset summary.
2. Standardized asset status.
3. Analysis input package status.
4. Available analysis type matrix.
5. Blockers and repair actions.
6. Task configuration entry.
7. Preflight results.
8. Formal run entry only when all gates pass.
9. Result index entry.
10. Report and plot entry only after stable result artifacts exist.

Current code partially matches this shape but is split across data check, standardized assets, analysis task center, result browser, imported DEG browser, immune scoring, and report viewer. The missing bridge is one Analysis Center state object that joins standardized repository state, package resolver state, task-run state, result index state, dependency state, and UI button rules.

Recommended UI status vocabulary:

- `available`: only for browsing/reviewing current stable artifacts.
- `config_only`: task configuration can be saved; no execution.
- `preflight_only`: input checks can run; no formal result.
- `exploratory`: B7 immune/TME scores and similar internal exploratory outputs.
- `developer_preview`: internal runner output, hidden behind developer diagnostics.
- `blocked_missing_resolver`: formal analysis blocked until B8.1.
- `blocked_missing_backend`: formal statistics blocked until dependency/backend decision.
- `blocked_missing_result_schema`: plotting/report-ready blocked until result schema exists.
- `hidden_until_ready`: do not render button in normal user flow.

## Button Enablement and Blocking Rules

### UI Button State Matrix

| Button | Should display? | Should enable now? | Enable condition | Disabled reason now | User next action |
| --- | --- | --- | --- | --- | --- |
| Enter DEG configuration | Yes | Yes, as config/preflight only | Project exists and standardized assets/readiness are inspectable | Not a formal run | Confirm expression, metadata, group design |
| Run DEG preflight | Yes | Yes when config inputs exist | selected expression, sample metadata or group assignments, group design | Missing group/matrix/value type/gene mapping blocks | Fix blockers in standardization/preflight |
| Run formal DEG | No normal UI | No | B8.1 resolver + B8.2 DEG-ready matrix + B8.3 backend/result schema | Missing resolver/backend/result schema | Build B8.1-B8.3 |
| Run ORA | Later | No | formal/imported DEG result, GMT, ORA result schema, task run | Missing result schema and trusted DEG input | Define result index and ORA task contract |
| Run GSEA preflight | Later | No or resource-only | ranked gene list package, selected GMT, rank policy | Missing ranked input resolver | Select GMT; wait for GSEA preflight contract |
| Run GSEA | No | No | GSEA preflight passed, backend and result schema ready | Executor not implemented | B8.5 after B8.4 |
| Run correlation | Later | No formal | normalized expression package, target gene, task run | Runner reads direct matrix today | Add resolver-backed task |
| Run immune score linkage | Yes | Exploratory only | TPM/normalized expression, signature coverage, value policy passes | Not deconvolution; raw/unknown blocked | Use B7 as exploratory score only |
| Run clinical association | Later | No | clinical package, variable schema, backend | Statistics absent | B8.7 design audit |
| Run survival preflight | Yes/later | Yes as preflight only | survival table, expression/case mapping, event threshold check | No survival execution | Inspect OS fields and missingness |
| Run KM / Cox / log-rank | No | No | survival result contract, lifelines/R backend, validation | Engine absent | B8.7 backend decision |
| Generate volcano plot | Hidden until result | No | formal/imported DEG result, plot schema | No plot artifact schema; preflight is not DEG | B8.5 |
| Generate heatmap | Hidden until result | No | DEG result or expression subset package, plot schema | No plot artifact schema | B8.5 |
| Generate KM plot | Hidden until result | No | survival result artifact | No survival result | B8.7 then B8.5 |
| Generate Markdown draft | Yes | Yes, draft only | Project state/result entries exist | Not report-ready | Generate draft and preserve semantics |
| Mark report-ready | Later | No | all result entries validated, non-testing semantics or explicit test report mode | Missing result schema/provenance/validation | B8.6 |
| Export report package | Later | No | report-ready gate, artifact package schema, logs, plots, provenance | Export package absent | B8.6 |

Mandatory rule translation:

- Without resolver, no formal analysis button is enabled.
- Multiple candidate matrices block formal analysis until a default asset is explicitly selected.
- GEO probe / ID_REF blocks formal DEG until platform mapping is confirmed.
- TPM / FPKM must not enter count-model DEG.
- GTEx must not automatically become TCGA normal control.
- Survival can show preflight only; KM/Cox/log-rank stay disabled.
- Report-ready requires stable result schema, provenance, validation status, plots, and warnings.

## Result Index and Task-Run Audit

Current result browser exists and reads `results/summaries/result_index.json` plus `manifests/result_manager.json`. Current `write_result_index()` writes only `schema_version` and result entries, while result manager records only result count. This is enough for a draft browser but not enough for formal analysis governance.

Current result semantics are useful but heuristic. `_analysis_entry_semantics()` infers semantics from strings and defaults unknown entries to testing-level. That is conservative for display, but formal task runs should require explicit `result_semantics`.

Current task-run gaps:

- `project_analysis_tasks.py` creates task records with `execution=not_run`.
- Integration has a richer task-run manifest idea, but it uses older asset naming such as `count_matrix` and cannot be copied directly into current `raw_count_matrix` / repository schema.
- Current immune scoring registers a result, but result index entries do not include input package id, dependency snapshot, parameters manifest, logs, failure reason, or validation status.

### Result Artifact / Schema Gap Matrix

| Result artifact | Current state | Stable schema? | Semantics supported? | Main gap | Required next step |
| --- | --- | --- | --- | --- | --- |
| DEG preflight manifest | Exists | Partial | `preflight_only` via boundary text | Not registered as formal result | Keep outside result table or register as preflight artifact |
| Testing GEO DEG CSV | Exists via developer action | Partial | `testing-level` | Developer-only runner, no resolver/task contract | Hide from normal UI; use only test fixture |
| Imported DEG table | Exists | Partial | `imported_external_result` | Needs column mapping provenance and source metadata | B8.4 result schema |
| ORA result | Runner exists | Partial runner summary | Not consistently indexed | No task-run/UI contract | B8.4/B8.5 |
| GSEA result | Absent | No | No | Executor absent | B8.5 |
| Correlation result | Runner exists | Partial runner summary | Not consistently indexed | Direct matrix input, no package id | B8.4 |
| Immune score result | Exists | Partial manifest | `exploratory`/testing-level | Missing dependency snapshot/input package id | B8.4 |
| Clinical association result | Absent | No | No | Statistics absent | B8.7 |
| Survival result | Absent | No | Preflight only | KM/Cox/log-rank absent | B8.7 |
| Plot artifact | Absent | No | Must inherit result semantics | No plot schema | B8.5 |
| Markdown draft | Exists | Draft manifest | Draft only | Not report-ready, no package export | B8.6 |
| Report-ready export | Absent | No | No | Gate absent | B8.6 |

Minimum result index fields:

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

Recommended additional fields:

- `task_run_id`
- `log_artifacts`
- `failure_reason`
- `user_visible_label_i18n_key`
- `method_summary_i18n_key`
- `report_ready_eligible`
- `migration_status`

## Plotting System Audit

Current plotting state:

- `config/bioinformatics/plotting_defaults.yaml` contains defaults for volcano, expression plot, correlation plot, enrichment plot, and survival plot.
- The current runtime does not expose formal plot generation.
- Result browser and report draft can display artifact metadata, but there is no plot artifact schema.
- Legacy/model9 code can produce volcano-ready descriptive tables, but those explicitly lack p-value/FDR and must not be treated as formal volcano plots.

Recommended rule: do not build scattered plot buttons now. First define plot artifact schema and bind each plot to a result artifact:

- Volcano plot -> formal/imported DEG result.
- Heatmap -> DEG result or expression subset package.
- ORA plot -> enrichment result.
- GSEA plot -> GSEA result.
- Correlation plot -> correlation result.
- KM plot -> survival result.

If a source result is `testing_level`, `exploratory`, or `imported_external_result`, the generated plot must inherit that warning. A testing-level score cannot become a formal plot by being rendered nicely.

## Report-Ready System Audit

Current project report draft exists and explicitly says it is not formal, clinical, publication-ready, or submission-ready. It includes project metadata, recognition, standardization, task status, preflight, imported DEG, result semantics, warnings, and next steps.

Current limitations:

- Markdown draft only; PDF/DOCX export is not supported in this runtime.
- Draft generation can include imported/testing-level entries as draft content, but it does not enforce report-ready eligibility.
- It does not yet require a stable result schema, dependency snapshot, validation status, logs, plot artifacts, or complete provenance for every included result.

Report-ready minimum conditions:

- All result claims come from result index entries.
- `result_semantics` is not testing-level unless the report is explicitly labeled as a test report.
- Input package provenance is present.
- Parameters and dependency versions are captured.
- Plots come from plot artifacts, not temporary previews.
- `validation_status` has no blocker.
- Warnings are displayed and recorded.
- No clinical diagnosis or medical advice is generated.

Recommended export package:

- Markdown report.
- Tables.
- Plot artifacts.
- Result index snapshot.
- Input package manifests.
- Parameters manifests.
- Dependency snapshot.
- Logs.
- Validation report.
- Limitations and warnings.

## Dependency and Settings Integration Audit

Current dependency state:

- `pyproject.toml` declares only `PySide6` as runtime dependency and `pytest` for dev.
- `config/bioinformatics/package_requirements.yaml` documents many R/Bioconductor packages, but there is no installed-status registry.
- Settings currently shows Python path, project-local venv placeholder, package manifest placeholder, GEO legacy environment check, default settings placeholders, and local AI settings.

Recommended Settings path:

`Settings -> 外部引擎、模型与分析资源 -> 分析资源与工具`

Rules:

- detect-first, never auto-install.
- Missing dependencies must surface as blockers/warnings, not Python tracebacks.
- R backend must be optional and explicit.
- Every dependency record should include purpose, module usage, installed status, version, local path, test action, and planned install/update/remove action.

### Dependency Detection Matrix

| Dependency / resource | Purpose | Module usage | Current declared/runtime status | Required detection | UI action planning |
| --- | --- | --- | --- | --- | --- |
| scipy | t-test/statistics | DEG/correlation future | Not declared runtime | import/version check | Test, install guide |
| statsmodels | FDR/multiple testing | DEG MVP | Not declared runtime | import/version check | Test, install guide |
| pandas | table handling | future analysis/report | Not declared runtime | import/version check | Test, install guide |
| numpy | numeric backend | future analysis | Not declared runtime | import/version check | Test, install guide |
| matplotlib | Python plots | plot artifacts | Not declared runtime | import/version/backend check | Test rendering |
| lifelines | KM/Cox/log-rank | survival | Not declared runtime | import/version check | Optional install guide |
| R | optional external backend | limma/DESeq2/edgeR/GSEA/survival | Not runtime dependency | `R --version`, path, library paths | Configure/test only |
| limma | log-scale DEG | optional R backend | Not detected | R package check | Optional install guide |
| DESeq2 | count DEG | optional R backend | Not detected | R package check | Optional install guide |
| edgeR | count DEG | optional R backend | Not detected | R package check | Optional install guide |
| clusterProfiler | ORA/GSEA | optional R backend | Listed in defaults | R package check | Optional install guide |
| fgsea | GSEA | optional R/backend | Not detected | R package check | Optional install guide |
| enrichplot | enrichment plots | optional R plots | Listed in package requirements | R package check | Optional install guide |
| GO resources | enrichment resource | ORA/GSEA | Not bundled | registry/cache status | Download/config later |
| KEGG resources | enrichment resource | ORA/GSEA | Not bundled | license/API/cache status | Configure only |
| Reactome resources | enrichment resource | ORA/GSEA | Not bundled | registry/cache status | Download/config later |
| MSigDB manual resource | GSEA | GMT manager | Local GMT import exists | selected GMT/validity/license warning | Import manual GMT |
| plotting packages | figure rendering | B8.5 | Defaults only | backend-specific checks | Test plot rendering |

## Real-Format Fixture and Validation Coverage

B8 correctly states TCGA/GTEx live validation is stronger than GEO controlled live validation. Current tests use many small synthetic fixtures created inside tests, but there is no dedicated `tests/fixtures/bioinformatics` corpus with real-format samples.

### Real-Format Validation Coverage Matrix

| Format | Test fixture exists? | Real sample validation? | Enters standardized repository? | Can generate analysis input package? | Formal analysis usable now? | Current blocker |
| --- | --- | --- | --- | --- | --- | --- |
| GEO Series Matrix | Synthetic test coverage | Limited historical/legacy; needs controlled current proof | Yes when recognized/selected | Potentially DEG/correlation package | No | ID_REF mapping, group confirmation, resolver |
| GEO family SOFT | Parser/recognition coverage | Limited legacy proof | Partial via recognition/standardization | Not consistently | No | deeper SOFT extraction and platform mapping |
| GEO supplementary expression matrix | Discovery/detection coverage | Needs comparable controlled validation | Yes if downloaded/recognized | Potentially | No | candidate selection, value type, mapping |
| GEO platform annotation / GPL | Candidate/mapping hints | Legacy model9 has useful parsers | Feature annotation asset possible | Blocks/permits DEG depending mapping | No | mapping quality not productized |
| Local CSV/TSV expression | Synthetic tests | No broad real corpus | Yes | Potentially | No | value type, sample/group alignment, resolver |
| Local XLSX expression | Import tests exist | No broad real corpus | Recognition/import level | Potentially after conversion | No | workbook/sheet mapping and standard package |
| Imported DEG table | Synthetic tests | No broad real corpus | Imported result repository | Enrichment/review package possible | Review only | source/provenance/column mapping schema |
| TCGA STAR counts | Unit plus lightweight live validation | Yes, limited TCGA validation | Yes via B6.4/B6.5 | DEG preflight candidate | No | limited validation, resolver/backend/result schema |
| TCGA clinical metadata | Unit plus lightweight live validation | Yes, limited TCGA validation | Yes clinical repository | Survival preflight package possible | No | event thresholds, survival engine absent |
| GTEx expression matrix | Unit plus lightweight API slice | Yes, limited GTEx validation | Yes | Correlation/heatmap/B7 package possible | No | not TCGA normal control, limited validation |
| GMT gene set | Gene set resource tests | Local import validation only | Resource registry, not ordinary data input | GSEA/ORA resource package later | No | executor/result schema/license |
| Clinical/survival table | Synthetic and TCGA clinical tests | TCGA limited validation | Yes for clinical assets | Survival preflight possible | No | KM/Cox/log-rank absent |

## Legacy / Integration / ReleaseBuild Reuse Boundary

### Legacy Reuse Boundary Matrix

| Asset | Reusable concept | Reusable code | Must rewrite/adapt | Must not enter current runtime as-is | Incompatibility / UI rule |
| --- | --- | --- | --- | --- | --- |
| `../Integration/app/bioinformatics/standardized_asset_selection.py` | explicit default asset selection | Some selection-state logic | Asset type names and schema | Direct copy | Uses `count_matrix`/`deg_result_table`; current branch uses `raw_count_matrix`/`differential_result_table` |
| `../Integration/app/bioinformatics/analysis_task_runs.py` | task-run manifest, logs, parameters | Manifest layout ideas | Current package ids, result schema | Direct copy | Old resolver depends on old selection module |
| `../Integration/app/bioinformatics/deg_executor_preflight.py` | executor preflight shape | Warnings/log materialization ideas | Current B8 resolver and package schema | Direct copy | Old `count_matrix` naming and dry-run-only semantics |
| `app/bioinformatics/legacy/geo_processing/*` | file detection, raw/heavy suppression | Specific classifiers may be mined | Contract boundary and current schema | Direct UI exposure | Legacy detector should not become analysis runtime |
| `app/bioinformatics/legacy/geo_pipeline/process.py` | SOFT/GPL parsing, phenotype extraction | Parser ideas | Current repository outputs and mapping reports | Direct overwrite | Must preserve current recognition/standardization boundary |
| `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/*` | real-format readiness reports | Parser/report ideas | Current app package/import paths | Direct import | Historical code, not active runtime |
| `../ReleaseBuild/archive/legacy_sources/model9/analysis/deg_ready_matrix.py` | DEG-ready matrix, probe mapping, collapse report | Logic idea | Current package schema and validation | Direct import | Good B8.2 design reference |
| `../ReleaseBuild/archive/legacy_sources/model9/analysis/deg_summary.py` | descriptive DEG summary and volcano-ready table | Concept only | Formal stats and result semantics | UI formal plot exposure | Lacks p-value/FDR; descriptive only |
| `../ReleaseBuild/archive/legacy_sources/model9/local_data/standardizer.py` | manifest/validation report pattern | Concept only | Current standardized repositories | Direct copy | Older local dataset contract |

## i18n and UI Copy Readiness

Current Bioinformatics UI text is mostly hard-coded Chinese in `workflow_pages.py`, with semantic strings mixed into UI construction and status helpers. This is workable for current internal beta, but not ready for a rebuilt analysis UI.

Recommended policy:

- Define i18n keys for status labels, button labels, blocker messages, warning messages, result semantics, and report-ready gates.
- Keep semantic codes in data (`preflight_only`, `exploratory`, `blocked_missing_backend`) and map them to Chinese/English UI text.
- Do not translate exploratory/preflight/testing into phrases that imply completed formal analysis.
- Prefer "探索性结果", "仅预检查", "测试级结果", "配置草稿" over "已完成分析" unless a formal result schema and validation gate passed.

## Risk Register

### Risk Register

| Risk | Severity | Evidence | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| UI treats `can_run` as formal execution readiness | High | Readiness rows drive "可配置" states | Users may believe analysis is runnable | Map to config/preflight/exploratory; formal buttons stay disabled |
| Existing testing GEO DEG runner is promoted | High | Developer action can write testing-level DEG result | False formal DEG impression | Keep behind developer diagnostics and label testing-level |
| Imported DEG is interpreted as recomputed DEG | High | Imported result appears in result browser/report draft | Misattributed result source | Always show imported/external labels and source provenance |
| B7 immune/TME score interpreted as deconvolution | High | Score matrix and report are generated | Overclaim immune cell fractions | Keep exploratory label and blocked downstream list |
| TCGA + GTEx readiness implies automatic joint DEG | High | Both sources can be recognized | Batch/control misuse | Maintain GTEx not TCGA normal control warning |
| Survival readiness implies KM/Cox/log-rank support | High | Clinical OS preflight can be ready | False survival claims | Preflight-only status until B8.7 |
| Plot UI creates formal-looking figures from weak results | High | Plot defaults exist | Figures may overclaim statistics | Define plot artifact schema after result schema |
| Report draft becomes report-ready by UI polish | High | Markdown draft exists | Clinical/scientific overclaim | Add report-ready gate and export package schema |
| Dependency failures surface as tracebacks | Medium | No dependency detection registry | Poor UX and hidden blockers | Settings detect-first registry |
| Legacy code copied into runtime | Medium | Multiple useful old assets exist | Schema drift/regressions | Adapt concepts only; write current tests |
| Real-format GEO validation remains weak | Medium | TCGA/GTEx stronger than GEO | False generalization | Add controlled GEO validation suite |
| Hard-coded Chinese statuses block future UI rebuild | Medium | UI strings in runtime code | i18n and semantics drift | Create semantic code to i18n mapping |

## Recommended Follow-up Milestones

### B8.1 Standardized analysis input resolver and task-run contract

Goal: establish the single downstream analysis entry point.

Deliver:

- Resolver over repository manifest, standardized assets registry, analysis input repository, and user default selections.
- Package contracts for DEG, imported DEG, enrichment, GSEA, correlation, immune score linkage, clinical/survival preflight.
- Task-run manifest with input package id, parameters, dependency snapshot, logs, status, failure reason, and output registration.

### B8.2 DEG-ready matrix and formal DEG preflight

Goal: establish DEG-ready matrix, sample alignment, gene ID/mapping report, and parameter manifest.

Deliver:

- Count matrix suitability policy.
- TPM/FPKM rejection for count-model DEG.
- GEO probe/ID_REF mapping blocker.
- Multi-candidate matrix selection gate.
- TCGA raw counts route to preflight only until backend/result schema is ready.

### B8.3 Controlled DEG MVP backend decision

Goal: decide Python-first scipy/statsmodels or optional R backend and build formal DEG result schema.

Deliver:

- dependency detection.
- p-value and FDR policy.
- method and engine version capture.
- DEG result schema and validation status.

### B8.4 Result index and result browser foundation

Goal: all results register through one result index with semantic labels, parameters, input package, dependency snapshot, logs, and artifacts.

Deliver:

- mandatory result schema fields.
- result browser filters for preflight/testing/exploratory/formal/imported.
- migration/reindex strategy for old result entries.

### B8.5 Plot artifact schema and basic plots

Goal: generate volcano, heatmap, enrichment, correlation, and later KM plots only from result artifacts.

Deliver:

- plot artifact schema.
- plot provenance.
- inherited result semantics and warnings.
- no plot generation from runner temp files.

### B8.6 Report-ready gate and export package

Goal: define report-ready conditions, export package, limitations, and provenance.

Deliver:

- report-ready eligibility checker.
- Markdown + tables + plots + provenance + logs package.
- no clinical advice policy.

### B8.7 Survival and clinical association design audit

Goal: finish KM/Cox/log-rank and clinical association design plus dependency audit before executors.

Deliver:

- survival input package.
- event/missingness thresholds.
- backend decision for lifelines or optional R.
- clinical association variable policy.

## Immediate Next Recommendation

Start B8.1 before any Analysis UI rebuild. The UI redesign should consume a resolver-produced state object and render all formal analysis buttons as disabled until the resolver, task-run manifest, backend dependency checks, and result schema gates pass.

For the current UI, the immediate safe adjustments are documentation/design rules rather than code changes:

- Treat Analysis Task Center `can_run` as "configurable/preflight" only.
- Keep testing GEO DEG generation in developer diagnostics.
- Keep B7 immune/TME score as exploratory.
- Keep report generation as Markdown draft, not report-ready.
- Add the dependency detection registry requirement to Settings design before formal analysis development.
