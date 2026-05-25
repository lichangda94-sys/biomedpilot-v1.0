from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from labtools.local_data import LabToolsDataSourceAdapterStatus


LAN_CLIENT_READONLY_DISABLED_REASON = "LAN client read-only adapter does not allow writes."
LAN_CLIENT_SCHEMA_VERSION = "labtools_lan_api.v1"
LOOPBACK_NETLOCS = frozenset({"127.0.0.1", "localhost"})


@dataclass(frozen=True)
class LabToolsLanReadonlyClientConfig:
    server_url: str
    server_label: str = "manual-loopback-server"
    workspace_id: str = ""
    timeout_seconds: float = 3.0
    data_source_mode: str = "future_lan"

    def normalized(self) -> "LabToolsLanReadonlyClientConfig":
        url = str(self.server_url or "").strip().rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme != "http":
            raise ValueError("LAN read-only client prototype only supports http loopback URLs.")
        if not _is_allowed_lan_readonly_host(parsed.hostname):
            raise ValueError("LAN read-only client only allows loopback or private LAN server URLs.")
        if parsed.path not in {"", "/"}:
            raise ValueError("LAN read-only client server_url must not include an API path.")
        timeout = float(self.timeout_seconds)
        if timeout <= 0:
            raise ValueError("LAN read-only client timeout must be positive.")
        return LabToolsLanReadonlyClientConfig(
            server_url=url,
            server_label=str(self.server_label or "manual-loopback-server").strip(),
            workspace_id=str(self.workspace_id or "").strip(),
            timeout_seconds=timeout,
            data_source_mode="future_lan",
        )


@dataclass(frozen=True)
class LabToolsLanReadonlyClientConnectionStatus:
    status: str
    data_source_mode: str
    enabled: bool
    network_enabled: bool
    connected: bool
    server_url: str
    server_label: str
    workspace_id: str
    reason: str
    adapter_status: LabToolsDataSourceAdapterStatus


@dataclass(frozen=True)
class LabToolsLanReadonlyReadModel:
    status: LabToolsDataSourceAdapterStatus
    reagents: tuple[Mapping[str, Any], ...] = ()
    samples: tuple[Mapping[str, Any], ...] = ()
    cells: tuple[Mapping[str, Any], ...] = ()
    freeze_vials: tuple[Mapping[str, Any], ...] = ()
    records: tuple[Mapping[str, Any], ...] = ()
    counts: Mapping[str, int] | None = None


