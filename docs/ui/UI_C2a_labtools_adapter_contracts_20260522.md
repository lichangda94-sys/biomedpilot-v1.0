# UI-C2a LabTools Adapter Contracts

Date: 2026-05-22

## 1. Scope

This document defines adapter contracts required before the LabTools PySide UI can safely move from mockup references into runtime pages.

The contracts are planning-level only. They do not implement adapters, modify backend business logic, add persistence, enable exports, package, or touch App icon / Finder icon / `.icns` / Info.plist / LaunchServices.

## 2. BioMedPilotLabToolsStorageAdapter

### 2.1 Purpose

`BioMedPilotLabToolsStorageAdapter` provides explicit BioMedPilot project-scoped storage paths to LabTools stores. It prevents desktop UI from falling back to LabTools package defaults such as `LABTOOLS_STORAGE_ROOT` or `~/.labtools`.

### 2.2 Contract Shape

```text
BioMedPilotLabToolsStorageAdapter
  project_id: str
  project_storage_root: Path
  labtools_root: Path
  status: active | disabled_missing_project_storage | blocked_permission_error | blocked_corrupt_store
  resolve_store_path(store_key) -> PathResolution
  create_reagent_template_store() -> AdapterStoreResult
  create_preparation_record_store() -> AdapterStoreResult
  create_wb_loading_record_store() -> AdapterStoreResult
  planned_calculation_record_store() -> DisabledCapability
  planned_bca_record_store() -> DisabledCapability
  planned_cell_experiment_record_store() -> DisabledCapability
```

Planning note: exact class/module placement should be decided during UI-C2 implementation, but it should live in BioMedPilot app integration code, not inside LabTools backend business logic.

### 2.3 Path Resolution

| Store Key | Path Under Project Storage | Current Backend Store |
| --- | --- | --- |
| `reagent_templates` | `labtools/reagents/templates/` | `ReagentTemplateStore(path=...)` |
| `reagent_preparation_records` | `labtools/reagents/preparations/` | `PreparationRecordStore(path=...)` |
| `wb_loading_records` | `labtools/protein/wb_loading/` | `WBLoadingRecordStore(path=...)` |
| `sds_page_templates` | `labtools/protein/sds_page/templates/` | Future adapter around template JSON/store helpers. |
| `calculation_history` | `labtools/calculations/history/` | Future only; no `CalculationRecordStore` yet. |
| `bca_records` | `labtools/protein/bca_records/` | Future only; no formal record/export store yet. |
| `cell_experiment_records` | `labtools/cell_experiments/records/` | Future only; no store yet. |

### 2.4 Required Rules

- The adapter must require a BioMedPilot project storage root.
- If the root is missing, it must return `disabled_missing_project_storage`, not create `~/.labtools`.
- Store constructors must receive explicit paths.
- Opening LabTools Home must not create directories or files.
- Directory creation should occur only when the user performs a confirmed save action and the adapter is active.
- Adapter status must be displayed before save buttons become active.
- Corruption, permission, and schema/version issues must be normalized for UI display.

### 2.5 Store Eligibility

| Store / Capability | UI-C2 Eligibility | Reason |
| --- | --- | --- |
| `ReagentTemplateStore` | Eligible after adapter. | Backend-ready, but must use explicit project path. |
| `PreparationRecordStore` | Eligible after adapter. | Backend-ready, but save must wait for adapter. |
| `WBLoadingRecordStore` | Eligible after adapter. | Backend-ready, but save must wait for adapter. |
| `SdsPageGelTemplateStore` | Planning only. | Current store status is testing/in-memory; persistence adapter needed. |
| `CalculationRecordStore` | Future disabled. | Store missing. |
| BCA store | Future disabled. | Record/export model missing. |
| Cell experiment record store | Future disabled. | Backend missing. |

## 3. FilePickerExportAdapter

### 3.1 Purpose

`FilePickerExportAdapter` handles user-chosen export destinations and filesystem safety. Backend export helpers should not be called until the user has selected a path and overwrite/permission checks pass.

### 3.2 Contract Shape

```text
FilePickerExportAdapter
  choose_save_path(export_kind, suggested_filename, allowed_extensions) -> ExportPathResult
  confirm_overwrite(path) -> OverwriteDecision
  write_with_backend(export_job) -> ExportResult
  normalize_export_error(error) -> NormalizedUiIssue
```

