# Western Blot Protein Loading + BCA Assay v1 Report

Date: 2026-05-14

## Stage name

Western Blot Protein Loading + BCA Assay v1.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch: `dev/labtools`
- Starting commit: `a055f78 Add LabTools SDS-PAGE gel template tool`
- Ending commit: this report's containing commit; see `git log --oneline -5` after commit.

## Scope

This stage implements two confirmed Western Blot tools:

- Protein loading calculator.
- BCA protein concentration assay v1.

In scope:

- `app/labtools/western_blot/**`
- `app/labtools/ui/western_blot_widgets.py`
- `app/labtools/workspace.py`
- `tests/labtools/**`
- `tests/ui/**`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`

## Files changed

- `app/labtools/western_blot/__init__.py`
- `app/labtools/western_blot/protein_loading.py`
- `app/labtools/western_blot/bca_assay.py`
- `app/labtools/ui/western_blot_widgets.py`
- `app/labtools/workspace.py`
- `tests/labtools/test_western_blot_protein_loading.py`
- `tests/labtools/test_bca_assay.py`
- `tests/ui/test_labtools_western_blot_loading_bca_ui.py`
- `tests/ui/test_labtools_western_blot_scaffold.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_western_blot_loading_bca_v1_report.md`

## Protein loading implementation

- Adds a pure Python service layer in `protein_loading.py`.
- Supports multi-sample input.
- Supports concentration units: `µg/µL`, `ug/uL`, `mg/mL`, `µg/mL`, `ug/mL`.
- Treats `µg/µL` and `mg/mL` as equivalent.
- Calculates:
  - loading buffer volume = final loading volume × target final concentration ÷ loading buffer multiple.
  - protein sample volume = target protein amount ÷ sample concentration.
  - water volume = final loading volume - protein sample volume - loading buffer volume.
- Applies default 3% overage to total component volumes.
- Returns Chinese user-facing errors and warnings for invalid inputs, impossible final volume, and small pipetting volumes.
- Provides copyable result text with input summary, sample results, totals, warnings, reducing agent notice, and manual-review notice.

## BCA implementation

- Adds a pure Python service layer in `bca_assay.py`.
- Supports 8×12 OD matrix parsing from plain numeric matrix, A-H row names, 1-12 column headers, and tab / Excel style paste.
- Supports Blank / Standard / Sample / Unused well annotations.
- Supports rectangular batch annotation ranges.
- Supports optional blank subtraction only when enabled by the user.
- Uses all valid Blank wells to compute blank mean when subtraction is enabled.
- Warns, but does not auto-subtract, when no Blank is marked and a 0 concentration standard exists.
- Implements linear fit only: `OD = slope × concentration + intercept`.
- Uses standard concentration group means for fitting.
- Calculates sample measured concentration and dilution-corrected original sample concentration.
- Produces Plate Raw Data, Standard Curve, and Sample Results structures.
- Issues warnings for insufficient standards, invalid slope, R² < 0.98, CV% > 15%, out-of-range samples, blank-corrected OD < 0, negative calculated concentration, missing/non-numeric/negative/unusually high OD.
- Does not automatically delete outlier wells.
- Provides copyable summary text with blank state, curve formula, R², sample results, warnings, and manual-review notice.

## Explicit non-goals

- No WB/gel grayscale.
- No band ROI.
- No background subtraction for WB bands.
- No target/loading control ratio.
- No Bradford.
- No NanoDrop.
- No ELISA standard curve.
- No 4PL.
- No plate layout template save.
- No XLSX export.
- No AI or network.
- No database or autosave.
- No Bioinformatics / Meta / ReleaseBuild / MainLine change.
- No `dist` or desktop app package change.
- No remote push.

## Validation results

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`: 191 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 192 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`: 18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed; output included `git_head=a055f78`, `workspace_entries=3`, `labtools_features=6`
- `python3 -m compileall app/labtools`: passed
- `git diff --check`: passed
- `git diff --cached --check`: passed before commit

## Known limitations

- BCA v1 uses linear fitting only.
- BCA v1 does not save plate layout templates.
- BCA v1 does not export `.xlsx`.
- BCA v1 flags unusual wells but does not remove them from analysis automatically.
- Protein loading v1 assumes reducer handling is outside this calculator and prompts the user to confirm loading buffer contents.
- The older general calculator WB loading surface remains present; the new Western Blot protein loading tool is the module-scoped implementation.

## Next recommended stage

- Discuss whether the older general calculator WB loading surface should be deprecated, redirected, or kept as a compatibility entry.
- Create separate Tool Logic Cards before BCA 4PL, Bradford, NanoDrop, ELISA standard curves, WB/gel grayscale, band ROI, background subtraction, target/loading control ratio, plate layout persistence, or export formats.

## Git status

Pending final commit at report update time.
