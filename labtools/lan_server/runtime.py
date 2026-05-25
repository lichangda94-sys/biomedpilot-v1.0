from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


LAN_API_SCHEMA_VERSION = "labtools_lan_api.v1"
LOOPBACK_HEALTH_RUNTIME_MODE = "loopback_health_only"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost"})


@dataclass(frozen=True)
class LabToolsLanHealthServerConfig:
    host: str = "127.0.0.1"
    port: int = 0
    data_source_mode: str = "future_lan"
    health_only: bool = True

    def normalized(self) -> "LabToolsLanHealthServerConfig":
        host = str(self.host or "127.0.0.1").strip()
        if host == "localhost":
            host = "127.0.0.1"
        port = int(self.port)
        if host not in LOOPBACK_HOSTS:
            raise ValueError("LAN health server prototype only allows loopback hosts.")
        if port < 0 or port > 65535:
            raise ValueError("LAN health server port must be between 0 and 65535.")
        return LabToolsLanHealthServerConfig(host=host, port=port, data_source_mode="future_lan", health_only=True)


@dataclass(frozen=True)
class LabToolsLanHealthServerRuntimeStatus:
    status: str
    lan_runtime_mode: str
    data_source_mode: str
    enabled: bool
    network_enabled: bool
    host: str
    port: int
    listening: bool
    data_access_enabled: bool
    sync_enabled: bool
    auth_enabled: bool
    reason: str = ""


def lan_response_envelope(
    *,
    ok: bool,
    status: str,
    reason: str = "",
    data: Any = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "status": status,
        "reason": reason,
        "data_source_mode": "future_lan",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "schema_version": LAN_API_SCHEMA_VERSION,
        "data": data,
    }


class LabToolsLanHealthServer:
    def __init__(self, config: LabToolsLanHealthServerConfig | None = None) -> None:
        self.config = (config or LabToolsLanHealthServerConfig()).normalized()
        self._server: _LabToolsLanThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._last_host = self.config.host
        self._last_port = self.config.port

    @property
    def server_address(self) -> tuple[str, int]:
        if self._server is None:
            return self._last_host, self._last_port
        host, port = self._server.server_address[:2]
        self._last_host = str(host)
        self._last_port = int(port)
        return self._last_host, self._last_port

    def status(self) -> LabToolsLanHealthServerRuntimeStatus:
        host, port = self.server_address
        return LabToolsLanHealthServerRuntimeStatus(
            status="ready" if self.is_listening else "created",
            lan_runtime_mode=LOOPBACK_HEALTH_RUNTIME_MODE,
            data_source_mode="future_lan",
            enabled=self.is_listening,
            network_enabled=self.is_listening,
            host=host,
            port=port,
            listening=self.is_listening,
            data_access_enabled=False,
            sync_enabled=False,
            auth_enabled=False,
            reason="Loopback health/status only; LabTools data endpoints are disabled.",
        )

    @property
    def is_listening(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> LabToolsLanHealthServerRuntimeStatus:
        if self._thread is None:
            self._server = _LabToolsLanThreadingHTTPServer(
                (self.config.host, self.config.port),
                _build_handler(),
                runtime=self,
            )
            self.server_address
            self._thread = threading.Thread(target=self._server.serve_forever, name="labtools-lan-health", daemon=True)
            self._thread.start()
        return self.status()

    def stop(self) -> LabToolsLanHealthServerRuntimeStatus:
        if self._server is not None and self._thread is not None:
            self._server.shutdown()
            self._thread.join(timeout=5)
            self._thread = None
        if self._server is not None:
            self._server.server_close()
            self._server = None
        return self.status()

    def url(self, path: str) -> str:
        host, port = self.server_address
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"http://{host}:{port}{normalized_path}"

    def __enter__(self) -> "LabToolsLanHealthServer":
        self.start()
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.stop()


def build_lan_health_server(config: LabToolsLanHealthServerConfig | None = None) -> LabToolsLanHealthServer:
    return LabToolsLanHealthServer(config)


class _LabToolsLanThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], runtime: LabToolsLanHealthServer) -> None:
        self.runtime = runtime
        super().__init__(server_address, handler)


def _build_handler():
    class LabToolsLanHealthRequestHandler(BaseHTTPRequestHandler):
        server_version = "LabToolsLANHealth/0.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            path = urlparse(self.path).path
            if path == "/health":
                self._write_json(
                    200,
                    lan_response_envelope(
                        ok=True,
                        status="ready",
                        data=self._health_payload(),
                    ),
                )
                return
            if path == "/status":
                self._write_json(
                    200,
                    lan_response_envelope(
                        ok=True,
                        status="ready",
                        reason="Loopback health/status only; LabTools data endpoints are disabled.",
                        data=self._status_payload(),
                    ),
                )
                return
            self._write_json(
                404,
                lan_response_envelope(
                    ok=False,
                    status="disabled_or_not_implemented",
                    reason="Only /health and /status are available in loopback health prototype.",
                    data=None,
                ),
            )

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
            self._write_method_not_allowed()

        def do_PUT(self) -> None:  # noqa: N802 - stdlib handler API
            self._write_method_not_allowed()

        def do_PATCH(self) -> None:  # noqa: N802 - stdlib handler API
            self._write_method_not_allowed()

        def do_DELETE(self) -> None:  # noqa: N802 - stdlib handler API
            self._write_method_not_allowed()

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _write_method_not_allowed(self) -> None:
            self._write_json(
                405,
                lan_response_envelope(
                    ok=False,
                    status="blocked_write_disabled",
                    reason="LAN loopback health prototype does not accept writes.",
                    data=None,
                ),
            )

        def _write_json(self, status_code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _health_payload(self) -> dict[str, Any]:
            return {
                "lan_runtime_mode": LOOPBACK_HEALTH_RUNTIME_MODE,
                "data_access_enabled": False,
                "sync_enabled": False,
                "auth_enabled": False,
                "write_enabled": False,
            }

        def _status_payload(self) -> dict[str, Any]:
            server = self.server
            runtime = getattr(server, "runtime", None)
            runtime_status = asdict(runtime.status()) if runtime is not None else {}
            return {
                **self._health_payload(),
                "runtime": runtime_status,
            }

    return LabToolsLanHealthRequestHandler
