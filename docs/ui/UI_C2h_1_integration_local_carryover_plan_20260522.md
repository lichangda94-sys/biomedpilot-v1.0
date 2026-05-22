# UI-C2h.1 Integration Local Carry-over Planning

Date: 2026-05-22

## 1. Scope

This stage plans a local-only carry-over path from `dev/ui-shell` into the local Integration workflow.

Source:

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- Branch: `dev/ui-shell`
- HEAD reviewed: `7a0fe71 docs(ui): audit LabTools carry-over to MainLine and Integration`

Target:

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Integration`
- Branch: `dev/integration`
- HEAD reviewed: `ea57a49 Restore bioinformatics task plan import surface`

Strict boundary:

- Planning only.
- No merge.
- No cherry-pick.
- No push.
- No package smoke.
- No packaged app.
- No App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices.
- No changes to `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`.

This stage adds only:

- `docs/ui/UI_C2h_1_integration_local_carryover_plan_20260522.md`
- `docs/ui/UI_C2h_1_integration_local_carryover_sequence_20260522.csv`

## 2. Carry-over Decision

Do not directly merge `dev/ui-shell` into `dev/integration`.

The previous UI-C2h audit found a non-destructive merge simulation result of 30 conflict markers and 13 `changed in both` sections for `dev/integration`. The primary conflict surface is `app/shell/main_window.py`.

Recommended next implementation branch, if carry-over is approved:

```bash
git -C "/Users/changdali/Developer/biomedpilot v1.0/Integration" switch -c codex/integration-labtools-ui-c2-carryover dev/integration
```

This command is not executed in this planning stage.

## 3. Integration State To Preserve

The Integration `app/shell/main_window.py` currently imports and mounts:

- `BioinformaticsWorkspaceWidget`
- `MetaAnalysisWorkspaceWidget`
- `LabToolsWorkspaceWidget`
- `ExternalEngineManagerPage`
- `SettingsProfile`

The carry-over must preserve these Integration-owned surfaces. In particular:

- Do not overwrite Integration's `ExternalEngineManagerPage` route.
- Do not remove the existing Bioinformatics workspace mounting.
- Do not remove the existing Meta Analysis runtime mounting.
- Do not replace the Integration project creation/opening flow without a separate audit.
- Do not replace `app/labtools/workspace.py` wholesale with the UI Shell one-file LabTools pages unless the target branch explicitly chooses that architecture.

## 4. UI Shell Source Package

The UI Shell LabTools C2 runtime package is made of these high-level layers:

| Layer | Source evidence | Carry-over note |
| --- | --- | --- |
| Shared UI primitives and semantic keys | `app/shared/semantic_keys.py`; `app/shared/ui_components/primitives.py`; `app/app_identity.py` | Needed before LabTools status chips, icons, and empty states can be stable. |
| Active icon/illustration assets | `assets/icons/modules/`; `assets/icons/labtools/`; `assets/icons/status/`; `assets/images/empty_states/`; limited `assets/icons/result_report_export/`; `assets/icons/settings/resources/` | Carry as assets only after loader paths are reconciled. Do not touch App icon. |
| LabTools read-only runtime bridge | `app/labtools_runtime.py` | Required for Quick Calculator, Formula Solver, Reagent preview, and WB loading preview. Must keep no-store/no-default-`~/.labtools` behavior. |
| LabTools UI shell and pages | `app/shell/main_window.py` changes in C2b-C2f | Must be manually extracted into Integration architecture instead of file overwrite. |
| Focused UI tests | `tests/ui/test_labtools_navigation_shell.py`; `test_labtools_general_calculator_ui.py`; `test_labtools_reagent_preparation_ui.py`; `test_labtools_wb_loading_ui.py`; `test_labtools_boundary_pages.py` | Add with any necessary target-specific fixture updates after UI code reconciliation. |

## 5. Recommended Carry-over Batches

### Batch 0: Local Branch And Freeze

Goal: create a local Integration carry-over branch and record a clean baseline.

Required checks:

- `git status --short` is clean in Integration.
- Record `dev/integration` HEAD.
- Do not push.
- Do not package.

Hold condition:

- Any uncommitted Integration changes appear before carry-over starts.

### Batch 1: Shared Foundation

Goal: add or reconcile the minimum shared foundation needed by LabTools UI-C2.

Include:

- `app/shared/semantic_keys.py`
- `app/shared/ui_components/primitives.py`
- relevant `app/shared/ui_components/__init__.py` exports
- `app/app_identity.py` icon loader additions
- semantic key tests and primitive tests that are needed by LabTools status chips

Manual reconciliation:

- Integration may already have `app/shared/local_engines/**`; keep it.
- `ExternalEngineManagerPage` remains the authoritative Settings external engine implementation in Integration.
- `status_available` must remain conditional and never imply feature availability unless the underlying resource status is confirmed.

Verification gate:

- `python3 -m pytest -q tests/shared/test_semantic_keys.py tests/ui/test_ui_primitives.py`
- `python3 -m app.main --smoke-test`

### Batch 2: Asset Loader And Non-App Assets

Goal: carry only non-App UI icon assets required by the active UI.

Include:

- `assets/icons/modules/`
- `assets/icons/labtools/`
- `assets/icons/status/`
- `assets/images/empty_states/`
- `assets/icons/result_report_export/` only for the five gated marker/helper icons
- `assets/icons/settings/resources/` only if Settings resource cards use the reconciled loader

Exclude:

- `assets/icons/app/`
- `.icns`
- iconset
- Info.plist binding
- LaunchServices
- package metadata

Verification gate:

- `python3 -m pytest -q tests/ui/test_app_identity.py tests/ui/test_status_icon_active_pilot.py`
- asset-path tests only after `app/app_identity.py` is reconciled.

### Batch 3: LabTools Runtime Bridge

Goal: add `app/labtools_runtime.py` and keep it read-only.

Required invariants:

- No default write to `~/.labtools`.
- No default `ReagentTemplateStore` creation.
- No `WBLoadingRecordStore` creation.
- No file export.
- No ImageJ/Fiji runner.
- No ELISA backend.
- No cell experiment record store.

Verification gate:

- focused import/runtime tests from LabTools UI tests after the target UI has been reconciled.

### Batch 4: LabTools Navigation Shell

Goal: reconcile UI-C2b with Integration's existing `LabToolsWorkspaceWidget` architecture.

Required UI invariants:

- LabTools first-level entries remain exactly:
  - General Calculator / 通用计算器
  - Reagent Preparation / 试剂制备
  - Experiment Modules / 实验模块
- ImageJ/Fiji is not a LabTools first-level entry.
- General Calculator does not contain WB, BCA, ELISA, qPCR workflow, or cell record saving.
- Reagent shell does not enable real save/export.
- Experiment Modules shows safe placeholders or boundary pages.

Recommended reconciliation strategy:

- Prefer moving UI-C2 LabTools page construction into `app/labtools/workspace.py` or a small Integration-owned LabTools UI module.
- Keep `app/shell/main_window.py` as route orchestration only.
- Do not paste the entire UI Shell `main_window.py` over Integration.

Verification gate:

- `python3 -m pytest -q tests/ui/test_labtools_navigation_shell.py tests/ui/test_labtools_shell.py`
- `python3 -m pytest -q tests/ui/test_module_selection.py tests/ui/test_sidebar.py`

### Batch 5: General Calculator And Formula Solver

Goal: add UI-C2c Quick Calculator and Dynamic Formula Solver.

Allowed:

- Execute quick calculator backend tasks through the read-only bridge.
- Execute formula solver through the read-only bridge.
- Copy result text.

Blocked:

- Save history.
- File export.
- `CalculationRecordStore`.
- Any write to `~/.labtools`.

Verification gate:

- `python3 -m pytest -q tests/ui/test_labtools_general_calculator_ui.py`

### Batch 6: Reagent Preparation UI

Goal: add UI-C2d reagent template and preparation preview.

Allowed:

- In-memory PBS 1x sample.
- `calculate_preparation()` preview.
- Copy summary.

Blocked:

- Save template.
- Save preparation record.
- Export.
- Inventory deduction.
- Cloud template library.
- Production batch release.
- Multi-user sync.

Verification gate:

- `python3 -m pytest -q tests/ui/test_labtools_reagent_preparation_ui.py`

### Batch 7: Western Blot Loading UI

Goal: add UI-C2e WB loading focused page.

Allowed:

- WB loading calculation preview.
- S1/S2/S3 in-memory example.
- S3 warning row.
- Schematic lane preview.
- Copy loading table.

Blocked:

- SDS-PAGE implementation.
- Fake gel bands.
- Image analysis.
- Automatic band recognition.
- Antibody recommendation.
- Save/export/history.

Verification gate:

- `python3 -m pytest -q tests/ui/test_labtools_wb_loading_ui.py`

### Batch 8: Boundary Pages

Goal: add UI-C2f safe boundary pages.

Pages:

- SDS-PAGE placeholder.
- BCA / OD MVP boundary.
- Cell Experiment Workspace shell.
- ELISA / Immuno-Absorbance blocked boundary.
- Image Processing Workspace boundary.

Required blocked semantics:

- ELISA remains `blocked_until_backend`.
- Cell records remain adapter/store missing.
- Image Processing remains Settings-linked and does not run ImageJ/Fiji.
- No macro surface.
- No automatic ROI, cell counting, band recognition, or IHC scoring.

Verification gate:

- `python3 -m pytest -q tests/ui/test_labtools_boundary_pages.py`

### Batch 9: Integration Regression Gate

Run after all carry-over batches are reconciled:

```bash
python3 -m pytest -q tests/ui/test_labtools_boundary_pages.py tests/ui/test_labtools_wb_loading_ui.py tests/ui/test_labtools_reagent_preparation_ui.py tests/ui/test_labtools_general_calculator_ui.py tests/ui/test_labtools_navigation_shell.py tests/ui/test_labtools_shell.py
python3 -m pytest -q tests/ui/test_module_selection.py tests/ui/test_sidebar.py
python3 -m pytest -q tests/ui/test_settings_shell.py tests/shared/test_semantic_keys.py
python3 -m app.main --smoke-test
git diff --check
git diff --cached --check
```

Do not run package smoke or packaged app during this carry-over planning/implementation gate.

## 6. High-risk Conflict Strategy

| Conflict surface | Risk | Required resolution |
| --- | --- | --- |
| `app/shell/main_window.py` | High | Preserve Integration route orchestration and external engine manager. Manually port only LabTools C2 widgets/routes. |
| `app/labtools/workspace.py` vs UI Shell LabTools one-file pages | High | Decide whether LabTools UI-C2 lives in Integration `app/labtools/workspace.py` or imported helper modules; avoid duplicate competing LabTools homes. |
| `app/app_identity.py` | Medium | Add non-App icon loaders without touching App icon, `.icns`, Info.plist, or LaunchServices. |
| `app/shared/semantic_keys.py` | Medium | Add semantic keys and enums without weakening Integration status semantics. |
| `assets/icons/**` | Medium | Carry only active non-App resources required by reconciled loaders. |
| `tests/ui/test_labtools_*.py` | Medium | Import after target UI object names and routing are stable; adjust only for Integration architecture, not for weakened assertions. |
| `docs/ui/**` | Low | Carry audit docs as reference, but do not let docs drive runtime behavior. |

## 7. Must-preserve Product Boundaries

The Integration carry-over must preserve these UI-C2 boundaries:

- No default write to `~/.labtools`.
- No active save/export/history for LabTools pages.
- No file export without a future file picker adapter.
- No `ReagentTemplateStore`, `PreparationRecordStore`, `WBLoadingRecordStore`, BCA store, or cell record store creation.
- No ImageJ/Fiji first-level LabTools entry.
- No ImageJ/Fiji runner.
- No macro exposure.
- No automatic ROI, automatic cell counting, automatic band recognition, or IHC scoring.
- No ELISA backend, active 4PL, formal report, or production save/export.
- No fake gel bands, fake records, fake reports, or report-ready package.
- Status icons remain auxiliary; text labels and semantic keys remain authoritative.

## 8. Recommended Next Stage

Recommended next stage:

`UI-C2h.2 Integration carry-over branch preparation`

Scope:

- Create a local branch from `dev/integration`.
- Do not push.
- Start Batch 0 and Batch 1 only.
- Reconcile shared primitives, semantic keys, and icon loader foundation before touching LabTools runtime pages.

Alternative if the user wants to skip planning and directly port:

`UI-C2h.2a Integration shared foundation carry-over`

This should still avoid direct merge/cherry-pick and should use manual file-level reconciliation.

## 9. Verification Commands

| Command | Result |
| --- | --- |
| `git status --short` in UIShell | Clean before planning document creation |
| `git -C .../Integration status --short` | Clean |
| `git log --oneline -5` | Reviewed current UIShell HEAD |
| `git -C .../Integration log --oneline -5` | Reviewed current Integration HEAD |
| `git diff --name-status dev/integration...dev/ui-shell -- app tests assets docs/ui` | Reviewed source/target changed files |
| `git log --oneline --reverse dev/integration..dev/ui-shell -- app tests assets docs/ui` | Reviewed source-only sequence |
| `git show dev/integration:app/shell/main_window.py` | Reviewed Integration main window route structure |
| `git show dev/integration:app/labtools/workspace.py` | Reviewed Integration LabTools workspace structure |
| `git show dev/integration:app/shared/local_engines/external_engine_manager_page.py` | Reviewed Integration external engine manager surface |
| CSV structure check for `docs/ui/UI_C2h_1_integration_local_carryover_sequence_20260522.csv` | Passed; 22 rows with required columns |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed after staging planning docs |

No runtime tests were run in this planning stage because no runtime code was modified.

## 10. Non-modification Statement

This planning stage did not modify Integration, MainLine, LabTools, app code, tests, active assets, scripts, or `dist/**`. It did not merge, cherry-pick, push, package, run package smoke, run a packaged app, or touch App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices.
