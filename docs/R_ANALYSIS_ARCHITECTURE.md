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
| `lite` | Lightweight real analysis during daily development | Lightweight packages/resources only; no large downloads. DEG, enrichment, survival, univariate, multivariate clinical association, immune infiltration, correlation, and spatial transcriptomics now have base R fixtures through the standard runner. Docking and molecular dynamics have external-tool command-manifest contract fixtures that do not execute AutoDock Vina or GROMACS and do not generate scientific external-tool results. |
| `full` | Formal analysis and full integration testing | Dedicated analysis container, renv lock, or isolated analysis environment. |

## Repository Contract

The initial contract is declared under:

```text
analysis/
  registry/analysis_modules.json
  registry/analysis_environments.json
  registry/resource_lock_evidence.json
  registry/environment_lock_evidence.json
  registry/standard_worker_migration_evidence.json
  schemas/input/module_input.schema.json
  schemas/output/result_package.schema.json
  schemas/output/worker_invocation.schema.json
  schemas/output/resource_lock_evidence.schema.json
  schemas/output/resource_lock_evidence_registry.schema.json
  schemas/output/environment_lock_evidence.schema.json
  schemas/output/environment_lock_evidence_registry.schema.json
  schemas/output/full_analysis_activation_gate.schema.json
  schemas/output/remediation_queue.schema.json
  modules/<module_id>/module.json
  runners/run_module.R
  fixtures/inputs/<module_id>/module_input.json
  fixtures/outputs/<module_id>/mock_result_package/
  resources/manifest.json

external_analysis_environments/
  README.md
  evidence/
  logs/

external_analysis_resources/
  README.md
  evidence/
  logs/

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

The resource validator emits `resource_lock_evidence_templates` for blocked full resources and external tools. Each template records the required lock evidence shape: version, source, SHA-256 hash, license, cache path, approved modules, evidence files, and `runtime_download_allowed=false`. Templates explicitly forbid runtime downloads, user-request downloads, placeholder hashes, and unlicensed caches. They are not resource locks and do not make full resources ready.

Locked resources must also point to a schema-valid evidence payload using `analysis/schemas/output/resource_lock_evidence.schema.json`. Evidence paths may be declared directly in the resource manifest for repository-local fixtures or registered through `analysis/registry/resource_lock_evidence.json` for externally prepared full resources. That payload records resource id, version, source, hash, license, cache path, approved modules, evidence files, and `runtime_download_allowed=false`. Missing evidence, malformed evidence, missing cache/evidence files, manifest/evidence mismatches, or any runtime-download permission block the resource lock. The current repository-local mock fixture has lock evidence; `analysis/registry/resource_lock_evidence.json` is intentionally empty, so full Reactome/MSigDB/spatial/chem resources remain blocked until real external lock evidence exists.

The Bioinformatics gene-set resource manager follows the same resource boundary. Common Reactome, GO, and KEGG catalog rows remain visible for repair guidance, but they are no longer runtime-downloadable from UI/user flows. `download_gene_set_resource()` and `refresh_downloaded_gene_set()` default to `runtime_gene_set_download_forbidden_import_or_prelocked_resource_required`; parser/download internals are reachable only through an explicit test/developer override. Formal and full enrichment resources must be imported as GMT files or supplied as externally prepared, versioned, hashed, licensed, prelocked resources.

The default dependency surface is guarded by tests. `requirements.txt`, `pyproject.toml`, `docker/Dockerfile.app-dev`, and `renv/renv.app.lock` must not include full R analysis packages or external simulation/docking tool names such as ReactomePA, Seurat, CellChat, GSVA, AutoDock Vina, GROMACS, limma, DESeq2, edgeR, clusterProfiler, fgsea, or msigdbr. `config/bioinformatics/package_requirements.yaml` may list detect-first external capabilities, but it must not be interpreted as an app-dev install list.

Environment governance is centralized in `analysis/registry/analysis_environments.json`. This registry is the authoritative map for `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`; it records the Dockerfile, renv lock, allowed modules, heavy-dependency policy, runtime-install policy, resource-lock requirement, and external-tool-lock requirement for each environment. Module manifests are tested against this registry so a module cannot silently point full analysis at `app-dev` or an unregistered worker environment.

Restored full environment evidence is centralized in `analysis/registry/environment_lock_evidence.json`. This registry is intentionally empty in the current developer checkout, so no full environment is marked restored. Future external environment build evidence must be registered there and pass `analysis/schemas/output/environment_lock_evidence_registry.schema.json` plus each entry's `analysis/schemas/output/environment_lock_evidence.schema.json` before a full environment can become ready. The registry is detect-first and forbids runtime package installation or runtime resource downloads.

`external_analysis_environments/` and `external_analysis_resources/` are lightweight handoff directories for small evidence manifests and logs only. They are not part of the default app-dev runtime, not resource caches, and not places to commit R package libraries, Docker image layers, Bioconductor databases, spatial references, AutoDock Vina bundles, or GROMACS installs. Their `.gitignore` guards preserve that boundary while still allowing small JSON evidence manifests.

`app/analysis_runtime/resources.py` now exposes `validate_analysis_environment_registry()`. The validator separates structural validity from full readiness: the current registry is structurally valid, but `full_mode_ready=false` because `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu` still point to `scaffold_only_not_restored` locks. This prevents a future resource-lock update from accidentally activating full mode before the isolated runtime locks are restored.

The environment validator also emits `environment_lock_evidence_templates` for blocked full environments. Each template records the required evidence shape for the external environment handoff: restored status, R and Bioconductor versions, package-lock hash, Dockerfile, renv lock, allowed modules, evidence files, and explicit forbidden runtime package/resource download policies. These templates are guidance for future registry entries; they do not mark an environment restored.

Restored environment locks must also provide schema-valid evidence using `analysis/schemas/output/environment_lock_evidence.schema.json`. `validate_analysis_environment_lock_evidence()` requires the environment id, restored/locked/active status, R version, Bioconductor version, package lock hash, Dockerfile, renv lock, allowed modules, evidence files, and explicit forbidden runtime package/resource download policies. A future renv lock that is marked `restored` without matching evidence remains blocked.

`build_analysis_center_state()` exposes this validator as `analysis_environment_gate_rows` plus developer diagnostics. The existing Analysis Center gate table can therefore show "Analysis environment registry" and "Full R environment readiness" without coupling the UI to Dockerfile, renv, or R package internals.

`app/analysis_runtime/architecture_status.py` exposes `build_analysis_architecture_status()`, a read-only machine snapshot for the 20 architecture requirements. The snapshot reports no P0 failures in the current source tree and keeps the overall state at `partial_with_p1_gaps` while full environment locks, resource locks, and universal isolated-worker migration remain incomplete.

`build_analysis_center_state()` exposes that snapshot as `analysis_architecture_status` and `analysis_architecture_gate_rows`. The UI gate table shows the architecture summary and P0 guard directly from the machine snapshot, so current P1 gaps stay visible without being confused with a full-mode pass.

Formal standard-worker migration evidence is centralized in `analysis/registry/standard_worker_migration_evidence.json`. The registry shape is checked by `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json`, and each evidence entry must pass `analysis/schemas/output/standard_worker_migration_evidence.schema.json`. `build_standard_worker_migration_matrix()` reads this registry and will not mark a module as `migrated_to_isolated_standard_worker` unless that module has a schema-valid evidence entry that passes `validate_standard_worker_migration_evidence()`. The current registry is intentionally empty, so no formal module is marked migrated.

Each standard-worker migration row now also exposes a `migration_evidence_template` and `migration_blockers`. The template is a machine-readable checklist for the future registry entry: `mode=full`, a task-center task id, a standard result package directory, standard R worker boundary, task-center invocation, result-index registration, frontend standard-package consumption, and formal semantics preservation. It explicitly forbids mock fixtures, lite testing-level packages, legacy service-adapter sidecars, and module-private output paths as migration evidence. These templates guide scoped module migration; they do not mark the current modules as migrated.

`build_full_analysis_activation_gate()` is the read-only full-mode release gate. It requires full environment locks, full resource locks, a passed migration evidence registry, and zero pending/blocked standard-worker migration rows. The current gate is blocked and is included in `build_analysis_architecture_status()` so consumers can inspect one activation decision without enabling full execution. The payload is checked against `analysis/schemas/output/full_analysis_activation_gate.schema.json` and exposes `schema_validation_status` plus `schema_blockers`.

`scripts/analysis_architecture_gate.py` provides a command-line wrapper for CI and ReleaseBuild preflight. It emits a `biomedpilot.analysis.architecture_gate_report.v1` JSON payload containing the architecture status, 20 requirement rows with PASS/WARN/FAIL counts, P0/P1/P2/P3 issue lists, top architecture risks, full activation gate, environment readiness, resource readiness, standard-worker migration summary, per-module migration rows, full remediation queue items, and a remediation summary with involved files and manual decision points. The payload shape is declared in `analysis/schemas/output/architecture_gate_report.schema.json` and self-reports `schema_validation_status` plus `schema_blockers`. The default gate is a P0/contract-validity guard and therefore exits zero for the current `partial_with_p1_gaps` state; `--require-full-ready` exits nonzero until full mode is actually eligible.

The same gate can also render a nine-section Markdown report with `--markdown-output <path>`. That report is generated from the JSON payload and covers the required human audit sections: current fit, PASS/WARN/FAIL table, top five risks, P0/P1/P2/P3 issues, involved files, minimal remediation path, priority files, completed changes, and manual decisions. Markdown rendering is read-only and does not change the activation decision.

For external environment/resource handoff, the gate can also write `--evidence-template-output <path>`. This JSON package contains environment lock templates, resource lock templates, standard-worker migration evidence templates, registry paths, current blockers, and template counts, and it self-checks against `analysis/schemas/output/evidence_template_package.schema.json`. It is a template export only: it does not register evidence, restore full environments, lock resources, execute workers, install packages, or download resources.

Analysis Center renders this as a dedicated `Full analysis activation gate` row in `analysis_architecture_gate_rows`, including disabled blockers for unrestored full environment locks, incomplete full resource locks, and pending standard-worker migration.

`app/analysis_runtime/package_catalog.py` builds a read-only catalog from result-index `standard_result_package` artifacts. `build_standard_analysis_package_detail()` reads only a selected standard package directory and returns a stable artifact manifest for declared `tables`, `plots`, `reports`, and package `logs`. `build_analysis_center_state()` exposes this catalog as `standard_analysis_packages`, so Analysis Center can discover standard packages and their artifact paths without reading R package internals or scanning arbitrary output folders. Catalog rows expose `worker_invocation`, `worker_backend`, `worker_invocation_status`, `worker_boundary_type`, `worker_migration_status`, and `artifact_manifest`, so UI diagnostics can use the standard package audit trail and distinguish packages generated by `analysis/runners/run_module.R`, task-bridge fixture copies, bridge-blocked packages, and compatibility sidecars generated by legacy service adapters. Existing module-specific detailed result views still need staged migration.

Existing controlled enrichment ORA/GSEA R adapters now also write a standard result package sidecar and register it as a `standard_result_package` output artifact in the current result index. The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar`, which prevents it from being mistaken for an isolated standard worker run. This is a result-package migration step only: it does not change the ORA/GSEA algorithms, enable plot/report-ready output, or prove that all formal R execution already runs through the isolated standard worker.

