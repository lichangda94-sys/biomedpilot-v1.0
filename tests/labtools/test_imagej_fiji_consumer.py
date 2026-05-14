from __future__ import annotations

import subprocess
from pathlib import Path

from app.labtools.image_analysis import IMAGE_REVIEW_NOTICE
from app.labtools.image_analysis.local_engine_consumer import (
    LABTOOLS_IMAGE_ANALYSIS_BOUNDARY,
    check_labtools_imagej_fiji_status,
    configure_labtools_imagej_fiji_path,
    labtools_imagej_fiji_prompt,
    load_labtools_imagej_fiji_status,
)
from app.labtools.workspace import labtools_features
from app.shared.local_engines import ENGINE_STATUS_AVAILABLE, ENGINE_STATUS_CONFIGURED_UNVERIFIED, IMAGEJ_FIJI_ENGINE_ID, ImageJFijiBridge, LocalEngineConfigStore


def _fake_executable(tmp_path: Path) -> Path:
    path = tmp_path / "fake_imagej"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _successful_runner(command, **kwargs):
    if "--version" in command:
        return subprocess.CompletedProcess(command, 0, stdout="ImageJ 1.54f\n", stderr="")
    output_path = Path(command[-1])
    output_path.write_text("status=ok\n", encoding="utf-8")
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def test_labtools_imagej_fiji_consumer_configures_and_checks_shared_bridge(tmp_path) -> None:
    bridge = ImageJFijiBridge(LocalEngineConfigStore(IMAGEJ_FIJI_ENGINE_ID, tmp_path / "imagej_fiji.json"))
    executable = _fake_executable(tmp_path)

    configured = configure_labtools_imagej_fiji_path(executable, bridge)
    loaded = load_labtools_imagej_fiji_status(bridge)
    checked = check_labtools_imagej_fiji_status(bridge, runner=_successful_runner)

    assert configured.status == ENGINE_STATUS_CONFIGURED_UNVERIFIED
    assert loaded.configured_path_or_endpoint == str(executable)
    assert checked.status == ENGINE_STATUS_AVAILABLE
    assert checked.detected_version == "1.54f"


def test_labtools_imagej_fiji_consumer_text_keeps_algorithm_boundary() -> None:
    prompt = labtools_imagej_fiji_prompt()
    feature = labtools_features()[0]

    assert "LabTools 图像定量 workflow" in prompt
    assert "ImageJ/Fiji" in prompt
    assert "不内置 WB/gel 真实分析、agarose gel、自动 ROI、细胞计数、条带识别" in LABTOOLS_IMAGE_ANALYSIS_BOUNDARY
    assert "生产级真实图像算法" in IMAGE_REVIEW_NOTICE
    assert "消费 shared ImageJ/Fiji 本机引擎检测" in feature.description


def test_labtools_package_does_not_export_forbidden_image_algorithms() -> None:
    import app.labtools as labtools

    exported = set(labtools.__all__)

    assert "LabToolsWorkspaceWidget" in exported
    assert "labtools_features" in exported
    assert not {"cell_counting", "automatic_roi", "pathology_workflow"} & exported
