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
| `lite` | Lightweight real analysis during daily development | Lightweight packages/resources only; no large downloads. DEG, enrichment, survival, univariate, multivariate clinical association, immune infiltration, and spatial transcriptomics now have base R fixtures through the standard runner. Docking and molecular dynamics have external-tool command-manifest contract fixtures that do not execute AutoDock Vina or GROMACS and do not generate scientific external-tool results. |
| `full` | Formal analysis and full integration testing | Dedicated analysis container, renv lock, or isolated analysis environment. |

## Repository Contract

The initial contract is declared under:

```text
analysis/
  registry/analysis_modules.json
  registry/analysis_environments.json
  schemas/input/module_input.schema.json
  schemas/output/result_package.schema.json
  schemas/output/worker_invocation.schema.json
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

Lite support is registry-gated. Any module that declares `modes.lite.supported=true` in `analysis/registry/analysis_modules.json` is covered by a focused task-bridge test that runs the module through `run_analysis_module_task(..., worker_backend="rscript")`, validates the standard package, verifies result-index registration, verifies standard package catalog discovery, and confirms the output remains `testing_level` with `report_ready_eligible=false`.

Full mode is also registry-gated, but currently as a blocking contract rather than an activation contract. Any module that declares `modes.full` is covered by a focused task-bridge test that requests `mode=full` with `worker_backend="rscript"` and verifies the bridge stops before worker execution, writes a blocked standard package, registers a blocked result-index entry, exposes the package in the standard catalog, and records non-executed R/Bioconductor/package/tool provenance.

For blocked `full` requests, `provenance.json` also records an `analysis_environment` snapshot. The same snapshot is copied into the result-index dependency snapshot. It records the target isolated environment id, Dockerfile, renv lock, heavy-dependency policy, resource-lock requirement, external-tool-lock requirement, authoritative environment-registry flags, no runtime-install/resource-download policies, module manifest path, required resource ids, and current resource/tool lock blockers. This is audit metadata only; it does not activate full-mode execution.

`validate_standard_result_package()` validates `analysis_environment` for every `full` package and for any package that declares the snapshot. It blocks missing snapshots, schema-version drift, mode/module mismatch, missing target Dockerfile/renv/module manifest fields, invalid full-mode isolation policy, invalid runtime-install/resource-download policy, and malformed resource-lock status. `build_standard_analysis_package_catalog()` and `build_standard_analysis_package_detail()` expose the same snapshot for UI diagnostics from the standard package contract.

In default mock mode, the bridge copies the module-specific fixed standard result package declared by the registry, then stamps the current `task_id`, hashes, timestamp, and worker log. This keeps UI/API/task-flow development deterministic without requiring R.

For worker-boundary validation, the bridge also supports an explicit `worker_backend="rscript"` path. That path writes `module_input.json`, invokes `analysis/runners/run_module.R`, validates the resulting standard package, and registers the package using the worker provenance. If `Rscript` is unavailable, it writes a blocked standard package instead of raising a traceback or installing R.

Standard task-bridge outcomes now persist `logs/worker_invocation.json` alongside `logs/worker.log`. The invocation manifest records the module, mode, task id, backend, invocation status, standard entrypoint, command, return code, stdout/stderr, blockers, runtime-install/resource-download policy, and worker-boundary migration status for mock fixture copies, validation gates, R worker attempts, and full-mode bridge gates. The result index keeps `worker.log` as the first log artifact for compatibility and appends the invocation manifest as `analysis_worker_invocation_manifest`.

Direct `analysis/runners/run_module.R` outputs also persist `logs/worker_invocation.json`. Their worker boundary records `task_system_invocation=standard_worker_direct_cli` because they are worker-level CLI contract artifacts, not UI/main-backend task submissions. Main-backend executions through `run_analysis_module_task()` continue to record `task_center_registered`.

Transitional legacy service-adapter sidecar packages also persist `logs/worker_invocation.json` when they mirror existing controlled results into a standard package. These manifests use `worker_backend=legacy_service_adapter`, `invocation_status=sidecar_recorded`, and `task_system_invocation=legacy_service_adapter_direct_call`, so the UI can diagnose them without confusing them with isolated standard-worker executions.

`analysis/schemas/output/worker_invocation.schema.json` defines the invocation manifest contract. `validate_standard_result_package()` validates this manifest when present and requires it for packages produced by `biomedpilot_analysis_task_bridge` or `biomedpilot_standard_r_worker`; missing manifests, invalid schemas, non-forbidden runtime install/resource download policy, invalid backend/status values, or missing task-system boundary metadata block standard package validation.

For transitional controlled adapters that still need module-specific R scripts, `app/analysis_runtime/r_worker.py` exposes `run_external_r_command()`. This helper centralizes external R subprocess behavior, timeout handling, blocker payloads, and worker-boundary metadata. It is not the final isolated standard worker interface; adapter-generated packages remain labeled as sidecars until their algorithms are moved behind `analysis/runners/run_module.R` or an equivalent isolated worker service.

Resource governance is centralized in `analysis/resources/manifest.json` and validated by `app/analysis_runtime/resources.py`. The manifest records mock fixtures plus blocked full-mode locks for Reactome, MSigDB, GO, KEGG, organism annotation databases, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and molecular dynamics templates. These entries are not installations and do not enable full mode; they are explicit cache/version/hash/license requirements that must be satisfied before future full workers can run. A resource cannot be marked `locked` while version, source, hash, license, or cache path still contains placeholder values such as `required_before_full_mode`; such entries block full mode instead of being treated as valid locks.

The Bioinformatics gene-set resource manager follows the same resource boundary. Common Reactome, GO, and KEGG catalog rows remain visible for repair guidance, but they are no longer runtime-downloadable from UI/user flows. `download_gene_set_resource()` and `refresh_downloaded_gene_set()` default to `runtime_gene_set_download_forbidden_import_or_prelocked_resource_required`; parser/download internals are reachable only through an explicit test/developer override. Formal and full enrichment resources must be imported as GMT files or supplied as externally prepared, versioned, hashed, licensed, prelocked resources.

The default dependency surface is guarded by tests. `requirements.txt`, `pyproject.toml`, `docker/Dockerfile.app-dev`, and `renv/renv.app.lock` must not include full R analysis packages or external simulation/docking tool names such as ReactomePA, Seurat, CellChat, GSVA, AutoDock Vina, GROMACS, limma, DESeq2, edgeR, clusterProfiler, fgsea, or msigdbr. `config/bioinformatics/package_requirements.yaml` may list detect-first external capabilities, but it must not be interpreted as an app-dev install list.

Environment governance is centralized in `analysis/registry/analysis_environments.json`. This registry is the authoritative map for `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`; it records the Dockerfile, renv lock, allowed modules, heavy-dependency policy, runtime-install policy, resource-lock requirement, and external-tool-lock requirement for each environment. Module manifests are tested against this registry so a module cannot silently point full analysis at `app-dev` or an unregistered worker environment.

`app/analysis_runtime/package_catalog.py` builds a read-only catalog from result-index `standard_result_package` artifacts. `build_standard_analysis_package_detail()` reads only a selected standard package directory and returns a stable artifact manifest for declared `tables`, `plots`, `reports`, and package `logs`. `build_analysis_center_state()` exposes this catalog as `standard_analysis_packages`, so Analysis Center can discover standard packages and their artifact paths without reading R package internals or scanning arbitrary output folders. Catalog rows expose `worker_invocation`, `worker_backend`, `worker_invocation_status`, `worker_boundary_type`, `worker_migration_status`, and `artifact_manifest`, so UI diagnostics can use the standard package audit trail and distinguish packages generated by `analysis/runners/run_module.R`, task-bridge fixture copies, bridge-blocked packages, and compatibility sidecars generated by legacy service adapters. Existing module-specific detailed result views still need staged migration.

Existing controlled enrichment ORA/GSEA R adapters now also write a standard result package sidecar and register it as a `standard_result_package` output artifact in the current result index. The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar`, which prevents it from being mistaken for an isolated standard worker run. This is a result-package migration step only: it does not change the ORA/GSEA algorithms, enable plot/report-ready output, or prove that all formal R execution already runs through the isolated standard worker.

