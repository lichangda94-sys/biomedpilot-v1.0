# Bioinformatics B14 Cox / Clinical Association Controlled MVP

## 旧实现审计

| Area | Conclusion | Notes |
| --- | --- | --- |
| `survival_clinical/*` | 可复用并扩展 | B13 KM/log-rank contract shape reused for parameter confirmation, result index v2, review, plot artifact and E2E audit. |
| `clinical_analysis/*` | 可复用 | Survival input package, outcome preflight, clinical variable typing/missingness and lifelines detect-first dependency snapshot reused. |
| `services/survival_service.py` | 最小迁入 | Kept as historical/preflight context only; no old preview runtime promoted. |
| `results/*` | 可复用 | Result index v2 registry and base validation reused for `task_type=cox_univariate`. |
| `plots/*` | 可复用并扩展 | Added Cox forest plot spec artifact; no renderer dependency. |
| `reports/*` | 不迁入为 Cox report-ready | B14 keeps `report_ready_eligible=False` and `report_artifacts=[]`. |
| `legacy/*`, Integration, ReleaseBuild archive | 不迁入 | No legacy Cox preview card, batch clinical p-values, clinical conclusion or risk score code was copied into formal runtime. |

## B14.1 Cox Univariate Parameter Gate

Added:

- `app/bioinformatics/survival_clinical/cox_parameter_gate.py`
- `app/bioinformatics/survival_clinical/cox_confirmation.py`

The Cox parameter manifest records B12 survival input/outcome identifiers, time/event fields, censoring/event coding, one covariate, covariate type/source/transform policy, included/excluded cases, sample/event/non-missing/missing counts, missing rate, minimum thresholds, dependency snapshot, warnings, blockers and provenance.

Blocking rules cover missing B12 input/outcome, outcome blockers, missing fields, ambiguous event coding, missing/unknown/identifier/date covariate, all-missing or constant covariate, too few samples/events/non-missing values, too many categories, mapping failure and missing/failed dependency snapshot.

Warnings include high missingness, unbalanced binary groups, rare categories, ordinal order needs confirmation, continuous outliers, PH assumption not tested, single-variable-only and not-clinical-conclusion boundaries.

User confirmation is stored at `manifests/cox_univariate_parameter_confirmation.json`; changed manifests, missing confirmation or failed dependency block execution.

## B14.2 Controlled Cox Univariate Execution

Added:

- `app/bioinformatics/survival_clinical/cox_executor.py`
- `app/bioinformatics/survival_clinical/cox_result_schema.py`

Execution is limited to a single-variable Cox proportional hazards MVP. It consumes only the B12 clinical asset path carried by the survival input package provenance and writes:

- Cox result table with `covariate`, `hazard_ratio`, `ci_lower`, `ci_upper`, `p_value`, `z_statistic`, counts, method and warnings.
- Task-run log under `analysis/survival_cox/`.
- Result index v2 entry with `task_type=cox_univariate`, `result_semantics=formal_computed_result`, `plot_artifacts=[]`, `report_artifacts=[]`, `report_ready_eligible=False`.

The runtime records `proportional_hazards_assumption_not_formally_tested`; it does not claim PH diagnostics were validated. It forbids `multivariate_adjusted_hr`, `risk_score`, `clinical_risk_group` and `treatment_recommendation`.

## B14.3 Cox Review / Forest Plot Artifact / E2E Audit

Added:

- `app/bioinformatics/survival_clinical/cox_review.py`
- `app/bioinformatics/plots/cox.py`
- `app/bioinformatics/survival_clinical/cox_e2e_audit.py`

Cox review displays result id, covariate, covariate type, HR, CI, p-value, sample/event/missing counts, method, engine/version, dependency snapshot, warnings, table preview and TSV/CSV export.

Guard copy:

> This is a single-variable Cox statistical result. It is not a clinical prognosis conclusion. It is not a treatment recommendation. It is not a validated risk score. Multivariate Cox is not performed in this stage.

Forest plot artifact is spec-only:

- `plot_type=cox_forest_plot`
- source must be `formal_computed_result` with `task_type=cox_univariate`
- source semantics are inherited
- `image_artifacts=[]`
- `rendering=spec_only_no_image_dependency`

E2E audit validates B12/B14 traceability, confirmation, dependency snapshot, task-run log, result index, Cox table, review, plot artifact source, absence of multivariate/risk/clinical fields and `report_ready_eligible=False`.

