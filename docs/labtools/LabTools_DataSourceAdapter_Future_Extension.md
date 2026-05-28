# LabTools DataSourceAdapter Future Extension

## Adapter Boundary

LabTools UI must access local data through an adapter:

```text
LabTools UI
-> LocalLabToolsDataSourceAdapter or ReadOnlyLabToolsDataSourceAdapter
-> LocalLabToolsDataStore
```

UI code must not import the JSON store directly. This keeps the same UI surface usable when future LAN or cloud adapters are added.

## Current Adapters

`LocalLabToolsDataSourceAdapter` supports local read/write/history/export capability when the local JSON store is initialized and valid.

`ReadOnlyLabToolsDataSourceAdapter` supports local reads and history display while disabling writes and exports.

Both adapters report:

```text
data_source_mode
read_enabled
write_enabled
history_enabled
export_enabled
reason
```

## Future Adapters

`FutureLanDataSourceAdapter` and `FutureCloudDataSourceAdapter` are placeholders only. Their status must remain:

```text
status = disabled_future_option
read_enabled = false
write_enabled = false
history_enabled = false
export_enabled = false
reason = Future adapter only; LAN/cloud sync not implemented.
```

Future LAN or cloud implementation must reuse the local contracts and audit rules. It must not add direct UI dependencies on network APIs, shared SQLite files, or cloud SDK payloads.

## Explicit Non-Goals

Current LabTools does not include:

- LAN Server.
- Cloud sync.
- Multi-user permissions.
- Automatic conflict merging.
- Direct sharing of SQLite or JSON files over a network folder.
- Inventory auto-deduction.
- Formal report generation from record summaries.
