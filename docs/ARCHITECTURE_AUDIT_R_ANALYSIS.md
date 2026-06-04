# Architecture Audit: R Analysis Kernel

Date: 2026-06-04

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

HEAD audited before changes: `4e66e5e848cac38742781cf58d629af9d85291e6`

## 1. Current Fit to Target Mode

Current state: **FAIL with partial mitigations**.

The project has useful Bioinformatics and Meta Analysis contracts, result indexes, gates, tests, and detect-first R adapters. However, before this audit there was no single top-level `analysis/` module registry, no uniform `run_module(input_json, output_dir, mode)` worker boundary, no universal input/output schema, and no guaranteed standard result package contract for every future R-native module.

This audit added a minimal boundary scaffold:

- `analysis/registry/analysis_modules.json`
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/result_package.schema.json`
- `analysis/runners/run_module.R`
- `analysis/fixtures/inputs/mock_analysis_input.json`
- `analysis/fixtures/outputs/mock_result_package/**`
- `analysis/resources/manifest.json`
- `docs/R_ANALYSIS_ARCHITECTURE.md`

The scaffold fixes the most basic registry/schema/mock result-package boundary. A minimal main-backend task bridge now also exists for mock-mode standard result packages:

- `app/analysis_runtime/registry.py`
- `app/analysis_runtime/standard_package.py`
- `app/analysis_runtime/task_bridge.py`

The bridge creates a `TaskCenter` task, writes a standard result package, validates it, and registers a result-index entry. It does not execute R packages or enable lite/full algorithms yet.

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
- CLI mode and input manifest mode mismatches are blocked.
- Paths containing spaces are supported.
- No R package install/download or `library(...)` import is used.

The main-backend bridge now has two mock-safe paths:

- `worker_backend="python_fixture"` copies fixed standard packages without requiring R.
- `worker_backend="rscript"` writes `module_input.json`, invokes the standard R runner, validates the package, and registers result-index entries from worker provenance.
- Missing `Rscript` produces a blocked standard result package, not a traceback or installer path.

External R command execution for transitional controlled adapters is now centralized:

- `app/analysis_runtime/r_worker.py` exposes `run_external_r_command()`.
- Existing controlled enrichment and multi-factor DEG adapters use this shared runtime boundary for Rscript commands instead of directly owning `subprocess.run`.
- The returned invocation payload includes owner, command, stdout/stderr, return code, blockers, and `worker_boundary.boundary_type=analysis_runtime_external_r_command`.
- This reduces scattered R execution logic, but it is still a transition boundary; it does not yet make those adapters isolated standard-worker tasks.

Resource governance now has a programmatic gate:

- `analysis/resources/manifest.json` records mock fixture resources and full-mode locks for Reactome, MSigDB, GO, KEGG, organism annotation databases, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and MD templates.
- `app/analysis_runtime/resources.py` validates required fields, forbids runtime downloads, and reports module-specific full-mode blockers.
- `locked` resources are rejected if version, source, hash, license, or cache path still contains placeholder values such as `required_before_full_mode`; this prevents a resource from being falsely marked full-mode ready.
- Blocked resources may carry partial future lock metadata, but they still produce module-specific full-mode blockers until their status is changed to a fully validated `locked` entry.
- Full mode remains blocked until these resources have real version, hash, license, and cache-path locks.

Standard package discovery is now available to the UI state layer:

- `app/analysis_runtime/package_catalog.py` reads only result-index `standard_result_package` artifacts.
- `build_analysis_center_state()` exposes `standard_analysis_packages` and developer diagnostics from that catalog.
- The catalog now exposes `worker_boundary_type` and `worker_migration_status`, so standard R worker packages can be distinguished from legacy service-adapter sidecars.
- `validate_standard_result_package()` now blocks passed full/formal packages if they are missing required provenance fields, runtime/package/tool version containers, command, hashes, random seed field, engine metadata, or worker-boundary metadata for non-standard-worker sidecars.
- Testing-level mock packages remain testing-level and do not become formal/report-ready results.

Existing controlled enrichment ORA/GSEA R adapters now write a standard result package sidecar:

- `app/bioinformatics/enrichment_r_adapter.py` mirrors the controlled ORA/GSEA result table into `analysis/standard_packages/<result_id>/`.
- The sidecar includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar` and `migration_status=sidecar_only_not_isolated_standard_worker`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- This is a package-contract migration step, not a claim that all formal R algorithms already run through the isolated standard worker.

Existing controlled multi-factor DEG R adapters now write a standard result package sidecar:

- `app/bioinformatics/deg_engine/multifactor_r_runner.py` mirrors successful limma, DESeq2, and edgeR fixture-proven formal result tables into `analysis/standard_packages/<result_id>/`.
- The sidecar includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- The sidecar preserves the parameter manifest, dependency snapshot, formula, contrast, covariates, batch variables, input/parameter/table hashes, R/package versions, and Rscript command provenance.
- The sidecar provenance records `worker_boundary.boundary_type=legacy_service_adapter_sidecar` and `migration_status=sidecar_only_not_isolated_standard_worker`.
- The current result index registers the sidecar as an `output_artifacts` item with `artifact_type=standard_result_package`.
- This is a package-contract migration step, not a claim that multi-factor DEG has been fully migrated into the isolated standard worker.

The first lightweight worker paths are now available:

- `analysis/runners/run_module.R` supports `module_id=deg`, `mode=lite` using base R Welch t-tests and fixed repository count/metadata fixtures.
- `analysis/runners/run_module.R` supports `module_id=enrichment`, `mode=lite` using base R hypergeometric ORA and fixed repository TERM2GENE fixtures.
- `analysis/runners/run_module.R` supports `module_id=survival`, `mode=lite` using base R KM/log-rank calculations and fixed repository survival fixture data.
- `analysis/runners/run_module.R` supports `module_id=univariate`, `mode=lite` using base R univariate clinical association calculations and fixed repository clinical fixture data.
- `analysis/runners/run_module.R` supports `module_id=multivariate`, `mode=lite` using base R linear model calculations and fixed repository clinical fixture data.
- `analysis/runners/run_module.R` supports `module_id=immune_infiltration`, `mode=lite` using base R signature mean scoring and fixed repository expression/signature fixture data.
- The DEG lite path writes a standard result package with `tables/lite_deg_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The enrichment lite path writes a standard result package with `tables/lite_ora_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The survival lite path writes a standard result package with `tables/lite_km_curve.tsv`, `tables/lite_logrank_result.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The univariate lite path writes a standard result package with `tables/lite_univariate_association.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The multivariate lite path writes a standard result package with `tables/lite_multivariate_association.tsv`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- The immune infiltration lite path writes a standard result package with `tables/lite_immune_scores.tsv`, `plots/lite_immune_heatmap.svg`, `result.json`, `provenance.json`, `reports/README_lite.md`, and `logs/worker.log`.
- These lite packages are `testing_level`; formal DEG, limma/DESeq2/edgeR execution, full enrichment, Reactome/MSigDB resources, GSVA/CellChat/Seurat resources, full survival/clinical packages, plot/report-ready export, prognosis, diagnosis, treatment guidance, and clinical interpretation remain disabled.

A first environment isolation scaffold now also exists:

- `analysis/modules/<module_id>/module.json` for DEG, survival, univariate, multivariate, enrichment, immune infiltration, spatial transcriptomics, docking, and molecular dynamics.
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

These files are policy scaffolds only. They do not restore packages, install full R dependencies, or prove full analysis readiness.

## 2. PASS / WARN / FAIL Table

| Requirement | Status | Evidence |
| --- | --- | --- |
| Unified analysis module directory | WARN | Added `analysis/` and `analysis/modules/<module_id>/module.json`; existing algorithms still live under `app/bioinformatics/**`. |
| Module registry | PASS | Added `analysis/registry/analysis_modules.json`. |
| Unified entrypoint | WARN | Added and tested `analysis/runners/run_module.R` for mock, DEG/enrichment/survival/univariate/multivariate/immune lite standard packages, and blocked unsupported/full standard packages; existing formal real modules do not call it yet. |
| Mock/lite/full design | WARN | Registry declares all three modes; every module has fixed mock input/output fixtures; DEG, enrichment, survival, univariate, multivariate, and immune infiltration have base R lite fixtures; other lite modes and full modes remain blocked pending migration. |
| Unified input/output schema | PASS | Added input and result package schemas. |
| Every module outputs `result.json` / `provenance.json` | WARN | Mock fixtures prove standard package shape for every registered module; controlled enrichment ORA/GSEA and controlled multi-factor DEG R fixture results now write standard sidecar packages; other existing real algorithms still use varied structures. |
| Every module outputs `tables/`, `plots/`, `reports/`, `logs/` | WARN | Mock fixtures prove required directories for every registered module; existing real algorithms not fully normalized. |
| Frontend consumes standard package only | WARN | Analysis Center state now exposes a standard package catalog from result-index artifacts and worker-boundary metadata; existing detailed result views still consume module-specific result indexes and service payloads. |
| Main backend task-system invocation | WARN | A mock/lite bridge now creates `TaskCenter` entries and result-index entries; it can explicitly invoke the standard R runner for mock, DEG-lite, enrichment-lite, survival-lite, univariate-lite, multivariate-lite, and immune-lite packages. Existing controlled enrichment and multi-factor DEG sidecars are now labeled as legacy service-adapter sidecars; direct service subprocess calls still remain. |
| Runtime R package installation in user flow | PASS | Search found no active non-legacy `install.packages`, `BiocManager::install`, `pak::pkg_install`, or `remotes::install_github`. |
| Heavy dependencies in default dev env | PASS/WARN | Heavy R packages are detect-first external dependencies, not default Python package deps; full env split is not complete. |
| Environment split | WARN | Docker/renv scaffold exists for `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`; not build/restoration proven. |
| `renv.lock` equivalent | WARN | Empty policy lockfiles exist; real package locks are not restored or approved. |
| Full analysis Docker image | WARN | Dedicated Dockerfile scaffolds exist; no full image build or package restoration is proven. |
| Large resources version/hash/license/cache | WARN | Added blocked full-mode resource ledger and validator; `locked` resources with placeholder fields now fail validation; real resource locks are incomplete. |
| Provenance captures versions/hashes/seed/command | WARN | The standard R worker records separate input and parameter hashes plus seed and command; full/formal standard package validation now blocks missing provenance containers, but package/tool version capture is still incomplete for unmigrated formal/full modules. |
| DEG/survival/univariate/multivariate/enrichment/immune/spatial/docking/MD share interface | WARN | Registry declares target modules; mock packages exist for all registered modules, and first R-native lite workers exist for DEG, enrichment, survival, univariate, multivariate, and immune infiltration; formal/full migration remains pending. |
| Docking/MD external tool adapters | FAIL | Target registry only; no adapters. |
| Default dev can start without full analysis deps | PASS | Current source smoke historically works without requiring full R environments; scaffold test does not require R. |

## 3. Top 5 Architecture Risks

1. **P0/P1: R analysis logic is not yet isolated behind a universal worker.** Current controlled R adapters now call a shared `analysis_runtime` external R command boundary instead of owning direct `subprocess.run`, and a standard bridge exists for mock, DEG lite, enrichment lite, survival lite, univariate lite, multivariate lite, and immune lite. Most existing formal algorithms are still not migrated into isolated standard-worker tasks.
2. **P1: Environment split is scaffold-only.** Docker/renv boundaries now exist for `r-bio-core`, `r-bio-full`, `r-spatial-full`, and `r-chem-full`, but no full worker image has been built or restored.
3. **P1: Standard result package is not universal.** Existing modules use result index entries, report packages, and custom paths rather than always producing `result.json` and `provenance.json`; controlled enrichment ORA/GSEA and controlled multi-factor DEG R fixture results are now partially remediated with sidecar packages that are explicitly labeled as legacy service-adapter sidecars.
4. **P1: Large resource governance is incomplete.** Required full-mode resources are now declared and blocked, and fake `locked` entries with placeholder values are rejected, but resources still need real version, source, hash, license, and cache-path locks.
5. **P2/P3: UI and backend are still aware of module-specific payloads.** Analysis Center state has a standard package catalog, but detailed result views should eventually consume standard result package metadata rather than individual R package output shapes.

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
| No lite/full environment split | No `docker/` or `renv` split existed before scaffold | Partially fixed with scaffold plus DEG, enrichment, survival, univariate, multivariate, and immune base R lite fixtures; real package locks and builds pending. |
| No universal module schema | Missing before audit | Fixed at initial schema level. |
| No complete resource lock | Only module-specific gates/docs existed | Blocked resource ledger and validator added; fake locked resources with placeholder values are blocked; real locks pending. |
| Full analysis no independent container | No Docker image split before scaffold | Partially fixed with Dockerfile scaffolds; real full image build pending. |
| UI/backend do not yet call standard worker | Existing direct service calls remain | Partially fixed for mock task bridge, standard package catalog, and controlled enrichment sidecar output; current UI algorithms not fully migrated. |

### P2

| Issue | Evidence |
| --- | --- |
| Tests do not yet prove all lite/full modules through one interface | Static tests and bridge tests now prove all registered modules can run mock through one interface, and DEG/enrichment/survival/univariate/multivariate/immune can run lite fixtures through the same R worker; other lite/full modules remain blocked. |
| Logs/provenance differ by module | Existing modules have custom log artifacts and result indexes; full/formal standard package sidecars now have a stricter provenance gate. |
| Example data is incomplete for every declared module | Generic and per-module mock fixtures exist for all registered modules; lite fixtures exist for DEG, enrichment, survival, univariate, multivariate, and immune infiltration only. |

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
4. Add lite mode for selected modules with lightweight fixture data and no large downloads. **Started with DEG, enrichment, survival, univariate, multivariate, and immune infiltration fixtures.**
5. Move full mode to an isolated `renv`/Docker environment.
6. Repeat module by module: survival, univariate, multivariate, enrichment, immune infiltration, then spatial/chem.

## 7. Recommended First Files to Modify Next

1. `app/bioinformatics/enrichment_r_adapter.py`
2. `app/bioinformatics/deg_engine/multifactor_r_runner.py`
3. `app/bioinformatics/analysis_task_runs.py`
4. `app/bioinformatics/results/registry.py`
5. `app/bioinformatics/analysis_ui/state.py`

## 8. Completed Changes in This Audit

- Established `analysis/` registry and schema scaffold.
- Added base R standard runner without package installation; mock writes standard packages and lite/full writes blocked standard packages.
- Added generic mock input and standard mock result package.
- Added per-module fixed mock inputs and fixed standard result package fixtures for all registered modules.
- Added DEG to the standard analysis module registry with a mock input, mock standard result package, and base R lite fixture standard package; full standard worker execution remains blocked.
- Added resource manifest skeleton with blocked full resources.
- Added static contract tests that do not require R.
- Added a mock-mode task bridge that copies module fixture packages, records task status, validates the package, and registers a result-index entry without requiring R.
- Added an explicit Rscript worker backend for the task bridge that invokes `analysis/runners/run_module.R`, validates the package, and records worker provenance in the result index.
- Split standard R worker provenance hashing so `input_hash` tracks the full input manifest and `parameter_hash` tracks the `parameters` object separately.
- Expanded resource governance with blocked full-mode resource locks and module-specific full-mode resource blockers.
- Added a standard analysis package catalog and exposed it in Analysis Center state without upgrading testing-level packages.
- Added the first standard worker lite paths: DEG base R two-group fixture, enrichment base R ORA, survival base R KM/log-rank, univariate base R clinical association, multivariate base R linear model, and immune infiltration base R signature mean heatmap fixtures producing testing-level standard result packages.
- Added controlled enrichment ORA/GSEA standard result package sidecars registered in result index v2.
- Added controlled multi-factor DEG R standard result package sidecars for successful limma/DESeq2/edgeR fixture results, registered in result index v2 without enabling new execution, plot/report-ready output, or clinical interpretation.
- Added per-module manifest scaffolds for all target modules.
- Added Docker/renv environment split scaffolds with explicit detect-first and no runtime-install policy.
- Added architecture and remediation docs.

## 9. Human Decisions Needed

- Whether full analysis environments will be Docker-only, `renv`-only, or both.
- Where large reference resource cache roots should live on user machines.
- Whether existing Bio result index v2 should become the standard result package index or remain a higher-level application index.
- Which module should be migrated first: enrichment or survival.
- Whether molecular docking/MD belongs in the same product release line or a separately gated advanced-analysis line.