### 3.3 Export State Matrix

| Page | Copy | Export | Export State |
| --- | --- | --- | --- |
| Quick Calculator | Allowed when result exists. | Not P0. | `future` or `disabled_missing_file_picker`. |
| Formula Solver | Allowed when result exists. | Not P0. | `future` or `disabled_missing_file_picker`. |
| Reagent Preparation | Copy summary allowed. | Future Markdown/CSV only after format and picker. | `disabled_missing_file_picker`. |
| WB Loading | Copy table/summary allowed. | Markdown/CSV planned. | `disabled_missing_file_picker` until adapter exists. |
| SDS-PAGE | Copy table allowed. | XLSX planned. | `disabled_missing_file_picker` until adapter exists. |
| BCA / OD | Copy preview only if safe. | Disabled. | `disabled_backend_missing`. |
| ELISA | Disabled. | Disabled. | `blocked_until_backend`. |
| Cell Records | Disabled. | Disabled. | `blocked_until_backend`. |
| Image Processing | Disabled. | Disabled. | `blocked_until_backend`. |

### 3.4 Required Error Handling

| Event | UI Result |
| --- | --- |
| User cancels file picker | Non-blocking info row; no export. |
| File exists and overwrite declined | Non-blocking warning row; no export. |
| Unsupported extension | Blocking export error; keep result preview. |
| Parent directory missing | Blocking export error unless user reselects. |
| Permission denied | Blocking export error with suggested path/action. |
| Backend export helper raises | Blocking export error with technical detail available. |
| Partial write failure | Blocking export error; no report-ready or export-complete state. |

## 4. UI-Facing Error Normalization

### 4.1 Normalized Issue Shape

```text
NormalizedUiIssue
  severity: info | warning | error | blocked
  user_message: str
  technical_detail: str | None
  affected_field: str | None
  suggested_action: str | None
  blocking: bool
  semantic_key: str
```

### 4.2 Error Source Mapping

| Source | Example UI Semantic Key | Required UI Behavior |
| --- | --- | --- |
| `CalculationError` | `labtools.error.calculation_invalid_input` | Highlight affected input; do not fabricate result. |
| `ReagentTemplateError` | `labtools.error.reagent_template_invalid` | Show validation row; save remains disabled. |
| `WBLoadingCalculatorError` | `labtools.error.wb_loading_invalid` | Show sample/warning row; keep table empty if blocked. |
| `SdsPageGelTemplateError` | `labtools.error.sds_page_template_invalid` | Show template/config issue; export remains disabled. |
| `BcaAssayError` | `labtools.error.bca_assay_invalid` | Show MVP warning/blocker; no formal result claim. |
| Storage adapter error | `labtools.error.storage_adapter_unavailable` | Keep save/history disabled; no fallback write. |
| File picker/export error | `labtools.error.export_unavailable` | Keep export disabled or failed; preserve copy if safe. |

### 4.3 Severity Rules

| Severity | Use |
| --- | --- |
| `info` | User canceled export, shell-only explanation, helper copy. |
| `warning` | Non-blocking calculation warning such as low volume or review-needed output. |
| `error` | Invalid inputs or export failure that prevents that action. |
| `blocked` | Backend missing, storage adapter missing, file picker missing, external engine missing. |

## 5. Adapter Test Expectations

| Test | Expected Assertion |
| --- | --- |
| No project root | Adapter status is unavailable and no directories are created. |
| Store path resolution | Current eligible stores resolve under project storage `labtools/...`. |
| No default write | No call path writes to `~/.labtools` from desktop UI adapter. |
| Disabled future store | Calculation/BCA/cell stores return disabled capability, not fake stores. |
| Export cancel | No backend export helper is called. |
| Export overwrite denied | No write occurs and UI issue is non-blocking. |
| Permission denied | Error is normalized and result preview remains. |
| Unsupported extension | Export blocked and required extension is explained. |

## 6. Implementation Guardrails

- Do not put adapter code into LabTools backend modules if it depends on BioMedPilot project state.
- Do not make storage adapter construction a side effect of opening LabTools Home.
- Do not make file picker availability imply that export is complete; export also needs backend output and format-specific helper.
- Do not let icons or green status chips replace disabled state text.
- Do not add UI-B10, App icon, packaging, signing, or desktop-entry work to adapter implementation.
