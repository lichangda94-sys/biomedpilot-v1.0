# LabTools Module Architecture Alignment 1 Report

Date: 2026-05-14

## Stage name

LabTools Module Architecture Alignment 1 - top-level module entry alignment.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch: `dev/labtools`
- Starting commit: `7625dea Audit LabTools tool usage logic`
- Ending commit: this report's containing commit; see `git log --oneline -5` after commit.

## Scope

This stage changes LabTools from a four-entry tool collection homepage to six larger module entries. It only updates module entry UI, placeholder pages, documentation, and tests.

In scope:

- `app/labtools/**`
- `tests/labtools/**`
- `tests/ui/**`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_module_architecture_alignment_1_report.md`

Out of scope:

- New algorithms.
- New experimental result analysis.
- New image processing logic.
- New persistence schema.
- New export format.
- Large code migration.
- Bioinformatics / Meta / ReleaseBuild / MainLine changes.
- `dist` or desktop app changes.
- Remote push.

## Files changed

- `app/labtools/labtools_home.py`
- `app/labtools/workspace.py`
- `tests/labtools/test_labtools_imports.py`
- `tests/ui/test_labtools_module_architecture.py`
- `tests/ui/test_labtools_status_semantics.py`
- `tests/ui/test_module_selection.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_module_architecture_alignment_1_report.md`

## Audit method

- Re-read the LabTools handoff, schema index, tool logic audit, and current code before editing.
- Verified branch and starting worktree state before applying changes.
- Mapped existing tool surfaces into the new module architecture without moving algorithm implementations.
- Added UI tests for six top-level entries, exact descriptions, planned placeholder wording, and offscreen workspace instantiation.
- Kept backward-compatible route methods for older internal callers while updating current `page_keys()` to the new module structure.

## Key findings

- The old four-entry homepage mixed implemented tools and future experiment-specific tools at the same level.
- General reagent calculations should not permanently carry all experiment-specific calculators.
- Existing result-generating tools still need user logic confirmation before expansion.
- Specialized modules can be introduced as navigation placeholders, but they must say planned / logic pending / not open until their Tool Logic Cards are confirmed.

## Tools requiring user confirmation

- Dilution / mass-molarity / cell seeding calculators.
- qPCR mix calculator.
- WB loading calculator.
- Fluorescence manual ROI.
- Wound / scratch manual ROI + threshold.
- ROI export summary.
- Recipe draft fields, safety category, and import/export semantics.
- Experiment template draft and experiment record draft JSON persistence semantics.

## Tools blocked from direct development

- Absorbance / OD calculation.
- Protein concentration / BCA / Bradford / NanoDrop.
- Wound healing full workflow.
- Transwell assay.
- WB / gel grayscale.
- Cell counting.
- qPCR Delta Delta Ct.
- ELISA standard curve.
- Automatic ROI.
- AI interpretation.
- Formal report-ready result.
- Full ELN.
- Batch image processing.

## Explicit non-goals

- No new algorithm.
- No new experimental result analysis.
- No new image processing logic.
- No new schema.
- No new persistence.
- No new export format.
- No Bioinformatics / Meta / ReleaseBuild / MainLine change.
- No `dist` or desktop app change.
- No remote push.

## Validation results

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`: 163 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 175 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`: 18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed; output included `workspace_entries=3` and `labtools_features=6`
- `python3 -m compileall app/labtools`: passed
- `git diff --check`: passed
- `git diff --cached --check`: passed before commit

## Next recommended discussion topics

- Confirm Tool Logic Cards for current result-generating calculators and manual ROI tools.
- Confirm recipe and experiment record draft field boundaries.
- Decide module ownership for fluorescence manual ROI.
- Start future module discussions in this order: cells, Western Blot, PCR / qPCR, ELISA / absorbance.

## Git status

Pending final validation and commit.
