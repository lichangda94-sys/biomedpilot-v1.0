# Bioinformatics B7: Bulk Immune / TME Signature Scoring

Date: 2026-05-20

## Summary

B7 adds a lightweight bulk expression immune / TME signature scoring workflow. The module accepts prepared expression matrices from existing TCGA, GTEx, GEO/local readiness surfaces, checks value type suitability, scores selected exploratory signatures, and writes score/coverage/sample-summary artifacts plus a draft report.

This stage does not implement CIBERSORT, xCell, ESTIMATE, TIMER, EPIC, quanTIseq, DEG/GSEA execution, KM, Cox, log-rank, or clinical conclusions.

## Implemented Scope

- Added `app/bioinformatics/immune_infiltration/` service package.
- Added built-in exploratory immune / TME signatures:
  - immune cell marker signatures
  - TME / inflammation signatures
  - checkpoint single-gene signatures
- Added GMT import support for custom signature resources.
- Added input readiness for TCGA / GTEx / standardized expression assets.
- Added value type policy:
  - recommended: TPM, normalized expression, log2 expression
  - usable: FPKM, FPKM-UQ, normalized microarray expression
  - blocked by default: raw counts and unknown value type
- Added scoring methods:
  - `mean_zscore`
  - `mean_expression`
- Added optional value transform:
  - `none`
  - `log2_x_plus_1`
- Added B7 output artifacts:
  - `immune_score_matrix.tsv`
  - `signature_gene_coverage.tsv`
  - `sample_score_summary.tsv`
  - `immune_scoring_manifest.json`
  - `immune_scoring_receipt.json`
  - `immune_tme_scoring_report.md`
- Added result index registration as testing-level exploratory result.
- Added linkage preflight for:
  - group comparison
  - target gene correlation
  - clinical association / basic OS preflight
- Added analysis task center entry: `免疫浸润 / TME评分`.
- Added dedicated UI page for B7 scoring and preview.
- Added unified readiness integration under `immune_infiltration_readiness`.

## Output Location

B7 scoring runs are stored under:

```text
analysis/immune_infiltration/runs/<run_id>/
```

The B7 module does not write expression source files and does not modify TCGA/GTEx acquisition artifacts.

## Boundary Rules

- Bulk signature score is exploratory and does not equal true immune cell proportions.
- Raw counts are blocked by default for scoring.
- TCGA + GTEx are not automatically merged.
- GTEx is not automatically used as TCGA normal control.
- Clinical linkage is preflight only; B7 does not run KM/Cox/log-rank.
- Score generation does not automatically trigger DEG/GSEA/report-ready.

## Tests Added

- `tests/bioinformatics/test_immune_infiltration.py`
- `tests/ui/test_bioinformatics_immune_infiltration_pages.py`

Coverage includes:

- built-in and GMT signature resource handling
- readiness allow/block policy
- project readiness capability matrix row
- scoring output manifest/receipt/result index
- raw/unknown value type blocking
- linkage preflight
- exploratory report draft generation
- analysis task center UI entry
- B7 page run/preview behavior
- workspace navigation to B7 page

## Validation

Checks passed during implementation:

```text
python3 -m pytest tests/bioinformatics/test_immune_infiltration.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_immune_infiltration_pages.py -q
git diff --check: passed
python3 -m pytest tests/bioinformatics -q: 304 passed
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q: 174 passed
python3 -m app.main --smoke-test: passed
```
