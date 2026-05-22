# Bioinformatics B23.1 Full Integrated Report Gate

Date: 2026-05-22

## Scope

B23.1 implements a full integrated report readiness gate without enabling full integrated report export.

The gate reads the result index and checks coverage for:

- formal DEG
- ORA enrichment
- preranked GSEA
- KM/log-rank
- Cox univariate or Cox multivariate

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/capability_map.py`
- `tests/bioinformatics/test_integrated_report_gate.py`

## Gate Behavior

The B23.1 gate validates each required section for:

- result index entry presence
- expected task type
- `result_semantics=formal_computed_result`
- required v2 result fields
- dependency snapshot passed
- validation status passed or warning
- no result blockers
- task-run log presence
- source table artifact presence
- section report-ready gate status
- no imported/testing/exploratory/preflight sources

The full integrated report gate currently remains blocked by design because survival/clinical report-ready has not been implemented.

Primary B23.1 blockers:

- `survival_clinical_report_ready_not_implemented`
- `full_integrated_report_export_not_enabled_in_b23_1`

## UI Changes

Analysis Center now exposes:

- `Full integrated report` gate preview row.
- `Export full integrated report` action row.
- disabled reason containing `survival_clinical_report_ready_not_implemented`.
- capability map status `b23_gate_blocked`.

Section-only report controls remain separate from the full integrated report action.

## Preserved Boundaries

- No full integrated report package is generated.
- DEG/ORA/GSEA section-only report packages are not re-labeled as full integrated reports.
- KM/Cox formal results and B22 real SVG plot artifacts do not enable survival report-ready.
- Imported/testing/exploratory/preflight results remain blocked from full integrated report.
- No clinical diagnosis, prognosis, treatment recommendation, or validated risk score wording is produced.
- No automatic dependency installation.

## Validation

Focused validation:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/capability_map.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_capability_map.py -q`
  - 26 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task_center_userized_main_surface_and_diagnostics"`
  - 1 passed, 111 deselected

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or formal_deg or ora or gsea or survival or cox or plot or analysis_ui or capability_map"`
  - 243 passed, 390 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 633 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 269 passed
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Conclusion

B23.1 is implemented as a visible, auditable, blocked full integrated report gate. The correct next step is B23.2 full integrated report package skeleton, still blocked until this gate passes.
