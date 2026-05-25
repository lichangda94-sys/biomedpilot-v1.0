# LabTools LAN Development Progress Audit

Date: 2026-05-25

## Executive Summary

LabTools LAN development is currently in a manual loopback read-only connection
prototype stage.

Usable cross-device LAN product capability is still effectively 0%: there is no
LAN client network connection, no public-network binding, no sync protocol, no
authentication, no multi-user permission model, and no conflict merge behavior.
The runtime service is manually started on loopback and can expose read-only
summary endpoints for local validation. A manual read-only client contract now
exists, but it is still loopback-only and does not create cross-device sharing.

LAN architecture readiness is approximately 65-75%. The local-first data
contract, adapter boundary, disabled future adapters, server skeleton contract,
client adapter skeleton, protocol authority spec, loopback health server, and
loopback read-only summary endpoints are in place. The read-only client contract
can consume those summaries manually. These are important prerequisites, but
they do not yet move LabTools data across machines.

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
| Manual read-only client contract | Prototype complete | 100% | Explicit loopback URL client; graceful unavailable/malformed handling; no writes. |
| UIShell manual LAN status panel | Prototype complete | 100% | Manual URL entry and read-only counts; no data-source switch yet. |
| Cross-device LAN data server runtime | Not started | 0% | No public bind, client connection flow, auth, or cross-device listener exists. |
| Real LAN client network I/O | Not started | 0% | No requests, device discovery, or connection flow exists. |
| Sync protocol | Not started | 0% | No pull/push/delta/full snapshot protocol exists. |
| Server storage authority | Not started | 0% | No decision whether server owns JSON, SQLite, or another store. |
| Authentication and permissions | Not started | 0% | No admin/editor/viewer model, token, user identity, or audit user mapping. |
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

The client accepts only explicit loopback HTTP URLs, consumes the stable LAN
envelope, returns graceful blocked statuses for server unavailable and malformed
responses, and blocks all writes.

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
- Manual read-only client reads loopback summaries.
- Manual read-only client blocks server unavailable and malformed responses
  gracefully.
- Manual read-only client blocks writes.
- UIShell manual LAN panel displays read-only counts through runtime wrappers.
- Skeleton source does not include network client/server imports or listener
  calls.
- Package smoke includes `labtools.lan_server` and `labtools.lan_client`.

## What Is Not Implemented

The following are not implemented and should not be described as available:

- Cross-device LAN server process.
- LAN client network transport.
- Device discovery.
- Workspace pairing.
- Authentication.
- User roles.
- Token storage.
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

Reason: no LabTools data can be shared across devices and no client can connect
to a server for summaries. The local-only loopback summary server is a runtime
validation step, not a data-sharing capability.

### Engineering Foundation

Current LAN engineering foundation: approximately 65-75%.

Reason: local-first data contracts, adapter boundaries, disabled future modes,
server skeleton, client adapter skeleton, protocol authority spec, loopback
health runtime, loopback read-only summary endpoints, manual read-only client
contract, and boundary tests are in place. These reduce future design risk but
do not implement LAN data sharing.

### Recommended Overall Label

Use this label in status reports:

```text
LAN: manual-loopback-readonly-ready / data-sharing-disabled
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
LAN-LT7 manual LAN data-source switch or public-bind design gate
```

Expected output:

- Decide whether LAN summaries can feed Reagent/WB/Cell pages, or remain
  status-only.
- If public bind is considered, design firewall, auth/token, pairing, and
  privacy boundaries before implementation.
- Preserve manual connection until automatic discovery has a separate approved
  design.
- No write endpoints.
- No auth/token.
- No sync.
- No automatic inventory/sample deduction.
- No UI direct store access.

## Current Recommendation

Do not implement LAN sync yet.

The current codebase is ready for a manual checkpoint on the manual loopback
read-only connection prototype. It is not ready for multi-user sync, automatic
conflict handling, networked writes, automatic discovery, or public-network
exposure.
