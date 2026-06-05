# External Analysis Resources Handoff

This directory is the handoff area for externally prepared full-analysis
resource-lock evidence.

It is not a runtime download cache for user requests. Do not place Reactome,
MSigDB, GO, KEGG, organism databases, spatial references, CellChatDB, AutoDock
Vina bundles, GROMACS installs, docking templates, molecular dynamics templates,
or other large scientific resources in this repository.

Allowed tracked files here are small evidence manifests and text logs that prove
resources were prepared and locked outside the user request flow. A resource is
not active until:

- `analysis/registry/resource_lock_evidence.json` references the evidence.
- The evidence payload passes `analysis/schemas/output/resource_lock_evidence.schema.json`.
- `validate_analysis_resource_manifest()` reports full resource readiness.

Expected evidence files should record resource id, version, source, hash,
license, cache path, approved modules, evidence files, and
`runtime_download_allowed=false`.

Current status: no full resource evidence is registered; full mode remains
blocked.
