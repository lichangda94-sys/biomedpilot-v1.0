# UI-B9b Semantic Key Adoption and Test Migration

Date: 2026-05-20

Goal: adopt the UI-B9a semantic key registry into selected navigation, module entry, status chip, and Result / Report / Export shell surfaces, then migrate focused high-risk tests away from literal copy assertions toward object names, page keys and semantic status properties.

## 1. Scope

Allowed:

- Add semantic properties to nav, module cards, status chips and report/export shell widgets.
- Extend the existing key registry only where needed for current navigation.
- Migrate focused tests to assert `objectName`, `pageKey`, `navKey`, `moduleKey`, `semanticKey`, `reportStatusKey`, `resultSemanticKey`, and `exportFormatKey`.

Forbidden:

- No full translation.
- No runtime language switch.
- No report template rewrite.
- No business workflow changes.
- No packaging.
- No packaged app run.
- No icon/resource replacement.

## 2. Adopted Semantic Surfaces

| area | adoption |
|---|---|
| Navigation registry | Added `nav.test_feedback` and `nav.about` so the current auxiliary Sidebar entries also have stable keys. |
| Sidebar | `COMMON_SIDEBAR_ITEMS` now carries `semantic_key`; rendered buttons expose `pageKey`, `navKey`, and `semanticKey`. |
| Dashboard / module entry | Module cards, module title labels and module buttons expose `moduleKey`, `navKey`, and `semanticKey`. |
| Brand display | Dashboard title/subtitle labels expose `brand.primary` and `brand.secondary` semantic keys. |
| Status chip primitive | `make_status_chip()` keeps the visual `statusKey` and adds full semantic `semanticKey`, such as `analysis.status.preflight_only`, `feature.status.testing`, or `report.status.draft`. |
| Result preview empty state | Adds `semanticKey` matching `resultSemanticKey`. |
| Report draft boundary | Adds `reportKey=report.status` and `semanticKey` matching the current report status. |
| Export gated buttons | Adds `exportFormatKey`, `semanticKey`, `reportStatusKey`, and `resultSemanticKey` while preserving existing button copy and gates. |

## 3. Test Migration

Migrated focused tests:

| test_file | migration |
|---|---|
| `tests/ui/test_sidebar.py` | Sidebar assertions now verify `pageKey` and `semanticKey` instead of relying only on labels/order. |
| `tests/ui/test_module_selection.py` | Module card/button tests now verify `ModuleKey` and `NavKey` properties; brand test verifies `BrandKey` properties. |
| `tests/ui/test_ui_primitives.py` | Status chip test verifies full semantic status key. |
| `tests/ui/test_result_report_export_shell.py` | Report/export tests verify semantic properties and gate state instead of localized body/button tooltip copy. |
| `tests/shared/test_semantic_keys.py` | Registry coverage includes auxiliary nav keys. |

Tests intentionally still leave some literal copy assertions in low-risk areas where the test is checking visible affordance text or current user-facing copy. Full locale migration remains future work.

## 4. Non-Changes

- `app/bioinformatics` business workflow behavior is unchanged.
- `app/meta_analysis` business workflow behavior is unchanged.
- Report builders/templates are unchanged.
- No locale files or language switch UI were added.
- No packaging script, `dist/**`, App icon, Finder icon or desktop entry was changed.

## 5. Verification

Completed:

| command | result |
|---|---|
| `python3 -m app.main --smoke-test` | passed; source launch reports `workspace_entries=3` and `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_sidebar.py tests/ui/test_module_selection.py tests/ui/test_ui_primitives.py tests/ui/test_result_report_export_shell.py tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | passed; `29 passed in 2.34s`. |

Required before commit:

| command | result |
|---|---|
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | passed; `171 passed in 17.88s`. |
| `git diff --check` | passed, no whitespace errors. |
| `git status --short` | only scoped semantic adoption code, focused tests and this document changed before staging. |
