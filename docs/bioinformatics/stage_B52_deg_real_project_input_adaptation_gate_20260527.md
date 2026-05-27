# B52 DEG Real Project Input Adaptation Gate

## Audit

Current DEG readiness already checked sample/group alignment and probe mapping through `deg_ready`, but the Analysis Center did not expose a dedicated real-project adaptation contract. The missing contract made it hard to review value type, gene identifier type, allowed method families, blockers, warnings, and repair guidance before formal DEG.

## Implementation

- Added `biomedpilot.deg_real_project_input_adaptation_gate.v1`.
- The gate consumes only the standardized resolver package plus the DEG-ready package.
- It reports `value_type`, `gene_id_type`, `sample_alignment_status`, `gene_mapping_status`, `allowed_methods`, `method_recommendations`, `blockers`, `warnings`, and `repair_guidance`.
- It blocks missing DEG packages, non-DEG packages, unknown value type, unsupported value type, GEO probe/ID_REF without mapping, DEG-ready blockers, and TPM/FPKM/log values requested for count-model DEG.
- The Analysis Center now shows a formal DEG gate row for real-project input adaptation.

## Boundaries

- No formal execution path was added.
- No GSEA, survival, plotting, report-ready, or clinical conclusion behavior was added.
- Repair guidance is advisory only; formal input must be regenerated through standardized assets.

## Stage Result

B52 is implemented as a gate and UI preview layer. It improves reviewability for GEO / TCGA / GTEx / local matrix inputs without changing formal execution semantics.
