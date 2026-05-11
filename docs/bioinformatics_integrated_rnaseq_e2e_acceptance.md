# Integrated RNA-seq XLSX E2E Acceptance

## Test Data Structure

Stage 2.4 uses a compact integrated RNA-seq workbook shaped like the user import case:

- `gene_id` with mouse Ensembl IDs such as `ENSMUSG00000026193`.
- 21 count columns: `A1_count` through grouped sample columns such as `H3_count`.
- 21 FPKM columns: matching `A1_fpkm` through `H3_fpkm`.
- DEG triplets per comparison: `<comparison>_log2FoldChange`, `<comparison>_pvalue`, `<comparison>_padj`.
- Gene annotation fields: `gene_name`, `gene_chr`, `gene_start`, `gene_end`, `gene_strand`, `gene_length`, `gene_biotype`, `gene_description`, `tf_family`.

## Recognition Result Summary

The recognition report identifies the integrated table as:

- `semantic_type`: `rna_seq_integrated_result_table`
- UI label: `RNA-seq 综合表达结果表`
- Species: `Mus musculus`
- Species group: `mouse`
- Gene ID type: `ensembl_mouse_gene_id`

Recognized content blocks:

- `gene_identifier`: mouse Ensembl gene IDs with `ENSMUSG` prefix.
- `count_expression_matrix`: 21 count sample columns, 7 inferred groups, about 3 replicates per group.
- `fpkm_expression_matrix`: 21 FPKM sample columns matching count sample IDs.
- `deg_comparisons`: at least 10 complete DEG comparisons.
- `gene_annotation`: coordinate, biotype, description, and TF family fields.

The recognized sample columns exclude DEG statistic columns and annotation numeric fields. In particular, `gene_start`, `gene_end`, `gene_length`, `*_log2FoldChange`, `*_pvalue`, and `*_padj` do not appear as expression sample columns.

## Standardized Assets Summary

Standardization reads `recognized_data/current.json`, then loads the current run's `recognition_report.json` and `recognized_files.json`.

For an integrated RNA-seq table, the registry now exposes multiple assets instead of a single vague matrix:

- `count_matrix`: recommended for differential expression, normalization, and quality control.
- `normalized_expression_matrix` with `value_type=fpkm`: recommended for expression visualization, heatmap, correlation, and gene expression browsing.
- `deg_result_table`: recommended for volcano plot, DEG filtering, enrichment input, and result browsing.
- `gene_annotation`: recommended for symbol mapping, description display, protein-coding filtering, and report annotation.
- `gene_identifier_metadata`: recommended for species inference, ID tracking, and ID conversion planning.

The standardization page summarizes this as a split from one integrated RNA-seq table into count matrix, FPKM matrix, imported DEG result table, and gene annotation. It also warns that re-running differential expression should use count data, while FPKM is suitable for expression display, heatmap, and correlation.

## Analysis Task Center Capabilities

The task center derives user-facing task groups from standardized assets:

- 可直接使用已有结果: view DEG results, DEG filtering, volcano plot, and enrichment input.
- 需要确认分组后运行: recompute differential expression, sample QC, and count matrix normalization.
- 表达数据探索: expression heatmap, sample correlation, and candidate gene expression browsing.
- 注释与报告: gene annotation browsing, protein-coding filtering, and report annotation.

For count matrices without confirmed group config, differential expression recomputation is `ready_with_group_confirmation`, not fully ready. Mouse projects show the note that the data are suitable for animal model analysis, mechanism exploration, and method validation; human cohort integration is not presented as a recommended path.

## Result Browser DEG Comparisons

Imported DEG assets are exposed as selectable comparisons. Example selectors include:

- `PFFvsPBS`
- `MMP3vsPBS`
- `MK2206vsPBS`
- `PI103vsPBS`
- `PDTCvsPBS`
- `PF271vsPBS`
- `MK2206vsPFF`
- `PI103vsPFF`
- `PDTCvsPFF`
- `PF271vsPFF`
- `MMP3vsPFF`

Selecting a comparison builds a unified DEG table with user-facing columns:

- `gene_id`
- `gene_name`
- `log2FC`
- `p value`
- `adjusted p value`
- `gene_biotype`
- `gene_description`

The UI labels imported DEG results as `差异结果来源：导入表格中的已有结果`, avoiding wording that implies BioMedPilot recomputed the analysis.

## Mouse Enrichment Species Check

For `Mus musculus` / `mouse` assets, imported DEG views use mouse enrichment species metadata. The result browser does not default to human enrichment background. Gene lists are generated as:

- up genes
- down genes
- all significant genes

The gene list builder prefers `gene_name` / gene symbol and keeps Ensembl IDs when symbols are unavailable, preserving the need for ID conversion.

## UI Text Fixes

Stage 2.4 tightened the visible text without changing page architecture:

- Recognition type cells now prefer `RNA-seq 综合表达结果表` without exposing `tabular_text_file` in the main label.
- Recognition cards include content-block summaries for count, FPKM, DEG comparisons, and annotation.
- Standardization summary explains the integrated table split and count-vs-FPKM usage.
- Task center adds a grouped user-facing capability summary above the technical task table.
- Result browser labels imported DEG comparisons in Chinese and shows source, thresholds, stats, gene lists, and mouse enrichment species.

Technical fields remain available in details areas or existing tables where needed for debugging.

## Remaining Limits

- Stage 2.4 does not add a new plotting engine; volcano plot support remains an input-ready path unless the existing plotting layer is wired later.
- Enrichment execution is not implemented here; this stage validates species-safe input preparation and gene list generation.
- Historical recognition records still remain isolated from the current recognition result. Viewing history exposes technical details and does not repopulate the current result card.

## Verification Commands

Required verification:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
- `git diff --check`