Existing controlled formal DEG executors now also write standard result package sidecars. The two-group Python controlled DEG runner mirrors successful formal result tables and task logs into `analysis/standard_packages/<result_id>/`; multi-factor limma, DESeq2, and edgeR adapters do the same for fixture-proven formal results. The sidecars preserve result tables, task logs, parameter manifests, dependency snapshots, hashes, engine metadata, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`. Multi-factor sidecars also preserve formula, contrast, covariates, and batch variables. They are registered in result index v2 as `standard_result_package` output artifacts. This is a package-contract migration step only: it does not enable new DEG execution, plot artifacts, report-ready output, clinical interpretation, or complete migration into the isolated standard worker.

Existing controlled KM/log-rank and Cox univariate executors now also write standard result package sidecars for successful controlled formal results. The sidecars preserve result tables, task logs, parameter manifests, dependency snapshots, hashes, engine metadata, `worker_boundary.boundary_type=legacy_service_adapter_sidecar`, and `logs/worker_invocation.json`. They are registered in result index v2 as `standard_result_package` output artifacts, and their worker invocation manifests are registered as `analysis_worker_invocation_manifest` log artifacts. This is a package-contract migration step only: it does not enable clinical conclusions, risk grouping, report-ready survival/clinical output, plot artifacts, or complete migration into the isolated standard worker.

Existing exploratory immune / TME scoring now also writes a standard result package sidecar and registers it as a `standard_result_package` output artifact in result index v2. The sidecar preserves the score matrix, signature coverage table, sample summary table, scoring manifest, receipt, hashes, limitations, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`. It remains `mode=lite` and `result_semantics=testing_level`; it does not enable GSVA, CellChat, Seurat, CIBERSORT, xCell, ESTIMATE, report-ready immune output, clinical interpretation, or isolated standard-worker migration.

