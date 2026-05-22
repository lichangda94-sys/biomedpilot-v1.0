# B18 Multi-factor DEG Contract and Preflight Gate

Date: 2026-05-22

Scope: ReleaseBuild candidate branch only. This stage implements a contract/preflight layer for future multi-factor DEG and does not enable formal multi-factor DEG execution.

## Implementation Summary

- Added `app/bioinformatics/deg_engine/multifactor_gate.py`.
- Added a preflight manifest schema: `biomedpilot.deg_multifactor_preflight.v1`.
- Added design config support for:
  - sample table
  - primary factor
  - case/control contrast
  - categorical covariates
  - continuous covariates
  - batch variables declared as covariates
- Added design matrix generation with intercept, one-hot categorical encoding, continuous covariate columns, rank calculation and full-rank validation.
- Added method/value type policy checks for:
  - `limma` normalized/log expression policy
  - `limma_voom` count-model policy
  - `deseq2` raw count policy
  - `edger` raw count policy
- Added Analysis Center exposure through:
  - `multi_factor_deg_gate`
  - formal DEG gate row: `Multi-factor DEG preflight`
  - deep analysis capability map row: `Multi-factor DEG design`

## Hard Boundaries

- No formal multi-factor DEG executor was added.
- No R, Bioconductor, limma, DESeq2 or edgeR invocation was added.
- No dependency installation action was added.
- No result index entry is written.
- `result_semantics` remains `preflight_only`.
- `formal_execution_enabled` remains `False`.
- `report_ready_eligible` remains `False`.
- Existing two-group controlled DEG, ORA, GSEA and KM/Cox boundaries remain unchanged.

## Preflight Blockers

The B18 gate blocks at least the following cases:

- missing multi-factor design config
- missing sample table
- duplicate or invalid sample ids
- missing/same case-control group
- empty case or control group
- missing or mismatched contrast
- missing covariate values
- non-numeric continuous covariate values
- unsupported variable type
- insufficient sample count for design matrix
- non-full-rank design matrix
- unknown value type
- DESeq2/edgeR/limma-voom requested for TPM/FPKM/FPKM-UQ/normalized/log expression values
- missing count matrix for DESeq2/edgeR
- missing count matrix for limma-voom
- probe/ID_REF mapping still blocked by DEG-ready gene mapping state

## UI Behavior

Analysis Center now shows multi-factor DEG as a preflight-only capability. The default state is blocked with `multi_factor_design_config_missing` until a design config is provided. A `design_ready` preflight state still does not enable a formal button because B19 adapter/output/result schema gates are required first.

## Test Coverage

Focused tests added:

- `tests/bioinformatics/test_deg_multifactor_preflight_gate.py`
- Updated `tests/bioinformatics/test_analysis_ui_state.py`
- Updated `tests/bioinformatics/test_analysis_capability_map.py`
- Updated `tests/ui/test_bioinformatics_workflow_pages.py`

Covered cases:

- legal full-rank limma normalized-expression design returns `design_ready`
- non-full-rank design is blocked
- insufficient sample count is blocked
- TPM/FPKM into DESeq2/edgeR count models is blocked
- missing count matrix for DESeq2/edgeR is blocked
- limma normalized-expression policy is distinguished from limma-voom count policy
- no formal result semantics are accepted by the B18 preflight validator
- UI continues to show multi-factor DEG as disabled/preflight-only

## Next Stage

Recommended next stage: B19 R/Bioconductor adapter contract planning. B19 should remain scoped to adapter input/output contracts and runtime capability detection before any formal multi-factor DEG execution is considered.
