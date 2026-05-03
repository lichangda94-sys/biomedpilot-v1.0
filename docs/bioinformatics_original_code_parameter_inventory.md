# Bioinformatics Original Code Parameter Inventory

Source reviewed:

- `/Users/changdali/Documents/code/bioinformatics_original_codes.md`
- `/Users/changdali/Documents/code/GEOgood1.txt`
- `/Users/changdali/Documents/code/GEOgood2.txt`
- `/Users/changdali/Documents/code/GEOgood3.txt`
- `/Users/changdali/Documents/code/GEObad.txt`
- `/Users/changdali/Documents/code/tcgagood1.txt`
- `/Users/changdali/Documents/code/tcgabad.txt`
- `/Users/changdali/Documents/code/tcga:gtex.txt`

Note: `bioinformatics_original_codes.md` is a scaffold with placeholders. The concrete parameters below were extracted from the adjacent original-code `.txt` files supplied in the same user command. Dataset names, target genes, drug names, and local paths are thesis examples, not software-fixed logic.

## 1. Code Blocks, Datasets, Purpose, Main Functions

| Dataset / source | Analysis purpose | Main functions extracted |
|---|---|---|
| GSE171483 | BCPAP thyroid cancer cell drug-treatment comparison: control vs Dabrafenib and Vemurafenib. | Load sample annotation and gene expression matrix, clean sample IDs, build limma design matrix, run contrasts, export DEG tables, volcano plots, enrichment, GSEA, target-gene expression plots, Pearson correlation and correlation-based enrichment. |
| GSE261830 | TPC-1 thyroid cancer cell control vs selpercatinib comparison. | Build DESeq2 count model, run contrast `selpercatinib` vs `control`, export ordered DEG table, volcano plot, GO/KEGG enrichment, GSEA, target-gene expression plots, Pearson correlation and enrichment for positive/negative correlated genes. |
| GSE60542 | PTC tumor/normal, N0/N1 lymph-node status, BRAF/nonBRAF and RET/nonRET subgroup analyses. | Clean clinical table and sample mapping, annotate expression matrix, compare target-gene expression across clinical or mutation groups, run limma DEG for N1 vs N0, PTC vs Normal, BRAF vs nonBRAF, RET vs nonRET, run GO/KEGG/GSEA and correlation-based enrichment by subgroup. |
| GEO preprocessing examples, including GSE3678, GSE50901, GSE86961 | General GEO download, annotation and QC workflow; some snippets are exploratory or "bad" prototypes. | `GEOquery::getGEO`, `exprs`, `pData`, `fData`, gene symbol/title detection, duplicate-gene aggregation, raw/normalized QC plots, probe annotation, limma DEG, enrichment and network plots. |
| TCGA-THCA clinical/expression | TCGA clinical XML parsing, paired tumor-normal sample identification, N0/N1 clinical subsets, survival-ready merged table. | Parse XML for BRAF/RET/PTC and survival fields, clean `n_stage`, build paired tumor/normal lists by submitter ID, merge expression with clinical tables, export `.csv`/`.xlsx` assets. |
| TCGA-THCA survival | Overall survival analysis for expression-high/low groups and clinical covariates. | Median split expression groups, `Surv(OS.time, OS)`, univariate and multivariate `coxph`, `survfit`, `ggsurvplot`, forest plots for HR and 95% CI. |
| TCGA correlation/enrichment | Correlate target gene expression with all genes in TCGA subsets. | Pearson and Spearman correlation, p/FDR adjustment, positive/negative gene sets, SYMBOL/ENSEMBL to ENTREZ conversion, GO/KEGG enrichment, GSEA-like ranked analysis. |
| TCGA + GTEx thyroid tumor-normal | Volcano visualization of limma tumor-normal result and manual labels for lipid receptor genes. | Classify significant genes by `adj.P.Val < 0.05` and `logFC` thresholds, draw volcano plots, add dashed threshold lines, highlight configurable gene panels. |
| TCGA data download prototypes | GDC download of TCGA-THCA expression, isoform, miRNA, methylation, structural variation, CNV, clinical supplement. | `TCGAbiolinks::GDCquery`, `GDCdownload`, `GDCprepare`; batch/retry parameters; download directory construction. |

