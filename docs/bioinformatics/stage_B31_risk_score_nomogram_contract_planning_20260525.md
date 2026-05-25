# Bioinformatics B31 Risk Score / Nomogram Contract Planning

Date: 2026-05-25

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline: `856acae docs(bio): close PDF rendered export ReleaseBuild gate`

## Scope

B31 plans the risk score / nomogram development line after B20/B28 multivariate Cox and B23-B30 report/renderer closure.

This stage is planning and gate hardening only. It must not generate a risk score, high/low-risk grouping, nomogram, clinical prognosis label, treatment recommendation, or clinical conclusion.

## Current State

Already implemented:

- B12 survival/clinical input, outcome, clinical variable, and sample/case contract hardening.
- B13 KM/log-rank controlled MVP.
- B14 Cox univariate controlled MVP.
- B20 Cox multivariate gated execution.
- B21 risk score design audit only.
- B22 KM/Cox real plot artifact gates.
- B23 full integrated report gate/package.
- B28 Cox multivariate review and section report-ready integration.
- B29/B30 DOCX/PDF rendered export package artifacts.

Current risk score status:

- `app/bioinformatics/survival_clinical/risk_score_design.py` exists.
- Schema: `biomedpilot.risk_score_design_audit.v1`.
- UI row: `Risk score / nomogram`.
- Action state: disabled / design audit only.
- `formal_execution_enabled=False`.
- `writes_result_index=False`.
- `result_semantics=design_audit_only`.
- `report_ready_eligible=False`.

## Hard Boundaries

B31 must preserve:

- No clinical diagnosis.
- No prognosis conclusion.
- No treatment recommendation.
- No validated risk group label.
- No nomogram output.
- No automatic variable selection.
- No LASSO/glmnet execution until a future audited backend stage.
- No report-ready package for risk score.
- No full integrated report unlock from risk score.
- No imported/testing/exploratory/preflight result upgrade.

## Required Source Contract

Risk score planning may only use audited sources:

1. B12 survival/clinical input package.
2. B12 clinical variable audit.
3. Formal Cox multivariate result with:
   - `result_semantics=formal_computed_result`
   - `task_type=cox_multivariate`
   - dependency snapshot passed
   - parameters manifest present
   - result table validation passed
   - task-run log present
   - no blockers
4. B28 Cox multivariate section package may be referenced for provenance, but it does not make risk score report-ready.

Forbidden sources:

- Cox univariate result as coefficient source.
- KM/log-rank result as coefficient source.
- Imported/testing/exploratory/preflight result.
- UI table rows or temporary preview tables.
- Legacy formal execution output.
- Free-text clinical conclusion.

## B31 Gate Design

Planned gate: `biomedpilot.risk_score_nomogram_contract_gate.v1`.

Minimum fields:

- `schema_version`
- `created_at`
- `status`
- `source_survival_package_id`
- `source_clinical_variable_audit_id`
- `source_cox_multivariate_result_id`
- `source_result_semantics`
- `source_result_validation_status`
- `source_result_dependency_snapshot`
- `source_result_parameters_manifest`
- `candidate_variables`
- `coefficient_source`
- `training_validation_plan`
- `cutoff_policy`
- `overfitting_protection_plan`
- `external_validation_plan`
- `missingness_policy`
- `scaling_policy`
- `calibration_plan`
- `nomogram_policy`
- `interpretation_boundary`
- `forbidden_outputs`
- `blockers`
- `warnings`

Must block:

- missing B12 survival/clinical input
- missing clinical variable audit
- missing formal Cox multivariate result
- Cox univariate source
- source result not `formal_computed_result`
- source result has blockers
- source dependency snapshot missing/failed
- source parameters manifest missing
- candidate variable not in clinical audit
- coefficient provenance missing
- training/validation split missing
- external validation missing when required
- cross-validation/overfitting protection missing
- cutoff policy missing or data-leakage prone
- missingness policy missing
- nomogram renderer requested before nomogram policy approval
- clinical conclusion text requested

## UI Planning

Analysis Center should continue to show `Risk score / nomogram` as disabled until a future execution stage.

B31 UI should expose:

- source Cox multivariate result readiness
- candidate variables
- training/validation plan status
- coefficient provenance
- cutoff policy
- overfitting/validation status
- disabled reasons
- guard copy: statistical model design only, not clinical prognosis

No normal-user button should run a risk score model in B31.

Developer preview actions, if added later, must remain separated from ordinary analysis actions and must not write formal results.

## Report / Plot Boundary

B31 does not create:

- risk score table
- risk group table
- nomogram plot
- calibration curve
- decision curve
- risk score report-ready package
- integrated report risk-score section

Future report integration requires a separate stage after:

1. execution backend gate passes
2. risk score result schema gate passes
3. validation/calibration gate passes
4. interpretation boundary audit passes
5. report package contract is defined

## Proposed Stage Sequence

### B31.1 Risk Score Source / Contract Gate

Implement a gate that validates source Cox multivariate result, clinical variable audit, coefficient provenance, and training/validation design. It remains non-executing and writes no result index.

### B31.2 Risk Score Parameter Confirmation Planning

Define user confirmation for variables, coefficients, formula, scaling, missingness, cutoff policy, and validation plan. Still no execution.

### B31.3 Risk Score Result Schema Planning

Define the future result schema and explicitly require validation status, provenance, dependency snapshot, and blocked clinical interpretation.

### B31.4 Nomogram / Calibration Renderer Planning

Plan renderer dependencies and artifact contracts. No SVG/PNG/PDF generation yet.

### B31.5 Controlled Risk Score Execution MVP

Only after B31.1-B31.4 pass, consider a controlled MVP that computes a score table. It must not label patients clinically and must not provide treatment recommendations.

### B31.6 Risk Score Review / Report Section Gate

Only after controlled execution and validation, define review UI and section-only report package. Full integrated report inclusion requires a separate content prerequisite gate.

## Test Plan For B31.1

Minimum tests:

```text
git diff --check
python3 -m pytest -q tests/bioinformatics/test_risk_score_design_audit.py
python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py
python3 -m pytest tests/bioinformatics -q -k "risk_score or cox_multivariate or survival_clinical or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "survival or cox or risk or analysis_task"
python3 -m app.main --smoke-test
```

Package/open-W/codesign should run when B31 changes UI/runtime code.

## B31.0 Verification

Commands run for this planning stage:

- `git status --short`
- `git diff --check`
- `python3 -m pytest -q tests/bioinformatics/test_risk_score_design_audit.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`
- `python3 -m app.main --smoke-test`

## Issues

Blocker: none for planning.

Major: none.

Minor: current B21 design audit does not yet distinguish calibration / decision curve / nomogram renderer policy; B31.1 should add those as explicit blocked planning fields.

## Conclusion

B31 should proceed as a contract-first development line. The next implementation stage should be B31.1 Risk Score Source / Contract Gate. Do not implement actual risk score execution or nomogram rendering until the source, parameter, result schema, validation, and clinical-boundary gates are explicit and tested.
