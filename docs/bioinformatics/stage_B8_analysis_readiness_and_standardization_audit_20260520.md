# Bioinformatics B8: Analysis Readiness and Standardization Audit

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
Branch: `dev/bioinformatics`
Audited HEAD: `e90c8c582b91909b59c58dd73abc4db2ae0555ab`

This audit reviews the current Bioinformatics runtime after TCGA B6, GTEx G6, and B7 immune / TME scoring. The emphasis is whether standardized data is mature enough to support the next phase of downstream analysis development.

## Executive Conclusion

The module is ready to start the next analysis-development phase, but not by immediately adding formal statistics on top of raw recognition outputs.

The safe next phase should first create a unified analysis input resolver and preflight layer that consumes standardized repository artifacts only. After that, downstream analysis can be implemented in a staged order:

1. Expression matrix validation and standardized package resolver.
2. DEG-ready matrix and task-run infrastructure.
3. Formal DEG engine decision and implementation.
4. Enrichment / GSEA / correlation / immune score linkage using real result index.
5. Clinical and survival preflight first; survival execution later.
6. Plotting and report-ready outputs only after result schemas are stable.

Current standardization is a real asset-organizing engine, not just a placeholder. It can identify, copy/canonicalize, register, validate, and package many expression/metadata/clinical/result assets. However, it is still not a full biological normalization, platform-mapping, batch-correction, or statistical-design engine. That boundary must remain explicit before formal analyses are exposed.

## Current Data Source Capabilities

| Source | Acquisition / Preview | Build / Standardized Artifact | Readiness | Current Boundary |
| --- | --- | --- | --- | --- |
| GEO / local files | GSE entry, GEO search, family SOFT download, asset manifest, Series Matrix / supplementary discovery, local file import | Recognition can parse Series Matrix, family SOFT, CSV/TSV/XLSX, imported DEG, metadata, annotation; standardization repository can materialize tabular assets | Ready / capability matrix can detect expression, sample metadata, clinical, imported result, GMT | GEO still lacks a fully controlled real-data standardization proof across all common formats; platform probe mapping and multi-candidate asset selection remain the main gaps |
| TCGA | GDC project preview, file plan, open GDC file download with cache/receipt/manifest | B6.4 builds raw counts, TPM, FPKM, FPKM-UQ matrices; sample metadata; gene annotation; sample/case/file mapping | B6.5 readiness recognizes TCGA expression builds; B6.6 adds clinical mapping and basic OS readiness | TCGA is the most complete source-specific chain, but it still stops at data-check/preflight; it must not auto-run DEG/GSEA/survival |
| GTEx | GTEx tissue preview and plan; limited API-slice validation mode; raw file acquisition path | G6.3 builds GTEx expression matrix, sample metadata, donor metadata, tissue metadata, gene annotation | G6.5 readiness recognizes GTEx expression builds and blocks automatic TCGA merge | GTEx remains independent normal-tissue expression; it is not automatically a TCGA normal control and not automatically joint-DEG ready |

## Recognition Engine Status

Current recognition is broad enough to support downstream preparation:

- GEO Series Matrix: metadata, sample fields, matrix block preview, ID_REF/sample columns, value type evidence, species evidence.
- GEO family SOFT: series/sample/platform blocks, sample metadata, phenotype candidates, platform table hints, expression-table candidates.
- CSV/TSV/TXT/XLSX: expression/count/TPM/FPKM, sample metadata, clinical/survival metadata, gene/platform annotation, imported DEG tables.
- TCGA / GTEx built artifacts are recognized through source-specific manifests/readiness, not only generic file sniffing.
- RAW/heavy files are treated as risky or blocked, not normal expression inputs.
- Imported DEG tables are separated from recompute expression matrices.

Current recognition is still evidence-based. It does not prove that a matrix is biologically normalized, correctly mapped to genes, batch-corrected, or statistically valid for a given analysis.

## Standardization Engine Status

