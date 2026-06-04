from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path

import pytest

from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    IMAGEJ_FIJI_ENGINE_ID,
    ImageJFijiBridge,
    LocalEngineConfigStore,
    detect_imagej_fiji_status,
    engine_status_from_dict,
    imagej_fiji_install_guide_text,
    imagej_fiji_setup_prompt_text,
    parse_imagej_fiji_version_output,
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


def test_missing_path_returns_not_configured_when_no_common_path(tmp_path, monkeypatch) -> None:
    import app.shared.local_engines.imagej_fiji_detector as detector

    monkeypatch.setattr(detector, "default_imagej_fiji_runtime_root", lambda: tmp_path / "missing_runtime")
    monkeypatch.setattr(detector, "detect_common_imagej_fiji_paths", lambda: ())

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


def test_bridge_runs_macro_after_detection(tmp_path) -> None:
    store = LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json")
    bridge = ImageJFijiBridge(store)
    executable = _fake_executable(tmp_path)
    macro_path = tmp_path / "draft.ijm"
    output_path = tmp_path / "macro_result.txt"
    macro_path.write_text('File.saveString("status=macro_ready\\n", getArgument());\n', encoding="utf-8")

    bridge.configure_path(executable)
    result = bridge.run_macro(macro_path=macro_path, argument=output_path, runner=_successful_runner)

    assert result.succeeded
    assert result.returncode == 0
    assert result.executable_path == str(executable)
    assert result.macro_path == str(macro_path)
    assert output_path.read_text(encoding="utf-8") == "status=ok\n"


def test_bridge_refuses_macro_when_engine_is_unavailable(tmp_path) -> None:
    bridge = ImageJFijiBridge(LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json"))
    bridge.configure_path(tmp_path / "missing_imagej")
    macro_path = tmp_path / "draft.ijm"
    macro_path.write_text('print("draft");\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="imagej_fiji_engine_not_available"):
        bridge.run_macro(macro_path=macro_path, runner=_successful_runner)


def test_version_parser_and_prompt_text_are_user_readable() -> None:
    assert parse_imagej_fiji_version_output("ImageJ 1.54f") == "1.54f"
    assert "本机" in imagej_fiji_install_guide_text()
    assert "自动检测" in imagej_fiji_setup_prompt_text(workflow_name="LabTools 图像定量")


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
