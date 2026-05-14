from __future__ import annotations

import subprocess
from pathlib import Path

from app.shared.local_engines import (
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ImageJFijiBridge,
    EngineStatus,
    default_imagej_fiji_status,
    imagej_fiji_setup_prompt_text,
)


LABTOOLS_IMAGEJ_FIJI_WORKFLOW_NAME = "LabTools 图像定量 workflow"
LABTOOLS_IMAGE_ANALYSIS_BOUNDARY = (
    "LabTools 不内置 WB/gel 真实分析、agarose gel、自动 ROI、细胞计数、条带识别、"
    "pathology workflow 或生产级图像算法；ImageJ/Fiji 仅作为用户显式配置和检测的本机外部引擎。"
)


def labtools_imagej_fiji_prompt() -> str:
    return imagej_fiji_setup_prompt_text(workflow_name=LABTOOLS_IMAGEJ_FIJI_WORKFLOW_NAME)


def load_labtools_imagej_fiji_status(bridge: ImageJFijiBridge | None = None) -> EngineStatus:
    target = bridge or ImageJFijiBridge()
    config = target.load_config()
    if config.last_status is not None:
        return config.last_status
    if config.configured_path_or_endpoint:
        return default_imagej_fiji_status(
            ENGINE_STATUS_CONFIGURED_UNVERIFIED,
            configured_path=config.configured_path_or_endpoint,
            last_error="已配置路径，尚未验证。",
        )
    return default_imagej_fiji_status()


def configure_labtools_imagej_fiji_path(path: str | Path, bridge: ImageJFijiBridge | None = None) -> EngineStatus:
    target = bridge or ImageJFijiBridge()
    config = target.configure_path(path)
    return config.last_status or load_labtools_imagej_fiji_status(target)


def check_labtools_imagej_fiji_status(
    bridge: ImageJFijiBridge | None = None,
    *,
    persist: bool = True,
    runner=subprocess.run,
) -> EngineStatus:
    target = bridge or ImageJFijiBridge()
    return target.check_status(persist=persist, runner=runner)


def clear_labtools_imagej_fiji_path(bridge: ImageJFijiBridge | None = None) -> EngineStatus:
    target = bridge or ImageJFijiBridge()
    target.clear()
    return load_labtools_imagej_fiji_status(target)
