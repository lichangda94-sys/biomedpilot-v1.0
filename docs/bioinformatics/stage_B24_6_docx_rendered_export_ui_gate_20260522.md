# Bioinformatics B24.6 DOCX Rendered Export UI Gate

Date: 2026-05-22

## Scope

B24.6 connects the B24.5 controlled DOCX rendered export backend to the Bioinformatics UI gate surface.

The UI now treats DOCX as a rendered copy of an existing full integrated markdown package. It is not a new analysis result, does not write result index v2, does not set `formal_computed_result`, and does not unlock PDF.

## Implemented Files

- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/bioinformatics/test_analysis_ui_action_rules.py`
- `docs/bioinformatics/stage_B24_6_docx_rendered_export_ui_gate_20260522.md`

## UI Behavior

Full integrated report preview now shows:

- markdown package eligibility
- renderer status
- DOCX rendered export status
- source markdown package path
- Pandoc missing reason / disabled reason
- output policy: package artifact only, no result index v2 write, no `formal_computed_result`

The DOCX rendered export button is enabled only when:

- a full integrated markdown package already exists
- the source package manifest is valid
- `integrated_report.md` exists and passes preflight
- user/system Pandoc is detected by the detect-first renderer gate
- no DOCX preflight blockers exist

If Pandoc is missing, the UI shows `renderer_dependency_missing:pandoc` and remains blocked. No install or download action is offered.

## Analysis Center

Analysis Center action matrix now includes:

- `full_integrated_docx_rendered_export`
- label: `Export DOCX rendered copy`
- enabled state only after the DOCX rendered export gate passes
- disabled reasons for missing markdown package or missing Pandoc

Gate preview now includes `DOCX rendered export` with explicit warning that the output is a package artifact only and never a result index v2 formal result.

## Boundaries

- Markdown full integrated package remains the primary export path.
- DOCX rendering requires an existing markdown package.
- PDF remains disabled.
- Pandoc is user/system runtime only; ReleaseBuild does not bundle, download, or install it.
- DOCX rendered export does not write `result_index_v2`.
- DOCX rendered export does not create `formal_computed_result`.
- No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram is generated.

## Validation

Focused validation before full regression:

- `python3 -m py_compile app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/workflow_pages.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py -q`
  - passed, `22 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "full_integrated or docx or report or settings"`
  - passed, `11 passed, 105 deselected`

Full validation is recorded in the completion response.

Full validation:

- `git diff --check`
  - passed
- `python3 -m py_compile app/bioinformatics/analysis_ui/state.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/workflow_pages.py`
  - passed
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py`
  - passed, `41 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "full_integrated or docx or report or settings"`
  - passed, `11 passed, 105 deselected`
- `python3 -m pytest tests/bioinformatics -q`
  - passed, `667 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - passed, `273 passed`
- `python3 -m app.main --smoke-test`
  - passed
- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_source_b24_6.json`
  - passed, `status=passed`, `environment=source`, `architecture=arm64`, `pandoc.available=false`
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_packaged_b24_6.json`
  - passed, `status=passed`, `environment=packaged_app_resource`, `architecture=arm64`, `pandoc.available=false`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_openw_b24_6.json`
  - passed, `status=passed`, `environment=packaged_app_resource`, `architecture=arm64`, `pandoc.available=false`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

Current renderer dependency result:

- `pandoc`: not available on renderer search paths
- `xelatex`: not available on renderer search paths
- `wkhtmltopdf`: not available on renderer search paths
- `quarto`: not available on renderer search paths

This is expected under the external-system-runtime policy. The UI remains graceful blocked for DOCX in this environment.

## Conclusion

B24.6 makes DOCX export understandable and auditable in the UI without changing the formal analysis boundary. Users can see why DOCX is disabled, and when Pandoc is present they can create a package-level DOCX rendered export from an existing full integrated markdown package.
