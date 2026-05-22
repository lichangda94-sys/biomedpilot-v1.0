# B19 limma / DESeq2 / edgeR Adapter Contract and Formal Runtime Gate

Date: 2026-05-22

Scope: ReleaseBuild candidate branch. This stage adds the Bioinformatics-side R/Bioconductor adapter contract and runtime gate for future limma, DESeq2 and edgeR execution. It does not invoke R, does not install R/Bioconductor packages and does not produce formal multi-factor DEG results.

## Implementation Summary

- Added `app/bioinformatics/deg_engine/r_adapter_contract.py`.
- Added adapter contract schema: `biomedpilot.r_deg_adapter_contract.v1`.
- Added runtime gate schema: `biomedpilot.r_deg_runtime_gate.v1`.
- Added method contracts for:
  - `limma`
  - `limma_voom`
  - `deseq2`
  - `edger`
- Added external capability keys:
  - `runtime.r.available`
  - `runtime.bioconductor.available`
  - `package.r.limma.available`
  - `package.r.deseq2.available`
  - `package.r.edger.available`
- Added method-specific input policies and output schemas.
- Added result registration bundle validation for future runtime outputs.
- Added Analysis Center rows for R adapter contracts.
- Updated deep analysis capability map so limma/DESeq2/edgeR show B19 adapter gate blockers instead of being presented as complete.

## Method-Specific Output Schemas

`limma` / `limma_voom` require:

- `feature_id`
- `logFC`
- `AveExpr`
- `t`
- `P.Value`
- `adj.P.Val`

Optional:

- `gene_symbol`
- `B`

`DESeq2` requires:

- `feature_id`
- `baseMean`
- `log2FoldChange`
- `lfcSE`
- `stat`
- `pvalue`
- `padj`

Optional:

- `gene_symbol`

`edgeR` requires:

- `feature_id`
- `logFC`
- `logCPM`
- `PValue`
- `FDR`

Optional:

- `gene_symbol`
- `LR`

## Runtime Gate Behavior

The gate blocks when:

- external engine capability registry is missing
- R runtime is missing
- Bioconductor is missing
- the selected method package is missing
- B18 multi-factor preflight is not `design_ready`
- method family does not match B18 preflight method policy
- dependency snapshot is missing or not passed
- output table is missing method-specific required columns
- execution failed but a formal result is attempted
- dependency provenance is missing from the future result index entry

When all capability and input gates pass, B19 can mark the method as `ready_for_external_runtime_execution`, but this stage still does not call R directly from Bioinformatics. Future execution must be implemented through an audited external engine handoff.

## Formal Result Boundary

`result_semantics=formal_computed_result` is allowed only after all of the following are true:

- external runtime execution succeeded
- method-specific output schema validation passed
- dependency snapshot is present and passed
- result index v2 registration fields are complete
- validation status is `passed`

Failed executions, schema mismatches, testing outputs, preflight outputs and imported outputs cannot be upgraded to `formal_computed_result`.

## UI Behavior

Analysis Center now shows R adapter contract rows for limma, limma-voom, DESeq2 and edgeR. In the current ReleaseBuild candidate these rows remain blocked by `external_engine_capability_registry_missing` because E1/E2/E5/E6 are not yet supplied to Bioinformatics as a capability snapshot.

## Tests

Added:

- `tests/bioinformatics/test_r_deg_adapter_contract.py`

Updated:

- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Covered cases:

- R missing blocks the runtime gate
- Bioconductor missing blocks the runtime gate
- method package missing blocks the runtime gate
- invalid B18 input preflight blocks the runtime gate
- limma, DESeq2 and edgeR output schemas are method-specific
- failed execution cannot generate a formal result
- successful execution bundle requires formal semantics and dependency provenance
- UI shows B19 adapter gate blockers without presenting limma/DESeq2/edgeR as completed

## Next Stage

Recommended next stage: B20 Multivariate Cox Contract and Gated Execution, or an external engine E1/E2/E5/E6 implementation pass if the product goal is to actually provide R/Bioconductor capability snapshots before any R-backed DEG execution.
