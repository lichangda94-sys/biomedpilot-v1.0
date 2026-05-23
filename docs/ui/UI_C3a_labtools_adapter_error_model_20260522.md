# UI-C3a LabTools Adapter Error Model

Date: 2026-05-22

## 1. Purpose

This document defines the normalized UI-facing error model for future LabTools storage, export, and history adapters.

It is planning-only. UI-C3a does not implement error normalization code or enable adapter actions.

## 2. Normalized Issue Shape

```text
LabToolsAdapterIssue
  severity: info | warning | error | blocked
  user_message: str
  technical_detail: str | None
  affected_action: str
  affected_path: str | None
  affected_field: str | None
  suggested_action: str | None
  blocking: bool
  retry_allowed: bool
  semantic_key: str
```

User-facing text must be actionable and must not expose stack traces by default. `technical_detail` can be available for developer diagnostics.

## 3. Severity Rules

| Severity | Meaning | UI behavior |
|---|---|---|
| info | User canceled or action was intentionally skipped. | Non-blocking row; preserve result preview. |
| warning | Recoverable condition or user decision needed. | Non-blocking warning row; action may be retried. |
| error | Action failed due to invalid path, extension, or backend writer error. | Blocking row for the affected action only. |
| blocked | Required adapter/backend/store is missing. | Keep button disabled and explain requirement. |

## 4. Error Mapping

| Source | severity | affected_action | blocking | retry_allowed | semantic_key |
|---|---|---|---|---|---|
| missing project storage | blocked | save/history | true | false | `labtools.adapter.storage_missing_project` |
| project storage permission denied | blocked | save/history | true | true | `labtools.adapter.storage_permission_denied` |
| corrupt project LabTools store | blocked | save/history | true | false | `labtools.adapter.storage_schema_error` |
| file picker canceled | info | export | false | true | `labtools.adapter.export_canceled` |
| overwrite declined | warning | export | false | true | `labtools.adapter.export_overwrite_declined` |
| unsupported extension | error | export | true | true | `labtools.adapter.export_unsupported_extension` |
| parent directory missing | error | export | true | true | `labtools.adapter.export_missing_parent` |
| permission denied | error | export | true | true | `labtools.adapter.export_permission_denied` |
| backend writer failure | error | export | true | true | `labtools.adapter.export_writer_failed` |
| partial write failure | error | export | true | false | `labtools.adapter.export_partial_write` |
| missing CalculationRecordStore | blocked | history | true | false | `labtools.adapter.calculation_history_future` |
| missing BCA record/export store | blocked | save/export | true | false | `labtools.adapter.bca_store_missing` |
| missing CellExperimentRecordStore | blocked | save/history | true | false | `labtools.adapter.cell_store_missing` |
| missing ELISA backend | blocked | save/export/run | true | false | `labtools.adapter.elisa_backend_missing` |
| missing ImageJ/Fiji result adapter | blocked | export/run | true | false | `labtools.adapter.image_engine_missing` |

## 5. Example Issues

```text
severity: blocked
user_message: Select or create a BioMedPilot project before saving LabTools records.
technical_detail: project_storage_root is None
affected_action: save
affected_path: null
suggested_action: Open a project with project storage, then retry.
blocking: true
retry_allowed: false
semantic_key: labtools.adapter.storage_missing_project
```

```text
severity: info
user_message: Export canceled. No file was written.
technical_detail: file picker returned canceled
affected_action: export
affected_path: null
suggested_action: Choose an export path when ready.
blocking: false
retry_allowed: true
semantic_key: labtools.adapter.export_canceled
```

```text
severity: error
user_message: This export type only supports CSV or Markdown.
technical_detail: selected suffix .pdf for wb_loading_table
affected_action: export
affected_path: /user/selected/output.pdf
suggested_action: Choose a .csv or .md file.
blocking: true
retry_allowed: true
semantic_key: labtools.adapter.export_unsupported_extension
```

## 6. UI Requirements

- The affected button remains disabled or returns to ready state based on `blocking` and `retry_allowed`.
- Error rows must not remove calculation previews unless the preview itself is invalid.
- Save/export/history failures must not create success chips.
- Adapter errors must not be represented only by icons.
- File write errors must not be converted into report-ready or export-complete states.
