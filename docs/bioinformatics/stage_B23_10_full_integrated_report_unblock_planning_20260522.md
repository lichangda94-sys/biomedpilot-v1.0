# Bioinformatics B23.10 Full Integrated Report Unblock Planning

Date: 2026-05-22

## Scope

B23.10 defines and implements the gate conditions under which KM/log-rank and Cox univariate section-only packages may satisfy the survival/clinical prerequisites for a future full integrated report.

This stage does not enable full integrated report export. It only upgrades validated survival/clinical section packages from "section-only output" to "eligible full integrated section prerequisite".

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `tests/bioinformatics/test_integrated_report_gate.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/bioinformatics/test_survival_clinical_report_ready_gate.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B23_10_full_integrated_report_unblock_planning_20260522.md`

## Section Package Prerequisite Policy

KM/log-rank and Cox section-only packages can satisfy full integrated section prerequisites only when all checks pass:

- source result is `formal_computed_result`
- source result has result index v2 fields, passed validation, passed dependency snapshot, source table, and task-run log
- section report-ready gate passes
- result index contains a matching `report_artifacts` entry
- report artifact has the expected section scope:
  - `survival_km_logrank_only`
  - `cox_univariate_only`
- report package manifest exists on disk
- package directory exists and has stable directories:
  - `tables/`
  - `plots/`
  - `manifests/`
  - `logs/`
  - `provenance/`
- required package files exist:
  - section markdown
  - `README_limitations.md`
  - gate snapshot
  - result index snapshot
  - source result entry
  - parameters manifest
  - dependency snapshot
  - table validation
  - plot artifacts manifest
  - warnings/limitations
  - package inventory
  - provenance
- package manifest source result id matches the selected source result
- `clinical_conclusion_enabled=False`
- `full_integrated_report_enabled=False`
- forbidden semantics policy includes imported/testing/exploratory/preflight exclusions

## Gate Changes

The full integrated gate now records survival/clinical section package validation in each prerequisite row:

- `section_package_validation_status`
- `section_only_package_sufficient`

If KM/Cox packages pass validation:

- `survival_clinical_report_ready_available=True`
- survival/clinical prerequisite rows can pass
- section-only KM/Cox scopes are no longer rejected by `full_integrated_prerequisite_forbids_section_package_as_full_report`

If a package is missing or invalid, the full integrated gate blocks with:

- `full_integrated_prerequisite_survival_clinical_section_package_not_passed:<section>`
- package-specific blockers such as missing manifest, missing required file, scope mismatch, or source result mismatch

## Preserved Blockers

Full integrated report export remains disabled by:

- `full_integrated_report_export_not_enabled_in_b23_1`

B23.10 does not enable:

- full integrated report package creation from real gate pass
- clinical diagnosis/prognosis/treatment recommendation
- risk score or nomogram
- imported/testing/exploratory/preflight result upgrade
- dependency auto-install

## Validation

Focused validation completed:

- `python3 -m pytest tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_survival_clinical_report_ready_gate.py tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q`
  - 39 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "results_browser_survival or formal_deg_report_ready_package_gate or analysis_task"`
  - 9 passed, 104 deselected

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or survival_clinical_report_ready or km or cox or survival or clinical or analysis_ui"`
  - 186 passed, 466 deselected
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

B23.10 removes the blanket "survival/clinical report-ready not implemented" prerequisite blocker and replaces it with auditable KM/Cox section package validation. Validated section-only packages can now satisfy survival/clinical section prerequisites, while full integrated report export remains gated off.
