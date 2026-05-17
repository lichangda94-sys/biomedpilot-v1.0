from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    PADDLEOCR_ENGINE_ID,
    PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION,
    PADDLEOCR_WORKER_MODE_IMAGE,
    PADDLEOCR_WORKER_MODE_PDF,
    PADDLEOCR_WORKER_MODULE,
    LocalEngineConfigStore,
    PaddleOCRBridge,
    build_paddleocr_worker_command,
    default_paddleocr_runtime_root,
    detect_paddleocr_runtime_status,
    load_paddleocr_runtime_manifest,
    paddleocr_install_guide_text,
)


def test_missing_manifest_returns_not_configured(tmp_path: Path) -> None:
    status = detect_paddleocr_runtime_status(tmp_path / "missing_runtime")

    assert status.engine_id == PADDLEOCR_ENGINE_ID
    assert status.status == ENGINE_STATUS_NOT_CONFIGURED
    assert "manifest" in status.last_error
    assert "静默下载" in status.install_guide_url_or_text


def test_valid_manifest_with_smoke_ok_returns_available(tmp_path: Path) -> None:
    python = tmp_path / "venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    manifest_path = tmp_path / "runtime_manifest.json"
    manifest_path.write_text(json.dumps(_manifest(str(python), smoke_status="ok"), ensure_ascii=False), encoding="utf-8")

    status = detect_paddleocr_runtime_status(tmp_path)
    manifest = load_paddleocr_runtime_manifest(tmp_path)

    assert status.status == ENGINE_STATUS_AVAILABLE
    assert status.detected_version == "3.0.0"
    assert status.smoke_test_result == "status=ok"
    assert manifest.engine_version == "3.0.0"


def test_valid_manifest_without_smoke_ok_returns_configured_unverified(tmp_path: Path) -> None:
    python = tmp_path / "venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / "runtime_manifest.json").write_text(json.dumps(_manifest(str(python), smoke_status="unknown")), encoding="utf-8")

    status = detect_paddleocr_runtime_status(tmp_path)

    assert status.status == ENGINE_STATUS_CONFIGURED_UNVERIFIED
    assert "smoke test" in status.last_error


def test_invalid_manifest_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "runtime_manifest.json").write_text(json.dumps({"schema_version": "bad"}), encoding="utf-8")

    status = detect_paddleocr_runtime_status(tmp_path)

    assert status.status == ENGINE_STATUS_FAILED
    assert "manifest 无效" in status.last_error


def test_bridge_persists_runtime_root_and_status(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    store = LocalEngineConfigStore(PADDLEOCR_ENGINE_ID, tmp_path / "paddleocr.json")
    bridge = PaddleOCRBridge(store)

    configured = bridge.configure_runtime_root(runtime)
    status = bridge.check_status()

    assert configured.last_status is not None
    assert configured.last_status.status == ENGINE_STATUS_CONFIGURED_UNVERIFIED
    assert status.status == ENGINE_STATUS_NOT_CONFIGURED
    assert bridge.load_config().configured_path_or_endpoint == str(runtime)


def test_default_runtime_roots_are_platform_specific(tmp_path: Path) -> None:
    assert default_paddleocr_runtime_root(platform_name="darwin", home=tmp_path).as_posix().endswith(
        "Library/Application Support/BioMedPilot/engines/ocr/paddleocr"
    )
    assert "BioMedPilot" in str(default_paddleocr_runtime_root(platform_name="win32", home=tmp_path, env={}))
    assert default_paddleocr_runtime_root(platform_name="linux", home=tmp_path).as_posix().endswith(
        ".local/share/BioMedPilot/engines/ocr/paddleocr"
    )


def test_detector_does_not_open_network_socket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked_socket(*args, **kwargs):  # pragma: no cover - should never be called
        raise AssertionError("network socket should not be opened")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    status = detect_paddleocr_runtime_status(tmp_path / "missing_runtime")

    assert status.status == ENGINE_STATUS_NOT_CONFIGURED
    assert "用户触发" in paddleocr_install_guide_text()


def test_worker_command_contract_is_shell_safe_and_mode_checked(tmp_path: Path) -> None:
    command = build_paddleocr_worker_command(
        tmp_path / "venv with space" / "python",
        input_path=tmp_path / "文献.pdf",
        mode=PADDLEOCR_WORKER_MODE_PDF,
        record_id="rec-1",
        attachment_id="att-1",
        lang="ch",
    )

    assert command[:3] == [str(tmp_path / "venv with space" / "python"), "-m", PADDLEOCR_WORKER_MODULE]
    assert "--mode" in command
    assert PADDLEOCR_WORKER_MODE_IMAGE in {"image", PADDLEOCR_WORKER_MODE_IMAGE}
    assert str(tmp_path / "文献.pdf") in command
    assert "att-1" in command

    with pytest.raises(ValueError, match="unsupported"):
        build_paddleocr_worker_command("python", input_path="x", mode="audio", record_id="rec-1")


def _manifest(python_executable: str, *, smoke_status: str) -> dict[str, object]:
    return {
        "schema_version": PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION,
        "engine_id": PADDLEOCR_ENGINE_ID,
        "runtime_id": "runtime-test",
        "platform": "macos",
        "python": {"executable": python_executable, "version": "3.12.0"},
        "packages": {"paddleocr": "3.0.0", "paddlex": "3.5.0"},
        "models": [{"name": "PP-OCRv5", "language": "ch", "path": "models/ch", "sha256": "abc"}],
        "smoke_test": {"status": smoke_status, "result_path": "smoke/result.json"},
    }
