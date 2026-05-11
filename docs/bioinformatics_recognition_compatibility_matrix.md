# Bioinformatics Recognition Compatibility Matrix

## Current Support Scope

BioMedPilot recognition currently handles small to medium local bioinformatics inputs through file extension, filename hints, tabular header profiling, GEO Series Matrix markers, and RNA-seq content block detection.

The recognition report remains backward compatible with v1 fields such as `recognized_type`, `recognized_roles`, `detected_assets`, and `content_profile`. For richer RNA-seq tables, file records can also expose `semantic_type`, `species`, `species_group`, `gene_id_type`, and `content_blocks`.

Standardization reads only `recognized_data/current.json` and the referenced run directory. Historical recognition records are not used unless the user explicitly sets one as current.

## Compatibility Matrix

| Input type | Typical fields | Recognition result | content_blocks / assets | Later workflow | Risk |
|---|---|---|---|---|---|
| Integrated RNA-seq result table | `gene_id`, `*_count`, `*_fpkm`, `*_log2FoldChange`, `*_pvalue`, `*_padj`, `gene_name`, `gene_biotype`, `gene_description` | `semantic_type=rna_seq_integrated_result_table`; bottom kind stays table-compatible | Blocks: gene identifier, count matrix, FPKM matrix, DEG comparisons, gene annotation. Assets: `count_matrix`, `normalized_expression_matrix`, `deg_result_table`, `gene_annotation`, `gene_identifier_metadata` | Standardization, count-based recompute DEG after group confirmation, imported DEG browsing, volcano input, enrichment input, report annotation | DEG/statistic and annotation numeric columns must not enter `sample_columns` |
| Pure count matrix | `gene_id`, `A1_count`, `A2_count`, `B1_count`, `B2_count` or numeric sample columns | `raw_count_matrix` or expression candidate; `_count` suffix gives explicit count block | Block: `count_expression_matrix`; asset: `count_matrix` | Recompute DEG, normalization, QC; requires group config or group confirmation | Count columns without group metadata must not be treated as fully ready for DEG |
| FPKM / TPM matrix | `gene_id`, `A1_fpkm`, `A2_fpkm`, `A1_tpm`, `A2_tpm` | Normalized expression candidate | Blocks: `fpkm_expression_matrix`, `tpm_expression_matrix`; asset: `normalized_expression_matrix` with `value_type=fpkm` or `tpm` | Heatmap, correlation, expression browse | Not recommended for DESeq2/edgeR-style recompute DEG |
| Single comparison DEG result | `gene_id`, `gene_name`, `log2FoldChange`, `pvalue`, `padj` | `differential_result_table` | Block: `deg_comparisons` with `comparison_name=imported_deg_results`; asset: `deg_result_table` | Imported DEG result browsing, filtering, volcano input, enrichment input | If `padj` is missing, filtering must fall back to p value with a warning |
| Multi-comparison wide DEG table | `A_vs_B_log2FoldChange`, `A_vs_B_pvalue`, `A_vs_B_padj`, `C_vs_D_*` | DEG result table or integrated result component | Block: `deg_comparisons` with one entry per comparison | Comparison selector, per-comparison DEG view, enrichment input | Incomplete comparisons are retained and marked `is_complete=false` |
| Gene annotation table | `gene_id`, `gene_name`, `gene_chr`, `gene_start`, `gene_end`, `gene_strand`, `gene_biotype`, `gene_description` | `gene_annotation` | Blocks: gene identifier and gene annotation; assets: `gene_annotation`, `gene_identifier_metadata` | Symbol mapping, description display, protein-coding filter, report annotation | Coordinate columns are numeric but must not become sample columns |
| Sample metadata / phenotype table | `sample_id`, `group`, `condition`, `batch`, `sex`, `age` | `sample_metadata`, optionally with clinical role | Asset: `sample_metadata` or `phenotype_metadata` when eligible | Group confirmation and sample annotation review | Age/sex fields should not force expression matrix detection |
| Comparison config | `comparison_name`, `case_group`, `control_group`, `method` | `comparison_config` | Asset: comparison config role when eligible | Supports DEG readiness and group setup | Must not be interpreted as expression matrix |
| GEO Series Matrix | `!Series_title`, `!Series_geo_accession`, `!Sample_geo_accession`, `!Sample_characteristics_ch1`, `!series_matrix_table_begin` | `geo_series_matrix_container` | Assets: expression matrix, sample metadata, platform reference hint, phenotype/clinical hints as detected | Recognition handoff, sample metadata review, expression candidate review | Organism should come from GEO metadata; missing organism must remain unknown, not default human |
| Unknown or ambiguous table | `id`, `value`, `note` | `unknown` | No analysis-ready asset | User must provide clearer data or manually annotate | Must warn that no clear expression, DEG, or sample annotation structure was detected |

