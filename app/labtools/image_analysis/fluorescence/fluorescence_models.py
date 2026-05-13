from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.image_models import ImageAnalysisError, utc_timestamp


FLUORESCENCE_REVIEW_NOTICE = "请人工复核 ROI、背景区域和图像曝光条件后再用于实验结论。"
FLUORESCENCE_FORMULA = "CTF = Integrated Density - ROI Area x Background Mean"
VALID_ROI_TYPES = {"signal", "background"}


@dataclass(frozen=True)
class FluorescenceROI:
    label: str
    x: int
    y: int
    width: int
    height: int
    roi_type: str
    notes: str = ""
    roi_id: str = field(default_factory=lambda: f"fluorescence_roi_{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if self.roi_type not in VALID_ROI_TYPES:
            raise ImageAnalysisError("ROI 类型必须是 signal 或 background。")
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
            "roi_type": self.roi_type,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class FluorescenceAnalysisParameters:
    image_path: str
    signal_roi: FluorescenceROI
    background_roi: FluorescenceROI
    channel_mode: str = "grayscale"
    background_correction_enabled: bool = True
    created_at: str = field(default_factory=utc_timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "signal_roi": self.signal_roi.to_dict(),
            "background_roi": self.background_roi.to_dict(),
            "channel_mode": self.channel_mode,
            "background_correction_enabled": self.background_correction_enabled,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class FluorescenceAnalysisMetrics:
    roi_area_pixels: int
    mean_intensity: float
    integrated_density: float
    background_mean_intensity: float
    corrected_total_fluorescence: float
    min_intensity: float
    max_intensity: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "roi_area_pixels": self.roi_area_pixels,
            "mean_intensity": self.mean_intensity,
            "integrated_density": self.integrated_density,
            "background_mean_intensity": self.background_mean_intensity,
            "corrected_total_fluorescence": self.corrected_total_fluorescence,
            "min_intensity": self.min_intensity,
            "max_intensity": self.max_intensity,
        }


@dataclass(frozen=True)
class FluorescenceAnalysisResult:
    task_id: str
    parameters: FluorescenceAnalysisParameters
    metrics: FluorescenceAnalysisMetrics
    image_width: int | None = None
    image_height: int | None = None
    status: str = "completed"
    formula: str = FLUORESCENCE_FORMULA
    warnings: tuple[str, ...] = ()
    review_notice: str = FLUORESCENCE_REVIEW_NOTICE
    generated_at: str = field(default_factory=utc_timestamp)
    result_id: str = field(default_factory=lambda: f"fluorescence_result_{uuid4().hex[:12]}")

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
            "signal_roi": self.parameters.signal_roi.to_dict(),
            "background_roi": self.parameters.background_roi.to_dict(),
            "parameters": self.parameters.to_dict(),
            "metrics": self.metrics.to_dict(),
            "formula": self.formula,
            "warnings": list(self.warnings),
            "review_notice": self.review_notice,
            "generated_at": self.generated_at,
        }
