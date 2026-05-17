from __future__ import annotations

from pathlib import Path

from app.shared.local_engines.engine_status import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    EngineStatus,
    UNKNOWN_VERSION,
    utc_now,
)
from app.shared.local_engines.install_guides import paddleocr_install_guide_text
from app.shared.local_engines.paddleocr_runtime import (
    PADDLEOCR_ENGINE_ID,
    default_paddleocr_runtime_root,
    load_paddleocr_runtime_manifest,
    paddleocr_runtime_manifest_path,
)


PADDLEOCR_ENGINE_NAME = "PaddleOCR 本地 OCR 引擎"
PADDLEOCR_ENGINE_TYPE = "local_ocr_backend"
PADDLEOCR_RECOMMENDED_VERSION = "PaddleOCR runtime pinned by BioMedPilot manifest"


def default_paddleocr_status(status: str = ENGINE_STATUS_NOT_CONFIGURED, *, configured_path: str = "", last_error: str = "") -> EngineStatus:
    return EngineStatus(
        engine_id=PADDLEOCR_ENGINE_ID,
        engine_name=PADDLEOCR_ENGINE_NAME,
        engine_type=PADDLEOCR_ENGINE_TYPE,
        configured_path_or_endpoint=configured_path,
        recommended_version=PADDLEOCR_RECOMMENDED_VERSION,
        status=status,
        last_error=last_error,
        install_guide_url_or_text=paddleocr_install_guide_text(),
    )


def detect_paddleocr_runtime_status(runtime_root: str | Path | None = None) -> EngineStatus:
    root = Path(runtime_root).expanduser() if runtime_root is not None else default_paddleocr_runtime_root()
    manifest_path = paddleocr_runtime_manifest_path(root)
    if not manifest_path.exists():
        return default_paddleocr_status(
            ENGINE_STATUS_NOT_CONFIGURED,
            configured_path=str(root),
            last_error="未找到 PaddleOCR runtime manifest。请在需要 PDF / 图片 OCR 时由用户触发安装或选择 runtime。",
        )
    try:
        manifest = load_paddleocr_runtime_manifest(root)
    except ValueError as exc:
        return _failed_status(root, f"PaddleOCR runtime manifest 无效：{exc}")
    python_path = Path(manifest.python_executable).expanduser()
    if not python_path.exists() or not python_path.is_file():
        return _failed_status(root, "PaddleOCR runtime Python 不存在。")
    if manifest.smoke_test_status == "ok":
        return EngineStatus(
            engine_id=PADDLEOCR_ENGINE_ID,
            engine_name=PADDLEOCR_ENGINE_NAME,
            engine_type=PADDLEOCR_ENGINE_TYPE,
            configured_path_or_endpoint=str(root),
            detected_version=manifest.engine_version or UNKNOWN_VERSION,
            recommended_version=PADDLEOCR_RECOMMENDED_VERSION,
            status=ENGINE_STATUS_AVAILABLE,
            last_check_at=utc_now(),
            last_error="",
            smoke_test_result="status=ok",
            install_guide_url_or_text=paddleocr_install_guide_text(),
        )
    return EngineStatus(
        engine_id=PADDLEOCR_ENGINE_ID,
        engine_name=PADDLEOCR_ENGINE_NAME,
        engine_type=PADDLEOCR_ENGINE_TYPE,
        configured_path_or_endpoint=str(root),
        detected_version=manifest.engine_version or UNKNOWN_VERSION,
        recommended_version=PADDLEOCR_RECOMMENDED_VERSION,
        status=ENGINE_STATUS_CONFIGURED_UNVERIFIED,
        last_check_at=utc_now(),
        last_error="PaddleOCR runtime manifest 已存在，但 smoke test 尚未通过。",
        smoke_test_result=f"status={manifest.smoke_test_status}",
        install_guide_url_or_text=paddleocr_install_guide_text(),
    )


def _failed_status(runtime_root: Path, error_message: str) -> EngineStatus:
    return EngineStatus(
        engine_id=PADDLEOCR_ENGINE_ID,
        engine_name=PADDLEOCR_ENGINE_NAME,
        engine_type=PADDLEOCR_ENGINE_TYPE,
        configured_path_or_endpoint=str(runtime_root),
        recommended_version=PADDLEOCR_RECOMMENDED_VERSION,
        status=ENGINE_STATUS_FAILED,
        last_check_at=utc_now(),
        last_error=error_message,
        install_guide_url_or_text=paddleocr_install_guide_text(),
    )
