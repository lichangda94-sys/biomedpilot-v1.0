# External / Web Engine Runtime Registry Stage Report - 2026-05-22

## Scope

Implemented the dependency-detection layer described in `External_Web_Engine_Module_Runtime_Plan.md` for shared external engines. This stage is limited to runtime, package, renderer, capability registry, blocker, and snapshot handoff infrastructure.

## Implemented

- Added R / Bioconductor detection for `Rscript`, R version, architecture, smoke execution, `BiocManager`, `limma`, `DESeq2`, `edgeR`, `survival`, `glmnet`, `ggplot2`, and `survminer`.
- Added Python statistical dependency detection for `scipy`, `statsmodels`, `lifelines`, `scikit-survival`, and `matplotlib`.
- Added report renderer detection for `pandoc`, `Quarto`, `LaTeX`, and `wkhtmltopdf`.
- Added persisted dependency snapshots under `project_storage/external_engines/`.
- Added stable capability query keys, safe unknown-key fallback, required-by query, and dependency snapshot handoff payloads.
- Added detect-first UI to the external engine settings page with a rerun detection entry and registry summary.
- Wired the capability registry into the existing bioinformatics consumers:
  - DEG dependency preflight now records the Python controlled-DEG handoff for `scipy` / `statsmodels` and blocks formal computation when a checked registry reports required capabilities missing.
  - Survival preflight now records the Python `lifelines` and optional R `survival` / `survminer` handoffs while keeping KM / Cox execution disabled.
  - Report export packages now persist a report-renderer handoff manifest for `pandoc`, `Quarto`, `LaTeX`, and `wkhtmltopdf` without making renderer status part of `report_ready`.

## Explicit Boundaries

- No formal DEG, KM, Cox, ORA, GSEA, or integrated report execution was implemented.
- Availability of `limma`, `DESeq2`, `edgeR`, `survival`, or renderer tools is exposed only as dependency state.
- The UI does not display "limma completed", "DESeq2 completed", "edgeR completed", "multi-factor DEG completed", or "Cox completed".
- Report renderer status does not decide `report_ready`.
- Registry handoffs are dependency evidence only; they do not promote any analysis family from preflight/testing status to formal status by themselves.

## Validation

- Focused tests added:
  - `tests/shared/test_external_dependency_registry.py`
  - `tests/ui/test_external_engine_manager_page.py`
  - `tests/bioinformatics/test_deg_dependency_check.py`
  - `tests/bioinformatics/test_survival_input_preflight.py`
  - `tests/bioinformatics/test_report_export_package.py`
- Expected gates:
  - focused shared local engine tests
  - focused external engine UI tests
  - source smoke
  - `git diff --check`
