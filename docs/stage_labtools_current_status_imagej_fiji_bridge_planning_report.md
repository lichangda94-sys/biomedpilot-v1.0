# LabTools Current Status + ImageJ/Fiji Bridge Planning Report

Date: 2026-05-14

## Stage name

LabTools Current Status + ImageJ/Fiji Bridge Planning.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch: `dev/labtools`
- Starting commit: `bf8cd6a Remove legacy LabTools WB loading calculator entry`
- Ending commit: this report's containing commit; see `git log --oneline -5` after commit.

## Scope

This stage is documentation-only unless existing status wording still implies self-developed image algorithms. No code changes were required at report creation time.

In scope:

- `docs/labtools_current_handoff.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_current_status_imagej_fiji_bridge_planning_report.md`

## Current completed LabTools status

Completed / available as Developer Preview or testing-level assistance:

- General calculators: concentration conversion, C1V1 dilution, solution preparation, mass / molarity, cell seeding, qPCR mix.
- Reagent and records: recipe draft store, recipe JSON import/export, safety category, conflict import behavior, experiment template draft, experiment record draft JSON persistence.
- Image assistance legacy MVPs: fluorescence manual ROI, wound / scratch manual ROI + threshold, ROI export package.
- Western Blot: SDS-PAGE user-entered gel template batch calculator, Protein Loading v1, BCA Assay v1.

Not completed:

- Automatic ROI.
- Automatic cell counting.
- WB / gel grayscale.
- Batch image processing.
- AI interpretation.
- Bradford / NanoDrop.
- ELISA standard curve.
- 4PL.
- qPCR Delta Delta Ct.
- Complete ELN or formal report-ready output.

## Image backend decision

Future image analysis backend direction is Fiji/ImageJ macro bridge.

Current Python/Pillow fluorescence and wound ROI tools remain legacy/testing manual-review MVPs. They are not the preferred expansion path for future image tools.

For future image tools, LabTools should own:

- UI parameter collection.
- Macro template selection.
- Input and output path validation.
- Dry-run / preview text.
- Local process execution feedback.
- Result file parsing.
- Provenance and review notices.
- No-overwrite export behavior.

Fiji/ImageJ macros should own image quantification logic.

## Next stage: ImageJ/Fiji Bridge v1

Recommended next stage:

- Build local Fiji/ImageJ executable discovery or user-selected executable path handling.
- Define macro template folder and macro metadata format.
- Define parameter serialization from LabTools to macro variables.
- Run a local macro against a controlled test fixture.
- Parse result files into JSON-compatible structures.
- Preserve manual-review / testing semantics.
- Add timeout, cancellation, missing executable, macro failure, and output-missing error handling.
- Add tests that do not require real biological image interpretation.

Explicit next-stage non-goals:

- No automatic cell counting.
- No WB / gel grayscale quantification.
- No automatic ROI.
- No batch workflow.
- No AI interpretation.
- No formal report-ready result.
- No remote/network execution.

## Explicit non-goals in this stage

- No code changes.
- No new image algorithm.
- No Fiji/ImageJ runtime integration.
- No macro execution.
- No persistence schema.
- No export format.
- No UI feature expansion.
- No Bioinformatics / Meta / ReleaseBuild / MainLine change.
- No `dist` or desktop app package change.
- No remote push.

## Validation results

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`: 191 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 192 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`: 18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed; output included `git_head=bf8cd6a`, `workspace_entries=3`, `labtools_features=6`
- `python3 -m compileall app/labtools`: passed
- `git diff --check`: passed
- `git diff --cached --check`: passed before commit

## Git status

Pending final commit.
