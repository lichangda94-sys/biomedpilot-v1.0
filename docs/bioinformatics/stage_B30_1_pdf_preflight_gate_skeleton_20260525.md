# B30.1 PDF Preflight Gate And Skeleton Attempt

Date: 2026-05-25

Baseline commit: `e853e6075cb974669745a90387f7ae3e5bc55cec`

Branch: `codex/releasebuild-formal-deg-carryover`

## Scope

B30.1 implements the first PDF renderer activation hardening layer:

- PDF preflight gate for an existing full integrated markdown package.
- PDF rendered export skeleton attempt that writes manifest/log evidence while remaining blocked.
- No real PDF conversion.
- No user-visible PDF activation.
- No result index v2 write.
- No renderer dependency installation, download, or bundling.

## Added API

`app.bioinformatics.reports.integrated` now exposes:

- `evaluate_full_integrated_pdf_preflight_gate(package_path, renderer_gate=None, include_activation_blocker=True)`
- `create_full_integrated_pdf_rendered_export_skeleton(package_path, renderer_gate=None, failure_reason="full_integrated_pdf_conversion_not_enabled_b30_1")`

The report namespace exports both APIs through `app.bioinformatics.reports`.

## PDF Preflight Gate

Schema:

- `biomedpilot.full_integrated_pdf_preflight_gate.v1`

Renderer:

- `renderer_id=pandoc_pdf`
- `selected_backend=pandoc_xelatex`

Required source package checks:

- package directory exists
- `integrated_report_package_manifest.json` exists
- package status is `full_integrated_report_package_created`
- `section_scope=full_integrated_report`
- source export format is `markdown`
- full integrated gate status is `eligible_for_full_integrated_report`
- `integrated_report.md` exists and is non-empty
- local markdown references resolve inside the package
- forbidden clinical conclusion wording is absent

Required renderer checks:

- Pandoc detected
- XeLaTeX detected
- `wkhtmltopdf` remains detect-only and not selected
- detect-first/no-install policy
- no conversion invoked

Activation blocker retained:

- `full_integrated_pdf_export_activation_required_b30_1`

Current environment blocker still expected unless XeLaTeX is installed:

- `renderer_dependency_missing:xelatex`

## Skeleton Attempt

`create_full_integrated_pdf_rendered_export_skeleton()` writes:

- `manifests/rendered_exports.json`
- `logs/pdf_renderer_<timestamp>.log`

Attempt fields include:

- `artifact_type=full_integrated_report_rendered_export_attempt`
- `export_format=pdf`
- `renderer_id=pandoc_pdf`
- `selected_backend=pandoc_xelatex`
- `conversion_invoked=false`
- `validation_status=blocked`
- renderer dependency snapshot
- blocker list
- conversion log path

The conversion log records:

- schema `biomedpilot.full_integrated_pdf_conversion_log.v1`
- renderer command/version
- backend command/version
- environment
- output path
- preflight status/blockers
- `conversion_invoked=false`
- `markdown_package_preserved=true`
- `temporary_output_removed=true`

## Manifest Policy

Rendered exports remain package artifacts:

- `rendered_exports_are_package_artifacts_not_analysis_results=true`
- `do_not_write_formal_computed_result=true`
- `pdf_conversion_enabled=false`

PDF skeleton attempts do not add successful exports and do not alter result semantics.

Existing DOCX rendered exports are preserved when a PDF skeleton attempt is written.

## Boundaries

B30.1 does not:

- call Pandoc for PDF
- create `.pdf`
- enable the UI PDF export action
- select `wkhtmltopdf` as the formal backend
- install or bundle XeLaTeX/TeX/Pandoc/wkhtmltopdf
- write result index v2
- mark rendered exports as `formal_computed_result`
- change full integrated report content eligibility
- add clinical diagnosis, prognosis, risk score, nomogram, or treatment recommendation text

## Tests

Added/updated tests:

- PDF preflight validates a full integrated markdown package but remains blocked by activation.
- PDF preflight blocks missing local markdown references.
- PDF skeleton writes blocked attempt manifest/log without creating PDF.
- PDF skeleton preserves existing successful DOCX exports and keeps `pdf_conversion_enabled=false`.

Validation run:

- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k 'pdf or docx_rendered_export_skeleton'`
  - `6 passed, 13 deselected`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py`
  - `9 passed`

## Issues

Blockers:

- PDF real conversion remains blocked until XeLaTeX is available and a controlled real PDF conversion stage is approved.

Major:

- None for B30.1.

Minor:

- `wkhtmltopdf` remains detect-only and is not selected.

## Conclusion

B30.1 completes the non-rendering PDF gate layer. PDF is now auditable as a blocked package-level rendered export attempt, with preflight diagnostics, dependency snapshot, conversion log, and manifest registration. Real PDF generation remains disabled.

Recommended next step: **B30.2 Controlled PDF Conversion Planning / XeLaTeX Runtime Acceptance**, only after XeLaTeX is installed and validated in source, packaged executable, and `open -W` environments.
