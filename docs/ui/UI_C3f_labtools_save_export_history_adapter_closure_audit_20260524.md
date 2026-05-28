# UI-C3f LabTools Save / Export / History Adapter Closure Audit

## 1. Scope

This closure audit covers the LabTools adapter track from UI-C3c through UI-C3e:

- UI-C3c: `edfa2a5 feat(ui): add LabTools storage adapter skeleton`
- UI-C3d: `85fcdf4 feat(ui): pilot LabTools reagent and WB history storage`
- UI-C3e: `82de31d feat(ui): pilot LabTools file picker exports`

This audit is documentation-only. It does not modify runtime UI, business logic, tests, assets, scripts, packaging, `dist/**`, App icon, Finder icon, Info.plist, LaunchServices, or packaged app behavior.

## 2. Closure Decision

Decision: `closed_with_scope_guardrails`

The LabTools save/export/history adapter pilot is closed for the currently approved pilot scope:

- Save/history is limited to Reagent Template, Reagent Preparation, and WB Loading.
- File export is limited to Reagent Preparation and WB Loading, and only Markdown / CSV.
- Quick Calculator, Dynamic Formula Solver, BCA / OD, Cell Experiment, ELISA / Immuno-Absorbance, and Image Processing remain disabled or boundary-only for persistence/export.
- PDF and DOCX remain disabled.
- All normal file exports use a file picker path.
- The runtime explicitly rejects `~/.labtools` export writes.
- No packaged app, App icon, Finder icon, Info.plist, LaunchServices, or desktop entry work occurred in this track.

## 3. Save / History Scope

| Area | Runtime status | Write location | Closure result |
| --- | --- | --- | --- |
| Reagent Template | pilot save enabled only with LabTools project context | `project_storage/labtools/templates/reagent_templates.json` | closed |
| Reagent Preparation | pilot record save enabled only with LabTools project context | `project_storage/labtools/records/reagent_preparations.json` | closed |
| WB Loading | pilot record save enabled only with LabTools project context | `project_storage/labtools/records/wb_loading_records.json` | closed |
| Quick Calculator / Formula Solver | save history disabled | none | guarded |
| BCA / OD | save disabled / boundary-only | none | guarded |
| Cell Experiment | save disabled / backend missing | none | guarded |
| ELISA / Immuno-Absorbance | save disabled / backend missing | none | guarded |
| Image Processing | save disabled / external engine adapter missing | none | guarded |

The active save pilot requires `MainWindow.set_labtools_project_root(...)` or a future equivalent project-context binding. Without project context, save/history buttons remain disabled with `disabled_missing_storage_adapter`.

## 4. Export Scope

| Area | Allowed export formats | Export path source | Closure result |
| --- | --- | --- | --- |
| Reagent Preparation | Markdown, CSV | `QFileDialog.getSaveFileName` | closed |
| WB Loading | Markdown, CSV | `QFileDialog.getSaveFileName` | closed |
| Quick Calculator / Formula Solver | none | none | guarded |
| BCA / OD | none | none | guarded |
| Cell Experiment | none | none | guarded |
| ELISA / Immuno-Absorbance | none | none | guarded |
| Image Processing | none | none | guarded |
| PDF / DOCX | none | none | guarded |

The legacy disabled export buttons remain present for PDF / DOCX future state and continue to use `disabledState=future`. They do not write files.

## 5. File Picker Requirement

Runtime export entry points in `app/shell/main_window.py` call `_choose_labtools_export_path(...)`, which uses `QFileDialog.getSaveFileName(...)`.

Focused tests monkeypatch `QFileDialog.getSaveFileName` to provide temp paths. This keeps tests deterministic while preserving the file-picker contract. No Reagent or WB export path is hard-coded to the Desktop, repo root, `dist/**`, or `~/.labtools`.

## 6. No ~/.labtools Write Boundary

The C3f audit confirms two layers:

- Storage adapter paths resolve under `project_storage/labtools/**`.
- Export writer rejects any resolved path under `Path.home() / ".labtools"`.

The tests cover:

- Reagent save does not create `~/.labtools`.
- WB save does not create `~/.labtools`.
- Reagent/WB file picker exports do not create `~/.labtools`.
- Direct export writer call to `~/.labtools` is rejected.

## 7. Disabled Surfaces

The following surfaces remain disabled and out of this adapter pilot:

- Quick Calculator history and export.
- Dynamic Formula Solver history and export.
- BCA / OD save and export.
- Cell Experiment save and export.
- ELISA save, analysis, report, and export.
- Image Processing run/save/export.
- PDF / DOCX export.
- Formal report package export.
- Any export that bypasses a file picker.

## 8. Business Logic Boundary

No new LabTools backend business logic was introduced in this adapter closure:

- Reagent preparation continues to use existing preview calculation.
- WB Loading continues to use existing focused calculation preview.
- BCA, Cell, ELISA, and Image Processing remain boundary pages.
- No ImageJ/Fiji runner was enabled.
- No PDF/DOCX/report package writer was enabled.

## 9. Packaging / Desktop Boundary

This track did not touch:

- packaged app
- package smoke
- App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices
- `dist/**`
- desktop `.app`
- desktop entry replacement

## 10. Runtime Status Matrix

See `docs/ui/UI_C3f_labtools_save_export_history_runtime_status_matrix_20260524.csv`.

## 11. Verification

Commands run for this closure audit:

- `python3 -m pytest -q tests/ui/test_labtools_storage_adapter.py tests/ui/test_labtools_reagent_save_history_pilot.py tests/ui/test_labtools_wb_save_history_pilot.py tests/ui/test_labtools_file_picker_export_pilot.py`
- `python3 -m pytest -q tests/ui/test_labtools_reagent_preparation_ui.py tests/ui/test_labtools_wb_loading_ui.py tests/ui/test_labtools_general_calculator_ui.py tests/ui/test_labtools_boundary_pages.py`
- `python3 -m app.main --smoke-test`
- `git diff --check`
- `git diff --cached --check`

Result: all verification commands passed in UI-C3f.

## 12. Next Stage Recommendation

Recommended next stage: UI-C3g LabTools adapter pilot runtime screenshot review or UI-C3h adapter error-state hardening.

Do not proceed to PDF/DOCX, formal report package, BCA/Cell/ELISA/Image Processing export, packaged app, App icon, Finder icon, Info.plist, or LaunchServices in this track without a separate scoped stage.