Existing local expression-correlation runner outputs now also write a standard result package sidecar and register it as a `standard_result_package` output artifact in result index v2. The sidecar preserves the Pearson correlation result table, summary log, hashes, limitations, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`. It remains `mode=lite` and `result_semantics=testing_level`; it does not enable report-ready output, causal interpretation, clinical interpretation, or isolated standard-worker migration. A separate standard R worker lite fixture path now also exists for correlation using base R Pearson correlation and fixed local expression data.

The first `lite` worker paths are DEG two-group testing, enrichment ORA, survival KM/log-rank, univariate clinical association, multivariate clinical association, immune infiltration signature scoring, spatial transcriptomics spot QC, docking external-tool adapter contract, and molecular dynamics external-tool adapter contract. `analysis/runners/run_module.R` can run these modules in `mode=lite` using base R and fixed repository fixtures. These paths write standard packages with `result.json`, `provenance.json`, `tables/`, `reports/`, and `logs/`; immune infiltration and spatial transcriptomics also write real fixture SVG previews without relying on an R graphics device. Spatial transcriptomics, docking, and molecular dynamics lite fixtures declare `r-bio-core`; they no longer point at `r-spatial-full`, `r-chem-full`, or `r-chem-gpu` until full mode is activated. The spatial lite path writes `tables/lite_spatial_spot_metrics.tsv`, `tables/lite_spatial_qc_summary.tsv`, and `plots/lite_spatial_spot_qc.svg`; it deliberately does not use Seurat, CellChat, spacexr, spatial reference resources, clustering, deconvolution, spatial domain calling, cell-cell communication, or report-ready spatial interpretation. The docking lite path writes only `tables/lite_docking_command_manifest.tsv` plus limitations/provenance, records `AutoDock Vina` as `not_executed_lite_contract`, and deliberately does not generate docking scores, poses, affinities, or scientific docking results. The molecular dynamics lite path writes only `tables/lite_md_command_manifest.tsv` plus limitations/provenance, records `GROMACS` as `not_executed_lite_contract`, and deliberately does not generate trajectory, energy, RMSD, simulation metrics, or scientific molecular dynamics results. They remain `testing_level`; they do not enable formal DEG, limma/DESeq2/edgeR, full resources, GSVA/CellChat/Seurat, AutoDock Vina execution, GROMACS execution, plot/report-ready export, prognosis, treatment guidance, diagnosis, or clinical interpretation.

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
| Architecture status snapshot | Present; `build_analysis_architecture_status()` summarizes the 20 target requirements, P0/P1 issues, environment validation, and resource validation without executing workers or installing/downloading dependencies. Analysis Center now exposes this as UI gate rows. |
| Architecture gate script | Present; `scripts/analysis_architecture_gate.py` emits a schema-checked read-only JSON gate for P0/contract validity, 20 requirement rows, P0/P1/P2/P3 issue lists, top risks, blocked environment/resource visibility, per-module migration visibility, and remediation file/decision guidance; it can optionally require full readiness. |
| Architecture Markdown report | Present; `scripts/analysis_architecture_gate.py --markdown-output <path>` renders the same gate payload into the required nine-section human report without executing workers or changing full-mode readiness. |
| Standard worker migration matrix | Present; `build_standard_worker_migration_matrix()` records module-level mock, lite, full, and formal standard-worker migration status for each registered module without executing workers. Lite fixture readiness remains separate from full/formal migration. |
| Standard worker migration evidence template | Present; every migration row exposes required evidence fields and blockers, while forbidding mock/lite/legacy sidecar outputs as completion evidence. |
| Standard worker migration evidence validator | Present; `analysis/registry/standard_worker_migration_evidence.json`, `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json`, `analysis/schemas/output/standard_worker_migration_evidence.schema.json`, `validate_standard_worker_migration_evidence_registry()`, and `validate_standard_worker_migration_evidence()` block migration completion claims unless a selected module has a registry-owned schema-valid full-mode evidence payload, full-mode standard package, standard R worker boundary, task-center invocation, result-index registration, formal semantics preservation, and UI standard-package consumption evidence. Mock, lite, and legacy sidecar packages do not pass. |
| Environment lock evidence gate | Present; `analysis/schemas/output/environment_lock_evidence.schema.json` and `validate_analysis_environment_lock_evidence()` block restored full environment locks unless package-lock hash, Dockerfile, renv lock, allowed modules, evidence files, R/Bioconductor versions, and no-install/no-download policy are schema-valid and registry-aligned. |
| Environment/resource evidence templates | Present; validators and the architecture gate expose machine-readable templates for the external full-environment and full-resource evidence required before readiness can pass. |
| Architecture remediation queue | Present; `build_analysis_remediation_queue()` converts current P1 gaps into deterministic manual remediation items for full environment locks, full resource locks, and isolated standard-worker migration. The payload self-checks against `analysis/schemas/output/remediation_queue.schema.json`. Analysis Center exposes this as blocked remediation rows; it performs no worker execution, package installation, resource download, or project mutation. |
| Environment registry | Present; module manifests are tested against `analysis/registry/analysis_environments.json`, Dockerfile paths, renv lock paths, heavy-dependency policy, and allowed-module lists. A runtime validator reports structural status separately from full readiness, Analysis Center exposes those gate rows, and full mode stays blocked while full locks remain scaffold-only or lack schema-valid lock evidence. |
| Lite/full environment split | Present; spatial transcriptomics, docking, and molecular dynamics lite fixtures run under `r-bio-core`, while their full modes remain assigned to `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`. |
| External evidence handoff directories | Present; `external_analysis_environments/` and `external_analysis_resources/` are README/.gitignore guarded handoff areas for small evidence manifests and logs only, not runtime caches or default app dependencies. |
| Per-module mock result packages | Present for all registered modules. |
| DEG module contract | Present as a registered standard module with mock input/output package and base R lite fixture; full standard worker execution remains blocked. |
| Standard R runner | Present for mock mode, DEG/enrichment/survival/univariate/multivariate/immune/correlation/spatial lite fixtures, docking and molecular dynamics external-tool command-manifest lite fixtures, and blocked full standard packages. |
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
| Correlation lite worker | Present for base R Pearson expression-correlation fixture only; testing-level standard package with no causal, clinical, or report-ready interpretation. |
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
| Resource manifest gate | Present as blocked full-mode resource ledger with validator; fake `locked` placeholder fields and missing/mismatched lock evidence are rejected; real full-resource locks pending. |
| Algorithm migration | Pending. |