## 2. Plotting Parameters

### Global plotting conventions

| Parameter | Extracted values |
|---|---|
| Primary plotting package | `ggplot2`; wrappers from `ggpubr`, `survminer`, `enrichplot`; base `png()` for some network/QC plots. |
| Common export format | Mostly `.png`; some plots are displayed only; a commented expression-plot export uses `.pdf`. |
| Common `ggsave` size | `width = 8, height = 6` for enrichment/GSEA; `width = 7, height = 6` or `7 x 5.5` for correlation dotplots; `width = 5, height = 5` for boxplots; `width = 9, height = 6` for GSE261830 top enrichment; `width = 10, height = 8` for generic enrichment bar/dot/network plots. |
| Common dpi | `dpi = 300` where specified; many `ggsave()` calls omit dpi and therefore use ggplot2 defaults. |
| Base graphics size | `png(width = 3000, height = 2000, res = 300)` for selected GSEA plots; `png(width = 1000, height = 800)` for network plots; several QC `png()` calls use default dimensions. |
| Theme | `theme_bw(base_size = 12/13/14)`, `theme_minimal()`, `theme_minimal(base_size = 14)`. |
| Font family | Not explicitly set. |
| Title styling | Centered titles via `plot.title = element_text(hjust = 0.5, face = "bold", size = 16)` for many boxplots; volcano title centered and bold in TCGA+GTEx. |
| Axis styling | X-axis text commonly `size = 16, face = "bold"`; Y-axis text `size = 12`; Y-axis title `size = 12` or `14`. |
| Legend | Frequently hidden for grouped boxplots with `legend.position = "none"`; volcano and Cox forest plots use `legend.position = "top"`; enrichment dotplots may keep legends for gene count/pathway type. |

### Volcano plots

| Parameter | Extracted values |
|---|---|
| Plot type | `ggplot(..., aes(logFC/log2FoldChange, -log10(adj.P.Val/padj), color = threshold)) + geom_point()` |
| Significance | GEO limma and TCGA+GTEx: `adj.P.Val < 0.05` and `abs(logFC) > 1`; DESeq2: `padj < 0.05` and `abs(log2FoldChange) > 1`. |
| Colors | Simple volcano: `Significant = "red"`, `Not Significant = "grey"`; TCGA+GTEx: up `red`, down `blue`, not significant `grey`. |
| Point | `alpha = 0.6`; TCGA+GTEx also `size = 1.5`. |
| Threshold lines | TCGA+GTEx uses vertical dashed lines at `logFC = -1, 1` and horizontal dashed line at `-log10(0.05)`, dark green annotation `FDR = 0.05`. |
| Highlight labels | `geom_text` with `size = 4`, `color = "black"`, `fontface = "bold"`, `vjust = -0.5`; arrow segments with `arrow(length = unit(0.02, "npc"))`; manual x/y offsets (`logFC +/- 3`, `-log10(adj.P.Val) + 15`). |
| File naming | Mostly not exported in code snippets; DEG table names encode dataset and contrast, e.g. `GSE171483_DEG_Dabrafenib_vs_control.csv`, `GSE261830_DEG_Selpercatinib_vs_control.csv`. |

### Expression boxplots / paired plots

| Parameter | Extracted values |
|---|---|
| Plot type | `geom_boxplot(outlier.shape = NA)` plus `geom_jitter`; paired tumor-normal plot also uses `geom_line(alpha = 0.5, color = "gray")`. |
| Colors | Tumor/N1/BRAF/RET often `#E64B35`; Normal/N0/nonBRAF/nonRET often `#4DBBD5`; ADIPOR comparison uses `skyblue` or `lightblue`; paired plot maps Tumor `#E64B35`, Normal `#4DBBD5`. |
| Jitter | Width `0.2`; point size usually `1.5`; alpha ranges `0.3`, `0.4`, `0.6`, `0.7`, `0.9`; point color often black. |
| Statistical label | `ggpubr::stat_compare_means`; methods include `t.test` and `wilcox.test`; labels include `p.signif`; text size often `6`. |
| Manual significance | Paired ADIPOR plot uses `wilcox.test(..., paired = TRUE)`, manual star conversion, annotation at `y_max * 1.10` with size `5`, bold, plus p-label at `y_max * 1.05`, size `4.5`. |
| Common size/export | `5 x 5`, `dpi = 300` for LDLR N0 vs N1; commented per-gene expression exports use `4 x 4` PDF. |
| File naming | Examples: `LDLR_Expression_N0_vs_N1_Boxplot.png`, `TPC1_<gene>_Expression.pdf`, `BCPAP_<gene>_Expression.pdf`. |

