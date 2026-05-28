# UI-C5d LabTools Dense Page Layout Rebuild

Date: 2026-05-25

## 1. Scope

This stage rebuilds the dense LabTools runtime page skeletons identified by UI-C5a, with focus on Reagent Preparation and WB Loading. It does not change LabTools backend logic, calculator behavior, storage behavior, export behavior, or history behavior.

Strictly not performed:

- no new LabTools backend feature
- no new save/history scope
- no new export scope
- no Quick Calculator history enablement
- no BCA / Cell / ELISA / Image Processing save or export enablement
- no PDF / DOCX enablement
- no default write to `~/.labtools`
- no package smoke or packaged app run
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work

## 2. Layout Changes

### Reagent Preparation

The runtime page previously used four horizontal columns:

- template list
- local reagent reference
- preparation run
- template detail side panel

This created horizontal pressure in the 1600 x 1000 screenshot viewport. The page now uses a safer three-column skeleton:

- `labtoolsReagentLeftColumn`: template list + local reagent reference stacked vertically
- `labtoolsReagentRunPanel`: central preparation calculation preview
- `labtoolsReagentDetailPanel`: right template detail / editor panel

The left column carries:

- `uiPrimitive=workbench_secondary_column`
- `layoutPolishNoOverlap=true`

### WB Loading

The runtime page previously used four horizontal columns:

- WB configuration
- local sample panel
- sample/result table
- lane preview

This created horizontal clipping. The page now uses a safer three-column skeleton:

- `labtoolsWbLeftColumn`: WB configuration + local sample panel stacked vertically
- `labtoolsWbSampleResultPanel`: central sample and calculation result panel
- `labtoolsWbLanePreviewPanel`: right lane preview panel

The left column carries:

- `uiPrimitive=workbench_secondary_column`
- `layoutPolishNoOverlap=true`

## 3. Preserved Boundaries

- Reagent Template / Preparation save remains gated by project storage context.
- Reagent Markdown / CSV export still requires the file picker.
- WB save/history remains gated by project storage context.
- WB Markdown / CSV export still requires the file picker.
- PDF / DOCX buttons remain disabled.
- WB still does not provide SDS-PAGE calculation, image analysis, automatic band detection, antibody recommendation, or complete WB protocol.
- BCA / OD, Cell, ELISA, and Image Processing remain boundary pages or disabled scopes.

## 4. Screenshots

New source-runtime screenshots were captured under:

- `docs/ui/runtime_screenshots/20260525_c5d_labtools_layout_rebuild/labtools_home.png`
- `docs/ui/runtime_screenshots/20260525_c5d_labtools_layout_rebuild/labtools_general_calculator.png`
- `docs/ui/runtime_screenshots/20260525_c5d_labtools_layout_rebuild/labtools_reagent_preparation.png`
- `docs/ui/runtime_screenshots/20260525_c5d_labtools_layout_rebuild/labtools_wb_loading.png`
- `docs/ui/runtime_screenshots/20260525_c5d_labtools_layout_rebuild/labtools_experiment_boundaries.png`

All five screenshots are `1600 x 1000`, non-empty PNG files.

## 5. Verification

Commands/checks run:

- `python3 -m pytest -q tests/ui/test_labtools_reagent_preparation_ui.py tests/ui/test_labtools_wb_loading_ui.py tests/ui/test_labtools_general_calculator_ui.py tests/ui/test_labtools_boundary_pages.py tests/ui/test_labtools_navigation_shell.py tests/ui/test_labtools_shell.py`
  - Result: 35 passed
- `python3 -m app.main --smoke-test`
  - Result: passed
- LabTools screenshot generation
  - Result: 5 non-empty PNG files created

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
