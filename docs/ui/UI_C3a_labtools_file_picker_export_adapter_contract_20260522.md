# UI-C3a LabTools File Picker Export Adapter Contract

Date: 2026-05-22

## 1. Purpose

`FilePickerExportAdapter` will make exports user-triggered and path-explicit. It prevents background exports, default desktop writes, and package-level fallback paths.

This is a planning contract only. UI-C3a does not implement file picking or export writing.

## 2. Contract Shape

```text
FilePickerExportAdapter
  choose_save_path(export_kind, suggested_filename, allowed_extensions) -> ExportPathResult
  validate_extension(path, allowed_extensions) -> ExportPathResult
  confirm_overwrite(path) -> OverwriteDecision
  write_with_backend(export_job) -> ExportWriteResult
  normalize_error(error, action, path) -> LabToolsAdapterIssue
```

## 3. Export Path Events

| Event | Required behavior |
|---|---|
| User cancels path selection | No backend export call; non-blocking info row. |
| Path has unsupported suffix | No backend export call; blocking error row. |
| Parent directory missing | No backend export call unless user reselects valid path. |
| File exists and overwrite declined | No backend export call; non-blocking warning row. |
| File exists and overwrite confirmed | Proceed only for allowed formats and active export job. |
| Permission denied | No success state; blocking error row with suggested action. |
| Backend writer failure | No success state; error row with technical detail. |
| Partial write failure | No export-complete state; diagnostics issue required. |

## 4. Format Policy

Allowed for future planning:

| Format | Current planning surface |
|---|---|
| Markdown / TXT | Reagent preparation summary, WB loading summary |
| CSV | WB loading table, reagent preparation component table |
| XLSX | SDS-PAGE future export only after file picker and backend helper review |
| JSON draft | Project-scoped internal draft snapshots only |

Forbidden until a separate stage:

| Format | Reason |
|---|---|
| PDF | Formal report/export boundary not ready. |
| DOCX | Formal report/export boundary not ready. |
| formal report package | Requires report system and provenance contract. |
| ELISA formal export | ELISA backend not complete. |
| BCA formal export | BCA formal record/export model missing. |
| Cell record export | Cell record store missing. |
| ImageJ/Fiji analysis result export | External engine adapter and result model missing. |

## 5. Page Export Policy

| Page | Copy state | Export state |
|---|---|---|
| Quick Calculator | active after valid result | future or disabled_missing_file_picker |
| Dynamic Formula Solver | active after valid result | future or disabled_missing_file_picker |
| Reagent Template | copy summary allowed where safe | disabled_missing_storage_adapter / disabled_missing_file_picker |
| Reagent Preparation | copy summary active | Markdown/CSV future after file picker |
| WB Loading | copy table active | Markdown/CSV future after file picker |
| SDS-PAGE | copy preview future | XLSX future after file picker and backend review |
| BCA / OD | copy preview only | disabled_backend_missing |
| Cell Experiment | disabled | blocked_future |
| ELISA / Immuno-Absorbance | disabled | blocked_until_backend |
| Image Processing | disabled | blocked_until_external_engine_adapter |

## 6. Export Job Shape

```text
LabToolsExportJob
  export_kind: reagent_summary | wb_loading_table | sds_page_xlsx | json_draft
  source_page_key: str
  format: md | txt | csv | xlsx | json
  suggested_filename: str
  allowed_extensions: tuple[str, ...]
  payload_view_model: object
  writer: callable
  requires_project_storage: bool
  requires_file_picker: bool
```

## 7. UI Rules

- Export buttons must stay disabled until both backend writer and file picker are available.
- File picker availability alone must not imply export availability.
- Export success must never mean report-ready.
- Export failure must preserve the result preview and show an error row.
- Copy actions are not exports and must not write files.
- No export path should default to `~/.labtools`, Desktop, Downloads, or project storage without explicit user selection, except future project-internal JSON draft snapshots gated by storage adapter.

## 8. Required Future Tests

- cancel path selection calls no writer
- unsupported suffix calls no writer
- overwrite declined calls no writer
- permission denied normalizes blocking error
- backend writer exception normalizes technical detail
- partial write failure does not show success
- export path and output extension are validated
- forbidden formats remain disabled
