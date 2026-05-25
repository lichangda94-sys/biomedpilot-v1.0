# LabTools LAN Pairing/Auth/Token Design

Date: 2026-05-25

## Purpose

LAN-LT8 is a design gate for pairing, authentication, and token handling. It
does not implement pairing endpoints, token storage, authorization headers,
user accounts, LAN writes, sync, or automatic discovery.

This design protects the existing explicit private LAN read-only prototype
before it becomes a normal multi-device feature.

## Current Baseline

Implemented before this design gate:

- Manual read-only server startup.
- Explicit private LAN bind with `--allow-lan-bind`.
- Read-only summary endpoints.
- Manual client URL entry.
- No writes.
- No sync.
- No automatic discovery.
- No pairing/auth/token runtime.

## Design Goals

- Pair a client device to a single authoritative LabTools host.
- Keep the first authenticated LAN mode read-only.
- Prevent raw store file access.
- Keep UI access through runtime/adapter wrappers.
- Make auth failures graceful and diagnosable.
- Preserve audit identity requirements before any future LAN write.
- Keep token handling revocable and scoped.

## Non-Goals

- No LAN write endpoints in this phase.
- No cloud account or cloud relay.
- No automatic discovery.
- No multi-user editing.
- No automatic conflict merge.
- No automatic reagent inventory or sample-volume deduction.
- No PDF/DOCX/report generation over LAN.

## Pairing Model

The host is the authority. A client must be paired before reading authenticated
summaries.

Recommended pairing flow:

1. Host user opens "Enable pairing" in a future LabTools LAN settings panel.
2. Host creates a short-lived pairing session.
3. Host displays:
   - server URL.
   - pairing code.
   - expiry time.
   - read-only capability notice.
4. Client user manually enters server URL and pairing code.
5. Server verifies the pairing code.
6. Server returns a client token once.
7. Client stores the token in local secure storage.
8. Later requests send the token with the request.

Pairing sessions should expire quickly, for example after 5-10 minutes. A
pairing session should be single-use unless a future UX explicitly allows
multiple devices from one session.

## Token Model

Token requirements:

- Token must be opaque and high entropy.
- Token must not encode user or permission data directly.
- Server stores only a token hash.
- Client stores only the opaque token.
- Token is scoped to one host and one client label.
- Token can be revoked by the host.
- Token has an expiry time.

Recommended token fields on the host:

```text
token_id
token_hash
client_label
role
created_at
expires_at
last_seen_at
revoked_at
created_by
notes
```

Initial authenticated role:

```text
viewer
```

Do not add `editor` or `admin` write behavior until a later LAN write design
gate approves endpoint-specific permissions and audit identity mapping.

## Token Storage

Server storage:

- Store token metadata outside raw LabTools data records.
- Do not expose token files through LAN endpoints.
- Store token hashes, not plaintext tokens.
- Treat token storage corruption as an auth-blocking state.

Client storage:

- Prefer OS secure storage when available.
- Do not store tokens in shared project exports.
- Do not include tokens in local record summaries, audit summaries, screenshots,
  or diagnostic reports.

## Future Request Auth

Recommended future request header:

```text
Authorization: Bearer <opaque-token>
```

Requests without a valid token should be blocked once authenticated LAN mode is
enabled.

Unauthenticated endpoints after auth exists:

- `GET /health` may remain unauthenticated and minimal.
- `GET /status` may return only server liveness and auth-required state.
- Read summary endpoints should require auth by default.

## Auth Response Envelope

Auth failures must use the existing LAN response envelope.

Required future auth states:

| State | Meaning |
| --- | --- |
| `auth_required` | Endpoint requires a token and none was provided. |
| `auth_invalid` | Token is malformed or unknown. |
| `auth_expired` | Token exists but is expired. |
| `auth_revoked` | Token was revoked by the host. |
| `pairing_required` | Client has not paired with this host. |
| `pairing_expired` | Pairing code/session expired. |
| `permission_denied` | Token is valid but lacks the required role. |
| `auth_store_unavailable` | Token metadata cannot be read safely. |

Example blocked response:

```json
{
  "ok": false,
  "status": "auth_required",
  "reason": "LAN read summaries require a paired client token.",
  "data_source_mode": "future_lan",
  "server_time": "2026-05-25T00:00:00+00:00",
  "schema_version": "labtools_lan_api.v1",
  "data": null
}
```

## Audit Identity Mapping

Read-only LAN requests should not write LabTools local_data audit entries.

Future LAN writes require a separate write gate and must map an authenticated
client token to an audit identity before any mutation is accepted.

Minimum future audit identity fields:

```text
auth_subject_id
client_label
role
paired_at
request_source
```

Accepted write audit entries must include the resolved identity. Unknown,
expired, revoked, or unpaired clients must not write audit entries as accepted
mutations.

## UIShell Pairing UX

Future host-side UI:

- Show LAN read-only server status.
- Show whether auth is required.
- Enable pairing for a short duration.
- Show pairing code and expiry.
- List paired devices.
- Revoke a device token.

Future client-side UI:

- Manual server URL entry.
- Pairing code entry.
- Pairing result state.
- Token expiry/revocation state.
- Read-only data source status.

The UI must continue to use runtime/adapter wrappers. UI pages must not import
server transport, token storage, local data store, or raw auth files directly.

## Migration Policy

Current LT7 behavior allows explicit unauthenticated private LAN read-only
summaries. When auth is implemented:

- New authenticated LAN mode should default to token-required.
- Existing unauthenticated read-only mode may remain only behind an explicit
  temporary compatibility setting.
- Compatibility mode must clearly show "unauthenticated read-only LAN".
- Compatibility mode must not enable writes.
- Compatibility mode should be removable after pairing UX is stable.

## Manual Checkpoint Before Runtime Auth

Stop before implementing runtime auth and confirm:

- Token expiry duration.
- Token storage location.
- Whether unauthenticated read-only compatibility remains available.
- Pairing code length and expiry.
- Device revocation UX.
- Whether `viewer` is the only role for the first auth runtime.

## Acceptance Criteria

- This design file exists.
- No token runtime is implemented.
- No `Authorization` header is required or sent.
- No token files are created.
- No pairing endpoint is exposed.
- No LAN write endpoint is exposed.
- Existing read-only LAN tests still pass.