## B14.4 Cox Multivariate Design Audit

Added:

- `app/bioinformatics/survival_clinical/cox_multivariate_design.py`

The design audit records candidate/selected covariates, event count, sample count, event per variable, missingness summary, category/type warnings, formula preview, blockers and provenance. It blocks too few events, too many covariates for event count, no valid covariates, high missingness, unknown variable type, unresolved collinearity and missing user confirmation.

It is design-only and does not execute multivariate Cox, adjusted HR, multivariate p-values, variable selection, risk score or nomogram.

## Dependency Policy

`lifelines` remains detect-first with no automatic install action. Missing lifelines blocks B14 Cox execution without traceback. Optional R survival/survminer remains not configured and is not called.

`config/bioinformatics/package_requirements.yaml` now documents that lifelines gates both B13 KM/log-rank and B14 single-variable Cox MVP.

## Result Semantics

Allowed formal result in B14:

- `task_type=cox_univariate`
- `result_semantics=formal_computed_result`

Only produced when B12 input/outcome gates, B14 parameter gate, dependency gate, user confirmation, controlled execution and result schema validation pass. B12 preflight, clinical variable audit, Cox parameter manifest, Cox multivariate design audit, blocked/failed runs and testing previews are not formal results.

## UI Changes

Analysis Center Survival / Clinical section now shows:

- B12 survival design preflight
- B13 two-group KM/log-rank gate
- KM plot artifact/spec
- B14 single-variable Cox gate
- Cox forest plot artifact/spec
- Multivariate Cox design audit
- Risk score / nomogram disabled
- Clinical association preflight

Action matrix now has `Confirm Cox univariate parameters` and `Run single-variable Cox` gate-driven rows. Multivariate Cox, risk score, survival report-ready and clinical conclusions remain disabled or hidden until a later audited stage.

## Report And Clinical Interpretation Boundary

B14 does not generate Cox report-ready packages and does not add Cox into DEG/ORA/GSEA/KM report packages. `report_ready_eligible=False` and `report_artifacts=[]` are preserved. UI/review copy explicitly states statistical result only, no prognosis conclusion, no treatment recommendation, no validated risk score and no multivariate Cox.

## Tests And Validation

Implementation validation:

- `python3 -m pytest tests/bioinformatics/test_cox_univariate_parameter_gate.py tests/bioinformatics/test_cox_univariate_confirmation.py tests/bioinformatics/test_cox_univariate_execution.py tests/bioinformatics/test_cox_result_schema.py tests/bioinformatics/test_cox_result_review.py tests/bioinformatics/test_cox_plot_artifact.py tests/bioinformatics/test_cox_e2e_acceptance_audit.py tests/bioinformatics/test_cox_multivariate_design_audit.py -q` -> 14 passed.
- `python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` -> 11 passed.
- `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or result_semantics or plot or analysis_ui"` -> 79 passed, 325 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` -> 12 passed, 97 deselected.

Full required sweep is recorded after final validation.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics/test_cox_univariate_parameter_gate.py tests/bioinformatics/test_cox_univariate_execution.py tests/bioinformatics/test_cox_result_schema.py tests/bioinformatics/test_cox_result_review.py tests/bioinformatics/test_cox_plot_artifact.py tests/bioinformatics/test_cox_e2e_acceptance_audit.py tests/bioinformatics/test_cox_multivariate_design_audit.py -q` -> 13 passed.
- `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or result_semantics or plot or analysis_ui"` -> 79 passed, 325 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` -> 12 passed, 97 deselected.
- `python3 -m pytest tests/bioinformatics -q` -> 404 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed.
- `python3 scripts/package_app.py --smoke-test` -> passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test` -> passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` -> passed.

## 保留边界

Not implemented:

- multivariate Cox execution
- automatic variable selection / stepwise Cox / LASSO Cox
- adjusted HR / multivariate p-value
- risk score / nomogram / risk group
- PH diagnostic formal pass/fail
- batch clinical association p-values
- Cox report-ready package
- full integrated report
- PNG/SVG/PDF forest plot rendering
- R survival/survminer calls
- prognosis, diagnosis or treatment recommendation

## Next Recommendation

Proceed to B14.5 Cox closure audit if the goal is to harden B12-B14 survival boundaries. If the next user-facing priority is visualization, proceed to B15 formal plotting/rendering engine planning without expanding clinical interpretation.
