# Bioinformatics B24 Renderer Expansion Planning

Date: 2026-05-22

## Scope

B24 plans the next renderer expansion after B23 full integrated report closure.

The current ReleaseBuild candidate can create a markdown-only full integrated report package after all section gates pass. PDF and DOCX are still disabled by the renderer gate. B24 defines what must be implemented and audited before those formats can be enabled.

This planning stage does not enable PDF export, DOCX export, clinical conclusions, risk score, nomogram, legacy formal execution, or any new analysis engine.

## Current State

Implemented:

- `evaluate_full_integrated_report_renderer_gate(export_format)`
- markdown renderer gate with `renderer_id=builtin_markdown`
- PDF renderer detection path with `renderer_id=pandoc_pdf`
- DOCX renderer detection path with `renderer_id=pandoc_docx`
- detect-first dependency status for `pandoc`, `xelatex`, and `wkhtmltopdf`
- UI disabled reasons in Results Browser
- full integrated package plan fields for renderer status, renderer id, dependencies, and disabled reason

Still disabled:

- PDF rendering
- DOCX rendering
- Quarto rendering
- bundled renderer runtime
- renderer install action
- report package conversion from markdown into PDF/DOCX

Current blocker strings:

- `full_integrated_pdf_renderer_not_enabled_in_b23_4`
- `full_integrated_docx_renderer_not_enabled_in_b23_4`
- `renderer_dependency_missing:pandoc`
- `renderer_dependency_missing:xelatex_or_wkhtmltopdf`

## Renderer Expansion Principles

PDF/DOCX support must remain gated by the same full integrated report content contract:

- all required sections pass
- source results are formal computed results
- result index v2 snapshots are complete
- section report-ready gates pass
- dependency snapshots pass
- task-run logs and provenance exist
- warnings and limitations are included
- no imported/testing/exploratory/preflight result is upgraded
- no clinical diagnosis, prognosis, treatment recommendation, or risk score interpretation is generated

Renderer readiness must be a separate conjunction:

- format supported
- renderer dependency detected
- renderer version captured
- renderer architecture/package environment captured where possible
- renderer implementation enabled for the specific format
- conversion output passes file integrity checks
- converted artifact is registered in the package manifest
- failure returns disabled reason, not traceback

## Dependency Policy

Renderer dependencies are external capabilities, not analysis dependencies.

| Capability | Role | B24 Policy |
|---|---|---|
| `pandoc` | DOCX conversion and possible PDF orchestration | Detect first; do not auto-install. |
| `xelatex` | PDF backend for Pandoc | Detect first; optional until PDF activation stage. |
| `wkhtmltopdf` | Alternative PDF backend | Detect first; optional until PDF activation stage. |
| `quarto` | Future publishing pipeline | Detect only in planning; do not enable in B24 MVP. |

Dependency snapshot must include:

- command
- available status
- executable path
- version
- missing reason
- packaging impact
- source/runtime context: source, packaged executable, or open-W launch

No Settings or Results Browser UI may expose an install button.

## Proposed Implementation Sequence

### B24.1 Renderer Capability Snapshot Hardening

Goal: make renderer detection reusable and auditable without enabling PDF/DOCX.

Suggested code:

- `app/bioinformatics/reports/renderer_capability.py`
- `tests/bioinformatics/test_report_renderer_capability.py`

Required fields:

- `schema_version`
- `created_at`
- `environment`
- `capabilities`
- `packaging_impact`
- `blockers`
- `warnings`

Validation:

- source detection does not traceback when tools are missing
- packaged launcher detection does not traceback
- open-W detection can report the same status class
- dependency snapshot is visible in Settings/Results Browser

### B24.2 DOCX Renderer Preflight Gate

Goal: define DOCX activation rules, still blocked until an explicit activation task.

Minimum activation conditions:

- full integrated markdown package gate passes
- `pandoc` detected and version captured
- markdown input file exists and has non-empty content
- all local image/table references resolve inside the package
- output path is timestamped and non-overwriting
- generated `.docx` passes existence, size, and manifest registration checks
- conversion log is written to `logs/`
- failures keep markdown package intact and return disabled reason

DOCX must not be enabled if:

- `pandoc` is missing
- source package is not full integrated report
- source package contains imported/testing/exploratory/preflight sections
- source markdown contains forbidden clinical conclusion wording
- renderer output cannot be registered in manifest

### B24.3 PDF Renderer Preflight Gate

Goal: define PDF activation rules separately from DOCX because PDF has stronger system dependency risk.

Minimum activation conditions:

- all DOCX-independent markdown package conditions pass
- `pandoc` detected
- at least one PDF backend detected: `xelatex` or `wkhtmltopdf`
- backend version captured
- conversion output exists and is non-empty
- conversion log and stderr summary are included in `logs/`
- package manifest records PDF renderer id and backend
- failure is graceful and leaves markdown package valid

PDF must remain disabled if:

- no PDF backend is detected
- renderer output is blank or corrupt
- fonts/assets fail to resolve
- generated output cannot be audited from package manifests

### B24.4 Renderer Output Registration

Generated renderer artifacts must be registered as package export artifacts, not analysis results.

Required manifest fields:

- `artifact_id`
- `artifact_type=full_integrated_report_rendered_export`
- `source_package_id`
- `source_markdown_path`
- `export_format`
- `renderer_id`
- `renderer_version`
- `renderer_dependency_snapshot`
- `output_path`
- `validation_status`
- `warnings`
- `blockers`
- `created_at`

Renderer artifacts must not change:

- source result semantics
- section report-ready status
- `report_ready_eligible`
- analysis result index semantics

### B24.5 UI Export Controls

Results Browser should keep one clear export control per format:

- markdown: enabled only when full integrated gate and markdown renderer pass
- DOCX: disabled until DOCX renderer activation gate passes
- PDF: disabled until PDF renderer activation gate passes

UI must show:

- renderer status
- dependency versions
- missing reason
- packaging impact
- output path after successful export
- conversion log path after failure
- disabled reason before activation

UI must not imply PDF/DOCX exists when only markdown exists.

### B24.6 Package / Release Validation

Before enabling PDF/DOCX in ReleaseBuild, run:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_integrated_report_package.py -q
python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

If a controlled renderer runtime is used, also run source, packaged executable, and open-W renderer checks with explicit output JSON.

## Acceptance Criteria

B24 can proceed to implementation only if:

- markdown-only full integrated report behavior remains unchanged
- PDF/DOCX are not enabled by detection alone
- missing external renderers block gracefully
- Settings/Results Browser show detect-first status without install actions
- renderer output artifacts are package exports, not formal analysis results
- converted files can be independently audited from package manifests
- package smoke, open-W smoke, and codesign pass after any packaging change

## Blockers / Risks

### Blocker

- None for planning.

### Major

- PDF support depends on external binary availability and font/rendering behavior.
- DOCX fidelity depends on Pandoc output and image/table reference handling.
- Current package builder records markdown package artifacts only; rendered artifact registration needs a dedicated package export manifest.

### Minor

- Quarto should stay future-planned until Pandoc DOCX/PDF MVP is stable.
- UI copy needs careful wording so users do not mistake renderer detection for export readiness.

## Recommendation

Proceed next to **B24.1 Renderer Capability Snapshot Hardening**.

Do not enable PDF/DOCX export in B24.1. The first implementation should only make renderer capability snapshots reusable across source, packaged executable, and open-W launch contexts while preserving the current markdown-only ReleaseBuild candidate behavior.
