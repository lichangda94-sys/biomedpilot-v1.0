# Meta M9 Statistical Executor Pre-integration Audit - 2026-05-13

## Stage

Meta M9 - Real Statistical Executor Pre-integration Audit

This is an audit/report stage for future statistical executor integration. No real statistical executor was implemented in this stage.

## Branch and HEAD

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Meta`
- Branch: `dev/meta-analysis`
- HEAD before work: `293a0b5` (`feat(meta): add draft report generation`)
- Scope: documentation-only report
- Expected untracked input artifact preserved: `docs/meta_dev_reports/Meta_handoff_report_20260513.md`

## Files inspected

- `CODEX.md`
- `README.md`
- `docs/meta_dev_reports/Meta_handoff_report_20260513.md`
- `app/meta_analysis/services/meta_statistics_engine_service.py`
- `app/meta_analysis/services/analysis_run_service.py`
- `app/meta_analysis/services/analysis_dataset_service.py`
- `app/meta_analysis/services/analysis_plan_service.py`
- `app/meta_analysis/services/manual_extraction_effect_row_service.py`
- `app/meta_analysis/services/advanced_analysis_service.py`
- `app/meta_analysis/services/figure_result_service.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/models/analysis_dataset.py`
- `app/meta_analysis/stats/meta_models.py`
- `app/meta_analysis/stats/meta_effects.py`
- `app/meta_analysis/stats/heterogeneity.py`
- `tests/meta_analysis/test_meta_statistics_engine_v2.py`
- `tests/meta_analysis/test_analysis_core_mvp.py`
- `tests/meta_analysis/test_stage_n_statistical_method_audit.py`
- `tests/meta_analysis/test_advanced_methods_expansion.py`
- `tests/meta_analysis/test_advanced_analysis_addons.py`
- `tests/meta_analysis/test_analysis_plan_builder_v1.py`
- `tests/meta_analysis/test_draft_report_generation_m8.py`
- `tests/meta_analysis/test_figure_result_table_mvp.py`

## Current statistical capability classification

| Component | Classification | Audit notes |
| --- | --- | --- |
| `app/meta_analysis/services/meta_statistics_engine_service.py` | `testing_level` | Newer guarded statistics path. Requires confirmed analysis plan, writes run/result/manifest/audit artifacts, records governance as suggestions, sets `testing_level_notice`, `production_grade=False`, and `medical_conclusion_status=not_generated`. Not a validated formal executor. |
| `app/meta_analysis/services/analysis_plan_service.py` | `testing_level` | M7 plan workspace supports draft and confirmed plans. Confirmation only marks future executor eligibility and does not run statistics. Good prerequisite for future executor gate. |
| `app/meta_analysis/services/manual_extraction_effect_row_service.py` | `testing_level` | M5 structured/manual extraction supports effect fields and evidence states. Confirmed rows can feed plans, but future executor still needs stricter effect-size normalization and row-level result eligibility. |
| `app/meta_analysis/services/analysis_dataset_service.py` | `testing_level` | Builds analysis-ready datasets from extraction records, including binary, continuous, generic, proportion, correlation, and diagnostic data. Network meta returns `not_implemented`. Needs stricter result-state and confirmed-only enforcement before formal use. |
| `app/meta_analysis/stats/meta_effects.py` | `testing_level` | Implements basic effect conversion for OR, RR, RD, MD, SMD, HR/generic inverse variance, proportions, correlations, and diagnostic ratios. Tested against local fixtures, but not externally validated as a production statistics library. |
| `app/meta_analysis/stats/meta_models.py` | `testing_level` | Implements fixed/random inverse-variance pooling. Random model uses a DerSimonian-Laird style tau-squared from `heterogeneity.py`. Suitable as testing foundation only. |
| `app/meta_analysis/stats/heterogeneity.py` | `testing_level` | Computes Q, I2, and tau-squared. No formal method selection, small-sample correction policy, or external statistical package parity audit yet. |
| `app/meta_analysis/services/analysis_run_service.py` | `unsafe_for_formal_use` | Older active service can generate `AnalysisResult` and persist pooled effects, forest/table source data, and task records without explicit `testing_level`, `production_grade`, `result_state`, or `medical_conclusion_status` fields in the result model. It is test-covered but must not be used as a formal executor without hardening. |
| `app/meta_analysis/models/analysis_result.py` | `unsafe_for_formal_use` | Current model stores pooled effect, CI, p value, heterogeneity, and study rows but has no result-state semantics. Future formal executor needs explicit states such as `computed`, `user_reviewed`, and `report_ready`. |
| `app/meta_analysis/services/figure_result_service.py` | `testing_level` / `UI_only` | Generates forest plot PNG and result table CSV from `AnalysisResult`. Useful rendering foundation, but artifacts depend on testing-level result semantics and should not be report-formal before executor audit. |
| `app/meta_analysis/services/advanced_analysis_service.py` | `testing_level` / `placeholder` | Subgroup and leave-one-out are simple testing helpers. Egger is a basic implementation; Begg is explicitly not implemented. Funnel plot is generated from testing-level results. |
| `app/meta_analysis/pages/analysis_page.py` | `UI_only` / `testing_level` | UI state declares internal testing labels, warnings, and blocked methods. The page exposes both older analysis result fields and newer M7/M9-style guarded state. |
| `app/meta_analysis/services/formal_report_service.py` | `testing_level` / `placeholder` | M8 draft report clearly states Developer Preview/testing and does not insert formal pooled effects, p values, forest plots, funnel plots, or medical conclusions. |
| `app/meta_analysis/legacy/**` | `legacy_isolated` | Historical isolation area only. Not inspected as active runtime proof and must not be used for future executor integration. |
| Network meta-analysis | `missing` / `placeholder` | Registry and dataset validation identify network meta as not implemented. |
| HSROC / bivariate diagnostic model | `missing` / `placeholder` | Diagnostic 2x2 basic metrics exist, but formal bivariate/HSROC model is not implemented. |
| Meta-regression | `missing` | No formal executor component found. |
| Publication bias beyond basic Egger | `placeholder` | Begg is explicitly not implemented; funnel plots are testing-level visualization only. |

## Data readiness audit by effect type

| Effect type | Required fields for future executor | Current extraction/schema coverage | Readiness |
| --- | --- | --- | --- |
| OR | Events and totals per case/intervention and control group, or reported OR with CI/SE | Covered by `events_case`, `total_case`, `events_control`, `total_control`, and older `group_1/group_2` raw fields; reported effect fields also exist | `testing_level_ready`, needs normalization and continuity policy audit |
| RR | Events and totals per case/intervention and control group, or reported RR with CI/SE | Covered similarly to OR | `testing_level_ready`, needs normalization and zero-cell policy audit |
| HR | Reported HR with CI or SE; optional adjusted/unadjusted metadata | Covered by `effect_measure_type`, `effect_estimate`, `ci_lower`, `ci_upper`, `standard_error`; older reported effect fields also support HR | `testing_level_ready`, needs adjusted-effect governance and survival-method assumptions |
| MD | Means, SDs, and totals for both groups | Covered by `mean_case`, `sd_case`, `total_case`, `mean_control`, `sd_control`, `total_control`; older raw fields also support it | `testing_level_ready`, needs unit/direction harmonization |
| SMD | Means, SDs, and totals for both groups | Covered by MD fields | `testing_level_ready`, needs SMD variant and small-sample correction policy audit |
| Proportion | Single-arm events and total, transformation policy | Partially covered through `events_case`/`total_case` and older `events`/`total` paths; M5 field names need explicit single-arm mapping | `partial`, needs normalized single-arm schema |
| Correlation | Correlation coefficient and sample size | Covered by `correlation_coefficient` and `sample_size_total`; older correlation outcome supports `r` and `sample_size` | `testing_level_ready`, needs Fisher-z policy and bounds validation in executor gate |
| Diagnostic accuracy | TP, FP, FN, TN; selected metric such as sensitivity, specificity, PLR, NLR, or DOR | Covered by `diagnostic_tp`, `diagnostic_fp`, `diagnostic_fn`, `diagnostic_tn`; older diagnostic fields support `tp/fp/fn/tn` | `partial`, basic metrics only; bivariate/HSROC missing |

## Future executor prerequisites

A future real statistical executor should require all of the following before producing formal output:

- Confirmed M7 analysis plan.
- Confirmed M5 extraction rows only; draft, suggested, rejected, and unreviewed rows must be excluded.
- Explicit effect-type consistency or an approved normalization map.
- Minimum study-count policy by method and output type.
- Valid numeric fields, confidence interval order, positive variance, and non-negative counts.
- Effect-direction and unit harmonization review for MD/SMD and ratio measures.
- Model settings captured in a reproducible run manifest.
- Clear result-state semantics independent of task success.
- Warnings when assumptions are not met.
- Audit trail linking source plan, source extraction rows, normalization decisions, method version, code version, and output artifacts.

## Future result-state semantics

Recommended formal result states:

- `not_run`: no executor request has been configured.
- `configured_not_run`: plan and data are selected but execution has not happened.
- `testing_level`: current Developer Preview/testing output or any non-validated helper output.
- `failed_validation`: executor refused to run because prerequisite validation failed.
- `computed`: validated executor produced deterministic output artifacts.
- `user_reviewed`: user reviewed assumptions, warnings, and outputs.
- `report_ready`: result is approved for inclusion in a report-safe summary.

Only `computed`, `user_reviewed`, or `report_ready` should be eligible for future formal statistical report sections, and only after the executor validation stage defines what "formal" means for this product.

## Future output requirements

The future executor should produce:

- Result manifest with schema version, executor version, method version, code commit, timestamp, and source artifact refs.
- Table output with per-study effect data, transformed effect, standard error, variance, model weight, warnings, and inclusion status.
- Forest plot data as structured coordinates/data, with rendering separate from computation.
- Heterogeneity summary with Q, degrees of freedom, p value, I2, tau2, and method labels.
- Model settings including fixed/random/both, tau estimator, transformation, continuity correction, CI method, and publication-bias eligibility.
- Warnings for study count, mixed effect type, missing fields, zero-event correction, adjusted/unadjusted mixing, and incomplete quality assessment.
- Reproducibility metadata including input hashes and manifest-relative paths only.
- Report-safe summary that is explicit about user review and result state.

## Future UI requirements

- Do not show a formal result until the executor returns `computed`.
- Keep current Developer Preview/testing labels for all existing helper outputs.
- Show assumptions, method settings, data warnings, excluded rows, and audit refs before user review.
- Prevent draft/suggested extraction rows, unconfirmed plans, or incomplete quality warnings from silently entering formal analysis.
- Keep raw JSON, manifest paths, local paths, and internal IDs out of the normal user-facing UI.
- Developer diagnostics may expose internals only in collapsed diagnostics.

## Missing requirements and risks

- `AnalysisResult` lacks explicit result-state fields, production/testing flags, result review state, and medical-conclusion status. This is the highest-priority model gap before M11.
- `AnalysisRunService` is an older testing path that can create pooled result artifacts without the newer M7/M9 guard metadata. It should be retired, wrapped, or converted to use the future executor contract before formal integration.
- Current pooling helpers are local implementations with local fixture tests, not an externally audited or validated statistical engine.
- Forest and funnel plot services render from testing-level result models; formal plot integration should consume executor plot data instead.
- Proportion and diagnostic workflows need explicit normalized input contracts before formal execution.
- Publication-bias support is incomplete; Begg is placeholder and Egger has no formal p value in the newer engine.
- Network meta-analysis, meta-regression, and bivariate/HSROC diagnostic models are missing.
- Report generation is safe in M8 because it avoids formal statistical conclusions, but future M13 must gate report insertion on result state.

## Recommended future executor architecture

1. Introduce a narrow `StatisticalExecutorInput` contract built only from confirmed M7 plans and confirmed M5 extraction rows.
2. Add an M10 effect-size normalization service that converts all supported extraction shapes into a single validated effect table.
3. Keep computation separate from rendering and reporting:
   - normalization service
   - validation service
   - executor service
   - result manifest writer
   - plot-data writer
   - report-safe summarizer
4. Add a result-state model and require state transitions through validation, computation, user review, and report readiness.
5. Make current testing helpers opt-in and visibly labeled; avoid reusing `AnalysisResult` as the formal result payload without adding state semantics.
6. Add parity tests against a trusted external reference set or package output before any formal executor claim.

## Proposed future stages

- M10 - effect-size normalization service: normalize OR/RR/HR/MD/SMD/proportion/correlation/diagnostic inputs, validate numeric fields, and produce executor-ready effect tables.
- M11 - real pairwise meta executor: implement or integrate validated pairwise fixed/random meta-analysis with reproducible manifests and result states.
- M12 - plot data and visualization: generate forest/funnel plot data from executor outputs and render report-safe figures only for computed/reviewed results.
- M13 - report-safe statistical result integration: allow M8-style reports to include statistical results only when result state and review status allow it.
- M14 - integration validation: run parity, regression, UI safety, reproducibility, and report-gating validation before any production-like claim.

## Validation

Validation completed on 2026-05-13:

```bash
git diff --check
# exit code 0; no output

python3 -m pytest tests/meta_analysis -q
# exit code 0
# 485 passed in 4.99s

QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
# exit code 0
# BioMedPilot / 医研智析
# app_version=0.1.0-internal-beta
# app_channel=Developer Preview / testing
# launch_mode=source
# app_root=/Users/changdali/Developer/biomedpilot v1.0/Meta
# git_head=293a0b5
# workspace_entries=2
# bioinformatics_features=5
# meta_analysis_features=7
# pyside6_available=True
```

## Limitations

- This audit did not implement a real executor.
- This audit did not modify runtime code or tests.
- This audit did not inspect `app/meta_analysis/legacy/**` as active runtime proof; legacy remains historical and isolated.
- This audit did not perform external statistical package parity validation.
- This audit does not upgrade any output from Developer Preview/testing status.

## Remaining untracked or dirty files

Status before committing this report:

```text
## dev/meta-analysis
?? docs/meta_dev_reports/Meta_M9_statistical_executor_preintegration_audit_20260513.md
?? docs/meta_dev_reports/Meta_handoff_report_20260513.md
```

Expected preserved input artifact: `docs/meta_dev_reports/Meta_handoff_report_20260513.md`.

## Commit status

Commit made for this stage with message: `docs(meta): audit statistical executor integration`. The exact final commit hash is reported in the assistant handoff after commit creation. No remote push is in scope.
