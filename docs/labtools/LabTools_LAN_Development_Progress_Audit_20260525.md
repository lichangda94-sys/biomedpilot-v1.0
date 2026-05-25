# LabTools LAN Development Progress Audit

Date: 2026-05-25

## Executive Summary

LabTools LAN development has moved from the pairing/auth/token design gate into
an LT9 read-only auth runtime prototype.

Usable cross-device LAN product capability is now an authenticated read-only
prototype: a manually started host can bind to loopback or an explicitly
allowed private LAN address, issue a short-lived pairing code, and require a
viewer bearer token for summary reads. There is still no sync protocol, LAN
write endpoint, automatic discovery, multi-user permission model, or conflict
merge behavior.

LAN architecture readiness is approximately 75-85%. The local-first data
contract, adapter boundary, disabled future adapters, server skeleton contract,
client adapter skeleton, protocol authority spec, loopback health server,
read-only summary endpoints, explicit private LAN bind, and read-only client
contract are in place. Pairing/auth/token requirements are documented and the
first runtime token gate is implemented. These are important prerequisites, but
sync and LAN writes are still not implemented.

## Current Commits Reviewed

- `487d369 docs(labtools): define future LAN cloud adapter boundary`
- `7131cd6 feat(labtools): add LAN server skeleton contract`
- `9b34485 feat(labtools): add LAN client adapter skeleton`
- `d137569 docs(labtools): define LAN protocol authority spec`
- `c4f9f03 feat(labtools): add loopback LAN health server`

The audit also relies on the local-first data store line through:

- `9b77128 feat(labtools): add local-first data store`
- `41a5e9a feat(labtools): support local reagent write operations`
- `b373ab0 feat(labtools): support local sample write operations`
- `818cbee feat(labtools): support local record index operations`

## Completion Matrix

| Area | Status | Completion | Notes |
| --- | --- | ---: | --- |
| Local-first route decision | Complete | 100% | LAN is explicitly delayed behind local-first. |
| Future LAN/cloud boundary doc | Complete | 100% | Current non-goals and future adapter rules are documented. |
| Future adapter disabled placeholders | Complete | 100% | `future_lan` and `future_cloud` report disabled status. |
| Local data contract reuse | Mostly complete | 80% | Reagent, sample, cell, freeze vial, record index, audit, version, and source mode are available for future adapters. |
| Server skeleton contract | Complete for skeleton | 100% | `labtools.lan_server` is importable and returns disabled non-listening status. |
| Client adapter skeleton contract | Complete for skeleton | 100% | `labtools.lan_client` is importable and blocks reads/writes as disabled. |
| Loopback health server runtime | Prototype complete | 100% | Manual `127.0.0.1` health/status server; no data endpoints. |
| Loopback read-only summary runtime | Prototype complete | 100% | Manual `127.0.0.1` summary endpoints through read-only adapter; no writes. |
| Explicit private LAN read-only bind | Prototype complete | 100% | `--allow-lan-bind` permits `0.0.0.0` or private/link-local IP read-only bind. |
| Manual read-only client contract | Prototype complete | 100% | Explicit loopback URL client; graceful unavailable/malformed handling; no writes. |
| UIShell manual LAN status panel | Prototype complete | 100% | Manual URL entry and read-only counts; no data-source switch yet. |
| Pairing/auth/token design | Complete for design gate | 100% | Pairing flow, token lifecycle, auth envelope, audit identity, and migration policy documented. |
| Pairing/auth/token runtime | Prototype complete | 100% | Read-only bearer token auth, 8-digit single-use pairing, 30-day token expiry, hash-only token store, host-local client list/revoke. |
| Cross-device LAN data server runtime | Prototype complete | 40% | Explicit private LAN read-only bind exists; no writes, sync, discovery, or user accounts. |
| Real LAN client network I/O | Prototype complete | 40% | Manual URL read-only HTTP client exists; no discovery, sync, or write flow. |
| Sync protocol | Not started | 0% | No pull/push/delta/full snapshot protocol exists. |
| Server storage authority | Not started | 0% | No decision whether server owns JSON, SQLite, or another store. |
| Authentication and permissions | Prototype complete | 30% | Viewer token auth exists for read-only summaries; no editor/admin/user identity mapping. |
| Conflict handling | Not started | 0% | Existing local expected-version blocking exists, but no multi-client policy. |
| UI LAN settings/status | Not started | 0% | UIShell has no LAN connection or status setup UI. |
| Network failure tests | Not started | 0% | Current tests intentionally verify no network code is active. |

