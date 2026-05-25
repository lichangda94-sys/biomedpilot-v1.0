from __future__ import annotations

import argparse
import time

from labtools.lan_server.runtime import LabToolsLanHealthServerConfig, build_lan_health_server


def main() -> int:
    parser = argparse.ArgumentParser(description="LabTools loopback LAN server prototype.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Non-loopback private LAN hosts require --allow-lan-bind.")
    parser.add_argument("--port", default=0, type=int, help="Loopback port. Use 0 to allocate an ephemeral port.")
    parser.add_argument("--local-data-root", default=None, help="Optional LabTools local_data root for read-only summary mode.")
    parser.add_argument("--allow-lan-bind", action="store_true", help="Allow binding read-only summaries to 0.0.0.0 or a private LAN address.")
    parser.add_argument("--allow-unauthenticated-readonly", action="store_true", help="Compatibility mode: allow read-only summaries without pairing/token auth.")
    parser.add_argument("--pairing-on-start", action="store_true", help="Create and print a single-use viewer pairing code on startup when auth is required.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--health-only", action="store_true", help="Run health/status only; data endpoints remain disabled.")
    mode.add_argument("--read-only-summaries", action="store_true", help="Run loopback read-only summary endpoints.")
    args = parser.parse_args()

    server = build_lan_health_server(
        LabToolsLanHealthServerConfig(
            host=args.host,
            port=args.port,
            health_only=args.health_only,
            local_data_root=args.local_data_root,
            allow_lan_bind=args.allow_lan_bind,
            auth_required=(not args.health_only and not args.allow_unauthenticated_readonly),
            allow_unauthenticated_readonly=args.allow_unauthenticated_readonly,
        )
    )
    status = server.start()
    print(f"LabTools LAN loopback server listening on http://{status.host}:{status.port}", flush=True)
    if args.health_only:
        print("Available endpoints: GET /health, GET /status", flush=True)
        print("Data endpoints, writes, auth, sync, and public-network binding are disabled.", flush=True)
    else:
        print(
            "Available endpoints: GET /health, GET /status, GET /records/summary, "
            "GET /reagents, GET /samples, GET /cells, GET /freeze-vials, GET /record-index",
            flush=True,
        )
        if args.allow_unauthenticated_readonly:
            print("Unauthenticated read-only compatibility is enabled; writes, sync, and automatic discovery are disabled.", flush=True)
        else:
            print("Read-only summaries require paired viewer token auth; writes, sync, and automatic discovery are disabled.", flush=True)
        if args.allow_lan_bind:
            print("LAN bind is explicitly enabled for read-only summaries.", flush=True)
        if status.auth_enabled and args.pairing_on_start:
            pairing = server.create_pairing_session(client_label="manual-client")
            print(f"Pairing code: {pairing.pairing_code}", flush=True)
            print(f"Pairing expires at: {pairing.expires_at}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop()
        print("LabTools LAN health server stopped.", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
