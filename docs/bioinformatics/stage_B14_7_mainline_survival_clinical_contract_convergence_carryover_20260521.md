# Bioinformatics B14.7 MainLine Survival Clinical Contract Convergence and Scoped Carry-over

Date: 2026-05-21

## Scope

This stage carries the survival/clinical MVP into MainLine with a scoped convergence plan:

- Preserve MainLine recognition, standardization, resolver, DEG, ORA, GSEA, plot, report, and packaging behavior.
- Add the ReleaseBuild B12 `survival_clinical` input contract shape into MainLine.
- Add Bioinformatics B13/B14 controlled KM/log-rank and Cox univariate runtime modules.
- Keep Cox multivariate as design audit only.
- Keep survival/clinical plots as spec-only artifacts.
- Keep survival/clinical `report_ready_eligible=False`.
- Do not touch ReleaseBuild code in this stage.

## Baselines

| Worktree | Branch / source | Baseline |
| --- | --- | --- |
| MainLine target | `stable/mainline` | `be8c924336f42e92e89eb1d8d7710bed02d4cd99` |
| MainLine carry-over branch | `codex/mainline-survival-clinical-carryover` | Created from `be8c924` |
| B12 contract source | ReleaseBuild `d074172e513e3e599e16ba342f33d90309e9041b` | Used only for B12 `survival_clinical` input contract modules/tests |
| B13/B14 runtime source | Bioinformatics `62600c0d1fbea84da2d1da61c9de3645bd66504c` | Used for KM/Cox controlled runtime, plot specs, UI gate rows, tests, docs |

## Carry-over Summary

### B12 Input Contract Convergence

MainLine now has a dedicated `app/bioinformatics/survival_clinical` package with the B12 input contract modules:

- `input_resolver.py`
- `outcome_gate.py`
- `clinical_variables.py`
- `missingness.py`
- `censoring.py`
- `source_mapping.py`
- `models.py`

The resolver contract remains bounded to standardized repository inputs:

- `standardized_data/repositories/repository_manifest.json`
- `manifests/standardized_assets_registry.json`
- `standardized_data/repositories/analysis_input_repository`
- `standardized_data/repositories/clinical_repository`
- validation and lineage metadata

It explicitly excludes formal reliance on:

- `recognition_report.json`
- UI temporary tables
- runner temporary output
- plot artifacts
- report packages
- unregistered raw clinical files

### B13 Controlled KM / Log-rank Carry-over

MainLine now has the controlled two-group KM/log-rank MVP modules:

- `km_parameter_gate.py`
- `km_confirmation.py`
- `km_executor.py`
- `km_result_schema.py`
- `km_review.py`
- `e2e_audit.py`
- `plots/survival.py`

Boundary:

- Runs only after survival input, outcome, parameter, user confirmation, dependency, and schema gates pass.
- Produces result-index v2 entries with `task_type=survival_km_logrank`.
- Uses `result_semantics=formal_computed_result` only when all gates pass.
- Keeps `plot_artifacts=[]`, `report_artifacts=[]`, and `report_ready_eligible=False` at runtime.
- KM plot is spec-only and source-result driven.

### B14 Cox Univariate Carry-over

MainLine now has the controlled single-variable Cox MVP modules:

- `cox_parameter_gate.py`
- `cox_confirmation.py`
- `cox_executor.py`
- `cox_result_schema.py`
- `cox_review.py`
- `cox_multivariate_design.py`
- `cox_e2e_audit.py`
- `plots/cox.py`

Boundary:

- Runs only after survival input, outcome, covariate, parameter, user confirmation, dependency, and schema gates pass.
- Produces result-index v2 entries with `task_type=cox_univariate`.
- HR / CI / p-value appear only in Cox univariate result bundles.
- Cox multivariate remains design audit only.
- Cox forest plot is spec-only and source-result driven.
- `report_ready_eligible=False` remains enforced.

## UI Gate Changes

Analysis Center now exposes survival/clinical gate state for:

- B12 survival input.
- B12 outcome gate.
- B13 KM/log-rank parameters.
- B13 KM/log-rank user confirmation.
- B14 Cox univariate parameters.
- B14 Cox user confirmation.
- B14 Cox multivariate design audit.
- Survival dependency state.

Action matrix additions:

- `km_logrank_parameter_confirmation`
- `km_cox_logrank`
- `cox_univariate_parameter_confirmation`
- `cox_univariate`
- `cox_multivariate` disabled
- `risk_score` disabled
- `survival_formal` still disabled for report-ready

UI copy now distinguishes:

- two-group KM/log-rank controlled MVP
- single-variable Cox controlled MVP
- multivariate Cox disabled
- risk score / nomogram disabled
- spec-only plot artifacts
- no clinical conclusion
- no survival report-ready package

## Dependency Policy

MainLine survival dependency detection is detect-first:

- Detects `lifelines`.
- Does not install dependencies.
- Missing `lifelines` blocks B13/B14 controlled execution gracefully.
- Settings/package metadata records `lifelines` packaging impact.

No automatic install action was added.

## Regression Boundary

Preserved:

- MainLine recognition logic.
- MainLine standardization logic.
- MainLine resolver contracts.
- Formal DEG MVP behavior.
- ORA/GSEA behavior.
- Existing result index/report-ready contracts.
- Existing package smoke behavior.

Not added:

- Cox multivariate execution.
- Survival report-ready package.
- Real rendered KM/Cox PNG/SVG/PDF plots.
- Clinical conclusion, prognosis, or treatment recommendation.
- GSEA/survival integration.
- ReleaseBuild code changes.

## Tests

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| Targeted B12/B13/B14 tests | Passed: 39 passed |
| `python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` | Passed: 11 passed |
| `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or analysis_ui"` | Passed: 82 passed, 371 deselected |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q -k "bioinformatics"` | Passed: 129 passed, 68 deselected |
| `python3 -m pytest tests/bioinformatics -q` | Passed: 453 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | Passed: 197 passed |
| `python3 -m app.main --smoke-test` | Passed |
| `python3 scripts/package_app.py --smoke-test` | Passed |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | Passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | Passed |

## Blockers / Major / Minor

### Blocker

None for MainLine scoped carry-over.

### Major

1. ReleaseBuild still has not received this MainLine convergence result.
2. ReleaseBuild must not directly overwrite its B12 modules from Bioinformatics source. It should receive the MainLine convergence commit or a scoped equivalent.

### Minor

1. Real KM/Cox plot rendering is intentionally not implemented.

## ReleaseBuild Next Step

Recommended next stage:

`B14.8 ReleaseBuild Survival Clinical Convergence Receive-from-MainLine`

ReleaseBuild should receive this MainLine convergence result, preserving its existing B12 contract files and re-running:

- `git diff --check`
- `python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
