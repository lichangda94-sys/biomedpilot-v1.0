from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


IMAGEJ_FIJI_RUNTIME_MANIFEST_SCHEMA_VERSION = "biomedpilot_imagej_fiji_runtime.v1"
IMAGEJ_FIJI_ENGINE_ID = "imagej_fiji"
IMAGEJ_FIJI_ENGINE_NAME = "ImageJ/Fiji 图像分析引擎"
IMAGEJ_FIJI_ENGINE_TYPE = "local_image_analysis_backend"
IMAGEJ_FIJI_RECOMMENDED_VERSION = "Fiji Stable / ImageJ 1.x or 2.x"
IMAGEJ_FIJI_DOWNLOAD_BASE_URL = "https://downloads.imagej.net/fiji/latest"


@dataclass(frozen=True)
class ImageJFijiDownloadAsset:
    platform: str
    architecture: str
    filename: str
    url: str
    sha256_url: str
    distribution: str = "fiji"

    def to_dict(self) -> dict[str, str]:
        return {
            "distribution": self.distribution,
            "platform": self.platform,
            "architecture": self.architecture,
            "filename": self.filename,
            "url": self.url,
            "sha256_url": self.sha256_url,
        }


@dataclass(frozen=True)
class ImageJFijiRuntimeManifest:
    runtime_id: str
    platform: str
    executable_path: str
    app_root: str
    distribution: str = "fiji"
    architecture: str = ""
    archive_url: str = ""
    archive_sha256: str = ""
    detected_version: str = ""
    smoke_test_status: str = "unknown"
    smoke_test_result_path: str = ""
    created_at: str = ""
    schema_version: str = IMAGEJ_FIJI_RUNTIME_MANIFEST_SCHEMA_VERSION
    engine_id: str = IMAGEJ_FIJI_ENGINE_ID

    @property
    def engine_version(self) -> str:
        return self.detected_version

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "runtime_id": self.runtime_id,
            "created_at": self.created_at,
            "platform": self.platform,
            "architecture": self.architecture,
            "distribution": self.distribution,
            "archive": {"url": self.archive_url, "sha256": self.archive_sha256},
            "application": {"root": self.app_root, "executable": self.executable_path},
            "version": {"detected": self.detected_version},
            "smoke_test": {"status": self.smoke_test_status, "result_path": self.smoke_test_result_path},
        }


def default_imagej_fiji_runtime_root(
    *,
    platform_name: str | None = None,
    home: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    platform_value = platform_name or sys.platform
    home_path = Path(home).expanduser() if home is not None else Path.home()
    env_values = env or os.environ
    if platform_value == "darwin":
        return home_path / "Library" / "Application Support" / "BioMedPilot" / "engines" / "image_analysis" / "imagej_fiji"
    if platform_value.startswith("win"):
        local_app_data = env_values.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else home_path / "AppData" / "Local"
        return base / "BioMedPilot" / "engines" / "image_analysis" / "imagej_fiji"
    return home_path / ".local" / "share" / "BioMedPilot" / "engines" / "image_analysis" / "imagej_fiji"


def imagej_fiji_runtime_manifest_path(runtime_root: str | Path) -> Path:
    return Path(runtime_root).expanduser() / "runtime_manifest.json"


def load_imagej_fiji_runtime_manifest(runtime_root: str | Path) -> ImageJFijiRuntimeManifest:
    path = imagej_fiji_runtime_manifest_path(runtime_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("imagej_fiji_runtime_manifest_missing") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("imagej_fiji_runtime_manifest_invalid") from exc
    return imagej_fiji_runtime_manifest_from_dict(payload)


def write_imagej_fiji_runtime_manifest(runtime_root: str | Path, manifest: ImageJFijiRuntimeManifest) -> Path:
    path = imagej_fiji_runtime_manifest_path(runtime_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def imagej_fiji_runtime_manifest_from_dict(payload: Any) -> ImageJFijiRuntimeManifest:
    if not isinstance(payload, dict):
        raise ValueError("imagej_fiji_runtime_manifest_must_be_object")
    if payload.get("schema_version") != IMAGEJ_FIJI_RUNTIME_MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported_imagej_fiji_runtime_manifest_schema")
    if str(payload.get("engine_id") or IMAGEJ_FIJI_ENGINE_ID) != IMAGEJ_FIJI_ENGINE_ID:
        raise ValueError("imagej_fiji_runtime_manifest_engine_id_mismatch")

    archive_payload = payload.get("archive") if isinstance(payload.get("archive"), dict) else {}
    application_payload = payload.get("application") if isinstance(payload.get("application"), dict) else {}
    version_payload = payload.get("version") if isinstance(payload.get("version"), dict) else {}
    smoke_payload = payload.get("smoke_test") if isinstance(payload.get("smoke_test"), dict) else {}

    runtime_id = str(payload.get("runtime_id") or "").strip()
    executable_path = str(application_payload.get("executable") or "").strip()
    app_root = str(application_payload.get("root") or "").strip()
    if not runtime_id:
        raise ValueError("imagej_fiji_runtime_manifest_missing_runtime_id")
    if not executable_path:
        raise ValueError("imagej_fiji_runtime_manifest_missing_executable")
    if not app_root:
        raise ValueError("imagej_fiji_runtime_manifest_missing_app_root")

    return ImageJFijiRuntimeManifest(
        runtime_id=runtime_id,
        platform=str(payload.get("platform") or ""),
        architecture=str(payload.get("architecture") or ""),
        distribution=str(payload.get("distribution") or "fiji"),
        executable_path=executable_path,
        app_root=app_root,
        archive_url=str(archive_payload.get("url") or ""),
        archive_sha256=str(archive_payload.get("sha256") or ""),
        detected_version=str(version_payload.get("detected") or ""),
        smoke_test_status=str(smoke_payload.get("status") or "unknown"),
        smoke_test_result_path=str(smoke_payload.get("result_path") or ""),
        created_at=str(payload.get("created_at") or ""),
    )


def select_imagej_fiji_download_asset(
    *,
    platform_name: str | None = None,
    machine: str | None = None,
    base_url: str = IMAGEJ_FIJI_DOWNLOAD_BASE_URL,
) -> ImageJFijiDownloadAsset:
    platform_value = platform_name or sys.platform
    architecture = _normalize_architecture(machine or platform.machine())
    platform_label, filename = _download_filename_for_platform(platform_value, architecture)
    url = f"{base_url.rstrip('/')}/{filename}"
    return ImageJFijiDownloadAsset(
        platform=platform_label,
        architecture=architecture,
        filename=filename,
        url=url,
        sha256_url=f"{url}.sha256",
    )


def _download_filename_for_platform(platform_name: str, architecture: str) -> tuple[str, str]:
    if platform_name == "darwin":
        suffix = "macos-arm64" if architecture == "arm64" else "macos64"
        return "macos", f"fiji-latest-{suffix}-jdk.zip"
    if platform_name.startswith("win"):
        suffix = "win-arm64" if architecture == "arm64" else "win64"
        return "windows", f"fiji-latest-{suffix}-jdk.zip"
    suffix = "linux-arm64" if architecture == "arm64" else "linux64"
    return "linux", f"fiji-latest-{suffix}-jdk.zip"


def _normalize_architecture(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"arm64", "aarch64"}:
        return "arm64"
    return "x86_64"
