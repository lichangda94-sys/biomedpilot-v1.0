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

The scaffold fixes the most basic registry/schema/mock result-package boundary, but existing algorithms are not yet migrated to the worker interface.

## 2. PASS / WARN / FAIL Table

| Requirement | Status | Evidence |
| --- | --- | --- |
| Unified analysis module directory | WARN | Added `analysis/`; existing algorithms still live under `app/bioinformatics/**`. |
| Module registry | PASS | Added `analysis/registry/analysis_modules.json`. |
| Unified entrypoint | WARN | Added `analysis/runners/run_module.R` for mock boundary; existing modules do not call it yet. |
| Mock/lite/full design | WARN | Registry declares all three modes; mock supported, lite/full blocked pending migration. |
| Unified input/output schema | PASS | Added input and result package schemas. |
| Every module outputs `result.json` / `provenance.json` | WARN | Contract exists; existing modules still use varied result-index/report structures. |
| Every module outputs `tables/`, `plots/`, `reports/`, `logs/` | WARN | Mock package fixture and schema exist; existing modules not fully normalized. |
| Frontend consumes standard package only | FAIL | Current UI still consumes module-specific result indexes and service payloads. |
| Main backend task-system invocation | WARN | Task/result contracts exist, but some analysis calls are direct service calls. |
| Runtime R package installation in user flow | PASS | Search found no active non-legacy `install.packages`, `BiocManager::install`, `pak::pkg_install`, or `remotes::install_github`. |
| Heavy dependencies in default dev env | PASS/WARN | Heavy R packages are detect-first external dependencies, not default Python package deps; full env split is not complete. |
| Environment split | FAIL | No complete `app-dev`, `r-bio-core`, `r-bio-full`, `r-spatial-full`, `r-chem-full` container/renv implementation yet. |
| `renv.lock` equivalent | FAIL | No committed renv lock split for analysis environments. |
| Full analysis Docker image | FAIL | No dedicated full-analysis Docker images in current tree. |
| Large resources version/hash/license/cache | WARN | Added starter `analysis/resources/manifest.json`; real resource locks are incomplete. |
| Provenance captures versions/hashes/seed/command | WARN | Some Bio result packages capture provenance; universal schema now requires it, migration incomplete. |
| Survival/univariate/multivariate/enrichment/immune/spatial/docking/MD share interface | FAIL | Registry now declares target modules; implementation migration is pending. |
| Docking/MD external tool adapters | FAIL | Target registry only; no adapters. |
| Default dev can start without full analysis deps | PASS | Current source smoke historically works without requiring full R environments; scaffold test does not require R. |

## 3. Top 5 Architecture Risks

1. **P0/P1: R analysis logic is not yet isolated behind a universal worker.** Current Rscript calls live in Python services such as `app/bioinformatics/deg_engine/multifactor_r_runner.py` and `app/bioinformatics/enrichment_r_adapter.py`.
2. **P1: No full environment split.** There is no complete `renv`/Docker separation for `r-bio-core`, `r-bio-full`, `r-spatial-full`, and `r-chem-full`.
3. **P1: Standard result package is not universal.** Existing modules use result index entries, report packages, and custom paths rather than always producing `result.json` and `provenance.json`.
4. **P1: Large resource governance is incomplete.** Reactome/MSigDB and future spatial/chem resources need version, source, hash, license, and cache-path locks.
5. **P2/P3: UI and backend are still aware of module-specific payloads.** Current UI should eventually consume standard result package metadata rather than individual R package output shapes.

## 4. P0/P1/P2/P3 Issues

### P0

| Issue | Evidence | Status after this audit |
| --- | --- | --- |
| No unified mock-mode analysis module framework | No top-level `analysis/registry` before this audit | Partially fixed with registry, mock fixture, and mock runner. |
| No standard result package contract | Existing modules emit varied outputs | Partially fixed at schema level; migration pending. |
| R analysis logic scattered in main backend services | `app/bioinformatics/enrichment_r_adapter.py`, `app/bioinformatics/deg_engine/multifactor_r_runner.py` | Not fixed; documented for staged migration. |

### P1

| Issue | Evidence | Status after this audit |
| --- | --- | --- |
| No lite/full environment split | No `docker/` or `renv/` split found | Not fixed. |
| No universal module schema | Missing before audit | Fixed at initial schema level. |
| No complete resource lock | Only module-specific gates/docs existed | Starter `analysis/resources/manifest.json` added; real locks pending. |
| Full analysis no independent container | No Docker image split | Not fixed. |
| UI/backend do not yet call standard worker | Existing direct service calls remain | Not fixed. |

### P2

| Issue | Evidence |
| --- | --- |
| Tests do not yet prove all modules can run mock/lite/full through one interface | Added only static contract tests. |
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
- `analysis/runners/run_module.R`
- `analysis/fixtures/inputs/mock_analysis_input.json`
- `analysis/fixtures/outputs/mock_result_package/result.json`
- `analysis/fixtures/outputs/mock_result_package/provenance.json`

## 6. Minimal Viable Remediation Path

1. Keep existing algorithms stable.
2. Add standard result package schema, registry, mock runner, and fixtures. **Completed in this audit.**
3. Wrap one existing R-native module behind the standard worker in mock mode first.
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
- Added base R mock runner without package installation.
- Added generic mock input and standard mock result package.
- Added resource manifest skeleton with blocked full resources.
- Added static contract tests that do not require R.
- Added architecture and remediation docs.

## 9. Human Decisions Needed

- Whether full analysis environments will be Docker-only, `renv`-only, or both.
- Where large reference resource cache roots should live on user machines.
- Whether existing Bio result index v2 should become the standard result package index or remain a higher-level application index.
- Which module should be migrated first: enrichment or survival.
- Whether molecular docking/MD belongs in the same product release line or a separately gated advanced-analysis line.

