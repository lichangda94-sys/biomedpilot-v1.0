# Local Dataset Standardization Design

This audit defines the minimum design for importing local sequencing-company delivery folders into standard project assets. It is documentation only. It does not parse FASTQ/BAM/CRAM files, run alignment, run quantification, run DEG/enrichment analysis, upload data, delete source files, or change `geo_workflow.py`.

## Delivery Folder Patterns

Sequencing vendors commonly deliver project folders with names such as:

- `RawData`: raw FASTQ files, checksum files, and sequencing lane folders.
- `CleanData`: trimmed or filtered FASTQ files.
- `QC`: FastQC/MultiQC reports, adapter reports, base quality reports, and sequence summary files.
- `Mapping`: BAM/SAM alignment outputs, mapping statistics, genome index notes, and aligner logs.
- `Expression`: count matrices, TPM/FPKM matrices, normalized expression matrices, and gene annotation tables.
- `Differential`: DEG tables, comparison-specific result folders, volcano/heatmap inputs, and method notes.
- `Enrichment`: GO/KEGG/GSEA result tables and plots.
- `Report`: PDF/HTML/Word reports and summary spreadsheets.

These names are not reliable enough to imply analysis readiness. A scanner should treat them as weak hints and record reasons for every detected file candidate.

## Local Delivery vs GEO Structure

Local delivery folders are usually project-centric and may contain already processed matrices, QC reports, and vendor-specific reports. GEO packages are submission-centric and may split data into series matrix files, supplementary archives, platform annotation, sample annotations, and raw data links.

Key differences:

- local folders may have complete processed results but incomplete public metadata.
- file names may use vendor conventions rather than GEO/GSM/GPL identifiers.
- sample names in matrices may not match clinical/sample metadata exactly.
- gene identifiers may be symbols, Ensembl ids, probe ids, or vendor-specific ids.
- local reports may describe processing software, genome build, and annotation versions, but these details may not be machine-readable.

## Current Supported Inputs

The first standardization phase should support processed result files only:

- raw count matrix
- TPM matrix
- FPKM matrix
- normalized expression matrix
- sample metadata
- gene annotation
- QC report
- DEG result

These files are enough to build a standard local dataset package for readiness checks and later Module 5 analysis planning. They are not enough to reproduce alignment or quantification from raw reads.

## Explicitly Unsupported

The current phase should not support:

- FASTQ/BAM/CRAM content parsing
- alignment
- featureCounts execution
- Salmon execution
- FastQC/MultiQC execution
- DESeq2/edgeR/limma execution
- GEO automatic submission
- production download/upload behavior
- source file deletion, movement, or overwrite

FASTQ files can be detected as candidates for reporting and GEO submission readiness, but their contents are not parsed.

## Recommended Subtasks

1. Delivery scanner:
   Read a delivery directory tree and classify file candidates by filename, extension, size, and path hints without reading large file contents.

2. Selected import plan:
   Record which detected files the user selected as expression matrix, sample metadata, gene annotation, and QC reports.

3. Local dataset standardizer:
   Copy or lightly normalize selected processed files into a project-standard asset directory without modifying the original delivery folder.

4. Validation report:
   Check standard assets for sample id alignment, gene id column presence, missing values, duplicate genes, non-negative expression values, and count-matrix compatibility.

5. GEO submission readiness checker:
   Report whether the standardized local package has the processed files and metadata needed for a likely manual GEO submission.

6. Standard asset compatibility contract:
   Define the shared output contract used by GEO, TCGA/GTEx, and local sequencing-company adapters.

## Recommended Output Layout

```text
project_dir/local_datasets/{dataset_slug}/
  delivery_scan_report.json
  selected_import_plan.json
  standardized/
    expression_matrix.csv
    sample_metadata.csv
    gene_annotation.csv
    local_dataset_manifest.json
    validation_report.json
    qc/
      ...
```

The original vendor delivery directory remains read-only from the application's perspective. Standardized assets are copied into the project directory and can be regenerated from the import plan.

## Mock Practical Test Strategy

Use fake/temp delivery folders with small files:

- one count matrix with matching sample metadata.
- one TPM or FPKM matrix with matching metadata.
- one folder with ambiguous filenames that should not be over-classified.
- one folder containing FASTQ filenames that are detected but not parsed.
- one folder with sample mismatch, duplicate gene ids, missing values, and small groups.

The mock test should verify detection, selected import plan validation, standard asset output, validation report contents, and GEO submission readiness without using real GEO/TCGA data or running any analysis tool.

## Next Minimal Scope

The next implementation step should be a local delivery scanner that identifies candidate processed files and raw FASTQ names without reading large file contents or modifying user files.

## Local Delivery Scanner Foundation

`scan_delivery_folder(root_dir)` recursively lists files and classifies candidates with weak path/name hints only. It records `DeliveryFileCandidate` entries in a `DeliveryScanReport` and supports these candidate types:

