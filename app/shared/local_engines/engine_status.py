from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ENGINE_STATUS_NOT_CONFIGURED = "not_configured"
ENGINE_STATUS_CONFIGURED_UNVERIFIED = "configured_unverified"
ENGINE_STATUS_AVAILABLE = "available"
ENGINE_STATUS_FAILED = "failed"
ENGINE_STATUS_UNSUPPORTED_VERSION = "unsupported_version"

ENGINE_STATUS_VALUES = (
    ENGINE_STATUS_NOT_CONFIGURED,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_UNSUPPORTED_VERSION,
)

UNKNOWN_VERSION = "unknown_version"


@dataclass(frozen=True)
class EngineStatus:
    engine_id: str
    engine_name: str
    engine_type: str
    configured_path_or_endpoint: str = ""
    detected_version: str = UNKNOWN_VERSION
    recommended_version: str = ""
    status: str = ENGINE_STATUS_NOT_CONFIGURED
    last_check_at: str = ""
    last_error: str = ""
    smoke_test_result: str = ""
    install_guide_url_or_text: str = ""

    @property
    def available(self) -> bool:
        return self.status == ENGINE_STATUS_AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_type": self.engine_type,
            "configured_path_or_endpoint": self.configured_path_or_endpoint,
            "detected_version": self.detected_version,
            "recommended_version": self.recommended_version,
            "status": self.status,
            "last_check_at": self.last_check_at,
            "last_error": self.last_error,
            "smoke_test_result": self.smoke_test_result,
            "install_guide_url_or_text": self.install_guide_url_or_text,
        }


def engine_status_from_dict(payload: Any) -> EngineStatus:
    if not isinstance(payload, dict):
        raise ValueError("Local engine status payload must be a JSON object")
    status = str(payload.get("status", ENGINE_STATUS_FAILED))
    if status not in ENGINE_STATUS_VALUES:
        status = ENGINE_STATUS_FAILED
    return EngineStatus(
        engine_id=str(payload.get("engine_id", "")),
        engine_name=str(payload.get("engine_name", "")),
        engine_type=str(payload.get("engine_type", "")),
        configured_path_or_endpoint=str(payload.get("configured_path_or_endpoint", "")),
        detected_version=str(payload.get("detected_version", UNKNOWN_VERSION) or UNKNOWN_VERSION),
        recommended_version=str(payload.get("recommended_version", "")),
        status=status,
        last_check_at=str(payload.get("last_check_at", "")),
        last_error=str(payload.get("last_error", "")),
        smoke_test_result=str(payload.get("smoke_test_result", "")),
        install_guide_url_or_text=str(payload.get("install_guide_url_or_text", "")),
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
