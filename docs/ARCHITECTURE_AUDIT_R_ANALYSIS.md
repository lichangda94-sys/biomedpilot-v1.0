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

The task bridge copies the module fixture package for `mock` mode and stamps current task metadata. Lite/full modes remain blocked.

The R-side standard entrypoint has also been hardened:

- `analysis/runners/run_module.R <input_json> <output_dir> <mode>`
- `mock` mode copies the module fixture package and writes fresh result/provenance/log metadata.
- `lite` and `full` write blocked standard result packages with provenance instead of executing.
- CLI mode and input manifest mode mismatches are blocked.
- Paths containing spaces are supported.
- No R package install/download or `library(...)` import is used.

The main-backend bridge now has two mock-safe paths:

- `worker_backend="python_fixture"` copies fixed standard packages without requiring R.
- `worker_backend="rscript"` writes `module_input.json`, invokes the standard R runner, validates the package, and registers result-index entries from worker provenance.
- Missing `Rscript` produces a blocked standard result package, not a traceback or installer path.

A first environment isolation scaffold now also exists:

- `analysis/modules/<module_id>/module.json` for survival, univariate, multivariate, enrichment, immune infiltration, spatial transcriptomics, docking, and molecular dynamics.
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
| Unified entrypoint | WARN | Added and tested `analysis/runners/run_module.R` for mock and blocked lite/full standard packages; existing real modules do not call it yet. |
| Mock/lite/full design | WARN | Registry declares all three modes; every module has fixed mock input/output fixtures; lite/full remain blocked pending migration. |
| Unified input/output schema | PASS | Added input and result package schemas. |
| Every module outputs `result.json` / `provenance.json` | WARN | Mock fixtures prove standard package shape for every registered module; existing real algorithms still use varied structures. |
| Every module outputs `tables/`, `plots/`, `reports/`, `logs/` | WARN | Mock fixtures prove required directories for every registered module; existing real algorithms not fully normalized. |
| Frontend consumes standard package only | FAIL | Current UI still consumes module-specific result indexes and service payloads. |
| Main backend task-system invocation | WARN | A mock-mode bridge now creates `TaskCenter` entries and result-index entries; it can explicitly invoke the standard R runner for mock packages. Existing analysis calls still include direct service calls. |
| Runtime R package installation in user flow | PASS | Search found no active non-legacy `install.packages`, `BiocManager::install`, `pak::pkg_install`, or `remotes::install_github`. |
| Heavy dependencies in default dev env | PASS/WARN | Heavy R packages are detect-first external dependencies, not default Python package deps; full env split is not complete. |
| Environment split | WARN | Docker/renv scaffold exists for `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`; not build/restoration proven. |
| `renv.lock` equivalent | WARN | Empty policy lockfiles exist; real package locks are not restored or approved. |
| Full analysis Docker image | WARN | Dedicated Dockerfile scaffolds exist; no full image build or package restoration is proven. |
| Large resources version/hash/license/cache | WARN | Added starter `analysis/resources/manifest.json`; real resource locks are incomplete. |
| Provenance captures versions/hashes/seed/command | WARN | Some Bio result packages capture provenance; universal schema now requires it, migration incomplete. |
| Survival/univariate/multivariate/enrichment/immune/spatial/docking/MD share interface | FAIL | Registry now declares target modules; implementation migration is pending. |
| Docking/MD external tool adapters | FAIL | Target registry only; no adapters. |
| Default dev can start without full analysis deps | PASS | Current source smoke historically works without requiring full R environments; scaffold test does not require R. |

## 3. Top 5 Architecture Risks

1. **P0/P1: R analysis logic is not yet isolated behind a universal worker.** Current Rscript calls live in Python services such as `app/bioinformatics/deg_engine/multifactor_r_runner.py` and `app/bioinformatics/enrichment_r_adapter.py`; a mock-mode bridge exists but does not migrate existing algorithms yet.
2. **P1: Environment split is scaffold-only.** Docker/renv boundaries now exist for `r-bio-core`, `r-bio-full`, `r-spatial-full`, and `r-chem-full`, but no full worker image has been built or restored.
3. **P1: Standard result package is not universal.** Existing modules use result index entries, report packages, and custom paths rather than always producing `result.json` and `provenance.json`.
4. **P1: Large resource governance is incomplete.** Reactome/MSigDB and future spatial/chem resources need version, source, hash, license, and cache-path locks.
5. **P2/P3: UI and backend are still aware of module-specific payloads.** Current UI should eventually consume standard result package metadata rather than individual R package output shapes.

## 4. P0/P1/P2/P3 Issues

### P0

| Issue | Evidence | Status after this audit |
| --- | --- | --- |
| No unified mock-mode analysis module framework | No top-level `analysis/registry` before this audit | Partially fixed with registry, mock fixture, and mock runner. |
| No standard result package contract | Existing modules emit varied outputs | Partially fixed at schema and mock task bridge level; algorithm migration pending. |
| R analysis logic scattered in main backend services | `app/bioinformatics/enrichment_r_adapter.py`, `app/bioinformatics/deg_engine/multifactor_r_runner.py` | Not fixed; documented for staged migration. |

### P1

| Issue | Evidence | Status after this audit |
| --- | --- | --- |
| No lite/full environment split | No `docker/` or `renv/` split existed before scaffold | Partially fixed with scaffold; real package locks and builds pending. |
| No universal module schema | Missing before audit | Fixed at initial schema level. |
| No complete resource lock | Only module-specific gates/docs existed | Starter `analysis/resources/manifest.json` added; real locks pending. |
| Full analysis no independent container | No Docker image split before scaffold | Partially fixed with Dockerfile scaffolds; real full image build pending. |
| UI/backend do not yet call standard worker | Existing direct service calls remain | Partially fixed for mock task bridge only; current UI algorithms not migrated. |

### P2

| Issue | Evidence |
| --- | --- |
| Tests do not yet prove lite/full through one interface | Static tests and bridge tests now prove all registered modules can run mock through one interface; lite/full remain blocked. |
| Logs/provenance differ by module | Existing modules have custom log artifacts and result indexes. |
| Example data is incomplete for every declared module | One generic mock fixture exists; per-module fixtures pending. |

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
4. Add lite mode for one module with lightweight fixture data and no large downloads.
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
- Added resource manifest skeleton with blocked full resources.
- Added static contract tests that do not require R.
- Added a mock-mode task bridge that copies module fixture packages, records task status, validates the package, and registers a result-index entry without requiring R.
- Added an explicit Rscript worker backend for the task bridge that invokes `analysis/runners/run_module.R`, validates the package, and records worker provenance in the result index.
- Added per-module manifest scaffolds for all target modules.
- Added Docker/renv environment split scaffolds with explicit detect-first and no runtime-install policy.
- Added architecture and remediation docs.

## 9. Human Decisions Needed

- Whether full analysis environments will be Docker-only, `renv`-only, or both.
- Where large reference resource cache roots should live on user machines.
- Whether existing Bio result index v2 should become the standard result package index or remain a higher-level application index.
- Which module should be migrated first: enrichment or survival.
- Whether molecular docking/MD belongs in the same product release line or a separately gated advanced-analysis line.
