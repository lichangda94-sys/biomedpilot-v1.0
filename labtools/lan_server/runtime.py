from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from labtools.local_data.datasource_adapter import ReadOnlyLabToolsDataSourceAdapter
from labtools.local_data.models import (
    CellProfileRecord,
    FreezeVialRecord,
    LabToolsRecordIndexEntry,
    ReagentRecord,
    SampleRecord,
)


LAN_API_SCHEMA_VERSION = "labtools_lan_api.v1"
LOOPBACK_HEALTH_RUNTIME_MODE = "loopback_health_only"
LOOPBACK_READONLY_RUNTIME_MODE = "loopback_readonly_summary"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost"})
READONLY_ENDPOINTS = frozenset(
    {
        "/records/summary",
        "/reagents",
        "/samples",
        "/cells",
        "/freeze-vials",
        "/record-index",
    }
)


@dataclass(frozen=True)
class LabToolsLanHealthServerConfig:
    host: str = "127.0.0.1"
    port: int = 0
    data_source_mode: str = "future_lan"
    health_only: bool = True
    local_data_root: str | Path | None = None

    def normalized(self) -> "LabToolsLanHealthServerConfig":
        host = str(self.host or "127.0.0.1").strip()
        if host == "localhost":
            host = "127.0.0.1"
        port = int(self.port)
        if host not in LOOPBACK_HOSTS:
            raise ValueError("LAN health server prototype only allows loopback hosts.")
        if port < 0 or port > 65535:
            raise ValueError("LAN health server port must be between 0 and 65535.")
        return LabToolsLanHealthServerConfig(
            host=host,
            port=port,
            data_source_mode="future_lan",
            health_only=bool(self.health_only),
            local_data_root=self.local_data_root,
        )


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
        self.adapter = ReadOnlyLabToolsDataSourceAdapter(self.config.local_data_root)
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
            lan_runtime_mode=self.lan_runtime_mode,
            data_source_mode="future_lan",
            enabled=self.is_listening,
            network_enabled=self.is_listening,
            host=host,
            port=port,
            listening=self.is_listening,
            data_access_enabled=not self.config.health_only,
            sync_enabled=False,
            auth_enabled=False,
            reason=self._runtime_reason(),
        )

    @property
    def is_listening(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def lan_runtime_mode(self) -> str:
        return LOOPBACK_HEALTH_RUNTIME_MODE if self.config.health_only else LOOPBACK_READONLY_RUNTIME_MODE

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

    def _runtime_reason(self) -> str:
        if self.config.health_only:
            return "Loopback health/status only; LabTools data endpoints are disabled."
        return "Loopback read-only summaries; writes, sync, auth, and public-network access are disabled."

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
                        data=self._runtime_payload(),
                    ),
                )
                return
            if path == "/status":
                self._write_status()
                return
            if path in READONLY_ENDPOINTS and self._runtime().config.health_only:
                self._write_json(
                    404,
                    lan_response_envelope(
                        ok=False,
                        status="disabled_or_not_implemented",
                        reason="Read-only summary endpoints are disabled in health-only mode.",
                        data=None,
                    ),
                )
                return
            if path == "/records/summary":
                self._write_readonly_payload(lambda: self._records_summary_payload())
                return
            if path == "/reagents":
                self._write_readonly_payload(
                    lambda: [reagent_summary(item) for item in self._runtime().adapter.list_reagents()]
                )
                return
            if path == "/samples":
                self._write_readonly_payload(
                    lambda: [sample_summary(item) for item in self._runtime().adapter.list_samples()]
                )
                return
            if path == "/cells":
                self._write_readonly_payload(lambda: [cell_summary(item) for item in self._runtime().adapter.list_cells()])
                return
            if path == "/freeze-vials":
                self._write_readonly_payload(
                    lambda: [freeze_vial_summary(item) for item in self._runtime().adapter.list_freeze_vials()]
                )
                return
            if path == "/record-index":
                query = urlparse(self.path).query
                record_type = _record_type_from_query(query)
                self._write_readonly_payload(
                    lambda: [record_index_summary(item) for item in self._runtime().adapter.list_record_index(record_type)]
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

        def _write_status(self) -> None:
            runtime = self._runtime()
            data = {
                **self._runtime_payload(),
                "runtime": asdict(runtime.status()),
            }
            if not runtime.config.health_only:
                data["adapter_status"] = safe_adapter_status(runtime.adapter)
            self._write_json(
                200,
                lan_response_envelope(
                    ok=True,
                    status="ready",
                    reason=runtime._runtime_reason(),
                    data=data,
                ),
            )

        def _write_readonly_payload(self, payload_builder: Callable[[], Any]) -> None:
            adapter_status = safe_adapter_status(self._runtime().adapter)
            if not adapter_status["read_enabled"]:
                semantic_status = adapter_status_to_blocked_state(adapter_status["status"])
                self._write_json(
                    503,
                    lan_response_envelope(
                        ok=False,
                        status=semantic_status,
                        reason=str(adapter_status["reason"]),
                        data={
                            "adapter_status": adapter_status,
                        },
                    ),
                )
                return
            try:
                data = payload_builder()
            except Exception as exc:  # noqa: BLE001 - endpoint must block gracefully.
                self._write_json(
                    503,
                    lan_response_envelope(
                        ok=False,
                        status="blocked_invalid_store",
                        reason=sanitize_reason(str(exc)),
                        data={
                            "adapter_status": safe_adapter_status(self._runtime().adapter),
                        },
                    ),
                )
                return
            self._write_json(
                200,
                lan_response_envelope(
                    ok=True,
                    status="ready_readonly",
                    reason="Read-only summary endpoint; writes and sync are disabled.",
                    data=data,
                ),
            )

        def _records_summary_payload(self) -> dict[str, Any]:
            adapter = self._runtime().adapter
            reagents = adapter.list_reagents()
            samples = adapter.list_samples()
            cells = adapter.list_cells()
            freeze_vials = adapter.list_freeze_vials()
            records = adapter.list_record_index()
            return {
                "counts": {
                    "reagents": len(reagents),
                    "samples": len(samples),
                    "cells": len(cells),
                    "freeze_vials": len(freeze_vials),
                    "record_index": len(records),
                },
                "record_index": [record_index_summary(item) for item in records],
            }

        def _runtime_payload(self) -> dict[str, Any]:
            runtime = self._runtime()
            return {
                "lan_runtime_mode": runtime.lan_runtime_mode,
                "data_access_enabled": not runtime.config.health_only,
                "sync_enabled": False,
                "auth_enabled": False,
                "write_enabled": False,
            }

        def _runtime(self) -> LabToolsLanHealthServer:
            return self.server.runtime

    return LabToolsLanHealthRequestHandler


def _record_type_from_query(query: str) -> str | None:
    values = parse_qs(query).get("record_type")
    if not values:
        return None
    return values[0].strip() or None


def adapter_status_to_blocked_state(status: object) -> str:
    if status == "missing_store":
        return "blocked_store_missing"
    if status == "blocked_invalid_store":
        return "blocked_invalid_store"
    return "blocked_read_disabled"


def safe_adapter_status(adapter: ReadOnlyLabToolsDataSourceAdapter) -> dict[str, Any]:
    status = adapter.status()
    store_status = status.local_store_status
    store_state = store_status.status if store_status is not None else status.status
    return {
        "status": store_state,
        "data_source_mode": "future_lan",
        "adapter_mode": status.data_source_mode,
        "read_enabled": status.read_enabled,
        "write_enabled": False,
        "history_enabled": status.history_enabled,
        "export_enabled": False,
        "reason": sanitize_reason(store_status.message if store_status is not None else status.reason),
        "counts": {
            "reagents": store_status.reagent_count if store_status is not None else 0,
            "samples": store_status.sample_count if store_status is not None else 0,
            "cells": store_status.cell_count if store_status is not None else 0,
            "record_index": store_status.record_count if store_status is not None else 0,
        },
    }


def sanitize_reason(reason: str) -> str:
    if "LabTools local data file is not valid JSON:" in reason:
        return "LabTools local data file is not valid JSON."
    if "Missing LabTools local data file:" in reason:
        return "Missing LabTools local data file."
    if "Unable to read LabTools local data file:" in reason:
        return "Unable to read LabTools local data file."
    if "LabTools local data file must contain a JSON object:" in reason:
        return "LabTools local data file must contain a JSON object."
    return reason


def reagent_summary(record: ReagentRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "name": record.name,
        "category": record.category,
        "concentration": record.concentration,
        "unit": record.unit,
        "vendor": record.vendor,
        "catalog_number": record.catalog_number,
        "lot_number": record.lot_number,
        "storage_location": record.storage_location,
        "expiry_date": record.expiry_date,
        "status": record.status,
        "version": record.version,
        "source_mode": record.source_mode,
        "updated_at": record.updated_at,
    }


def sample_summary(record: SampleRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "sample_name": record.sample_name,
        "sample_type": record.sample_type,
        "linked_experiment": record.linked_experiment,
        "project": record.project,
        "concentration": record.concentration,
        "concentration_unit": record.concentration_unit,
        "volume": record.volume,
        "volume_unit": record.volume_unit,
        "storage_location": record.storage_location,
        "status": record.status,
        "version": record.version,
        "source_mode": record.source_mode,
        "updated_at": record.updated_at,
    }


def cell_summary(record: CellProfileRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "cell_name": record.cell_name,
        "species": record.species,
        "disease": record.disease,
        "source": record.source,
        "passage": record.passage,
        "mycoplasma_status": record.mycoplasma_status,
        "storage_status": record.storage_status,
        "status": record.status,
        "version": record.version,
        "source_mode": record.source_mode,
        "updated_at": record.updated_at,
    }


def freeze_vial_summary(record: FreezeVialRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "freeze_batch_id": record.freeze_batch_id,
        "vial_label": record.vial_label,
        "location": record.location,
        "status": record.status,
        "version": record.version,
        "source_mode": record.source_mode,
        "updated_at": record.updated_at,
    }


def record_index_summary(record: LabToolsRecordIndexEntry) -> dict[str, Any]:
    return {
        "id": record.id,
        "record_type": record.record_type,
        "title": record.title,
        "summary": record.record_summary,
        "linked_reagents": list(record.linked_reagents),
        "linked_samples": list(record.linked_samples),
        "linked_cells": list(record.linked_cells),
        "artifact_refs": list(record.artifact_refs),
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "version": record.version,
        "source_mode": record.source_mode,
    }
