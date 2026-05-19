# Bioinformatics B6.6 TCGA Clinical Metadata Acquisition and Expression-Clinical Mapping

Date: 2026-05-19

## Scope

B6.6 adds TCGA clinical metadata acquisition from the GDC `/cases` endpoint and maps case-level clinical data back to B6.4 expression sample mappings. This stage does not execute survival analysis, Cox regression, Kaplan-Meier, log-rank tests, clinical plotting, DEG, GSEA, or report-ready clinical conclusions.

## Implemented

- `TCGAClinicalMetadataBuilder` reads the latest B6.4 expression build manifest and `tcga_sample_file_mapping.csv`, queries `/cases` by `case_id` / `case_submitter_id`, and builds expression-matched clinical artifacts.
- Project-only clinical preview is supported when no B6.4 expression build exists. It is marked `project_clinical_preview_only` and cannot claim expression-clinical readiness.
- Outputs are written as:
  - `tcga_clinical_raw_cases.json`
  - `tcga_clinical_case_table.tsv`
  - `tcga_clinical_diagnosis_table.tsv`
  - `tcga_clinical_followup_table.tsv`
  - `tcga_clinical_survival_table.tsv`
  - `tcga_clinical_mapping_table.tsv`
  - `tcga_clinical_build_manifest.json`
  - `acquisition/clinical_receipts/*.json`
  - `acquisition/clinical_manifests/*.json`
- Only the raw GDC cases JSON is registered as a clinical source file for traceability. Derived TSVs and manifests stay in the clinical artifact manifest and are not treated as expression source files.
- Basic OS is derived from GDC clinical fields only:
  - `OS_event = 1` when vital status is `Dead`
  - `OS_event = 0` when vital status is `Alive`
  - death time prefers `days_to_death`
  - alive time prefers `days_to_last_follow_up`, then maximum follow-up days
- TCGA readiness now reports `tcga_clinical_readiness`, clinical gate status, expression-clinical mapping status, and basic OS readiness.
- TCGA UI now includes `获取 TCGA 临床信息` and displays case count, matched case/sample counts, OS availability, death events, artifact paths, and warnings.

## Boundaries

- TCGA clinical metadata does not merge with GTEx.
- B6.6 does not reproduce TCGA-CDR DSS/DFI/PFI endpoints.
- Clinical metadata can feed readiness and later preflight configuration, but it does not auto-run survival, DEG, GSEA, or report generation.
