# Bioinformatics B30.5 PDF ReleaseBuild Closure / Handoff Gate

Date: 2026-05-25

Branch: `codex/releasebuild-formal-deg-carryover`

Baseline before this audit: `f6834ee audit Bioinformatics PDF rendered export UX`

## Scope

B30.5 closes the PDF rendered export activation line for the ReleaseBuild candidate. It verifies that B30.1-B30.4 can be handed forward as a controlled package-artifact capability.

This is a ReleaseBuild closure and handoff gate. It does not publish a release, does not create a notarized distribution, and does not change full integrated report semantics.

## B30 Capability Summary

| Stage | Capability | Status |
| --- | --- | --- |
| B30 planning | PDF backend policy selected as Pandoc + XeLaTeX; `wkhtmltopdf` detect-only | Passed |
| B30.1 | PDF preflight gate and blocked skeleton attempt | Passed |
| B30.2 | Controlled PDF conversion through external Pandoc + XeLaTeX | Passed |
| B30.3 | Analysis UI / Results Browser PDF rendered export gate | Passed |
| B30.4 | Real UI package artifact acceptance | Passed |
| B30.5 | ReleaseBuild source/package/open-W closure | Passed |

## ReleaseBuild Candidate State

- HEAD: `f6834ee`
- `.app`: `dist/BioMedPilot.app`
- Bundle `BioMedPilotGitHead`: `f6834ee`
- Bundle executable: `BioMedPilot`
- Signing: ad-hoc signed, `codesign --verify --deep --strict` passed
- Bundle size: `34M`
- Host architecture: `arm64`
- Packaged renderer environment: `packaged_app_resource`

The worktree still contains one unrelated untracked file:

- `docs/release/ReleaseBuild_handoff_report_20260513.md`

It is intentionally excluded from this B30.5 handoff gate.

## Renderer Runtime Matrix

| Environment | Status | Architecture | Pandoc | XeLaTeX | `wkhtmltopdf` | Quarto | Blockers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Source | passed | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` | `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)` | missing, detect-only | missing, detect-only | none |
| Packaged executable | passed | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` | `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)` | missing, detect-only | missing, detect-only | none |
| `open -W` | passed | arm64 | `/opt/homebrew/bin/pandoc`, `pandoc 3.9.0.2` | `/Users/changdali/Library/TinyTeX/bin/universal-darwin/xelatex`, `XeTeX 3.141592653-2.6-0.999998 (TeX Live 2026)` | missing, detect-only | missing, detect-only | none |

## Packaging Boundary

ReleaseBuild continues to follow the B24.3 renderer runtime policy:

- Detect first.
- Do not auto-install or download renderer tools.
- Do not bundle Pandoc, TeX/XeLaTeX, `wkhtmltopdf`, Quarto, or `tlmgr`.
- Launcher exports stable renderer search paths for Finder / `open -W`.
- Codesign scope remains the BioMedPilot app bundle only.

Bundle scan result:

- No bundled `pandoc`
- No bundled `xelatex`
- No bundled `wkhtmltopdf`
- No bundled `tlmgr`
- No bundled `Rscript`

## UI / Product Boundary

PDF is user-visible only as a rendered export of an existing full integrated markdown package.

It remains blocked unless all of these are true:

1. The full integrated markdown package exists.
2. The package manifest status is `full_integrated_report_package_created`.
3. The package scope is `full_integrated_report`.
4. The source markdown exists and local references resolve.
5. The markdown does not contain forbidden clinical conclusion terms.
6. Pandoc is detected.
7. XeLaTeX is detected.
8. `wkhtmltopdf` is not selected.
9. The PDF preflight gate passes with explicit PDF activation.

The PDF action must continue to show disabled reasons when any gate fails.

## Artifact Boundary

PDF rendered export writes only inside the full integrated report package:

- `exports/*.pdf`
- `logs/pdf_renderer_*.json`
- `manifests/rendered_exports.json`
- `integrated_report_package_manifest.json` rendered export summary

It must not:

- write `result_index_v2`
- create or update `formal_computed_result`
- change report-ready eligibility
- enable GSEA / survival / clinical execution
- generate diagnosis, prognosis, risk score, nomogram, or treatment advice

## ReleaseBuild Handoff Gate

Recommended ReleaseBuild carry-forward status: proceed.

Conditions:

- Carry forward B30.1-B30.5 as a controlled full integrated report rendered export capability.
- Keep PDF as package artifact only.
- Keep external renderer policy unchanged.
- Keep `wkhtmltopdf` detect-only unless a future policy stage explicitly changes backend selection.
- Do not treat missing user-system Pandoc/XeLaTeX on another machine as a crash condition; UI must gracefully block with renderer dependency reasons.

## Rollback Plan

If packaged PDF export causes a ReleaseBuild regression:

1. Disable the UI action by forcing the PDF rendered export UI gate to blocked.
2. Preserve DOCX and markdown report package behavior.
3. Keep `create_full_integrated_pdf_rendered_export()` available for internal tests only if safe.
4. Remove any generated package-local `exports/*.pdf` artifacts from test fixtures.
5. Re-run renderer detection and UI gate tests before re-enabling.

## Verification Commands

Run for B30.5:

- `git status --short`
- `git diff --check`
- `python3 -m py_compile app/bioinformatics/workflow_pages.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/state.py`
- `python3 -m pytest -q tests/bioinformatics/test_analysis_ui_action_rules.py tests/bioinformatics/test_analysis_ui_state.py`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k 'report or integrated or renderer or pdf'`
- `python3 -m pytest -q tests/bioinformatics/test_integrated_report_package.py -k 'pdf'`
- `python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer or analysis_ui"`
- `python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_5_source_renderer.json`
- `dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_5_packaged_renderer.json`
- `python3 -m app.main --smoke-test`
- `python3 scripts/package_app.py --smoke-test`
- `open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_b30_5_openw_renderer.json`
- `open -W -n dist/BioMedPilot.app --args --smoke-test`
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`

Observed results:

- `git diff --check`: passed
- `py_compile`: passed
- `test_analysis_ui_action_rules.py` + `test_analysis_ui_state.py`: 27 passed
- `test_bioinformatics_workflow_pages.py -k 'report or integrated or renderer or pdf'`: 11 passed
- `test_integrated_report_package.py -k 'pdf'`: 8 passed
- `tests/bioinformatics -k "integrated or report or renderer or analysis_ui"`: 145 passed
- source renderer runtime check: passed
- packaged executable renderer runtime check: passed
- source smoke: passed
- package smoke: passed
- `open -W` renderer runtime check: passed
- `open -W` smoke: passed
- codesign strict verification: passed

## Issues

Blocker: none.

Major: none.

Minor: none.

Residual note: `wkhtmltopdf` and Quarto remain unavailable. This is acceptable because B30 selects Pandoc + XeLaTeX and keeps the other tools detect-only.

## Conclusion

B30.5 passes. The PDF rendered export line is ready to be carried forward in ReleaseBuild as a controlled package-artifact feature. It is not a formal analysis result and does not expand clinical, GSEA, survival, risk score, or report-ready semantics.
