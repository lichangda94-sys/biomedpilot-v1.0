# Bioinformatics Parameter Extraction TODO

## Completed In This Pass

- Read the scaffold `/Users/changdali/Documents/code/bioinformatics_original_codes.md`.
- Confirmed the scaffold does not contain pasted R code and relies on adjacent original-code `.txt` files for concrete extraction.
- Extracted dataset-level purpose and major functions for GSE171483, GSE261830, GSE60542, TCGA-THCA, TCGA+GTEx, and prototype GEO/TCGA download workflows.
- Extracted recurring plotting parameters: file formats, sizes, dpi, themes, colors, legends, axes, significance annotations, volcano threshold lines, enrichment/GSEA filenames, and survival plot settings.
- Extracted statistical parameters for limma, DESeq2, expression comparison tests, correlation, GO/KEGG enrichment, GSEA, Kaplan-Meier, and Cox models.
- Extracted R package dependencies and mapped them to software modules.
- Drafted input/output contracts and a configurable software parameter schema.
- Flagged paper-specific genes, GEO IDs, drug groups, mutation groups, TCGA project, local paths, manual label offsets, and keyword filters as non-hard-coded logic.

## Still Missing / Needs Manual Confirmation

| Priority | Item | Reason |
|---|---|---|
| High | Paste or generate a real `reference/bioinformatics_original_codes.md` inside the repository if that is the intended canonical reference. | The requested path does not exist in the current repo; the available markdown is outside the repo and is a template. |
| High | Confirm whether `GSE261830_expression_by_gene.csv` contains raw counts or TPM/normalized expression. | The original DESeq2 code uses `round(expr)`, which is invalid for normalized expression unless intentionally overridden. |
| High | Define canonical duplicate gene/probe handling. | Original GEO preprocessing uses different approaches, including max expression for duplicate symbols. |
| High | Confirm correlation gene-set cutoffs. | Code clearly separates positive/negative correlations, but numeric correlation and p/FDR thresholds are inconsistent or absent. |
| High | Define enrichment universe/background. | Original `enrichGO/enrichKEGG` calls generally omit `universe`. |
| High | Standardize p-adjust method. | Both `BH` and `fdr` appear. |
| Medium | Decide default enrichment q-value cutoff. | Values `0.05`, `0.2`, and clusterProfiler defaults appear. |
| Medium | Confirm whether GSEA exploratory cutoff `pvalueCutoff = 0.5` should be a software default, an exploratory mode, or paper-only behavior. | Source uses permissive cutoffs for pathway exploration. |
| Medium | Define clinical stage recoding and N-stage cleaning rules as schema records. | Original code contains thesis-specific stage grouping. |
| Medium | Define TCGA clinical XML field priority and fallback tags. | XML parsing logic searches multiple fields for BRAF/RET/PTC and survival information. |
| Medium | Standardize plot export for survival/KM and forest plots. | Several plots are printed but not saved. |
| Medium | Choose default font family. | Original code does not specify font family. |
| Low | Convert prototype GEO "bad" code into reusable ingestion requirements only. | It includes exploratory candidate datasets, manual selections, QC/network prototypes, and should not be copied into production. |
| Low | Add package version capture. | Original code does not capture session info. |

## Suggested Next Documentation Tasks

1. Create a canonical repo-local `reference/bioinformatics_original_codes.md` or document that `/Users/changdali/Documents/code/*.txt` are the current source archive.
2. Build a small parameter manifest per dataset/contrast using the schema draft:
   - `GSE171483_Dabrafenib_vs_control`
   - `GSE171483_Vemurafenib_vs_control`
   - `GSE261830_Selpercatinib_vs_control`
   - `GSE60542_N1_vs_N0`
   - `GSE60542_PTC_vs_Normal`
   - `GSE60542_BRAF_vs_nonBRAF`
   - `GSE60542_RET_vs_nonRET`
   - `TCGA_THCA_survival`
   - `TCGA_GTEx_thyroid_tumor_vs_normal`
3. Add validation rules for unsafe analysis choices:
   - DESeq2 requires raw integer counts.
   - Paired tests require subject IDs.
   - Survival requires non-missing time and event columns.
   - Enrichment requires valid gene ID conversion rate above a configured threshold.
4. Decide which plot defaults belong in global settings and which belong per analysis type.
5. Add a "paper example presets" section that can load the thesis gene panels without making them fixed logic.

## Do Not Do In This Task

- Do not copy original R code into production modules.
- Do not add a runner.
- Do not change UI.
- Do not hard-code `ADIPOR1`, `ADIPOR2`, `CDH13`, `APPL1`, or `LDLR` as software logic.
- Do not change existing tests unless a future implementation task requires it.
