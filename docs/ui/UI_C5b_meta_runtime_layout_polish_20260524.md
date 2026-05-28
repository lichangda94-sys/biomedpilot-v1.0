# UI-C5b Meta Runtime Layout Polish

Date: 2026-05-24

## 1. Scope

This stage fixes Meta Analysis source-runtime layout issues found in UI-C5 screenshots.

Strictly not performed:

- no Meta executor enablement
- no Pairwise Meta enablement
- no Network Meta enablement
- no Chinese database direct retrieval
- no Chinese PDF extraction
- no formal pooled effect
- no forest plot generation
- no report-ready package
- no export enablement
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no packaging or packaged app run

## 2. Problem From UI-C5

The UI-C5 runtime screenshots showed that Meta Analysis pages had overlapping and compressed target IA navigation/content:

- `meta_project_home.png`
- `meta_question_type.png`
- `meta_search_strategy.png`
- `meta_screening_extraction.png`
- `meta_result_export.png`

Root cause: `app/meta_analysis/workspace.py` placed workflow navigation, shared Result/Report/Export gate, and all runtime page panels into one vertical `metaTargetIAShell`. Page visibility was toggled, but all panels still belonged to one dense layout surface, so offscreen runtime screenshots compressed the navigation and content regions.

## 3. Changes

Runtime layout polish:

- Added a dedicated `metaWorkflowNavigationPanel` for workflow navigation.
- Added a dedicated `metaRuntimeContentPanel` for current page content.
- Added `metaTargetRuntimeStack` so only the selected Meta runtime page occupies the central content area.
- Wrapped runtime pages in scrollable source-runtime containers to avoid cross-page overlap.
- Kept the shared Result / Report / Export adoption panel as a side panel visible only for Result & Report and Report Export.
- Added shell-only / planned boundary panels for `analysis_tasks` and `meta_settings`, preserving page coverage without enabling any executor.
- Preserved legacy `page_keys()` contract and 10 main-flow pages + Meta Settings IA.

No gate semantics changed:

- `Network Meta` remains `planned_disabled`.
- `resultSemanticKey` remains non-formal.
- `reportStatusKey` remains draft / not ready.
- `exportGate` remains disabled.
- Export buttons remain disabled.

## 4. Focused Test Coverage

Added:

- `tests/ui/test_meta_analysis_runtime_layout_polish.py`

Coverage:

- `metaWorkflowNavigationPanel`, `metaRuntimeContentPanel`, and `metaTargetRuntimeStack` exist.
- Layout panels carry `layoutPolishNoOverlap=true`.
- Every target IA page switches through the single runtime stack.
- Result/report/export gate remains disabled.
- Network Meta remains disabled.

## 5. Updated Screenshots

New screenshots:

- `docs/ui/runtime_screenshots/20260524_c5b_meta_polish/meta_project_home.png`
- `docs/ui/runtime_screenshots/20260524_c5b_meta_polish/meta_question_type.png`
- `docs/ui/runtime_screenshots/20260524_c5b_meta_polish/meta_search_strategy.png`
- `docs/ui/runtime_screenshots/20260524_c5b_meta_polish/meta_screening_extraction.png`
- `docs/ui/runtime_screenshots/20260524_c5b_meta_polish/meta_result_export.png`

All five screenshots are `1600 x 1000`, non-empty PNG files.

## 6. Review Notes

Improved:

- Target IA navigation no longer overlaps the active page content.
- Question & Type page now uses a readable central content panel.
- Report Export page now separates workflow navigation, export gate content, and shared RRE side panel.
- Project Home / Search Strategy / Extraction pages render as one current page instead of sharing vertical space with other hidden runtime panels.

Remaining future polish:

- The legacy mainline compatibility panel still appears below the runtime shell. It is intentionally preserved for contract compatibility, but could be collapsed in a future polish stage if product review prefers a pure target-IA view.
- Some tables still use native Qt table styling and should be refined in a later visual polish pass.
- The shared Result / Report / Export side panel is functionally gated but visually dense in the narrow right column.

## 7. Verification

Commands/checks run:

- `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_meta_analysis_project_question_gated_pages.py tests/ui/test_meta_analysis_search_reference_gated_pages.py tests/ui/test_meta_analysis_screening_extraction_rob_gated_pages.py tests/ui/test_meta_analysis_result_report_export_gates.py tests/ui/test_meta_analysis_runtime_layout_polish.py`
  - Result: 28 passed
- C5b screenshot existence and size check
  - Result: 5 screenshots present, all `1600 x 1000`, non-empty
- `python3 -m app.main --smoke-test`
  - Result: passed

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
