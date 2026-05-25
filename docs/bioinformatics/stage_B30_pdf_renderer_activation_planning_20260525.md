# B30 PDF Renderer Activation Planning

Date: 2026-05-25

Baseline commit: `e8b6973ebdb6aa334a6b8da0bcda43f928fb7209`

Branch: `codex/releasebuild-formal-deg-carryover`

## Scope

B30 plans the PDF renderer activation path for full integrated report packages after B29 proved user/system Pandoc can be detected and used for DOCX rendering in source, packaged executable, and `open -W` contexts.

This stage is planning only. It does not enable PDF export, does not invoke a PDF conversion backend, does not bundle or install renderer dependencies, and does not change report/result semantics.

## Current State

Implemented before B30:

- Full integrated markdown report package creation.
- DOCX rendered export from a valid full integrated markdown package when user/system Pandoc is present.
- Renderer capability snapshot for `pandoc`, `xelatex`, `wkhtmltopdf`, and `quarto`.
- Renderer runtime packaging policy: external system tools only, detect-first, no install/download action.
- UI disabled reasons for renderer dependencies and unavailable formats.

Current B30 source runtime check:

| Capability | Status | Path / reason | Version | Packaging impact |
| --- | --- | --- | --- | --- |
| `pandoc` | available | `/opt/homebrew/bin/pandoc` | `pandoc 3.9.0.2` | external binary, not bundled |
| `xelatex` | missing | `xelatex_not_found_on_renderer_search_paths` |  | external binary, not bundled |
| `wkhtmltopdf` | missing | `wkhtmltopdf_not_found_on_renderer_search_paths` |  | detect-only alternative, not bundled |
| `quarto` | missing | `quarto_not_found_on_renderer_search_paths` |  | future detect-only |

Current blocker:

- `renderer_dependency_missing:xelatex_or_wkhtmltopdf`

For the formal full integrated PDF path, this is still a blocker because ReleaseBuild policy selects Pandoc + `xelatex` as the future backend. `wkhtmltopdf` remains detect-only and must not become the formal full integrated statistical report backend without a separate policy change.

## Activation Decision

B30 should not activate PDF in the current environment.

Reason:

- `xelatex` is missing.
- PDF output has stricter rendering, font, image, pagination, and reproducibility risk than DOCX.
- The existing product contract says PDF must be a rendered export artifact from a valid full integrated markdown package, not an analysis result.
- The `.app` must not redistribute TeX/Pandoc/wkhtmltopdf binaries under codesign.

## Required PDF Gate

PDF enablement must be a conjunction of independent gates:

1. Full integrated markdown package gate passed.
2. Source package manifest confirms `section_scope=full_integrated_report`.
3. Source sections are only formal report-ready DEG / ORA / GSEA / KM / Cox sections.
4. No imported/testing/exploratory/preflight result is present in the source package.
5. No clinical diagnosis, prognosis, treatment recommendation, risk score, or nomogram wording is present.
6. Renderer runtime policy is `b24_3_system_path_no_bundled_renderers`.
7. `pandoc` is detected and version captured.
8. `xelatex` is detected and version captured.
9. `wkhtmltopdf`, if detected, is recorded as detect-only and not selected.
10. Markdown local references resolve inside the package.
11. Fonts/assets required by Pandoc + XeLaTeX resolve or are explicitly blocked.
12. Output path is timestamped and non-overwriting.
13. Conversion writes to `exports/.tmp/` first.
14. Final `.pdf` is moved into `exports/` only after validation.
15. Output PDF exists, is non-empty, and passes a minimum header check.
16. Conversion log is written under `logs/`.
17. `manifests/rendered_exports.json` registers the PDF rendered export.
18. `integrated_report_package_manifest.json` records rendered export summary.
19. Failure removes temporary output and preserves the markdown package.
20. PDF artifact remains a package export artifact and does not write result index v2.

## Proposed Implementation Sequence

### B30.1 PDF Preflight Gate

Add a PDF-specific preflight function parallel to DOCX:

- `evaluate_full_integrated_pdf_preflight_gate(package_path, renderer_gate=None, include_activation_blocker=True)`

Required outputs:

- schema version
- status
- renderer id: `pandoc_pdf`
- selected backend: `pandoc_xelatex`
- source package path
- source markdown path
- dependency snapshot
- checks
- blockers
- warnings
- planned output path
- conversion log path

Required blockers:

- `full_integrated_pdf_export_activation_required_b30_1`
- `renderer_dependency_missing:pandoc`
- `renderer_dependency_missing:xelatex`
- `pdf_backend_not_selected:wkhtmltopdf_detect_only`
- `full_integrated_markdown_package_missing`
- `source_package_not_full_integrated_report`
- `source_markdown_missing_or_empty`
- `pdf_markdown_local_reference_missing:<path>`
- `pdf_forbidden_clinical_language_detected`

### B30.2 PDF Rendered Export Skeleton

Add a skeleton registration path that writes a blocked attempt without invoking Pandoc:

- `create_full_integrated_pdf_rendered_export_skeleton(package_path, renderer_gate=None)`

It should write:

- `manifests/rendered_exports.json`
- `logs/pdf_renderer_<timestamp>.json`

It must not create `.pdf`.

### B30.3 Controlled PDF Conversion

Only after `xelatex` is available in source, packaged executable, and `open -W`, add:

- `create_full_integrated_pdf_rendered_export(package_path, timeout_seconds=...)`

Conversion command:

```bash
pandoc integrated_report.md --pdf-engine=xelatex -o exports/.tmp/integrated_report_<stamp>.tmp.pdf
```

Validation:

- return code is zero
- temp PDF exists
- file size is greater than zero
- first bytes begin with `%PDF`
- final output path does not pre-exist
- temp file is moved atomically to `exports/`
- failure removes temp file
- markdown package remains intact

### B30.4 UI Gate

Update Analysis UI / Results Browser only after the preflight and controlled conversion path exist.

User-visible state must include:

- PDF renderer status
- Pandoc version
- XeLaTeX version or missing reason
- selected backend: Pandoc + XeLaTeX
- `wkhtmltopdf` detect-only note when present
- disabled reason
- output path after success
- conversion log path after failure

The UI must not imply PDF exists when only markdown or DOCX exists.

### B30.5 Package / Open-W Runtime Acceptance

Before any user-visible PDF activation:

```bash
python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_source_renderer.json
python3 scripts/package_app.py --smoke-test
dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_packaged_renderer.json
open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_openw_renderer.json
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Acceptance requirements:

- `pandoc.available=true`
- `xelatex.available=true`
- architecture is `arm64`
- source / packaged / open-W detection agree
- package scan finds no bundled `pandoc`, `xelatex`, `wkhtmltopdf`, or TeX distribution payload
- package size impact is documented
- startup timing is documented
- codesign passes

### B30.6 Real PDF Fixture Acceptance

Run a controlled full integrated markdown package through real Pandoc + XeLaTeX.

Required evidence:

- PDF output path
- output size
- `%PDF` header
- conversion log
- renderer versions
- dependency snapshot
- rendered export manifest entry
- package manifest rendered export summary
- failure rollback test

## Test Plan

Minimum tests for implementation stages:

```bash
git diff --check
python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k "pdf or renderer"
python3 -m pytest -q tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k "report or integrated or renderer or pdf"
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

When XeLaTeX is installed, add a guarded real-environment test similar to B29 DOCX:

- runs real Pandoc + XeLaTeX only when both are available
- skips when dependencies are missing
- asserts PDF header and manifest/log registration

## Boundaries

B30 and future PDF activation must not:

- install renderer dependencies
- download TeX/Pandoc/wkhtmltopdf
- bundle renderer binaries into the `.app`
- select `wkhtmltopdf` as the formal full integrated statistical PDF backend
- write result index v2 entries for rendered exports
- mark rendered exports as `formal_computed_result`
- change source result semantics
- enable GSEA/survival/risk-score expansion
- generate clinical diagnosis, prognosis, treatment recommendation, or nomogram text

## Blockers / Major / Minor

Blockers:

- `xelatex` missing in the current environment.

Major:

- PDF rendering fidelity and font behavior must be validated separately from DOCX.
- Package/open-W runtime must be revalidated after XeLaTeX installation because Finder launch PATH behavior is the common failure point.

Minor:

- `wkhtmltopdf` remains missing. This is not a blocker for the selected Pandoc + XeLaTeX formal backend.

## Conclusion

B30 planning is complete. PDF should remain disabled until a future implementation stage adds the PDF preflight gate, skeleton attempt registration, real Pandoc + XeLaTeX conversion path, UI disabled reason updates, and source/package/open-W runtime acceptance with XeLaTeX installed.

Recommended next step: **B30.1 PDF Preflight Gate / Skeleton Attempt Implementation**, still without creating real PDFs unless XeLaTeX is available and explicitly accepted.