Existing controlled formal DEG executors now also write standard result package sidecars. The two-group Python controlled DEG runner mirrors successful formal result tables and task logs into `analysis/standard_packages/<result_id>/`; multi-factor limma, DESeq2, and edgeR adapters do the same for fixture-proven formal results. The sidecars preserve result tables, task logs, parameter manifests, dependency snapshots, hashes, engine metadata, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`. Multi-factor sidecars also preserve formula, contrast, covariates, and batch variables. They are registered in result index v2 as `standard_result_package` output artifacts. This is a package-contract migration step only: it does not enable new DEG execution, plot artifacts, report-ready output, clinical interpretation, or complete migration into the isolated standard worker.

Existing controlled KM/log-rank and Cox univariate executors now also write standard result package sidecars for successful controlled formal results. The sidecars preserve result tables, task logs, parameter manifests, dependency snapshots, hashes, engine metadata, `worker_boundary.boundary_type=legacy_service_adapter_sidecar`, and `logs/worker_invocation.json`. They are registered in result index v2 as `standard_result_package` output artifacts, and their worker invocation manifests are registered as `analysis_worker_invocation_manifest` log artifacts. This is a package-contract migration step only: it does not enable clinical conclusions, risk grouping, report-ready survival/clinical output, plot artifacts, or complete migration into the isolated standard worker.

Existing exploratory immune / TME scoring now also writes a standard result package sidecar and registers it as a `standard_result_package` output artifact in result index v2. The sidecar preserves the score matrix, signature coverage table, sample summary table, scoring manifest, receipt, hashes, limitations, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`. It remains `mode=lite` and `result_semantics=testing_level`; it does not enable GSVA, CellChat, Seurat, CIBERSORT, xCell, ESTIMATE, report-ready immune output, clinical interpretation, or isolated standard-worker migration.

