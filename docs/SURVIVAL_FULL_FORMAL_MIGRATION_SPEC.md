# Survival Full/Formal Migration Specification

Generated: `2026-06-15`

Scope: `survival` only.

## Current Status

- Survival has scoped survival_minimal_v1 full/formal migration evidence.
- Survival is migrated only for the survival_minimal_v1 scope.
- Survival is not globally full-ready.
- Survival is not production-ready for expanded survival methods.
- The global full activation gate remains blocked.
- Current full/formal execution is limited to the standard R worker evidence package for survival_minimal_v1.
- Legacy sidecar output remains transitional/review-only and is not accepted as migration evidence.

## Full/Formal Analysis Scope

The first full/formal survival migration includes:

- Kaplan-Meier grouped survival analysis
- log-rank test
- Cox univariate model
- Cox multivariate model
- Cox forest plot
- standard report package

## Out Of Scope For This Stage

The following are explicitly not included in the first full/formal survival migration:

- time-dependent ROC
- nomogram
- calibration curve
- competing risk
- batch survival analysis
- multi-omics survival model
- online database validation
- automatic clinical covariate inference

## Acceptance Data Requirements

The survival_minimal_v1 full/formal survival evidence bundle must include:

- `clinical_survival.tsv`
- `expression_or_signature.tsv`
- `input.json`
- `expected_result_manifest.json`
- `README.md`

### clinical_survival.tsv

Minimum fields:

- `sample_id`
- `survival_time`
- `survival_event`
- `group` or `candidate_variable`
- `age` optional
- `sex` optional
- `stage` optional
- `additional_covariates` optional

### expression_or_signature.tsv

Minimum fields:

- `sample_id`
- `feature_id` or `signature_score`
- `value`

### input.json

Required declarations:

- `module_id=survival`
- `mode=full`
- `analysis_scope`
- `survival_time_column`
- `survival_event_column`
- `grouping_column` or `expression_feature`
- `covariates`
- `cutoff_policy`
- `random_seed`
- `output_format`
- `expected_environment=r-bio-full`

## Required Standard Result Package

The survival_minimal_v1 full/formal survival standard result package must contain:

- `result.json`
- `provenance.json`
- `tables/survival_summary.tsv`
- `tables/km_logrank.tsv`
- `tables/cox_univariate.tsv`
- `tables/cox_multivariate.tsv`
- `plots/km_curve.svg`
- `plots/cox_forest.svg`
- `reports/survival_full_formal_report.md`
- `logs/stdout.log`
- `logs/stderr.log`
- `logs/worker_invocation.json`
- `logs/r_session_info.txt`

## Provenance Requirements

The survival_minimal_v1 full/formal survival package provenance must include:

- R version
- Bioconductor version
- package versions
- external tool versions, even if empty
- input hash
- parameter hash
- random seed
- execution command
- worker boundary metadata
- environment id
- docker image digest
- renv lock hash
- result package hash

## Scoped Evidence

The current scoped migration evidence is:

- `analysis/standard_packages/survival/survival_full_formal_v1`
- `analysis/registry/standard_worker_migration_evidence.json`
- `results/summaries/result_index.json`
- `external_analysis_environments/r-bio-full/environment_lock_evidence.json`
- `renv/renv.bio-full.lock`

This evidence is valid only for the survival_minimal_v1 scope: Kaplan-Meier/log-rank, univariate Cox, and multivariate Cox using the clinical fixture profile.

## Global Full-Ready Prerequisites

Global full-ready must remain blocked until all of the following are real and validated across the required module/resource scope:

- `r-bio-full` Docker build evidence exists.
- `r-bio-full` renv restore evidence exists.
- Survival standard worker migration evidence is schema-valid.
- The full result package validates.
- Provenance validates.
- Task bridge execution evidence validates.
- Frontend package catalog consumes the standard result package.
- `logs/worker_invocation.json` exists and records `boundary=standard_r_worker`.
- `logs/r_session_info.txt` exists.
- Provenance records Docker image digest and renv lock hash.
- Provenance records input hash and parameter hash.
- The result package is registered in the result index.
- `--require-full-ready` only passes after all required evidence is real for the full architecture, not just survival_minimal_v1.

## Resource Profile

Survival full/formal preflight currently uses `clinical_fixture_only` resource scope. Reactome, MSigDB, GO, KEGG, OrgDb, CellChatDB, AutoDock Vina, and GROMACS are not required for survival evidence. They remain global full-ready blockers for enrichment, spatial transcriptomics, docking, and molecular dynamics.

## Forbidden Evidence Sources

The following must not be accepted as survival full/formal migration evidence:

- mock fixture
- lite fixture
- blocked full package
- legacy sidecar
- module-private output
- manually copied artifact
- result without worker invocation
- result without provenance
- result without task bridge

## Current Gate Position

The current survival scoped preflight status is passed for survival_minimal_v1, while global full-ready remains blocked:

- `standard_worker_evidence`: `survival_standard_worker_evidence_passed_scope_survival_minimal_v1_full_activation_still_blocked`
- `result_package_evidence`: `survival_full_formal_standard_package_passed_scope_survival_minimal_v1`
- `provenance_evidence`: `survival_full_formal_provenance_passed_scope_survival_minimal_v1`
- `task_bridge_evidence`: `task_bridge_registered_survival_full_formal_standard_worker_execution`
- `frontend_package_catalog_evidence`: `catalog_contract_exists_and_survival_full_package_registered_scope_survival_minimal_v1`
- `environment_evidence`: `r_bio_full_environment_evidence_passed_scope_survival_minimal_v1_full_activation_still_blocked`
- `forbidden_source_guard`: `blocked_mock_lite_blocked_full_legacy_sidecar_forbidden`
- `gate_evidence`: `survival_scoped_migration_evidence_passed_global_full_ready_blocked; require_full_ready_expected_exit_code_1`
