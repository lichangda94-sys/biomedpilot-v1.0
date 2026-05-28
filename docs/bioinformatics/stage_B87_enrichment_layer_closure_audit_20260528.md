# B87 Enrichment Layer Closure Audit

## Scope

B87 closes the current enrichment layer implementation from B81-B86.

Covered stages:

- B81 resource registry and resource gate.
- B82 external R enrichment backend capability gate.
- B83 controlled R ORA/GSEA adapters.
- B84 execution parameter and confirmation gate.
- B85 result review and export.
- B86 plot artifact and section report package gate.

## Implemented

Added `app/bioinformatics/enrichment_e2e_audit.py` with `audit_enrichment_layer_acceptance(...)`.

The audit checks:

- resource registry availability;
- backend gate detect-first policy;
- selected formal ORA/GSEA result;
- review exclusion of non-formal results;
- plot gate pass/block status with clear reasons;
- section report gate scope;
- non-formal outputs not promoted;
- no clinical interpretation.

## Current Capability Matrix

| Area | Status |
| --- | --- |
| Resource registry | Implemented |
| External R backend detection consumption | Implemented |
| Controlled ORA | Implemented with `clusterProfiler::enricher` adapter |
| Controlled preranked GSEA | Implemented with `fgsea` adapter |
| Parameter confirmation gate | Implemented |
| Result review/export | Implemented |
| Formal enrichment SVG artifact | Implemented for controlled section artifacts |
| Enrichment section report package | Implemented |
| Full integrated report upgrade | Not enabled |
| ReactomePA execution | Blocked until package/resource gates pass |
| msigdbr catalog execution | Blocked until package/resource gates pass |
| Clinical interpretation | Not implemented and forbidden |

## Boundary Decisions

- `formal_computed_result` enrichment entries are allowed only after controlled adapter gates and output validation pass.
- Imported/testing/exploratory/preflight results are excluded from review/report package promotion.
- Plot artifacts inherit formal enrichment source semantics.
- Section report packages are `formal_enrichment_only`, not full integrated reports.
- ReactomePA/msigdbr remain visible blocked capabilities until external engine preparation is complete.

## Validation

Focused audit tests cover:

- passing closure audit for a formal ORA section package;
- imported result exclusion;
- blocking when no formal enrichment result exists.

## Conclusion

B81-B87 are ready as an internal controlled enrichment layer candidate for ORA and preranked GSEA, excluding ReactomePA/msigdbr-dependent paths. The next safe stage is ReleaseBuild/MainLine carry-over alignment or UI execution control wiring for the already-gated ORA/GSEA path.
