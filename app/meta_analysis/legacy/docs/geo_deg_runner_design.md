# GSE33630 DEG Runner Design Audit

This document audits the minimum design for a first GSE33630 DEG runner path. It is documentation only. It does not implement or run DEG, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

## Current Readiness Evidence

The controlled GSE33630 readiness path now has:

- Series Matrix metadata parsed from a local manual `.txt.gz` file.
- expression table report with 54675 features and 105 samples.
- matrix-vs-metadata sample id match status: `match`.
- PTC vs normal/control group detection: 49 PTC, 45 normal/control, 11 ATC excluded.
- GPL570 probe-to-symbol mapping report: 54675 probes, 45782 mapped probes, mapping success rate 0.8373, acceptable.
- readiness/preflight runnable: yes.

## Inputs

A minimal first runner would require explicit, already-local inputs:

- Series Matrix expression values for a GSE33630-like matrix.
- Series Matrix metadata rows with GSM ids and group labels.
- group detection result for PTC vs normal/control.
- GPL570 probe-to-symbol mapping report and, later, a mapping table.
- comparison definition: PTC as case, normal/control as control.

The runner should not fetch GEO, download Series Matrix, download GPL570, inspect RAW/CEL archives, or infer new comparisons automatically.

## Outputs

The future runner should produce:

- DEG-ready matrix artifact or DEG result table artifact, depending on implementation stage.
- DEG runner summary with feature/gene counts, case/control counts, mapping rate, collapse strategy, warnings, and errors.
- `TaskResultRecord` metadata including dataset id, platform id, comparison id, case/control groups, sample counts, feature count, mapped feature count, gene count, collapse strategy, runner type, and source task id when available.

## First Runner Scope Recommendation

The safest first implementation is a DEG-ready matrix builder, not formal statistical DEG.

Recommended v1 scope:

- only GSE33630-like Series Matrix input.
- only two-group comparison.
- only PTC vs normal/control.
- only local files already supplied by the user.
- produce a DEG-ready matrix readiness report and, in a later scoped task, optionally a small artifact.

Formal statistical testing should be deferred until engine choice and dependency policy are explicit.

## Dependency Decision

The current `pyproject.toml` runtime dependency list contains only `PySide6`. It does not include `scipy`, `statsmodels`, `numpy`, or `pandas` as project dependencies.

Because no numerical/statistical stack is declared, the first version should not add heavy dependencies implicitly. A DEG-ready matrix builder can be implemented with standard library fixtures and small in-memory lists for tests. Formal two-group statistics should be a later audit that decides whether to add `scipy`/`statsmodels`, use an optional dependency, or call an external R workflow under explicit user control.

## Probe-To-Symbol Collapse Strategy

GSE33630 uses GPL570 probe ids. A DEG-ready matrix must define how duplicate probes mapping to the same symbol are collapsed.

Recommended first policy:

- implement a simple `mean` collapse for fake/small fixtures in the DEG-ready matrix builder.
- record duplicated gene count and collapse strategy in the report.
- do not claim formal DEG readiness if collapse is unavailable.

A max-variance strategy is plausible later, but it requires variance computation over expression values and clearer numeric dependency policy. Mean collapse is simpler and auditable for the first foundation.

## Explicit Non-Goals

This design does not include:

- enrichment analysis.
- survival analysis.
- batch correction.
- multi-group analysis.
- limma, DESeq2, or edgeR execution.
- production downloader changes.
- `geo_workflow.py` changes.
- automatic task scanning or scheduler behavior.

## Next Minimal Implementation Options

A. DEG-ready matrix builder:

- consume fake expression matrix rows, fake group labels, and fake probe mapping.
- report feature count, mapped feature count, gene count, sample count, case/control counts, duplicated gene count, collapse strategy, readiness, warnings, and errors.
- do not run statistical tests.

B. Minimal two-group DEG runner:

- only after the DEG-ready matrix builder is stable.
- requires a formal dependency/statistical engine decision.
- should still avoid production downloader and `geo_workflow.py` changes.

## DEG-Ready Matrix Builder Foundation

