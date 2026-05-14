from __future__ import annotations

from dataclasses import replace

from app.labtools.imagej_bridge import imagej_fiji_context_prompt, imagej_fiji_status_label, read_shared_imagej_fiji_status
from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    IMAGEJ_FIJI_ENGINE_ID,
    ImageJFijiBridge,
    LocalEngineConfig,
    LocalEngineConfigStore,
    default_imagej_fiji_status,
)


def _bridge(tmp_path) -> ImageJFijiBridge:
    return ImageJFijiBridge(LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json"))


def test_labtools_reads_not_configured_status_from_shared_layer(tmp_path) -> None:
    status = read_shared_imagej_fiji_status(_bridge(tmp_path))

    assert status.engine_id == IMAGEJ_FIJI_ENGINE_ID
    assert status.status == ENGINE_STATUS_NOT_CONFIGURED
    assert "尚未配置" in status.last_error


def test_labtools_reads_available_status_from_shared_last_status(tmp_path) -> None:
    bridge = _bridge(tmp_path)
    available = default_imagej_fiji_status(ENGINE_STATUS_AVAILABLE, configured_path="/Applications/Fiji.app")
    bridge._store.save(  # noqa: SLF001 - focused test for shared store consumption
        LocalEngineConfig(
            engine_id=IMAGEJ_FIJI_ENGINE_ID,
            configured_path_or_endpoint="/Applications/Fiji.app",
            last_status=replace(available, detected_version="2.14.0", smoke_test_result="status=ok"),
        )
    )

    status = read_shared_imagej_fiji_status(bridge)

    assert status.status == ENGINE_STATUS_AVAILABLE
    assert status.detected_version == "2.14.0"
    assert status.smoke_test_result == "status=ok"


def test_labtools_reads_failed_status_safely(tmp_path) -> None:
    bridge = _bridge(tmp_path)
    failed = default_imagej_fiji_status(
        ENGINE_STATUS_FAILED,
        configured_path="/bad/path",
        last_error="Fiji/ImageJ 路径无效或不可执行",
    )
    bridge._store.save(  # noqa: SLF001
        LocalEngineConfig(
            engine_id=IMAGEJ_FIJI_ENGINE_ID,
            configured_path_or_endpoint="/bad/path",
            last_status=failed,
        )
    )

    status = read_shared_imagej_fiji_status(bridge)

    assert status.status == ENGINE_STATUS_FAILED
    assert "路径无效" in status.last_error
    assert "Traceback" not in status.last_error


def test_labtools_reports_configured_unverified_when_shared_config_has_path_without_status(tmp_path) -> None:
    bridge = _bridge(tmp_path)
    bridge._store.save(  # noqa: SLF001
        LocalEngineConfig(
            engine_id=IMAGEJ_FIJI_ENGINE_ID,
            configured_path_or_endpoint="/Applications/Fiji.app",
            last_status=None,
        )
    )

    status = read_shared_imagej_fiji_status(bridge)

    assert status.status == ENGINE_STATUS_CONFIGURED_UNVERIFIED
    assert status.configured_path_or_endpoint == "/Applications/Fiji.app"


def test_labtools_status_labels_and_prompt_are_contextual() -> None:
    assert imagej_fiji_status_label(ENGINE_STATUS_NOT_CONFIGURED) == "未配置"
    assert imagej_fiji_status_label(ENGINE_STATUS_AVAILABLE) == "可用"
    assert imagej_fiji_status_label(ENGINE_STATUS_FAILED) == "验证失败"

    prompt = imagej_fiji_context_prompt(workflow_name="Western Blot 灰度分析 workflow", can_continue_without_engine=False)

    assert "需要本机 ImageJ/Fiji" in prompt
    assert "自动检测" in prompt
    assert "选择本机路径" in prompt