## What Is Implemented

### Boundary

`docs/labtools/LabTools_Future_LAN_Cloud_Adapter_Boundary.md` defines that the
current product has no LAN server, no cloud sync, no multi-user permissions, no
automatic conflict merging, no public network service, no token/auth flow, and
no port listener.

It also defines the future rule: LAN/cloud must enter through
`LabToolsDataSourceAdapter`, reuse local data contracts, preserve expected
version checks, preserve audit log behavior, and keep UI away from direct server
or database access.

### Server Skeleton

`labtools.lan_server` exposes:

- `LabToolsLanServerConfig`
- `LabToolsLanServerStatus`
- `LabToolsLanServerSkeleton`
- `build_lan_server_skeleton()`

The skeleton returns disabled status:

```text
status = disabled_skeleton
data_source_mode = future_lan
enabled = false
network_enabled = false
listening = false
```

`start()` and `stop()` do not bind a port or start a service.

### Client Adapter Skeleton

`labtools.lan_client` exposes:

- `LabToolsLanClientConfig`
- `LabToolsLanClientStatus`
- `LabToolsLanClientDataSourceAdapter`
- `build_lan_client_adapter_skeleton()`

The adapter reports `future_lan` disabled status, returns empty read results,
and blocks write methods with a disabled reason. It does not perform network
I/O.

### Manual Read-Only Client Contract

`labtools.lan_client` exposes:

- `LabToolsLanReadonlyClientConfig`
- `LabToolsLanReadonlyClientDataSourceAdapter`
- `LabToolsLanReadonlyReadModel`
- `build_lan_readonly_client_adapter()`

The client accepts explicit loopback/private/link-local/`.local` HTTP URLs,
consumes the stable LAN envelope, returns graceful blocked statuses for server
unavailable and malformed responses, and blocks all writes.

### Pairing/Auth/Token Runtime

`docs/labtools/LabTools_LAN_Pairing_Auth_Token_Design.md` defines:

- pairing flow.
- token lifecycle and storage boundaries.
- future auth request header shape.
- auth failure envelope states.
- audit identity mapping.
- UIShell pairing UX.
- migration policy from unauthenticated read-only LAN.

LT9 adds:

- `LabToolsLanAuthManager`
- in-memory single-use pairing sessions.
- 8-digit pairing codes with 10-minute expiry.
- 30-day viewer tokens.
- host-side `lan_auth/paired_clients.json` token metadata.
- `token_hash` storage instead of plaintext tokens.
- `POST /pairing/claim`.
- `Authorization: Bearer <opaque-token>` handling for read-only endpoints.
- host-local paired client listing and revocation by token id.
- explicit unauthenticated read-only compatibility mode.

### Loopback Health And Read-Only Runtime

`labtools.lan_server` also exposes:

- `LabToolsLanHealthServerConfig`
- `LabToolsLanHealthServerRuntimeStatus`
- `LabToolsLanHealthServer`
- `build_lan_health_server()`

The health-only runtime is manually started only:

```text
python3 -m labtools.lan_server --host 127.0.0.1 --port 0 --health-only
```

The read-only summary runtime is manually started only:

```text
python3 -m labtools.lan_server --host 127.0.0.1 --port 0 --read-only-summaries
```

Private LAN bind is explicit:

```text
python3 -m labtools.lan_server --host 0.0.0.0 --port 8787 --read-only-summaries --allow-lan-bind
```

It supports:

- `GET /health`
- `GET /status`
- `GET /records/summary`
- `GET /reagents`
- `GET /samples`
- `GET /cells`
- `GET /freeze-vials`
- `GET /record-index`

It rejects non-loopback bind hosts, does not bind during object construction,
does not auto-start from imports, uses `ReadOnlyLabToolsDataSourceAdapter` for
summary reads, blocks write methods, and does not expose local paths.

### Tests

Current tests verify:

- Server skeleton does not listen.
- Server skeleton start/stop do not enable network.
- Client skeleton does not connect.
- Client skeleton read methods return empty results.
- Client skeleton write methods block.
- Loopback health runtime rejects public bind hosts.
- Loopback health runtime serves `/health` and `/status`.
- Loopback health runtime blocks data endpoints and write methods.
- Loopback health runtime does not create local data files.
- Loopback read-only runtime blocks missing/corrupted stores gracefully.
- Loopback read-only runtime lists reagent/sample/cell/freeze vial/record
  summaries.
