# R Analysis Remediation Plan

Date: 2026-06-04

## Goal

Move BioMedPilot analysis capabilities toward:

```text
main app + task system + isolated analysis worker/service + standard result package
```

Do not install full R/Bioconductor/spatial/chem dependencies in the default development environment. Do not download large databases during user requests.

## Phase R0: Boundary Contract

Status: started.

Completed in this audit:

- `analysis/registry/analysis_modules.json`
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/result_package.schema.json`
- `analysis/runners/run_module.R`
- `analysis/fixtures/inputs/mock_analysis_input.json`
- `analysis/fixtures/outputs/mock_result_package/**`
- `analysis/resources/manifest.json`
- `app/analysis_runtime/registry.py`
- `app/analysis_runtime/standard_package.py`
- `app/analysis_runtime/task_bridge.py`
- `analysis/modules/<module_id>/module.json`
- `docker/Dockerfile.app-dev`
- `docker/Dockerfile.r-bio-core`
- `docker/Dockerfile.r-bio-full`
- `docker/Dockerfile.r-spatial-full`
- `docker/Dockerfile.r-chem-full`
- `docker/Dockerfile.r-chem-gpu`
- `renv/renv.app.lock`
- `renv/renv.bio-core.lock`
- `renv/renv.bio-full.lock`
- `renv/renv.spatial-full.lock`
- `renv/renv.chem-full.lock`

Remaining:

- Add per-module mock fixtures.
- Wire one current analysis module through the bridge.

Update: the first result package validator and mock-mode backend adapter now exist under `app/analysis_runtime/`.

## Phase R1: Task-System Bridge

Scope:

- Add a Python bridge that submits module jobs by writing `module_input.json`.
- The bridge calls the standard worker only through task execution, not directly from UI.
- The UI consumes `result.json`, `provenance.json`, and artifact manifest metadata.

Acceptance:

- One module can run `mock` mode through the task system. **Started: generic registered modules can produce mock standard packages.**
- Output package includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, `logs/`.
- No R installation is required.

## Phase R2: Enrichment Lite Worker

Recommended first module because controlled ORA/GSEA R adapters already exist.

Scope:

- Wrap existing enrichment controlled adapters behind the standard worker.
- Use lightweight local TERM2GENE fixtures.
- No ReactomePA/msigdbr full resources in lite mode.

Acceptance:

- `mock` and `lite` pass.
- `full` remains blocked until resource locks and full env exist.
- Provenance records R version, package versions, input hash, parameter hash, seed, and command.

## Phase R3: Survival / Clinical R-Native Worker

Scope:

- Migrate survival, univariate, and multivariate clinical association behind the same worker interface.
- Keep clinical conclusion disabled.
- Require standard result package outputs.

Acceptance:

- `mock` passes without R.
- `lite` passes with lightweight R packages/data.
- `full` blocked until container/renv is approved.

## Phase R4: DEG R Worker Alignment

Scope:

- Wrap limma/DESeq2/edgeR multi-factor code behind the same standard worker.
- Preserve existing result index v2 and DEG audit package, but emit standard result package too.

Acceptance:

- No Python service embeds long-running R execution as a UI request side effect.
- All outputs have standard package metadata.

## Phase R5: Environment Split

Required environment artifacts:

```text
docker/Dockerfile.app-dev
docker/Dockerfile.r-bio-core
docker/Dockerfile.r-bio-full
docker/Dockerfile.r-spatial-full
docker/Dockerfile.r-chem-full
docker/Dockerfile.r-chem-gpu
renv/renv.app.lock
renv/renv.bio-core.lock
renv/renv.bio-full.lock
renv/renv.spatial-full.lock
renv/renv.chem-full.lock
```

Status: scaffolded, not restored.

Completed:

- Added Dockerfile scaffolds for app-dev, bio-core, bio-full, spatial-full, chem-full, and chem-gpu.
- Added empty policy lockfiles for app, bio-core, bio-full, spatial-full, and chem-full.
- Added contract tests proving app-dev excludes known heavy analysis dependency names and that Dockerfiles do not contain runtime package installer entrypoints.

Remaining:

- Build real images in a controlled environment.
- Replace empty policy locks with approved package-version locks.
- Add resource lock validation for full mode.
- Add package/open-W checks only after real worker runtime exists.

Acceptance:

- App-dev image starts and tests UI without full analysis dependencies.
- Full image contains full R/Bioconductor dependencies and resource locks.
- Chem/spatial dependencies are separated from bio-core.

## Phase R6: Resource Governance

Scope:

- Lock Reactome, MSigDB, GO, KEGG, org dbs, spatial references, docking resources, and MD templates.
- Record version, source, hash, license, and cache path.

Acceptance:

- Full mode refuses to run if required resource lock is missing.
- No user request downloads a large database ad hoc.

## Phase R7: Advanced Analysis Lines

Order:

1. Immune infiltration heatmap.
2. Spatial transcriptomics.
3. Molecular docking.
4. Molecular dynamics.

Rules:

- Spatial goes to `r-spatial-full`.
- Docking/MD use R adapters to external tools only.
- Docking/MD never share the normal bio-core environment.

## Current Stop Rule

Do not migrate algorithms until the standard package validator and one mock-mode task-system bridge are in place.
