from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.image_models import ImageAnalysisError, utc_timestamp


WOUND_REVIEW_NOTICE = "该结果为基于用户 ROI 和阈值的划痕区域估算，请人工复核阈值、ROI 和原图质量后再用于实验结论。"
WOUND_FORMULA = (
    "scratch_area_fraction = scratch_area_pixels / ROI area; "
    "non_scratch_area_fraction = 1 - scratch_area_fraction"
)
VALID_SCRATCH_MODES = {"bright", "dark"}


@dataclass(frozen=True)
class WoundHealingROI:
    label: str
    x: int
    y: int
    width: int
    height: int
    notes: str = ""
    roi_id: str = field(default_factory=lambda: f"wound_roi_{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ImageAnalysisError("请填写 ROI 标签。")
        for field_name, value in (("x", self.x), ("y", self.y), ("width", self.width), ("height", self.height)):
            if not isinstance(value, int):
                raise ImageAnalysisError(f"ROI {field_name} 必须是整数。")
        if self.x < 0 or self.y < 0:
            raise ImageAnalysisError("ROI 坐标不能为负数。")
        if self.width <= 0 or self.height <= 0:
            raise ImageAnalysisError("ROI 宽度和高度必须大于 0。")

    @property
    def area_pixels(self) -> int:
        return self.width * self.height

    def to_dict(self) -> dict[str, Any]:
        return {
            "roi_id": self.roi_id,
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class WoundHealingParameters:
    image_path: str
    roi: WoundHealingROI
    threshold: int
    scratch_mode: str
    channel_mode: str = "grayscale"
    created_at: str = field(default_factory=utc_timestamp)

    def __post_init__(self) -> None:
        if not isinstance(self.threshold, int):
            raise ImageAnalysisError("阈值必须是 0-255 之间的整数。")
        if self.threshold < 0 or self.threshold > 255:
            raise ImageAnalysisError("阈值必须在 0-255 之间。")
        if self.scratch_mode not in VALID_SCRATCH_MODES:
            raise ImageAnalysisError("划痕模式必须是 bright 或 dark。")

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "roi": self.roi.to_dict(),
            "threshold": self.threshold,
            "scratch_mode": self.scratch_mode,
            "channel_mode": self.channel_mode,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class WoundHealingMetrics:
    roi_area_pixels: int
    scratch_area_pixels: int
    scratch_area_fraction: float
    non_scratch_area_pixels: int
    non_scratch_area_fraction: float
    threshold: int
    scratch_mode: str

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "roi_area_pixels": self.roi_area_pixels,
            "scratch_area_pixels": self.scratch_area_pixels,
            "scratch_area_fraction": self.scratch_area_fraction,
            "non_scratch_area_pixels": self.non_scratch_area_pixels,
            "non_scratch_area_fraction": self.non_scratch_area_fraction,
            "threshold": self.threshold,
            "scratch_mode": self.scratch_mode,
        }


@dataclass(frozen=True)
class WoundHealingResult:
    task_id: str
    parameters: WoundHealingParameters
    metrics: WoundHealingMetrics
    image_width: int | None = None
    image_height: int | None = None
    status: str = "completed"
    formula: str = WOUND_FORMULA
    warnings: tuple[str, ...] = ()
    review_notice: str = WOUND_REVIEW_NOTICE
    generated_at: str = field(default_factory=utc_timestamp)
    result_id: str = field(default_factory=lambda: f"wound_result_{uuid4().hex[:12]}")

    def image_dimensions_dict(self) -> dict[str, int | str | None]:
        return {
            "width": self.image_width,
            "height": self.image_height,
            "unit": "pixels",
        }

    def to_dict(self) -> dict[str, Any]:
        filename = Path(self.parameters.image_path).name or "未命名图片"
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "status": self.status,
            "image_filename": filename,
            "source_path_summary": filename,
            "image_dimensions": self.image_dimensions_dict(),
            "roi": self.parameters.roi.to_dict(),
            "threshold": self.parameters.threshold,
            "scratch_mode": self.parameters.scratch_mode,
            "parameters": self.parameters.to_dict(),
            "metrics": self.metrics.to_dict(),
            "formula": self.formula,
            "warnings": list(self.warnings),
            "review_notice": self.review_notice,
            "generated_at": self.generated_at,
        }
