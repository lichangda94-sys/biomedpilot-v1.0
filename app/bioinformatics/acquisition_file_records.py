from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_MANIFEST_SCHEMA_VERSION = "biomedpilot.acquisition_source_manifest.v1"


def build_file_record(
    path: str | Path,
    *,
    source: str,
    role: str = "",
    status: str = "available",
    source_url: str = "",
    source_path: str = "",
    remote_checksum: str = "",
    risk_level: str = "",
    message: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local_path = Path(path).expanduser()
    exists = local_path.is_file()
    payload: dict[str, Any] = {
        "source": source,
        "source_url": source_url,
        "source_path": source_path,
        "local_path": str(local_path.resolve()) if exists else str(local_path),
        "status": status if exists else "missing",
        "size_bytes": local_path.stat().st_size if exists else 0,
        "sha256": sha256_file(local_path) if exists else "",
        "remote_checksum": remote_checksum,
        "role": role,
        "risk_level": risk_level,
        "message": message,
    }
    if extra:
        payload.update(extra)
    return payload


def build_blocked_file_record(
    *,
    source: str,
    role: str,
    source_url: str = "",
    source_path: str = "",
    risk_level: str = "high",
    message: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source": source,
        "source_url": source_url,
        "source_path": source_path,
        "local_path": "",
        "status": "blocked",
        "size_bytes": 0,
        "sha256": "",
        "remote_checksum": "",
        "role": role,
        "risk_level": risk_level,
        "message": message,
    }
    if extra:
        payload.update(extra)
    return payload


def write_source_manifest(
    path: str | Path,
    *,
    acquisition_id: str,
    source_type: str,
    source_label: str,
    source: str,
    file_records: list[dict[str, Any]],
    receipt_path: str = "",
    request_path: str = "",
    status: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    statuses = [str(record.get("status") or "") for record in file_records]
    payload: dict[str, Any] = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "acquisition_id": acquisition_id,
        "source_type": source_type,
        "source_label": source_label,
        "source": source,
        "created_at": _now(),
        "status": status or _manifest_status(statuses),
        "receipt_path": receipt_path,
        "request_path": request_path,
        "file_records": file_records,
        "summary": summarize_file_records(file_records),
    }
    if extra:
        payload.update(extra)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def summarize_file_records(file_records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    for record in file_records:
        status = str(record.get("status") or "unknown")
        role = str(record.get("role") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        role_counts[role] = role_counts.get(role, 0) + 1
    real_files = [record for record in file_records if str(record.get("local_path") or "") and str(record.get("status") or "") in {"available", "downloaded", "cache_hit", "copied", "referenced"}]
    return {
        "file_count": len(file_records),
        "real_file_count": len(real_files),
        "status_counts": status_counts,
        "role_counts": role_counts,
        "total_size_bytes": sum(int(record.get("size_bytes") or 0) for record in file_records),
        "sha256_recorded_count": sum(1 for record in file_records if str(record.get("sha256") or "")),
    }


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_status(statuses: list[str]) -> str:
    if not statuses:
        return "empty"
    if any(status in {"failed", "missing"} for status in statuses):
        return "partial_with_errors"
    if any(status == "blocked" for status in statuses):
        return "partial_with_blocked"
    if any(status in {"available", "downloaded", "cache_hit", "copied", "referenced"} for status in statuses):
        return "available"
    return "recorded"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
