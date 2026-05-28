# UI-C3a LabTools Storage Adapter Contract

Date: 2026-05-22

## 1. Purpose

`BioMedPilotLabToolsStorageAdapter` will provide explicit BioMedPilot project-scoped storage to LabTools stores. It prevents the desktop UI from writing to standalone LabTools defaults, especially `~/.labtools`.

This is a planning contract only. No adapter is implemented in UI-C3a.

## 2. Directory Contract

Required root:

```text
project_storage/labtools/
  templates/
  records/
  exports/
  attachments/
  diagnostics/
```

Recommended subdirectories:

```text
project_storage/labtools/templates/reagents/
project_storage/labtools/templates/sds_page/
project_storage/labtools/records/reagent_preparations/
project_storage/labtools/records/wb_loading/
project_storage/labtools/records/calculations/
project_storage/labtools/records/bca/
project_storage/labtools/records/cell_experiments/
project_storage/labtools/exports/reagents/
project_storage/labtools/exports/wb_loading/
project_storage/labtools/exports/sds_page/
project_storage/labtools/attachments/images/
project_storage/labtools/diagnostics/adapter_logs/
```

Only the top-level directory contract is frozen. Subdirectories may be refined during implementation, but they must remain under `project_storage/labtools/`.

## 3. Contract Shape

```text
BioMedPilotLabToolsStorageAdapter
  project_id: str
  project_storage_root: Path
  labtools_root: Path
  status: active | disabled_missing_project_storage | blocked_permission_error | blocked_schema_error
  resolve_path(category, key) -> PathResolution
  resolve_store_path(store_key) -> PathResolution
  create_reagent_template_store() -> AdapterStoreResult
  create_preparation_record_store() -> AdapterStoreResult
  create_wb_loading_record_store() -> AdapterStoreResult
  planned_calculation_record_store() -> DisabledCapability
  planned_bca_record_store() -> DisabledCapability
  planned_cell_experiment_record_store() -> DisabledCapability
  planned_elisa_store() -> DisabledCapability
  planned_image_processing_export_store() -> DisabledCapability
```

## 4. Path Resolution Rules

| Store key | Planned path | Status |
|---|---|---|
| `reagent_templates` | `project_storage/labtools/templates/reagents/` | adapter_required |
| `reagent_preparation_records` | `project_storage/labtools/records/reagent_preparations/` | adapter_required |
| `wb_loading_records` | `project_storage/labtools/records/wb_loading/` | adapter_required |
| `sds_page_templates` | `project_storage/labtools/templates/sds_page/` | adapter_required_later |
| `calculation_history` | `project_storage/labtools/records/calculations/` | future_missing_store |
| `bca_records` | `project_storage/labtools/records/bca/` | blocked_future |
| `cell_experiment_records` | `project_storage/labtools/records/cell_experiments/` | blocked_future |
| `elisa_records` | `project_storage/labtools/records/elisa/` | blocked_until_backend |
| `image_processing_exports` | `project_storage/labtools/exports/image_processing/` | blocked_until_external_engine_adapter |

## 5. No-Write Rules

- Opening LabTools Home must not create directories.
- Opening Quick Calculator, Formula Solver, Reagent Preparation, WB Loading, or boundary pages must not create stores.
- Missing project storage must return `disabled_missing_project_storage`.
- Adapter construction must not create `~/.labtools`.
- Store construction is allowed only after user-confirmed save/history enablement in a future implementation stage.
- All file writes must be covered by tests proving the resolved path is under `project_storage/labtools/`.

## 6. Store Eligibility

| Store | Current state | Future enablement rule |
|---|---|---|
| ReagentTemplateStore | backend exists | Enable only with active storage adapter and explicit save. |
| PreparationRecordStore | backend exists | Enable only with active storage adapter and explicit save. |
| WBLoadingRecordStore | backend exists | Enable only with active storage adapter and explicit save. |
| CalculationRecordStore | missing | History remains future. |
| BCA record/export store | missing | Blocked/future until formal record model exists. |
| CellExperimentRecordStore | missing | Blocked/future until cell store exists. |
| ELISA store/export | backend missing | Blocked until ELISA backend is complete. |
| Image Processing export | external adapter missing | Blocked until ImageJ/Fiji result adapter exists. |

## 7. Adapter Result Types

```text
PathResolution
  status: resolved | disabled | blocked
  path: Path | None
  reason: str
  semantic_key: str

AdapterStoreResult
  status: active | disabled | blocked
  store: object | None
  root_path: Path | None
  issue: LabToolsAdapterIssue | None

DisabledCapability
  status: future | blocked_until_backend | blocked_until_external_adapter
  label: str
  reason: str
  required_stage: str
```

## 8. Required Future Tests

- adapter refuses missing project storage
- adapter resolves eligible paths under `project_storage/labtools/`
- adapter never resolves to `~/.labtools`
- opening LabTools pages creates no files
- disabled stores do not instantiate fake stores
- permission errors produce normalized blocked issues
- corrupt/schema errors preserve UI preview and keep save/history disabled