class LabToolsLanReadonlyClientDataSourceAdapter:
    data_source_mode = "future_lan"

    def __init__(self, config: LabToolsLanReadonlyClientConfig) -> None:
        self.config = config.normalized()

    def client_status(self) -> LabToolsLanReadonlyClientConnectionStatus:
        adapter_status = self.status()
        connected = adapter_status.read_enabled
        return LabToolsLanReadonlyClientConnectionStatus(
            status=adapter_status.status,
            data_source_mode="future_lan",
            enabled=True,
            network_enabled=True,
            connected=connected,
            server_url=self.config.server_url,
            server_label=self.config.server_label,
            workspace_id=self.config.workspace_id,
            reason=adapter_status.reason,
            adapter_status=adapter_status,
        )

    def status(self) -> LabToolsDataSourceAdapterStatus:
        envelope = self._get_envelope("/status")
        if not envelope.get("ok"):
            return _blocked_status(str(envelope.get("status") or "blocked_server_unavailable"), str(envelope.get("reason") or "LAN server unavailable."))
        data = _dict_payload(envelope.get("data"))
        adapter_status = _dict_payload(data.get("adapter_status"))
        read_enabled = bool(adapter_status.get("read_enabled"))
        semantic_status = "ready_readonly" if read_enabled else _blocked_read_status(adapter_status.get("status"))
        return LabToolsDataSourceAdapterStatus(
            status=semantic_status,
            data_source_mode="future_lan",
            read_enabled=read_enabled,
            write_enabled=False,
            history_enabled=read_enabled,
            export_enabled=False,
            reason=str(adapter_status.get("reason") or envelope.get("reason") or "LAN read-only client status."),
        )

    def read_model(self) -> LabToolsLanReadonlyReadModel:
        status = self.status()
        if not status.read_enabled:
            return LabToolsLanReadonlyReadModel(status=status, counts={})
        return LabToolsLanReadonlyReadModel(
            status=status,
            reagents=self.list_reagents(),
            samples=self.list_samples(),
            cells=self.list_cells(),
            freeze_vials=self.list_freeze_vials(),
            records=self.list_record_index(),
            counts=self.summary_counts(),
        )

    def summary_counts(self) -> Mapping[str, int]:
        envelope = self._get_envelope("/records/summary")
        if not envelope.get("ok"):
            return {}
        data = _dict_payload(envelope.get("data"))
        counts = data.get("counts")
        if not isinstance(counts, dict):
            return {}
        return {str(key): int(value or 0) for key, value in counts.items()}

    def list_reagents(self) -> tuple[Mapping[str, Any], ...]:
        return self._list_endpoint("/reagents")

    def list_samples(self) -> tuple[Mapping[str, Any], ...]:
        return self._list_endpoint("/samples")

    def list_cells(self) -> tuple[Mapping[str, Any], ...]:
        return self._list_endpoint("/cells")

    def list_freeze_vials(self) -> tuple[Mapping[str, Any], ...]:
        return self._list_endpoint("/freeze-vials")

    def list_record_index(self, record_type: str | None = None) -> tuple[Mapping[str, Any], ...]:
        path = "/record-index"
        if record_type:
            path = f"{path}?{urlencode({'record_type': record_type})}"
        return self._list_endpoint(path)

    def create_reagent(self, payload: Mapping[str, object]) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def update_reagent(self, reagent_id: str, payload: Mapping[str, object], *, expected_version: int) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def archive_reagent(self, reagent_id: str, *, expected_version: int) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def create_sample(self, payload: Mapping[str, object]) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def update_sample(self, sample_id: str, payload: Mapping[str, object], *, expected_version: int) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def archive_sample(self, sample_id: str, *, expected_version: int) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def create_record_index_entry(self, payload: Mapping[str, object]) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def update_record_index_status(self, record_id: str, status: str, *, expected_version: int) -> Mapping[str, Any]:
        raise PermissionError(LAN_CLIENT_READONLY_DISABLED_REASON)

    def _list_endpoint(self, path: str) -> tuple[Mapping[str, Any], ...]:
        envelope = self._get_envelope(path)
        if not envelope.get("ok"):
            return ()
        data = envelope.get("data")
        if not isinstance(data, list):
            return ()
        return tuple(item for item in data if isinstance(item, Mapping))

    def _get_envelope(self, path: str) -> Mapping[str, Any]:
        url = f"{self.config.server_url}{path}"
        request = Request(url, method="GET")
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310 - loopback-only prototype.
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                return _blocked_envelope("blocked_invalid_response", "LAN server returned a malformed error response.")
        except URLError:
            return _blocked_envelope("blocked_server_unavailable", "LAN server is unavailable.")
        except TimeoutError:
            return _blocked_envelope("blocked_server_unavailable", "LAN server request timed out.")
        except json.JSONDecodeError:
            return _blocked_envelope("blocked_invalid_response", "LAN server returned malformed JSON.")
        except OSError:
            return _blocked_envelope("blocked_server_unavailable", "LAN server request failed.")
        if not isinstance(payload, Mapping):
            return _blocked_envelope("blocked_invalid_response", "LAN server response must be a JSON object.")
        if payload.get("schema_version") != LAN_CLIENT_SCHEMA_VERSION:
            return _blocked_envelope("blocked_invalid_response", "LAN server response schema is unsupported.")
        return payload


def build_lan_readonly_client_adapter(config: LabToolsLanReadonlyClientConfig) -> LabToolsLanReadonlyClientDataSourceAdapter:
    return LabToolsLanReadonlyClientDataSourceAdapter(config)


def _blocked_status(status: str, reason: str) -> LabToolsDataSourceAdapterStatus:
    return LabToolsDataSourceAdapterStatus(
        status=status,
        data_source_mode="future_lan",
        read_enabled=False,
        write_enabled=False,
        history_enabled=False,
        export_enabled=False,
        reason=reason,
    )


def _blocked_envelope(status: str, reason: str) -> Mapping[str, Any]:
    return {"ok": False, "status": status, "reason": reason, "data_source_mode": "future_lan", "data": None, "schema_version": LAN_CLIENT_SCHEMA_VERSION}


def _dict_payload(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _status_text(value: object, *, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _blocked_read_status(value: object) -> str:
    text = _status_text(value, default="blocked_read_disabled")
    if text == "missing_store":
        return "blocked_store_missing"
    if text == "blocked_invalid_store":
        return "blocked_invalid_store"
    if text.startswith("blocked_"):
        return text
    return "blocked_read_disabled"


def _is_allowed_lan_readonly_host(host: str | None) -> bool:
    if host in LOOPBACK_NETLOCS:
        return True
    if not host:
        return False
    try:
        parsed = ip_address(host)
    except ValueError:
        return host.endswith(".local")
    return parsed.is_private or parsed.is_link_local
