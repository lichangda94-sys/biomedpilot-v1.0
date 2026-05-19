# Bioinformatics B6.4 TCGA expression quantification builder report

Date: 2026-05-19

## Scope

B6.4 consumes only B6.3 TCGA/GDC raw acquisition records. It does not trigger new downloads, does not touch GTEx, and does not advance B5.19.

The implemented goal is to parse downloaded TCGA RNA-seq gene expression quantification files and build local, internally recognizable TCGA expression assets while keeping the analysis gate at data check/preparation.

## Implemented

- Added a B6.4 builder service: `app/bioinformatics/data_sources/tcga_expression_builder.py`.
- Reads B6.3 acquisition records, source manifests, receipts, and download manifests.
- Identifies GDC gene expression quantification files from B6.3 `source_files`.
- Parses GDC STAR - Counts style TSV/TSV.GZ fields:
  - `gene_id`
  - `gene_name`
  - `gene_type`
  - raw counts (`unstranded` or equivalent)
  - TPM
  - FPKM
  - FPKM-UQ
- Builds matrix outputs by sample:
  - primary raw counts matrix
  - TPM matrix
  - FPKM matrix
  - FPKM-UQ matrix
  - gene annotation table
  - sample metadata table
  - sample barcode/case/file mapping table
- Writes a B6.4 expression build manifest and the existing TCGA prepare manifest.
- Registers the built expression assets as a new acquisition record with:
  - `download_status=tcga_expression_matrix_built`
  - `ready_for_recognition=pending_data_check`
  - `analysis_gate_status=pending_data_check`
- Keeps B6.3 raw file records out of ready counts until the B6.4 build succeeds.
- Keeps B6.4 output out of direct DEG/GSEA ready; the next step remains unified data check and preparation.

## B6.2/B6.3 Compatibility Updates

- B6.2 TCGA plan entries now persist full case/sample mapping fields:
  - `case_ids`
  - `case_submitter_ids`
  - `sample_ids`
  - `sample_submitter_ids`
  - `sample_types`
- B6.3 download file records and events carry those mapping fields forward so B6.4 can build sample metadata without another GDC request.
- Older B6.3 records with missing sample barcodes can still be parsed, but the builder records warnings and uses a file-derived fallback sample identifier.

## UI

The TCGA data source page now includes:

- `构建 TCGA 表达矩阵` button (`buildTcgaExpressionMatrixButton`)
- B6.4 status panel (`tcgaExpressionBuildStatus`)
- build summary showing:
  - parsed/source file counts
  - sample/gene counts
  - counts matrix path
  - sample metadata path
  - sample mapping path
  - build manifest path

The button is enabled only after a B6.3 raw TCGA record exists.

## Status Semantics

- B6.3 raw files:
  - status: `TCGA 原始文件已获取，等待 B6.4 构建表达矩阵`
  - ready count: `0`
- B6.4 built expression assets:
  - status: `TCGA 表达矩阵已构建，等待数据检查与准备`
  - ready count: included for data check/preparation
  - missing content: `统一数据检查与准备`

## Tests Added

- `tests/bioinformatics/test_tcga_expression_builder.py`
  - verifies plan mapping persistence
  - verifies B6.3 raw records are consumed
  - verifies counts/TPM/gene annotation/sample metadata/sample mapping outputs
  - verifies registration as `pending_data_check`
  - verifies missing B6.3 raw records are rejected
- `tests/ui/test_bioinformatics_workflow_pages.py`
  - verifies B6.4 UI button/status behavior
  - verifies built TCGA datasets move to the data check queue

## Verification

Targeted checks passed during implementation:

- `python3 -m pytest tests/bioinformatics/test_tcga_expression_builder.py tests/bioinformatics/test_tcga_download_executor.py -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`
- `python3 -m compileall app/bioinformatics/data_sources/tcga_expression_builder.py app/bioinformatics/workflow_pages.py app/bioinformatics/data_sources/tcga_preview.py app/bioinformatics/data_sources/tcga_download_executor.py`

Full regression should still be run before commit:

- `git diff --check`
- `python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `python3 -m app.main --smoke-test`
