# Bioinformatics B14.5 Cox / Survival Clinical Closure Audit

## 审计范围

Baseline: `dc4d49c add Bioinformatics controlled Cox univariate MVP`.

Audited areas:

- B12 survival/clinical input package, outcome preflight, clinical variable typing and dependency detection.
- B13 KM/log-rank parameter gate, confirmation, execution, review, KM plot spec and E2E audit.
- B14 Cox univariate parameter gate, confirmation, execution, review, forest plot spec, E2E audit and multivariate design audit.
- Analysis Center UI state/action rows and workflow page rendering.
- Result index v2, plot artifact semantics, report-ready boundary and clinical interpretation guard copy.

Untracked files intentionally excluded from audit commit:

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
- `project_storage/bioinformatics/`

## Closure Table

| Check | Result | Evidence |
| --- | --- | --- |
| 1. B12 input / outcome / clinical variable audit not formal result | Pass | `clinical_analysis/*` returns preflight/design dictionaries only and does not call result registry. |
| 2. KM/log-rank result only from B12/B13 gates | Pass | `run_controlled_km_logrank` requires parameter gate, user confirmation and passed dependency before registering `survival_km_logrank`. |
| 3. Cox univariate result only from B12/B14 gates | Pass | `run_controlled_cox_univariate` blocks unless Cox parameter manifest, confirmation and dependency gate pass. |
| 4. Cox multivariate remains design audit | Pass | `audit_cox_multivariate_design` records `design_audit_only=True` and `multivariate_execution=False`; UI run action remains disabled. |
| 5. HR / CI / Cox p-value limited to Cox univariate result | Pass with note | `hazard_ratio`, `ci_lower`, `ci_upper` are only in Cox result schema/executor/review/forest plot spec. Generic `p_value` also exists in DEG and B13 log-rank; Cox p-value is limited to `cox_univariate`. |
| 6. KM / Cox plot artifacts spec-only | Pass | KM and Cox plot artifacts use `rendering=spec_only_no_image_dependency` and `image_artifacts=[]`; no PNG/SVG/PDF renderer dependency. |
| 7. `report_ready_eligible` remains false | Pass | KM and Cox executors, plot registration and E2E audits preserve `report_ready_eligible=False`; report artifacts stay empty. |
| 8. No clinical conclusion / prognosis / treatment advice | Pass | Review guard copy and UI disabled reasons explicitly state statistical-only, no prognosis, no treatment recommendation and no risk score. |
| 9. UI distinguishes KM/log-rank, Cox univariate, multivariate disabled | Pass | Analysis Center rows show Two-group KM/log-rank, Single-variable Cox, Cox forest plot artifact/spec, Multivariate Cox design audit and Risk score disabled. |
| 10. E2E audit covers failure cases | Pass after small hardening | Added blocker pass-through in KM/Cox E2E audits and tests covering missing dependency, invalid covariate, low event count and preflight source blocked. |

## Small Hardening

Two E2E audit helpers now preserve original parameter-gate blockers when the parameter manifest is blocked:

- `audit_survival_km_e2e_acceptance` now reports specific KM blockers such as `minimum_event_count_not_met`.
- `audit_cox_univariate_e2e_acceptance` now reports specific Cox blockers such as `identifier_not_allowed_as_covariate` and `minimum_event_count_not_met`.

This is not a feature expansion. It only improves closure-audit diagnosability.

## Boundary Notes

KM/log-rank:

- Formal result: `task_type=survival_km_logrank`, `result_semantics=formal_computed_result`.
- Requires B12 input/outcome package, B13 parameter gate, confirmation and dependency snapshot.
- Does not output HR, CI, Cox p-value, clinical conclusion or report-ready package.

Cox univariate:

- Formal result: `task_type=cox_univariate`, `result_semantics=formal_computed_result`.
- Requires B12 input/outcome package, B14 parameter gate, confirmation and dependency snapshot.
- Outputs HR/CI/p-value only for the selected single covariate.
- Records PH assumption not formally tested.

Cox multivariate:

- Design audit only.
- No adjusted HR, multivariate p-value, stepwise selection, LASSO, risk score, nomogram or clinical risk grouping.

Plot/report:

- KM plot and Cox forest plot are spec-only artifacts.
- `image_artifacts=[]`.
- `report_ready_eligible=False`.
- `report_artifacts=[]`.

## UI Audit

Analysis Center Survival / Clinical section clearly separates:

- B12 survival design preflight.
- B13 two-group KM/log-rank.
- B13 KM plot artifact/spec.
- B14 single-variable Cox.
- B14 Cox forest plot artifact/spec.
- B14 multivariate Cox design audit.
- Risk score / nomogram disabled.
- Clinical association preflight.

Action matrix separates executable controlled MVP actions from disabled future actions:

- `Run two-group KM/log-rank` is gate-driven.
- `Run single-variable Cox` is gate-driven.
- `Run multivariate Cox` is disabled.
- `Generate risk score` is disabled.
- Survival report-ready remains disabled.

## Tests And Validation

Commands run for this audit:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics/test_cox_e2e_acceptance_audit.py tests/bioinformatics/test_survival_e2e_acceptance_audit.py -q` -> 6 passed.
- `python3 -m pytest tests/bioinformatics/test_cox_univariate_parameter_gate.py tests/bioinformatics/test_cox_multivariate_design_audit.py tests/bioinformatics/test_km_logrank_parameter_gate.py -q` -> 7 passed.

Full post-document validation is recorded in the final response.

Final validation:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics/test_cox_e2e_acceptance_audit.py tests/bioinformatics/test_survival_e2e_acceptance_audit.py -q` -> 6 passed.
- `python3 -m pytest tests/bioinformatics/test_cox_univariate_parameter_gate.py tests/bioinformatics/test_cox_multivariate_design_audit.py tests/bioinformatics/test_km_logrank_parameter_gate.py -q` -> 7 passed.
- `python3 -m pytest tests/bioinformatics -q -k "survival or clinical or cox or km or logrank or result_semantics or plot or analysis_ui"` -> 81 passed, 325 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or survival or clinical or results_browser"` -> 12 passed, 97 deselected.
- `python3 -m pytest tests/bioinformatics -q` -> 406 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 176 passed.
- `python3 -m app.main --smoke-test` -> passed.
- `python3 scripts/package_app.py --smoke-test` -> passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test` -> passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` -> passed.

## Issues

Blocker: none.

Major: none.

Minor:

- The term `p_value` is shared by DEG, KM/log-rank and Cox result tables. The closure boundary should be read as Cox HR/CI/Cox model p-value must only appear in `cox_univariate`; B13 log-rank p-value remains valid within `survival_km_logrank`.

## Final Conclusion

小问题通过.

B12-B14 survival/clinical contracts are closed for the current MVP boundary. KM/log-rank and Cox univariate are controlled formal results only after their gates pass. Cox multivariate remains design audit only. Plot artifacts remain spec-only. Survival/Cox report-ready and clinical interpretation remain disabled.

## Recommendation

Proceed to B15 formal plotting/rendering engine planning if the next priority is real image rendering. If the priority is release hardening, proceed to a MainLine/ReleaseBuild carry-over audit for B12-B14 survival/clinical contracts.
