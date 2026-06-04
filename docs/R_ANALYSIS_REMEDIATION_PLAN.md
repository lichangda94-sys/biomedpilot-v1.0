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
- `analysis/fixtures/inputs/<module_id>/module_input.json`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/**`
- `analysis/resources/manifest.json`
- `app/analysis_runtime/package_catalog.py`
- `app/analysis_runtime/registry.py`
- `app/analysis_runtime/r_worker.py`
- `app/analysis_runtime/resources.py`
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

- Add richer per-module mock tables/plots only where the UI needs them, while preserving mock labeling.
- Wire one current real analysis module through the bridge for lite mode.

Update: the first result package validator and mock-mode backend adapter now exist under `app/analysis_runtime/`. All registered modules now have fixed mock input and standard result package fixtures.

Update: the R-side standard runner now accepts `<input_json> <output_dir> <mode>`, copies module-specific mock packages in `mock` mode, writes blocked standard packages for `lite` and `full`, and blocks CLI/input mode mismatches. It remains a contract runner only; no real R algorithms are activated.

Update: the main-backend task bridge now has an explicit `worker_backend="rscript"` path. It materializes `module_input.json`, invokes the standard R runner, validates the standard package, and registers worker provenance in the result index. Missing `Rscript` is a graceful blocked package.

Update: the resource manifest now declares required full-mode resources for enrichment, immune infiltration, spatial transcriptomics, docking, and molecular dynamics. `app/analysis_runtime/resources.py` validates the manifest and adds module-specific full-mode blockers until real locks exist.

Update: the standard package catalog now reads result-index `standard_result_package` artifacts and is exposed in Analysis Center state as `standard_analysis_packages`. This is a read-only UI bridge; detailed module result views still need migration.

Update: enrichment now has the first `lite` standard worker path. `run_module.R` can execute a base R hypergeometric ORA fixture with local TERM2GENE files and write a testing-level standard result package. It does not use Reactome/MSigDB/full resources and does not enable report-ready output.

## Phase R1: Task-System Bridge

Scope:

- Add a Python bridge that submits module jobs by writing `module_input.json`.
- The bridge calls the standard worker only through task execution, not directly from UI.
- The UI consumes `result.json`, `provenance.json`, and artifact manifest metadata.

Acceptance:

- Every registered module can run `mock` mode through the task system using its fixed fixture package. **Completed for mock mode.**
- The R-side runner can generate a mock standard package from a module fixture and a blocked standard package for disabled modes. **Completed for runner contract.**
- The task bridge can explicitly call the R-side standard runner for mock packages without enabling lite/full real analysis. **Completed for worker-boundary contract.**
- Analysis Center can discover standard result packages from the result index without scanning module-specific output folders. **Completed for state-level preview.**
- Enrichment can run `lite` mode through the standard R worker using fixed local fixture resources. **Completed for first lite worker.**
- Output package includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, `logs/`.
- No R installation is required.

## Phase R2: Enrichment Lite Worker

Recommended first module because controlled ORA/GSEA R adapters already exist.

Scope:

- Wrap existing enrichment controlled adapters behind the standard worker.
- Use lightweight local TERM2GENE fixtures.
- No ReactomePA/msigdbr full resources in lite mode.

Acceptance:

- `mock` and base R ORA `lite` pass through the standard worker. **Completed for fixture ORA.**
- `full` remains blocked until resource locks and full env exist. **Still required.**
- Provenance records R version, input hash, parameter hash, seed, and command. **Completed for fixture ORA.**
- Package-version capture for non-base R lite/full workers remains pending.

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

Status: contract gate present; real locks pending.

Completed:

- Declared blocked full-mode resources for Reactome, MSigDB, GO, KEGG, human org db, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and MD templates.
- Added resource manifest validation and module-specific full-mode resource blockers.
- Kept runtime downloads forbidden for every resource entry.

Remaining:

- Replace `required_before_full_mode` placeholders with approved versions, source metadata, hashes, licenses, and cache paths.
- Add controlled environment checks proving resources are present in the isolated full worker.

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