Existing local expression-correlation runner outputs now also write a standard result package sidecar and register it as a `standard_result_package` output artifact in result index v2. The sidecar preserves the Pearson correlation result table, summary log, hashes, limitations, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`. It remains `mode=lite` and `result_semantics=testing_level`; it does not enable report-ready output, causal interpretation, clinical interpretation, or isolated standard-worker migration.

The first `lite` worker paths are DEG two-group testing, enrichment ORA, survival KM/log-rank, univariate clinical association, multivariate clinical association, immune infiltration signature scoring, spatial transcriptomics spot QC, docking external-tool adapter contract, and molecular dynamics external-tool adapter contract. `analysis/runners/run_module.R` can run these modules in `mode=lite` using base R and fixed repository fixtures. These paths write standard packages with `result.json`, `provenance.json`, `tables/`, `reports/`, and `logs/`; immune infiltration and spatial transcriptomics also write real fixture SVG previews without relying on an R graphics device. The spatial lite path writes `tables/lite_spatial_spot_metrics.tsv`, `tables/lite_spatial_qc_summary.tsv`, and `plots/lite_spatial_spot_qc.svg`; it deliberately does not use Seurat, CellChat, spacexr, spatial reference resources, clustering, deconvolution, spatial domain calling, cell-cell communication, or report-ready spatial interpretation. The docking lite path writes only `tables/lite_docking_command_manifest.tsv` plus limitations/provenance, records `AutoDock Vina` as `not_executed_lite_contract`, and deliberately does not generate docking scores, poses, affinities, or scientific docking results. The molecular dynamics lite path writes only `tables/lite_md_command_manifest.tsv` plus limitations/provenance, records `GROMACS` as `not_executed_lite_contract`, and deliberately does not generate trajectory, energy, RMSD, simulation metrics, or scientific molecular dynamics results. They remain `testing_level`; they do not enable formal DEG, limma/DESeq2/edgeR, full resources, GSVA/CellChat/Seurat, AutoDock Vina execution, GROMACS execution, plot/report-ready export, prognosis, treatment guidance, diagnosis, or clinical interpretation.

## Module Manifests

Every registered target module now has a `module.json` scaffold:

```text
analysis/modules/deg/module.json
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

`analysis/registry/analysis_environments.json` is now tested as the authoritative environment boundary registry. `app-dev` has no allowed analysis modules, `r-bio-core` disallows heavy analysis dependencies, and spatial/chem modules are restricted to `r-spatial-full`, `r-chem-full`, or `r-chem-gpu`. All registered environments keep runtime package installation forbidden.

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

The standard R worker hashes the complete input manifest separately from the `parameters` object. This preserves distinct `input_hash` and `parameter_hash` values for mock, lite, blocked, and future full-mode standard packages without adding an R package dependency.

Passed `full` or `formal_computed_result` packages are validated with a stricter provenance gate. Missing input hash, parameter hash, command, random seed field, engine name/version, runtime version containers, package/external-tool version containers, or worker-boundary metadata for non-standard-worker sidecars blocks package validation. Mock and lite testing-level packages remain allowed to carry lighter provenance.

## Current Implementation Status

