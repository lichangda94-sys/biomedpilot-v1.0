# B29 DOCX Real Environment Acceptance With Installed Pandoc

Date: 2026-05-25

Baseline commit: `8aa10f529fbbac221bf696e3029fa53e6a4e9bb4`

Branch: `codex/releasebuild-formal-deg-carryover`

## Scope

B29 validates the real DOCX renderer environment after user/system Pandoc was installed. This stage does not bundle Pandoc, does not install or download renderer tools, does not enable PDF, and does not turn rendered report exports into result index v2 `formal_computed_result` entries.

Accepted scope:

- Detect user/system Pandoc in source, packaged executable, and `open -W` launch environments.
- Run a real controlled full integrated markdown package through Pandoc DOCX conversion.
- Verify rendered export manifest, conversion log, package manifest update, rollback/failure policy, and no result-index write.
- Verify package smoke, `open -W`, codesign, package size, startup timing, architecture, and external-renderer packaging boundary.

Out of scope:

- PDF activation.
- Bundling Pandoc, XeLaTeX, wkhtmltopdf, Quarto, or R into the `.app`.
- GSEA/survival/clinical expansion.
- Full integrated report content gate changes.
- Any clinical interpretation or treatment recommendation.

## Runtime Detection

| Environment | Command | Status | Environment label | Architecture | Pandoc |
| --- | --- | --- | --- | --- | --- |
| Source | `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b29_source_renderer.json` | passed | source | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` |
| Packaged executable | `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b29_packaged_renderer.json` | passed | packaged_app_resource | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` |
| Finder/open-W launch | `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b29_openw_renderer.json` | passed | packaged_app_resource | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` |

All three environments used the detect-first policy and reported `detect_first_no_install_no_download`.

Remaining expected renderer blocker:

- `renderer_dependency_missing:xelatex_or_wkhtmltopdf`

This blocker is acceptable for B29 because PDF remains disabled. DOCX requires only Pandoc.

## Real DOCX Conversion Evidence

A controlled full integrated markdown package was created in a temporary project root and rendered through the real Pandoc executable.

Result:

- Status: `full_integrated_docx_rendered_export_created`
- Output: `exports/integrated_report_20260525062455947507.docx`
- Output size: `10994` bytes
- Renderer version: `pandoc 3.9.0.2`
- Conversion invoked: `true`
- Exit code: `0`
- `manifests/rendered_exports.json` exports count: `1`
- Latest attempt status: `passed`

Policy recorded in `rendered_exports.json`:

- `rendered_exports_are_package_artifacts_not_analysis_results=true`
- `do_not_write_formal_computed_result=true`
- `docx_conversion_enabled=true`
- `pdf_conversion_enabled=false`

This confirms DOCX is a report package rendered export artifact, not a formal analysis result.

## Packaging Boundary

ReleaseBuild packaging remains external-renderer only:

- `renderer_runtime_packaging_policy.policy_id=b24_3_system_path_no_bundled_renderers`
- `bundles_external_renderers=false`
- `network_downloads=false`
- `auto_install=false`
- Launcher exports `BIOMEDPILOT_RENDERER_SEARCH_PATHS` with stable Homebrew/system search paths.

Bundle scan:

- `find dist/BioMedPilot.app -name pandoc -o -name Rscript -o -name xelatex -o -name wkhtmltopdf` returned no bundled renderer binaries.

Package metadata:

- Package size: `34M`
- `CFBundleExecutable=BioMedPilot`
- Launcher file: POSIX shell script
- Packaged Python: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`
- Package git head: `8aa10f5`

## UI / Product Boundary

The DOCX action remains controlled by the full integrated markdown package gate and the renderer gate. Missing Pandoc still produces `renderer_dependency_missing:pandoc` with no traceback and no install/download action.

PDF remains disabled because B29 does not activate a PDF backend. `xelatex` and `wkhtmltopdf` are still detect-only/missing in this environment.

## Tests And Commands

Passed:

- `git diff --check`
- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b29_source_renderer.json`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k 'docx_rendered_export_real_pandoc_environment_acceptance or docx_rendered_export_creates_docx'`
  - `2 passed, 13 deselected`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py tests/test_package_app.py`
  - `31 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k 'report or integrated or renderer or docx'`
  - `10 passed, 106 deselected`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b29_packaged_renderer.json`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b29_openw_renderer.json`
- `/usr/bin/time -p open -W -n dist/BioMedPilot.app --args --smoke-test`
  - `real 1.77`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

## Code/Test Change

Added a guarded real-environment acceptance test:

- `tests/bioinformatics/test_integrated_report_package.py`
  - `test_docx_rendered_export_real_pandoc_environment_acceptance`

The test runs only when user/system Pandoc is available on the renderer search path. Without Pandoc, it skips instead of failing, preserving the ReleaseBuild external dependency policy.

## Issues

Blockers:

- None for DOCX real environment acceptance.

Major:

- None.

Minor / expected:

- `xelatex` and `wkhtmltopdf` are still missing, so PDF remains blocked. This is expected and does not affect DOCX acceptance.

## Conclusion

B29 passes for DOCX real environment acceptance with installed user/system Pandoc.

DOCX can be rendered from a valid full integrated markdown package, registered as a rendered export package artifact, and audited through the conversion log and manifest. The `.app` does not bundle Pandoc or other external renderer binaries, and source/package/open-W detection is consistent.

Recommended next step: **B30 PDF renderer activation planning**, keeping PDF disabled until Pandoc + XeLaTeX policy, package impact, failure rollback, and open-W runtime acceptance are separately audited.