- Loopback read-only runtime filters record index by `record_type`.
- Loopback read-only runtime does not write audit entries or deduct sample
  volume.
- Loopback read-only runtime does not expose local filesystem paths.
- Explicit private LAN bind requires `--allow-lan-bind`.
- Public IP bind remains blocked.
- Manual read-only client reads loopback summaries.
- Manual read-only client accepts private LAN URLs and rejects public IP URLs.
- Manual read-only client blocks server unavailable and malformed responses
  gracefully.
- Manual read-only client blocks writes.
- UIShell manual LAN panel displays read-only counts through runtime wrappers.
- Pairing/auth/token design gate exists.
- Runtime/client code implements read-only pairing, token storage, and
  `Authorization` headers.
- Pairing codes are single-use.
- Token revocation and unknown-token states block gracefully.
- Paired client listing does not expose plaintext tokens or token hashes.
- Remote paired-device management endpoints remain disabled.
- Authenticated reads do not write audit entries or deduct sample volume.
- Skeleton source does not include network client/server imports or listener
  calls.
- Package smoke includes `labtools.lan_server` and `labtools.lan_client`.

## What Is Not Implemented

The following are not implemented and should not be described as available:

- Device discovery.
- Workspace pairing runtime in UIShell.
- Editor/admin user roles.
- Remote paired-device management endpoints.
- Full UI paired-device management.
- Remote database.
- Remote JSON or SQLite sharing.
- Sync scheduling.
- Push/pull conflict handling.
- Automatic conflict merge.
- LAN UI setup page.
- LAN status page.
- Network failure handling.
- Multi-device test matrix.

## Completion Assessment

### Product Capability

Current cross-device LAN product capability: 0%.

Reason: LabTools summaries can be read through a manually configured,
authenticated read-only LAN path, but there is no sync, write, discovery, or
multi-user workflow.

### Engineering Foundation

Current LAN engineering foundation: approximately 80-90%.

Reason: local-first data contracts, adapter boundaries, disabled future modes,
server skeleton, client adapter skeleton, protocol authority spec, loopback
health runtime, read-only summary endpoints, explicit private LAN bind, manual
read-only client contract, pairing/auth/token design, pairing runtime, token
gate, and boundary tests are in place. These reduce future design risk but do
not implement sync or writes.

### Recommended Overall Label

Use this label in status reports:

```text
LAN: pairing-auth-readonly-prototype / sync-write-disabled
```

Avoid labels such as:

```text
cross-device LAN data ready
LAN sync available
multi-user ready
cross-device server available
```

## Key Risks Before Real LAN Work

1. Server storage authority is undecided.

   A future task must decide whether the LAN server wraps the existing JSON
   store, migrates to SQLite, or owns a separate server-side persistence layer.

2. Multi-client version semantics are undefined.

   Local expected-version blocking exists, but LAN needs a policy for stale
   remote clients, offline edits, retries, and conflict presentation.

3. Auth and audit identity are missing.

   Current audit uses local-user semantics. LAN needs user identity mapping
   before multi-user writes can be trusted.

4. UI behavior is not designed.

   There is no connection setup, connection health, read-only fallback, sync
   queue, or conflict display UI.

5. Packaging impact is unknown.

   A listening server or background process will affect desktop packaging,
   firewall prompts, LaunchServices validation, and support expectations.

## Recommended Next Steps

### Next Safe Development Task

Stop for manual checkpoint, then implement:

```text
LAN-LT10 UIShell pairing credential UX prototype
```

Expected output:

- Add UIShell runtime wrappers for claiming a pairing code.
- Store client token in a local settings credential file, with OS keychain
  deferred.
- Feed stored bearer token into the manual read-only LAN client.
- Show clear read-only/auth/expiry status.
- Keep unauthenticated read-only as an explicit compatibility state only.
- Surface host-local paired client list/revoke in a local-only UI without
  exposing remote admin endpoints.
- No write endpoints.
- No sync.
- No automatic inventory/sample deduction.
- No UI direct store access.

## Current Recommendation

Do not implement LAN sync yet.

The current codebase is ready for a manual checkpoint before UIShell pairing
credential UX and paired-device management. It is not ready for multi-user
sync, automatic conflict handling, networked writes, or automatic discovery.
