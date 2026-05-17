from __future__ import annotations

import hashlib
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.request import urlopen

from app.shared.local_engines.engine_status import ENGINE_STATUS_AVAILABLE, UNKNOWN_VERSION, utc_now
from app.shared.local_engines.imagej_fiji_detector import (
    DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
    detect_imagej_fiji_version,
    infer_imagej_fiji_bundled_java_home,
    resolve_imagej_fiji_executable,
    run_imagej_fiji_smoke_test,
)
from app.shared.local_engines.imagej_fiji_runtime import (
    IMAGEJ_FIJI_ENGINE_ID,
    ImageJFijiDownloadAsset,
    ImageJFijiRuntimeManifest,
    default_imagej_fiji_runtime_root,
    select_imagej_fiji_download_asset,
    write_imagej_fiji_runtime_manifest,
)
from app.shared.local_engines.imagej_fiji_runner_contract import build_imagej_fiji_macro_command


Downloader = Callable[[str, Path], None]
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ImageJFijiRuntimeInstallResult:
    runtime_root: str
    manifest_path: str
    executable_path: str
    app_root: str
    archive_path: str
    archive_sha256: str
    smoke_test_status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "runtime_root": self.runtime_root,
            "manifest_path": self.manifest_path,
            "executable_path": self.executable_path,
            "app_root": self.app_root,
            "archive_path": self.archive_path,
            "archive_sha256": self.archive_sha256,
            "smoke_test_status": self.smoke_test_status,
        }


def prepare_imagej_fiji_runtime(
    *,
    runtime_root: str | Path | None = None,
    asset: ImageJFijiDownloadAsset | None = None,
    allow_network_download: bool = False,
    replace_existing: bool = False,
    run_smoke_test: bool = True,
    downloader: Downloader | None = None,
    runner: Runner = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
) -> ImageJFijiRuntimeInstallResult:
    if not allow_network_download:
        raise PermissionError("imagej_fiji_download_requires_user_trigger")

    root = Path(runtime_root).expanduser() if runtime_root is not None else default_imagej_fiji_runtime_root()
    selected_asset = asset or select_imagej_fiji_download_asset()
    downloads_dir = root / "downloads"
    payload_root = root / "runtime"
    archive_path = downloads_dir / selected_asset.filename

    downloads_dir.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    _prepare_empty_directory(payload_root, replace_existing=replace_existing)

    download = downloader or _download_file
    download(selected_asset.url, archive_path)
    sha256_text_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    download(selected_asset.sha256_url, sha256_text_path)
    expected_sha256 = _parse_sha256_text(sha256_text_path.read_text(encoding="utf-8"))
    actual_sha256 = sha256_file(archive_path)
    if expected_sha256 and actual_sha256.lower() != expected_sha256.lower():
        raise ValueError("imagej_fiji_archive_sha256_mismatch")

    extract_zip_safely(archive_path, payload_root)
    app_root, executable_path = locate_imagej_fiji_runtime_executable(payload_root)
    java_home = infer_imagej_fiji_bundled_java_home(executable_path)
    detected_version = detect_imagej_fiji_version(
        executable_path,
        runner=runner,
        timeout_seconds=timeout_seconds,
        java_home=java_home,
    )
    smoke_status = "unknown"
    if run_smoke_test:
        status = run_imagej_fiji_smoke_test(
            executable_path,
            configured_path=app_root,
            runner=runner,
            timeout_seconds=timeout_seconds,
            java_home=java_home,
        )
        smoke_status = "ok" if status.status == ENGINE_STATUS_AVAILABLE else "failed"

    manifest = ImageJFijiRuntimeManifest(
        runtime_id=f"{IMAGEJ_FIJI_ENGINE_ID}-{selected_asset.platform}-{selected_asset.architecture}",
        platform=selected_asset.platform,
        architecture=selected_asset.architecture,
        distribution=selected_asset.distribution,
        executable_path=str(executable_path),
        app_root=str(app_root),
        archive_url=selected_asset.url,
        archive_sha256=actual_sha256,
        java_home=java_home,
        detected_version="" if detected_version == UNKNOWN_VERSION else detected_version,
        smoke_test_status=smoke_status,
        created_at=utc_now(),
    )
    manifest_path = write_imagej_fiji_runtime_manifest(root, manifest)
    return ImageJFijiRuntimeInstallResult(
        runtime_root=str(root),
        manifest_path=str(manifest_path),
        executable_path=str(executable_path),
        app_root=str(app_root),
        archive_path=str(archive_path),
        archive_sha256=actual_sha256,
        smoke_test_status=smoke_status,
    )


def run_imagej_fiji_macro(
    executable: str | Path,
    *,
    macro_path: str | Path,
    argument: str | Path = "",
    headless: bool = True,
    java_home: str | Path = "",
    runner: Runner = subprocess.run,
    timeout_seconds: int = DEFAULT_IMAGEJ_FIJI_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    command = build_imagej_fiji_macro_command(
        executable,
        macro_path=macro_path,
        argument=argument,
        headless=headless,
        java_home=java_home,
    )
    return runner(command, capture_output=True, text=True, timeout=timeout_seconds)


def locate_imagej_fiji_runtime_executable(runtime_payload_root: str | Path) -> tuple[Path, Path]:
    root = Path(runtime_payload_root).expanduser()
    for app_path in sorted(root.rglob("*.app")):
        try:
            return app_path, resolve_imagej_fiji_executable(app_path)
        except ValueError:
            continue
    names = {
        "ImageJ-macosx",
        "ImageJ-linux64",
        "ImageJ-linux-arm64",
        "ImageJ-win64.exe",
        "ImageJ-win32.exe",
        "ImageJ.exe",
        "ImageJ",
        "Fiji",
        "fiji",
        "fiji-macos-arm64",
        "fiji-macos-x64",
        "fiji-macos",
        "jaunch-macos-arm64",
        "jaunch-macos-x64",
        "jaunch-macos",
    }
    for candidate in sorted(path for path in root.rglob("*") if path.name in names):
        try:
            executable = resolve_imagej_fiji_executable(candidate)
        except ValueError:
            continue
        return candidate.parent, executable
    raise ValueError("imagej_fiji_runtime_executable_not_found")


def extract_zip_safely(archive_path: str | Path, destination: str | Path) -> None:
    archive = Path(archive_path)
    target = Path(destination).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    target_resolved = target.resolve()
    with zipfile.ZipFile(archive) as zip_file:
        for member in zip_file.infolist():
            member_path = target / member.filename
            try:
                member_path.resolve().relative_to(target_resolved)
            except ValueError as exc:
                raise ValueError("imagej_fiji_archive_unsafe_path") from exc
            extracted = Path(zip_file.extract(member, target))
            mode = member.external_attr >> 16
            if mode & 0o111:
                extracted.chmod(extracted.stat().st_mode | 0o111)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def _parse_sha256_text(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    return text.split()[0]


def _prepare_empty_directory(path: Path, *, replace_existing: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace_existing:
            raise FileExistsError("imagej_fiji_runtime_directory_not_empty")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
