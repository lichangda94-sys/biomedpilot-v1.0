# LabTools Local-First Data Architecture Plan

## Decision

LabTools will build the local data system first. The current phase does not implement a LAN server, cloud sync, multi-user permissions, network deployment, conflict merging, or a complete LIMS.

The implementation path is:

```text
LabTools UI
-> LabTools runtime
-> LabToolsDataSourceAdapter
-> LocalLabToolsDataStore
-> project_storage/labtools JSON files
```

Future LAN or cloud support must be added as a new data source adapter that reuses the local data contract. It must not require UI pages to read JSON, SQLite, network shares, or remote APIs directly.

## Local Storage Layout

The target project layout is:

```text
project_storage/labtools/
├── labtools_data_store.json
├── labtools_record_index.json
├── labtools_audit_log.json
├── backups/
└── exports/
```

The standalone LabTools package also supports an explicit local data root for tests and adapters. Desktop integration should pass the BioMedPilot project storage path instead of relying on a user-home default.

## Boundaries

This phase does not implement:

- LAN Server or client-server deployment.
- Cloud sync or public network sync.
- Multi-user permissions.
- Automatic conflict merging.
- Automatic reagent or sample inventory deduction.
- Direct sharing of SQLite or JSON database files over a network folder.
- Formal report generation from record summaries.

## Relationship To UI-C3b And UI-C3c

UI-C3b established record/export contracts for LabTools workflows. UI-C3c established read-only storage adapter boundaries. This local-first phase extends those decisions by adding a real local data contract, a JSON store, audit logging, version checks, and adapter-level access, while keeping UI write integration as a later controlled step.

## Release Gate

Before enabling a user-visible write flow, LabTools must have:

- Versioned data contracts for reagent, sample, cell, freeze inventory, record index, and audit log.
- Local JSON store initialization and validation.
- Audit log entries for every local write.
- Expected-version checks for updates.
- Backup and restore design.
- Future adapter placeholders that are disabled by default.
