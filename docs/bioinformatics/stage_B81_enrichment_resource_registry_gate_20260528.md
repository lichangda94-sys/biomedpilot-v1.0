# B81 Enrichment Resource Registry / Resource Gate

## Audit

The existing gene set resource manager can import, select, validate, download, and cache GMT resources for GSEA preparation. However, ORA/GSEA production hardening needs an explicit shared resource gate before execution and reporting work continues.

Observed gap:

- Resources were managed as GSEA-oriented local GMT assets.
- ORA/GSEA did not share a formal resource gate payload.
- User-imported GMT resources did not consistently expose checksum/file size in the registry.
- There was no strict gate requiring species, gene ID type, version, source, license, checksum, and local path provenance.

## Implementation

- Added `app/bioinformatics/enrichment_resources.py`.
- Added `biomedpilot.enrichment_resource_registry.v1`.
- Added `biomedpilot.enrichment_resource_gate.v1`.
- The registry snapshot records:
  - known resource catalog for Reactome / GO / KEGG / MSigDB / custom GMT
  - resource id/name
  - collection type
  - species
  - gene id type
  - source type/name/url
  - license note
  - version
  - checksum and checksum algorithm
  - local path
  - gene set count
  - allowed analysis types
- The resource gate blocks:
  - no selected/explicit resource
  - unsupported analysis type
  - unavailable/missing/invalid resource
  - species mismatch
  - gene ID type mismatch
  - missing source name
  - missing license note
  - missing version
  - missing checksum
  - missing gene set count
  - missing local path
- User-imported GMT resources now record checksum and file size.
- Known catalog entries expose user-triggered download/import policy; the gate does not silently fetch any resource.

## Boundary

B81 is a resource contract only. It does not run ORA, run GSEA, download resources automatically, install external dependencies, generate plots, create report-ready packages, or interpret pathway biology.
