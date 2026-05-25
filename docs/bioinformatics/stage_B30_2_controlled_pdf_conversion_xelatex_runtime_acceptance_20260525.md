# B30.2 Controlled PDF Conversion And XeLaTeX Runtime Acceptance

Date: 2026-05-25

Baseline commit: `ee3f8033d8c9cb269ed0ed6e98b3bb9b89da6556`

Branch: `codex/releasebuild-formal-deg-carryover`

## Scope

B30.2 installs and validates an external XeLaTeX runtime, then activates a controlled internal PDF rendered export path for an existing full integrated markdown package.

This stage does not enable the ordinary full integrated PDF button, does not bundle TeX/Pandoc into the `.app`, does not install dependencies from the app, and does not write result index v2 entries for rendered exports.

## Runtime Installation

Attempted first:

- `brew install --cask basictex`
- Result: blocked by interactive `sudo` because the non-interactive automation environment cannot provide a password.

Completed:

- Installed user-level TinyTeX through `https://yihui.org/tinytex/install-unx.sh`.
- Install path: `/Users/changdali/Library/TinyTeX`
- Install size: `248M`
- XeLaTeX path: `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`
- XeLaTeX version: `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)`
- `tlmgr` version: TeX Live 2026, installation `/Users/changdali/Library/TinyTeX`

Boundary:

- TinyTeX is an external user/system runtime.
- It is not copied into `dist/BioMedPilot.app`.
- The app still does not auto-install or download renderers.

## Search Path Hardening

Updated renderer search path handling so source and packaged launches can detect user-level TinyTeX without a `/usr/local/bin` symlink:

- `app/bioinformatics/reports/renderer_runtime_policy.py`
  - added user-level renderer paths:
    - `~/Library/TinyTeX/bin/universal-darwin`
    - `~/.TinyTeX/bin/universal-darwin`
- `app/bioinformatics/reports/renderer_capability.py`
  - expands `~` and environment variables in renderer search paths.
- `scripts/package_app.py`
  - launcher default `BIOMEDPILOT_RENDERER_SEARCH_PATHS` now includes `${HOME}/Library/TinyTeX/bin/universal-darwin` and `${HOME}/.TinyTeX/bin/universal-darwin`.

## Runtime Detection Acceptance

| Environment | Status | Architecture | Pandoc | XeLaTeX | Blockers |
| --- | --- | --- | --- | --- | --- |
| Source | passed | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` | `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)` | none |
| Packaged executable | passed | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` | `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)` | none |
| `open -W` | passed | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` | `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)` | none |

`wkhtmltopdf` remains missing and detect-only. It is not required for the selected Pandoc + XeLaTeX backend.

## Controlled PDF Conversion

Added internal API:

- `create_full_integrated_pdf_rendered_export(package_path, command_finder=None, runner=None, timeout_seconds=90)`

The function:

- evaluates `evaluate_full_integrated_report_renderer_gate("pdf", allow_pdf_activation=True)`
- evaluates `evaluate_full_integrated_pdf_preflight_gate(..., include_activation_blocker=False)`
- requires Pandoc and XeLaTeX to be detected
- writes to `exports/.tmp/` first
- validates non-empty output and `%PDF` header
- moves the PDF into `exports/` only after validation
- writes `logs/pdf_renderer_<timestamp>.log`
- registers the rendered export in `manifests/rendered_exports.json`
- updates `integrated_report_package_manifest.json`
- removes temporary output on failure

Real controlled fixture result:

- Status: `full_integrated_pdf_rendered_export_created`
- Output: `exports/integrated_report_20260525105732701830.pdf`
- Output size: `12532` bytes
- Header: `%PDF`
- Renderer: `pandoc 3.9.0.2`
- Backend: `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)`
- Conversion invoked: `true`
- Exit code: `0`
- Rendered exports count: `1`
- Latest attempt status: `passed`

Manifest policy:

- `rendered_exports_are_package_artifacts_not_analysis_results=true`
- `do_not_write_formal_computed_result=true`
- `pdf_conversion_enabled=true` only on the rendered export package manifest

This does not change source result semantics or section report-ready status.

## Product Boundary

Still disabled by default:

- `create_full_integrated_report_package(..., export_format="pdf")`
- ordinary UI PDF action
- PDF as a formal analysis result
- result index v2 write for rendered exports
- `wkhtmltopdf` backend selection
- clinical diagnosis, prognosis, risk score, nomogram, or treatment recommendation text

## Package Boundary

Package validation:

- `python3 scripts/package_app.py --smoke-test`: passed
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed
- `.app` size: `34M`
- Bundle scan for `pandoc`, `xelatex`, `wkhtmltopdf`, `tlmgr`: no bundled renderer binaries found

## Tests

Passed:

- `git diff --check`
- `python3 -m py_compile app/bioinformatics/reports/integrated.py app/bioinformatics/reports/__init__.py app/bioinformatics/reports/renderer_capability.py app/bioinformatics/reports/renderer_runtime_policy.py scripts/package_app.py`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k 'pdf'`
  - `8 passed, 15 deselected`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py tests/test_package_app.py`
  - `17 passed`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py tests/test_package_app.py`
  - `40 passed`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"`
  - `123 passed, 596 deselected`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k 'report or integrated or renderer or pdf'`
  - `8 passed, 108 deselected`
- `python3 -m app.main --smoke-test`
- source / packaged executable / `open -W` renderer runtime checks
- package smoke / open-W smoke / codesign

## Issues

Blockers:

- None for controlled PDF conversion.

Major:

- Ordinary user-visible PDF export remains intentionally disabled until a separate UI activation / acceptance stage.

Minor:

- Homebrew BasicTeX cask could not complete without interactive sudo; user-level TinyTeX is the accepted runtime for this candidate.
- `wkhtmltopdf` remains missing and detect-only.

## Conclusion

B30.2 passes. The environment now has an external user-level XeLaTeX runtime, source/package/open-W detection is consistent, and a controlled internal PDF rendered export can be created from a valid full integrated markdown package.

Recommended next step: **B30.3 PDF UI Activation / User Confirmation Gate**, keeping the ordinary PDF action disabled unless full integrated markdown package gate, renderer dependency gate, PDF preflight, conversion validation, manifest registration, and package provenance all pass.
