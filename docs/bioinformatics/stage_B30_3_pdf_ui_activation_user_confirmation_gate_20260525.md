# Bioinformatics B30.3 PDF UI Activation / User Confirmation Gate

Date: 2026-05-25

## Scope

B30.3 connects the controlled B30.2 PDF rendered export capability to the Analysis Center and Results Browser UI.

This stage is UI activation for a package artifact only. It does not make PDF a formal analytical result, does not write `result_index_v2`, and does not change DEG / ORA / GSEA / survival / clinical execution semantics.

## Implemented UI Gate

The Analysis Center state builder now evaluates a dedicated `biomedpilot.full_integrated_pdf_rendered_export_ui_gate.v1` gate.

Required checks:

- Existing full integrated markdown package is present.
- Renderer gate passes for `export_format=pdf` with explicit PDF activation.
- `pandoc` is detected.
- `xelatex` is detected.
- PDF preflight gate passes with the B30.1 activation blocker excluded because B30.2 has activated the controlled backend.
- `wkhtmltopdf` remains detect-only and is not selected.
- The export is package-artifact-only and records `writes_result_index_v2=false`.

Blocked examples:

- `full_integrated_markdown_package_missing`
- `renderer_dependency_missing:pandoc`
- `renderer_dependency_missing:xelatex`
- PDF preflight blockers from the full integrated report package.

## Action Matrix

Added action row:

- `action_id=full_integrated_pdf_rendered_export`
- label: `Export PDF rendered copy`
- enabled only when the PDF rendered export gate status is `passed`
- button behavior: `enabled_pdf_rendered_export_package_artifact_only`
- disabled state: `blocked_pdf_rendered_export_gate`

The action copy states that the UI renders an existing markdown package to PDF with user/system Pandoc + XeLaTeX, and does not write `result_index_v2` or mark `formal_computed_result`.

## Results Browser

The full integrated report panel now shows separate DOCX and PDF rendered export gates.

Added button:

- `fullIntegratedPdfRenderedExportButton`
- label: `生成 PDF rendered export`
- enabled only when the PDF rendered export UI gate passes

The report plan table now includes:

- `pdf_rendered_export_status`
- `pdf_rendered_export_source_package`
- `pdf_rendered_export_renderer`
- `pdf_rendered_export_backend`
- `pdf_rendered_export_disabled_reason`
- `pdf_rendered_export_output_policy`

On success the status message reports the PDF output path and explicitly states that the file is a rendered copy of the full integrated markdown package, not a result-index entry and not a `formal_computed_result`.

## Boundaries Preserved

- No `result_index_v2` write for PDF rendered exports.
- No formal result semantics upgrade.
- No clinical diagnosis, prognosis, risk score, or treatment advice.
- No GSEA, survival, or clinical analysis activation.
- No `wkhtmltopdf` formal backend activation.
- No automatic renderer installation.

## Test Coverage

Added or updated tests for:

- Analysis UI action row enabled/blocked behavior.
- Analysis Center state diagnostics and gate preview rows.
- Results Browser PDF button disabled reason when XeLaTeX is missing.
- Results Browser PDF button enablement and success message when the gate passes.
- Existing full integrated markdown UX copy after DOCX/PDF rendered export gate separation.

## Verification

Focused checks run during implementation:

- `python3 -m py_compile app/bioinformatics/workflow_pages.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/state.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k 'report or integrated or renderer or pdf'`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k 'pdf'`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer or analysis_ui"`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_3_openw_renderer.json`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Observed renderer runtime after package/open-W:

- `pandoc.available=true`, path `/opt/homebrew/bin/pandoc`, version `pandoc 3.9.0.2`
- `xelatex.available=true`, path `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, version `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)`
- `wkhtmltopdf.available=false`, detect-only and not selected
- blockers: `[]`
- app size: `34M`
- bundle scan found no bundled `pandoc`, `xelatex`, `wkhtmltopdf`, or `tlmgr`

## Conclusion

B30.3 is ready for broader renderer/report regression testing. PDF rendered export is now visible and controlled in the UI, but remains a rendered package artifact only.
