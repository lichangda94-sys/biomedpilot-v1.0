# UI-C2a LabTools Adapter-First Implementation Plan

Date: 2026-05-22

## 1. Scope

This stage defines the adapter-first implementation plan for the real PySide LabTools UI after the UI-C1c3d mockup set closure audit.

Inputs:

- `docs/ui/UI_C1c3d_labtools_mockup_set_closure_audit_20260522.md`
- `docs/ui/UI_C1c3d_labtools_mockup_implementation_readiness_matrix_20260522.csv`
- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`
- `docs/ui/UI_C1c2_labtools_visual_style_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c3b_labtools_mockup_candidate_QA_report_20260522.md`
- `docs/ui/UI_C1c3b_labtools_mockup_revision_brief_20260522.md`
- `docs/ui/references/labtools/LabTools_UI_integration_contract_20260522.md`
- `docs/ui/references/labtools/LabTools_backend_gap_audit_20260522.md`

This stage only creates implementation planning, adapter contracts, view model contracts, sequencing, and test planning. It does not implement real UI pages, modify LabTools backend logic, add ELISA backend, add a cell experiment record store, add an ImageJ/Fiji runner, enable save/export/history/batch actions, execute UI-B10, package, or run a packaged app.

## 2. Implementation Principle

LabTools UI-C2 must be adapter-first:

1. Build UI pages only against explicit adapter contracts.
2. Never let a PySide page instantiate LabTools stores with their default root if that default can fall back to `~/.labtools`.
3. Treat copy, save, export, history, and external engine execution as different capabilities.
4. Render disabled / adapter-needed / shell-only states as first-class UI states, not as TODO comments.
5. Normalize backend errors before they reach widgets.
6. Render all calculation results through a shared result/warning view model.
7. Preserve LabTools IA and mockup boundaries before visual polish.

## 3. Required Adapter Contracts

| Adapter | Purpose | Required Before |
| --- | --- | --- |
| `BioMedPilotLabToolsStorageAdapter` | Resolves BioMedPilot project-scoped LabTools storage paths and constructs LabTools stores with explicit paths. | Any save/history action becomes active. |
| `FilePickerExportAdapter` | Wraps user file selection, overwrite confirmation, cancellation, and filesystem errors for exports. | Any file export button becomes active. |
| UI-facing error normalization | Converts backend exceptions into consistent user-facing rows. | Any real calculator/reagent/WB/BCA page renders backend output. |
| LabTools result/warning view model | Defines result tables, warning rows, review notices, copy text, save/export states, and semantic keys. | Any UI-C2 result preview is implemented. |
| Disabled / adapter-needed state model | Makes unavailable actions explicit and testable. | Any button, menu item, or status chip that represents unavailable capability. |

Detailed contracts are defined in:

`docs/ui/UI_C2a_labtools_adapter_contracts_20260522.md`

`docs/ui/UI_C2a_labtools_view_model_contract_20260522.md`

## 4. Storage Adapter Plan

`BioMedPilotLabToolsStorageAdapter` should resolve paths under BioMedPilot project storage, not under the LabTools package default.

Proposed project-scoped layout:

| Store / Area | Project Storage Path Class | Notes |
| --- | --- | --- |
| Reagent templates | `project_storage/labtools/reagents/templates/` | Backed by `ReagentTemplateStore(path=...)`. |
| Reagent preparation records | `project_storage/labtools/reagents/preparations/` | Backed by `PreparationRecordStore(path=...)`. |
| WB loading records | `project_storage/labtools/protein/wb_loading/` | Backed by `WBLoadingRecordStore(path=...)`. |
| SDS-PAGE templates | `project_storage/labtools/protein/sds_page/templates/` | Future persistent adapter around current template helpers. |
| Calculation history | `project_storage/labtools/calculations/history/` | Disabled until `CalculationRecordStore` exists. |
| BCA records | `project_storage/labtools/protein/bca_records/` | Disabled until BCA record/export model exists. |
| Cell experiment records | `project_storage/labtools/cell_experiments/records/` | Disabled until cell record store exists. |

Rules:

- Desktop UI must never default-write to `~/.labtools`.
- The adapter must return an explicit unavailable state if no active BioMedPilot project storage root exists.
- Store creation must be lazy and page-scoped; opening LabTools Home must not create write paths.
- Corrupt store, missing directory, permission error, and schema-version mismatch must be normalized into UI-facing errors.
- `ReagentTemplateStore`, `PreparationRecordStore`, and `WBLoadingRecordStore` are the only current P0/P1 stores eligible for future active integration through this adapter.
- `CalculationRecordStore`, BCA store, and `CellExperimentRecordStore` are future placeholders and must keep save/history disabled until implemented.

## 5. File Picker Export Plan

`FilePickerExportAdapter` separates copy preview from file export.

| Area | Allowed In UI-C2 | Required State |
| --- | --- | --- |
| Quick Calculator | Copy only. | Save history adapter-needed; export disabled/future. |
| Dynamic Formula Solver | Copy only. | Save history adapter-needed; export disabled/future. |
| Reagent Preparation | Copy summary first. | Export disabled until export format and file picker are defined. |
| WB Loading | Copy table/summary first; Markdown/CSV export can be planned. | Export requires file picker and overwrite handling before active. |
| SDS-PAGE | Copy table first; XLSX export can be planned later. | Export requires file picker and adapter state. |
| BCA / OD | Copy preview only if helper exposes safe text. | Save/export disabled until record/export model exists. |
| ELISA | Disabled. | Backend missing. |
| Cell records | Disabled. | Record store missing. |
| Image Processing | Disabled. | External engine adapter missing. |

Failure handling must cover:

- User cancels file selection.
- Target path exists and user declines overwrite.
- Parent path is missing.
- Permission denied.
- Invalid extension or unsupported format.
- Backend export helper raises a domain-specific error.
- Disk write fails after confirmation.

No export button may become the primary action unless the page has a real backend result, file picker adapter, disabled-state tests, and a visible review notice.

## 6. Error Normalization Plan

All backend exceptions should become the same UI structure:

| Field | Meaning |
| --- | --- |
| `severity` | `info`, `warning`, `error`, or `blocked`. |
| `user_message` | Short Chinese user-facing message. |
| `technical_detail` | Optional developer/detail text for diagnostics. |
| `affected_field` | Optional field key for form highlighting. |
| `suggested_action` | What the user can do next. |
| `blocking` | Whether the action/result should be blocked. |

Coverage:

| Error Source | UI Treatment |
| --- | --- |
| `CalculationError` | Field-level error or warning row; no fake result. |
| `ReagentTemplateError` | Template validation row; save remains disabled. |
| `WBLoadingCalculatorError` | Result/warning panel row; affected sample highlighted when possible. |
| `SdsPageGelTemplateError` | Template/config row; XLSX export remains disabled until valid output and file picker exist. |
| `BcaAssayError` | BCA MVP warning/blocker row; no formal quantification claim. |
| Storage errors | Adapter-needed or blocking storage row; no fallback write to `~/.labtools`. |
| File export errors | Export warning/blocker row; copy action remains separate if safe. |

## 7. Result / Warning View Model Plan

All LabTools result pages should render through a shared view model:

| Field | Required Use |
| --- | --- |
| `primary_result` | The headline calculation result, if any. |
| `secondary_results` | Supporting values and converted units. |
| `result_table` | Structured table rows and columns. |
| `warning_rows` | Visible warnings tied to fields/rows. |
| `review_notice` | Always visible before bench use. |
| `copy_text` | Safe text for clipboard copy. |
| `export_state` | `active`, `disabled_missing_file_picker`, `disabled_backend_missing`, etc. |
| `save_state` | `active`, `disabled_missing_storage_adapter`, etc. |
| `status_chip` | Text-labelled status. |
| `semantic_key` | Stable semantic key for tests and UI state. |

The view model must not encode fake success. `status_chip` and icons are auxiliary; the result semantic and disabled state remain authoritative.

## 8. Disabled / Adapter-Needed State Model

Use these canonical states in UI-C2 planning and tests:

| State | Meaning | Example |
| --- | --- | --- |
| `active` | Action is backed by implemented backend and required UI adapter. | Copy calculated WB table. |
| `disabled_missing_storage_adapter` | Backend model exists, but project-scoped storage adapter is absent. | Save reagent template. |
| `disabled_missing_file_picker` | Export helper exists, but UI file picker/overwrite flow is absent. | Export WB CSV/Markdown. |
| `disabled_backend_missing` | UI exists but backend capability is missing. | ELISA run. |
| `shell_only` | Page is IA/visual shell without runtime operation. | Cell Experiment Workspace. |
| `blocked_until_backend` | Must wait for backend model/store/executor. | ELISA / Immuno-Absorbance. |
| `future` | Planned but not in current implementation batch. | Calculation history store. |
| `testing_preview_only` | Can preview testing/MVP output but cannot claim production. | BCA / OD MVP preview. |

Buttons must keep text labels such as `需存储适配`, `需文件选择器`, `后端未完成`, or `暂未开放`.

## 9. UI-C2 Implementation Batches

### 9.1 First Batch

| Page | Implementation Aim | Required Boundaries |
| --- | --- | --- |
| LabTools Home | Apply accepted three-entry IA and revised text. | No save/export; no ImageJ/Fiji first-level card; add review notice. |
| Quick Calculator + Formula Solver | Render backend-ready task/formula specs through adapters and result view model. | Copy allowed; save/history/export disabled or adapter-needed. |
| Reagent Template / Preparation shell | Render template/preparation structure with adapter-safe states. | Save template/preparation and export remain disabled or adapter-needed until storage/export adapters are implemented. |

### 9.2 Second Batch

| Page | Implementation Aim | Required Boundaries |
| --- | --- | --- |
| Reagent Template Editor side panel | Add validation, dirty state, and disabled save behavior. | No active persistence without storage adapter. |
| Reagent Preparation Run preview | Render calculation preview and copy summary. | Save/export adapter-needed. |
| WB Loading focused page | Render WB config, sample table, result table, lane schematic, and warnings. | Downstream protein steps remain placeholders; save/export adapter-needed. |

### 9.3 Third Batch

| Page | Implementation Aim | Required Boundaries |
| --- | --- | --- |
| SDS-PAGE placeholder/subpage | Planning-oriented or adapter-safe page. | XLSX/export adapter-needed; no full workflow claim. |
| BCA / OD MVP boundary | Render matrix/annotation/fit preview as MVP/testing only. | Save/export disabled; no ELISA/4PL/formal report. |
| Cell Experiment Workspace shell | Render recalibrated three-zone IA. | No real save, no fake records/timeline, no image analysis execution. |
| ELISA / Immuno-Absorbance boundary | Render blocked page. | No active ELISA, 4PL, report, save, export. |
| Image Processing Workspace boundary | Render Settings-linked external engine boundary. | No ImageJ/Fiji execution, macros, auto ROI, auto cell counting, auto band recognition. |

The full sequence table is:

`docs/ui/UI_C2a_labtools_implementation_sequence_20260522.csv`

## 10. Testing Plan

| Test Area | Purpose |
| --- | --- |
| Adapter contract tests | Verify storage adapter returns explicit paths, never defaults to `~/.labtools`, and reports unavailable roots. |
| File picker export adapter tests | Verify cancel, overwrite denied, permission errors, missing path, unsupported extension, and backend export errors. |
| View model tests | Verify result/warning/review/copy/save/export/status structures are stable. |
| Disabled state tests | Verify missing adapters keep save/export/history disabled and text-labelled. |
| No default write tests | Verify opening LabTools UI and constructing adapter without project root does not create or write `~/.labtools`. |
| UI smoke tests | Verify LabTools Home and first-batch pages render without changing backend state. |
| IA regression tests | Verify exactly three LabTools first-level entries and no ImageJ/Fiji first-level entry. |
| Save/export behavior tests | Verify disabled buttons do not call stores/export helpers. |
| Shell-only boundary tests | Verify Cell, ELISA, BCA, Image Processing pages keep correct boundary states. |

## 11. Not In This Stage

UI-C2a does not:

- Implement real PySide pages.
- Refactor LabTools UI runtime.
- Modify LabTools backend business logic.
- Add ELISA backend.
- Add cell experiment record store.
- Add ImageJ/Fiji runner.
- Enable save/export/history/batch actions.
- Replace icons or active assets.
- Execute UI-B10.
- Touch App icon, Finder icon, `.icns`, iconset, Info.plist, LaunchServices.
- Package, sign, run package smoke, run packaged app, modify `dist/**`, or overwrite desktop entry.

## 12. Verification

| Command | Result |
| --- | --- |
| `python3 - <<'PY' ... CSV structure check ... PY` | Passed: 12 rows, 12 columns, unique `screen_id` values. |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