### Correlation dotplots

| Parameter | Extracted values |
|---|---|
| Method | Pearson for most GEO/TCGA all-gene correlations; Spearman appears in one TCGA block with FDR adjustment. |
| Plot type | Dotplot of selected genes: x = correlation, y = gene, size = `-log10(p-value)`, color = correlation. |
| Theme/export | `theme_bw(base_size = 14)`; `ggsave(width = 7, height = 6 or 5.5, dpi = 300)`. |
| File naming | Examples: `ADIPOR1_ADIPOR2_correlation_Selpercatinib.png`, `LDLR_correlation_Selpercatinib.png`, `ADIPOR1_ADIPOR2_correlation_sorted_noLDLR.png`, `LDLR_correlation_dotplot.png`. |

### Enrichment dotplots/barplots and GSEA plots

| Parameter | Extracted values |
|---|---|
| Dotplot axes | x = `-log10(p.adjust)` or `-log10(FDR)`; y = reordered `Description`; size = `Count`. |
| GO color | Often `steelblue`; KEGG often `darkred`; highlighted terms use `yes = "red"`, `no = "black"`. |
| Gradient barplot | Enrichment bars use `scale_fill_gradient(low = "#4DBBD5", high = "#E64B35")`. |
| Theme | `theme_bw(base_size = 12/13/14)` or `theme_minimal(base_size = 14)`. |
| Show categories | Top 10, top 15, or `showCategory = 20` in prototype `enrichplot` calls. |
| Export size | Usually `8 x 6`, `9 x 6`, or `10 x 8`; dpi only sometimes `300`. |
| File naming | `GSE261830_GO_BP_enrichment_top15.png`, `GSE261830_KEGG_enrichment_top15.png`, `<target_gene>_<GO|KEGG>_<positive|negative>_dotplot.png`, `GSEA_<keyword>_<i>_<safe_desc>.png`, `GSEA_GO_BP_results.csv`, `GSEA_GO_BP_object.rds`. |

### Survival and Cox plots

| Parameter | Extracted values |
|---|---|
| KM plotting | `survminer::ggsurvplot`. |
| KM options | `pval = TRUE`, `risk.table = TRUE`, `conf.int = FALSE`, palette `c("#00BFC4", "#F8766D")`, legend labels `Low`, `High`, x-axis `Time (days)`, y-axis `Overall Survival Probability`. |
| Forest plots | `geom_point(size = 3)`, `geom_errorbarh(height = 0.2)`, dashed HR=1 line in `gray40`, p-value text at `max(CI_upper) * 1.1`, colors `Significant = "red"`, `Not significant = "#0072B2"`, `theme_minimal(base_size = 14)`, legend top. |
| Export | Several survival plots are printed but not saved in the reviewed snippets; Cox tables are exported to CSV. |

## 3. Statistical Analysis Parameters

### DEG: limma

| Parameter | Extracted values |
|---|---|
| Packages/functions | `limma::lmFit`, `makeContrasts`, `contrasts.fit`, `eBayes`, `topTable`. |
| Design | `model.matrix(~0 + group)` with group-specific columns. |
| GSE171483 groups | `control`, `Dabrafenib`, `Vemurafenib`. |
| GSE171483 contrasts | `Dabrafenib - control`; `Vemurafenib - control`. |
| GSE60542 contrasts | `N1 - N0`, `PTC - Normal`, `BRAF - nonBRAF`, `RET - nonRET`. |
| Transform | GSE60542 DEG uses `log_expr` in its limma helper; exact pseudo-count/log base should be confirmed from source before implementation. |
| Multiple testing | `topTable(..., adjust.method = "fdr")` in GSE171483; otherwise `topTable` default or explicit post-filter `adj.P.Val`. |
| DEG threshold | Main DEG filters: `adj.P.Val < 0.05` and `abs(logFC) > 1`; enrichment sometimes relaxes to `logFC > 0.5` / `< -0.5` plus `adj.P.Val < 0.05`. |

