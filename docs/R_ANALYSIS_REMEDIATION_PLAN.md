# R Analysis Remediation Plan

Generated: `2026-06-11`

Source of truth: `scripts/analysis_architecture_gate.py --json-output /tmp/analysis_architecture_gate.json --markdown-output docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md`

## Current Position

BioMedPilot is now partially aligned with the target pattern:

```text
main app + task system + isolated R analysis worker/service + standard result package
```

The architecture gate reports `passed` for the default safety gate because there are no P0 blockers, no runtime R package install hits, no runtime resource-download hits, and no heavy full-analysis dependencies in the default app-dev surface. The real state is still `partial_with_p1_gaps`: full analysis activation is intentionally `blocked`.

## Completed Boundary Work

- Top-level `analysis/` structure exists with registry, schemas, modules, fixtures, runner, resources, and tests.
- `analysis/registry/analysis_modules.json` declares the registered modules and their standard worker contract.
- `analysis/runners/run_module.R` provides the shared `<input_json> <output_dir> <mode>` entrypoint.
- All target modules have mock fixtures and standard result package fixtures.
- All target modules have lite coverage through the task bridge and standard R worker contract.
- Standard packages require `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, and `logs/`.
- App-dev and r-bio-core are separated from full environments.
- Full environments are declared as separate Docker/renv surfaces: `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`.
- Runtime installs and runtime full-resource downloads are forbidden by scan and policy.
- Frontend/result browsing is routed through result-index registered standard packages rather than raw R package internals.
- Legacy DEG and survival sidecars are labeled transitional and cannot count as isolated standard-worker migration evidence.

## Remaining Priority Issues

### P0

None in the current gate output.

### P1

- `full_analysis_environment_locks_not_restored`: `r-bio-full` now has schema-valid Docker build, renv bootstrap, renv restore, R session, package inventory, and `survival_minimal_v1` lock evidence. `r-spatial-full`, `r-chem-full`, and `r-chem-gpu` remain scaffold-only with no restored Docker image / renv evidence.
- `full_analysis_resource_locks_not_complete`: Reactome, MSigDB, GO, KEGG, OrgDb, spatial references, CellChatDB, AutoDock Vina, docking templates, GROMACS, and MD force-field resources lack complete version/source/hash/license/cache evidence.
- `formal_algorithms_not_universally_migrated_to_isolated_standard_worker`: all 10 formal modules still need registry-owned full standard-worker migration evidence.

### P2

- DEG and survival still have transitional legacy sidecar producers, guarded by default execution gates.
- DEG and survival sidecar provenance remains transitional and cannot be used as full isolated-worker evidence.

### P3

- Full mode remains declared as blocked for all modules until full environments and resources are restored.
- Documentation and naming should keep distinguishing mock/lite/testing outputs from full/formal outputs.

## Minimum Viable Remediation Path

1. Restore full analysis environment locks outside the default development environment.
2. Lock full analysis resources and external tools with real version, source, hash, license, cache path, and evidence files.
3. Migrate one formal module at a time into task-center registered standard R-worker execution.

Do not install heavy R packages, Bioconductor databases, spatial packages, AutoDock Vina, GROMACS, or large references in app-dev. Do not download large resources during user requests.

## Recommended Module Order

1. `survival`: first scoped full/formal migration completed for `survival_minimal_v1`; it is not global full-ready and does not cover expanded survival methods.
2. `univariate`: base statistical contract is simple and useful for clinical association.
3. `multivariate`: follows univariate and extends the same clinical schema.
4. `enrichment`: requires resource lock discipline for Reactome/MSigDB/GO/KEGG/OrgDb.
5. `immune_infiltration`: depends on signature/resource governance and heatmap/report packaging.
6. `deg`: broader legacy sidecar surface; migrate after the smaller R-native contracts are proven.
7. `spatial_transcriptomics`, `docking`, `molecular_dynamics`: keep planned until spatial/chem full images and external tool locks are ready.

## Survival Formal Migration Evidence Checklist

Survival was selected as the first full/formal migration because its R-native scope is narrower than enrichment, spatial, docking, or molecular dynamics. The `survival_minimal_v1` migration evidence now passes for KM/log-rank, univariate Cox, and multivariate Cox through the standard R worker. This does not make global full production activation ready.

The detailed survival full/formal migration specification is maintained in `docs/SURVIVAL_FULL_FORMAL_MIGRATION_SPEC.md`. Template-only evidence files live under `analysis/evidence_specs/survival_full_formal/`; they remain templates and are not counted as readiness evidence.

The scoped survival evidence that now exists includes:

- Standard worker evidence: `analysis/registry/standard_worker_migration_evidence.json` has a schema-valid survival entry proving task-center registered standard R-worker execution.
- Result package evidence: `analysis/standard_packages/survival/survival_full_formal_v1` validates with `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, `logs/`, `logs/worker_invocation.json`, and `logs/r_session_info.txt`.
- Provenance evidence: the package records R version, Bioconductor version, R package versions, external tool versions if any, input hash, parameter hash, random seed, execution command, worker boundary metadata, Docker image digest, and renv lock hash.
- Task bridge evidence: survival full/formal execution goes through `app/analysis_runtime/task_bridge.py` and not through a direct legacy sidecar path.
- Frontend catalog evidence: the result index registers the standard package and the package catalog/detail views consume that package instead of module-private survival outputs.
- Environment evidence: `r-bio-full` has restored renv lock evidence and Docker image build evidence.
- Gate evidence: default gate remains passed, `--require-full-ready` remains blocked until all full evidence exists globally, while survival is reported as `migrated_to_isolated_standard_worker` only for the scoped `survival_minimal_v1` migration.
- Forbidden source guard: mock fixtures, lite fixtures, blocked-full packages, legacy sidecars, module-private outputs, manually copied artifacts, and packages without worker invocation/provenance/task bridge are invalid full evidence sources.

