# UI-C3g LabTools Adapter Pilot Runtime Review / Error-State Hardening

Date: 2026-05-24

## 1. Scope

This stage reviews and hardens the LabTools save/export/history adapter pilot after UI-C3f.

Allowed runtime hardening:

- preserve current pilot scope
- improve file-picker export affordance metadata
- improve user-visible cancellation/error feedback
- add focused regression tests

Not allowed and not changed:

- Quick Calculator / Formula Solver history or export
- BCA / OD save or export
- Cell Experiment save or export
- ELISA analysis/save/report/export
- Image Processing run/save/export
- PDF / DOCX
- hardcoded export paths
- `~/.labtools` writes
- packaged app
- App icon / Finder icon / `.icns` / Info.plist / LaunchServices

## 2. Runtime Review Result

Decision: `hardened_with_scope_preserved`.

The adapter pilot remains limited to:

- Reagent Template save/history through BioMedPilot project storage.
- Reagent Preparation save/history through BioMedPilot project storage.
- WB Loading save/history through BioMedPilot project storage.
- Reagent Preparation Markdown / CSV export through file picker.
- WB Loading Markdown / CSV export through file picker.

No new LabTools surface was enabled.

## 3. Hardening Changes

Runtime UI changes:

- Reagent Preparation Markdown / CSV export buttons now carry:
  - `exportRequiresFilePicker=True`
  - `exportFormat=markdown` or `csv`
- WB Loading Markdown / CSV export buttons now carry:
  - `exportRequiresFilePicker=True`
  - `exportFormat=markdown` or `csv`
- File-picker cancellation now writes a non-blocking UI message:
  - `导出已取消；未写入任何文件。`
- Cancellation does not set the error state.
- `~/.labtools` rejection remains blocking and visible in the UI error row.
- Missing suffix handling still appends the expected `.md` or `.csv` suffix.

Runtime writer boundaries retained:

- export writers still reject `~/.labtools`
- export writers still require expected suffix
- export writers still write only the user-selected file-picker path
- no PDF / DOCX writer exists
- no hardcoded desktop/repo/dist export path exists

## 4. Error-State Coverage

| Scenario | Current behavior | Closure |
| --- | --- | --- |
| User cancels file picker | non-blocking message, no file write | hardened |
| Missing suffix from picker | appends expected suffix | covered |
| `~/.labtools` path selected | rejected, error row visible, no file write | covered |
| corrupt reagent history JSON | history error state, no crash | already covered |
| corrupt WB history JSON | history error state, no crash | already covered |
| missing project context | save/history disabled | preserved |
| non-pilot export surfaces | buttons disabled or absent | preserved |

## 5. Scope Guardrails

Still disabled:

- Quick Calculator history/export
- Dynamic Formula Solver history/export
- SDS-PAGE save/export
- BCA / OD save/export
- Cell Experiment save/export
- ELISA analysis/save/report/export
- Image Processing run/save/export
- PDF / DOCX
- formal report package

Still forbidden:

- writing to `~/.labtools`
- export without file picker
- hardcoded export path
- default Desktop / Downloads export path
- packaged app or desktop identity changes

## 6. Files Changed

Runtime:

- `app/shell/main_window.py`

Tests:

- `tests/ui/test_labtools_adapter_error_hardening.py`
- `tests/ui/test_labtools_navigation_shell.py`

Docs:

- `docs/ui/UI_C3g_labtools_adapter_runtime_review_error_hardening_20260524.md`
- `docs/ui/UI_C3g_labtools_adapter_error_state_matrix_20260524.csv`

## 7. Verification

Commands run:

- `python3 -m pytest -q tests/ui/test_labtools_adapter_error_hardening.py`
- `python3 -m pytest -q tests/ui/test_labtools_file_picker_export_pilot.py tests/ui/test_labtools_reagent_save_history_pilot.py tests/ui/test_labtools_wb_save_history_pilot.py tests/ui/test_labtools_storage_adapter.py`
- `python3 -m pytest -q tests/ui/test_labtools_adapter_error_hardening.py tests/ui/test_labtools_file_picker_export_pilot.py tests/ui/test_labtools_reagent_save_history_pilot.py tests/ui/test_labtools_wb_save_history_pilot.py tests/ui/test_labtools_storage_adapter.py tests/ui/test_labtools_reagent_preparation_ui.py tests/ui/test_labtools_wb_loading_ui.py tests/ui/test_labtools_general_calculator_ui.py tests/ui/test_labtools_boundary_pages.py tests/ui/test_labtools_navigation_shell.py tests/ui/test_labtools_shell.py`
- `python3 -m app.main --smoke-test`
- CSV structure check for `docs/ui/UI_C3g_labtools_adapter_error_state_matrix_20260524.csv`

Result:

- C3g focused tests passed, 6 tests.
- C3f adapter regression tests passed, 18 tests.
- Full LabTools C3/C2 focused regression passed, 59 tests.
- Source smoke passed.
- CSV structure check passed, 17 rows.

## 8. Next Stage

Proceed to Bioinformatics formal DEG carry-over readiness audit.

Do not enable formal DEG in this C3g stage.