`DegReadyMatrixReport` and `build_deg_ready_matrix_report(...)` provide the first fake-fixture matrix preparation foundation. The builder consumes small in-memory expression rows, sample group labels, and a probe-to-symbol mapping. It reports feature count, mapped feature count, gene count, sample count, case/control counts, duplicated gene count, collapse strategy, readiness, warnings, and errors.

The first collapse strategy is `mean` for duplicated gene symbols. The foundation does not run statistical tests, does not produce a formal DEG result, does not read real GSE33630 files, and does not add scipy/statsmodels or other heavy dependencies.

## GSE33630 DEG-Ready Matrix Manual Test Plan

A future controlled manual test can apply the DEG-ready matrix builder to local GSE33630 files. The test should use the local Series Matrix expression values, local metadata-derived group labels, and local GPL570 mapping report/table.

The test should record feature count, mapped feature count, gene count, sample count, case count, control count, duplicated gene count, collapse strategy, ready status, warnings, and errors.

This test must stop before formal DEG statistics. It must not run limma, DESeq2, edgeR, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

## v0.36 DEG Readiness Baseline

`v0.36-gse33630-deg-readiness` records the current DEG readiness checkpoint:

- GSE33630 readiness/preflight is runnable based on local manual Series Matrix and GPL570 mapping reports.
- GPL570 probe-to-symbol mapping is acceptable for readiness purposes.
- `DegReadyMatrixReport` and `build_deg_ready_matrix_report(...)` provide the first DEG-ready matrix builder foundation.
- mean collapse is the first declared duplicate-symbol strategy for fake/small fixtures.

The baseline still excludes formal DEG statistics, limma/DESeq2/edgeR, enrichment, survival, production downloader changes, and `geo_workflow.py` changes.

Recommended next steps are:

- run a controlled real GSE33630 DEG-ready matrix manual test using local untracked files.
- or audit a minimal two-group statistical DEG runner before adding any statistical dependency.

## Controlled Real GSE33630 DEG-Ready Matrix Manual Test Scope

The controlled manual test uses local, untracked files only:

- `tests/geodatabase/GSE33630_series_matrix.txt.gz`
- `tests/geodatabase/GPL570-55999 (1).txt`

The goal is to generate a DEG-ready matrix readiness report, not a formal DEG result. The test should verify:

- Series Matrix expression features can be matched to GPL570 probe-to-symbol mapping.
- mapped and unmapped probe counts are reported.
- duplicated gene-symbol targets are counted before collapse.
- duplicated symbols can be handled with the declared `mean` collapse strategy.
- sample grouping remains PTC = 49 and normal/control = 45.

The report should record:

- feature count.
- mapped feature count.
- unmapped feature count.
- duplicated gene count.
- gene count after collapse.
- case count.
- control count.
- collapse strategy.
- ready yes/no.
- warnings and errors.

This manual test must not compute formal DEG statistics. It must not compute p-values, formal logFC, enrichment, or a DEG result table. It must not download files, commit local GEO/GPL files, change production downloader behavior, or modify `geo_workflow.py`.

## DEG-Ready Matrix Report Support

The DEG-ready matrix builder now supports two lightweight paths:

- small in-memory probe matrix rows plus sample group labels and a probe-to-symbol mapping.
- readiness reports: `SeriesMatrixExpressionReport`, `PlatformAnnotationMappingReport`, and sample group labels.

`DegReadyMatrixReport` records feature count, mapped feature count, unmapped feature count, duplicated gene count, gene count after collapse, sample count, case/control counts, collapse strategy, ready status, warnings, and errors.

The only supported collapse strategy is `mean`. This remains readiness/reporting only: it does not calculate p-values, formal logFC, or a DEG result table, and it does not depend on real GSE33630 files in unit tests.

## GSE33630 DEG-Ready Matrix Manual Report

The controlled local-file manual report used the untracked GSE33630 Series Matrix and GPL570 annotation files. It produced:

- feature count: 54675.
- mapped feature count: 45782.
- unmapped feature count: 8893.
- duplicated gene count: 22902.
- gene count after collapse: 22880.
- sample count: 105.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- ready: yes.
- warnings: `multi_symbol_cells_collapsed_to_first`, `duplicated_symbols_detected`, `duplicated_genes_collapsed`, `unmapped_probes_excluded`.
- errors: none.

