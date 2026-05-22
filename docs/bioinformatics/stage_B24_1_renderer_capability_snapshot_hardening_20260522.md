# Bioinformatics B24.1 Renderer Capability Snapshot Hardening

Date: 2026-05-22

## Scope

B24.1 makes full integrated report renderer detection reusable and auditable across source, packaged executable, and open-W runtime contexts.

This stage does not enable PDF export, DOCX export, Quarto export, clinical conclusions, risk score, nomogram, legacy formal execution, or any new analysis engine.

## Implemented Files

- `app/bioinformatics/reports/renderer_capability.py`
- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/main.py`
- `tests/bioinformatics/test_report_renderer_capability.py`
- `tests/bioinformatics/test_integrated_report_renderer_gate.py`
- `tests/bioinformatics/test_analysis_ui_state.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B24_1_renderer_capability_snapshot_hardening_20260522.md`

## Capability Snapshot

New API:

- `build_report_renderer_capability_snapshot(...)`
- `detect_renderer_dependency(command)`

Snapshot fields:

- `schema_version`
- `created_at`
- `status`
- `environment`
- `python_executable`
- `platform`
- `capabilities`
- `capability_keys`
- `packaging_impact`
- `checks`
- `blockers`
- `warnings`

Commands detected:

- `pandoc`
- `xelatex`
- `wkhtmltopdf`
- `quarto`

Detection policy:

- detect first
- no install action
- no renderer invocation
- no report export enabled
- missing dependency returns blockers and missing reasons, not traceback

## Integrated Report Gate Wiring

`evaluate_full_integrated_report_renderer_gate(export_format)` now consumes the reusable capability snapshot instead of doing direct local detection.

Preserved behavior:

- markdown passes with `renderer_id=builtin_markdown`
- PDF remains blocked with `full_integrated_pdf_renderer_not_enabled_in_b23_4`
- DOCX remains blocked with `full_integrated_docx_renderer_not_enabled_in_b23_4`
- unsupported formats are blocked without traceback
- dependency detection is still surfaced through `detected_dependencies`

New behavior:

- renderer gate includes `renderer_capability_snapshot`
- detected dependencies include packaging impact fields
- Settings/Analysis Center can reuse the same snapshot model

## CLI Runtime Check

New runtime check:

```bash
python3 -m app.main --bio-report-renderer-runtime-check
python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime.json
```

The command prints a JSON capability snapshot and exits successfully when detection completes, even if optional external renderer binaries are missing.

This command does not:

- install renderer dependencies
- invoke Pandoc/Quarto conversion
- create PDF/DOCX files
- mark PDF/DOCX as enabled

## UI Visibility

Analysis Center and Settings dependency rows now include report renderer capabilities:

- Pandoc report renderer
- XeLaTeX PDF backend
- wkhtmltopdf PDF backend
- Quarto report renderer

Each row exposes:

- installed/missing status
- version when detected
- disabled/missing reason
- packaging impact
- detect-only action text
- explicit PDF/DOCX disabled wording

Renderer dependency rows are visible dependency status rows. They do not become global analysis blockers and do not enable PDF/DOCX export.

## Preserved Boundaries

- Markdown-only full integrated report behavior is unchanged.
- PDF/DOCX are not enabled by dependency detection.
- Quarto remains future-planned.
- Renderer artifacts are not registered yet.
- No analysis result semantics change.
- No `report_ready_eligible` change.
- Imported/testing/exploratory/preflight results remain excluded from full integrated reports.
- No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram is generated.

## Validation

Focused validation:

- `python3 -m pytest tests/bioinformatics/test_report_renderer_capability.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_analysis_ui_state.py -q`
  - passed, `19 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or settings"`
  - passed, `12 passed, 102 deselected`

Runtime renderer checks:

- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_source.json`
  - passed, `status=passed`, `environment=source`
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_packaged.json`
  - passed, `status=passed`, `environment=packaged_app_resource`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_openw.json`
  - passed, `status=passed`, `environment=packaged_app_resource`

Current renderer dependency status in this environment:

- `pandoc`: missing, `pandoc_not_found_on_path`
- `xelatex`: missing, `xelatex_not_found_on_path`
- `wkhtmltopdf`: missing, `wkhtmltopdf_not_found_on_path`
- `quarto`: missing, `quarto_not_found_on_path`

Expected renderer blockers are graceful and non-fatal:

- `renderer_dependency_missing:pandoc`
- `renderer_dependency_missing:xelatex_or_wkhtmltopdf`

Regression validation:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"`
  - passed, `98 passed, 558 deselected`
- `python3 -m pytest tests/bioinformatics -q`
  - passed, `656 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - passed, `271 passed`
- `python3 -m app.main --smoke-test`
  - passed
- `python3 scripts/package_app.py --smoke-test`
  - passed, ad-hoc signed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Blockers / Risks

### Blocker

- None.

### Major

- Renderer conversion output registration is still not implemented.
- PDF/DOCX activation still requires dedicated preflight gates and package artifact validation.

### Minor

- Quarto detection is included for future planning but is not used by the current renderer gate.

## Conclusion

B24.1 completes renderer capability snapshot hardening. The application can now audit renderer availability in source and packaged contexts without enabling PDF/DOCX export.

Recommended next step: **B24.2 DOCX Renderer Preflight Gate**, still initially disabled until explicit activation criteria and output registration are implemented.
