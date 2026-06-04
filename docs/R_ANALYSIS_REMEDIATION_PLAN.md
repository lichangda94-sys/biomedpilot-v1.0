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
- `analysis/registry/analysis_environments.json`
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/result.schema.json`
- `analysis/schemas/output/provenance.schema.json`
- `analysis/schemas/output/result_package.schema.json`
- `analysis/schemas/output/worker_invocation.schema.json`
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
- Migrate existing formal/full algorithms behind the isolated standard worker instead of sidecar or service-adapter execution.

Update: the first result package validator and mock-mode backend adapter now exist under `app/analysis_runtime/`. All registered modules now have fixed mock input and standard result package fixtures.

Update: DEG is now registered as a standard analysis module with a mock input, mock standard result package, and base R lite worker fixture. DEG full/formal standard worker execution remains blocked until the existing controlled DEG runners are migrated behind the standard worker.

Update: the R-side standard runner now accepts `<input_json> <output_dir> <mode>`, copies module-specific mock packages in `mock` mode, writes blocked standard packages for `lite` and `full`, and blocks CLI/input mode mismatches. It remains a contract runner only; no real R algorithms are activated.

Update: standard R worker provenance now computes `input_hash` from the full input manifest and `parameter_hash` from the `parameters` object separately, without adding an R package dependency.

Update: the main-backend task bridge now has an explicit `worker_backend="rscript"` path. It materializes `module_input.json`, invokes the standard R runner, validates the standard package, and registers worker provenance in the result index. Missing `Rscript` is a graceful blocked package.

Update: transitional controlled adapters now route external R commands through `app/analysis_runtime/r_worker.py::run_external_r_command()`. This centralizes subprocess behavior and worker-boundary metadata for enrichment and multi-factor DEG adapters, but still leaves full isolated standard-worker migration pending.

Update: transitional R adapters no longer import `subprocess` or set `subprocess.run` as their own default runner. Optional test runners are still injectable, but the default subprocess owner is now only `app/analysis_runtime/r_worker.py`; an architecture test guards this boundary for enrichment and multi-factor DEG adapters.

Update: the resource manifest now declares required full-mode resources for enrichment, immune infiltration, spatial transcriptomics, docking, and molecular dynamics. `app/analysis_runtime/resources.py` validates the manifest and adds module-specific full-mode blockers until real locks exist.

Update: resource validation now rejects any resource marked `locked` while version, source, hash, license, or cache path still contains placeholder values such as `required_before_full_mode`. Partially prepared blocked resources may carry warnings, but full mode remains blocked until the lock is complete.

Update: the Bioinformatics gene-set resource manager now blocks Reactome/GO/KEGG runtime downloads by default. Common resources remain visible as guidance, but user/UI flows must import GMT files or use externally prepared prelocked resources; parser/download code requires an explicit developer/test override and is not a normal runtime acquisition path.

Update: the standard package catalog now reads result-index `standard_result_package` artifacts and is exposed in Analysis Center state as `standard_analysis_packages`. This is a read-only UI bridge; detailed module result views still need migration.

Update: the standard package catalog now exposes worker-boundary metadata. Packages generated by the standard R worker are identifiable as `standard_r_worker`; compatibility sidecars generated by existing enrichment and multi-factor DEG service adapters are explicitly labeled `legacy_service_adapter_sidecar` with `migration_status=sidecar_only_not_isolated_standard_worker`.

Update: standard package validation now applies a stricter gate to passed full/formal packages. Such packages must include input/parameter hashes, command, random seed field, engine name/version, runtime version containers, package/external-tool version containers, and worker-boundary metadata when not produced by the standard R worker.

Update: DEG now has a `lite` standard worker path. `run_module.R` can execute base R two-group Welch t-tests on fixed local count/metadata fixtures and write a testing-level standard result package. It does not use limma, DESeq2, edgeR, scipy, statsmodels, report-ready output, or clinical interpretation.

Update: enrichment now has a `lite` standard worker path. `run_module.R` can execute a base R hypergeometric ORA fixture with local TERM2GENE files and write a testing-level standard result package. It does not use Reactome/MSigDB/full resources and does not enable report-ready output.

Update: controlled ORA/GSEA R adapters now mirror successful formal enrichment fixture results into standard result package sidecars and register them in result index v2 as `standard_result_package` artifacts. Their provenance records the sidecar-only worker boundary. This does not change the algorithms, does not enable plot/report-ready output, and does not complete isolated worker migration.

Update: controlled DEG executors now mirror successful formal results into standard result package sidecars and register them in result index v2 as `standard_result_package` artifacts. This covers two-group Python controlled formal DEG plus multi-factor limma/DESeq2/edgeR fixture-proven formal results. It preserves result table, task log, parameter manifest, dependency snapshot, hashes, command provenance, and sidecar-only worker-boundary metadata; multi-factor sidecars also preserve formula/contrast provenance and R package versions. This does not enable new DEG execution, plot/report-ready output, clinical interpretation, or complete isolated worker migration.

Update: controlled KM/log-rank and Cox univariate executors now mirror successful controlled formal results into standard result package sidecars and register them in result index v2 as `standard_result_package` artifacts. This preserves result tables, task logs, parameter manifests, dependency snapshots, hashes, engine metadata, and sidecar-only worker-boundary metadata. This does not enable clinical conclusions, risk grouping, plot artifacts, report-ready survival/clinical output, or complete isolated worker migration.

Update: exploratory immune / TME scoring now mirrors score matrix, signature coverage, sample summary, scoring manifest, and receipt artifacts into a standard result package sidecar and registers it in result index v2 as a `standard_result_package` artifact. It remains `mode=lite` and `result_semantics=testing_level`; it does not enable GSVA/CellChat/Seurat, report-ready output, clinical interpretation, or complete isolated worker migration.

Update: local expression correlation now mirrors Pearson correlation result tables and summary logs into a standard result package sidecar and registers it in result index v2 as a `standard_result_package` artifact. It remains `mode=lite` and `result_semantics=testing_level`; it does not enable report-ready output, causal interpretation, clinical interpretation, or complete isolated worker migration.

Update: correlation is now registered as a standard analysis module with a fixed mock input/output package and full-mode blocking. The existing runtime remains a testing-level legacy service-adapter sidecar until a standard worker migration is implemented.

Update: result-index task type aliases are now declared in `analysis/registry/analysis_modules.json` as `result_index_task_types`. The standard package catalog uses that registry-owned mapping when validating whether a result-index entry belongs to a package module, instead of carrying a separate hard-coded task-type map. `analysis:<module_id>` result-index entries are also blocked if the module id is not registered.

Update: survival now has a `lite` standard worker path. `run_module.R` can execute base R KM/log-rank calculations on fixed local survival fixture data and write a testing-level standard result package. It does not generate prognosis, treatment guidance, report-ready survival output, or clinical interpretation.

Update: univariate clinical association now has a `lite` standard worker path. `run_module.R` can execute base R Welch t-test and Pearson correlation calculations on fixed local clinical fixture data and write a testing-level standard result package. It does not generate clinical conclusions, report-ready clinical output, diagnosis, prognosis, or treatment guidance.

Update: multivariate clinical association now has a `lite` standard worker path. `run_module.R` can execute a base R linear model fixture on fixed local clinical fixture data and write a testing-level standard result package. It does not generate clinical conclusions, model selection recommendations, risk scores, report-ready clinical output, diagnosis, prognosis, or treatment guidance.

Update: immune infiltration now has a `lite` standard worker path. `run_module.R` can execute base R signature mean scoring on fixed local expression/signature fixture data and write a testing-level standard result package with a real SVG heatmap fixture. It does not use GSVA, CellChat, Seurat, large signature databases, report-ready immune interpretation, diagnosis, prognosis, or treatment guidance.

Update: spatial transcriptomics now has a `lite` standard worker path. `run_module.R` can execute base R spot QC and coordinate SVG preview on fixed local expression/coordinate fixture data and write a testing-level standard result package. It does not use Seurat, CellChat, spacexr, spatial references, clustering, deconvolution, spatial domain calling, cell-cell communication, or report-ready spatial interpretation.

Update: docking now has a `lite` standard worker adapter-contract path. `run_module.R` can validate fixed local receptor/ligand/config fixtures and write `tables/lite_docking_command_manifest.tsv` plus provenance and limitations. It does not execute AutoDock Vina, does not generate docking poses/scores/affinities, and does not enable full molecular docking.

Update: molecular dynamics now has a `lite` standard worker adapter-contract path. `run_module.R` can validate fixed local topology/coordinate/mdp fixtures and write `tables/lite_md_command_manifest.tsv` plus provenance and limitations. It does not execute GROMACS, does not generate trajectory/energy/RMSD/simulation outputs, and does not enable full molecular dynamics.

Update: lite-mode coverage is now enforced by a registry-driven bridge test. Every module that declares `modes.lite.supported=true` in `analysis/registry/analysis_modules.json` must run through `run_analysis_module_task(..., worker_backend="rscript")`, produce a passed standard result package, register a result-index entry, appear in the standard package catalog, preserve `result_semantics=testing_level`, and keep `report_ready_eligible=false`.

Update: full-mode blocking is now enforced by a registry-driven bridge test. Every module that declares a `full` mode must return a blocked standard result package through `run_analysis_module_task(..., worker_backend="rscript")` before worker execution, preserve empty table/plot/report artifacts, register a blocked result-index entry, expose the blocked package through the standard catalog, and record `r_version=not_executed`, `bioconductor_version=not_executed`, empty package/tool version maps, and `command=analysis_task_bridge_mode_gate`.

Update: blocked full-mode standard packages now include an `analysis_environment` snapshot in `provenance.json` and in the result-index dependency snapshot. The snapshot records the target isolated environment id, Dockerfile, renv lock, heavy-dependency allowance, resource-lock requirement, external-tool-lock requirement, no runtime-install/resource-download policies, module manifest path, required resource ids, and current resource/tool lock blockers. This makes a blocked full request auditable without enabling full execution.

Update: `validate_standard_result_package()` now validates the `analysis_environment` snapshot for `full` packages and any package that declares one. Missing snapshots, schema-version drift, mode/module mismatch, missing Dockerfile/renv/module manifest fields, invalid full-mode isolation policy, invalid runtime-install/resource-download policy, or malformed resource-lock status block the standard package. `build_standard_analysis_package_catalog()` and `build_standard_analysis_package_detail()` expose this snapshot for UI diagnostics.

Update: environment boundaries are now centralized in `analysis/registry/analysis_environments.json`. The registry declares `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`, including Dockerfile, renv lock, allowed modules, heavy-dependency policy, resource/tool lock policy, and no runtime-install policy. Tests verify module manifests match this registry and cannot point analysis execution at `app-dev` or unregistered worker environments.

Update: all standard task-bridge outcomes now write `logs/worker_invocation.json` and register it in result-index log artifacts. The manifest records backend, invocation status, standard entrypoint, command, return code, stdout/stderr, blockers, worker-boundary migration status, and explicit no runtime-install/resource-download policies. Mock fixture copies, validation gates, R worker attempts, and full-mode bridge gates all use this audit record.

Update: direct `analysis/runners/run_module.R` outputs now also write `logs/worker_invocation.json` with `worker_boundary.task_system_invocation=standard_worker_direct_cli`. Focused tests validate direct mock and blocked full runner packages through the same Python standard package validator. The blocked full direct-runner package records target environment/resource-lock snapshots and remains non-executing.

Update: transitional service-adapter sidecar packages now write `logs/worker_invocation.json` with `worker_backend=legacy_service_adapter`, `invocation_status=sidecar_recorded`, and `task_system_invocation=legacy_service_adapter_direct_call`. This covers current formal DEG, multifactor DEG, controlled enrichment, controlled survival/KM/Cox, immune scoring, and correlation sidecar packages while preserving the explicit `sidecar_only_not_isolated_standard_worker` migration status.

Update: standard package validation now requires `logs/worker_invocation.json` for legacy service-adapter sidecar packages as well as task-bridge and standard-worker packages. A sidecar without the invocation manifest is blocked instead of being accepted as a valid standard package.

Update: passed standard result packages now require reproducibility provenance. `validate_standard_result_package()` blocks passed packages missing input hash, parameter hash, random seed field, command, engine name/version, R version, Bioconductor version, R package-version container, or external-tool-version container.

Update: content-level schemas now exist for `result.json` and `provenance.json` under `analysis/schemas/output/result.schema.json` and `analysis/schemas/output/provenance.schema.json`. These schemas mirror the core validator contract for result semantics, artifact declarations, reproducibility hashes, runtime version containers, engine metadata, seed, and command provenance.

Update: standard package validation now blocks `result.json` and `provenance.json` schema-version drift. Packages must use `biomedpilot.analysis.result.v1` and `biomedpilot.analysis.provenance.v1`.

Update: result/provenance payload schema discovery is now explicit. `analysis/registry/analysis_modules.json` declares `standard_result_package.payload_schemas`, every registry module entry declares `result_payload_schema` and `provenance_payload_schema`, and every `analysis/modules/<module_id>/module.json` manifest declares the same payload schema files. Architecture tests guard consistency and file existence.

Update: standard package catalog and detail payloads now expose the result/provenance payload schema paths from the module registry. UI and report consumers can discover the correct schema through `build_standard_analysis_package_catalog()` or `build_standard_analysis_package_detail()` instead of inferring it from validator internals or module-private output conventions.

Update: standard package validation now enforces required fields from the declared result/provenance payload schema files. Packages missing schema-required result fields such as `result_semantics` or `created_at`, or schema-required provenance fields such as `engine` or `command`, are blocked. Main-backend task-bridge blocked packages now write `result_semantics=blocked`, keeping blocked outputs schema-complete.

Update: standard package validation now also enforces basic schema shape from the declared result/provenance payload schemas. It blocks enum/type/minLength drift, array item type drift, and one-level nested object shape drift for fields such as `mode`, `tables`, `warnings`, `engine.version`, and `runtime.package_versions`.

Update: the standard package catalog now maps known Bioinformatics result-index `task_type` values such as `deg`, `ora`, `gsea_preranked`, `survival_km_logrank`, `cox_univariate`, `analysis:immune_infiltration`, and `analysis:correlation` to their expected standard package `module_id`. A mismatched `result.json` or `provenance.json` module id now blocks catalog validation instead of silently passing.

Update: `analysis/schemas/output/worker_invocation.schema.json` now defines the worker invocation manifest contract. `validate_standard_result_package()` requires this manifest for packages produced by `biomedpilot_analysis_task_bridge` or `biomedpilot_standard_r_worker`, and blocks missing or invalid schema version, runtime-install/resource-download policy, backend/status, command/blocker shape, and task-system boundary fields.

Update: the standard package catalog now exposes `worker_invocation`, `worker_backend`, and `worker_invocation_status` from `logs/worker_invocation.json`. Analysis Center can display these diagnostics from the standard package catalog instead of reading module-private R outputs.

Update: `build_standard_analysis_package_detail()` now exposes a UI-safe `artifact_manifest` for declared standard-package tables, plots, reports, and package logs. Catalog rows include this manifest so Analysis Center can discover artifact paths from the standard package contract instead of module-private output conventions.

Update: standard package validation now blocks malformed, missing, absolute, package-external, or wrong-group `tables`/`plots`/`reports` artifact declarations. This turns artifact manifest drift into a contract blocker instead of leaving UI consumers to discover missing files later.

Update: Analysis Center state now exposes `standard_package_gate_rows` for standard package catalog source, package validation, and artifact-manifest validity. The UI can display package-contract blockers without reading module-private R outputs.

Update: Analysis Center result rows now join current result-index entries with the standard package catalog by `result_id`, showing standard package registration status, validation status, package path, and artifact counts. Missing standard packages remain visible as `missing_standard_result_package` instead of being silently treated as valid result output.

Update: the current Bioinformatics Results Browser table now displays standard package contract status for each result row, including registration, validation state, relative package path, and artifact counts. This is a UI consumption step only; it does not change result semantics or make testing/imported/preflight outputs formal.

Update: standard package catalog rows now expose `input_hash`, `parameter_hash`, and `random_seed` from `provenance.json`. The current Bioinformatics Results Browser displays these alongside runtime, engine, command, worker backend, invocation status, worker boundary, and migration status.

Update: the current Bioinformatics Results Browser now displays a standard package artifact manifest table for declared `tables`, `plots`, `reports`, and package `logs`. The table is derived from the standard package catalog and uses package-relative paths only.

Update: `config/bioinformatics/package_requirements.yaml` now records R/Bioconductor packages as a detect-first capability inventory only. It explicitly forbids runtime install/download and default app dependency use, and an architecture test guards it against becoming an install manifest.

Update: Bioinformatics analysis default configs that mention heavy R packages now carry the same no-install boundary. `analysis_defaults.yaml`, `enrichment_defaults.yaml`, and `survival_defaults.yaml` are parameter/capability defaults only; they explicitly forbid runtime install/download and default app dependency use, and an architecture test guards those files.

## Phase R1: Task-System Bridge

Scope:

- Add a Python bridge that submits module jobs by writing `module_input.json`.
- The bridge calls the standard worker only through task execution, not directly from UI.
- The UI consumes `result.json`, `provenance.json`, and artifact manifest metadata.

Acceptance:

- Every registered module can run `mock` mode through the task system using its fixed fixture package. **Completed for mock mode.**
- The R-side runner can generate a mock standard package from a module fixture and a blocked standard package for disabled modes. **Completed for runner contract.**
- The task bridge can explicitly call the R-side standard runner for mock packages without enabling lite/full real analysis. **Completed for worker-boundary contract.**
- Transitional controlled R adapters route Rscript commands through the shared analysis runtime boundary instead of owning direct R subprocess calls. **Completed for enrichment and multi-factor DEG adapters.**
- Transitional controlled R adapters do not own subprocess imports or `subprocess.run` defaults. **Completed for enrichment and multi-factor DEG adapters.**
- Analysis Center can discover standard result packages from the result index without scanning module-specific output folders. **Completed for state-level preview.**
- Analysis Center can read worker invocation diagnostics from the standard package catalog. **Completed for task-bridge standard packages.**
- Analysis Center can read declared standard-package artifact paths for tables, plots, reports, and logs without module-private output coupling. **Completed for catalog artifact manifest.**
- Standard package validation blocks declared table/plot/report artifacts that are missing or outside their standard package directories. **Completed for artifact declaration gate.**
- Analysis Center exposes standard package validation/artifact blockers as gate rows. **Completed for UI gate preview.**
- Analysis Center result rows expose per-result standard package registration, validation, path, and artifact-count status. **Completed for result-row package preview.**
- Results Browser displays per-result standard package registration, validation, path, and artifact-count status in the user-visible result table. **Completed for current results table preview.**
- Results Browser displays standard package provenance and worker-boundary rows including runtime, engine, command, hashes, seed, worker backend, invocation status, boundary type, and migration status. **Completed for current provenance/worker preview.**
- Results Browser displays standard package artifact manifest rows for declared tables, plots, reports, and logs without scanning module-private output folders. **Completed for current artifact manifest preview.**
- Standard package catalog/detail payloads expose result/provenance payload schema paths for UI/report consumers. **Completed for UI-safe schema discovery.**
- Standard package validation blocks result/provenance payloads that omit schema-required fields, and task-bridge blocked packages now include `result_semantics=blocked`. **Completed for schema-required payload gate.**
- Standard package validation blocks result/provenance payload type, enum, minLength, array item, and one-level nested object shape drift. **Completed for schema-shape payload gate.**
- Bioinformatics R package requirement config remains a detect-first capability inventory, not a runtime install manifest or default app dependency source. **Completed for dependency policy guard.**
- DEG can run `lite` mode through the standard R worker using fixed local count/metadata fixture data. **Completed for DEG lite worker.**
- Enrichment can run `lite` mode through the standard R worker using fixed local fixture resources. **Completed for enrichment lite worker.**
- Survival can run `lite` mode through the standard R worker using fixed local fixture data. **Completed for second lite worker.**
- Univariate can run `lite` mode through the standard R worker using fixed local clinical fixture data. **Completed for third lite worker.**
- Multivariate can run `lite` mode through the standard R worker using fixed local clinical fixture data. **Completed for fourth lite worker.**
- Immune infiltration can run `lite` mode through the standard R worker using fixed local expression/signature fixture data and generate a real SVG heatmap fixture. **Completed for fifth lite worker.**
- Spatial transcriptomics can run `lite` mode through the standard R worker using fixed local expression/coordinate fixture data and generate a real SVG spot QC preview. **Completed for sixth lite worker.**
- Docking can run `lite` mode through the standard R worker as an external-tool command-manifest contract without executing AutoDock Vina. **Completed for docking adapter boundary fixture.**
- Molecular dynamics can run `lite` mode through the standard R worker as an external-tool command-manifest contract without executing GROMACS. **Completed for MD adapter boundary fixture.**
- Every registered `lite` module can run through the same main-backend task bridge and standard R worker package contract. **Completed with registry-driven focused test.**
- Every registered `full` module is blocked through the same main-backend task bridge with a standard result package, result-index entry, catalog row, and non-executed provenance. **Completed with registry-driven focused test.**
- Every registered `full` module records target isolated environment and resource/tool lock status in the blocked standard package and result-index dependency snapshot. **Completed for full-mode bridge gate.**
- Full-mode standard packages are blocked by validation if target environment/resource-lock snapshots are missing or malformed. **Completed for validator/catalog gate.**
- All standard task-bridge outcomes write a worker invocation manifest and register it in result-index log artifacts. **Completed for task-bridge paths.**
- Task-bridge and standard-worker packages are blocked if their worker invocation manifest is missing or violates the schema/policy contract. **Completed for validator gate.**
- Direct standard R runner mock and blocked full outputs validate as standard packages without requiring heavy R packages or enabling full execution. **Completed for direct runner contract.**
- Current service-adapter sidecar standard packages expose worker invocation diagnostics without claiming isolated standard-worker execution. **Completed for sidecar diagnostics.**
- Output package includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, `logs/`.
- Passed full/formal standard packages block if provenance or worker-boundary metadata is incomplete. **Completed for validator gate.**
- No R installation is required.

## Phase R2: Enrichment Lite Worker

Recommended first module because controlled ORA/GSEA R adapters already exist.

Scope:

- Wrap existing enrichment controlled adapters behind the standard worker.
- Use lightweight local TERM2GENE fixtures.
- No ReactomePA/msigdbr full resources in lite mode.

Acceptance:

- `mock` and base R ORA `lite` pass through the standard worker. **Completed for fixture ORA.**
- Controlled ORA/GSEA R fixture results are mirrored into standard package sidecars and indexed as `standard_result_package`. **Completed for package sidecar.**
- Controlled ORA/GSEA standard package sidecars record `legacy_service_adapter_sidecar` worker-boundary metadata. **Completed for migration-status transparency.**
- `full` remains blocked until resource locks and full env exist. **Still required.**
- Provenance records R version, input hash, parameter hash, seed, and command. **Completed for fixture ORA.**
- Package-version capture for non-base R lite/full workers remains pending.
- Existing controlled enrichment R adapters still need full task-worker isolation instead of direct service-level subprocess execution.

## Phase R3: Survival / Clinical R-Native Worker

Scope:

- Migrate survival, univariate, and multivariate clinical association behind the same worker interface.
- Keep clinical conclusion disabled.
- Require standard result package outputs.

Status: started with base R lite fixture.

Completed:

- Survival `mock` remains available without R.
- Survival `lite` can run a fixed KM/log-rank fixture through `analysis/runners/run_module.R`.
- Standard result package includes `result.json`, `provenance.json`, `tables/lite_km_curve.tsv`, `tables/lite_logrank_result.tsv`, `reports/README_lite.md`, and `logs/worker.log`.
- Controlled KM/log-rank formal results are mirrored into standard package sidecars with `legacy_service_adapter_sidecar` boundary metadata.
- Controlled Cox univariate formal results are mirrored into standard package sidecars with `legacy_service_adapter_sidecar` boundary metadata.
- Controlled KM/log-rank and Cox univariate sidecars now write `logs/worker_invocation.json` and register it in result index v2 as `analysis_worker_invocation_manifest`.
- Univariate `mock` remains available without R.
- Univariate `lite` can run a fixed base R clinical association fixture through `analysis/runners/run_module.R`.
- Univariate standard result package includes `result.json`, `provenance.json`, `tables/lite_univariate_association.tsv`, `reports/README_lite.md`, and `logs/worker.log`.
- Multivariate `mock` remains available without R.
- Multivariate `lite` can run a fixed base R linear model fixture through `analysis/runners/run_module.R`.
- Multivariate standard result package includes `result.json`, `provenance.json`, `tables/lite_multivariate_association.tsv`, `reports/README_lite.md`, and `logs/worker.log`.
- Clinical conclusion remains disabled for survival, univariate, and multivariate lite packages.

Remaining:

- Migrate existing controlled KM/Cox runtime behind the standard worker.
- Keep full clinical analysis blocked until environment/resource locks are approved.

Acceptance:

- `mock` passes without R.
- `lite` passes with lightweight R packages/data. **Completed for survival, univariate, and multivariate base R fixtures.**
- `full` blocked until container/renv is approved.

## Phase R4: DEG R Worker Alignment

Scope:

- Wrap limma/DESeq2/edgeR multi-factor code behind the same standard worker.
- Preserve existing result index v2 and DEG audit package, but emit standard result package too.

Acceptance:

- No Python service embeds long-running R execution as a UI request side effect.
- All outputs have standard package metadata.

Status: started with result-package sidecar alignment.

Completed:

- Successful two-group Python formal DEG results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Successful controlled limma multi-factor fixture results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Successful controlled DESeq2 multi-factor fixture results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Successful controlled edgeR multi-factor fixture results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Multi-factor DEG standard package sidecars record `legacy_service_adapter_sidecar` worker-boundary metadata.
- Blocked incompatible non-count DESeq2/edgeR requests still stop before result index registration.

Remaining:

- Move long-running limma/DESeq2/edgeR Rscript execution behind the standard task worker instead of service-level subprocess calls.
- Replace the transitional `run_external_r_command()` sidecar boundary with isolated standard-worker task execution.
- Add isolated full worker environment proof before claiming complete DEG R worker migration.
- Keep plot/report-ready output and clinical interpretation disabled unless their existing gates pass.

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
analysis/registry/analysis_environments.json
```

