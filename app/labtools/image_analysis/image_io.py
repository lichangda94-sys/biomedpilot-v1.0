from __future__ import annotations

from pathlib import Path

from app.labtools.image_analysis.image_models import (
    SUPPORTED_IMAGE_EXTENSIONS,
    ImageAnalysisError,
    LabImageRecord,
)


LARGE_IMAGE_WARNING_BYTES = 50 * 1024 * 1024


def validate_image_path(source_path: object) -> Path:
    if source_path is None or str(source_path).strip() == "":
        raise ImageAnalysisError("请先选择或填写本地图片路径。")
    path = Path(str(source_path).strip()).expanduser()
    if not path.exists():
        raise ImageAnalysisError("图片路径不存在，请检查后重新选择。")
    if not path.is_file():
        raise ImageAnalysisError("请选择具体图片文件，不要选择文件夹。")
    extension = path.suffix.lower()
    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        supported = "、".join(SUPPORTED_IMAGE_EXTENSIONS)
        raise ImageAnalysisError(f"暂不支持该图片格式：{extension or '无扩展名'}。支持格式：{supported}。")
    return path


def create_image_record(source_path: object, *, image_role: str = "primary_image", notes: str = "") -> LabImageRecord:
    path = validate_image_path(source_path)
    size = path.stat().st_size
    warnings: list[str] = []
    status = "valid"
    if size == 0:
        warnings.append("图片文件大小为 0，请确认文件是否完整。")
        status = "valid_with_warnings"
    if size > LARGE_IMAGE_WARNING_BYTES:
        warnings.append("图片文件较大，本阶段仅记录路径和文件信息，不复制文件。")
        status = "valid_with_warnings"
    return LabImageRecord.from_path(path, image_role=image_role, notes=notes, warnings=tuple(warnings), validation_status=status)