### DEG: DESeq2

| Parameter | Extracted values |
|---|---|
| Dataset | GSE261830. |
| Packages/functions | `DESeq2::DESeqDataSetFromMatrix`, `DESeq`, `results`. |
| Count input | `round(expr)` from `GSE261830_expression_by_gene.csv`; this may be unsafe if the file is TPM-like and requires validation. |
| Design | `design = ~ group`. |
| Grouping | First 3 samples control, last 3 samples selpercatinib. |
| Contrast | `results(dds, contrast = c("group", "selpercatinib", "control"))`. |
| Ordering | `res[order(res$padj), ]`. |
| DEG threshold | `padj < 0.05` and `abs(log2FoldChange) > 1`. |
| Shrinkage | No `lfcShrink` observed. |

### Expression comparison

| Parameter | Extracted values |
|---|---|
| Tests | `t.test` in some drug/two-gene comparisons; `wilcox.test` for most clinical subgroup and paired comparisons. |
| Paired handling | Paired TCGA tumor-normal uses `paired = TRUE`; ADIPOR1 vs ADIPOR2 within same patient uses `wilcox.test(..., paired = TRUE)`. |
| Significance labels | `p.signif` from `stat_compare_means`; manual stars: `p < 0.001`, `p < 0.01`, `p < 0.05`, else `ns`. |
| Group examples | N0 vs N1, Tumor vs Normal, BRAF vs nonBRAF, RET vs nonRET, control vs treatment. |

### Correlation

| Parameter | Extracted values |
|---|---|
| Methods | Pearson in most code: `cor(..., method = "pearson")` and `cor.test(...)`; Spearman in one TCGA block: `cor.test(..., method = "spearman")`. |
| P-value handling | Raw `cor.test(...)$p.value`; one Spearman block applies `p.adjust(..., method = "fdr")`. |
| Gene-set split | Positive and negative correlated genes are created, but the exact correlation cutoffs are inconsistently visible and should be confirmed; direction is at least sign-based in several blocks. |
| ID conversion | `clusterProfiler::bitr` from `SYMBOL` or `ENSEMBL` to `ENTREZID`, using `org.Hs.eg.db`. |

### GO / KEGG enrichment

| Parameter | Extracted values |
|---|---|
| Packages/functions | `clusterProfiler::enrichGO`, `enrichKEGG`, `bitr`; `org.Hs.eg.db`; `enrichplot` for plotting. |
| Organism | Human: `OrgDb = org.Hs.eg.db`, `organism = "hsa"`. |
| ID type | `SYMBOL`, `ENSEMBL`, `ENTREZID`; enrichment generally consumes ENTREZ IDs. |
| Ontology | GO `ont = "BP"`. |
| P-adjust method | `BH` and `fdr` both appear; software should expose this and default to `BH` or `fdr` consistently after confirmation. |
| P/q cutoffs | `pvalueCutoff = 0.05` in some TCGA/prototype blocks; many `enrichGO/enrichKEGG` calls rely on defaults; `qvalueCutoff = 0.05` and `qvalueCutoff = 0.2` both appear. |
| Readable | `readable = TRUE` in many GO calls. |
| DEG-to-enrichment filters | `adj.P.Val < 0.05 & abs(logFC) > 1`; relaxed direction-specific filters `logFC > 0.5` or `< -0.5` plus `adj.P.Val < 0.05`; DESeq2 `padj < 0.05 & abs(log2FoldChange) > 1`. |

### GSEA