This report does not include p-values, formal logFC, or a DEG result table. It supports moving to a minimal two-group DEG statistical runner audit, with dependency/statistical engine policy still explicit and unresolved.

## GSE33630 DEG-Ready Matrix Baseline

The GSE33630 DEG-ready matrix stage is complete at readiness/report level:

- expression matrix report is connected.
- sample group labels are connected.
- GPL570 probe-to-symbol mapping is connected.
- feature count: 54675.
- mapped feature count: 45782.
- unmapped feature count: 8893.
- gene count after collapse: 22880.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- ready: yes.

Still not implemented:

- formal DEG statistics.
- p-values.
- formal logFC.
- limma, DESeq2, or edgeR.
- enrichment analysis.
- production downloader changes.
- `geo_workflow.py` changes.

Next recommended task: audit a minimal two-group DEG statistical runner before introducing any statistical dependency or formal DEG artifact.

## Minimal Two-Group DEG Statistical Runner Design

The first statistical runner should remain scoped to the already prepared GSE33630-like DEG-ready inputs:

- DEG-ready matrix report and, in a later implementation, the corresponding gene-level matrix.
- sample group labels.
- comparison: PTC vs normal/control.

The current project does not declare scipy, statsmodels, numpy, or pandas as runtime dependencies. Without adding statistical dependencies, the first implementation should not claim a complete DEG test. A standard-library-only runner can reasonably produce:

- per-gene case mean.
- per-gene control mean.
- basic mean difference.
- basic log2FC summary with a documented pseudocount policy.
- a `DegResultSummary` describing counts, comparison, warnings, and limitations.
- a `deg_result_table.csv` that is explicitly effect-size-only.

It should not produce p-values or FDR-adjusted p-values. A complete t-test, multiple-testing correction, limma/DESeq2/edgeR parity, or robust variance modeling requires a separate dependency/statistical-engine audit.

Optional future outputs after dependency review:

- `volcano_ready_table.csv`, only if p-value or FDR policy is implemented.
- formal DEG result table with p-value and adjusted p-value columns.

First-version non-goals:

- no limma.
- no DESeq2.
- no edgeR.
- no enrichment.
- no survival.
- no batch correction.
- no production downloader changes.
- no `geo_workflow.py` changes.

Recommended next task: implement a minimal DEG summary runner without p-values, or perform a dedicated scipy/statsmodels dependency audit before formal statistics.

## Minimal DEG Summary Model Foundation

`DegSummaryReport` and `DegSummaryRow` provide the first standard-library-only effect-size summary model. The fake-fixture runner consumes a small gene-level matrix plus sample group labels and computes per-gene case mean, control mean, and log2FC with a small pseudocount.

This foundation explicitly reports `pvalue_available=false` and `fdr_available=false`. It does not sort genes as statistically significant, does not calculate p-values, does not calculate adjusted p-values, does not run limma/DESeq2/edgeR, and does not depend on real GSE33630 files.

`write_deg_summary_table(report, output_path)` writes the effect-size-only summary artifact with stable CSV columns: `gene_symbol`, `case_mean`, `control_mean`, `log2fc`, and `status`. The report method is `mean_log2fc_summary`; p-value and FDR fields are intentionally unavailable and are not written to the artifact.

## GSE33630 Minimal DEG Summary Manual Test Plan

The current GSE33630 DEG-ready matrix status is `ready=yes`, with 49 PTC case samples, 45 normal/control samples, and 22880 genes after mean collapse. The next controlled manual test should use a gene-level collapsed matrix to compute an exploratory mean log2FC summary.

The manual test should record:

- gene count.
- computed gene count.
- skipped gene count.
- top absolute log2FC genes.
- warnings and errors.

This is not a formal DEG result. The test must not calculate p-values, adjusted p-values, formal significance calls, enrichment, survival, or limma/DESeq2/edgeR output. Label the output as exploratory DEG summary only.

## GSE33630 Exploratory Minimal DEG Summary Manual Test

