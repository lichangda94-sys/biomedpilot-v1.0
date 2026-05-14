# LabTools ImageJ/Fiji Bridge v1 Report

Date: 2026-05-14

## Stage name

LabTools ImageJ/Fiji Bridge v1.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch: `dev/labtools`
- Starting commit: `b632b17 Document LabTools ImageJ Fiji bridge direction`
- Ending commit: this report's containing commit; see `git log --oneline -5` after commit.

## Scope

Implemented local Fiji/ImageJ bridge infrastructure only.

In scope:

- External Fiji/ImageJ executable path configuration.
- Common local path probing.
- Version detection best effort.
- Macro smoke test through a temporary `.ijm` file.
- Local configuration JSON.
- LabTools settings UI entry and status display.
- Tests and documentation.

## Files changed

- `app/labtools/imagej_bridge.py`
- `app/labtools/ui/imagej_bridge_widgets.py`
- `app/labtools/workspace.py`
- `tests/labtools/test_imagej_bridge.py`
- `tests/labtools/test_labtools_imports.py`
- `tests/ui/test_labtools_imagej_bridge_ui.py`
- `tests/ui/test_labtools_module_architecture.py`
- `tests/ui/test_module_selection.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_imagej_fiji_bridge_v1_report.md`

## Bridge design

The first version uses an external Fiji/ImageJ executable plus a BioMedPilot bridge and ImageJ macro automation.

LabTools owns:

- User-triggered path configuration.
- Common path detection.
- Executable resolution for `.app` bundles and direct executable paths.
- Version detection best effort.
- Temporary macro generation.
- Subprocess execution with timeout handling.
- Smoke-test result parsing.
- UI status and readable errors.

The bridge writes temporary smoke-test files under `tempfile` only during validation and does not write test outputs into the repository, `dist`, or the desktop app package.

## Recommended version policy

- Recommended backend: Fiji Stable / Java 8.
- Other versions are not rejected only because of version text.
- If version parsing fails, the bridge records `unknown_version` and still runs the smoke test.
- If smoke test passes with an unknown or non-recommended version, the UI marks the backend callable but not version-verified.
- If smoke test fails, status becomes `failed` with a readable Chinese error summary.

## Configuration schema

Added local configuration schema: `labtools_imagej_bridge_config.v1`.

Fields:

- `schema_version`
- `backend_type`
- `recommended_backend`
- `configured_path`
- `detected_version`
- `java_version`
- `status`
- `last_smoke_test_at`
- `last_smoke_test_result`
- `last_error`
- `updated_at`

Status values:

- `not_configured`
- `configured_unverified`
- `available`
- `failed`

This is a local configuration schema, not an image analysis result schema.

## Smoke test behavior

The bridge creates a temporary ImageJ macro that creates a small test image and writes `status=ok` to `smoke_test_result.csv`.

Success requires:

- Fiji/ImageJ process exits successfully.
- The output file exists.
- The output file contains `status=ok`.

Failure cases produce `failed` status:

- Missing or non-executable path.
- `.app` bundle without a recognized executable.
- Subprocess timeout.
- Process launch failure.
- Non-zero process exit.
- Missing output file.
- Output missing `status=ok`.

## UI behavior

LabTools now has an `ImageJ/Fiji 后端设置` entry in the LabTools workspace header.

The page shows:

- Current status.
- Recommended backend wording.
- Current configured path.
- Detected ImageJ/Fiji version.
- Java version.
- Recent validation time.
- Recent error summary.
- Buttons for auto-detect, choose path, run validation, show official download addresses, and clear config.

The page explicitly states that BioMedPilot does not bundle Fiji/ImageJ and that future image analysis will use user-configured Fiji/ImageJ plus macro automation with manual review.

## Explicit non-goals

- No WB/gel grayscale.
- No fluorescence automated analysis.
- No wound automated analysis.
- No cell counting.
- No automatic ROI.
- No batch image processing.
- No OpenCV or scikit-image.
- No PyImageJ.
- No automatic Fiji/ImageJ download.
- No bundled Fiji/ImageJ runtime.
- No network installer.
- No Bioinformatics / Meta / ReleaseBuild / MainLine changes.
- No `dist` or desktop app package changes.
- No remote push.

## Validation results

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`: 200 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 196 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`: 18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed; output included `git_head=b632b17`, `workspace_entries=3`, `labtools_features=6`
- `python3 -m compileall app/labtools`: passed
- `git diff --check`: passed
- `git diff --cached --check`: passed before commit

## Known limitations

- The bridge does not include macro templates for concrete image workflows.
- The bridge does not parse analysis output tables beyond the smoke-test status file.
- Version detection is best effort because Fiji/ImageJ command-line output varies across installations.
- Tests use fake executables and mock subprocess behavior; they do not require a real Fiji installation.

## Next recommended stage

ImageJ/Fiji macro workflow Tool Logic Card for the first concrete image tool, before implementing analysis logic. The card should define input images, parameters, macro provenance, output fields, warnings, result semantics, export behavior, and manual-review wording.

## Git status

Pending final commit at report update time.
