# LabTools LAN Protocol And Authority Spec

Date: 2026-05-25

## Purpose

This document defines the minimum LAN MVP protocol and authority boundary for
LabTools. The original LAN-LT3 section is a design gate. LAN-LT4 added the
first manual loopback health server prototype. LAN-LT5 adds loopback read-only
summary endpoints while keeping writes, auth, sync, and public-network binding
disabled. LAN-LT6 adds a manual read-only client contract and UIShell connection
surface without automatic discovery or sync.

This phase does not add LAN client network I/O, auth, token storage, sync jobs,
write endpoints, public-network binding, or UI behavior.

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

## LAN-LT4 Loopback Health Prototype

LAN-LT4 implements a manually started loopback-only health runtime:

```text
python3 -m labtools.lan_server --host 127.0.0.1 --port 0 --health-only
```

Available endpoints:

```text
GET /health
GET /status
```

Runtime constraints:

- Binds only to `127.0.0.1` or `localhost`, normalized to `127.0.0.1`.
- Does not bind a port until `start()` or the CLI is invoked.
- Does not auto-start from package import, smoke test, adapter construction, or
  UI runtime.
- Does not expose reagent, sample, cell, freeze vial, record, report, image,
  PDF, DOCX, filesystem, or raw store endpoints.
- Does not import or mutate `LocalLabToolsDataStore`.
- Returns the stable `labtools_lan_api.v1` envelope for health/status and
  blocked endpoints.
- Blocks write methods with `blocked_write_disabled`.

Manual checkpoint before LAN-LT5:

- Confirm loopback health/status behavior is acceptable.
- Confirm no data read endpoints should be enabled yet.
- Confirm LAN client transport should remain disabled until a separate read-only
  endpoint phase.
- Confirm auth/token/multi-user/sync/write behavior remains out of scope.

## LAN-LT5 Loopback Read-Only Summary Prototype

LAN-LT5 implements manually started loopback-only summary endpoints:

```text
python3 -m labtools.lan_server --host 127.0.0.1 --port 0 --read-only-summaries
```

Available endpoints:

```text
GET /health
GET /status
GET /records/summary
GET /reagents
GET /samples
GET /cells
GET /freeze-vials
GET /record-index
GET /record-index?record_type=wb_loading
```

Runtime constraints:

- Uses `ReadOnlyLabToolsDataSourceAdapter`.
- Does not initialize a missing store automatically.
- Does not expose local paths in response envelopes.
- Does not expose raw JSON store files, backups, exports, binary artifacts,
  images, PDF, or DOCX files.
- Does not create audit entries for reads.
- Does not deduct reagent amount or sample volume.
- Does not change sample, cell, freeze vial, reagent, or record status.
- Blocks write methods with `blocked_write_disabled`.
- Maps missing/corrupted/read-disabled store states to graceful blocked
  envelopes.

Manual checkpoint before LAN-LT6:

- Confirm loopback read-only summaries are sufficient for the first product
  validation.
- Confirm whether UIShell should add a manual LAN connection/status panel next.
- Confirm no public-network binding should be enabled yet.
- Confirm auth/token/multi-user/sync/write behavior remains out of scope.

## LAN-LT6 Manual Connection And Client Read Contract

LAN-LT6 implements a manually configured read-only client adapter:

```text
LabToolsLanReadonlyClientDataSourceAdapter
```

Client constraints:

- Accepts only explicit loopback HTTP server URLs.
- Does not perform automatic server discovery.
- Does not connect unless called by runtime/UI code.
- Consumes the `labtools_lan_api.v1` envelope.
- Maps server unavailable, malformed JSON, unsupported schema, missing store,
  corrupted store, and read-disabled states to graceful blocked statuses.
- Exposes read-only reagent, sample, cell, freeze vial, and record summaries.
- Blocks all write methods.

UIShell may show a manual LAN read-only status panel that calls runtime wrappers.
UIShell must not import LAN client transport or local data store code directly.

Manual checkpoint before LAN-LT7:

- Confirm whether a manual LAN data-source switch should feed Reagent/WB/Cell
  pages or remain status-only.
- Confirm whether public LAN binding can be designed, still without auth/sync.
- Confirm no automatic discovery, auth/token, multi-user permission, sync, or
  write behavior should be enabled yet.

## Acceptance Criteria For LAN-LT3 Spec Gate

- This file exists.
- No runtime server code is added.
- No client network code is added.
- No auth/token code is added.
- No port listener is added.
- No UI behavior is changed.
- Existing future LAN/cloud placeholders remain disabled.