Status: scaffolded, not restored.

Completed:

- Added Dockerfile scaffolds for app-dev, bio-core, bio-full, spatial-full, chem-full, and chem-gpu.
- Added empty policy lockfiles for app, bio-core, bio-full, spatial-full, and chem-full.
- Added the central environment registry that maps modules to allowed worker environments and locks app-dev out of analysis execution.
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

## Phase R5a: Docking External Tool Adapter Boundary

Scope:

- Keep AutoDock Vina outside app-dev and ordinary R bio-core environments.
- Prove a standard result package can describe the external-tool command boundary before full tool execution exists.
- Do not generate scientific docking results in lite mode.

Status: started with command-manifest contract fixture.

Completed:

- Docking `mock` remains available without R.
- Docking `lite` can run through `analysis/runners/run_module.R` using fixed receptor, ligand, and config fixture files.
- The lite package includes `result.json`, `provenance.json`, `tables/lite_docking_command_manifest.tsv`, `reports/README_lite.md`, and `logs/worker.log`.
- Provenance records `external_tool_versions.AutoDock Vina=not_executed_lite_contract`.
- The result warnings explicitly state that the external tool was not executed and no scientific docking result was generated.

Remaining:

- Full AutoDock Vina execution remains blocked until `r-chem-full` image/tool/resource locks are approved.

