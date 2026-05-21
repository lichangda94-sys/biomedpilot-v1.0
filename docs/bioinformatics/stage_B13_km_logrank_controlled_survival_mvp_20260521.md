# Bioinformatics B13 KM / Log-rank Controlled Survival MVP

## 旧实现审计

| Area | Conclusion | Notes |
| --- | --- | --- |
| `clinical_analysis/*` | 可复用 | B12-ish survival input package、survival preflight、clinical variable preflight、lifelines detect-first dependency snapshot can be reused. |
| `services/survival_service.py` | 最小迁入 | Kept as legacy/preflight context only; no direct runtime promotion. |
| `results/*` | 可复用 | Result index v2 registry/validation used for `survival_km_logrank`. |
| `plots/*` | 可复用并扩展 | Added KM curve spec artifact type; no image renderer dependency. |
| `analysis_ui/*` / `workflow_pages.py` | 最小迁入 | Analysis Center now shows B13 KM/log-rank gates while Cox/HR/report-ready remain disabled. |
| `legacy/*`, Integration, ReleaseBuild archive | 不迁入 | No old survival preview card, Cox, HR or clinical conclusion code was copied into formal runtime. |

## B13.1 KM / Log-rank Parameter Gate

Added `app/bioinformatics/survival_clinical/km_parameter_gate.py` and `km_confirmation.py`.

The parameter manifest records B12 input identifiers, time/event fields, event coding, censoring policy, grouping variable, group labels, sample lists, group counts, event counts, minimum size/event thresholds, missingness policy, log-rank method, dependency snapshot, warnings, blockers, and provenance. It blocks missing B12 input/outcome gate, outcome blockers, missing fields, ambiguous event coding, invalid grouping, overlapping groups, low group/event counts, mapping failures, and missing/failed dependency snapshot.

User confirmation is stored at `manifests/km_logrank_parameter_confirmation.json` with a manifest digest and output plan. Confirmation mismatch, missing confirmation, failed dependency, or changed parameter manifest blocks execution.

## B13.2 Controlled KM / Log-rank Execution

Added `app/bioinformatics/survival_clinical/km_executor.py` and `km_result_schema.py`.

Execution is limited to two-group KM curve data and a two-group log-rank chi-square df=1 p-value. It consumes only the B12 clinical asset path carried in the survival input package provenance. It writes:

- KM curve table: `time`, `survival_probability`, `group`, `at_risk`, `events`, `censored`, `time_unit`, `warnings`.
- Log-rank table: `group_a`, `group_b`, `test_statistic`, `p_value`, `method`, event/sample counts, `warnings`.
- Task-run log under `analysis/survival_km/`.
- Result index v2 entry with `task_type=survival_km_logrank` and `result_semantics=formal_computed_result`.

The result schema forbids Cox/HR fields such as `hazard_ratio`, `ci_lower`, `ci_upper`, and `cox_p_value`. It keeps `plot_artifacts=[]`, `report_artifacts=[]`, and `report_ready_eligible=False` after execution.

## B13.3 Review / Plot Artifact / E2E Audit

Added `km_review.py`, `plots/survival.py`, and `e2e_audit.py`.

KM review exposes group names, sample/event counts, median survival when calculable, log-rank p-value, time unit, censoring policy, missingness summary, engine/version, dependency snapshot, KM/log-rank previews, TSV/CSV export, and guard copy:

> This is a statistical survival analysis result. It is not a clinical prognosis conclusion. It is not a treatment recommendation. No Cox hazard ratio is produced in this stage.

KM plot activation is spec-only:

- `plot_type=km_curve`
- source must be `formal_computed_result` with `task_type=survival_km_logrank`
- source result semantics are inherited
- `image_artifacts=[]`
- `rendering=spec_only_no_image_dependency`

The E2E audit validates input traceability, parameter confirmation, dependency snapshot, task-run log, result index, result review, KM plot artifact source, absence of HR/Cox fields, and `report_ready_eligible=False`.

## Dependency Policy

`lifelines` is now a B13 controlled KM/log-rank runtime dependency gate. Detection is still detect-first only:

- no automatic install action
- Settings/Analysis Center show version/status/blockers
- missing lifelines blocks KM/log-rank execution without traceback
- R `survival` / `survminer` remain optional/not configured

`config/bioinformatics/package_requirements.yaml` records the packaging impact for `lifelines`.

## Result Semantics

Allowed formal result in B13:

- `task_type=survival_km_logrank`
- `result_semantics=formal_computed_result`

Only produced when B12 input/outcome gates, B13 parameter gate, dependency gate, user confirmation, runtime validation, and result schema validation pass. B12 preflight, clinical variable audit, parameter manifests, blocked runs, testing previews, and imported sources are not promoted to formal results.

## UI Changes

Analysis Center now shows:

- Survival design preflight row
- Two-group KM/log-rank parameter status and disabled reasons
- KM plot artifact/spec row
- Cox / HR disabled row
- Clinical association preflight row
- lifelines dependency status and packaging impact

Action matrix now has a separate `Confirm KM/log-rank parameters` action and a gate-driven `Run two-group KM/log-rank` action. Cox, HR, multivariable survival, clinical conclusions, and survival report-ready remain disabled.

## Report Boundary

B13 does not create survival report-ready packages and does not add KM/log-rank into DEG/ORA/GSEA report packages. `report_ready_eligible` remains false, `report_artifacts=[]`, and report status remains disabled with `survival_report_gate_not_implemented`.

## Tests And Validation

Executed during implementation:

- `python3 -m pytest tests/bioinformatics/test_km_logrank_parameter_gate.py tests/bioinformatics/test_km_logrank_confirmation.py tests/bioinformatics/test_km_logrank_execution.py tests/bioinformatics/test_km_result_schema.py tests/bioinformatics/test_km_result_review.py tests/bioinformatics/test_km_plot_artifact.py tests/bioinformatics/test_survival_e2e_acceptance_audit.py -q` -> passed.
- `python3 -m pytest tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_clinical_association_preflight.py tests/bioinformatics/test_survival_input_preflight.py -q` -> passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` -> passed.

Full required test sweep is recorded in the final task report after completion.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics/test_km_logrank_parameter_gate.py tests/bioinformatics/test_km_logrank_execution.py tests/bioinformatics/test_km_result_schema.py tests/bioinformatics/test_km_result_review.py tests/bioinformatics/test_km_plot_artifact.py tests/bioinformatics/test_survival_e2e_acceptance_audit.py -q` -> 12 passed.
- `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or km or logrank or result_semantics or plot or analysis_ui"` -> 65 passed, 325 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` -> 12 passed, 97 deselected.
- `python3 -m pytest tests/bioinformatics -q` -> 390 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed.

Package/codesign commands were not run because B13 did not modify launcher, packaging, app bundle, or codesign configuration.

## 保留边界

Not implemented in B13:

- Cox univariate or multivariate
- hazard ratio / confidence intervals
- clinical association formal p-values
- automatic best cutoff or maximally selected rank statistics
- risk score model
- survival report-ready package
- full integrated report
- real PNG/SVG/PDF KM rendering
- R survival/survminer runtime
- prognosis or treatment recommendation

## Next Recommendation

Proceed to B14.1 Cox univariate parameter gate only after B13 is stable in source/UI/package validation. B14.1 should start with contract planning and dependency/runtime audit, not immediate Cox execution.
