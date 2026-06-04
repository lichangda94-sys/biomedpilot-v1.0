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
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/result_package.schema.json`
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
- Wire one current real analysis module through the bridge for lite mode.

Update: the first result package validator and mock-mode backend adapter now exist under `app/analysis_runtime/`. All registered modules now have fixed mock input and standard result package fixtures.

Update: DEG is now registered as a standard analysis module with a mock input, mock standard result package, and base R lite worker fixture. DEG full/formal standard worker execution remains blocked until the existing controlled DEG runners are migrated behind the standard worker.

Update: the R-side standard runner now accepts `<input_json> <output_dir> <mode>`, copies module-specific mock packages in `mock` mode, writes blocked standard packages for `lite` and `full`, and blocks CLI/input mode mismatches. It remains a contract runner only; no real R algorithms are activated.

Update: the main-backend task bridge now has an explicit `worker_backend="rscript"` path. It materializes `module_input.json`, invokes the standard R runner, validates the standard package, and registers worker provenance in the result index. Missing `Rscript` is a graceful blocked package.

Update: the resource manifest now declares required full-mode resources for enrichment, immune infiltration, spatial transcriptomics, docking, and molecular dynamics. `app/analysis_runtime/resources.py` validates the manifest and adds module-specific full-mode blockers until real locks exist.

Update: the standard package catalog now reads result-index `standard_result_package` artifacts and is exposed in Analysis Center state as `standard_analysis_packages`. This is a read-only UI bridge; detailed module result views still need migration.

Update: DEG now has a `lite` standard worker path. `run_module.R` can execute base R two-group Welch t-tests on fixed local count/metadata fixtures and write a testing-level standard result package. It does not use limma, DESeq2, edgeR, scipy, statsmodels, report-ready output, or clinical interpretation.

Update: enrichment now has a `lite` standard worker path. `run_module.R` can execute a base R hypergeometric ORA fixture with local TERM2GENE files and write a testing-level standard result package. It does not use Reactome/MSigDB/full resources and does not enable report-ready output.

Update: controlled ORA/GSEA R adapters now mirror successful formal enrichment fixture results into standard result package sidecars and register them in result index v2 as `standard_result_package` artifacts. This does not change the algorithms, does not enable plot/report-ready output, and does not complete isolated worker migration.

Update: controlled multi-factor DEG R adapters now mirror successful limma/DESeq2/edgeR fixture-proven formal results into standard result package sidecars and register them in result index v2 as `standard_result_package` artifacts. This preserves result table, task log, parameter manifest, dependency snapshot, formula/contrast provenance, hashes, package versions, and command provenance. This does not enable new DEG execution, plot/report-ready output, clinical interpretation, or complete isolated worker migration.

Update: survival now has a `lite` standard worker path. `run_module.R` can execute base R KM/log-rank calculations on fixed local survival fixture data and write a testing-level standard result package. It does not generate prognosis, treatment guidance, report-ready survival output, or clinical interpretation.

Update: univariate clinical association now has a `lite` standard worker path. `run_module.R` can execute base R Welch t-test and Pearson correlation calculations on fixed local clinical fixture data and write a testing-level standard result package. It does not generate clinical conclusions, report-ready clinical output, diagnosis, prognosis, or treatment guidance.

Update: multivariate clinical association now has a `lite` standard worker path. `run_module.R` can execute a base R linear model fixture on fixed local clinical fixture data and write a testing-level standard result package. It does not generate clinical conclusions, model selection recommendations, risk scores, report-ready clinical output, diagnosis, prognosis, or treatment guidance.

Update: immune infiltration now has a `lite` standard worker path. `run_module.R` can execute base R signature mean scoring on fixed local expression/signature fixture data and write a testing-level standard result package with a real SVG heatmap fixture. It does not use GSVA, CellChat, Seurat, large signature databases, report-ready immune interpretation, diagnosis, prognosis, or treatment guidance.

## Phase R1: Task-System Bridge

Scope:

- Add a Python bridge that submits module jobs by writing `module_input.json`.
- The bridge calls the standard worker only through task execution, not directly from UI.
- The UI consumes `result.json`, `provenance.json`, and artifact manifest metadata.

Acceptance:

- Every registered module can run `mock` mode through the task system using its fixed fixture package. **Completed for mock mode.**
- The R-side runner can generate a mock standard package from a module fixture and a blocked standard package for disabled modes. **Completed for runner contract.**
- The task bridge can explicitly call the R-side standard runner for mock packages without enabling lite/full real analysis. **Completed for worker-boundary contract.**
- Analysis Center can discover standard result packages from the result index without scanning module-specific output folders. **Completed for state-level preview.**
- DEG can run `lite` mode through the standard R worker using fixed local count/metadata fixture data. **Completed for DEG lite worker.**
- Enrichment can run `lite` mode through the standard R worker using fixed local fixture resources. **Completed for enrichment lite worker.**
- Survival can run `lite` mode through the standard R worker using fixed local fixture data. **Completed for second lite worker.**
- Univariate can run `lite` mode through the standard R worker using fixed local clinical fixture data. **Completed for third lite worker.**
- Multivariate can run `lite` mode through the standard R worker using fixed local clinical fixture data. **Completed for fourth lite worker.**
- Immune infiltration can run `lite` mode through the standard R worker using fixed local expression/signature fixture data and generate a real SVG heatmap fixture. **Completed for fifth lite worker.**
- Output package includes `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, `logs/`.
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

- Successful controlled limma multi-factor fixture results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Successful controlled DESeq2 multi-factor fixture results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Successful controlled edgeR multi-factor fixture results write a standard result package sidecar and result-index `standard_result_package` artifact.
- Blocked incompatible non-count DESeq2/edgeR requests still stop before result index registration.

Remaining:

- Move long-running limma/DESeq2/edgeR Rscript execution behind the standard task worker instead of service-level subprocess calls.
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
```

Status: scaffolded, not restored.

Completed:

- Added Dockerfile scaffolds for app-dev, bio-core, bio-full, spatial-full, chem-full, and chem-gpu.
- Added empty policy lockfiles for app, bio-core, bio-full, spatial-full, and chem-full.
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

## Phase R6: Resource Governance

Scope:

- Lock Reactome, MSigDB, GO, KEGG, org dbs, spatial references, docking resources, and MD templates.
- Record version, source, hash, license, and cache path.

Status: contract gate present; real locks pending.

Completed:

- Declared blocked full-mode resources for Reactome, MSigDB, GO, KEGG, human org db, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and MD templates.
- Added resource manifest validation and module-specific full-mode resource blockers.
- Kept runtime downloads forbidden for every resource entry.

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
- Full immune analysis remains blocked until GSVA/CellChat/Seurat/signature resource locks and isolated worker environments are approved.

Rules:

- Spatial goes to `r-spatial-full`.
- Docking/MD use R adapters to external tools only.
- Docking/MD never share the normal bio-core environment.

## Current Stop Rule

Do not migrate algorithms until the standard package validator and one mock-mode task-system bridge are in place.
