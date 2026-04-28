"""Minimal local/mockable download runtime for TCGA/GTEx."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any
from urllib import request


DOWNLOAD_MANIFEST_FILE = "download_manifest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _record_to_mapping(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(f"Unsupported record type for download runtime: {type(record)!r}")


def _resolve_locator(record: dict[str, Any]) -> tuple[str | None, str | None]:
    metadata = record.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}

    local_path = record.get("local_path") or metadata.get("local_path")
    if local_path:
        return "local_path", str(local_path)

    download_url = record.get("download_url") or metadata.get("download_url")
    if download_url:
        return "download_url", str(download_url)

    return None, None


def _download_relative_path(record: dict[str, Any]) -> Path:
    source = (record.get("source") or "unknown").replace("/", "_")
    study_id = record.get("study_id") or "unknown"
    file_name = record.get("file_name") or (record.get("file_id") or "downloaded_asset.dat")
    return Path("downloaded_files") / source / study_id / file_name


def _copy_local_file(source_path: Path, target_path: Path) -> int:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    return target_path.stat().st_size


def _download_http_file(url: str, target_path: Path) -> int:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with request.urlopen(url, timeout=15) as response, target_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return target_path.stat().st_size


def download_dataset_files(
    study_id: str,
    out_dir: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or {}
    output_dir = Path(out_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / DOWNLOAD_MANIFEST_FILE

    raw_records = options.get("resolved_records") or options.get("file_records") or []
    records = [_record_to_mapping(record) for record in raw_records]
    selected_records = [record for record in records if (record.get("study_id") or "").upper() == study_id.upper()]

    if not selected_records:
        return {
            "status": "failed",
            "message": "No resolved records matched the requested study_id for download.",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path),
            "warnings": [],
            "data": {
                "study_id": study_id,
                "record_count": 0,
                "records": [],
            },
        }

    manifest_records: list[dict[str, Any]] = []
    success_count = 0
    failed_count = 0

    for record in selected_records:
        locator_type, locator_value = _resolve_locator(record)
        manifest_record = {
            "source": record.get("source"),
            "study_id": record.get("study_id"),
            "file_name": record.get("file_name"),
            "guessed_role": record.get("guessed_role"),
            "locator_type": locator_type,
            "locator_value": locator_value,
            "status": "failed",
            "size_bytes": 0,
            "relative_path": None,
            "error_message": "",
        }

        if locator_type is None or locator_value is None:
            manifest_record["error_message"] = "Missing downloadable locator (local_path or download_url)."
            manifest_records.append(manifest_record)
            failed_count += 1
            continue

        target_path = output_dir / _download_relative_path(record)
        manifest_record["relative_path"] = str(target_path.relative_to(output_dir).as_posix())

        try:
            if locator_type == "local_path":
                source_path = Path(locator_value).expanduser().resolve()
                if not source_path.exists() or not source_path.is_file():
                    raise FileNotFoundError(f"Local download source does not exist: {source_path}")
                size_bytes = _copy_local_file(source_path, target_path)
            elif locator_type == "download_url":
                size_bytes = _download_http_file(locator_value, target_path)
            else:
                raise ValueError(f"Unsupported locator type: {locator_type}")
        except Exception as exc:
            manifest_record["error_message"] = str(exc)
            manifest_records.append(manifest_record)
            failed_count += 1
            continue

        manifest_record["status"] = "success"
        manifest_record["size_bytes"] = size_bytes
        manifest_records.append(manifest_record)
        success_count += 1

    manifest_payload = {
        "generated_at": _now_iso(),
        "study_id": study_id,
        "output_dir": str(output_dir),
        "download_root": "downloaded_files/",
        "record_count": len(selected_records),
        "success_count": success_count,
        "failed_count": failed_count,
        "all_succeeded": failed_count == 0 and success_count > 0,
        "records": manifest_records,
    }
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if failed_count > 0 or success_count == 0:
        return {
            "status": "failed",
            "message": "One or more TCGA/GTEx files could not be downloaded.",
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path),
            "warnings": [],
            "data": manifest_payload,
        }

    return {
        "status": "success",
        "message": f"Downloaded {success_count} TCGA/GTEx files into the local runtime directory.",
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "warnings": [],
        "data": manifest_payload,
    }


__all__ = ["DOWNLOAD_MANIFEST_FILE", "download_dataset_files"]
