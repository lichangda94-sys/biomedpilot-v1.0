from __future__ import annotations

from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    IMAGEJ_FIJI_ENGINE_ID,
    EngineStatus,
    ImageJFijiBridge,
    default_imagej_fiji_status,
    imagej_fiji_setup_prompt_text,
)


def is_meaningful_imagej_fiji_path(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip()
    if not normalized:
        return False
    return normalized not in {"0", "1", "true", "false", "None", "null", "-"}


def imagej_fiji_display_path(value: str | None) -> str:
    if is_meaningful_imagej_fiji_path(value):
        return value.strip()
    return "未配置 / 路径无效"


def read_shared_imagej_fiji_status(bridge: ImageJFijiBridge | None = None) -> EngineStatus:
    """Read ImageJ state, with optional Fiji support, from the shared local-engine config layer."""

    engine_bridge = bridge or ImageJFijiBridge()
    try:
        config = engine_bridge.load_config()
    except ValueError as exc:
        return default_imagej_fiji_status(ENGINE_STATUS_FAILED, last_error=str(exc))
    if config.last_status is not None:
        return config.last_status
    if is_meaningful_imagej_fiji_path(config.configured_path_or_endpoint):
        return default_imagej_fiji_status(
            ENGINE_STATUS_CONFIGURED_UNVERIFIED,
            configured_path=config.configured_path_or_endpoint,
            last_error="已配置路径，尚未验证。",
        )
    return default_imagej_fiji_status(
        ENGINE_STATUS_NOT_CONFIGURED,
        last_error="尚未配置 ImageJ。本地手动 ROI MVP 可继续使用；需要 macro 执行时请配置 ImageJ.app、ij.jar、可执行入口或增强 Fiji 路径。",
    )


def imagej_fiji_status_label(status: str) -> str:
    return {
        ENGINE_STATUS_NOT_CONFIGURED: "未配置",
        ENGINE_STATUS_CONFIGURED_UNVERIFIED: "已配置，尚未验证",
        ENGINE_STATUS_AVAILABLE: "可用",
        ENGINE_STATUS_FAILED: "验证失败",
    }.get(status, "验证失败")


def imagej_fiji_context_prompt(*, workflow_name: str, can_continue_without_engine: bool = True) -> str:
    return imagej_fiji_setup_prompt_text(
        workflow_name=workflow_name,
        can_continue_without_engine=can_continue_without_engine,
    )


__all__ = [
    "ENGINE_STATUS_AVAILABLE",
    "ENGINE_STATUS_CONFIGURED_UNVERIFIED",
    "ENGINE_STATUS_FAILED",
    "ENGINE_STATUS_NOT_CONFIGURED",
    "IMAGEJ_FIJI_ENGINE_ID",
    "EngineStatus",
    "ImageJFijiBridge",
    "imagej_fiji_display_path",
    "imagej_fiji_context_prompt",
    "imagej_fiji_status_label",
    "is_meaningful_imagej_fiji_path",
    "read_shared_imagej_fiji_status",
]