Implemented standardization outputs:

- `manifests/standardization_confirmation.json`
- `manifests/standardized_assets_registry.json`
- `standardized_data/repositories/repository_manifest.json`
- `standardized_data/repositories/validation_report.json`
- `standardized_data/repositories/asset_lineage.jsonl`
- `standardized_data/analysis_ready_assets/analysis_ready_manifest.json`
- `manifests/data_processing_task_plan.json`
- `standardized_data/repositories/analysis_input_repository/*.json`

Implemented repositories:

- expression repository
- sample metadata repository
- group design repository
- feature annotation repository
- clinical repository
- imported result repository
- analysis input repository

Implemented validation / packaging:

- Matrix canonicalization to TSV for text expression assets.
- Row/column counts, duplicate feature warnings, numeric-value checks, negative-count blocking.
- Sample-alignment checks against confirmed group design.
- Blocking for unknown expression value type.
- Blocking for probe/ID_REF without confirmed platform mapping.
- Default asset selection with single-candidate auto-recommendation and multi-candidate blocking.
- Analysis packages for DEG recompute, enrichment from imported result, correlation/heatmap, and survival.

What standardization does not yet do:

- It does not perform biological normalization.
- It does not perform ID_REF/probe-to-gene mapping.
- It does not collapse probes/transcripts to gene-level final matrices.
- It does not batch-correct TCGA + GTEx.
- It does not verify all statistical assumptions for DEG/survival/clinical analysis.
- It does not provide one final cross-source resolver API used by all analysis runners.

Assessment: standardization is a strong asset registry and preparation layer, but the next phase needs a stable resolver and analysis-specific preflight before formal statistics.

## Current Analysis Capabilities

| Analysis area | Current implementation | Runtime status |
| --- | --- | --- |
| DEG preflight | `deg_task_plan.py` and readiness rows validate inputs and store configuration | Connected to current UI as preflight/config only |
| GEO DEG runner | `geo_differential_expression_runner.py` can compute local two-group summaries; uses SciPy Welch t-test if SciPy is present, otherwise fallback statistics; writes CSV/summary | Exists and tested, but not yet productized as a formal task-run path from standardized repository |
| TCGA DEG runner | `tcga/deg_runner.py` supports minimal tumor-vs-normal summary from prepared TCGA package; optional SciPy p-values | Exists and tested, but not exposed as formal B6 continuation |
| Enrichment ORA | `enrichment_runner.py` consumes DEG table + GMT and writes local ORA results | Exists, but depends on a trusted DEG result and selected gene set |
| GSEA | Gene set resource manager and readiness exist | Execution not implemented |
| Correlation | `correlation_runner.py` computes Pearson correlation against a target gene | Exists, needs standardized input resolver and UI parameterization |
| Survival | TCGA clinical builder derives basic OS readiness; `survival_service.py` is preflight-only | KM/Cox/log-rank are not implemented |
| Clinical association / univariate analysis | Clinical parsing and readiness exist; TCGA clinical tables are built | No formal association statistics yet |
| Immune / TME scoring | B7 bulk signature scoring outputs score matrix, coverage, summary, manifest, report draft | Implemented as exploratory score; not true deconvolution |
| Plotting | Result browser/report can consume artifacts; old UI had preview cards | Formal volcano/heatmap/GSEA/KM plots are not implemented in current runtime |
| Report | Markdown report drafts and result index semantics exist | Not report-ready clinical/scientific conclusion |

## Old / Integration / Legacy Findings

Useful prior work:

