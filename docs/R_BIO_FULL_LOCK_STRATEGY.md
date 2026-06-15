# r-bio-full Lock Strategy

Generated: `2026-06-14`

## Current Lock Profile

The first `r-bio-full` lock profile is `survival_minimal_v1`.

This profile exists only to support survival full/formal pre-migration work. It is an isolated environment evidence step, not a declaration that survival has migrated and not a declaration that global full analysis is ready.

Required top-level packages:

- `renv`
- `survival`
- `jsonlite`
- `data.table`
- `digest`
- `ggplot2`
- `broom`
- `htmltools`

## Scope Boundary

`survival_minimal_v1` intentionally excludes pathway, immune, spatial, docking, and molecular dynamics dependencies.

It does not include:

- ReactomePA or Reactome databases
- MSigDB, GO, KEGG, or OrgDb resources
- Seurat, CellChat, GSVA, or spatial transcriptomics stacks
- AutoDock Vina
- GROMACS
- large Bioconductor annotation databases

The profile therefore does not make enrichment, immune infiltration, spatial transcriptomics, docking, or molecular dynamics production-ready.

## Package Source

The default CRAN source is:

```text
https://cloud.r-project.org
```

An operator may replace this with an internal RSPM or CRAN mirror, but that choice must be recorded in the lock generation metadata and r-bio-full environment evidence.

## Evidence Policy

The lock must be generated inside the isolated `r-bio-full` Docker image by `scripts/full_env/generate_r_bio_full_lock.sh --execute`.

It must not be generated through app-dev, a request handler, a frontend flow, or the default developer environment.

Evidence can pass only when:

- `renv/renv.bio-full.lock` has non-empty `Packages`.
- `BioMedPilotPolicy.status` is `restored`.
- `BioMedPilotPolicy.lock_profile` is `survival_minimal_v1`.
- the required package set is present in the lock and installed package inventory.
- the lock hash, Docker digest, renv restore evidence, R session info, and package inventory validate.

Passing `r-bio-full` environment evidence is still only one prerequisite. Full production activation remains blocked until resource/tool locks and formal module migration evidence also pass.

## Future Profiles

Later profiles must be added deliberately rather than folded into `survival_minimal_v1`:

- `enrichment_full_v1`: pathway and annotation resources such as Reactome, MSigDB, GO, KEGG, and OrgDb.
- `immune_full_v1`: immune signatures, heatmap/reporting dependencies, and any required annotation resources.
- `spatial_full_v1`: spatial transcriptomics packages and spatial reference resources.
- `chem_full_v1`: docking tools and templates.
- `chem_gpu_full_v1`: molecular dynamics and GPU-capable chemistry execution.

Each future profile needs its own environment/resource evidence and must keep runtime package installation and runtime resource download forbidden.
