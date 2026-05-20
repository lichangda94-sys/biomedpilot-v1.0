# UI-C0 Low-Fidelity Shell Usability Pass

Date: 2026-05-20

Goal: improve low-fidelity shell usability without changing business flows, replacing resources, enabling full i18n, changing report templates, packaging, or running the packaged app.

## 1. Scope

Implemented:

- Welcome primary entry action now exposes default-button and usability-role metadata.
- Sidebar primary and auxiliary navigation buttons expose usability roles, accessible names, tooltips and minimum hit height.
- Dashboard module cards and module entry buttons expose usability roles and accessible names.
- LabTools shell is now hosted in a scrollable shell page to avoid truncation on smaller windows.
- Settings shell is now hosted in a scrollable shell page to avoid truncation on smaller windows.
- Focused tests verify the low-fidelity usability properties.

Not implemented:

- No high-fidelity redesign.
- No new icons, image replacement or active resource replacement.
- No business workflow changes.
- No full translation or language switch.
- No report template rewrite.
- No packaging, packaged app run, desktop entry update or `.app` overwrite.

## 2. Verification

Focused verification completed:

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/ui/test_labtools_shell.py tests/ui/test_settings_shell.py` | Passed; `30 passed in 7.50s`. |
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reported `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed; `178 passed in 20.64s`. |
| `git diff --check` | Passed. |

## 3. Boundary Statement

UI-C0 is a low-fidelity shell usability pass. It only changes shell usability metadata, scrollability for long shell pages, focused tests and this checkpoint document.
