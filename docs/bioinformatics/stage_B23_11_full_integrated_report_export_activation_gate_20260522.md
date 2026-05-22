# Bioinformatics B23.11 Full Integrated Report Export Activation Gate

Date: 2026-05-22

## Scope

B23.11 activates the markdown full integrated report export path only after all required section prerequisites pass:

- Formal DEG
- ORA enrichment
- Preranked GSEA
- KM/log-rank survival
- Cox univariate clinical association

This stage does not enable PDF/DOCX export, clinical diagnosis, prognosis, treatment recommendation, risk score, nomogram, or any imported/testing/exploratory/preflight result upgrade.

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `tests/bioinformatics/test_integrated_report_gate.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/bioinformatics/test_survival_clinical_report_ready_gate.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B23_11_full_integrated_report_export_activation_gate_20260522.md`

## Activation Rule

The full integrated report gate reaches `eligible_for_full_integrated_report` only when:

- all five required sections are requested
- all required section results are present
- all section results are `formal_computed_result`
- all section result index v2 fields are present
- all validations pass
- all dependency snapshots pass
- all task-run logs are present
- all source tables are present
- all section report-ready gates pass
- KM/Cox section package integrity validation passes
- no imported/testing/exploratory/preflight source is included

When those checks pass:

- `export_activation_status=eligible_for_markdown_export`
- `enabled_export_formats=["markdown"]`
- `disabled_export_formats=["pdf", "docx"]`
- the old blanket blocker `full_integrated_report_export_not_enabled_in_b23_1` is no longer emitted

When section prerequisites are still incomplete, the gate blocks with:

- `full_integrated_report_export_waiting_for_section_prerequisites`

## Export Output

The markdown package writer remains the existing audited skeleton and writes:

- `integrated_report.md`
- `README_limitations.md`
- `integrated_report_package_manifest.json`
- `sections/`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`

The package uses only registered result index artifacts and keeps warnings, limitations, dependency snapshots, provenance, and result semantics attached.

## Preserved Boundaries

- PDF and DOCX remain blocked by the B23.4 renderer gate.
- Full integrated report remains statistical research reporting only.
- No clinical conclusion, prognosis, treatment recommendation, validated risk score, or nomogram is generated.
- Section-only KM/Cox packages can satisfy section prerequisites only after B23.10 integrity validation passes; they are not re-labeled as full integrated packages.
- Imported/testing/exploratory/preflight results remain forbidden in the full integrated package.

## Validation

Focused validation completed:

- `python3 -m pytest tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_survival_clinical_report_ready_gate.py -q`
  - 19 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "formal_deg_report_ready_package_gate or results_browser_survival or analysis_task"`
  - 9 passed, 104 deselected

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or survival_clinical_report_ready or km or cox or survival or clinical or analysis_ui"`
  - 187 passed, 466 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task or survival or cox"`
  - 17 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 653 passed
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

B23.11 enables markdown-only full integrated report package creation when all DEG/ORA/GSEA/KM/Cox prerequisites pass. The feature remains bounded to statistical research reporting and keeps PDF/DOCX and clinical interpretation disabled.
