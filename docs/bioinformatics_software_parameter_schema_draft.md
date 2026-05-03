# Bioinformatics Software Parameter Schema Draft

This draft translates extracted thesis-code parameters into configurable software settings. Values shown under `defaults` are candidates, not fixed biology logic.

## 1. Project-Level Schema

```yaml
project:
  analysis_id: string
  organism:
    species: Homo sapiens
    orgdb: org.Hs.eg.db
    kegg_code: hsa
  output:
    root_dir: results
    overwrite: false
    save_intermediate: true
    table_format: csv
    figure_formats: [png]
    dpi: 300
```

## 2. Dataset Ingestion

```yaml
datasets:
  - dataset_id: GSE_or_TCGA_or_custom
    source_type: geo | tcga | gtex | local_matrix
    source:
      accession: null
      local_expression_file: null
      local_sample_annotation_file: null
      local_clinical_file: null
      tcga_project: null
      clinical_xml_dir: null
    expression:
      matrix_orientation: genes_by_samples
      gene_id_column: SYMBOL
      sample_id_columns: []
      gene_id_type: SYMBOL | ENSEMBL | ENTREZ | PROBE
      remove_ensembl_version: true
      duplicate_gene_strategy: max_expression | mean_expression | first | error
      transform:
        log2: auto
        pseudo_count: 1
      normalization:
        method: already_normalized | raw_counts | tpm | cpm | gcrma | custom
    sample_annotation:
      group_column: null
      sample_id_column: null
      cleaning_rules:
        strip_quotes: true
        strip_prefix_regex: "^X|\\.$|^\\."
```

## 3. Gene Panels

The following panel is an example from the thesis code only and must not be fixed software logic.

```yaml
gene_panels:
  - name: thesis_example_adiponectin_lipid_panel
    genes: [ADIPOR1, ADIPOR2, CDH13, APPL1, LDLR]
    editable: true
  - name: user_custom
    genes: []
    editable: true
```

## 4. Comparisons

```yaml
comparisons:
  - comparison_id: string
    dataset_id: string
    group_column: treatment
    case_group: treatment
    control_group: control
    contrast_expression: case_group - control_group
    paired:
      enabled: false
      subject_id_column: null
    subset:
      enabled: false
      filters: []
    labels:
      case_label: Case
      control_label: Control
```

Examples that should stay as user-configured comparison records:

```yaml
examples:
  - comparison_id: GSE171483_Dabrafenib_vs_control
    group_column: treatment
    case_group: Dabrafenib
    control_group: control
  - comparison_id: GSE171483_Vemurafenib_vs_control
    group_column: treatment
    case_group: Vemurafenib
    control_group: control
  - comparison_id: GSE261830_Selpercatinib_vs_control
    group_column: group
    case_group: selpercatinib
    control_group: control
  - comparison_id: GSE60542_N1_vs_N0
    group_column: n_stage_clean
    case_group: N1
    control_group: N0
```

## 5. DEG Analysis

```yaml
deg:
  method: limma | deseq2
  limma:
    design: no_intercept_group
    normalize_between_arrays: false
    contrast: "{case_group} - {control_group}"
    top_table:
      number: Inf
      sort_by: P
      adjust_method: fdr
  deseq2:
    design_formula: "~ group"
    count_rounding: true
    contrast: ["group", "{case_group}", "{control_group}"]
    lfc_shrinkage:
      enabled: false
      type: null
  thresholds:
    logfc_abs: 1
    adjusted_p_value: 0.05
    raw_p_value: null
  output:
    write_all_results: true
    write_significant_results: true
    filename_template: "{dataset_id}_DEG_{case_group}_vs_{control_group}.csv"
```

## 6. Expression Comparison

```yaml
expression_comparison:
  genes: []
  group_column: null
  paired:
    enabled: false
    subject_id_column: null
  test_method: wilcox.test
  alternative: two.sided
  p_label:
    mode: p.signif
    star_thresholds:
      "***": 0.001
      "**": 0.01
      "*": 0.05
      ns: default
  plot:
    type: boxplot
    show_jitter: true
    jitter_width: 0.2
    point_size: 1.5
    point_alpha: 0.7
    outlier_shape: null
    theme: theme_bw
    base_size: 14
    legend_position: none
    dimensions:
      width: 5
      height: 5
      units: in
```

## 7. Correlation Analysis

