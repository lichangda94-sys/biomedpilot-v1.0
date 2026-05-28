# UI-B7.1 Result / Report / Export Shell Adoption Calibration

Date: 2026-05-20

Goal: calibrate adoption of the shared Result / Report / Export shell into Bioinformatics and Meta Analysis target shells, while keeping all report-ready, formal result, fake plot, fake result, production export, packaging and resource replacement work out of scope.

## 1. Scope

Allowed:

- Add a reusable Result / Report / Export adoption panel.
- Mount the shared panel in Bioinformatics and Meta Analysis target shell surfaces.
- Expose semantic properties for result state, report status, export gate and report-ready package permission.
- Add focused tests for shared panel, Bio adoption and Meta adoption.
- Add this checkpoint document.

Forbidden in this stage:

- No fake plots, fake results or formal computed results.
- No report-ready export package.
- No report template rewrite.
- No Bioinformatics or Meta Analysis business workflow changes.
- No full i18n adoption or language switch.
- No resource/icon replacement.
- No packaging, packaged app run, LaunchServices, Finder icon, App icon, Info.plist icon binding or desktop `.app` overwrite.

## 2. Adoption Model

Implemented adoption state:

| module | adopted_surface | default_state | export_gate | report_ready |
|---|---|---|---|---|
| Bioinformatics | Target IA shell | empty result preview | `disabled_empty_result` | `False` |
| Meta Analysis | Target IA shell | empty result preview | `disabled_empty_result` | `False` |

The adoption panel uses the shared B7 shell components:

- `make_result_preview_empty_state`
- `make_report_draft_boundary`
- `make_export_buttons`

It does not replace legacy report business pages yet. It marks the target shell with shared semantics so later module pages can migrate to the same state model without confusing draft/testing outputs with formal report-ready outputs.

## 3. Runtime Changes

Implemented:

- Added `make_result_report_export_adoption_panel()` in `app/shared/result_report_export_shell.py`.
- Added adoption panel properties:
  - `adoptionModule`
  - `resultSemanticKey`
  - `reportStatusKey`
  - `exportGate`
  - `reportReadyPackageAllowed=False`
- Added export button properties:
  - `formalActionEnabled=False`
  - `reportReadyPackageAllowed=False`
- Mounted the adoption panel in:
  - Bioinformatics target IA shell
  - Meta Analysis target IA shell

Not changed:

- Legacy Bioinformatics result browser and report viewer remain mounted for existing focused tests.
- Meta Analysis target shell remains shell-only/select-only; no full workflow runtime is introduced.
- No report/export backend behavior changed.

## 4. Acceptance

UI-B7.1 is accepted when:

- Shared adoption panel defaults to empty result preview.
- Bioinformatics target shell exposes one adoption panel with `adoptionModule=bioinformatics`.
- Meta Analysis target shell exposes one adoption panel with `adoptionModule=meta_analysis`.
- Export buttons remain disabled in empty-result adoption state.
- `formalActionEnabled=False` and `reportReadyPackageAllowed=False` are exposed on export controls.
- Focused Result / Report / Export, Bio IA and Meta IA tests pass.

## 5. Command Log

| command | result |
|---|---|
| `git status --short` | Passed; workspace was clean before UI-B7.1 edits. |
| `rg -n "UI-B7\|B7\\.1\|Result / Report / Export\|result_report\|report_export\|make_result\|make_report\|make_export\|report draft\|export gating\|resultSemantic" docs/ui app tests -S` | Passed; identified shared shell, adoption gaps and tests. |
| `rg --files app tests docs/ui \| rg "result_report\|report_export\|bioinformatics/workspace\|meta_analysis/workspace\|test_result_report\|test_bioinformatics_ia\|test_meta_analysis_ia\|B7"` | Passed; identified scoped files. |
| `sed -n '1,240p' app/shared/result_report_export_shell.py` | Passed; read shared shell state model and widget builders. |
| `sed -n '1,180p' tests/ui/test_result_report_export_shell.py` | Passed; read UI focused Result / Report / Export tests. |
| `sed -n '1,220p' tests/shared/test_result_report_export_shell.py` | Passed; read shared state tests. |
| `sed -n '420,490p' app/bioinformatics/workspace.py` and `sed -n '250,370p' app/meta_analysis/workspace.py` | Passed; inspected target shell insertion points. |
| `python3 -m pytest -q tests/ui/test_result_report_export_shell.py tests/shared/test_result_report_export_shell.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_meta_analysis_ia_shell.py` | Passed; `27 passed in 1.66s`. |

## 6. Verification

Completed verification:

| command | result |
|---|---|
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reports `workspace_entries=3` and `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_result_report_export_shell.py tests/shared/test_result_report_export_shell.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_meta_analysis_ia_shell.py` | Passed; `27 passed in 1.45s`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed; `177 passed in 18.27s`. |
| `git diff --check` | Passed, no whitespace errors. |
| `git status --short` | Only shared R/R/E shell, Bio/Meta target shell adoption, focused tests and this document changed before staging. |

## 7. Boundary Statement

This stage only calibrates shared Result / Report / Export shell adoption in Bioinformatics and Meta Analysis target shells, focused tests and this checkpoint document. It does not modify report templates, business execution flows, active resources, icons, packaging, desktop entries or packaged app behavior.