## Recognition Rules

- Table headers are parsed for CSV, TSV, TXT, gzipped text tables, and XLSX workbooks.
- `ENSMUSG...` infers `Mus musculus`, `mouse`, and `ensembl_mouse_gene_id`.
- `ENSG...` infers `Homo sapiens`, `human`, and `ensembl_human_gene_id`.
- `ENSMUST...` infers `Mus musculus`, `mouse`, and `ensembl_mouse_transcript_id`.
- `_count` / `_counts` columns become count expression blocks.
- `_fpkm` columns become FPKM expression blocks.
- `_tpm` columns become TPM expression blocks.
- `<comparison>_(log2FoldChange|log2fc|logFC|pvalue|p_value|padj|fdr|qvalue)` columns become DEG comparison blocks.
- Unprefixed `log2FoldChange`, `pvalue`, and `padj` columns become a single imported DEG comparison named `imported_deg_results`.
- Gene annotation fields include coordinates, strand, length, biotype, description, gene symbol/name, and TF family.
- Sample metadata requires sample identifiers plus grouping or phenotype attributes.

## Sample Column Guardrails

The following fields are explicitly excluded from expression `sample_columns`:

- Gene coordinates and metadata: `gene_start`, `gene_end`, `gene_length`, `gene_chr`, `gene_strand`, `gene_biotype`, `gene_description`.
- DEG statistics: `*_log2FoldChange`, `*_pvalue`, `*_padj`, `log2FoldChange`, `pvalue`, `padj`, `P.Value`, `adj.P.Val`.
- Other annotation/statistical fields detected by DEG or annotation header rules.

## Later Workflow Readiness

- Count matrices can support recomputed DEG, normalization, and QC, but recomputed DEG is `ready_with_group_confirmation` unless a confirmed comparison config exists.
- FPKM/TPM matrices support expression visualization, heatmap, correlation, and gene expression browsing.
- Imported DEG results support browsing, threshold filtering, volcano input, and enrichment input.
- Gene annotation supports symbol mapping, report annotation, and protein-coding filtering.
- Sample metadata supports group confirmation and sample annotation review.
- Unknown tables do not create analysis-ready assets.

## Regression Test Coverage

Automated coverage lives in `tests/bioinformatics/test_recognition_compatibility_matrix.py`.

| Test case | Covered behavior |
|---|---|
| Integrated RNA-seq result table | Semantic type, mouse Ensembl inference, count/FPKM/DEG/annotation blocks, sample column guardrails |
| Pure count matrix | Count block, human Ensembl inference, count asset, group confirmation readiness |
| FPKM / TPM matrix | Normalized expression blocks and assets with `value_type=fpkm/tpm`, DEG limitation text |
| Single comparison DEG | Imported DEG block and asset, mouse enrichment species |
| Multi-comparison wide DEG | Comparison count and incomplete comparison tracking |
| Gene annotation | Annotation asset and coordinate-field exclusion |
| Sample metadata | Sample metadata classification and expression matrix avoidance |
| Comparison config | Comparison config classification and expression matrix avoidance |
| GEO Series Matrix | GEO roles, organism parsing, non-human default safety |
| Unknown table | Unknown classification, warning text, no analysis-ready asset |

## Known Limits

- This matrix uses minimal simulated files, not full public datasets.
- GEO organism parsing currently covers standard `!Series_organism_ch1` and `!Sample_organism_ch1` metadata lines.
- Single-comparison DEG tables without an explicit comparison label are normalized to `imported_deg_results`.
- TPM and FPKM are registered as normalized expression assets; downstream modules decide which visual workflows are implemented.