- `app/bioinformatics/legacy/geo_processing/*`: file classification, RAW/heavy suppression, supplementary and matrix detection rules.
- `app/bioinformatics/legacy/geo_pipeline/process.py`: deeper GEOparse-style family SOFT processing, phenotype extraction, GPL annotation, gene-level aggregation.
- `../ReleaseBuild/archive/legacy_sources/model9/geo_readiness/*`: Series Matrix, SOFT, platform annotation, real-dataset readiness reports.
- `../ReleaseBuild/archive/legacy_sources/model9/local_data/standardizer.py`: local standardized dataset copy and validation report patterns.
- `../ReleaseBuild/archive/legacy_sources/model9/analysis/*`: comparison readiness, DEG-ready matrix, group detection, profile preflight ideas.
- `../Integration/app/bioinformatics/standardized_asset_selection.py`: selectable default asset resolver, but it uses old asset type names and must be adapted to current repository schema.
- `../Integration/app/bioinformatics/analysis_task_runs.py` and `deg_executor_preflight.py`: useful task-run manifest and dry-run preflight shape, but still dry-run and schema-incompatible with current standardized assets.

Important old-boundary findings:

- Old docs repeatedly concluded that limma/DESeq2/edgeR/RStudio-style execution was not implemented.
- Old GSE33630 work reached readiness/descriptive DEG summaries and volcano-shaped tables, not formal p-value/FDR DEG.
- Old survival UI had KM/Cox preview cards, but not a current runtime survival engine.
- Old R / pandas / numpy / GEOparse flows are legacy or optional; current `pyproject.toml` only declares `PySide6` as runtime dependency.

## R / RStudio / Statistical Engine Decision

The next phase should not quietly add RStudio/R, rpy2, limma, DESeq2, edgeR, lifelines, scipy, statsmodels, pandas, or numpy as implicit runtime assumptions.

There are two viable paths:

1. Python-first formal statistics:
   - Add and audit `scipy` + `statsmodels` for t-test / Mann-Whitney and multiple-testing correction.
   - Keep DESeq2/edgeR/limma out of scope initially.
   - Good for controlled two-group DEG MVP, correlation, ORA, and basic plots.

2. External R workflow:
   - Treat R as an explicit optional execution backend.
   - Require environment detection, version capture, script templates, input/output contracts, logs, and failure handling.
   - Use limma/DESeq2/edgeR only after standard input packages and result schemas are stable.

Recommendation: start with a dependency audit for `scipy` + `statsmodels` and a controlled Python DEG MVP. Do not use rpy2/RStudio as the first backend because it adds heavier environment coupling and packaging risk.

## Can Next Analysis Development Start?

Yes, but with a preparatory P0 layer first.

Do not start by wiring buttons directly to existing runners. Existing runners can read files, but the product needs one authoritative path from standardized assets to task runs to result index.

Required P0 before formal analysis:

1. Build `analysis_input_resolver` over current `repository_manifest.json`, `standardized_assets_registry.json`, and `analysis_input_repository`.
2. Normalize asset type naming across current branch and Integration helpers.
3. Define stable analysis package schemas:
   - `deg_recompute`
   - `deg_imported_result`
   - `enrichment_from_deg`
   - `gsea_preranked`
   - `correlation_expression`
   - `immune_score_linkage`
   - `tcga_clinical_survival_preflight`
4. Add a task-run manifest layer in current runtime, adapted from Integration but not copied blindly.
5. Make result-index registration mandatory for every executed analysis.
6. Add formal semantics:
   - `preflight_only`
   - `testing_level`
   - `exploratory`
   - `formal_computed_result`
   - `imported_external_result`

## Recommended Next Work Plan

### P0: Standardized Analysis Input Contract

Deliverables:

- `app/bioinformatics/analysis_inputs/resolver.py`
- resolver tests for GEO/local, TCGA, GTEx, imported DEG, clinical, immune score
- schema docs for each package type
- UI diagnostics showing selected package and blockers

Acceptance:

- Downstream analysis never reads `recognition_report.json` directly.
- Multiple candidate matrices block formal execution until selected.
- Raw counts are routed to DEG only; TPM/FPKM/log-normalized are routed to display/correlation/immune scoring.
- GTEx is never auto-selected as TCGA normal control.

### P1: DEG-Ready Matrix and DEG Preflight

