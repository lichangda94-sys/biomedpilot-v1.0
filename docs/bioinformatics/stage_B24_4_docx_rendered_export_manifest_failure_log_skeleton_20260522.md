# Bioinformatics B24.4 DOCX Rendered Export Manifest / Failure Log Skeleton

Date: 2026-05-22

## Scope

B24.4 implements the DOCX rendered export manifest skeleton and conversion failure log writer behind the disabled DOCX activation gate.

This stage does not invoke Pandoc, does not create a `.docx` file, does not enable the user-visible DOCX export button, and does not mark any rendered export as passed.

This stage also scoped-carries the integration renderer runtime packaging policy from `c67bd48` without merging unrelated source-tree deletions or UI work.

## Implemented Files

- `app/bioinformatics/reports/renderer_runtime_policy.py`
- `app/bioinformatics/reports/renderer_capability.py`
- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `scripts/package_app.py`
- `tests/bioinformatics/test_report_renderer_capability.py`
- `tests/bioinformatics/test_integrated_report_renderer_gate.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/test_package_app.py`
- `docs/bioinformatics/stage_B24_3_renderer_runtime_packaging_policy_20260522.md`
- `docs/bioinformatics/stage_B24_4_docx_rendered_export_manifest_failure_log_skeleton_20260522.md`

## Runtime Policy Carry-over

ReleaseBuild renderer runtime policy now records:

- no bundled Pandoc / TeX / wkhtmltopdf / Quarto
- no downloads
- no auto-install
- no third-party renderer binaries in app codesign scope
- DOCX runtime provider is user/system Pandoc on renderer search path
- PDF remains disabled; future backend is Pandoc + `xelatex`
- `wkhtmltopdf` remains detect-only, not formal full integrated PDF backend

Packaged launcher now exports:

- `BIOMEDPILOT_EXTERNAL_RENDERER_POLICY`
- `BIOMEDPILOT_RENDERER_SEARCH_PATHS`
- renderer search paths prepended to `PATH`

Packaged `BUILD_INFO.json` includes `renderer_runtime_packaging_policy`.

## B24.4 API

New API:

- `create_full_integrated_docx_rendered_export_skeleton(package_path, renderer_gate=None, failure_reason="full_integrated_docx_conversion_not_enabled_b24_4")`

Behavior:

- runs B24.2 DOCX preflight gate
- reserves a non-overwriting planned `.docx` output path under `exports/`
- writes a conversion log under `logs/`
- writes or updates `manifests/rendered_exports.json`
- appends a blocked attempt
- preserves existing successful rendered exports
- updates `integrated_report_package_manifest.json` with rendered export summary
- does not create `.docx`
- does not invoke Pandoc

## Rendered Export Manifest

Manifest path:

- `manifests/rendered_exports.json`

Manifest schema:

- `schema_version=biomedpilot.full_integrated_rendered_exports.v1`
- `package_scope=full_integrated_report`
- `source_package_id`
- `source_package_path`
- `exports`
- `attempts`
- `latest_attempt_status`
- `latest_attempt_log_path`
- policy flags

Policy flags:

- rendered exports are package artifacts, not analysis results
- do not write `formal_computed_result`
- DOCX conversion disabled
- PDF conversion disabled

B24.4 only writes blocked attempts. `exports` stays empty unless a future activation stage validates a real rendered file.

## Conversion Log

Log schema:

- `schema_version=biomedpilot.full_integrated_docx_conversion_log.v1`
- `created_at`
- `source_package_path`
- `source_markdown_path`
- `requested_export_format=docx`
- `renderer_id=pandoc_docx`
- `renderer_command`
- `renderer_version`
- `environment`
- `working_directory`
- `output_path`
- `exit_code`
- `stdout_tail`
- `stderr_tail`
- `duration_ms`
- `status`
- `failure_reason`
- `preflight_status`
- `preflight_blockers`
- `conversion_invoked=false`
- `temporary_output_removed=true`
- `markdown_package_preserved=true`

## Rollback / Preservation Behavior

B24.4 is safe to run on an existing full integrated markdown package:

- markdown package remains intact
- no temp DOCX is left behind
- no final DOCX is written
- existing passed exports remain in `exports`
- failed/blocked attempts are recorded separately
- package manifest is updated only with rendered export summary and manifest path

## Boundaries

- DOCX export remains disabled.
- PDF export remains disabled.
- Pandoc is not invoked.
- No `.docx` file is created.
- No rendered export is registered as passed.
- No result index v2 formal result is created.
- Result semantics are unchanged.
- `report_ready_eligible` is unchanged.
- No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram.

## Validation

Focused validation before full regression:

- `python3 -m pytest -q tests/bioinformatics/test_report_renderer_capability.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_integrated_report_package.py tests/test_package_app.py`
  - passed, `26 passed`

Full validation is recorded in the completion response.

Full validation:

- `git diff --check`
  - passed
- `python3 -m py_compile app/bioinformatics/reports/renderer_runtime_policy.py app/bioinformatics/reports/renderer_capability.py app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py scripts/package_app.py`
  - passed
- `python3 -m pytest -q tests/bioinformatics/test_report_renderer_capability.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_integrated_report_package.py tests/test_package_app.py`
  - passed, `26 passed`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"`
  - passed, `104 passed, 558 deselected`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or settings"`
  - passed, `12 passed, 102 deselected`
- `python3 -m pytest -q tests/test_package_app.py`
  - passed, `7 passed`
- `python3 -m pytest tests/bioinformatics -q`
  - passed, `662 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - passed, `271 passed`
- `python3 -m app.main --smoke-test`
  - passed
- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_source_b24_4.json`
  - passed, `status=passed`, policy `b24_3_system_path_no_bundled_renderers`
- `python3 scripts/package_app.py --smoke-test`
  - passed, packaged `BUILD_INFO.json` includes renderer runtime policy
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_packaged_b24_4.json`
  - passed, `status=passed`, policy `b24_3_system_path_no_bundled_renderers`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_openw_b24_4.json`
  - passed, `status=passed`, policy `b24_3_system_path_no_bundled_renderers`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

Current renderer dependency result:

- `pandoc`: not available on renderer search paths
- `xelatex`: not available on renderer search paths
- `wkhtmltopdf`: not available on renderer search paths
- `quarto`: not available on renderer search paths

This is expected and remains graceful blocked under the external-system-runtime policy.

## Conclusion

B24.4 provides the package-safe manifest/log skeleton needed before real DOCX conversion can be activated. The feature remains disabled until a later controlled activation stage validates user/system Pandoc runtime and real conversion output.