Acceptance:

- Lite command-manifest package is testing-level only.
- No AutoDock Vina binary is required in app-dev.
- No runtime tool install/download is performed.

## Phase R5b: Molecular Dynamics External Tool Adapter Boundary

Scope:

- Keep GROMACS outside app-dev, ordinary R bio-core, and ordinary chem-full environments.
- Prove a standard result package can describe the external-tool command boundary before full GPU/tool execution exists.
- Do not generate scientific molecular dynamics results in lite mode.

Status: started with command-manifest contract fixture.

Completed:

- Molecular dynamics `mock` remains available without R.
- Molecular dynamics `lite` can run through `analysis/runners/run_module.R` using fixed topology, coordinate, and mdp fixture files.
- The lite package includes `result.json`, `provenance.json`, `tables/lite_md_command_manifest.tsv`, `reports/README_lite.md`, and `logs/worker.log`.
- Provenance records `external_tool_versions.GROMACS=not_executed_lite_contract`.
- The result warnings explicitly state that the external tool was not executed and no scientific molecular dynamics result was generated.

Remaining:

- Full GROMACS execution remains blocked until `r-chem-gpu` image/tool/resource locks are approved.
- Trajectory, energy, RMSD, simulation metrics, and scientific MD outputs remain unavailable in lite mode.

