# LabTools Tool Logic Audit 1 Report

Date: 2026-05-14

## Stage name

LabTools Tool Logic Audit 1 - tool usage logic and result semantics retrospective.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch: `dev/labtools`
- Starting commit: `599185f docs(labtools): add retrospective tool logic audit`
- Ending commit: this report's containing commit; see `git log --oneline -5` after commit.

## Scope

This stage pauses feature development and audits current LabTools tool usage logic. It only updates documentation and adds a documentation coverage test.

In scope:

- `docs/labtools_tool_logic_audit.md`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/stage_labtools_tool_logic_audit_1_report.md`
- `tests/labtools/test_labtools_tool_logic_audit.py`

Out of scope:

- New tools.
- New algorithms.
- New image processing logic.
- New calculation formulas.
- New persistence schema.
- New export formats.
- Bioinformatics / Meta / ReleaseBuild / MainLine changes.
- `dist` or desktop app package changes.
- Remote push.

## Files changed

- `docs/labtools_tool_logic_audit.md`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/stage_labtools_tool_logic_audit_1_report.md`
- `tests/labtools/test_labtools_tool_logic_audit.py`

## Audit method

The audit reviewed current LabTools implementation files, UI wording, schema index, stage reports, and tests against the requested tool inventory. Each tool now has an audit record containing:

- `tool_id`
- `tool_name`
- `tool_category`
- `current_status`
- `implemented_files`
- `test_files`
- `does_generate_result`
- `does_write_to_disk`
- `current_inputs`
- `current_user_workflow`
- `current_outputs`
- `current_result_meaning`
- `review_level`
- `known_failure_cases`
- `user_logic_confirmed`
- `risk_level`
- `needs_user_discussion`
- `needs_code整改`
- `recommended_next_action`

## Key findings

- No blocking mismatch was found between UI, docs, and code for current tool status.
- Implemented calculators and manual ROI tools generate useful local draft results, but their formula semantics, units, and result fields should be user-confirmed before expansion.
- Recipe draft and experiment record draft workflows correctly remain draft/manual-review flows, but their field sets and safety language should be user-confirmed before adding richer templates.
- Planned tools remain placeholder-only and must not be developed directly without a Tool Logic Card.

## Tools requiring user confirmation

- Dilution calculator.
- Mass / molarity calculator.
- Cell seeding calculator.
- qPCR mix calculator.
- WB loading calculator.
- Fluorescence manual ROI.
- Wound / scratch manual ROI + threshold.
- ROI export result summary.
- Recipe draft fields, safety category, import/export semantics.
- Experiment template draft and experiment record draft fields.

## Tools blocked from direct development

These require future Tool Logic Cards before implementation:

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

- No new tool.
- No new algorithm.
- No new image processing logic.
- No new calculation formula.
- No new persistence schema.
- No new export format.
- No Bioinformatics / Meta / ReleaseBuild / MainLine change.
- No `dist` or desktop app package change.
- No remote push.

## Validation results

- `python3 -m pytest tests/labtools/test_labtools_tool_logic_audit.py -q`: 4 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`: 163 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 169 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`: 18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed; output included `workspace_entries=3` and `labtools_features=4`
- `python3 -m compileall app/labtools`: passed
- `git diff --check`: passed
- `git diff --cached --check`: passed before commit

## Next recommended discussion topics

Priority 1:

- Dilution / mass-molarity / cell seeding calculators.
- Fluorescence manual ROI.
- Wound manual ROI + threshold.
- ROI export summary.

Priority 2:

- Recipe draft.
- Experiment record draft.

Priority 3:

- Absorbance / OD calculation.
- Protein concentration.
- Wound healing full workflow.
- Transwell assay.
- WB / gel grayscale.
- Cell counting.
- qPCR Delta Delta Ct.
- ELISA standard curve.

## Git status

Pending final commit.
