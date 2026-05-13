from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


IMAGE_REVIEW_NOTICE = (
    "当前图像分析仅支持手动 ROI 荧光 grayscale 指标和手动 ROI + 阈值划痕面积估算；"
    "未启用自动 ROI、细胞计数或灰度/墨值算法。所有结果都需要人工复核，"
    "请勿将占位状态作为实验结果。"
)

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif")


class ImageAnalysisError(ValueError):
    """User-facing image analysis framework error."""


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class LabImageRecord:
    source_path: str
    filename: str
    file_extension: str
    file_size_bytes: int
    image_role: str = "primary_image"
    notes: str = ""
    validation_status: str = "valid"
    warnings: tuple[str, ...] = ()
    imported_at: str = field(default_factory=utc_timestamp)
    image_id: str = field(default_factory=lambda: f"lab_image_{uuid4().hex[:12]}")

    @classmethod
    def from_path(
        cls,
        source_path: str | Path,
        *,
        image_role: str = "primary_image",
        notes: str = "",
        warnings: tuple[str, ...] = (),
        validation_status: str = "valid",
    ) -> "LabImageRecord":
        path = Path(source_path).expanduser()
        return cls(
            source_path=str(path),
            filename=path.name,
            file_extension=path.suffix.lower(),
            file_size_bytes=path.stat().st_size,
            image_role=image_role,
            notes=notes,
            validation_status=validation_status,
            warnings=warnings,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "source_path": self.source_path,
            "filename": self.filename,
            "file_extension": self.file_extension,
            "file_size_bytes": self.file_size_bytes,
            "imported_at": self.imported_at,
            "image_role": self.image_role,
            "notes": self.notes,
            "validation_status": self.validation_status,
            "warnings": list(self.warnings),
        }
