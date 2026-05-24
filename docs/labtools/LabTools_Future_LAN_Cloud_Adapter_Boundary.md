# LabTools Future LAN And Cloud Adapter Boundary

LAN and cloud sync are future adapter options, not current LabTools behavior.
The current LabTools data line remains local-first. This document defines the
boundary that future LAN or cloud work must respect.

## Current State

Current LabTools does not include:

- LAN server.
- Cloud sync.
- Multi-user permissions.
- Automatic conflict merging.
- Public network service.
- Token, account, or remote-authentication flow.
- Port listening or background network daemon.
- Network tests.

The only active runtime path is local data access through
`LabToolsDataSourceAdapter` implementations. `FutureLanDataSourceAdapter` and
`FutureCloudDataSourceAdapter` are disabled placeholders only.

Placeholder status must remain:

```text
status = disabled_future_option
data_source_mode = future_lan | future_cloud
read_enabled = false
write_enabled = false
history_enabled = false
export_enabled = false
reason = "Future adapter only; LAN/cloud sync not implemented."
```

## Required Future Entry Point

Future LAN or cloud support must enter through a new
`LabToolsDataSourceAdapter` implementation.

The future adapter must reuse:

- Local data contract fields for reagent, sample, cell, freeze vial, record
  index, and audit log records.
- `source_mode` values, including `future_lan` and `future_cloud`.
- Version checks and expected-version blocking.
- Audit log events for create, update, archive, status changes, import, and
  export.
- The same summary/read models already used by the UI.

Future LAN/cloud work must not require UI pages to read remote payloads
directly. UI code must not import a server client, database client, cloud SDK,
or local JSON store directly. The UI remains adapter-driven.

## Data Governance Rules

Future LAN/cloud adapters must preserve the existing local-first data rules:

- A write must either pass validation and expected-version checks or fail with a
  graceful blocked result.
- Conflicts must not be silently merged.
- Audit/version history must not be bypassed.
- Record summaries are not formal reports.
- Reagent/sample inventory or sample volume must not be automatically deducted
  unless a later explicit inventory phase defines that behavior.
- Reagent templates must not be overwritten by experiment-run UI actions.
- Sample status must not be changed by calculation previews.

## Explicitly Forbidden In This Phase

This phase must not add:

- Server code.
- Client network code.
- Token/auth code.
- Port listeners.
- Background sync jobs.
- Device discovery.
- Network tests.
- Shared-folder database behavior.
- Direct sharing of SQLite or JSON files across machines.
- Public-cloud SDK integration.

## Future LAN Readiness Gate

Before LAN implementation can begin, a separate task must define:

- Server storage authority.
- Adapter API shape.
- Authentication and permission model.
- Conflict policy.
- Backup and restore policy.
- Deployment and packaging expectations.
- Test strategy for offline, single-user, concurrent, and network-failure
  cases.

Until that gate is accepted, `future_lan` and `future_cloud` remain disabled
placeholders and must not alter LabTools runtime behavior.

## LAN-LT1 Server Skeleton

`labtools.lan_server` provides a contract-only server skeleton. It exposes:

- `LabToolsLanServerConfig`.
- `LabToolsLanServerStatus`.
- `LabToolsLanServerSkeleton`.
- `build_lan_server_skeleton()`.

The skeleton is importable for future planning and tests, but it does not bind a
port, listen on the network, start a background service, authenticate users, or
synchronize data. `start()` and `stop()` return disabled non-listening status.

This keeps the future LAN line visible without changing the current local-first
runtime.
