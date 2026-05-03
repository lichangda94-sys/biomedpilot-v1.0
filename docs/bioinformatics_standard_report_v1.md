# Bioinformatics Standard Report v1

## Goal

Standard report v1 turns the extracted GEO / TCGA / GTEx parameter inventory into a reusable reporting layer. It does not run real analyses and does not replace existing runner logic. Its job is to collect an analysis result or artifact manifest, attach the software defaults used by the project, write a reproducibility configuration snapshot, and generate a stable Markdown report.

## Report Structure

The report template is `reporting/templates/bioinformatics_standard_report.md.j2` and includes:

- Project Summary
- Dataset Summary
- Input Files
- Sample Annotation and Grouping
- Analysis Workflow
- Parameter Summary
- Differential Expression Results
- Target Gene Expression Results
- Correlation Results
- Enrichment / GSEA Results
- Survival Analysis Results
- Figures
- Tables
- Warnings and Limitations
- Reproducibility Information
- Software Configuration Snapshot

Missing result sections render as `Not available in this run` so partial analyses can still produce a report.

## Parameter Sources

The configuration files are derived from:

- `docs/bioinformatics_original_code_parameter_inventory.md`
- `docs/bioinformatics_software_parameter_schema_draft.md`
- `docs/bioinformatics_parameter_extraction_todo.md`

The source documents were extracted from original GEO / TCGA / GTEx thesis code. Paper-specific genes, datasets, drugs, subgroup names, and pathway keywords remain examples only.

## Configuration Files

Configuration lives under `config/bioinformatics/`:

- `plotting_defaults.yaml`: plot format, DPI, figure sizes, theme, colors, and common plot settings.
- `analysis_defaults.yaml`: organism, gene panel example, ingestion defaults, comparisons, DEG, expression comparison, and correlation defaults.
- `enrichment_defaults.yaml`: gene ID mapping, enrichment universe, GO/KEGG/GSEA defaults, and output naming.
- `survival_defaults.yaml`: OS columns, median split, KM, Cox, and forest plot defaults.
- `package_requirements.yaml`: R package inventory and report v1 dependency behavior.

Unified defaults:

- `p_adjust_method: BH`
- `dpi: 300`
- default figure size: `8 x 6`
- square figure size: `5 x 5`
- enrichment figure size: `7 x 6`
- large figure size: `10 x 8`
- `font_family: system_or_sans`
- `output_format: png`
- optional output formats: `pdf`, `tiff`, `svg`

`ADIPOR1`, `ADIPOR2`, `CDH13`, `APPL1`, and `LDLR` appear only in `example_gene_panel` and are not software defaults.

## Implemented

- Lightweight report generator: `reporting/bioinformatics_standard_report.py`.
- Markdown template rendering without requiring Jinja2.
- YAML config loading without requiring PyYAML, using a small built-in YAML subset parser with optional PyYAML support when installed.
- Standard warnings for known analysis risks.
- Config snapshot writing to `results/reproducibility/config_snapshot/bioinformatics_config_snapshot.yaml` or the same relative path under a caller-supplied output directory.
- Tests that do not require GEO, TCGA, GTEx, R, network access, or downloads.

## Placeholders

- DOCX/PDF export is not implemented in this repository-level report v1. If a caller requests those formats, Markdown is still generated and a warning is recorded.
- The report accepts already-produced result summaries, figures, and tables. It does not calculate DEG, enrichment, correlation, or survival results.
- The template is intentionally conservative and Markdown-first. More detailed tables can be added after real runner manifests stabilize.

## Runner Integration Still Needed

Future runner work should pass a normalized `analysis_result` or `artifact_manifest` with:

- project and dataset metadata
- input file paths and sample grouping summaries
- analysis workflow steps
- parameter overrides actually used in the run
- DEG, target gene, correlation, enrichment/GSEA, and survival summaries
- figure and table artifacts
- warnings from validation and execution

The report layer should remain downstream of analysis execution. Real GEO / TCGA / GTEx runners should not import report defaults as biological assumptions; they should pass explicit run parameters into the report.
