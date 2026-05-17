from app.shared.local_engines.engine_config import LocalEngineConfig, LocalEngineConfigStore, local_engine_config_from_dict
from app.shared.local_engines.engine_status import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_CONFIGURED_UNVERIFIED,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    ENGINE_STATUS_UNSUPPORTED_VERSION,
    EngineStatus,
    engine_status_from_dict,
)
from app.shared.local_engines.imagej_fiji_bridge import ImageJFijiBridge
from app.shared.local_engines.imagej_fiji_detector import (
    IMAGEJ_FIJI_ENGINE_ID,
    default_imagej_fiji_status,
    detect_common_imagej_fiji_paths,
    detect_imagej_fiji_status,
    parse_imagej_fiji_version_output,
    resolve_imagej_fiji_executable,
)
from app.shared.local_engines.install_guides import imagej_fiji_install_guide_text, imagej_fiji_setup_prompt_text, paddleocr_install_guide_text
from app.shared.local_engines.paddleocr_bridge import PaddleOCRBridge
from app.shared.local_engines.paddleocr_detector import (
    PADDLEOCR_ENGINE_NAME,
    PADDLEOCR_ENGINE_TYPE,
    PADDLEOCR_RECOMMENDED_VERSION,
    default_paddleocr_status,
    detect_paddleocr_runtime_status,
)
from app.shared.local_engines.paddleocr_runtime import (
    PADDLEOCR_ENGINE_ID,
    PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION,
    PaddleOCRModelAsset,
    PaddleOCRRuntimeManifest,
    default_paddleocr_runtime_root,
    load_paddleocr_runtime_manifest,
    paddleocr_runtime_manifest_from_dict,
    paddleocr_runtime_manifest_path,
)
from app.shared.local_engines.paddleocr_worker_contract import (
    PADDLEOCR_WORKER_MODE_IMAGE,
    PADDLEOCR_WORKER_MODE_PDF,
    PADDLEOCR_WORKER_MODES,
    PADDLEOCR_WORKER_MODULE,
    build_paddleocr_worker_command,
)

__all__ = [
    "ENGINE_STATUS_AVAILABLE",
    "ENGINE_STATUS_CONFIGURED_UNVERIFIED",
    "ENGINE_STATUS_FAILED",
    "ENGINE_STATUS_NOT_CONFIGURED",
    "ENGINE_STATUS_UNSUPPORTED_VERSION",
    "IMAGEJ_FIJI_ENGINE_ID",
    "PADDLEOCR_ENGINE_ID",
    "PADDLEOCR_ENGINE_NAME",
    "PADDLEOCR_ENGINE_TYPE",
    "PADDLEOCR_RECOMMENDED_VERSION",
    "PADDLEOCR_RUNTIME_MANIFEST_SCHEMA_VERSION",
    "PADDLEOCR_WORKER_MODE_IMAGE",
    "PADDLEOCR_WORKER_MODE_PDF",
    "PADDLEOCR_WORKER_MODES",
    "PADDLEOCR_WORKER_MODULE",
    "EngineStatus",
    "ImageJFijiBridge",
    "LocalEngineConfig",
    "LocalEngineConfigStore",
    "PaddleOCRBridge",
    "PaddleOCRModelAsset",
    "PaddleOCRRuntimeManifest",
    "build_paddleocr_worker_command",
    "default_imagej_fiji_status",
    "default_paddleocr_runtime_root",
    "default_paddleocr_status",
    "detect_common_imagej_fiji_paths",
    "detect_imagej_fiji_status",
    "detect_paddleocr_runtime_status",
    "engine_status_from_dict",
    "imagej_fiji_install_guide_text",
    "imagej_fiji_setup_prompt_text",
    "load_paddleocr_runtime_manifest",
    "local_engine_config_from_dict",
    "paddleocr_install_guide_text",
    "paddleocr_runtime_manifest_from_dict",
    "paddleocr_runtime_manifest_path",
    "parse_imagej_fiji_version_output",
    "resolve_imagej_fiji_executable",
]
