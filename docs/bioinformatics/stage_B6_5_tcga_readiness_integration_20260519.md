# Bioinformatics B6.5 TCGA readiness integration report

Date: 2026-05-19

## Scope

B6.5 connects B6.4 TCGA expression build outputs to the existing data check and preparation readiness flow. This stage does not download files, does not parse GDC quantification files again, does not merge TCGA with GTEx, and does not execute DEG/GSEA.

## Implemented

- Added TCGA B6.4 build manifest discovery inside `project_readiness`.
- Reads B6.4 acquisition records with `download_status=tcga_expression_matrix_built`.
- Reads the B6.4 expression build manifest and validates:
  - raw counts primary matrix path
  - sample metadata path
  - gene annotation path
  - expression sample columns
  - sample metadata sample IDs
  - sample type counts
- Adds TCGA B6.4 assets into readiness available inputs:
  - `tcga_expression_matrix`
  - `expression_matrix`
  - `raw_count_matrix`
  - `tcga_sample_metadata`
  - `sample_metadata`
  - `gene_annotation`
- Adds `tcga_readiness` to readiness report and dataset readiness summary.
- Adds TCGA value type policy:
  - raw counts: `count`, default DEG input
  - TPM: display only, not default DEG input
  - FPKM: display only, not default DEG input
  - FPKM-UQ: display only, not default DEG input
- Checks default tumor/normal grouping:
  - `Primary Tumor` vs `Solid Tissue Normal` becomes a default grouping candidate when both are present.
  - If tumor/normal is insufficient, status becomes expression display/manual group only.
- Keeps DEG execution blocked:
  - B6.5 only lets data move toward DEG preflight.
  - comparison config confirmation is still required.
  - no automatic DEG/GSEA execution is enabled.
- Keeps TCGA + GTEx boundary:
  - readiness report records that TCGA B6.4 outputs do not auto-merge with GTEx.
  - TCGA + GTEx still requires independent GTEx ingestion and a batch correction plan.

## Standardization Candidate Alignment

B6.4 primary TCGA expression matrix is now carried through source manifest evidence as a B6.4 raw counts matrix. Standardization candidate collection reports its expression value type as `count`, while TPM/FPKM/FPKM-UQ remain display-side assets in the B6.5 policy.

## Tests Added

- TCGA B6.4 readiness summary identifies a valid tumor/normal build as `ready_for_deg_preflight_candidate`.
- Readiness report includes TCGA available inputs and value type policy.
- Differential expression row still requires comparison config confirmation.
- B6.4 raw counts expression matrix becomes a standardization candidate with value type `count`.
- Tumor-only TCGA build is downgraded to expression display/manual grouping and reports insufficient tumor/normal grouping.

## Verification

Targeted verification passed:

- `python3 -m compileall app/bioinformatics/project_readiness.py app/bioinformatics/project_recognition.py app/bioinformatics/standardization_confirmation.py app/bioinformatics/project_standardization.py`
- `python3 -m pytest tests/bioinformatics/test_tcga_expression_builder.py -q`

Full regression should be run before commit:

- `git diff --check`
- `python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `python3 -m app.main --smoke-test`
