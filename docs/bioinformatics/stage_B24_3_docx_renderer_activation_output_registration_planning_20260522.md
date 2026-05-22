# Bioinformatics B24.3 DOCX Renderer Activation / Output Registration Planning

Date: 2026-05-22

## Scope

B24.3 plans DOCX renderer activation and rendered export artifact registration for full integrated report packages.

This stage is planning only. It does not invoke Pandoc, does not create a `.docx` file, does not enable the user-visible DOCX export button, and does not change the current graceful blocked behavior when `pandoc` is missing.

The current runtime gap for `pandoc` / `xelatex` / `wkhtmltopdf` is assigned to integration / packaging. Bioinformatics must not bypass that dependency gate.

This stage does not enable PDF export, Quarto export, clinical conclusions, risk score, nomogram, legacy formal execution, or any new analysis engine.

## Current Baseline

Implemented before B24.3:

- B24.1 reusable renderer capability snapshot
- source / packaged executable / open-W renderer runtime check
- Settings and Analysis Center renderer dependency visibility
- B24.2 DOCX preflight gate for full integrated markdown packages
- `renderer_preflight_policy` in the full integrated package plan

Current blocked behavior:

- `pandoc` missing keeps DOCX blocked.
- `xelatex` / `wkhtmltopdf` missing keeps PDF blocked.
- Missing renderer dependencies return disabled reasons, not traceback.
- DOCX preflight can reach `passed_pending_activation` only under a mocked/controlled Pandoc-ready gate; actual activation remains blocked by `full_integrated_docx_export_activation_required_b24_2`.

## Integration Handoff Boundary

Integration / packaging must decide and validate:

- whether Pandoc is bundled or treated as a required external binary
- how packaged app PATH resolves Pandoc under direct executable launch and `open -W`
- macOS arm64 compatibility
- license and redistribution constraints
- package size impact
- codesign and Gatekeeper impact
- how renderer runtime status is exposed to ReleaseBuild

Bioinformatics must wait for an integration-provided runtime signal before enabling DOCX execution.

Expected integration evidence:

- source renderer runtime check: `status=passed`, `pandoc.available=true`
- packaged executable renderer runtime check: `status=passed`, `pandoc.available=true`
- open-W renderer runtime check: `status=passed`, `pandoc.available=true`
- version and path captured in renderer capability snapshot
- package smoke passed
- open-W smoke passed
- codesign passed

## Activation Gate Design

Future DOCX activation must be the conjunction of:

- full integrated markdown package exists
- B23 full integrated content gate passed
- B24.2 DOCX preflight structural checks pass
- renderer capability snapshot detects Pandoc
- DOCX activation flag is enabled by audited implementation stage
- source markdown references resolve inside package
- markdown contains no forbidden clinical conclusion wording
- output path is non-overwriting
- conversion log path is available
- conversion process exits successfully
- output `.docx` exists and is non-empty
- rendered export artifact manifest is written
- package manifest is updated atomically

The activation gate must stay blocked when:

- Pandoc is missing
- source package is not full integrated markdown
- source package is imported/testing/exploratory/preflight-derived
- local image/table references are missing
- forbidden clinical conclusion wording is detected
- output path already exists
- Pandoc exits non-zero
- output file is missing or empty
- manifest update fails

## Rendered Export Artifact Manifest

DOCX rendered outputs must be registered as package export artifacts, not as analysis results.

Suggested manifest file:

- `manifests/rendered_exports.json`

Suggested schema:

```json
{
  "schema_version": "biomedpilot.full_integrated_rendered_exports.v1",
  "package_scope": "full_integrated_report",
  "source_package_id": "<package id or timestamp>",
  "source_package_path": "<package path>",
  "exports": [
    {
      "artifact_id": "docx_<timestamp>",
      "artifact_type": "full_integrated_report_rendered_export",
      "source_markdown_path": "integrated_report.md",
      "export_format": "docx",
      "renderer_id": "pandoc_docx",
      "renderer_version": "<pandoc version>",
      "renderer_dependency_snapshot": {},
      "output_path": "exports/integrated_report_<timestamp>.docx",
      "conversion_log_path": "logs/docx_renderer_<timestamp>.log",
      "validation_status": "passed",
      "warnings": [],
      "blockers": [],
      "created_at": "<iso timestamp>"
    }
  ]
}
```

Required rules:

- Use relative paths inside the package manifest where possible.
- Keep absolute paths only in developer diagnostics if needed.
- Do not write rendered exports into result index v2 as `formal_computed_result`.
- Do not change source section result semantics.
- Do not change `report_ready_eligible`.
- Do not claim PDF exists when only DOCX exists.

## Conversion Log Design

Each DOCX attempt must write a log under `logs/`.

Minimum log fields:

- `schema_version`
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

Log constraints:

- No raw clinical interpretation is generated.
- No patient identifiers beyond already packaged research artifact paths.
- Long stdout/stderr should be truncated with a byte/line limit.
- Failure logs must be written even when conversion fails.

## Failure Rollback Strategy

DOCX rendering must be transactional from the package user's perspective.

Recommended sequence:

1. Run B24.2 preflight.
2. Reserve a timestamped output path under `exports/`.
3. Write conversion log as `in_progress`.
4. Invoke Pandoc into a temporary file under `exports/.tmp/`.
5. Validate temp output exists and size is greater than zero.
6. Move temp output atomically to final output path.
7. Write or update `manifests/rendered_exports.json`.
8. Update package manifest with rendered export summary.
9. Rewrite conversion log as `passed`.

Failure behavior:

- delete temporary output if present
- keep existing markdown package intact
- keep existing successful rendered exports intact
- write failure log with reason
- return `status=blocked` or `status=failed`
- expose disabled/failure reason in UI
- never partially register a failed DOCX export as passed

## Overwrite / Path Policy

DOCX export must never overwrite existing files.

Allowed path forms:

- `exports/integrated_report_<timestamp>.docx`
- `logs/docx_renderer_<timestamp>.log`

If a path exists:

- choose a new timestamp/counter
- do not truncate existing output
- do not reuse an existing log path

The UI must show:

- final output path after success
- failure log path after failure
- explicit reason if no output was created

## UI Controls

Results Browser should keep DOCX separate from markdown:

- Markdown package button remains current behavior.
- DOCX export button must remain disabled until activation gate passes.
- DOCX row should show:
  - Pandoc status and version
  - DOCX preflight status
  - activation status
  - disabled reason
  - planned output path
  - conversion log path

User-visible wording must not imply:

- DOCX already exists
- PDF exists
- renderer detection equals export readiness
- converted document is a clinical report

## Testing Plan

Required focused tests before implementation:

- missing Pandoc blocks DOCX activation without traceback
- full integrated markdown package required
- non-full-integrated package blocked
- missing `integrated_report.md` blocked
- empty markdown blocked
- missing local image reference blocked
- forbidden clinical conclusion wording blocked
- output path is timestamped and non-overwriting
- failed conversion writes failure log and no passed manifest
- successful controlled Pandoc fixture writes `.docx`, log, and rendered export manifest
- rendered export artifact is not written to result index v2 as `formal_computed_result`
- existing markdown-only package remains valid after failed DOCX attempt

Suggested validation commands:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_integrated_report_package.py tests/bioinformatics/test_integrated_report_renderer_gate.py tests/bioinformatics/test_report_renderer_capability.py -q
python3 -m pytest tests/bioinformatics -q -k "integrated or report or renderer"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or settings"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 -m app.main --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_source_b24_3.json
python3 scripts/package_app.py --smoke-test
dist/BioMedPilot.app/Contents/MacOS/BioMedPilot --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_packaged_b24_3.json
open -W -n dist/BioMedPilot.app --args --bio-report-renderer-runtime-check --bio-report-renderer-runtime-check-output /tmp/biomedpilot_report_renderer_runtime_openw_b24_3.json
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

When integration provides a controlled Pandoc runtime, add:

```bash
python3 -m pytest tests/bioinformatics -q -k "docx_renderer_activation or rendered_exports"
```

## Blockers / Risks

### Blocker

- Pandoc runtime is not currently available in this ReleaseBuild environment.

### Major

- Packaging decision is external to Bioinformatics and must be resolved by integration.
- Atomic manifest update and rollback need implementation before user-visible activation.
- DOCX fidelity may vary by Pandoc version and embedded image/table references.

### Minor

- PDF should stay deferred until DOCX output registration is stable.
- Quarto remains detect-only and should not be folded into DOCX MVP.

## Recommendation

Do not implement DOCX conversion execution until integration provides a validated Pandoc runtime.

Recommended next Bioinformatics step while integration works on runtime:

- prepare B24.4 DOCX rendered export manifest skeleton and failure-log writer behind a disabled activation gate, or
- wait for integration runtime evidence and then implement controlled DOCX activation with fixture-based tests.