The full/formal result package validator is stricter than mock/lite validation. A future full/formal package fails if it lacks `logs/worker_invocation.json`, `logs/r_session_info.txt`, Docker image digest, renv lock hash, input hash, parameter hash, a `standard_r_worker` boundary, or result-index registration. Mock and lite packages are not treated as full/formal evidence.

Survival's current full/formal resource profile is `clinical_fixture_only`: Reactome, MSigDB, GO, KEGG, OrgDb, CellChatDB, AutoDock Vina, and GROMACS are `not_required` for the survival preflight. Global `--require-full-ready` still remains blocked until enrichment, spatial, docking, and molecular-dynamics resources/tools are locked.

## r-bio-full Environment Evidence Specification

`r-bio-full` environment evidence now passes for the scoped `survival_minimal_v1` lock profile. Together with the survival standard-worker evidence, it supports the scoped survival migration only; it does not unblock global full production activation.

The registry documents the expected evidence root and required files:

- `external_analysis_environments/r-bio-full/docker_build.log`
- `external_analysis_environments/r-bio-full/docker_image_digest.txt`
- `external_analysis_environments/r-bio-full/docker_inspect.json`
- `external_analysis_environments/r-bio-full/renv_lock_generate.log`
- `external_analysis_environments/r-bio-full/renv_lock_generate_metadata.json`
- `external_analysis_environments/r-bio-full/renv_bootstrap_version.txt`
- `external_analysis_environments/r-bio-full/renv_bootstrap_source.txt`
- `external_analysis_environments/r-bio-full/renv_restore.log`
- `external_analysis_environments/r-bio-full/renv_status.json`
- `external_analysis_environments/r-bio-full/r_session_info.txt`
- `external_analysis_environments/r-bio-full/installed_packages.tsv`
- `external_analysis_environments/r-bio-full/environment_lock_evidence.json`
- `external_analysis_environments/r-bio-full/evidence_manifest.json`

Current `environment_lock_evidence.json` includes environment id/class, evidence source, expected/base image, source digest, Docker build/load status, Docker image digest, Docker inspect path, equivalence claim/status, lock profile, required package set, renv lock path/hash, renv bootstrap status/version/source, renv restore status/log path, renv status path, R/Bioconductor versions, R session info path, package inventory path, creator/review metadata, validation status/errors, and evidence hash.

## r-bio-full Evidence Collection Workflow

This stage adds explicit manual tooling only. Manual `--execute` may build the isolated `r-bio-full` Docker image, generate the scoped `survival_minimal_v1` lock, bootstrap `renv`, and restore the lock inside that image. It does not build full Docker images, restore renv locks, install R/Bioconductor packages, or download resources during default app-dev, default tests, default gate execution, or user request flows.

Evidence root:

- `external_analysis_environments/r-bio-full/`

Manual dry-run:

```bash
bash scripts/full_env/collect_r_bio_full_evidence.sh \
  --evidence-root external_analysis_environments/r-bio-full \
  --image-tag biomedpilot/r-bio-full:local-YYYYMMDD \
  --dry-run
```

Manual real collection, only when an operator is ready to create full evidence:

```bash
bash scripts/full_env/generate_r_bio_full_lock.sh \
  --image-tag biomedpilot/r-bio-full:local-YYYYMMDD \
  --profile survival_minimal_v1 \
  --cran-repo https://cloud.r-project.org \
  --execute
```

