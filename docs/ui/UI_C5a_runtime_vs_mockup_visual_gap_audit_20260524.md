# UI-C5a Runtime vs Mockup Visual Gap Audit

Date: 2026-05-24

## 1. Scope

This audit compares source-runtime PySide screenshots in `docs/ui/runtime_screenshots/20260524/` against the approved high-fidelity mockups under `/Users/changdali/Desktop/UI/界面示意图/`.

This stage is documentation-only. It does not modify runtime UI, package the app, run the packaged app, modify `dist/**`, or touch App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices.

## 2. Overall Finding

The current runtime UI is functionally gated and safer than earlier shells, but the visual gap versus the mockups is still too large for UI-B10 visual sign-off.

The gap is not mainly color or icon polish. It is structural:

- Runtime pages use native Qt widgets and ad hoc layouts where mockups expect a stable workbench shell.
- Most pages lack a consistent module-local secondary navigation, main content area, right gate/summary panel, and bottom action bar.
- Tables, status chips, review notices, disabled/gated buttons, and cards are implemented repeatedly with inconsistent spacing and density.
- Dense pages such as LabTools Reagent/WB, Bioinformatics Analysis/Export, Meta original C5 pages, and Settings should not be patched in place. They need a layout skeleton rebuild.

## 3. Baseline and Prior Local Fix

Audit baseline:

- `docs/ui/runtime_screenshots/20260524/`

Important note:

- `UI-C5b Meta runtime layout polish` already exists as commit `ed726b6`.
- Its screenshots live in `docs/ui/runtime_screenshots/20260524_c5b_meta_polish/`.
- That stage reduced Meta navigation/content overlap, but it is a local repair. It does not replace the broader C5a conclusion that unified workbench primitives are needed before final UI-B10 review.

## 4. Severity Summary

Most severe visual gaps:

1. `settings_home`
   - Looks like diagnostic inventory rather than a user settings page.
   - Needs a settings hierarchy rebuild.
2. `labtools_reagent_preparation`
   - Runtime overflows horizontally and compresses three work areas.
   - Needs a Reagent workbench skeleton.
3. `labtools_wb_loading`
   - Runtime is dense and clipped; lane preview and warning/results compete for space.
   - Needs a focused WB skeleton.
4. Original C5 Meta screenshots
   - Severe target IA/content overlap before the C5b local fix.
   - Needs primitives-based rebuild, not more local stacking patches.
5. `bioinformatics_result_export`
   - Too diagnostic-heavy and contains enabled open-report-file/folder affordances while gates are disabled.
   - Needs export-gate affordance and layout polish.

## 5. Classification

### A. Pages Suitable for Local Polish

- Dashboard
- LabTools Home
- LabTools Experiment Boundaries
- Bioinformatics Project Home
- Bioinformatics Data Source

These have acceptable navigation and safety semantics. They still need shared card/chip/button styling, but their layout skeletons are not the main blocker.

### B. Pages Needing Layout Skeleton Rebuild

- LabTools Reagent Preparation
- LabTools WB Loading
- Meta original C5 target pages
- Bioinformatics Analysis Tasks
- Bioinformatics Result / Report / Export
- Settings

These pages should not continue to accumulate patch-level layout fixes. The mockup intent requires explicit layout regions and stable proportions.

### C. Pages Needing Shared Components First

All workbench-like pages should consume shared layout primitives before further visual polish, especially pages with:

- module-local secondary navigation
- main content and right inspector/gate panel
- status chip rows
- dense tables
- warning/review notices
- disabled/gated action bars

The affected families are Meta, LabTools, Bioinformatics, and Settings.

### D. Why UI-B10 Should Not Proceed

UI-B10 is still blocked from a visual readiness perspective because:

- Runtime UI still diverges materially from high-fidelity mockups.
- Several first-viewports are too dense or clipped.
- Settings is not user-oriented enough.
- Bioinformatics export has potentially misleading enabled affordances.
- Meta has only had a local overlap fix, not a full workbench rebuild.
- App icon and packaging work would not solve these runtime UI gaps.

## 6. Required Follow-up Sequence

Fixed order:

1. `UI-C5b Workbench layout primitives refactor`
2. `UI-C5c Meta layout rebuild`
3. `UI-C5d LabTools dense page layout rebuild`
4. `UI-C5e Bioinformatics affordance/layout polish`
5. `UI-C5f Settings hierarchy polish`
6. `UI-C5g Runtime screenshot re-review`

No stage should enable executor, formal result, report-ready package, export, packaging, App icon, Finder icon, Info.plist, LaunchServices, or desktop app overwrite.

## 7. Verification

Checks for this audit:

- Runtime screenshot paths exist.
- Mockup reference paths exist.
- `docs/ui/UI_C5a_runtime_visual_gap_matrix_20260524.csv` has the required fixed fields.
- `git diff --check`
- `git diff --cached --check`

No packaged app, package smoke, signing, `dist/**`, or LaunchServices work was performed.
