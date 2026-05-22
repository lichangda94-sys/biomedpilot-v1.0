# Bioinformatics B24.5 Controlled DOCX Conversion Activation Gate

Date: 2026-05-22

## Scope

B24.5 activates a controlled backend path for full integrated DOCX rendering only when user/system Pandoc is detected and the existing full integrated markdown package passes DOCX preflight.

This stage does not enable PDF, does not bundle or install Pandoc, does not change markdown-only full integrated package behavior, and does not make DOCX a result index v2 `formal_computed_result`.

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/bioinformatics/test_integrated_report_renderer_gate.py`
- `docs/bioinformatics/stage_B24_5_controlled_docx_conversion_activation_gate_20260522.md`

## Activation Gate

Default DOCX renderer behavior remains blocked:

- `evaluate_full_integrated_report_renderer_gate("docx")` still returns blocked with `full_integrated_docx_renderer_not_enabled_in_b23_4`.
- Existing UI/package planning calls continue to see DOCX as disabled unless an explicit backend activation call requests it.

Controlled activation requires:

- `allow_docx_activation=True`
- Pandoc detected on the renderer search path
- no auto-install and no download
- full integrated source package exists
- source package is markdown export
- source full integrated gate is passed
- `integrated_report.md` exists and is non-empty
- local markdown references resolve
- forbidden clinical conclusion terms are absent

If any gate fails, the operation records a blocked/failed attempt and does not create DOCX.

## New API

New API:

- `create_full_integrated_docx_rendered_export(package_path, command_finder=None, runner=None, timeout_seconds=60)`

Behavior:

- evaluates the DOCX renderer gate with explicit activation requested
- evaluates the DOCX preflight gate without the old B24.2 activation blocker
- invokes Pandoc only after both gates pass
- writes conversion logs under `logs/`
- writes DOCX output under `exports/`
- writes/updates `manifests/rendered_exports.json`
- updates `integrated_report_package_manifest.json` rendered export summary
- preserves the markdown package
- preserves existing successful exports
- does not write to result index v2

## Success Registration

Successful DOCX conversion registers a package artifact:

- `artifact_type=full_integrated_report_rendered_export`
- `export_format=docx`
- `renderer_id=pandoc_docx`
- `renderer_dependency_snapshot`
- `output_path`
- `conversion_log_path`
- `validation_status=passed`

The artifact is a rendered package export only. It is not an analysis result, not a formal computation result, and not a clinical report-ready bypass.

## Failure / Rollback

Failure handling:

- Pandoc exception, non-zero exit code, missing output, or empty output marks the attempt failed.
- Temporary DOCX output is removed.
- Final output path is not written.
- Markdown package remains intact.
- `manifests/rendered_exports.json` records the failed attempt.
- conversion log records command, exit code, stdout/stderr tail, duration, failure reason, and preflight state.

Missing Pandoc remains a graceful blocked state with `renderer_dependency_missing:pandoc`.

## Boundaries

- PDF remains disabled.
- `wkhtmltopdf` remains detect-only and is not a formal PDF backend.
- Pandoc is not bundled, downloaded, or installed.
- DOCX export remains separate from result index v2.
- No GSEA, survival, Cox, DEG, ORA, or plot behavior is changed.
- No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram is generated.
- Markdown-only full integrated report package behavior remains unchanged.

## Validation

Focused validation before full regression:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py`
  - passed
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py`
  - passed, `19 passed`

Full validation is recorded in the completion response.

Full validation:

- `git diff --check`
  - passed
- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py scripts/package_app.py`
  - passed
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py tests/test_package_app.py`
  - passed, `30 passed`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"`
  - passed, `108 passed, 558 deselected`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or settings"`
  - passed, `12 passed, 102 deselected`
- `python3 -m pytest tests/bioinformatics -q`
  - passed, `666 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - passed, `271 passed`
- `python3 -m app.main --smoke-test`
  - passed, source smoke
- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_source_b24_5.json`
  - passed, `status=passed`, `environment=source`, `architecture=arm64`, `pandoc.available=false`
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_packaged_b24_5.json`
  - passed, `status=passed`, `environment=packaged_app_resource`, `architecture=arm64`, `pandoc.available=false`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_openw_b24_5.json`
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

This is expected under the external-system-runtime policy. Real DOCX conversion remains blocked in this environment until user/system Pandoc is installed.

## Conclusion

B24.5 provides the controlled DOCX conversion activation gate for environments where user/system Pandoc is already installed. The default product surface remains conservative: DOCX stays disabled unless explicitly activated through the gated backend path, and PDF remains blocked.