| Parameter | Extracted values |
|---|---|
| Packages/functions | `clusterProfiler::gseKEGG`, `gseGO`, `enrichplot::gseaplot2`. |
| Ranking metric | limma `logFC`; DESeq2 `log2FoldChange`; TCGA correlation block ranks by correlation after SYMBOL to ENTREZ conversion. |
| Sorting | Rank vector named by gene symbol/ENTREZ, `sort(..., decreasing = TRUE)`. |
| Organism/ontology | KEGG `organism = "hsa"`; GO `ont = "BP"`; `keyType = "ENTREZID"` when specified. |
| Gene-set size | `minGSSize = 10`; TCGA GSEA block also `maxGSSize = 500`. |
| P-value cutoff | `pvalueCutoff = 0.5` for exploratory GEO GSEA, `pvalueCutoff = 1` in one GSE261830 KEGG GSEA block, `pvalueCutoff = 0.05` in TCGA correlation GSEA. |
| Term selection | Keyword filters for lipid/metabolism/survival-related pathways and `adj.P.Val < 0.25` in some GSEA result filtering. These are paper-specific. |

### Survival

| Parameter | Extracted values |
|---|---|
| Packages/functions | `survival::Surv`, `coxph`, `survfit`; `survminer::ggsurvplot`. |
| Time/event | `OS.time`, `OS`. |
| Grouping | Median split: expression `>= median(..., na.rm = TRUE)` is `High`, otherwise `Low`; factor levels `Low`, `High`. |
| KM test | `ggsurvplot(pval = TRUE)` implies log-rank p-value. |
| Cox models | Univariate Cox loops over expression group, stage, age, gender; multivariate Cox uses continuous expression plus `stage_group + age + gender`. |
| Stage handling | `stage_group` merges stage categories; exact mapping is code-specific and should become configurable. |
| Outputs | `cox_univariate_results.csv`, `cox_univariate_LDLR.csv`, forest plot displayed; KM plots displayed but not always saved. |

## 4. R Package Dependencies and Uses

| Package | Source | Use | Software role |
|---|---|---|---|
| tidyverse | CRAN | Data wrangling, reshaping, plotting wrapper imports | Core convenience |
| dplyr | CRAN | Filtering, grouping, mutation, joins | Core |
| tidyr | CRAN | Long/wide reshaping | Core |
| readr | CRAN | CSV reading/writing | Core |
| readxl | CRAN | Excel input | Optional input |
| openxlsx | CRAN | Excel output | Optional output |
| writexl | CRAN | Excel output in prototype code | Optional output |
| stringr | CRAN | Sample/gene/path string cleaning | Core |
| purrr | CRAN | Functional iteration in TCGA download prototypes | Optional |
| XML | CRAN | TCGA clinical XML parsing | TCGA clinical |
| TCGAbiolinks | Bioconductor | GDC query/download/prepare for TCGA | Data acquisition |
| GEOquery | Bioconductor | GEO download/load in prototype code | Data acquisition |
| Biobase | Bioconductor | `exprs`, `pData`, `fData` objects via GEO workflows | Data acquisition |
| limma | Bioconductor | Microarray/log-expression DEG | Core analysis |
| DESeq2 | Bioconductor | Count DEG | Core analysis |
| clusterProfiler | Bioconductor | GO/KEGG/GSEA and ID conversion | Enrichment |
| org.Hs.eg.db | Bioconductor | Human SYMBOL/ENSEMBL/ENTREZ mapping | Annotation |
| enrichplot | Bioconductor | GSEA and enrichment visualization | Plotting |
| biomaRt | Bioconductor | Annotation lookup in prototype code | Optional annotation |
| affy | Bioconductor | Affymetrix raw preprocessing in prototype code | Optional legacy |
| gcrma | Bioconductor | Affymetrix normalization in prototype code | Optional legacy |
| ggplot2 | CRAN | General plotting | Core plotting |
| ggpubr | CRAN | `stat_compare_means` and expression plot statistics | Plotting/stat annotation |
| ggrepel | CRAN | Loaded for label placement, though manual `geom_text` is often used | Optional plotting |
| grid | R base/recommended | Arrow unit sizing in volcano label segments | Plotting helper |
| ggtext | CRAN | Markdown-colored enrichment axis labels | Optional plotting |
| reshape2 | CRAN | Melt/reshape in expression snippets | Legacy optional |
| survival | CRAN | Cox/KM survival analysis | Survival |
| survminer | CRAN | KM survival plotting | Survival plotting |
| forcats | CRAN | Factor reordering in Cox forest plots | Optional |
| igraph | CRAN | Pathway interaction network prototypes | Optional network |

