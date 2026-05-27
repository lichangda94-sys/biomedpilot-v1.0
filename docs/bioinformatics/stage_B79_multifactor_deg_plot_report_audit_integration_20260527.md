# B79 Multi-factor DEG Plot / Report / Audit Integration

## Audit

Formal DEG plot and audit paths were already semantics-driven and accepted formal DEG result index entries, but report-ready validation only recognized the two-group formal DEG confirmation file. Multi-factor DEG results also had blank group mean columns, which blocked DEG table validation.

## Implementation

- Multi-factor limma/DESeq2/edgeR fixture tables now include numeric `case_mean` and `control_mean`.
- Formal DEG plot artifacts now carry `multifactor_design_provenance` when the source result has formula/contrast/covariates/batch fields.
- DEG production audit packages now write `manifests/multifactor_design_provenance.json`.
- Formal DEG section report-ready gate now accepts multi-factor parameter confirmation manifests for multi-factor DEG results.
- Formal DEG report markdown and provenance include formula, contrast, covariates, batch variables, and backend method.

## Boundary

B79 allows controlled multi-factor formal DEG results to enter existing DEG volcano/summary heatmap, audit package, and DEG section report pathways. It does not enable GSEA, survival, full clinical interpretation, or clinical conclusions.
