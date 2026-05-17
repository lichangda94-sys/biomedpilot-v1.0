from __future__ import annotations

import json
import shutil
import socket
import subprocess
import zipfile
from pathlib import Path

import pytest

from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    IMAGEJ_FIJI_RUNTIME_MANIFEST_SCHEMA_VERSION,
    IMAGEJ_FIJI_ENGINE_ID,
    ImageJFijiDownloadAsset,
    ImageJFijiRuntimeManifest,
    ImageJFijiBridge,
    LocalEngineConfigStore,
    build_imagej_fiji_macro_command,
    default_imagej_fiji_runtime_root,
    detect_imagej_fiji_status,
    detect_imagej_fiji_runtime_status,
    engine_status_from_dict,
    extract_zip_safely,
    imagej_fiji_install_guide_text,
    imagej_fiji_runtime_manifest_from_dict,
    imagej_fiji_setup_prompt_text,
    infer_imagej_fiji_bundled_java_home,
    load_imagej_fiji_runtime_manifest,
    prepare_imagej_fiji_runtime,
    parse_imagej_fiji_version_output,
    select_imagej_fiji_download_asset,
    sha256_file,
    write_imagej_fiji_runtime_manifest,
)


def _fake_executable(tmp_path: Path) -> Path:
    path = tmp_path / "fake_imagej"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _successful_runner(command, **kwargs):
    if "--version" in command:
        return subprocess.CompletedProcess(command, 0, stdout="Fiji 2.14.0\n", stderr="")
    output_path = Path(command[-1])
    output_path.write_text("status=ok\n", encoding="utf-8")
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def _write_fake_fiji_archive(tmp_path: Path) -> Path:
    archive_path = tmp_path / "fiji-test.zip"
    info = zipfile.ZipInfo("Fiji/Fiji.app/Contents/MacOS/fiji-macos-arm64")
    info.external_attr = 0o755 << 16
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(info, "#!/bin/sh\nexit 0\n")
    return archive_path


def test_missing_path_returns_not_configured_when_no_common_path(monkeypatch) -> None:
    import app.shared.local_engines.imagej_fiji_detector as detector

    monkeypatch.setattr(detector, "detect_common_imagej_fiji_paths", lambda: ())
    monkeypatch.setattr(
        detector,
        "detect_imagej_fiji_runtime_status",
        lambda *args, **kwargs: detector.default_imagej_fiji_status(ENGINE_STATUS_NOT_CONFIGURED),
    )

    status = detect_imagej_fiji_status()

    assert status.status == ENGINE_STATUS_NOT_CONFIGURED
    assert status.engine_id == IMAGEJ_FIJI_ENGINE_ID
    assert "未找到" in status.last_error
    assert "静默下载" in status.install_guide_url_or_text


def test_configured_invalid_path_returns_failed(tmp_path) -> None:
    status = detect_imagej_fiji_status(configured_path=tmp_path / "missing")

    assert status.status == ENGINE_STATUS_FAILED
    assert "路径无效" in status.last_error
    assert "Traceback" not in status.last_error


def test_mocked_valid_path_returns_available(tmp_path) -> None:
    status = detect_imagej_fiji_status(configured_path=_fake_executable(tmp_path), runner=_successful_runner)

    assert status.status == ENGINE_STATUS_AVAILABLE
    assert status.available
    assert status.detected_version == "2.14.0"
    assert status.smoke_test_result == "status=ok"


