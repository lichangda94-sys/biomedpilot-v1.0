# LabTools Local Data Contracts

## Common Fields

Every local LabTools data object carries traceability fields:

```text
id
version
status
created_at
updated_at
created_by
updated_by
source_mode
```

Allowed `source_mode` values are:

```text
local
imported
future_lan
future_cloud
```

Local writes start at `version = 1`. Updates increment the version and must provide the expected current version. Archive actions are status changes, not physical deletes.

## Entity Contracts

The local store covers:

- `ReagentRecord`: name, category, concentration, unit, vendor, catalog number, lot number, storage location, expiry date, notes.
- `SampleRecord`: sample name, sample type, linked experiment, project, concentration, concentration unit, volume, volume unit, storage location, notes.
- `CellProfileRecord`: cell name, species, disease, source, passage, culture medium, mycoplasma status, storage status, notes.
- `FreezeBatchRecord`: cell id, batch name, passage, freeze date, vial count, storage location.
- `FreezeVialRecord`: freeze batch id, vial label, location, status.
- `LabToolsRecordIndexEntry`: record type, title, linked reagents, linked samples, linked cells, status, summary, artifact refs.
- `LabToolsAuditLogEntry`: entity type, entity id, action, user id, timestamp, before version, after version, summary, source mode.
- `LabToolsDataStoreManifest`: schema version, timestamps, entity counts, source mode.

## Record Index Types

The record index stores summaries only. Supported record types are:

```text
reagent_preparation
formula_solver
quick_calculation
wb_loading
bca_od
cell_passage
cell_thawing
cell_plating
sds_page
image_processing_boundary
```

The record summary is not a formal report and must not contain large image files, raw external analysis outputs, or generated PDF/DOCX artifacts.

## Audit Rules

Every create, update, archive, status update, import, export, or restore operation must append an audit log entry. Local mode uses `local_user` until a future authenticated adapter exists.

## Inventory Rules

The first local-first stage treats reagents, samples, cells, batches, and vials as selectable and traceable records. It does not automatically deduct reagent quantity, deduct sample volume, change cell state, or overwrite sample concentration from BCA output. BCA-derived concentration changes should be represented as update proposals until a user confirms them.
