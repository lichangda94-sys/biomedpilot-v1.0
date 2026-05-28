# UI-B8b4c-2 P1 Meta Analysis Page Icon Active Replacement Pilot

## 1. Scope

This stage connects only the 10 P1 `meta_pages` production candidate icons from `docs/ui/icon_production/p1/` into the active UI as a pilot.

In scope:

- `meta_page_project_home`
- `meta_page_question_meta_type`
- `meta_page_search_strategy`
- `meta_page_import_deduplication`
- `meta_page_screening`
- `meta_page_fulltext_extraction`
- `meta_page_quality_assessment`
- `meta_page_analysis_tasks`
- `meta_page_result_report`
- `meta_page_report_export`

Out of scope:

- Bioinformatics page icons except prior manifest consistency checks
- status icons
- settings resource icons
- result/report/export icons
- empty states
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices
- packaging, packaged app runtime, desktop app replacement

## 2. Active Asset Additions

Added active pilot files under:

- `assets/icons/meta/pages/`

Each of the 10 Meta page icons now has:

- one SVG active pilot asset
- PNG exports at 24, 32, 48, and 64 px

No active asset was added under App icon, status, settings resource, result/report/export, empty state, Bioinformatics, or LabTools directories during this stage.

## 3. Registry And Loader

Updated `app/app_identity.py` with:

- `META_PAGE_ICON_DIR`
- `META_PAGE_ICON_PATHS`
- 10 Meta page `IconAssetSlot` entries
- `load_meta_page_icon`
- `load_meta_page_pixmap`

The registry is keyed by stable `PageKey` semantic values. It does not use absolute paths and returns an empty `QIcon` when the file is absent or the key is unknown.

## 4. UI Wiring

Updated `app/meta_analysis/workspace.py` so Meta target IA navigation buttons use the new page icon loader.

Preserved button properties:

- `pageKey`
- `moduleKey`
- `semanticKey`
- `statusKey`
- `statusSemanticKey`
- `interactionMode`
- `formalActionEnabled`

Fallback behavior:

- If an icon is missing, the text label remains visible.
- Page navigation remains available.
- `formalActionEnabled` remains `false`.
- `iconFallback=true` records the fallback state.

The existing `meta_settings` auxiliary page has no P1 icon in this batch and remains on fallback. No page was added to force a one-to-one icon count.

## 5. IA And Gate Boundaries

Meta Analysis target IA remains unchanged:

- 10 main-flow pages
- 1 auxiliary `meta_settings` page
- 10 active Meta type cards
- Network Meta remains disabled/planned only
- Search, screening, extraction, quality assessment, analysis tasks, result review, and report/export semantics remain shell/testing/planned/draft as before

This stage does not enable:

- a new Meta analysis executor
- Chinese database direct search
- Chinese PDF extraction
- production-grade systematic review output
- formal report-ready package generation

## 6. Pilot Manifest

Generated:

- `docs/ui/UI_B8b4c_2_p1_meta_page_icon_active_pilot_manifest_20260521.csv`

Manifest state:

- 31 P1 rows total
- 10 `meta_pages` rows marked `active_pilot=true`
- 21 prior P1 rows for modules, LabTools, and Bioinformatics marked `prior_active_pilot=true`
- no non-P1 families marked active
- replacement state remains `pilot_only`

## 7. Focused Tests

Added:

- `tests/ui/test_p1_meta_page_icon_active_pilot.py`

Coverage:

- 10 Meta page active assets exist and are registered
- loader fallback is safe for unknown keys and `meta_settings`
- Meta target IA nav renders active icons for the 10 P1 pages
- `meta_settings` remains fallback
- Meta IA page list remains unchanged
- Network Meta and formal gates remain disabled
- manifest marks only `meta_pages` as this stage active pilot
- Bio/status/settings/result/export/empty/App icon assets are not copied into Meta page active assets

## 8. Verification

Commands run:

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_p1_meta_page_icon_active_pilot.py` | Passed: 7 passed |
| `python3 -m pytest -q tests/ui/test_icon_resource_readiness_inventory.py tests/ui/test_p1_icon_production_manifest.py tests/ui/test_p1_module_icon_active_pilot.py tests/ui/test_p1_labtools_icon_active_pilot.py` | Passed: 24 passed |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py` | Passed: 23 passed |
| `python3 -m pytest -q tests/ui/test_p1_bio_page_icon_active_pilot.py` | Passed: 7 passed |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | Passed: 8 passed |
| `python3 -m app.main --smoke-test` | Passed |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |

## 9. Boundary Confirmation

This stage did not:

- modify packaged app output
- run packaged app
- run package smoke
- codesign
- modify `dist/**`
- modify desktop entry files
- touch App icon, Finder icon, `.icns`, iconset, Info.plist, or LaunchServices
- change Bioinformatics page icons
- change status, settings resource, result/report/export, or empty-state icon families
- change Meta Analysis business logic, execution gates, report-ready states, or analysis semantics