Acceptance:

- Lite command-manifest package is testing-level only.
- No GROMACS binary is required in app-dev.
- No runtime tool install/download is performed.

## Phase R6: Resource Governance

Scope:

- Lock Reactome, MSigDB, GO, KEGG, org dbs, spatial references, docking resources, and MD templates.
- Record version, source, hash, license, and cache path.

Status: contract gate present; real locks pending.

Completed:

- Declared blocked full-mode resources for Reactome, MSigDB, GO, KEGG, human org db, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and MD templates.
- Added resource manifest validation and module-specific full-mode resource blockers.
- Kept runtime downloads forbidden for every resource entry.
- Blocked Reactome/GO/KEGG runtime downloads in the Bioinformatics gene-set resource manager and enrichment resource catalog; UI/user flows now require GMT import or prelocked resources.
- Added negative validation for fake `locked` resources whose version/source/hash/license/cache fields still contain placeholder values.

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

Status:

- Immune infiltration `mock` remains available without R.
- Immune infiltration `lite` can run fixed base R signature mean scoring through `analysis/runners/run_module.R`.
- Immune infiltration standard result package includes `result.json`, `provenance.json`, `tables/lite_immune_scores.tsv`, `plots/lite_immune_heatmap.svg`, `reports/README_lite.md`, and `logs/worker.log`.
- Existing exploratory immune/TME scoring service outputs now also mirror into a standard package sidecar with score matrix, coverage, sample summary, manifest, receipt, and limitations artifacts.
- Full immune analysis remains blocked until GSVA/CellChat/Seurat/signature resource locks and isolated worker environments are approved.
- Spatial transcriptomics `lite` can run fixed base R spot QC and coordinate SVG preview through `analysis/runners/run_module.R`.
- Spatial transcriptomics standard result package includes `result.json`, `provenance.json`, `tables/lite_spatial_spot_metrics.tsv`, `tables/lite_spatial_qc_summary.tsv`, `plots/lite_spatial_spot_qc.svg`, `reports/README_lite.md`, and `logs/worker.log`.
- Full spatial analysis remains blocked until Seurat/CellChat/spacexr/spatial reference locks and isolated worker environments are approved.
- Docking `lite` can run a command-manifest adapter contract through `analysis/runners/run_module.R` without executing AutoDock Vina or generating scientific docking results.
- Molecular dynamics `lite` can run a command-manifest adapter contract through `analysis/runners/run_module.R` without executing GROMACS or generating trajectory, energy, RMSD, simulation metrics, or scientific MD results.

Rules:

- Spatial goes to `r-spatial-full`.
- Docking/MD use R adapters to external tools only.
- Docking/MD never share the normal bio-core environment.

## Current Stop Rule

Do not migrate algorithms until the standard package validator and one mock-mode task-system bridge are in place.
