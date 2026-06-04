# R Analysis Architecture

Date: 2026-06-04

## Boundary

BioMedPilot analysis modules use this target pattern:

```text
Frontend
  -> task submission / progress / result display
Main backend
  -> task creation / queue / status / files / result index
Dedicated analysis worker
  -> R packages, Bioconductor packages, databases, and external scientific tools
Standard result package
  -> result.json / provenance.json / tables / plots / reports / logs
```

R and external tools are not default frontend or main-backend runtime dependencies.

## Modes

| Mode | Purpose | Dependency policy |
| --- | --- | --- |
| `mock` | Frontend, API, task-flow, and result-display development | No heavy R packages; fixed fixture input/output. |
| `lite` | Lightweight real analysis during daily development | Lightweight packages/resources only; no large downloads. |
| `full` | Formal analysis and full integration testing | Dedicated analysis container, renv lock, or isolated analysis environment. |

## Repository Contract

The initial contract is declared under:

```text
analysis/
  registry/analysis_modules.json
  schemas/input/module_input.schema.json
  schemas/output/result_package.schema.json
  modules/<module_id>/module.json
  runners/run_module.R
  fixtures/
  resources/manifest.json

docker/
  Dockerfile.app-dev
  Dockerfile.r-bio-core
  Dockerfile.r-bio-full
  Dockerfile.r-spatial-full
  Dockerfile.r-chem-full
  Dockerfile.r-chem-gpu

renv/
  renv.app.lock
  renv.bio-core.lock
  renv.bio-full.lock
  renv.spatial-full.lock
  renv.chem-full.lock
```

`analysis/runners/run_module.R` is a base R mock-mode boundary runner. It does not install packages and does not enable full analysis. Existing Bioinformatics algorithms still need staged migration into this contract.

The main-backend side has a narrow mock-mode bridge:

```text
app/analysis_runtime/
  registry.py
  standard_package.py
  task_bridge.py
```

The bridge can create a task record, write a standard result package, validate the package, and register the package in the current result index. It returns blocked standard packages for lite/full modes until isolated worker environments are available.

## Module Manifests

Every registered target module now has a `module.json` scaffold:

```text
analysis/modules/survival/module.json
analysis/modules/univariate/module.json
analysis/modules/multivariate/module.json
analysis/modules/enrichment/module.json
analysis/modules/immune_infiltration/module.json
analysis/modules/spatial_transcriptomics/module.json
analysis/modules/docking/module.json
analysis/modules/molecular_dynamics/module.json
```

Each manifest declares:

- standard entrypoint,
- input/output schemas,
- mock/lite/full mode gates,
- app-dev/lite/full Docker boundary,
- renv lock placeholder,
- detect-first dependency policy,
- standard result package contract.

These manifests do not claim that lite/full analysis is active. They make the environment boundary explicit so future module migration can be tested without pulling heavy R packages into the default app runtime.

## Environment Split

The current environment files are policy scaffolds:

| Environment | Purpose | Current status |
| --- | --- | --- |
| `app-dev` | Main app and UI development without R analysis dependencies | Scaffolded; no full analysis dependencies. |
| `r-bio-core` | Future lite R worker for small bio fixtures | Scaffolded; package lock is empty. |
| `r-bio-full` | Future full R/Bioconductor worker | Scaffolded; blocked until lock/resource approval. |
| `r-spatial-full` | Future spatial transcriptomics worker | Scaffolded; blocked until lock/resource approval. |
| `r-chem-full` | Future docking external-tool worker | Scaffolded; blocked until external tool/resource lock approval. |
| `r-chem-gpu` | Future molecular dynamics external-tool worker | Scaffolded; blocked until GPU/tool lock approval. |

The Dockerfiles do not restore or install R packages. The renv lock files intentionally contain empty package maps and `scaffold_only_not_restored` status. This is an architecture boundary, not a full runtime validation.

## Result Package

Every module must eventually write:

```text
result.json
provenance.json
tables/
plots/
reports/
logs/
```

`provenance.json` must record engine version, R version, package versions, external tool versions, input hash, parameter hash, random seed, and command.

## Current Implementation Status

| Layer | Status |
| --- | --- |
| Registry/schema | Present. |
| Mock result package | Present. |
| Mock task bridge | Present. |
| Lite worker | Not enabled. |
| Full worker | Not enabled. |
| Docker/renv split | Scaffolded only; not build/restoration proven. |
| Algorithm migration | Pending. |