Deliverables:

- DEG-ready matrix builder for standardized packages.
- Sample alignment report: expression columns vs metadata vs group design.
- Gene ID / mapping report: symbol / Ensembl / probe ID status.
- Parameters manifest: method, comparison, thresholds, pseudocount, engine.

Acceptance:

- GEO probe/ID_REF data blocks formal DEG until mapping is confirmed.
- TCGA raw counts can enter DEG preflight but not formal execution until sample groups are sufficient.
- TPM/FPKM are rejected for count-model DEG but allowed for display/correlation/immune score.

### P2: Formal DEG Engine Decision and MVP

Deliverables:

- dependency audit for `scipy` + `statsmodels`, or explicit external R backend design
- minimal two-group DEG result schema
- p-value and FDR policy
- result index registration
- report wording that distinguishes formal vs exploratory

Acceptance:

- No fake p-values.
- No formal significance claim without adjusted p-values.
- Engine version and parameters recorded.

### P3: Enrichment and GSEA

Deliverables:

- ORA consumes formal/imported DEG result plus selected GMT.
- GSEA preflight consumes ranked gene list and selected GMT.
- GSEA execution remains separate after rank metric policy is finalized.

Acceptance:

- Selected gene set resource is required.
- MSigDB licensing remains external/manual.
- Enrichment results are not generated from raw expression without DEG/ranked input.

### P4: Correlation, Immune Score Linkage, Clinical Association

Deliverables:

- correlation task using standardized expression package and target gene
- immune score group comparison / target gene correlation preflight
- TCGA clinical field mapping preflight
- univariate clinical association design document

Acceptance:

- No survival statistics yet.
- Clinical missingness and sample/case mapping are visible.
- B7 immune score stays exploratory and does not become deconvolution.

### P5: Survival Analysis

Deliverables:

- survival input package with OS_time, OS_event, expression grouping policy
- KM/log-rank/Cox design audit
- optional dependency/backend decision

Acceptance:

- OS derivation source is recorded.
- Minimum event thresholds are warnings/blockers according to explicit policy.
- No KM/Cox/log-rank output until backend and censoring rules are validated.

### P6: Plotting and Report-Ready Outputs

Deliverables:

- plot artifact schema
- volcano/heatmap/enrichment/correlation/KM plots after result schemas stabilize
- report-ready gate requiring result semantics, source provenance, and validation status

Acceptance:

- Plotting reads result artifacts only.
- No plot implies formal analysis if the result is exploratory/testing-level.

## Major Gaps to Close

Blocker-level:

- No unified resolver consumed by all downstream analyses.
- Current standardization does not guarantee gene-level mapped matrices for GEO probes.
- Formal DEG dependency/backend decision is unresolved.
- Survival execution backend and censoring policy are absent.

Major:

- Integration helper schemas diverge from current repository schema.
- Multi-candidate asset selection needs current-runtime UI and resolver ownership.
- TCGA/GTEx source-specific builds are strong, but generic standardization still needs cross-source fixtures.
- Result plotting is not yet tied to a stable result artifact schema.

Minor / notes:

- Existing runners are useful test foundations but must be re-wrapped with task-run manifests.
- Current tests are broad, but more real-format fixtures are needed for standardized repository output.
- B6.V light validation proved TCGA/GTEx live interfaces under limits; GEO still needs a comparable controlled live validation around selected Series Matrix / supplementary assets.

## Immediate Recommendation

Start the next milestone as:

**B8.1: Standardized analysis input resolver and task-run contract**

Do not start with formal DEG or survival execution. Build the bridge from standardized repository to analysis tasks first. Once that bridge is stable, the existing GEO DEG runner, TCGA DEG runner, ORA runner, correlation runner, B7 immune scoring, and TCGA clinical readiness can be connected in a controlled order.

This keeps the product honest: data source pipelines can continue to mature, while downstream analyses only run on explicitly prepared and validated inputs.