```bash
bash scripts/full_env/collect_r_bio_full_evidence.sh \
  --evidence-root external_analysis_environments/r-bio-full \
  --image-tag biomedpilot/r-bio-full:local-YYYYMMDD \
  --source docker_hub \
  --execute
```

If Docker Hub remains unavailable, use one of the explicit offline/controlled sources instead:

```bash
bash scripts/full_env/collect_r_bio_full_evidence.sh \
  --evidence-root external_analysis_environments/r-bio-full \
  --image-tag biomedpilot/r-bio-full:internal-YYYYMMDD \
  --source internal_registry \
  --internal-image registry.example/biomedpilot/r-bio-full:YYYYMMDD \
  --source-digest sha256:<digest> \
  --source-url https://registry.example/biomedpilot/r-bio-full \
  --source-attestation external_analysis_environments/r-bio-full/source_attestation.md \
  --execute
```

```bash
bash scripts/full_env/collect_r_bio_full_evidence.sh \
  --evidence-root external_analysis_environments/r-bio-full \
  --image-tag biomedpilot/r-bio-full:local-YYYYMMDD \
  --source local_image_tar \
  --image-tar /path/to/r-bio-full.tar \
  --source-digest sha256:<digest> \
  --source-attestation external_analysis_environments/r-bio-full/source_attestation.md \
  --execute
```

Current Docker Hub access is available through the operator-provided proxy path. `r-bio-full` Docker build, `survival_minimal_v1` lock generation, renv bootstrap/restore, R session, and package inventory evidence have been collected and validate as passed. Internal registry and local image tar evidence paths remain available and must pass digest/hash, source attestation, Docker inspect, renv bootstrap, renv restore, R session, package inventory, and lock-profile validation before they can replace the current Docker Hub evidence.

Read-only validation:

```bash
python3 scripts/full_env/validate_r_bio_full_evidence.py \
  --evidence-root external_analysis_environments/r-bio-full
```

Report rendering:

```bash
python3 scripts/full_env/render_r_bio_full_evidence_report.py \
  --evidence-root external_analysis_environments/r-bio-full \
  --markdown-output docs/R_BIO_FULL_ENVIRONMENT_EVIDENCE.md
```

Current expected state is `passed` for `r-bio-full` environment evidence and `passed` for scoped survival `survival_minimal_v1` migration evidence. It must not be described as global full-ready or production-ready because full resources/tools and remaining formal module migrations are incomplete.

## Files to Change First

- Environment locks: `analysis/registry/environment_lock_evidence.json`, `analysis/registry/analysis_environments.json`, `renv/renv.bio-full.lock`, `renv/renv.spatial-full.lock`, `renv/renv.chem-full.lock`, `external_analysis_environments/`.
- Resource locks: `analysis/resources/manifest.json`, `analysis/registry/resource_lock_evidence.json`, `analysis/resources/locks/`, `external_analysis_resources/`.
- Module migration: `analysis/runners/run_module.R`, `analysis/modules/<module_id>/module.json`, `analysis/registry/standard_worker_migration_evidence.json`, `app/bioinformatics/`.
- Validation: `scripts/analysis_architecture_gate.py`, `tests/test_analysis_architecture_gate_script.py`, `tests/test_analysis_runtime_task_bridge.py`.

## Acceptance Gates

- Default app-dev starts without full R, Bioconductor, spatial, docking, or MD dependencies.
- `python3 scripts/analysis_architecture_gate.py --pretty` exits 0 and reports no P0 issues.
- `python3 scripts/analysis_architecture_gate.py --require-full-ready` remains blocked until all full environment locks, resource locks, and formal migration evidence are real.
- A migrated formal module must produce a passed full standard package through the task bridge, with `result.json`, `provenance.json`, `tables/`, `plots/`, `reports/`, `logs/`, `logs/worker_invocation.json`, and `logs/r_session_info.txt`.
- The package provenance must include R version, Bioconductor version, R package versions, external tool versions, input hash, parameter hash, random seed, command, worker boundary metadata, Docker image digest, and renv lock hash.
- Survival may be labeled `scoped survival_minimal_v1 migrated`; it must not be labeled global full-ready or production-ready.

## Manual Decisions Needed

- Which full Docker image and renv build process is authoritative for `r-bio-full`, `r-spatial-full`, `r-chem-full`, and `r-chem-gpu`.
- Which resource cache location and license policy will be used for Reactome/MSigDB/GO/KEGG/OrgDb/spatial/CellChat resources.
- Whether chemistry execution should support CPU-only `r-chem-full`, GPU `r-chem-gpu`, or both for the first production milestone.
- Which module should be migrated next after scoped survival. Recommended order: `univariate`, then `multivariate`, then `enrichment`, then `immune_infiltration`.