The local GSE33630 Series Matrix and GPL570 annotation files were used read-only to build a gene-level collapsed matrix and compute an exploratory mean/log2FC summary:

- gene-level collapsed matrix built: yes.
- gene count: 22880.
- computed gene count: 22880.
- skipped gene count: 0.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- pvalue available: false.
- FDR available: false.
- warnings: `multi_symbol_cells_collapsed_to_first`, `duplicated_symbols_detected`, `duplicated_genes_collapsed`, `unmapped_probes_excluded`.
- errors: none.

Top absolute log2FC genes, exploratory only: `RP11-476D10.1`, `MMRN1`, `PRR15`, `ARHGAP36`, `ZCCHC12`, `LRP1B`, `RXRG`, `TMEM255A`, `GABRB2`, and `PDZRN4`.

This is not a formal DEG result and does not include p-values, FDR, limma/DESeq2/edgeR, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

## Formal DEG Statistical Dependency Audit

The current minimal DEG summary is descriptive only. Its limitations are:

- no p-value.
- no FDR or multiple-testing correction.
- no variance model.
- no empirical Bayes moderation.
- no formal significance calling.

A formal two-group DEG runner would need:

- a defined statistical test.
- variance handling.
- multiple-testing correction.
- logFC.
- p-value.
- adjusted p-value.
- clear output semantics for formal DEG result tables.

Dependency options:

- no new dependency: keep descriptive summaries only.
- scipy: can support basic tests such as t-test or Mann-Whitney, but does not by itself provide a full DEG workflow policy.
- statsmodels: can support multiple-testing correction.
- rpy2/limma: not recommended for the next step because it adds a heavier runtime and environment coupling.

Recommendation: do not introduce statistical dependencies in this step. Run a dedicated scipy + statsmodels dependency audit before implementing formal p-values or FDR. Until then, keep the current output labeled exploratory/descriptive.

Still not done: formal DEG runner, requirements changes, real statistical testing, limma/DESeq2/edgeR, enrichment, survival, production downloader changes, and `geo_workflow.py` changes.

## v0.37 Minimal DEG Summary Foundation

`v0.37-minimal-deg-summary-foundation` records the first minimal DEG summary foundation:

- `DegSummaryReport`
- `DegSummaryRow`
- mean/log2FC effect-size summaries with pseudocount.
- `write_deg_summary_table(...)` for a stable effect-size-only CSV artifact.

This is not formal DEG. It has no p-value, no FDR, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes.

Recommended next steps:

- A. GSE33630 real minimal DEG summary manual test.
- B. statistical dependency audit for scipy/statsmodels.
- C. formal DEG runner design.

## v0.38 GSE33630 Exploratory DEG Summary Baseline

`v0.38-gse33630-exploratory-deg-summary` records the controlled real-file exploratory DEG summary baseline for GSE33630:

- gene-level collapsed matrix built: yes.
- gene count: 22880.
- computed gene count: 22880.
- skipped gene count: 0.
- case count: 49.
- control count: 45.
- collapse strategy: `mean`.
- summary method: descriptive mean/log2FC.
- pvalue available: false.
- FDR available: false.

The baseline also records the formal DEG dependency audit conclusion: do not change requirements or implement formal statistics in this phase. Formal DEG requires a separate scipy/statsmodels decision for statistical tests and multiple-testing correction.

This remains exploratory only. It is not formal DEG, does not produce p-values or FDR, does not run limma/DESeq2/edgeR, does not run enrichment or survival, does not change production downloader behavior, and does not modify `geo_workflow.py`.

Next options:

- A. introduce scipy/statsmodels after a focused dependency decision and implement minimal formal DEG.
- B. continue no-dependency descriptive DEG summaries.
- C. build a volcano-ready descriptive table without p-values.

## Volcano-Ready Descriptive Table Design

The first volcano-ready table should consume the existing `DegSummaryReport.rows` output and write a structurally plot-friendly CSV named `volcano_ready_descriptive_table.csv`. It remains descriptive only and must not be used for statistical significance thresholds.

Required columns:

- `gene_symbol`
- `case_mean`
- `control_mean`
- `log2fc`
- `abs_log2fc`
- `status`
- `pvalue`
- `padj`
- `pvalue_available`
- `fdr_available`
- `method`

Field policy:

- `abs_log2fc` is the absolute value of `log2fc`.
- `pvalue` and `padj` are empty because no statistical test is performed.
- `pvalue_available=false`.
- `fdr_available=false`.
- `method=descriptive_mean_log2fc`.
- row status should avoid significance language; use descriptive statuses such as `descriptive_only`, `computed`, or `skipped`.

UI and report layers must label this output as exploratory/descriptive only. It is volcano-ready only in the sense that downstream plotting code can read gene and log2FC columns. It is not formal DEG, does not support p-value or FDR cutoffs, and does not require scipy, statsmodels, limma, DESeq2, or edgeR.

## Volcano-Ready Descriptive Table Writer

`write_volcano_ready_descriptive_table(report, output_path)` writes the no-dependency descriptive volcano table. It uses existing `DegSummaryReport.rows`, writes empty `pvalue` and `padj` cells, sets `pvalue_available=false`, `fdr_available=false`, and records `method=descriptive_mean_log2fc`.

Computed rows are labeled `descriptive_only` rather than `significant`. The writer does not sort genes as formal DEG hits, does not calculate p-values or FDR, does not add statistical dependencies, and does not require real GSE33630 files in tests.

## GSE33630 Descriptive Volcano Table Manual Test

The controlled GSE33630 exploratory summary can generate a descriptive volcano-ready table without producing a formal DEG result:

- total genes: 22880.
- computed genes: 22880.
- skipped genes: 0.
- local artifact path: `<local-temp>/volcano_ready_descriptive_table.csv` (not committed).
- pvalue available: false.
- FDR available: false.
- no formal DEG.
- no significance claim.

The top absolute log2FC genes remain the exploratory list from the v0.38 summary: `RP11-476D10.1`, `MMRN1`, `PRR15`, `ARHGAP36`, `ZCCHC12`, `LRP1B`, `RXRG`, `TMEM255A`, `GABRB2`, and `PDZRN4`.

No complete volcano table was committed and no volcano plot was generated.

## v0.39 Descriptive Volcano Table Baseline

`v0.39-descriptive-volcano-table` records the no-dependency descriptive volcano table baseline:

- `write_volcano_ready_descriptive_table(...)`.
- `volcano_ready_descriptive_table.csv` field policy.
- GSE33630 descriptive volcano-ready table manual test.
- empty `pvalue` and `padj`.
- `pvalue_available=false`.
- `fdr_available=false`.
- `method=descriptive_mean_log2fc`.

This baseline has no p-values, no FDR, no formal DEG, no statistical significance calls, no scipy/statsmodels, no limma/DESeq2/edgeR, no enrichment, no survival, no production downloader changes, and no `geo_workflow.py` changes.

Next step: decide whether formal DEG should introduce scipy/statsmodels or continue descriptive-only reporting.

## Formal DEG Dependency Decision

The current descriptive DEG outputs remain limited:

- no p-value.
- no FDR or multiple-testing correction.
- no variance model.
- no formal differential expression claim.

A minimal formal two-group DEG layer would need:

- two-group statistical test.
- log2FC.
- p-value.
- adjusted p-value.
- stable result table with explicit method metadata.

Dependency options:

- no new dependency: continue descriptive-only summaries and volcano-ready tables with empty p-value/FDR fields.
- scipy: suitable for a first basic two-group test such as `ttest_ind` or `mannwhitneyu`.
- statsmodels: suitable for `multipletests` FDR adjustment.
- rpy2/limma: not recommended for the next step because it introduces heavier R runtime coupling.
- DESeq2/edgeR: not recommended for the next step because count-model workflow and R dependency policy need a separate design.

Recommendation: if formal DEG is allowed, introduce scipy and statsmodels together in a dedicated dependency task before implementing the runner. If new dependencies are not allowed, continue descriptive reporting/UI only.

This audit does not install dependencies, does not change `pyproject.toml`, does not change `requirements.txt`, and does not implement or run formal DEG statistics.
