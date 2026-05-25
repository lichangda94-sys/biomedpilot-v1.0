# Bioinformatics B30.4 PDF Rendered Export UX / Package Acceptance Audit

Date: 2026-05-25

## Scope

B30.4 audits the user-facing PDF rendered export flow introduced in B30.3 and validates it against the controlled B30.2 Pandoc + XeLaTeX backend.

This stage does not expand report semantics. PDF remains a rendered copy of an existing full integrated markdown report package.

## Acceptance Checklist

| Area | Result | Evidence |
| --- | --- | --- |
| UI entry point | Passed | Results Browser exposes `fullIntegratedPdfRenderedExportButton`. |
| Disabled reason visibility | Passed | Plan table shows `pdf_rendered_export_disabled_reason`. |
| Source package visibility | Passed | Plan table shows `pdf_rendered_export_source_package`. |
| Backend clarity | Passed | Plan table shows `pdf_rendered_export_renderer=pandoc_pdf` and `pdf_rendered_export_backend=pandoc_xelatex`. |
| Package artifact boundary | Passed | UI/action copy states no `result_index_v2` write and no `formal_computed_result`. |
| Real renderer execution | Passed | UI-level real environment test generates a PDF through Pandoc + XeLaTeX when the gate passes. |
| PDF file validation | Passed | Test verifies the generated file exists and starts with `%PDF`. |
| Manifest registration | Passed | `manifests/rendered_exports.json` records the PDF export artifact with `validation_status=passed`. |
| Package manifest update | Passed | `integrated_report_package_manifest.json` records `rendered_exports_summary.pdf_conversion_enabled=true`. |
| Temporary output cleanup | Passed | Test verifies no `.tmp/*.pdf` remains after successful conversion. |
| Clinical boundary | Passed | UI status copy excludes diagnosis, prognosis, risk score, and treatment advice. |
| `wkhtmltopdf` boundary | Passed | UI and gate continue to mark `wkhtmltopdf` as detect-only and not selected. |

## Real UI Acceptance Test

B30.4 adds a UI-level real environment test:

- `test_results_browser_pdf_rendered_export_real_environment_registers_package_artifact`

The test:

1. Evaluates the real PDF renderer gate with `allow_pdf_activation=True`.
2. Skips only if Pandoc + XeLaTeX are unavailable.
3. Creates a controlled full integrated markdown package fixture.
4. Refreshes the Results Browser.
5. Verifies the PDF button is enabled.
6. Invokes `generate_full_integrated_pdf_rendered_export()`.
7. Validates the generated PDF file header.
8. Validates rendered export manifest registration.
9. Validates package manifest summary update.
10. Verifies temporary PDF files are not left behind.

## Boundaries Preserved

- No `result_index_v2` write.
- No `formal_computed_result` marking.
- No PDF report-ready semantics beyond the existing full integrated markdown package.
- No GSEA, survival, clinical conclusion, risk score, or treatment recommendation activation.
- No automatic installation of Pandoc, XeLaTeX, TeX, or `wkhtmltopdf`.
- No bundled renderer binaries inside the `.app`.

## Verification Commands

Run during implementation:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k 'pdf_rendered_export_real_environment'`
- `git diff --check`
- `python3 -m py_compile app/bioinformatics/workflow_pages.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/state.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k 'report or integrated or renderer or pdf'`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k 'pdf'`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer or analysis_ui"`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_4_openw_renderer.json`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

## Issues

Blocker: none.

Major: none.

Minor: none.

## Conclusion

B30.4 passes. The PDF rendered export UX is acceptable for ReleaseBuild candidate use as a package artifact flow. It is not a formal analytical result and does not unlock clinical conclusions, risk score, GSEA, survival, or additional report semantics.