| Layer | Status |
| --- | --- |
| Registry/schema | Present. |
| Environment registry | Present; module manifests are tested against `analysis/registry/analysis_environments.json`, Dockerfile paths, renv lock paths, heavy-dependency policy, and allowed-module lists. |
| Per-module mock result packages | Present for all registered modules. |
| DEG module contract | Present as a registered standard module with mock input/output package and base R lite fixture; full standard worker execution remains blocked. |
| Standard R runner | Present for mock mode, DEG/enrichment/survival/univariate/multivariate/immune/spatial lite fixtures, docking and molecular dynamics external-tool command-manifest lite fixtures, and blocked full standard packages. |
| Mock task bridge | Present; default path copies module-specific fixture packages, explicit `rscript` path invokes the standard R runner, and both register result-index entries. |
| Registered lite bridge acceptance | Present; all registry-declared lite modules are exercised through the same task bridge, standard R worker, standard result package validator, result index, and catalog path. |
| Registered full bridge block gate | Present; all registry-declared full modules are blocked before worker execution and still emit standard package, result-index, catalog, and non-executed provenance records. |
| Full-mode environment snapshot | Present and validated for full packages; `provenance.json`, result-index dependency snapshots, catalog rows, and package detail payloads record target Dockerfile, renv lock, resource/tool lock policy, and blockers without enabling execution. |
| Worker invocation manifest | Present for all standard task-bridge outcomes, direct standard R runner packages, and current transitional service-adapter sidecar packages; task-bridge manifests are registered in result index log artifacts. |
| Direct standard R runner validation | Present for mock and blocked full outputs; direct worker packages include invocation manifests and validate without installing heavy R packages or enabling full execution. |
| Legacy sidecar invocation diagnostics | Present for current formal DEG, multifactor DEG, controlled enrichment, survival/KM/Cox, immune scoring, and correlation sidecar standard packages; explicitly labeled as non-isolated legacy adapter outputs. |
| Worker invocation validation | Present for task-bridge and standard-worker packages; missing or invalid invocation manifests block standard package validation. |
| Shared external R command boundary | Present for transitional controlled adapters; reduces scattered subprocess handling but does not complete isolated standard-worker migration. |
| Enrichment lite worker | Present for base R ORA fixture only; testing-level standard package. |
| Survival lite worker | Present for base R KM/log-rank fixture only; testing-level standard package with no clinical conclusion. |
| Univariate lite worker | Present for base R clinical association fixture only; testing-level standard package with no clinical conclusion. |
| Multivariate lite worker | Present for base R linear model fixture only; testing-level standard package with no clinical conclusion. |
| Immune infiltration lite worker | Present for base R signature mean score fixture plus real SVG heatmap; testing-level standard package with no clinical interpretation. |
| Spatial transcriptomics lite worker | Present for base R spot QC and coordinate SVG fixture only; testing-level standard package with no Seurat/CellChat/spacexr, spatial domain calling, cell-cell communication, or report-ready interpretation. |
| Docking lite adapter contract | Present for AutoDock Vina command-manifest fixture only; testing-level standard package with no external tool execution and no scientific docking output. |
| Molecular dynamics lite adapter contract | Present for GROMACS command-manifest fixture only; testing-level standard package with no external tool execution and no trajectory, energy, RMSD, simulation metric, or scientific MD output. |
| Standard package catalog | Present; Analysis Center state exposes result-index-derived package summaries, worker invocation diagnostics, and worker-boundary metadata. |
| Standard package artifact manifest | Present; package detail rows expose declared tables/plots/reports plus package logs without reading module-private output folders. |
| Full/formal package provenance gate | Present; passed full/formal packages with incomplete provenance or missing worker-boundary metadata are blocked by standard package validation. |
| Controlled enrichment standard package sidecar | Present for ORA/GSEA R fixture results with `legacy_service_adapter_sidecar` boundary metadata; does not enable plot/report-ready output or complete isolated worker migration. |
| Controlled DEG standard package sidecar | Present for successful two-group Python formal DEG and multi-factor limma/DESeq2/edgeR fixture results with `legacy_service_adapter_sidecar` boundary metadata; does not enable new execution, plot/report-ready output, clinical interpretation, or complete isolated worker migration. |
| Controlled survival/clinical standard package sidecar | Present for successful KM/log-rank and Cox univariate controlled results with `legacy_service_adapter_sidecar` boundary metadata and indexed worker invocation manifests; does not enable clinical conclusions, report-ready output, plot artifacts, risk grouping, or complete isolated worker migration. |
| Exploratory immune/TME standard package sidecar | Present for bulk signature scoring outputs with `legacy_service_adapter_sidecar` boundary metadata; remains `testing_level`/`lite` and does not enable GSVA/CellChat/Seurat, report-ready output, or clinical interpretation. |
| Local correlation standard package sidecar | Present for Pearson expression-correlation runner outputs with `legacy_service_adapter_sidecar` boundary metadata; remains `testing_level`/`lite` and does not enable report-ready output or clinical interpretation. |
| Other lite workers | All registered non-full module lines now have mock mode; lite/full formal migration remains gated module by module. |
| Full worker | Not enabled. |
| Docker/renv split | Scaffolded only; not build/restoration proven. |
| Resource manifest gate | Present as blocked full-mode resource ledger with validator; fake `locked` placeholder fields are rejected; real locks pending. |
| Algorithm migration | Pending. |
