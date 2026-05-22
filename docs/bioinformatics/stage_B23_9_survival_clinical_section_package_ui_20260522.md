# Bioinformatics B23.9 Survival / Clinical Section Package UI

Date: 2026-05-22

## Scope

B23.9 wires the B23.7/B23.8 KM/log-rank and Cox univariate section package gates into the Analysis Center state and Results Browser UI.

This stage does not enable full integrated report export. KM/Cox packages remain section-only and do not generate clinical diagnosis, prognosis, treatment recommendation, or validated risk score output.

## Implemented Files

- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## Analysis Center Changes

- Adds KM/log-rank and Cox section report-ready gates to Analysis Center state.
- Adds survival/clinical report gate rows to diagnostics and gate previews.
- Updates `survival_report_ready` action from a constant disabled placeholder to a gate-driven section-only export action.
- Keeps full integrated survival/clinical reporting blocked.

## Results Browser Changes

New UI controls:

- `kmReportReadyButton`
- `kmReportReadyStatus`
- `coxReportReadyButton`
- `coxReportReadyStatus`
- `survivalClinicalReportGateTable`
- `kmTableOnlyReportMode`
- `coxTableOnlyReportMode`

The buttons are enabled only when the corresponding section gate reaches:

- `eligible_for_km_logrank_report_ready`
- `eligible_for_cox_report_ready`

Generated packages remain under:

- `survival_clinical_report_package/survival_km_logrank_only/`
- `survival_clinical_report_package/cox_univariate_only/`

## Preserved Boundaries

- No full integrated report export is enabled.
- Section-only packages do not satisfy full integrated report prerequisites.
- No Cox multivariate report package is enabled.
- No risk score, prognosis label, treatment recommendation, or clinical conclusion is generated.
- No imported/testing/exploratory/preflight result can be upgraded into a formal survival/clinical section package.
- No dependency installation action is added.

## Validation

Focused validation completed:

- `python3 -m pytest tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_survival_clinical_report_ready_gate.py -q`
  - 30 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser_survival or analysis_task or report"`
  - 14 passed, 99 deselected

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "survival_clinical_report_ready or integrated or report or km or cox or survival or clinical or plot or analysis_ui"`
  - 208 passed, 444 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task or survival or cox"`
  - 17 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 652 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 270 passed
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Conclusion

B23.9 makes KM/log-rank and Cox univariate section-only package readiness visible and actionable in the UI while preserving the full integrated report gate.
