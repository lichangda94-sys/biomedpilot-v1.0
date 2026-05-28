# UI-B9c Selective Key Adoption And Test Migration Expansion

Date: 2026-05-20

Goal: selectively expand semantic key adoption across Bioinformatics target shell, Meta target shell, LabTools shell and Settings shell, while reducing high-risk literal text assertions. This is not full translation, language switching or report template work.

## 1. Scope

Implemented:

- Added a selective `page.*` key group to `app/shared/semantic_keys.py`.
- Added module/page/status semantic properties to Bioinformatics target IA buttons.
- Added module/page/status semantic properties to Meta target IA buttons and active type shell controls.
- Added module/page/status semantic properties to LabTools shell pages, cards and disabled shell buttons.
- Added module/page/status semantic properties to Settings shell pages, secondary navigation and detect-first controls.
- Migrated focused tests toward `semanticKey`, `pageKey`, `statusKey`, `moduleKey`, `statusSemanticKey` and Qt item data.

Not implemented:

- No full translation.
- No language switch.
- No report template rewrite.
- No business workflow change.
- No packaging or packaged app run.

## 2. Adopted Key Areas

| area | adopted properties |
|---|---|
| Bioinformatics target shell | `pageKey`, `moduleKey`, `statusKey`, `semanticKey`, `statusSemanticKey` |
| Meta target shell | `pageKey`, `moduleKey`, `statusKey`, `semanticKey`, `statusSemanticKey`, `interactionMode` |
| Meta active type controls | `moduleKey`, `statusKey`, `semanticKey`, `interactionMode`, `formalActionEnabled=False` |
| LabTools shell | `pageKey`, `moduleKey`, `statusKey`, `semanticKey` |
| Settings shell | `pageKey`, `moduleKey`, `statusKey`, `semanticKey`; secondary nav stores page key and semantic key in Qt item data |

## 3. Boundary Statement

The new `page.*` keys are stable identifiers for tests and shell semantics. They are not localized labels and do not enable full i18n.

UI-B9c does not change report templates, report export behavior, Bioinformatics analysis behavior, Meta Analysis workflow execution, LabTools calculation logic, Settings install/download/cloud behavior, resources, icons, packaging, desktop entries or packaged app behavior.

## 4. Verification

Completed verification:

| command | result |
|---|---|
| `python3 -m pytest -q tests/shared/test_semantic_keys.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_labtools_shell.py tests/ui/test_settings_shell.py` | Passed; `32 passed in 5.19s`. |
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reports `workspace_entries=3` and `pyside6_available=True`. |
| `python3 -m pytest -q tests/shared/test_semantic_keys.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_meta_analysis_ia_shell.py tests/ui/test_labtools_shell.py tests/ui/test_settings_shell.py` | Passed; `32 passed in 5.68s`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed; `178 passed in 19.07s`. |
| `git diff --check` | Passed, no whitespace errors. |
| `git status --short` | Only semantic key registry, Bio/Meta/LabTools/Settings shell properties, focused tests and docs changed before staging. |
