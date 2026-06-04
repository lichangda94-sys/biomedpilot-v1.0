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
| `lite` | Lightweight real analysis during daily development | Lightweight packages/resources only; no large downloads. Enrichment, survival, univariate, and multivariate clinical association now have base R fixtures through the standard runner. |
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
  fixtures/inputs/<module_id>/module_input.json
  fixtures/outputs/<module_id>/mock_result_package/
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

`analysis/runners/run_module.R` is a base R boundary runner. It accepts:

```text
Rscript analysis/runners/run_module.R <input_json> <output_dir> <mode>
```

In `mock` mode it copies the module-specific fixed standard result package declared by the registry, then writes fresh `result.json`, `provenance.json`, and `logs/worker.log` metadata for the current task. For supported `lite` modules it executes only lightweight fixed-fixture base R paths; unsupported `lite` modes and all `full` modes write blocked standard packages with provenance instead of executing analysis. The runner does not install packages and does not enable full analysis. Existing Bioinformatics algorithms still need staged migration into this contract.

The main-backend side has a narrow mock-mode bridge:

```text
app/analysis_runtime/
  package_catalog.py
  registry.py
  r_worker.py
  resources.py
  standard_package.py
  task_bridge.py
```

The bridge can create a task record, write a standard result package, validate the package, and register the package in the current result index. It can invoke supported `lite` worker paths explicitly via `worker_backend="rscript"`; unsupported `lite` modes and all `full` modes remain blocked until isolated worker environments are available.

In default mock mode, the bridge copies the module-specific fixed standard result package declared by the registry, then stamps the current `task_id`, hashes, timestamp, and worker log. This keeps UI/API/task-flow development deterministic without requiring R.

For worker-boundary validation, the bridge also supports an explicit `worker_backend="rscript"` path. That path writes `module_input.json`, invokes `analysis/runners/run_module.R`, validates the resulting standard package, and registers the package using the worker provenance. If `Rscript` is unavailable, it writes a blocked standard package instead of raising a traceback or installing R.

Resource governance is centralized in `analysis/resources/manifest.json` and validated by `app/analysis_runtime/resources.py`. The manifest records mock fixtures plus blocked full-mode locks for Reactome, MSigDB, GO, KEGG, organism annotation databases, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and molecular dynamics templates. These entries are not installations and do not enable full mode; they are explicit cache/version/hash/license requirements that must be satisfied before future full workers can run.

`app/analysis_runtime/package_catalog.py` builds a read-only catalog from result-index `standard_result_package` artifacts. `build_analysis_center_state()` exposes this catalog as `standard_analysis_packages`, so Analysis Center can discover standard packages without reading R package internals or scanning arbitrary output folders. Existing module-specific result views still need staged migration.

The first `lite` worker paths are enrichment ORA, survival KM/log-rank, univariate clinical association, and multivariate clinical association. `analysis/runners/run_module.R` can run these modules in `mode=lite` using base R and fixed repository fixtures. These paths write standard packages with `result.json`, `provenance.json`, `tables/`, `reports/`, and `logs/`. They remain `testing_level`; they do not enable full resources, plot/report-ready export, prognosis, treatment guidance, diagnosis, or clinical interpretation.

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
| Per-module mock result packages | Present for all registered modules. |
| Standard R runner | Present for mock mode, enrichment/survival/univariate/multivariate lite fixtures, and blocked full standard packages. |
| Mock task bridge | Present; default path copies module-specific fixture packages, explicit `rscript` path invokes the standard R runner, and both register result-index entries. |
| Enrichment lite worker | Present for base R ORA fixture only; testing-level standard package. |
| Survival lite worker | Present for base R KM/log-rank fixture only; testing-level standard package with no clinical conclusion. |
| Univariate lite worker | Present for base R clinical association fixture only; testing-level standard package with no clinical conclusion. |
| Multivariate lite worker | Present for base R linear model fixture only; testing-level standard package with no clinical conclusion. |
| Standard package catalog | Present; Analysis Center state exposes result-index-derived package summaries. |
| Other lite workers | Not enabled. |
| Full worker | Not enabled. |
| Docker/renv split | Scaffolded only; not build/restoration proven. |
| Resource manifest gate | Present as blocked full-mode resource ledger with validator; real locks pending. |
| Algorithm migration | Pending. |
