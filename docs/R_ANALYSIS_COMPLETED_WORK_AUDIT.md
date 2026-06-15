# R Analysis Completed Work Audit

Generated: `2026-06-11`

Scope: BioMedPilot / Labors R analysis kernel architecture.

This report summarizes what has already been completed toward the target pattern:

```text
main app + task system + isolated R analysis worker/service + standard result package
```

It should be read together with:

- `docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md`
- `docs/R_ANALYSIS_REMEDIATION_PLAN.md`
- `docs/R_ANALYSIS_ARCHITECTURE.md`

## Executive Summary

The completed work establishes the architecture boundary and development-safe operating model. The project now has a unified `analysis/` layer, a module registry, standard schemas, a shared R worker entrypoint, mock fixtures, lite worker contracts, standard result packages, environment separation, resource governance stubs, frontend/package consumption gates, and CI-readable architecture diagnostics.

The current gate status is safe for daily development:

- P0 issues: none.
- Default development environment: does not require full R/Bioconductor/spatial/chem dependencies.
- Runtime R package install scan: passed.
- Runtime large resource download scan: passed.
- Standard result package contract: present and validated.
- Full/formal result package validator: stricter preflight checks exist for worker invocation, R session info, Docker image digest, renv lock hash, input/parameter hashes, standard R worker boundary, legacy sidecar rejection, and result-index registration.
- r-bio-full evidence workflow: explicit manual dry-run/execute scripts, read-only validation, and Markdown reporting exist; Docker Hub build, `survival_minimal_v1` lock generation, renv bootstrap, renv restore, R session, and package inventory evidence now pass in the isolated r-bio-full image.
- Full analysis activation: intentionally blocked until real full environment/resource/migration evidence exists.

The work completed so far is boundary completion plus the first scoped survival full/formal migration, not global full scientific production activation.

Survival `survival_minimal_v1` is now the first scoped full/formal migration completed through the standard R worker. It covers KM/log-rank, univariate Cox, and multivariate Cox only; it is not global full-ready and does not cover expanded survival methods.

The survival preflight specification now lives in `docs/SURVIVAL_FULL_FORMAL_MIGRATION_SPEC.md`, with template-only evidence rules under `analysis/evidence_specs/survival_full_formal/`. These templates are not full evidence and do not change readiness.

The r-bio-full external environment evidence workflow now lives under `scripts/full_env/` and `external_analysis_environments/r-bio-full/`. It has produced real Docker build evidence, `survival_minimal_v1` lock evidence, renv bootstrap evidence, renv restore evidence, R session evidence, and package inventory evidence inside the isolated r-bio-full image. It supports the scoped survival migration but does not produce global full production readiness because resources/tools and other formal module migrations remain incomplete.

## Completed Architecture Boundaries

### Unified Analysis Directory

Completed.

The repository has a top-level `analysis/` structure with:

- `analysis/registry/`
- `analysis/schemas/input/`
- `analysis/schemas/output/`
- `analysis/modules/`
- `analysis/fixtures/inputs/`
- `analysis/fixtures/outputs/`
- `analysis/runners/`
- `analysis/resources/`

This gives the project a single place to register analysis modules, define schemas, store fixtures, run the worker, and govern resources.

### Module Registry

Completed.

`analysis/registry/analysis_modules.json` is the current authoritative module registry. It declares the target modules, worker entrypoint, supported modes, environment routing, standard package requirements, result-index task type mapping, and migration state.

Registered target modules include:

- `deg`
- `survival`
- `univariate`
- `multivariate`
- `enrichment`
- `immune_infiltration`
- `correlation`
- `spatial_transcriptomics`
- `docking`
- `molecular_dynamics`

### Shared R Worker Entrypoint

Completed.

`analysis/runners/run_module.R` provides the shared worker entrypoint:

```text
run_module.R <input_json> <output_dir> <mode>
```

The runner supports:

- mock package materialization
- lite fixture execution
- blocked full-mode package output
- standard result/provenance writing
- input hash and parameter hash generation
- worker log output
- command/provenance recording
- no runtime package installation
- no runtime large resource acquisition

## Completed Mode Support

### Mock Mode

Completed.

All target modules have fixed mock input and fixed mock output packages. Mock mode is usable for frontend development, API development, task-flow development, result browser development, and report display development without installing heavy R dependencies.

Mock outputs include:

- `result.json`
- `provenance.json`
- `tables/`
- `plots/`
- `reports/`
- `logs/`

### Lite Mode

Completed as testing-level worker contracts.

All registered target modules have lite coverage through the standard task bridge and R worker path. Lite mode is explicitly testing/development level and does not claim full scientific production readiness.

Lite coverage includes:

- DEG: base R fixture Welch-style differential result path.
- Survival: base R fixture KM/log-rank style path.
- Univariate: base R clinical association fixture path.
- Multivariate: base R linear-model fixture path.
- Enrichment: base R hypergeometric ORA fixture path.
- Immune infiltration: base R signature scoring fixture plus heatmap SVG.
- Correlation: base R Pearson correlation fixture path.
- Spatial transcriptomics: base R spot QC and coordinate preview fixture.
- Docking: AutoDock Vina command-manifest contract, no tool execution.
- Molecular dynamics: GROMACS command-manifest contract, no tool execution.