```yaml
correlation:
  target_genes: []
  matrix_scope:
    subset_filters: []
  method: pearson
  min_samples: null
  p_adjust:
    enabled: true
    method: fdr
  split_gene_sets:
    enabled: true
    positive:
      correlation_min: 0
      p_adjusted_max: null
    negative:
      correlation_max: 0
      p_adjusted_max: null
  output:
    correlation_table_template: "{target_gene}_correlation_all.csv"
    positive_gene_table_template: "{target_gene}_positive_correlated_genes.csv"
    negative_gene_table_template: "{target_gene}_negative_correlated_genes.csv"
  plot:
    type: dotplot
    x: correlation
    y: gene
    size: minus_log10_p
    color: correlation
    theme: theme_bw
    base_size: 14
    dimensions:
      width: 7
      height: 6
      units: in
```

## 8. Enrichment Analysis

```yaml
enrichment:
  input_gene_sets:
    source: deg_up_down | correlation_positive_negative | user_gene_list
    id_type: SYMBOL
    convert_to: ENTREZID
  universe:
    mode: expressed_genes
    genes: null
  go:
    enabled: true
    function: enrichGO
    ontology: BP
    p_adjust_method: BH
    pvalue_cutoff: 0.05
    qvalue_cutoff: 0.2
    readable: true
  kegg:
    enabled: true
    function: enrichKEGG
    organism: hsa
    p_adjust_method: BH
    pvalue_cutoff: 0.05
    qvalue_cutoff: 0.2
  deg_filters_for_enrichment:
    strict:
      logfc_abs: 1
      adjusted_p_value: 0.05
    relaxed_directional:
      logfc_abs: 0.5
      adjusted_p_value: 0.05
  plot:
    type: dotplot
    show_category: 15
    x: minus_log10_p_adjust
    y: description
    size: count
    theme: theme_bw
    base_size: 13
    dimensions:
      width: 8
      height: 6
      units: in
```

## 9. GSEA

```yaml
gsea:
  enabled: false
  ranking:
    metric: logFC | log2FoldChange | correlation
    decreasing: true
    id_type: SYMBOL
    convert_to: ENTREZID
  go:
    enabled: true
    function: gseGO
    ontology: BP
    key_type: ENTREZID
  kegg:
    enabled: true
    function: gseKEGG
    organism: hsa
  parameters:
    min_gene_set_size: 10
    max_gene_set_size: 500
    pvalue_cutoff: 0.5
    p_adjust_method: BH
  term_selection:
    mode: top_n | keyword | all_significant
    top_n: 10
    keywords: []
    adjusted_p_value_max: 0.25
  plot:
    function: gseaplot2
    dimensions:
      width: 8
      height: 6
      units: in
    dpi: 300
    filename_template: "GSEA_{keyword}_{index}_{safe_description}.png"
```

## 10. Survival Analysis

```yaml
survival:
  enabled: false
  input:
    time_column: OS.time
    event_column: OS
  grouping:
    method: median_split
    genes: []
    high_label: High
    low_label: Low
    high_rule: "value >= median(value, na.rm = TRUE)"
  km:
    function: survfit
    plot_function: ggsurvplot
    p_value: true
    risk_table: true
    confidence_interval: false
    palette: ["#00BFC4", "#F8766D"]
    x_label: "Time (days)"
    y_label: "Overall Survival Probability"
  cox:
    models:
      - type: univariate
        variables: []
      - type: multivariate
        variables: []
    default_covariates: [stage_group, age, gender]
    output_columns: [variable, HR, CI_lower, CI_upper, p_value]
  forest_plot:
    point_size: 3
    errorbar_height: 0.2
    reference_hr: 1
    reference_linetype: dashed
    theme: theme_minimal
    base_size: 14
    legend_position: top
```

## 11. Plot Defaults

```yaml
plot_defaults:
  device: png
  dpi: 300
  font_family: null
  theme: theme_bw
  base_size: 14
  colors:
    case: "#E64B35"
    control: "#4DBBD5"
    significant: "red"
    not_significant: "grey"
    up: "red"
    down: "blue"
    neutral: "grey"
    annotation: "black"
  volcano:
    width: 8
    height: 6
    point_alpha: 0.6
    point_size: 1.5
    show_threshold_lines: true
    label_size: 4
  enrichment:
    width: 8
    height: 6
    show_category: 15
  survival:
    width: 7
    height: 6
  qc:
    width_px: null
    height_px: null
```

## 12. Required UI/Software Guardrails

- Treat all dataset IDs, target genes, drug names, mutation labels, and pathway keywords as user/project configuration.
- Never hard-code `ADIPOR1`, `ADIPOR2`, `CDH13`, `APPL1`, or `LDLR` outside example presets.
- Validate whether an expression matrix is raw counts before enabling DESeq2; reject TPM/normalized matrices unless the user explicitly overrides.
- Require explicit group mapping before running contrasts.
- Keep local source paths out of generated configs; store them only as imported project file references.
- Record package versions and parameters in `results/reproducibility/`.
