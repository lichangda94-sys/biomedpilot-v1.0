# Bioinformatics B23.12 Full Integrated Report UX / Acceptance Audit

Date: 2026-05-22

## Scope

B23.12 audits and hardens the user-visible full integrated report export UX after B23.11 enabled markdown-only export when all section prerequisites pass.

This stage does not expand the report content model. It only makes gate state, renderer capability, section provenance, output path, and limitations clearer in the Results Browser.

## Implemented Files

- `app/bioinformatics/workflow_pages.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B23_12_full_integrated_report_ux_acceptance_audit_20260522.md`

## UX Acceptance Criteria

The Results Browser now shows:

- `markdown-only package can be created` when the full integrated gate passes
- `PDF/DOCX disabled` in the enabled status copy
- `export_activation_status`
- `enabled_export_formats`
- `disabled_export_formats`
- renderer status, renderer id, renderer disabled reason, and renderer dependencies
- section package validation status for each section
- limitations, including no clinical diagnosis/prognosis/treatment advice
- output path after package creation

The section table now includes a `Package` column so survival/clinical section package validation is visible next to report gate and prerequisite status.

## Export UX

On successful package creation, the status text says:

- package is markdown full integrated report
- output path is visible
- package contains only gate-passed statistical research sections
- PDF/DOCX remain disabled
- no clinical diagnosis, prognosis, risk score, or treatment advice is generated

## Preserved Boundaries

- PDF/DOCX remain renderer-disabled.
- No clinical conclusion, prognosis, treatment recommendation, risk score, or nomogram is generated.
- Section provenance remains visible through result id, semantics, validation, report gate, plot status, package validation, prerequisite status, and blockers.
- Full integrated report still requires all DEG/ORA/GSEA/KM/Cox prerequisites.
- Imported/testing/exploratory/preflight sources remain excluded by the backend gate.

## Validation

Focused validation completed:

- `python3 -m pytest tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_gate.py -q`
  - 10 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "full_integrated_markdown_ux or formal_deg_report_ready_package_gate or results_browser_survival"`
  - 3 passed, 111 deselected

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or survival_clinical_report_ready or km or cox or survival or clinical or analysis_ui"`
  - 187 passed, 466 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task or survival or cox"`
  - 18 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 653 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 271 passed
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Conclusion

B23.12 makes the full integrated report UX explicit enough for user acceptance: users can see why export is enabled or disabled, which format is available, why PDF/DOCX are unavailable, where the package was written, and which section prerequisites were satisfied.
