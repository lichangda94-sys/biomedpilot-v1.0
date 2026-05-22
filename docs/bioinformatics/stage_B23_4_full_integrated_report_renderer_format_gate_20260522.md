# Bioinformatics B23.4 Full Integrated Report Renderer Format Gate

Date: 2026-05-22

## Scope

B23.4 separates full integrated report export format readiness from the full integrated report content gate.

The stage adds an explicit renderer capability gate for:

- Markdown
- PDF
- DOCX

This is not full integrated report activation. The full integrated report remains blocked until all section report-ready gates, including survival/clinical report-ready, are implemented and pass.

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_integrated_report_renderer_gate.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B23_4_full_integrated_report_renderer_format_gate_20260522.md`

## Renderer Gate

New API:

- `evaluate_full_integrated_report_renderer_gate(export_format)`

Gate fields include:

- `schema_version`
- `created_at`
- `status`
- `export_format`
- `requested_format`
- `renderer_id`
- `required_dependencies`
- `detected_dependencies`
- `checks`
- `disabled_reason`
- `blockers`
- `warnings`

Renderer behavior:

| Format | Renderer | Status in B23.4 | Boundary |
| --- | --- | --- | --- |
| Markdown | `builtin_markdown` | Passed | Can be used only if the full integrated report content gate also passes. |
| PDF | `pandoc_pdf` | Blocked | Detects `pandoc` and `xelatex` or `wkhtmltopdf`, but PDF rendering is not enabled in B23.4. |
| DOCX | `pandoc_docx` | Blocked | Detects `pandoc`, but DOCX rendering is not enabled in B23.4. |

Detection is detect-first only. No install action is exposed or executed.

## Package Plan Integration

`build_full_integrated_report_package_plan` now includes:

- `renderer_gate`
- `renderer_status`
- `renderer_id`
- `renderer_disabled_reason`
- `renderer_dependencies`
- `disabled_reasons`

`can_create_package` is now the conjunction of:

- full integrated report content gate passed
- renderer gate passed

`create_full_integrated_report_package` now returns the renderer gate in blocked and created package responses.

## UI Integration

The Results Browser full integrated report preview now displays renderer details in the package plan table:

- renderer status
- renderer id
- renderer dependencies
- renderer disabled reason

When PDF or DOCX is selected, the disabled reason is shown through the same user-visible full integrated report status label instead of being hidden behind a generic format block.

## Preserved Boundaries

- No PDF renderer is invoked.
- No DOCX renderer is invoked.
- No full integrated package is generated while the content gate is blocked.
- No survival/clinical report-ready gate is created in this stage.
- No GSEA, survival, clinical statistics, or risk-score capability is expanded.
- No clinical diagnosis, prognosis, treatment recommendation, or risk interpretation is generated.
- Imported/testing/exploratory/preflight results remain excluded from formal integrated reports.

## Validation

Focused validation completed:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/workflow_pages.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_integrated_report_package.py -q`
  - 9 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "formal_deg_report_ready_package_gate"`
  - 1 passed, 111 deselected

Full validation is recorded in the final completion report.

Full validation completed:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or formal_deg or ora or gsea or survival or cox or plot or analysis_ui or capability_map"`
  - 252 passed, 390 deselected
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task"`
  - 16 passed, 96 deselected
- `python3 -m pytest tests/bioinformatics -q`
  - 642 passed
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

B23.4 makes export renderer readiness a first-class, auditable gate. Markdown remains the only implemented renderer path, PDF/DOCX remain disabled with explicit detect-first reasons, and no full integrated report export is activated while the content gate remains blocked.
