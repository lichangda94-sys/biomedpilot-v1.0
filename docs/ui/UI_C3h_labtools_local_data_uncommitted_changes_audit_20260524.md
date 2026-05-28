# UI-C3h LabTools Local Data Uncommitted Changes Audit

Date: 2026-05-24

## 1. Scope

This audit reviewed the LabTools local_data files that had previously appeared as uncommitted changes:

- `app/labtools_runtime.py`
- `app/shell/main_window.py`
- `tests/ui/test_labtools_shell.py`
- `tests/labtools/`
- `tests/ui/test_labtools_local_data_read_integration.py`

This audit did not modify UI-B10, packaging, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, `dist/**`, or desktop app entries.

## 2. Current Git State

Current `git status --short`: clean.

Current `git diff --stat`: empty.

The LabTools local_data changes are no longer uncommitted. They are already recorded as an independent functional commit:

- `7afe07b feat(labtools): connect local data store to UI read paths`

Files in that commit:

- `app/labtools_runtime.py`
- `app/shell/main_window.py`
- `tests/labtools/test_local_data_runtime_bridge.py`
- `tests/ui/test_labtools_local_data_read_integration.py`
- `tests/ui/test_labtools_shell.py`

## 3. Functional Scope Assessment

Decision: `complete_already_committed`.

The committed changes belong to a LabTools local_data read integration stage, not UI-B10.

Observed scope:

- `app/labtools_runtime.py` provides local_data read-model/status bridge functions.
- `app/shell/main_window.py` reads local_data through `labtools_runtime`, not by directly importing `labtools.local_data`.
- LabTools home can show missing or initialized local_data status.
- Reagent and WB pages can display local_data-derived read previews where project context exists.
- Tests cover missing local_data store, initialized local_data counts, UI read integration, and no direct UI import of `labtools.local_data`.

The changes are read-path integration and do not represent App icon, packaging, Finder, Info.plist, LaunchServices, or UI-B10 work.

## 4. Boundary Assessment

No evidence was found that the local_data stage:

- modifies UI-B10 scope
- changes package scripts
- writes App icon assets
- modifies `dist/**`
- overwrites desktop app entries
- runs LaunchServices
- enables package smoke
- enables formal report/export behavior

The local_data integration should remain outside UI-B10 and should not be bundled into any App icon / packaging commit.

## 5. Test Results

Commands run:

- `python3 -m pytest -q tests/labtools/test_local_data_runtime_bridge.py tests/ui/test_labtools_local_data_read_integration.py`
  - Result: 11 passed
- `python3 -m pytest -q tests/ui/test_labtools_shell.py tests/ui/test_labtools_general_calculator_ui.py tests/ui/test_labtools_reagent_preparation_ui.py tests/ui/test_labtools_wb_loading_ui.py tests/ui/test_labtools_boundary_pages.py`
  - Result: 31 passed
- `python3 -m app.main --smoke-test`
  - Result: passed
- `git diff --check`
  - Result: passed
- `git diff --cached --check`
  - Result: passed

## 6. Submission Decision

No functional commit was created by this audit because the LabTools local_data changes were already committed as:

- `7afe07b feat(labtools): connect local data store to UI read paths`

This audit adds documentation only.

## 7. Recommendation

Proceed with UI-B10 only after the existing UI-B10 readiness gate human decisions are resolved. Treat LabTools local_data read integration as complete and separate from UI-B10.
