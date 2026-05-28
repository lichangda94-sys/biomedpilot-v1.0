# B82 External Enrichment R Backend Gate

## Scope

This stage consumes the external R enrichment backend detection payload and turns it into a Bioinformatics Analysis contract gate. It does not install R packages, download gene-set resources, run formal ORA/GSEA, generate formal plots, or create report-ready output.

The current external engine detection reports R 4.4.2 arm64 with core enrichment packages available:

- clusterProfiler
- fgsea
- DOSE
- enrichplot
- ggplot2
- AnnotationDbi
- org.Hs.eg.db
- GO.db
- KEGGREST

ReactomePA and msigdbr are still missing. B82 therefore gates capabilities independently instead of treating the global detector status as an all-or-nothing blocker.

## Implemented Contract

Added `app/bioinformatics/enrichment_backend.py` with `build_enrichment_backend_gate(...)`.

The gate:

- reads `r_enrichment_backend_detection.json`;
- verifies schema `biomedpilot.external_enrichment_r_backend_detection.v1`;
- surfaces Rscript path, version, architecture, package versions and packaging policy;
- keeps `install_action=none_detect_first_only`;
- keeps `packaging_policy=external_runtime_not_bundled`;
- returns `semantic_boundary=backend_gate_only_not_enrichment_execution`;
- evaluates selected capabilities rather than the detector's global status alone.

## Capability Behavior

Passed while ReactomePA/msigdbr are missing:

- `ora_enricher`
- `ora_go`
- `ora_kegg`
- `gsea_preranked_fgsea`
- `gsea_preranked_clusterprofiler`
- `enrichment_plot_dotplot`
- `enrichment_plot_barplot`
- `gsea_plot_curve`

Still blocked:

- `ora_reactome` because ReactomePA is missing.
- `msigdbr_gene_set_catalog` because msigdbr is missing.

The gate records ReactomePA/msigdbr as visible blockers for their own capabilities, but they do not block core ORA/GSEA work that does not require them.

## UI Exposure

Analysis Center dependency rows now include external R enrichment backend status and package versions. Rows remain detect-first only and expose no install action.

Formal GSEA/ORA execution is not enabled by this stage. Existing formal action boundaries remain unchanged.

## Boundaries

- No automatic package installation.
- No R package bundling into the app.
- No Reactome or MSigDB activation until their packages and resource policy pass later gates.
- No GSEA/survival/clinical expansion.
- No report-ready bypass.

## Validation

Focused tests cover:

- core ORA passing while ReactomePA/msigdbr are missing;
- GO/KEGG/GSEA/plot capability gates passing independently;
- Reactome and msigdbr capability gates blocking;
- missing, invalid and schema-mismatched detection payloads blocking gracefully;
- Analysis Center dependency rows showing enrichment backend detect-first state.
