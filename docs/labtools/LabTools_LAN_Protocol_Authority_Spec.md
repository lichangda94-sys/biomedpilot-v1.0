# LabTools LAN Protocol And Authority Spec

Date: 2026-05-25

## Purpose

This document defines the minimum LAN MVP protocol and authority boundary for
LabTools. It is a design gate, not a runtime implementation.

This phase does not add server runtime code, client network I/O, auth, token
storage, port listeners, sync jobs, write endpoints, or UI behavior.

## MVP Mode

The first LAN product line must start as:

```text
single_host_authority
read_only_client
adapter_driven_ui
no_automatic_conflict_merge
no_inventory_deduction
```

One host owns the authoritative LabTools local data store. LAN clients may read
summaries from that host only after a later runtime phase implements read-only
endpoints. Clients must not access the host JSON files directly.

## Server Authority

The LAN server is the only process allowed to touch the authoritative LabTools
local data store in LAN mode.

The server must access data through:

```text
LocalLabToolsDataSourceAdapter
or
ReadOnlyLabToolsDataSourceAdapter
```

The server must not expose filesystem paths, raw JSON store files, SQLite files,
or local lock files to clients.

The client must access data through:

```text
LabToolsLanClientDataSourceAdapter
```

The UI must continue to access data through runtime/adapter wrappers. UI pages
must not import server code, client transport code, database code, or
`LocalLabToolsDataStore` directly.

## Initial Endpoint Draft

The first real LAN runtime phase may expose only health and read-only data
endpoints.

### Health And Status

```text
GET /health
GET /status
```

`/health` is for process liveness only. It must not read or write LabTools data.

`/status` may report local store status through the data source adapter, but it
must not mutate data.

### Read-Only Data Endpoints

```text
GET /records/summary
GET /reagents
GET /samples
GET /cells
GET /freeze-vials
GET /record-index
```

These endpoints may return summary payloads only. They must not return raw store
documents, local paths, backups, binary files, PDF/DOCX reports, images, or
private runtime configuration.

### Deferred Write Endpoints

Write endpoints are explicitly out of scope for the first LAN runtime phases.

Deferred examples:

```text
POST /reagents
PATCH /reagents/{id}
POST /samples
PATCH /samples/{id}
POST /record-index
PATCH /record-index/{id}/status
```

They require a later controlled write gate covering identity, permission,
expected-version conflict handling, audit user mapping, and UI conflict
presentation.

## Response Envelope

All LAN responses should use a stable envelope:

```json
{
  "ok": true,
  "status": "ready",
  "reason": "",
  "data_source_mode": "future_lan",
  "server_time": "2026-05-25T00:00:00+00:00",
  "schema_version": "labtools_lan_api.v1",
  "data": {}
}
```

For blocked responses:

```json
{
  "ok": false,
  "status": "blocked_store_missing",
  "reason": "local_data store has not been initialized",
  "data_source_mode": "future_lan",
  "server_time": "2026-05-25T00:00:00+00:00",
  "schema_version": "labtools_lan_api.v1",
  "data": null
}
```

The envelope is intentionally simple so UIShell runtime wrappers can handle LAN
responses without directly coupling UI pages to transport details.

## Status Codes And Semantic States

The protocol should preserve semantic status even if an HTTP runtime later maps
responses to numeric status codes.

Required semantic states:

| State | Meaning |
| --- | --- |
| `ready` | Server runtime is alive and the requested read is available. |
| `ready_readonly` | Server can read, but write/export is disabled. |
| `blocked_store_missing` | Authoritative local data store is not initialized. |
| `blocked_invalid_store` | Store exists but is corrupted or fails validation. |
| `blocked_read_disabled` | Adapter reports read disabled. |
| `blocked_write_disabled` | Write attempted before LAN write phase. |
| `blocked_version_conflict` | Future write expected-version mismatch. |
| `disabled_future_option` | LAN/cloud feature remains disabled. |
| `auth_not_implemented` | Auth is required by a future phase but not active now. |

## Read Model Requirements

Read-only LAN responses must preserve the same summary shape already used by
the local UI integration:

- reagent summaries.
- sample summaries, including concentration and concentration unit.
- cell profile summaries.
- freeze vial summaries and status.
- record index summaries.
- adapter status and counts.

LAN read responses must not:

- deduct reagent amount.
- deduct sample volume.
- change sample status.
- update freeze vial status.
- overwrite reagent templates.
- generate formal reports.
- generate PDF/DOCX.
- write audit entries for pure reads.

## Write Transaction Rules

LAN writes are not enabled in the MVP read-only phase.

When a later write phase is approved, writes must follow these rules:

- The client must send `expected_version`.
- The server must compare against the authoritative current version.
- Version mismatch must block the write.
- The server must write an audit log entry for accepted writes.
- No automatic conflict merge is allowed.
- No automatic inventory or sample-volume deduction is allowed.
- User identity mapping must be defined before multi-user writes are allowed.

## Error Handling

Required graceful error behavior:

- Store missing: return blocked envelope, do not initialize automatically unless
  a future explicit admin action is approved.
- Store corrupted: return blocked envelope, do not attempt repair.
- Server unavailable: client adapter returns disconnected/blocked status.
- Malformed response: client adapter returns blocked_invalid_response.
- Version conflict: return blocked_version_conflict.
- Unsupported endpoint: return disabled_or_not_implemented.

## Security And Privacy Boundary

The first LAN runtime must be local-lab oriented, not public-network oriented.

Until a dedicated auth phase exists:

- Do not expose public network service.
- Do not store tokens.
- Do not implement user accounts.
- Do not map audit users over LAN.
- Do not expose raw store files.
- Do not expose backup files.

## UI State Contract

UIShell should eventually display LAN as a distinct data source state:

```text
local
readonly
future_lan_disabled
lan_readonly_connected
lan_disconnected
lan_blocked
```

In LAN read-only mode:

- counts may be shown.
- reagent/sample/cell/record summaries may be shown.
- write buttons must be disabled.
- UI must clearly say LAN read-only and no sync/write is active.

## Manual Checkpoint Before LAN-LT4

Stop after this document and obtain human approval for:

- Single host authority.
- Read-only-first LAN MVP.
- Health/status endpoints.
- Read-only summary endpoint list.
- No write endpoints in the first runtime phase.
- No auth/token in the first runtime phase.
- No multi-user permission model in the first runtime phase.
- No automatic conflict merge.
- No automatic inventory or sample-volume deduction.

## Manual Checkpoint Before LAN Writes

Before any LAN write endpoint is implemented, require a separate approved design
for:

- Admin/editor/viewer role model.
- User identity in audit logs.
- Expected-version conflict UI.
- Retry policy.
- Server backup/restore behavior.
- Write endpoint allowlist.
- Reagent/sample/record-specific write boundaries.

## Acceptance Criteria For This Spec

- This file exists.
- No runtime server code is added.
- No client network code is added.
- No auth/token code is added.
- No port listener is added.
- No UI behavior is changed.
- Existing future LAN/cloud placeholders remain disabled.
