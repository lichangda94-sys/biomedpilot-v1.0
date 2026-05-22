# Bioinformatics B24.2 DOCX Renderer Preflight Gate

Date: 2026-05-22

## Scope

B24.2 adds a DOCX renderer preflight gate for full integrated report packages.

This stage validates whether an existing full integrated markdown package is structurally ready for a future DOCX conversion. It does not invoke Pandoc, does not create a `.docx` file, and does not enable user-visible DOCX export.

This stage does not enable PDF export, Quarto export, clinical conclusions, risk score, nomogram, legacy formal execution, or any new analysis engine.

## Implemented Files

- `app/bioinformatics/reports/integrated.py`
- `app/bioinformatics/reports/__init__.py`
- `app/bioinformatics/workflow_pages.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `docs/bioinformatics/stage_B24_2_docx_renderer_preflight_gate_20260522.md`

## DOCX Preflight API

New API:

- `evaluate_full_integrated_docx_preflight_gate(package_path, renderer_gate=None)`

Gate fields include:

- `schema_version`
- `created_at`
- `status`
- `preflight_status`
- `source_package_path`
- `source_manifest_path`
- `source_markdown_path`
- `export_format`
- `renderer_id`
- `renderer_gate`
- `planned_output_path`
- `conversion_log_path`
- `overwrite_policy`
- `artifact_manifest_preview`
- `checks`
- `disabled_reason`
- `blockers`
- `warnings`

The gate always returns `status=blocked` in B24.2 because activation is intentionally deferred.

If all structural checks pass, it returns:

- `preflight_status=passed_pending_activation`
- blocker `full_integrated_docx_export_activation_required_b24_2`

## Structural Checks

The DOCX preflight gate verifies:

- source package directory exists
- `integrated_report_package_manifest.json` exists
- package `status=full_integrated_report_package_created`
- `section_scope=full_integrated_report`
- `export_format=markdown`
- embedded full integrated content gate passed
- `integrated_report.md` exists
- `integrated_report.md` is non-empty
- local markdown image references resolve inside the package
- markdown does not contain forbidden clinical conclusion statement patterns
- Pandoc is detected through the renderer gate when available
- no conversion is invoked

## Blockers

Potential blockers include:

- `docx_source_package_missing`
- `docx_source_package_manifest_missing`
- `docx_source_package_status_not_created`
- `docx_source_package_scope_not_full_integrated_report`
- `docx_source_package_must_be_markdown_export`
- `docx_source_full_integrated_gate_not_passed`
- `docx_source_markdown_missing`
- `docx_source_markdown_empty`
- `docx_markdown_local_reference_missing:<path>`
- `docx_source_markdown_forbidden_clinical_conclusion:<term>`
- `renderer_dependency_missing:pandoc`
- `full_integrated_docx_renderer_not_enabled_in_b23_4`
- `full_integrated_docx_export_activation_required_b24_2`

## Package Plan / UI Visibility

`build_full_integrated_report_package_plan` now includes `renderer_preflight_policy`.

For DOCX, the policy describes:

- source package requirement: full integrated markdown package
- required renderer: `pandoc_docx`
- planned output: `exports/integrated_report.docx`
- conversion log: `logs/docx_renderer_preflight.log`
- required checks
- activation status: `disabled_until_docx_renderer_activation_stage`

Results Browser displays the preflight policy in the full integrated report plan table.

## Preserved Boundaries

- DOCX export remains disabled.
- Pandoc is never invoked by B24.2.
- No `.docx` file is created.
- No rendered export artifact is registered yet.
- Markdown-only full integrated report behavior is unchanged.
- PDF/Quarto remain disabled.
- Result semantics are unchanged.
- `report_ready_eligible` is unchanged.
- Imported/testing/exploratory/preflight results remain excluded from full integrated reports.
- No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram is generated.

## Validation

Focused validation:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/workflow_pages.py`
  - passed
- `python3 -m pytest tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py -q`
  - passed, `15 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser"`
  - passed, `11 passed, 103 deselected`

Full validation:

- `git diff --check`
  - passed
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"`
  - passed, `100 passed, 558 deselected`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or settings"`
  - passed, `12 passed, 102 deselected`
- `python3 -m pytest tests/bioinformatics -q`
  - passed, `658 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - passed, `271 passed`
- `python3 -m app.main --smoke-test`
  - passed
- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_source_b24_2.json`
  - passed, `status=passed`
- `python3 scripts/package_app.py --smoke-test`
  - passed
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_packaged_b24_2.json`
  - passed, `status=passed`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_openw_b24_2.json`
  - passed, `status=passed`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
  - passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`
  - passed

## Issues

### Blocker

- None.

### Major

- DOCX conversion execution and output artifact registration are still intentionally not implemented.

### Minor

- Local markdown reference validation currently covers markdown and HTML image references. Broader link checking can be added when DOCX conversion is activated.

## Conclusion

B24.2 completes the DOCX renderer preflight gate. The system can now audit whether a full integrated markdown package is ready for future DOCX rendering while keeping DOCX export disabled.

Recommended next step: **B24.3 DOCX Renderer Activation / Output Registration Planning or Implementation**, depending on whether a controlled Pandoc runtime is available.