### Full Mode

Completed as a blocked boundary, not production activation.

Full mode is registered and intentionally blocked until:

- full Docker images are built and evidenced
- full renv locks are restored and evidenced
- required full resources/tools are locked
- module-level formal migration evidence passes

This prevents accidental production claims or hidden dependency installation during user requests.

## Completed Standard Result Package Contract

Completed.

The project now standardizes analysis output around the package structure:

```text
result.json
provenance.json
tables/
plots/
reports/
logs/
```

The package contract is represented by output schemas under:

- `analysis/schemas/output/result.schema.json`
- `analysis/schemas/output/provenance.schema.json`
- `analysis/schemas/output/result_package.schema.json`
- `analysis/schemas/output/worker_invocation.schema.json`

The result package validator checks key package invariants, artifact paths, provenance fields, worker boundary metadata, and package-level manifest assumptions.

## Completed Provenance Contract

Completed for standard packages and lite/mock outputs.

Standard package provenance now includes or reserves fields for:

- module id
- mode
- task id
- creation time
- input hash
- parameter hash
- random seed
- engine metadata
- R version
- Bioconductor version
- R package versions
- external tool versions
- command
- worker boundary metadata

For full/formal packages, missing reproducibility fields are blocked by validation.

## Completed Task-System Boundary

Completed for mock/lite standard-worker flow.

The main app has a task bridge under:

- `app/analysis_runtime/task_bridge.py`

The bridge is responsible for task-centered execution of analysis packages. It writes package-local input manifests, calls the standard worker when appropriate, validates standard result packages, and registers result-index artifacts.

This establishes the intended split:

- frontend: parameters, task submission, progress/result display
- main backend: task creation, state, file/index management
- analysis worker: R and external scientific execution

Formal/full algorithms still need migration evidence before being treated as fully isolated standard-worker executions.

## Completed Frontend / Result Consumption Boundary

Completed for standard package discovery and result browsing.

The app has a package catalog layer under:

- `app/analysis_runtime/package_catalog.py`

The catalog reads result-index registered standard result package artifacts. UI surfaces can display standard package metadata, provenance, input manifests, artifact manifests, worker boundary status, and validation state without reading R package internals directly.

Current policy distinguishes:

- standard worker packages
- testing-level lite packages
- blocked full packages
- transitional legacy sidecars

Legacy sidecars are review-only and cannot count as full migration evidence.

UI preview integration was audited in `docs/UI_PREVIEW_INTEGRATION_AUDIT.md`. The analysis center state exposes a `preview_readiness_matrix` so mock/lite packages, blocked full packages, scoped survival evidence, r-bio-full environment evidence, and legacy sidecar detail views remain review-only and cannot be shown as global full-ready.

## Completed Environment Split

Completed as architecture scaffolding.

The project now declares separate environments:

- `app-dev`
- `r-bio-core`
- `r-bio-full`
- `r-spatial-full`
- `r-chem-full`
- `r-chem-gpu`

Dockerfiles exist for the split:

- `docker/Dockerfile.app-dev`
- `docker/Dockerfile.r-bio-core`
- `docker/Dockerfile.r-bio-full`
- `docker/Dockerfile.r-spatial-full`
- `docker/Dockerfile.r-chem-full`
- `docker/Dockerfile.r-chem-gpu`

renv lock surfaces exist:

- `renv/renv.app.lock`
- `renv/renv.bio-core.lock`
- `renv/renv.bio-full.lock`
- `renv/renv.spatial-full.lock`
- `renv/renv.chem-full.lock`

`renv/renv.bio-full.lock` is restored for the scoped `survival_minimal_v1` profile. `renv/renv.spatial-full.lock` and `renv/renv.chem-full.lock` remain scaffold-only, and no spatial or chemistry full environment is production-ready.

## Completed Heavy Dependency Isolation Guard

Completed.

Architecture scans confirm the default app-dev surface does not include heavy full-analysis dependencies such as:

- ReactomePA
- reactome.db
- Seurat
- CellChat
- GSVA
- AutoDock Vina
- GROMACS
- clusterProfiler
- fgsea

Runtime install/download scans also pass for active app/analysis/scripts/config surfaces.

This means daily development can proceed without installing full analysis dependencies.

## Completed Resource Governance Boundary

Completed as a blocking contract.

The project has a full-resource manifest and resource lock evidence schema path:

- `analysis/resources/manifest.json`
- `analysis/registry/resource_lock_evidence.json`
- `analysis/schemas/output/resource_lock_evidence.schema.json`
- `analysis/schemas/output/resource_lock_evidence_registry.schema.json`

The manifest includes blocked resources/tools for:

- Reactome
- MSigDB
- GO
- KEGG
- OrgDb
- spatial references
- CellChatDB
- AutoDock Vina
- docking templates
- GROMACS
- MD force-field templates

Full resources are not treated as ready until version, source, hash, license, cache path, and evidence files are complete.

## Completed External Tool Adapter Boundary

Completed as lite adapter contracts.

Docking and molecular dynamics are represented as R-adapter-controlled external-tool boundaries:

- docking full target: `r-chem-full`
- molecular dynamics full target: `r-chem-gpu`

Lite mode only writes command manifests and provenance. It does not execute AutoDock Vina or GROMACS, and it does not generate scientific docking/MD outputs.

This prevents molecular simulation tooling from leaking into normal R development or app-dev.

## Completed Architecture Gate

Completed.

`scripts/analysis_architecture_gate.py` produces a schema-versioned architecture gate payload and Markdown report.

The gate currently reports:

- `status=passed`
- `architecture_status=partial_with_p1_gaps`
- P0 issue count: 0
- PASS/WARN/FAIL: 12 / 8 / 0
- full analysis activation: blocked

The gate can also be run with `--require-full-ready`; that mode should remain blocked until real full evidence exists.

## Completed Reports

Completed.

Generated/updated:

- `docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md`
- `docs/R_ANALYSIS_REMEDIATION_PLAN.md`
- `docs/R_ANALYSIS_COMPLETED_WORK_AUDIT.md`

The main audit report contains the required nine-section summary:

1. current fit to target mode
2. PASS / WARN / FAIL table
3. top five architecture risks
4. P0/P1/P2/P3 issue list
5. involved file paths
6. minimum viable remediation path
7. suggested priority files
8. completed changes
9. manual decisions needed

## Completed Tests / Verification

Completed.

The focused verification passed:

```text
python3 -m pytest tests/test_analysis_architecture_gate_script.py tests/test_analysis_runtime_task_bridge.py
```

Result:

```text
52 passed
```

## What Is Explicitly Not Completed

The following are intentionally not completed yet:

- full production R/Bioconductor execution
- global full renv locks for all full environments
- built full Docker image evidence for spatial and chemistry environments
- locked full reference databases
- locked AutoDock Vina or GROMACS installations
- formal isolated-worker migration evidence for all modules
- production spatial transcriptomics
- production docking
- production molecular dynamics
- expanded survival methods beyond `survival_minimal_v1`

Survival has scoped standard-worker migration evidence, full result package evidence, full provenance evidence, task bridge evidence, frontend package catalog evidence, and gate evidence for `survival_minimal_v1`. It still cannot be called global full-ready because `--require-full-ready` remains blocked until all real full environment, resource/tool, and remaining module migration evidence exists.

These remain blocked by design so the default app remains lightweight and user requests cannot trigger hidden installs/downloads.

## Completion Classification

| Area | Status | Notes |
| --- | --- | --- |
| Architecture directory | Completed | Unified `analysis/` exists. |
| Module registry | Completed | Registry is present and authoritative. |
| Shared worker entrypoint | Completed | `run_module.R <input_json> <output_dir> <mode>`. |
| Mock mode | Completed | All target modules have fixed fixtures/packages. |
| Lite mode | Completed | All target modules have task-bridge standard-worker coverage. |
| Full mode | Boundary completed | Full activation remains blocked pending evidence. |
| Standard result package | Completed | Required structure and schemas exist. |
| Provenance contract | Completed | Enforced for standard packages; stricter for full/formal with Docker digest and renv hash checks. |
| Task-system boundary | Completed for mock/lite | Formal migration still pending. |
| Frontend package consumption | Completed for catalog/result browser | Sidecars remain review-only. |
| Environment split | Completed with first r-bio-full evidence | `r-bio-full` has scoped `survival_minimal_v1` evidence; spatial/chem full locks and images remain pending. |
| Resource governance | Completed as blocking contract | Real full resource locks pending. |
| External tool isolation | Completed as adapter boundary | Full tool execution pending. |
| CI/readiness gate | Completed | Current default gate passes with P1 gaps. |
| Survival full/formal migration | Completed for scoped `survival_minimal_v1` | KM/log-rank, univariate Cox, and multivariate Cox run through the standard R worker; not global full-ready. |
| Survival evidence specification | Completed with scoped evidence | Template-only rules remain non-evidence; real survival evidence is registered in `analysis/registry/standard_worker_migration_evidence.json`. |
| Full/formal package validator | Completed as preflight guard | Strict checks reject missing invocation, missing R session info, missing environment hashes, non-standard worker boundary, legacy sidecar evidence, and unregistered packages. |
| Survival resource profile | Completed as preflight rule | Survival is `clinical_fixture_only`; enrichment/spatial/chem resources remain global full-ready blockers, not survival evidence blockers. |
| r-bio-full evidence workflow | Completed as manual workflow with passed scoped evidence | Docker build, `survival_minimal_v1` lock, renv bootstrap, renv restore, R session, and package inventory evidence pass; this is not full production activation. |
