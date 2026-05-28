# LabTools Real LAN Interop Audit

Date: 2026-05-26

## Scope

This audit checks whether the current LabTools LAN line is ready for real
private-LAN device interop testing. It does not enable packaging, automatic
discovery, LAN writes, sync, cloud relay, or multi-user editing.

Repositories audited:

- LabTools: `ba841f1 feat(labtools): add host LAN paired client management`
- UIShell: `b49647a feat(labtools): improve LAN client token connection UX`

## Current Capability

Implemented:

- Manual read-only LAN server.
- Explicit private LAN bind with `--allow-lan-bind`.
- Auth-required read-only mode by default.
- Explicit unauthenticated read-only compatibility mode.
- Eight-digit pairing code.
- Ten-minute single-use pairing session.
- Thirty-day viewer token.
- Server token metadata at `local_data_root/lan_auth/paired_clients.json`.
- Server stores only token hash, not plaintext token.
- Client sends `Authorization: Bearer <opaque-token>`.
- Host-local paired client list and revoke.
- UIShell host panel for start/stop, mode, pairing code, paired clients, revoke.
- UIShell client panel for saved token status, role, expiry, clear token,
  auth-failed re-pairing prompt, and compatibility warning.

Still disabled:

- LAN writes.
- Sync.
- Automatic discovery.
- Cloud relay.
- Editor/admin roles.
- Remote paired-device management endpoints.
- Automatic conflict merge.
- Automatic inventory or sample-volume deduction.
- PDF/DOCX/report generation over LAN.

## Local Private-LAN Bind Probe

The audit ran a host/client probe on the machine's private LAN address:

```text
lan_ip=192.168.1.72
server_url=http://192.168.1.72:54508
```

Probe path:

1. Initialize a temporary LabTools local data store.
2. Bind read-only LAN host to `192.168.1.72` with `allow_lan_bind=True`.
3. Require token auth.
4. Confirm unauthenticated client read is blocked.
5. Create pairing session on host.
6. Claim pairing through LAN client.
7. Read summaries through bearer token.
8. Revoke paired client.
9. Confirm revoked client read is blocked.
10. Confirm read path does not write audit entries or deduct sample volume.

Observed result:

```text
unauth_status=blocked_read_disabled read_enabled=False
claim_status=paired role=viewer token_len=43
authed_status=ready_readonly read_enabled=True sample_count=1
revoked_status=blocked_read_disabled read_enabled=False
audit_delta=0
sample_volume_before_after=25 25
```

Interpretation:

- The current code path can bind to an actual private LAN interface, not only
  loopback.
- Token-required read-only access works through the LAN client adapter.
- Revoke blocks later reads gracefully.
- Read-only access does not mutate local_data.

Limitation:

- This probe is same-machine private-IP testing. It does not prove that a
  second physical device can reach the host through local firewall/router
  policy.

## Automated Test Evidence

Current targeted verification:

```text
UIShell LAN/UI targeted: 19 passed
LabTools LAN auth/runtime/client/design: 26 passed
LabTools smoke: passed
```

Coverage confirmed:

- UI does not directly import LAN server/client/auth/store modules.
- Revoke after pairing causes client reads to block gracefully.
- Compatibility mode remains explicit and is not the default.
- LAN writes, sync, and discovery remain disabled.
- Private LAN bind requires explicit `allow_lan_bind`.
- Public IP bind remains blocked.
- LAN client accepts loopback/private/link-local URLs and rejects public IP
  URLs.

## Real Two-Device Checklist

Manual two-device interop remains the next required checkpoint.

Host device:

1. Confirm host and client are on the same private LAN.
2. Confirm host IP, for example `192.168.x.x`.
3. Start LabTools LAN host in auth-required read-only mode.
4. Confirm host panel shows:
   - server mode: `auth required`.
   - server URL using private LAN IP.
   - write disabled.
   - sync disabled.
   - discovery disabled.
5. Create a pairing code.
6. Confirm paired client appears after client pairing.
7. Revoke the paired client after successful read.

Client device:

1. Enter host URL manually.
2. Confirm unauthenticated read is blocked before pairing.
3. Enter pairing code.
4. Confirm saved token status shows:
   - role: `viewer`.
   - expiry timestamp.
5. Read reagent/sample/cell/freeze vial/record summaries.
6. Confirm WB sample concentration is visible if sample data exists.
7. After host revokes token, reconnect and confirm graceful auth failure with
   re-pairing prompt.
8. Clear saved token locally.

Network/environment checks:

- macOS firewall prompt/setting.
- Router client isolation/AP isolation.
- VPN state.
- Multiple active network interfaces.
- Private IP changes after sleep/reconnect.
- Port reachability from client to host.

## Risk Assessment

Current real LAN readiness: read-only interop candidate.

Remaining risks before calling it product-ready:

- No verified two-device run yet.
- No firewall prompt handling guide.
- No packaged app entitlement/firewall audit.
- No automatic discovery, so users must know the host URL.
- Token store is local JSON rather than OS keychain or encrypted store.
- Client token store is a local settings credential file, not OS keychain.
- No remote admin endpoint, so revoke/list remains host-local UI only.
- No persistent background service lifecycle; host must be manually started.

## Recommendation

Proceed to a manual two-device LAN checkpoint before implementing automatic
discovery.

Do not implement LAN sync or LAN writes yet. The next engineering task should
be:

```text
LT11 Real LAN two-device manual interop checkpoint
```

Stop criteria for LT11:

- Host and client on separate devices complete auth-required pairing/read.
- Revoke blocks client read gracefully.
- Compatibility mode is tested explicitly and marked risky.
- LAN writes remain blocked.
- Sync/discovery remain disabled.
- Firewall/router blockers are recorded with screenshots or logs.