## 5. Input and Output File Specifications

### Inputs

| Input | Observed format / columns |
|---|---|
| GEO expression matrix | CSV, genes/probes as rows and samples as columns; examples include `GSE171483_expression_by_gene.csv`, `GSE261830_expression_by_gene.csv`, `GSE60542_expression_matrix_annotated.csv`. |
| GEO sample annotation | CSV/XLSX; sample ID columns such as `sample`, GSM, or sample ID mapping; group fields such as `treatment`, tumor/normal, N stage, mutation status. |
| GEO raw data | GEOquery `getGEO(dataset_name, GSEMatrix = TRUE)` saved as `<dataset_name>_rawdata.RData`; raw expression/sample/gene info exported to CSV. |
| TCGA expression/clinical merged table | CSV, examples include `THCA_clinical_expression_merged.csv`, `THCA_final_for_survival.csv`; expected columns include `submitter_id`, target gene expression columns, `OS.time`, `OS`, `stage`, `age`, `gender`. |
| TCGA clinical supplement | XML directory; parsed for submitter ID, survival time/event, mutation/fusion and clinical fields. |
| TCGA/GTEx DEG result | CSV `DEG_thyroid_limma_results.csv`, row names as genes, columns including `logFC`, `adj.P.Val`. |
| DEG result for downstream enrichment | CSV with `SYMBOL`, `logFC`, `adj.P.Val` or DESeq2 fields `log2FoldChange`, `padj`. |
| Gene panels / target genes | Hard-coded vectors in source; should become user-provided list or config. |

### Outputs

| Output | Observed naming |
|---|---|
| DEG tables | `GSE171483_DEG_Dabrafenib_vs_control.csv`, `GSE171483_DEG_Vemurafenib_vs_control.csv`, `GSE261830_DEG_Selpercatinib_vs_control.csv`, `DEG_N0_PTC_vs_Normal_clean.csv`, mutation contrast DEG files. |
| Significant DEG tables | Contrast-specific clean/significant CSV/XLSX files; suffixes include `_clean`, `_sig`, or direction-specific up/down outputs. |
| Clinical assets | `THCA_clinical_all_info_with_BRAF_RET.xlsx`, `THCA_expression_paired_sample_list.xlsx`, `THCA_PTC_N0_clinical.xlsx`, `THCA_PTC_N1_clinical.xlsx`, `THCA_survival_info.csv`. |
| Survival outputs | `cox_univariate_results.csv`, `cox_univariate_LDLR.csv`; KM and forest plots are often printed, not saved. |
| Enrichment tables | `GO_BP_enrichment.csv`, `KEGG_enrichment.csv`, `GSEA_GO_BP_results.csv`, `GSEA_GO_BP_object.rds`, contrast/gene-specific GO/KEGG XLSX files. |
| Plot files | PNG names encode dataset, contrast, target gene, direction and analysis type, e.g. `GSE261830_GO_BP_enrichment_top15.png`, `<target_gene>_GO_positive_dotplot.png`, `GSEA_<keyword>_<term>.png`. |
| Prototype QC | `Boxplot_Raw_Data.png`, `Density_Raw_Data.png`, `Heatmap_Raw_Data.png`, `PCA_Raw_Data.png`, normalized equivalents. |

Suggested software output structure:

```text
results/
  inputs_snapshot/
  tables/
    deg/
    clinical/
    correlation/
    enrichment/
    survival/
  figures/
    volcano/
    expression/
    correlation/
    enrichment/
    gsea/
    survival/
    qc/
  logs/
  reproducibility/
```

## 6. Paper-Specific Logic That Must Not Be Hard-Coded

