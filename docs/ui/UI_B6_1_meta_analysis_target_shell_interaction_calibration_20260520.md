# UI-B6.1 Meta Analysis Target Shell Interaction Calibration

Date: 2026-05-20

Goal: calibrate Meta Analysis target shell interactions so target IA pages and active Meta types can be selected as shell-state previews without enabling the full Meta runtime, Network Meta, production systematic-review workflows, automatic AI conclusions, report-ready outputs, packaging, or resource replacement.

## 1. Scope

Allowed:

- Add select-only interaction state to the Meta target IA shell.
- Keep target page navigation inside the shell preview layer.
- Add active Meta type selection state for the 10 active v1 types.
- Keep Network Meta visible only as planned/disabled boundary.
- Add focused UI tests for interaction properties and selection state.
- Add this checkpoint document.

Forbidden in this stage:

- No legacy Meta registry hookup.
- No Network Meta enablement.
- No production systematic-review workflow claims.
- No automatic AI conclusion or final recommendation generation.
- No report template rewrite, report-ready export, PDF production, or publication package.
- No business workflow implementation, cloud configuration, resource replacement, packaging, or packaged app run.

## 2. Interaction Calibration

Implemented interaction model:

| surface | interaction | execution boundary |
|---|---|---|
| Target IA page nav | Enabled as `select_only` shell buttons. | Updates selected target page status preview only; does not switch to a full workflow runtime. |
| Active Meta type cards | Adds `schema_shell` select buttons for the 10 active v1 types. | Updates selected type preview only; does not run extraction, QA, statistics or report generation. |
| Network Meta | Remains planned/disabled. | Not an active type and not selectable. |
| AI suggestion boundary | Kept as review-only copy. | No automatic conclusion, no accept-as-final workflow. |
| Mainline shell contract | Preserved as `workflow_home`, `project_contract`, `dev_branch`. | Target shell interaction does not replace the old 3-page mainline contract yet. |

## 3. Runtime Changes

Implemented:

- Extended `MetaTargetIAPage` with `page_group` and `flow_index`.
- Extended `MetaActiveType` with `interaction_mode`.
- Added current shell-state helpers:
  - `current_target_page_key()`
  - `selected_active_meta_type_id()`
  - `network_meta_enabled()`
- Added select-only target page buttons with properties:
  - `pageKey`
  - `pageGroup`
  - `flowIndex`
  - `statusKey`
  - `interactionMode=select_only`
  - `formalActionEnabled=False`
- Added active type select buttons with:
  - `typeId`
  - `statusKey`
  - `interactionMode=schema_shell`
  - `formalActionEnabled=False`
- Added disabled Network Meta planned button with:
  - `typeId=network_meta_analysis`
  - `statusKey=planned`
  - `interactionMode=planned_disabled`
  - `formalActionEnabled=False`
- Added shell state labels:
  - `metaTargetInteractionStatus`
  - `metaActiveTypeInteractionStatus`

Not changed:

- Existing mainline shell pages remain `workflow_home`, `project_contract`, `dev_branch`.
- No full workflow runtime page was added.
- No analysis, extraction, statistics, report, PDF, export or AI conclusion workflow was enabled.

## 4. Acceptance

UI-B6.1 is accepted when:

- Target IA buttons are selectable shell controls, not disabled static labels.
- Selecting a target page updates only `current_target_page_key()` and status preview.
- Selecting an active Meta type updates only `selected_active_meta_type_id()` and status preview.
- All target/type interactions expose `formalActionEnabled=False`.
- Network Meta remains disabled and `network_meta_enabled()` returns `False`.
- The existing mainline shell page contract remains unchanged.

## 5. Command Log

| command | result |
|---|---|
| `git status --short` | Passed; workspace was clean before UI-B6.1 edits. |
| `rg -n "UI-B6\|B6\\.1\|Meta Analysis target\|Meta.*shell\|AI suggestion\|Network Meta\|interaction" docs/ui app/meta_analysis tests/ui -S` | Passed; identified Meta shell and planning boundaries. |
| `rg --files app/meta_analysis tests/ui docs/ui \| rg "meta\|Meta\|B6\|semantic\|result_report"` | Passed; identified Meta code, tests and target draft files. |
| `sed -n '1,420p' app/meta_analysis/workspace.py` | Passed; read current target shell implementation. |
| `sed -n '1,240p' tests/ui/test_meta_analysis_ia_shell.py` | Passed; read focused Meta IA tests. |
| `sed -n '250,330p' docs/ui/UI_Rebuild_MasterPlan_20260520.md` | Passed; confirmed Meta target flow and Network Meta boundary. |
| `sed -n '250,276p' docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | Passed; confirmed AI suggestion and shell-only constraints. |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed; `8 passed in 0.42s`. |

## 6. Verification

Completed verification:

| command | result |
|---|---|
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reports `workspace_entries=3` and `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_meta_analysis_ia_shell.py` | Passed; `8 passed in 0.41s`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed; `173 passed in 17.88s`. |
| `git diff --check` | Passed, no whitespace errors. |
| `git status --short` | Only `app/meta_analysis/workspace.py`, `tests/ui/test_meta_analysis_ia_shell.py`, and this document changed before staging. |

## 7. Boundary Statement

This stage only calibrates Meta Analysis target shell interaction state, focused tests and this checkpoint document. It does not modify packaging, desktop entries, active icons/resources, report templates, language switching, or Meta Analysis business execution flows.
