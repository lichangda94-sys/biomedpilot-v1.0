from __future__ import annotations

import argparse
import time

from labtools.lan_server.runtime import LabToolsLanHealthServerConfig, build_lan_health_server


def main() -> int:
    parser = argparse.ArgumentParser(description="LabTools loopback LAN health server prototype.")
    parser.add_argument("--host", default="127.0.0.1", help="Loopback host. Only 127.0.0.1/localhost are accepted.")
    parser.add_argument("--port", default=0, type=int, help="Loopback port. Use 0 to allocate an ephemeral port.")
    parser.add_argument("--health-only", action="store_true", help="Required guard for the prototype health/status-only runtime.")
    args = parser.parse_args()

    if not args.health_only:
        parser.error("--health-only is required; data endpoints are not enabled in this phase.")

    server = build_lan_health_server(LabToolsLanHealthServerConfig(host=args.host, port=args.port, health_only=True))
    status = server.start()
    print(f"LabTools LAN health server listening on http://{status.host}:{status.port}", flush=True)
    print("Available endpoints: GET /health, GET /status", flush=True)
    print("Data endpoints, writes, auth, sync, and public-network binding are disabled.", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop()
        print("LabTools LAN health server stopped.", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