- `raw_count_matrix`
- `tpm_matrix`
- `fpkm_matrix`
- `normalized_expression_matrix`
- `sample_metadata`
- `gene_annotation`
- `differential_expression_result`
- `qc_report`
- `raw_fastq`
- `unknown`

The scanner is intentionally conservative. Unknown CSV/TXT files are not treated as expression matrices without a matching filename or path hint. FASTQ files are detected for readiness reporting but their contents are not parsed. The scanner does not delete, move, overwrite, normalize, copy, or analyze source files.

## Selected Import Plan Foundation

`SelectedImportPlan` records the user-confirmed files that should become standard assets later:

- dataset slug
- selected expression matrix
- expression data type
- selected sample metadata
- selected gene annotation
- selected QC reports
- warnings, errors, and validity

Supported expression data types are `raw_count_matrix`, `tpm_matrix`, `fpkm_matrix`, and `normalized_expression_matrix`. A missing expression matrix or unsupported expression type makes the plan invalid. Missing sample metadata is currently a warning, not a hard block, because early local deliveries may need a manual metadata repair step before standardization. The plan builder does not read large files, execute analysis, standardize assets, or modify original delivery files.

## Local Dataset Standardizer Foundation

`standardize_local_dataset(project_dir, scan_report, import_plan)` copies selected processed files into the standard project layout:

```text
project_dir/local_datasets/{dataset_slug}/
  delivery_scan_report.json
  selected_import_plan.json
  standardized/
    expression_matrix.csv
    sample_metadata.csv
    gene_annotation.csv
    local_dataset_manifest.json
```

`gene_annotation.csv` is optional. The `LocalDatasetManifest` records dataset slug, source type, detected files, selected source paths, expression data type, sample count, gene count, creation time, and warnings. This foundation copies selected processed files only; it does not modify source delivery files, execute analysis, parse FASTQ/BAM/CRAM contents, or run QC/alignment/DEG tools.

## Local Dataset Validation Report

The standardizer also writes `standardized/validation_report.json` for standardized local assets. The report records:

- sample id match status between expression matrix columns and `sample_metadata.csv`.
- missing expression value count.
- duplicated gene id count.
- group count and per-group sample sizes from the `group` metadata column.
- expression value type.
- count-based compatibility.
- warnings and errors.

The validation report checks for a `gene_id` or `gene_symbol` first column, sample id mismatch, missing values, duplicated genes, negative expression values, and small groups with `n < 3`. Raw count matrices are count-compatible only when expression values are mostly integer-like. TPM, FPKM, and normalized matrices are explicitly not count-based compatible. The report is validation-only: it does not execute analysis, repair data, change original files, or run DEG tools.

## GEO Submission Readiness Checker

`GeoSubmissionReadinessReport` checks whether a standardized local package is likely ready for manual GEO submission review. It reports processed expression availability, sample metadata availability, gene annotation, raw FASTQ presence, sample-to-raw-file mapping, reference genome information, annotation version information, processing software information, sample id consistency, privacy review warnings, and readiness level.

This checker is not a submission tool. It does not upload data, contact GEO, parse raw FASTQ/BAM/CRAM contents, run analysis, or modify standardized assets.

## Standard Asset Compatibility Contract

All dataset adapters should eventually converge on the same standard asset contract:

- `GEOAdapter -> standard assets`
- `TCGA_GTEx_Adapter -> standard assets`
- `SequencingCompanyAdapter -> standard assets`
- `GEOReadyLocalPackageAdapter -> standard assets`

The unified output should contain:

- `StandardExpressionMatrix`
- `StandardSampleMetadata`
- `StandardGeneAnnotation`
- `StandardDatasetManifest`
- `StandardValidationReport`
- `StandardQCReport` optional

The current local standardizer already writes the first concrete local version of this contract as:

- `standardized/expression_matrix.csv`
- `standardized/sample_metadata.csv`
- `standardized/gene_annotation.csv` optional
- `standardized/local_dataset_manifest.json`
- `standardized/validation_report.json`

Future GEO, TCGA/GTEx, sequencing-company, and GEO-ready local package adapters should normalize into the same conceptual assets before Module 5 analysis planning. Module 5 should consume the standard expression matrix, sample metadata, gene annotation, manifest, and validation report rather than source-specific folder structures. The UI should display validation and GEO submission readiness from these standard assets without mutating original files.

## v0.33 Local Dataset Standardization Baseline

`v0.33-local-dataset-standardization` records the current MVP baseline:

- local delivery scanner.
- selected import plan.
- local dataset standardizer.
- local dataset validation report.
- GEO submission readiness checker.
- standard asset compatibility contract.

The baseline supports processed result files only: count matrix, TPM matrix, FPKM matrix, normalized expression matrix, sample metadata, gene annotation, QC report references, and DEG result candidates. It explicitly does not support FASTQ/BAM/CRAM content parsing, alignment, FastQC/MultiQC execution, DESeq2/edgeR/limma execution, GEO automatic submission, production downloader changes, or `geo_workflow.py` changes.

Recommended next tasks are a mock local delivery practical test, controlled real GEO readiness test design, or UI local dataset import readiness display.