- Target genes and panels: `ADIPOR1`, `ADIPOR2`, `CDH13`, `APPL1`, `LDLR`, plus lipid receptor panels such as `HMGCR`, `SREBF1`, `SREBF2`, `PCSK9`, `APOB`, `APOE`, `ABCA1`, `OLR1`, `SCARB1`, `LRP1`. These are examples only.
- Specific GEO datasets: `GSE171483`, `GSE261830`, `GSE60542`, and exploratory candidates/prototypes including `GSE3678`, `GSE50901`, `GSE86961`, `GSE130512`, `GSE230424`, `GSE232237`, `GSE202413`, `GSE199207`, `GSE191288`, `GSE197443`, `GSE129880`, `GSE83560`, `GSE94464`, `GSE6004`, `GSE246010`, `GSE69039`.
- Drug group labels and ordering: `control`, `Dabrafenib`, `Vemurafenib`, `selpercatinib`, and assumptions such as first 3 samples are control and last 3 are treatment.
- Disease/subgroup labels: PTC, N0/N1, BRAF/nonBRAF, RET/nonRET, Tumor/Normal; these should be configurable comparison definitions.
- TCGA project: `TCGA-THCA` should be a selected project, not fixed software behavior.
- Local absolute paths under `/Volumes/lab`, `/Volumes/data`, and `~/Desktop/SX`.
- Manual volcano label offsets for specific genes such as APOB and SREBF2.
- Keyword filters for pathway focus plots and GSEA term selection; these are paper narratives, not defaults.
- Stage recoding and XML tag search rules unless converted into explicit, documented clinical field mappings.

## 7. Parameters Suitable for Software Defaults

| Parameter | Suggested default | Rationale |
|---|---|---|
| Plot format | `png`, optional `pdf` | Source mostly uses PNG; PDF appears as a commented export. |
| DPI | `300` | Commonly specified for publication-oriented PNGs. |
| Standard plot size | `8 x 6 in` | Most enrichment/GSEA plots use this. |
| Boxplot size | `5 x 5 in` | Explicitly used for target expression plot export. |
| Volcano threshold | `abs(logFC) > 1`, adjusted p `< 0.05` | Repeated across limma/DESeq2/TCGA+GTEx. |
| DEG p-adjust method | `BH`/`fdr`, exposed in config | Both appear; use one default but keep configurable. |
| limma design style | no-intercept group design `~0 + group` | Common in original limma code. |
| DESeq2 design | `~ group` | Used in GSE261830. |
| Enrichment organism | human (`org.Hs.eg.db`, KEGG `hsa`) | All reviewed analyses are human. |
| GO ontology | `BP` | Most GO enrichment uses biological process. |
| GSEA `minGSSize` | `10` | Repeated in GSEA blocks. |
| KM grouping | median split, labels Low/High | Repeated in survival blocks; should remain configurable. |
| KM plot | p-value on, risk table on, CI off | Matches `ggsurvplot` snippets. |
| Expression plot stats | default `wilcox.test`, paired false | Most clinical expression comparisons use Wilcoxon; paired true only when explicitly configured. |
| Missing font family | system default or configurable `Arial` | Source does not specify font family. |

## 8. Missing or Ambiguous Parameters

| Area | Missing / ambiguous parameter |
|---|---|
| `bioinformatics_original_codes.md` | Contains placeholders rather than pasted R code; concrete extraction depended on `.txt` files. |
| GEO preprocessing | Exact platform-specific annotation columns and duplicate probe strategy vary; prototypes use manual detection and sometimes max expression for duplicate symbols. |
| Normalization | GSE171483 expression appears preprocessed; GSE60542 uses log expression in helper code; GSE261830 rounds expression for DESeq2, but whether input is raw counts or TPM requires confirmation. |
| Correlation filters | Positive/negative gene cutoff is not consistently visible; sign-based separation is clear, numeric correlation and p/FDR cutoffs need confirmation. |
| Enrichment universe | Background/universe genes are not specified. |
| Enrichment p-value defaults | Some calls omit `pvalueCutoff`/`qvalueCutoff`, relying on clusterProfiler defaults. |
| GSEA term filtering | Keyword lists and `adj.P.Val < 0.25` term selection are paper-specific and need user-configured presets. |
| Survival | KM plot export filenames and dimensions are not consistently defined; stage recoding requires explicit mapping. |
| TCGA downloads | Retry/chunk behavior varies by prototype; exact file manifest and output asset schema should be normalized before implementation. |
