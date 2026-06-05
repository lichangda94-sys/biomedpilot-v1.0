# Architecture Audit: R Analysis Kernel

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

HEAD audited before changes: `f57bfcc4651c19b62e906e0b9c084fa5ffc98ee0`

## 1. Current Fit to Target Mode

Current state: **FAIL with partial mitigations**.

The project has useful Bioinformatics and Meta Analysis contracts, result indexes, gates, tests, and detect-first R adapters. However, before this audit there was no single top-level `analysis/` module registry, no uniform `run_module(input_json, output_dir, mode)` worker boundary, no universal input/output schema, and no guaranteed standard result package contract for every future R-native module.

This audit added a minimal boundary scaffold:

- `analysis/registry/analysis_modules.json`
- `analysis/registry/analysis_environments.json`
- `analysis/registry/resource_lock_evidence.json`
- `analysis/registry/environment_lock_evidence.json`
- `analysis/registry/standard_worker_migration_evidence.json`
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/result.schema.json`
- `analysis/schemas/output/provenance.schema.json`
- `analysis/schemas/output/result_package.schema.json`
- `analysis/schemas/output/worker_invocation.schema.json`
- `analysis/schemas/output/resource_lock_evidence.schema.json`
- `analysis/schemas/output/resource_lock_evidence_registry.schema.json`
- `analysis/schemas/output/environment_lock_evidence.schema.json`
- `analysis/schemas/output/environment_lock_evidence_registry.schema.json`
- `analysis/schemas/output/full_analysis_activation_gate.schema.json`
- `analysis/schemas/output/remediation_queue.schema.json`
- `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json`
- `analysis/runners/run_module.R`
- `analysis/fixtures/inputs/mock_analysis_input.json`
- `analysis/fixtures/outputs/mock_result_package/**`
- `analysis/resources/manifest.json`
- `external_analysis_environments/README.md`
- `external_analysis_resources/README.md`
- `docs/R_ANALYSIS_ARCHITECTURE.md`

The scaffold fixes the most basic registry/schema/mock result-package boundary. A minimal main-backend task bridge now also exists for mock-mode standard result packages:

- `app/analysis_runtime/registry.py`
- `app/analysis_runtime/standard_package.py`
- `app/analysis_runtime/task_bridge.py`

The bridge creates a `TaskCenter` task, writes a standard result package, validates it, and registers a result-index entry. It can execute registry-declared lite fixtures through the standard R worker, but it does not enable formal/full algorithms.

Mock mode now has fixed per-module inputs and fixed per-module standard result package fixtures:

- `analysis/fixtures/inputs/<module_id>/module_input.json`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/result.json`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/provenance.json`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/tables/`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/plots/`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/reports/`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/logs/`

The task bridge copies the module fixture package for `mock` mode and stamps current task metadata. Supported lite paths can be invoked explicitly through the standard R worker; unsupported lite paths and full modes remain blocked.

The R-side standard entrypoint has also been hardened:

- `analysis/runners/run_module.R <input_json> <output_dir> <mode>`
- `mock` mode copies the module fixture package and writes fresh result/provenance/log metadata.
- Supported `lite` modules execute fixed-fixture base R paths; unsupported `lite` modes and all `full` modes write blocked standard result packages with provenance instead of executing.
- Direct standard R runner outputs now copy the submitted input to package-local `module_input.json` and write `logs/worker_invocation.json` with `input_manifest=module_input.json` and `worker_boundary.task_system_invocation=standard_worker_direct_cli`. This keeps the worker CLI contract self-contained for development and tests while the main backend still uses `task_center_registered` through `run_analysis_module_task()`.
- Transitional service-adapter sidecar packages now also write `logs/worker_invocation.json` with `worker_backend=legacy_service_adapter` and `task_system_invocation=legacy_service_adapter_direct_call`. These manifests make catalog diagnostics consistent without claiming the adapters have migrated into the isolated standard worker.
- CLI mode and input manifest mode mismatches are blocked.
- Paths containing spaces are supported.
- No R package install/download or `library(...)` import is used.

The main-backend bridge now has two mock-safe paths:

- `worker_backend="python_fixture"` copies fixed standard packages without requiring R.
- Every bridge outcome now writes `module_input.json` before validation or worker execution, so mock, blocked, and Rscript packages keep the submitted input payload for audit.
- `worker_backend="rscript"` invokes the standard R runner with that `module_input.json`, validates the package, and registers result-index entries from worker provenance.
- Missing `Rscript` produces a blocked standard result package, not a traceback or installer path.
- All standard task-bridge outcomes now write `logs/worker_invocation.json`, recording backend, invocation status, standard entrypoint, command, return code, stdout/stderr, blockers, and no runtime-install/resource-download policies. The result index keeps `worker.log` first for compatibility and appends the invocation manifest as a second log artifact.
- `logs/worker_invocation.json` now has an explicit schema in `analysis/schemas/output/worker_invocation.schema.json`; `validate_standard_result_package()` requires and validates it for task-bridge, standard-worker, and legacy service-adapter sidecar packages. Missing manifests, schema-version drift, non-forbidden runtime install/resource download policy, invalid backend/status values, invalid command/blocker shapes, or missing task-system worker-boundary metadata block standard package validation.

External R command execution for transitional controlled adapters is now centralized:

- `app/analysis_runtime/r_worker.py` exposes `run_external_r_command()`.
- Existing controlled enrichment and multi-factor DEG adapters use this shared runtime boundary for Rscript commands instead of directly owning `subprocess.run`.
- Transitional R adapters no longer import `subprocess` or set `subprocess.run` as their own default runner; optional test runners are passed through to `run_external_r_command()`, and the default subprocess owner remains `app/analysis_runtime/r_worker.py`.
- The returned invocation payload includes owner, command, stdout/stderr, return code, blockers, and `worker_boundary.boundary_type=analysis_runtime_external_r_command`.
- This reduces scattered R execution logic, but it is still a transition boundary; it does not yet make those adapters isolated standard-worker tasks.

Resource governance now has a programmatic gate:

- `analysis/resources/manifest.json` records mock fixture resources and full-mode locks for Reactome, MSigDB, GO, KEGG, organism annotation databases, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and MD templates.
- `app/analysis_runtime/resources.py` validates required fields, forbids runtime downloads, and reports module-specific full-mode blockers.
- `locked` resources must now reference a schema-valid evidence payload under `analysis/resources/locks/`. That payload records resource id, version, source, hash, license, cache path, approved modules, evidence files, and `runtime_download_allowed=false`; missing or mismatched evidence blocks the resource lock.
- `app/analysis_runtime/resources.py` now also reports module-specific full-environment blockers. Full mode is blocked unless the module's registered full environment has an existing Dockerfile and a restored environment lock; current full locks are still `scaffold_only_not_restored`, so they remain blockers even if resource locks are later filled in.
- Restored full-environment locks must now provide schema-valid evidence. `validate_analysis_environment_lock_evidence()` requires restored status, R/Bioconductor versions, package-lock hash, Dockerfile, renv lock, allowed modules, evidence files, and explicit no runtime-install/resource-download policies.
- `app/analysis_runtime/resources.py` now validates the environment registry itself. `validate_analysis_environment_registry()` reports structural blockers separately from readiness blockers, so the current scaffold can be structurally valid while still returning `full_mode_ready=false` for unrestored full locks.
- `locked` resources are rejected if version, source, hash, license, or cache path still contains placeholder values such as `required_before_full_mode`; this prevents a resource from being falsely marked full-mode ready.
- `locked` resources are also rejected if their evidence file is missing, malformed, points at a missing cache path/evidence file, allows runtime downloads, mismatches required modules, or disagrees with the manifest version/source/hash/license/cache path.
- Blocked resources may carry partial future lock metadata, but they still produce module-specific full-mode blockers until their status is changed to a fully validated `locked` entry.
- Full mode remains blocked until these resources have real version, hash, license, and cache-path locks.
- `app/bioinformatics/gene_set_resources.py` now aligns with that policy for enrichment resources: Reactome, GO, and KEGG catalog rows are visible but not runtime-downloadable by default. User/UI flows must import GMT files or use externally prepared prelocked resources; parser/download tests opt in explicitly.

Standard package discovery is now available to the UI state layer:

- `build_analysis_architecture_status()` creates a read-only machine snapshot for the 20 R analysis architecture requirements, including P0/P1 issue lists plus resource and environment validator payloads.
- `analysis/registry/standard_worker_migration_evidence.json` is now the authoritative registry for formal isolated-worker migration evidence. The registry is empty, so no formal module is marked migrated.
- `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json` validates the authoritative migration registry shape. The current empty registry is schema-valid but still contains zero evidence entries, so every formal module remains pending.
- `build_full_analysis_activation_gate()` combines full environment readiness, full resource locks, and standard-worker migration evidence into a single read-only activation gate. Current status is blocked; the gate performs no worker execution, package installation, or resource download, and the payload self-checks against `analysis/schemas/output/full_analysis_activation_gate.schema.json`.
- `scripts/analysis_architecture_gate.py` wraps the architecture snapshot, full activation gate, migration matrix, and remediation queue into a CI/ReleaseBuild-safe JSON gate. The report contract is declared in `analysis/schemas/output/architecture_gate_report.schema.json`, and each script run reports `schema_validation_status` plus `schema_blockers`. The report includes `requirement_summary`, 20 `requirement_rows`, `priority_issue_lists`, `top_architecture_risks`, `environment_readiness`, `resource_readiness`, per-module `standard_worker_migration_rows`, full `remediation_queue` items, and a `remediation_summary` with involved files, minimal remediation path, and manual decision points. Consumers can see the PASS/WARN/FAIL audit table, P0/P1/P2/P3 issues, top risks, blocked full environments, blocked resource/tool locks, pending migration rows, and next safe files to change without rerunning internal validators. By default it passes when P0 is empty and contract payloads are valid, even though full mode is still blocked by P1 gaps. With `--require-full-ready`, the same current state exits nonzero until full environment locks, resource locks, and standard-worker migration evidence are complete.
- The same script can write a human-readable nine-section Markdown report with `--markdown-output <path>`. The Markdown is rendered from the same gate payload, covering current fit, PASS/WARN/FAIL counts, top five risks, P0/P1/P2/P3 issues, involved files, minimal remediation path, priority files, completed changes, and manual decisions. It is a report rendering path only; it does not execute workers, install R packages, download resources, or mark full analysis ready.
- Analysis Center exposes that activation gate as a visible row with disabled reasons, so full-mode blockers are not hidden in developer-only diagnostics.
- `build_analysis_remediation_queue()` now self-checks against `analysis/schemas/output/remediation_queue.schema.json`, keeping P1 remediation queue consumers on a stable contract.
- `analysis/registry/environment_lock_evidence.json` is now the authoritative registry for restored full environment evidence. It is intentionally empty, so no full environment is restored; `validate_analysis_environment_lock_evidence_registry()` provides the future evidence entry point without changing the default app-dev dependency boundary.
- `analysis/registry/resource_lock_evidence.json` is now the authoritative registry for externally prepared full resource lock evidence. It is intentionally empty, so no Reactome/MSigDB/spatial/chem resource is locked; `validate_analysis_resource_lock_evidence_registry()` provides the future evidence entry point without permitting runtime downloads.
- `app/analysis_runtime/package_catalog.py` reads only result-index `standard_result_package` artifacts.
- Result-index `task_type` to standard module mapping is now owned by `analysis/registry/analysis_modules.json` through `result_index_task_types`; the catalog no longer carries its own hard-coded Bioinformatics task-type map, and `analysis:<module_id>` entries are blocked when the module is not registered.
- `build_analysis_center_state()` exposes `standard_analysis_packages` and developer diagnostics from that catalog.
- `build_analysis_center_state()` now exposes `analysis_architecture_status` and `analysis_architecture_gate_rows`, giving the UI a compact architecture snapshot and P0 guard derived from the same machine-readable status payload.
- `build_analysis_center_state()` now also exposes `standard_package_gate_rows`, giving the UI direct gate rows for catalog source policy, package validation status, artifact-manifest validity, and input-manifest validity without inspecting module-private output folders.
- `build_analysis_center_state()` now exposes `analysis_environment_gate_rows` from `validate_analysis_environment_registry()`, so the UI can show registry structure and full R environment readiness blockers without reading Dockerfiles, renv locks, or R package internals directly.
- `build_result_gate_rows()` now joins result-index rows with the standard package catalog by `result_id`, so Analysis Center result rows can show standard package registration status, validation status, package path, and artifact counts without reading module-specific R outputs.
- `BioinformaticsResultsBrowserWidget` now carries those standard package fields into the current results table, so ordinary result browsing surfaces whether each result has a registered standard package, its validation state, relative package path, and artifact counts.
- The standard package catalog and detail payloads now expose the synthesized `package_manifest` and `result_package_schema`, so UI/report consumers can inspect the package-level contract without rerunning validation internals.
- The standard package catalog rows now expose provenance digests (`input_hash`, `parameter_hash`, `random_seed`) alongside runtime, command, engine, worker backend, and worker boundary metadata.
- The current Results Browser renders that standard package provenance/worker summary as a user-visible table, keeping R/runtime evidence out of developer-only JSON.
- The current Results Browser renders a standard package manifest table showing the `result_package.schema.json` path, module/mode/task/status, required directories, and payload files.
- The current Results Browser now renders a standard package input manifest table from catalog `input_manifest` metadata, including package path, schema, module/mode/task, input keys, and parameter keys.
- The current Results Browser also renders a standard package artifact manifest table for declared `tables`, `plots`, `reports`, and `logs`, constrained to package-relative paths from the catalog.
- The catalog now exposes `worker_boundary_type` and `worker_migration_status`, so standard R worker packages can be distinguished from legacy service-adapter sidecars.
- The catalog also exposes `worker_invocation`, `worker_backend`, and `worker_invocation_status` from `logs/worker_invocation.json`, so Analysis Center diagnostics can use standard package audit metadata rather than module-private R outputs.
- The catalog and detail payloads now expose a UI-safe `input_manifest` object derived from `worker_invocation.input_manifest`, including package-relative path, validation status, module/mode/task summary, input keys, parameter keys, and schema path for package-local `module_input.json`.
- The catalog now includes a standard `artifact_manifest` for declared `tables`, `plots`, `reports`, and package `logs`; this gives UI/detail surfaces a contract-safe path list without scanning module-private output folders.
- `validate_standard_result_package()` now blocks passed full/formal packages if they are missing required provenance fields, runtime/package/tool version containers, command, hashes, random seed field, engine metadata, or worker-boundary metadata for non-standard-worker sidecars.
- `validate_standard_result_package()` now blocks every passed standard package if it is missing reproducibility provenance: input hash, parameter hash, random seed field, command, engine name/version, R version, Bioconductor version, R package-version container, or external-tool-version container.
- `validate_standard_result_package()` now blocks `result.json` or `provenance.json` schema-version drift from `biomedpilot.analysis.result.v1` and `biomedpilot.analysis.provenance.v1`.
- `validate_standard_result_package()` now blocks result-declared `tables`, `plots`, and `reports` artifacts when the declared item is malformed, missing a path, absolute, outside its standard package group, or missing on disk. This prevents current or future UI consumers from treating module-private paths or stale artifact declarations as valid standard package output.
- Testing-level mock packages remain testing-level and do not become formal/report-ready results.

Existing controlled enrichment ORA/GSEA R adapters now write a standard result package sidecar:

- `app/bioinformatics/enrichment_r_adapter.py` mirrors the controlled ORA/GSEA result table into `analysis/standard_packages/<result_id>/`.
- The sidecar includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar` and `migration_status=sidecar_only_not_isolated_standard_worker`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- This is a package-contract migration step, not a claim that all formal R algorithms already run through the isolated standard worker.

Existing controlled DEG executors now write a standard result package sidecar:

- `app/bioinformatics/deg_engine/formal_runner.py` mirrors successful controlled two-group formal DEG result tables into `analysis/standard_packages/<result_id>/`.
- `app/bioinformatics/deg_engine/multifactor_r_runner.py` mirrors successful limma, DESeq2, and edgeR fixture-proven formal result tables into `analysis/standard_packages/<result_id>/`.
- The sidecar includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar preserves the parameter manifest, dependency snapshot, input/parameter/table hashes, engine metadata, and command provenance. Multi-factor DEG sidecars also preserve formula, contrast, covariates, batch variables, and R/package versions.
- The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar` and `migration_status=sidecar_only_not_isolated_standard_worker`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- This is a package-contract migration step, not a claim that DEG has been fully migrated into the isolated standard worker.

Existing controlled survival/clinical executors now write a standard result package sidecar:

- `app/bioinformatics/survival_clinical/km_executor.py` mirrors successful KM curve and log-rank result tables into `analysis/standard_packages/<result_id>/`.
- `app/bioinformatics/survival_clinical/cox_executor.py` mirrors successful Cox univariate result tables into `analysis/standard_packages/<result_id>/`.
- The sidecars include `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar` and `migration_status=sidecar_only_not_isolated_standard_worker`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- The sidecar also writes `logs/worker_invocation.json` and the current result index registers it as `analysis_worker_invocation_manifest`.
- This is a package-contract migration step, not a claim that survival/clinical execution has been fully migrated into the isolated standard worker, and it does not enable clinical conclusions, risk grouping, plot artifacts, or report-ready output.

Existing exploratory immune / TME scoring now writes a standard result package sidecar:

- `app/bioinformatics/immune_infiltration/scoring.py` mirrors score matrix, signature coverage, sample summary, scoring manifest, and receipt artifacts into `analysis/standard_packages/<result_id>/`.
- The sidecar includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar records `mode=lite`, `result_semantics=testing_level`, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- This is a package-contract migration step, not a claim that immune/TME scoring has been migrated into the isolated standard worker or that GSVA/CellChat/Seurat, report-ready output, or clinical interpretation are enabled.

Existing local expression correlation now writes a standard result package sidecar:

- `app/bioinformatics/services/correlation_runner.py` mirrors the Pearson correlation table and summary into `analysis/standard_packages/<result_id>/`.
- The sidecar includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar records `mode=lite`, `result_semantics=testing_level`, and `worker_boundary.boundary_type=legacy_service_adapter_sidecar`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- Correlation is now registered in `analysis/registry/analysis_modules.json` and `analysis/modules/correlation/module.json` with fixed mock and lite fixture packages plus full-mode blocking. Its existing production-facing runtime remains a legacy service-adapter sidecar until migrated behind the standard worker.
- The correlation lite registry now declares `runner=analysis/runners/run_module.R`, so `build_standard_worker_migration_matrix()` reports the fixed base R lite fixture as `standard_worker_lite_ready` while still keeping formal/full migration blocked.
- This is a package-contract migration step, not a claim that correlation has been migrated into the isolated standard worker or that report-ready output, causal interpretation, or clinical interpretation are enabled.

The first lightweight worker paths are now available:

- `analysis/runners/run_module.R` supports `module_id=deg`, `mode=lite` using base R Welch t-tests and fixed repository count/metadata fixtures.
- `analysis/runners/run_module.R` supports `module_id=enrichment`, `mode=lite` using base R hypergeometric ORA and fixed repository TERM2GENE fixtures.
- `analysis/runners/run_module.R` supports `module_id=survival`, `mode=lite` using base R KM/log-rank calculations and fixed repository survival fixture data.
- `analysis/runners/run_module.R` supports `module_id=univariate`, `mode=lite` using base R univariate clinical association calculations and fixed repository clinical fixture data.
- `analysis/runners/run_module.R` supports `module_id=multivariate`, `mode=lite` using base R linear model calculations and fixed repository clinical fixture data.
- `analysis/runners/run_module.R` supports `module_id=immune_infiltration`, `mode=lite` using base R signature mean scoring and fixed repository expression/signature fixture data.
- `analysis/runners/run_module.R` supports `module_id=correlation`, `mode=lite` using base R Pearson correlation calculations and fixed repository expression fixture data.
- `analysis/runners/run_module.R` supports `module_id=spatial_transcriptomics`, `mode=lite` using base R spot QC and fixed repository expression/coordinate fixture data.
- `analysis/runners/run_module.R` supports `module_id=docking`, `mode=lite` as an external-tool adapter contract fixture that writes an AutoDock Vina command manifest without executing AutoDock Vina.
- `analysis/runners/run_module.R` supports `module_id=molecular_dynamics`, `mode=lite` as an external-tool adapter contract fixture that writes a GROMACS command manifest without executing GROMACS.
- Spatial transcriptomics, docking, and molecular dynamics lite fixtures now declare `r-bio-core` as their lite environment. Their full modes still point to `r-spatial-full`, `r-chem-full`, and `r-chem-gpu` and remain blocked until full locks and resources exist.
- The DEG lite path writes a standard result package with `tables/lite_deg_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The enrichment lite path writes a standard result package with `tables/lite_ora_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The survival lite path writes a standard result package with `tables/lite_km_curve.tsv`, `tables/lite_logrank_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The univariate lite path writes a standard result package with `tables/lite_univariate_association.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The multivariate lite path writes a standard result package with `tables/lite_multivariate_association.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The immune infiltration lite path writes a standard result package with `tables/lite_immune_scores.tsv`, `plots/lite_immune_heatmap.svg`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The correlation lite path writes a standard result package with `tables/lite_correlation_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The spatial transcriptomics lite path writes a standard result package with `tables/lite_spatial_spot_metrics.tsv`, `tables/lite_spatial_qc_summary.tsv`, `plots/lite_spatial_spot_qc.svg`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`; it does not use Seurat, CellChat, spacexr, spatial references, clustering, deconvolution, spatial domain calling, cell-cell communication, or report-ready interpretation.
- The docking lite path writes a standard result package with `tables/lite_docking_command_manifest.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`; it records AutoDock Vina as `not_executed_lite_contract` and does not generate docking scores, poses, affinities, or scientific docking results.
- The molecular dynamics lite path writes a standard result package with `tables/lite_md_command_manifest.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`; it records GROMACS as `not_executed_lite_contract` and does not generate trajectory, energy, RMSD, simulation metrics, or scientific molecular dynamics results.
- These lite packages are `testing_level`; formal DEG, limma/DESeq2/edgeR execution, full enrichment, Reactome/MSigDB resources, GSVA/CellChat/Seurat resources, AutoDock Vina execution, GROMACS execution, full survival/clinical packages, plot/report-ready export, prognosis, diagnosis, treatment guidance, and clinical interpretation remain disabled.
- A registry-driven focused test now enforces lite coverage for all modules that declare `modes.lite.supported=true`. Each such module must pass through `run_analysis_module_task(..., worker_backend="rscript")`, write a valid standard package, register a result-index row, appear in the standard package catalog, retain `result_semantics=testing_level`, and keep `report_ready_eligible=false`.
- A registry-driven focused test now also enforces full-mode blocking for all modules that declare `modes.full`. Each such module must be stopped by `run_analysis_module_task(..., worker_backend="rscript")` before worker execution, write a blocked standard package, register a blocked result-index row, appear in the standard package catalog, and record `r_version=not_executed`, `bioconductor_version=not_executed`, empty package/tool version maps, and `command=analysis_task_bridge_mode_gate`.
- Full-mode blocked standard packages now also record an `analysis_environment` snapshot in `provenance.json` and in the result-index dependency snapshot. The snapshot includes the target environment id, Dockerfile, renv lock, heavy-dependency policy, resource-lock policy, external-tool-lock policy, authoritative environment-registry flags, no runtime-install/resource-download policies, module manifest path, environment-lock blockers, required resource ids, and module-specific resource/tool lock blockers. This improves auditability of blocked full requests; it does not enable full-mode execution.
- `validate_standard_result_package()` now enforces the `analysis_environment` snapshot contract for `full` packages and validates any package that declares one. Missing snapshots, schema drift, mode/module mismatches, missing Dockerfile/renv/module manifest fields, invalid runtime-install/resource-download policy, invalid full-mode isolation policy, malformed environment-lock status, or malformed resource-lock status block package validation. The standard package catalog and detail payload expose this snapshot for UI diagnostics.
- Direct `analysis/runners/run_module.R` mock and blocked full outputs are now validated by the same Python standard package validator in focused tests. The full direct-runner blocked package includes target environment/resource-lock snapshots and a worker invocation manifest; it remains blocked and does not activate full analysis.

A first environment isolation scaffold now also exists:

- `analysis/registry/analysis_environments.json`
- `analysis/modules/<module_id>/module.json` for DEG, survival, univariate, multivariate, enrichment, immune infiltration, correlation, spatial transcriptomics, docking, and molecular dynamics.
- `external_analysis_environments/README.md`
- `external_analysis_resources/README.md`
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

These files are policy scaffolds only. They do not restore packages, install full R dependencies, or prove full analysis readiness. The external handoff directories are lightweight evidence/log areas with `.gitignore` guards; they are not resource caches, Docker layer stores, R package libraries, or user-request download locations. The environment registry is now the authoritative map for `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`; tests verify module manifests cannot silently point lite/full analysis at unregistered environments or at `app-dev`.

The standard result payload schema contract is now explicit in the module registry and in every module manifest:

- `analysis/registry/analysis_modules.json` declares `standard_result_package.payload_schemas` for `result.json` and `provenance.json`.
- Every registry module entry declares `result_payload_schema=analysis/schemas/output/result.schema.json` and `provenance_payload_schema=analysis/schemas/output/provenance.schema.json`.
- Every `analysis/modules/<module_id>/module.json` manifest declares the same payload schema files.
- `build_standard_analysis_package_catalog()` and `build_standard_analysis_package_detail()` now expose those payload schema paths in UI-safe catalog/detail payloads.
- `tests/test_r_analysis_architecture_contract.py` verifies these paths exist and remain consistent across registry and manifests.

This closes a schema-discovery gap for future UI/catalog consumers: they no longer have to infer the payload schema from the package validator or from module-private conventions.

The standard package validator now uses the result/provenance payload schema files as a required-field gate:

- `validate_standard_result_package()` now synthesizes a package-level manifest from the package filesystem and `result.json`, then validates it against `analysis/schemas/output/result_package.schema.json`.
- Package-level schema validation exposes `result_package_schema` and `package_manifest` in the validation payload and blocks package directory contract drift such as missing `logs/`.
- `validate_standard_result_package()` reads `analysis/schemas/output/result.schema.json` and blocks packages missing required result fields such as `result_semantics` or `created_at`.
- It reads `analysis/schemas/output/provenance.schema.json` and blocks packages missing required provenance fields such as `engine` or `command`.
- It now also enforces top-level schema shape for declared `type`, `enum`, `const`, `minLength`, array item types, and one-level nested object properties such as `engine.version` and `runtime.package_versions`.
- Main-backend task-bridge blocked packages now write `result_semantics=blocked`, keeping blocked outputs schema-complete instead of relying on result-index semantics alone.

The main-backend task bridge now also treats the module input schema as an execution gate:

- `run_analysis_module_task()` reads `analysis/schemas/input/module_input.schema.json` before invoking a fixture copy or R worker.
- Missing schema-required fields such as `parameters` produce `module_input_schema_required_field_missing:<field>` blockers while preserving existing semantic blockers for UI disabled reasons.
- Shape drift such as invalid mode enum, empty `task_id`, non-object `inputs`, and invalid nested `runtime` field types is blocked before worker execution and still writes a diagnostic standard result package plus `logs/worker_invocation.json`.
- `validate_standard_result_package()` now follows `logs/worker_invocation.json -> input_manifest`; for task-center packages, `input_manifest` must be `module_input.json`, the file must exist inside the standard package, and its content must satisfy `analysis/schemas/input/module_input.schema.json` plus expected module/task/mode matching.

## 2. PASS / WARN / FAIL Table

| Requirement | Status | Evidence |
| --- | --- | --- |
| Unified analysis module directory | WARN | Added `analysis/` and `analysis/modules/<module_id>/module.json`; existing algorithms still live under `app/bioinformatics/**`. |
| Module registry | PASS | Added `analysis/registry/analysis_modules.json`. |
| Machine-readable architecture status | PASS/WARN | `build_analysis_architecture_status()` returns 20 requirement rows and currently reports `partial_with_p1_gaps`, with no P0 failures but unresolved full environment/resource locks and incomplete universal isolated-worker migration; Analysis Center exposes the same summary and P0 guard as gate rows. |
| Unified entrypoint | WARN | Added and tested `analysis/runners/run_module.R` for mock, every registry-declared lite standard package, docking/MD lite command-manifest packages, and validator-passing blocked unsupported/full standard packages; every registry-declared full mode is bridge-blocked with a standard package; existing formal real modules do not call it yet. |
| Mock/lite/full design | WARN | Registry declares all three modes; every module has fixed mock input/output fixtures; every module that declares lite support is covered by a registry-driven bridge test; every module that declares full mode is covered by a registry-driven blocked-package bridge test; full activation remains blocked pending migration. |
| Unified input/output schema | PASS | Added input, result payload, provenance payload, worker invocation, and result package schemas. |
| Registry/manifest payload schema declaration | PASS | `analysis/registry/analysis_modules.json` and every `analysis/modules/<module_id>/module.json` now explicitly declare the result and provenance payload schemas; architecture tests guard consistency and file existence. |
| UI-safe payload schema discovery | PASS | Standard package catalog rows and package detail payloads now expose result/provenance payload schema paths for consumers. |
| Payload schema required-field validation | PASS | `validate_standard_result_package()` now blocks result/provenance payloads missing fields required by their schema files; task-bridge blocked packages include `result_semantics=blocked`. |
| Payload schema shape validation | PASS | `validate_standard_result_package()` now blocks result/provenance payload enum/type/minLength drift, array item type drift, and declared one-level nested object shape drift. |
| Result package schema validation | PASS | `validate_standard_result_package()` synthesizes a package manifest and validates it against `analysis/schemas/output/result_package.schema.json`, including required package files and directory contract shape. |
| Module input schema validation | PASS | `run_analysis_module_task()` now blocks required-field and shape drift from `analysis/schemas/input/module_input.schema.json` before worker execution while still returning a standard diagnostic package and worker invocation manifest. |
| Materialized input manifest validation | PASS | Standard package validation now verifies task-center `worker_invocation.input_manifest=module_input.json`, checks the file exists in the package, and validates its schema plus expected module/task/mode. |
| Every module outputs `result.json` / `provenance.json` | WARN | Mock fixtures prove standard package shape for every registered module; controlled enrichment ORA/GSEA, controlled DEG, controlled KM/log-rank, controlled Cox univariate, exploratory immune/TME scoring, and local correlation results now write standard sidecar packages; other existing real algorithms still use varied structures. |
| Every module outputs `tables/`, `plots/`, `reports/`, `logs/` | WARN | Mock fixtures prove required directories for every registered module; existing real algorithms not fully normalized. |
| Frontend consumes standard package only | WARN | Analysis Center state now exposes a standard package catalog and standard-package gate rows from result-index artifacts, worker invocation diagnostics, worker-boundary metadata, full-mode environment snapshots, and a standard artifact manifest; package validation blocks declared table/plot/report artifacts that are missing or escape the standard package directories. Existing detailed result views still consume module-specific result indexes and service payloads. |
| Main backend task-system invocation | WARN | A mock/lite/full-blocking bridge now creates `TaskCenter` entries and result-index entries; registry-declared lite modules are covered through the standard R runner, result package validator, result index, and catalog, while registry-declared full modules are blocked before worker execution with standard package provenance and explicit target environment/resource-lock snapshots. Existing controlled enrichment and multi-factor DEG sidecars are now labeled as legacy service-adapter sidecars; transitional adapters delegate subprocess defaults to `analysis_runtime.r_worker` but still need full task-worker migration. |
| Worker invocation audit trail | WARN | All standard task-bridge outcomes, direct standard R runner outputs, and current transitional service-adapter sidecar packages now persist `logs/worker_invocation.json`; task-bridge and current sidecar result-index entries register it as `analysis_worker_invocation_manifest`; the standard package catalog blocks packages whose result-index log artifact omits, mispoints, or mis-schemas that invocation manifest; sidecar manifests remain explicitly labeled as non-isolated legacy adapter diagnostics. |
| Worker invocation schema validation | PASS | Added `analysis/schemas/output/worker_invocation.schema.json`; standard package validation blocks missing or invalid invocation manifests for task-bridge, standard-worker, and legacy service-adapter sidecar packages while preserving explicit sidecar migration status. |
| Runtime R package installation in user flow | PASS | Search found no active non-legacy `install.packages`, `BiocManager::install`, `pak::pkg_install`, or `remotes::install_github`. |
| Runtime large resource download in user flow | PASS/WARN | Gene-set resource UI/gates now block Reactome/GO/KEGG runtime downloads by default and require GMT import or prelocked resources; real full resource locks are still incomplete. |
| Heavy dependencies in default dev env | PASS/WARN | Heavy R packages and external tools are detect-first external dependencies, not default Python/app-dev deps; tests guard `requirements.txt`, `pyproject.toml`, `docker/Dockerfile.app-dev`, and `renv/renv.app.lock` against ReactomePA, Seurat, CellChat, GSVA, AutoDock Vina, GROMACS, limma, DESeq2, edgeR, clusterProfiler, fgsea, and related full-stack names. `config/bioinformatics/package_requirements.yaml` is explicitly guarded as a capability/detection inventory, and `analysis_defaults.yaml`, `enrichment_defaults.yaml`, and `survival_defaults.yaml` are now explicitly guarded as gated capability/default-parameter configs, not install manifests, with runtime install/download and default-app dependency flags set false. Full env split is not build/restoration proven. |
| Environment split | WARN | Docker/renv scaffold and `analysis/registry/analysis_environments.json` exist for `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`; module manifests and the environment registry are validated, restored locks require schema-valid evidence, and Analysis Center surfaces the registry/readiness gates, but full image builds and lock restoration are not proven. |
| `renv.lock` equivalent | WARN | Empty policy lockfiles exist; real package locks and environment lock evidence are not restored or approved. |
| Full analysis Docker image | WARN | Dedicated Dockerfile scaffolds exist; no full image build or package restoration is proven. |
| Large resources version/hash/license/cache | WARN | Added blocked full-mode resource ledger and validator; `locked` resources with placeholder fields now fail validation; gene-set runtime downloads are blocked by default; real resource locks are incomplete. |
| Provenance captures versions/hashes/seed/command | WARN | The standard R worker records separate input and parameter hashes plus seed and command; bridge-blocked full packages now record and validate target environment Dockerfile/renv/resource-lock snapshots; every passed standard package is blocked if required reproducibility provenance containers are missing, but package/tool version capture is still incomplete for unmigrated formal/full modules. |
| DEG/survival/univariate/multivariate/enrichment/immune/correlation/spatial/docking/MD share interface | WARN | Registry declares target modules; mock packages exist for all registered modules, R-native lite workers exist for DEG, enrichment, survival, univariate, multivariate, immune infiltration, correlation, and spatial transcriptomics, and docking/MD have lite external-tool command-manifest contract fixtures. Formal/full migration remains pending. |
| Docking/MD external tool adapters | WARN | Docking and molecular dynamics have testing-level command-manifest adapter contracts that do not execute AutoDock Vina or GROMACS and do not generate scientific docking or MD outputs. |
| Default dev can start without full analysis deps | PASS | Current source smoke historically works without requiring full R environments; scaffold test does not require R. |

## 3. Top 5 Architecture Risks

1. **P0/P1: R analysis logic is not yet isolated behind a universal worker.** Current controlled R adapters now call a shared `analysis_runtime` external R command boundary instead of owning direct `subprocess.run` or subprocess defaults, and a standard bridge exists for mock, DEG lite, enrichment lite, survival lite, univariate lite, multivariate lite, immune lite, spatial lite, docking lite, and MD lite command-manifest packages. Most existing formal algorithms are still not migrated into isolated standard-worker tasks.
2. **P1: Environment split is scaffold-only.** Docker/renv boundaries now exist for `r-bio-core`, `r-bio-full`, `r-spatial-full`, and `r-chem-full`, and restored locks now require schema-valid evidence, but no full worker image has been built or restored.
3. **P1: Standard result package is not universal.** Existing modules use result index entries, report packages, and custom paths rather than always producing `result.json` and `provenance.json`; controlled enrichment ORA/GSEA, controlled DEG, controlled KM/log-rank, controlled Cox univariate, exploratory immune/TME scoring, and local correlation results are now partially remediated with sidecar packages that are explicitly labeled as legacy service-adapter sidecars.
4. **P1: Large resource governance is incomplete.** Required full-mode resources are now declared and blocked, fake `locked` entries with placeholder values are rejected, and Reactome/GO/KEGG runtime downloads are blocked by default, but resources still need real version, source, hash, license, and cache-path locks.
5. **P2/P3: UI and backend are still aware of module-specific payloads.** Analysis Center state and the current Results Browser now expose standard package catalog gates, per-result standard package status, provenance/worker summaries, and package artifact manifests, but detailed result-specific review panels should eventually consume standard result package metadata rather than individual R package output shapes.

## 4. P0/P1/P2/P3 Issues

### P0

| Issue | Evidence | Status after this audit |
| --- | --- | --- |
| No unified mock-mode analysis module framework | No top-level `analysis/registry` before this audit | Partially fixed with registry, mock fixture, and mock runner. |
| No standard result package contract | Existing modules emit varied outputs | Partially fixed at schema and mock task bridge level; algorithm migration pending. |
| R analysis logic scattered in main backend services | `app/bioinformatics/enrichment_r_adapter.py`, `app/bioinformatics/deg_engine/multifactor_r_runner.py` | Partially fixed by routing controlled enrichment and multi-factor DEG R commands through `app/analysis_runtime/r_worker.py`; staged isolated worker migration still pending. |

### P1

| Issue | Evidence | Status after this audit |
| --- | --- | --- |
| No lite/full environment split | No `docker/` or `renv` split existed before scaffold | Partially fixed with scaffold, authoritative environment registry, DEG/enrichment/survival/univariate/multivariate/immune/spatial base R lite fixtures, and docking/MD command-manifest lite fixtures; real package locks and builds pending. |
| No universal module schema | Missing before audit | Fixed at initial schema level. |
| No complete resource lock | Only module-specific gates/docs existed | Blocked resource ledger and validator added; fake locked resources with placeholder values are blocked; real locks pending. |
| Full analysis no independent container | No Docker image split before scaffold | Partially fixed with Dockerfile scaffolds; real full image build pending. |
| UI/backend do not yet call standard worker | Existing direct service calls remain | Partially fixed for mock task bridge, standard package catalog/artifact manifest, and controlled enrichment sidecar output; current UI algorithms not fully migrated. |

### P2

| Issue | Evidence |
| --- | --- |
| Full modules are not yet proven through isolated full-worker environments | Static tests and bridge tests now prove all registered modules can run mock through one interface, every registry-declared lite module can run through the same R worker/result-index/catalog path, and every registry-declared full module is blocked through the same task bridge with non-executed provenance plus target environment/resource-lock snapshots; isolated full execution remains unavailable. |
| Logs/provenance differ by module | All standard task-bridge packages and current service-adapter sidecar packages now have `worker.log` plus `worker_invocation.json`; existing formal sidecars still have custom result indexes and remain labeled as non-isolated sidecars; full/formal standard package sidecars now have a stricter provenance gate. |
| Worker invocation manifest was diagnostic-only | Task-bridge and direct standard R runner packages now require schema-valid `logs/worker_invocation.json`; invalid policy, backend/status, command, blockers, or task-system boundary fields block standard package validation. Standard package catalog validation also requires result-index `analysis_worker_invocation_manifest` log artifacts to point at the same package-local manifest when one exists. |
| Full-mode environment snapshot was write-only | Full packages now block validation if the environment snapshot is missing or malformed; catalog/detail payloads expose the snapshot for UI diagnostics. |
| Declared artifacts could be stale or package-external | Standard package validation now blocks malformed, missing, absolute, package-external, or wrong-group `tables`/`plots`/`reports` artifact declarations; Analysis Center exposes these as standard package gate rows and top blockers. |
| Example data is incomplete for every declared module | Generic and per-module mock fixtures exist for all registered modules; lite fixtures exist for DEG, enrichment, survival, univariate, multivariate, immune infiltration, spatial transcriptomics, docking command-manifest contract, and molecular dynamics command-manifest contract only. |

### P3

| Issue | Evidence |
| --- | --- |
| Naming is inconsistent across old Bio R adapters, enrichment gates, and future worker terms | Current code predates unified `analysis/` contract. |
| Documentation was missing a central R analysis architecture page | Added `docs/R_ANALYSIS_ARCHITECTURE.md`. |

## 5. Involved File Paths

Current R/external worker candidates:

- `app/bioinformatics/deg_engine/multifactor_r_runner.py`
- `app/bioinformatics/enrichment_r_adapter.py`
- `app/bioinformatics/enrichment_backend.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`

Current result/provenance package candidates:

- `app/bioinformatics/results/registry.py`
- `app/bioinformatics/reports/formal_deg.py`
- `app/bioinformatics/reports/export_package.py`
- `app/bioinformatics/deg_engine/audit_package.py`
- `app/meta_analysis/services/meta_result_contract_adapter.py`

New architecture boundary files:

- `analysis/registry/analysis_modules.json`
- `analysis/registry/analysis_environments.json`
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/result_package.schema.json`
- `analysis/resources/manifest.json`
- `analysis/modules/deg/module.json`
- `analysis/modules/survival/module.json`
- `analysis/modules/univariate/module.json`
- `analysis/modules/multivariate/module.json`
- `analysis/modules/enrichment/module.json`
- `analysis/modules/immune_infiltration/module.json`
- `analysis/modules/spatial_transcriptomics/module.json`
- `analysis/modules/docking/module.json`
- `analysis/modules/molecular_dynamics/module.json`
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
- `analysis/runners/run_module.R`
- `analysis/fixtures/inputs/mock_analysis_input.json`
- `analysis/fixtures/outputs/mock_result_package/result.json`
- `analysis/fixtures/outputs/mock_result_package/provenance.json`
- `analysis/fixtures/inputs/<module_id>/module_input.json`
- `analysis/fixtures/outputs/<module_id>/mock_result_package/**`
- `app/analysis_runtime/registry.py`
- `app/analysis_runtime/standard_package.py`
- `app/analysis_runtime/task_bridge.py`

## 6. Minimal Viable Remediation Path

1. Keep existing algorithms stable.
2. Add standard result package schema, registry, mock runner, and fixtures. **Completed in this audit.**
3. Wrap one existing R-native module behind the standard worker in mock mode first. **Started with `app/analysis_runtime/task_bridge.py` and `app/analysis_runtime/r_worker.py`.**
4. Add lite mode for selected modules with lightweight fixture data and no large downloads. **Started with DEG, enrichment, survival, univariate, multivariate, immune infiltration, spatial transcriptomics, docking command-manifest, and molecular dynamics command-manifest fixtures.**
5. Turn formal algorithm migration into a module-level standard-worker matrix. **Completed with `build_standard_worker_migration_matrix()` and Analysis Center rows.**
6. Turn current P1 gaps into an auditable remediation queue. **Completed with `build_analysis_remediation_queue()` and Analysis Center rows.**
7. Move full mode to an isolated `renv`/Docker environment.
8. Repeat module by module: survival, univariate, multivariate, enrichment, immune infiltration, then spatial/chem.

## 7. Recommended First Files to Modify Next

The current machine-readable queue exposes these P1 items:

| Queue item | Priority files | Required evidence |
| --- | --- | --- |
| `restore_full_analysis_environment_locks` | `analysis/registry/analysis_environments.json`, `analysis/registry/environment_lock_evidence.json`, `renv/renv.bio-full.lock`, `renv/renv.spatial-full.lock`, `renv/renv.chem-full.lock`, `analysis/schemas/output/environment_lock_evidence.schema.json`, `analysis/schemas/output/environment_lock_evidence_registry.schema.json`, `external_analysis_environments/`, `docker/Dockerfile.r-bio-full`, `docker/Dockerfile.r-spatial-full`, `docker/Dockerfile.r-chem-full`, `docker/Dockerfile.r-chem-gpu` | Full environment locks restored from controlled external environments; every restored full environment lock has schema-valid registry evidence; image build evidence captured outside default app-dev; environment validator reports full readiness. |
| `lock_full_analysis_resources` | `analysis/resources/manifest.json`, `analysis/registry/resource_lock_evidence.json`, `analysis/schemas/output/resource_lock_evidence.schema.json`, `analysis/schemas/output/resource_lock_evidence_registry.schema.json`, `analysis/resources/locks/`, `external_analysis_resources/` | Every full resource declares version, source, hash, license, and cache path; every locked full resource has schema-valid registry evidence; resource validator reports full readiness. |
| `migrate_formal_algorithms_to_isolated_standard_worker` | `app/bioinformatics/`, `analysis/registry/standard_worker_migration_evidence.json`, `analysis/runners/run_module.R`, `analysis/modules/`, `analysis/schemas/input/module_input.schema.json`, `analysis/schemas/output/standard_worker_migration_evidence.schema.json`, `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json`, `analysis/schemas/output/result_package.schema.json` | Selected formal module has registry-owned schema-valid migration evidence, executes through the task bridge and standard worker boundary, and frontend consumes the standard package instead of module-private output paths. |

The current standard-worker migration matrix is intentionally still `partial`: all registered modules have mock packages and lite worker fixture paths, but full/formal migration remains blocked or pending until a selected formal module has a registry-owned payload in `analysis/registry/standard_worker_migration_evidence.json`, that payload matches `analysis/schemas/output/standard_worker_migration_evidence.schema.json`, passes `validate_standard_worker_migration_evidence()`, and passes isolated environment/resource gates.

## 8. Completed Changes in This Audit

- Established `analysis/` registry and schema scaffold.
- Added base R standard runner without package installation; mock writes standard packages and lite/full writes blocked standard packages.
- Added generic mock input and standard mock result package.
- Added per-module fixed mock inputs and fixed standard result package fixtures for all registered modules.
- Added DEG to the standard analysis module registry with a mock input, mock standard result package, and base R lite fixture standard package; full standard worker execution remains blocked.
- Added resource manifest skeleton with blocked full resources.
- Added resource lock evidence schema and a mock fixture resource evidence payload; locked resources now require schema-valid evidence before they can pass manifest validation.
- Added static contract tests that do not require R.
- Added a mock-mode task bridge that copies module fixture packages, records task status, validates the package, and registers a result-index entry without requiring R.
- Added an explicit Rscript worker backend for the task bridge that invokes `analysis/runners/run_module.R`, validates the package, and records worker provenance in the result index.
- Materialized `module_input.json` inside direct standard R runner output packages and changed direct runner `worker_invocation.input_manifest` to package-local `module_input.json`.
- Materialized `module_input.json` for all standard task-bridge outcomes, including Python fixture copy and validation/mode-blocked packages, so `logs/worker_invocation.json` can always point to an auditable input manifest.
- Added `logs/worker_invocation.json` for all standard task-bridge outcomes, and registered it in result-index log artifacts after `worker.log`.
- Added `analysis/schemas/output/worker_invocation.schema.json` and validation blockers for missing or invalid task-bridge/standard-worker invocation manifests.
- Added result-package-level schema validation against `analysis/schemas/output/result_package.schema.json`; validation payloads now expose the synthesized package manifest and block package-level directory contract drift.
- Exposed synthesized package manifest metadata in `build_standard_analysis_package_catalog()` and `build_standard_analysis_package_detail()`, and rendered it in Results Browser.
- Added schema-driven module input validation in the task bridge so required-field, enum, type, minLength, and nested runtime field drift from `analysis/schemas/input/module_input.schema.json` is blocked before worker execution.
- Added standard package validation for materialized task-center input manifests: `worker_invocation.input_manifest` must point to package-local `module_input.json`, and that manifest must pass schema and expected module/task/mode checks.
- Exposed materialized input manifest metadata in `build_standard_analysis_package_catalog()` and `build_standard_analysis_package_detail()` so UI/report consumers can discover package-local `module_input.json` without reading worker-private output conventions.
- Added an Analysis Center standard package input-manifest gate row so malformed or missing package-local `module_input.json` appears in UI blockers.
- Added a Results Browser input-manifest table so standard package input metadata is visible outside developer diagnostics.
- Split standard R worker provenance hashing so `input_hash` tracks the full input manifest and `parameter_hash` tracks the `parameters` object separately.
- Expanded resource governance with blocked full-mode resource locks and module-specific full-mode resource blockers.
- Added a standard analysis package catalog and exposed it in Analysis Center state without upgrading testing-level packages.
- Exposed worker invocation diagnostics in the standard package catalog and Analysis Center state.
- Added standard package artifact manifests for declared tables/plots/reports plus package logs, exposed through the catalog for UI-safe result browsing.
- Added the first standard worker lite paths: DEG base R two-group fixture, enrichment base R ORA, survival base R KM/log-rank, univariate base R clinical association, multivariate base R linear model, immune infiltration base R signature mean heatmap, and spatial transcriptomics base R spot QC/coordinate SVG fixtures producing testing-level standard result packages.
- Added docking and molecular dynamics lite external-tool adapter contract fixtures that produce standard command-manifest packages without executing AutoDock Vina/GROMACS or generating scientific docking/MD results.
- Added controlled enrichment ORA/GSEA standard result package sidecars registered in result index v2.
- Added controlled DEG standard result package sidecars for successful two-group Python formal DEG and multi-factor limma/DESeq2/edgeR fixture results, registered in result index v2 without enabling new execution, plot/report-ready output, or clinical interpretation.
- Added controlled KM/log-rank and Cox univariate standard result package sidecars plus indexed worker invocation manifests registered in result index v2 without enabling clinical conclusions, risk grouping, plot/report-ready output, or isolated worker claims.
- Added exploratory immune/TME scoring standard result package sidecars registered in result index v2 without enabling GSVA/CellChat/Seurat, report-ready output, clinical interpretation, or isolated worker claims.
- Added local Pearson correlation standard result package sidecars registered in result index v2 without enabling report-ready output, causal interpretation, clinical interpretation, or isolated worker claims.
- Added per-module manifest scaffolds for all target modules.
- Added Docker/renv environment split scaffolds with explicit detect-first and no runtime-install policy.
- Added `analysis/registry/analysis_environments.json` as the central environment boundary registry, with tests that module manifests match registered Dockerfiles, renv locks, allowed-module lists, heavy-dependency policy, and runtime-install policy.
- Added `external_analysis_environments/` and `external_analysis_resources/` lightweight evidence handoff directories with `.gitignore` guards. They establish where external environment/resource evidence can be placed without committing heavy dependencies or resource caches, and they do not change full-mode readiness.
- Added `validate_analysis_environment_registry()` to make environment-registry validity and full-readiness status consumable by runtime gates, UI diagnostics, and future reports.
- Added Analysis Center environment gate rows for registry structure and full R environment readiness.
- Added `build_analysis_remediation_queue()` to expose current P1 architecture gaps as blocked, manual, read-only remediation items with source issues, recommended files, and required evidence.
- Added `build_standard_worker_migration_matrix()` to expose module-level mock/lite/full/formal migration status and to drive the formal-standard-worker P1 issue from evidence instead of a static string.
- Added `analysis/schemas/output/standard_worker_migration_evidence.schema.json` and `validate_standard_worker_migration_evidence()` to block full/formal migration completion claims unless schema-valid standard package, standard R worker boundary, task-center invocation, result-index registration, UI standard-package consumption, and formal semantics preservation evidence is present.
- Added `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json` so the authoritative migration registry itself is schema-checked before formal worker migration completion can be claimed.
- Added Analysis Center remediation rows so the UI can display full environment, full resource, and isolated worker migration blockers without implying full analysis readiness.
- Added architecture and remediation docs.

## 9. Human Decisions Needed

- Whether full analysis environments will be Docker-only, `renv`-only, or both.
- Where large reference resource cache roots should live on user machines.
- Whether existing Bio result index v2 should become the standard result package index or remain a higher-level application index.
- Which module should be migrated first: enrichment or survival.
- Whether molecular docking/MD belongs in the same product release line or a separately gated advanced-analysis line.