def test_no_network_call_is_made_for_detection(tmp_path, monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # pragma: no cover - should never be called
        raise AssertionError("network socket should not be opened")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    status = detect_imagej_fiji_status(configured_path=_fake_executable(tmp_path), runner=_successful_runner)

    assert status.status == ENGINE_STATUS_AVAILABLE


def test_status_serialization_is_stable(tmp_path) -> None:
    status = detect_imagej_fiji_status(configured_path=_fake_executable(tmp_path), runner=_successful_runner)
    payload = status.to_dict()

    assert list(payload) == [
        "engine_id",
        "engine_name",
        "engine_type",
        "configured_path_or_endpoint",
        "detected_version",
        "recommended_version",
        "status",
        "last_check_at",
        "last_error",
        "smoke_test_result",
        "install_guide_url_or_text",
    ]
    assert json.loads(json.dumps(payload, ensure_ascii=False))["engine_id"] == IMAGEJ_FIJI_ENGINE_ID
    assert engine_status_from_dict(payload).to_dict() == payload


def test_config_store_and_bridge_round_trip(tmp_path) -> None:
    store = LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json")
    bridge = ImageJFijiBridge(store)
    executable = _fake_executable(tmp_path)

    configured = bridge.configure_path(executable)
    loaded = bridge.load_config()

    assert configured.to_dict() == loaded.to_dict()
    assert loaded.last_status is not None
    assert loaded.last_status.status == ENGINE_STATUS_CONFIGURED_UNVERIFIED

    status = bridge.check_status(runner=_successful_runner)

    assert status.status == ENGINE_STATUS_AVAILABLE
    assert bridge.load_config().last_status.status == ENGINE_STATUS_AVAILABLE


def test_default_runtime_roots_are_platform_specific(tmp_path: Path) -> None:
    assert default_imagej_fiji_runtime_root(platform_name="darwin", home=tmp_path).as_posix().endswith(
        "Library/Application Support/BioMedPilot/engines/image_analysis/imagej_fiji"
    )
    assert "BioMedPilot" in str(default_imagej_fiji_runtime_root(platform_name="win32", home=tmp_path, env={}))
    assert default_imagej_fiji_runtime_root(platform_name="linux", home=tmp_path).as_posix().endswith(
        ".local/share/BioMedPilot/engines/image_analysis/imagej_fiji"
    )


def test_download_asset_selection_uses_official_latest_fiji_names() -> None:
    mac_arm = select_imagej_fiji_download_asset(platform_name="darwin", machine="arm64")
    mac_x64 = select_imagej_fiji_download_asset(platform_name="darwin", machine="x86_64")
    win = select_imagej_fiji_download_asset(platform_name="win32", machine="AMD64")
    linux = select_imagej_fiji_download_asset(platform_name="linux", machine="aarch64")

    assert mac_arm.filename == "fiji-latest-macos-arm64-jdk.zip"
    assert mac_x64.filename == "fiji-latest-macos64-jdk.zip"
    assert win.filename == "fiji-latest-win64-jdk.zip"
    assert linux.filename == "fiji-latest-linux-arm64-jdk.zip"
    assert mac_arm.sha256_url.endswith(".zip.sha256")


def test_runtime_manifest_round_trip_and_status(tmp_path: Path) -> None:
    executable = _fake_executable(tmp_path)
    manifest = ImageJFijiRuntimeManifest(
        runtime_id="imagej-fiji-test",
        platform="macos",
        architecture="arm64",
        executable_path=str(executable),
        app_root=str(tmp_path),
        java_home=str(tmp_path / "java-home"),
        detected_version="2.14.0",
        smoke_test_status="ok",
    )
    write_imagej_fiji_runtime_manifest(tmp_path, manifest)

    loaded = load_imagej_fiji_runtime_manifest(tmp_path)
    status = detect_imagej_fiji_runtime_status(tmp_path)

    assert loaded.to_dict()["schema_version"] == IMAGEJ_FIJI_RUNTIME_MANIFEST_SCHEMA_VERSION
    assert status.status == ENGINE_STATUS_AVAILABLE
    assert status.detected_version == "2.14.0"
    assert loaded.java_home == str(tmp_path / "java-home")
    assert imagej_fiji_runtime_manifest_from_dict(loaded.to_dict()).to_dict() == loaded.to_dict()


def test_runtime_download_requires_explicit_user_trigger(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="user_trigger"):
        prepare_imagej_fiji_runtime(runtime_root=tmp_path)


def test_prepare_runtime_downloads_verifies_extracts_and_writes_manifest(tmp_path: Path) -> None:
    source_archive = _write_fake_fiji_archive(tmp_path)
    source_sha = sha256_file(source_archive)
    asset = ImageJFijiDownloadAsset(
        platform="macos",
        architecture="arm64",
        filename="fiji-test.zip",
        url="https://example.invalid/fiji-test.zip",
        sha256_url="https://example.invalid/fiji-test.zip.sha256",
    )

    def fake_downloader(url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if url.endswith(".sha256"):
            destination.write_text(source_sha, encoding="utf-8")
        else:
            shutil.copyfile(source_archive, destination)

    result = prepare_imagej_fiji_runtime(
        runtime_root=tmp_path / "runtime-root",
        asset=asset,
        allow_network_download=True,
        downloader=fake_downloader,
        runner=_successful_runner,
    )
    status = detect_imagej_fiji_runtime_status(result.runtime_root)
    manifest = load_imagej_fiji_runtime_manifest(result.runtime_root)

    assert Path(result.executable_path).is_file()
    assert result.archive_sha256 == source_sha
    assert result.smoke_test_status == "ok"
    assert status.status == ENGINE_STATUS_AVAILABLE
    assert manifest.archive_url == asset.url
    assert manifest.java_home == ""


def test_extract_zip_safely_rejects_zip_slip(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", "bad")

    with pytest.raises(ValueError, match="unsafe"):
        extract_zip_safely(archive_path, tmp_path / "target")


def test_macro_command_contract_is_shell_safe(tmp_path: Path) -> None:
    command = build_imagej_fiji_macro_command(
        tmp_path / "Fiji App" / "ImageJ-macosx",
        macro_path=tmp_path / "macro with space.ijm",
        argument=tmp_path / "result.txt",
        java_home=tmp_path / "java home",
    )

    assert command == [
        str(tmp_path / "Fiji App" / "ImageJ-macosx"),
        f"--java-home={tmp_path / 'java home'}",
        "--headless",
        "-macro",
        str(tmp_path / "macro with space.ijm"),
        str(tmp_path / "result.txt"),
    ]


def test_infers_bundled_java_home_from_official_fiji_layout(tmp_path: Path) -> None:
    executable = tmp_path / "Fiji" / "Fiji.app" / "Contents" / "MacOS" / "fiji-macos-arm64"
    java = tmp_path / "Fiji" / "java" / "macos-arm64" / "zulu" / "zulu-21.jdk" / "Contents" / "Home" / "bin" / "java"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    java.parent.mkdir(parents=True)
    java.write_text("#!/bin/sh\n", encoding="utf-8")
    java.chmod(0o755)

    assert infer_imagej_fiji_bundled_java_home(executable) == str(java.parent.parent)


def test_version_parser_and_prompt_text_are_user_readable() -> None:
    assert parse_imagej_fiji_version_output("ImageJ 1.54f") == "1.54f"
    assert "本机" in imagej_fiji_install_guide_text()
    assert "自动检测" in imagej_fiji_setup_prompt_text(workflow_name="Western Blot 灰度分析")


def test_invalid_serialized_status_fails_closed() -> None:
    status = engine_status_from_dict(
        {
            "engine_id": IMAGEJ_FIJI_ENGINE_ID,
            "engine_name": "ImageJ/Fiji",
            "engine_type": "local",
            "status": "unexpected_status",
        }
    )

    assert status.status == ENGINE_STATUS_FAILED


def test_non_object_status_payload_is_rejected() -> None:
    with pytest.raises(ValueError):
        engine_status_from_dict([])
