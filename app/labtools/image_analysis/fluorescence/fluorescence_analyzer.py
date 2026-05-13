from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.labtools.image_analysis.audit_models import ImageAnalysisAuditRecord
from app.labtools.image_analysis.image_io import validate_image_path
from app.labtools.image_analysis.image_models import ImageAnalysisError
from app.labtools.image_analysis.fluorescence.fluorescence_models import (
    FluorescenceAnalysisMetrics,
    FluorescenceAnalysisParameters,
    FluorescenceAnalysisResult,
    FluorescenceROI,
)
from app.labtools.image_analysis.fluorescence.fluorescence_quality import evaluate_fluorescence_quality


ALGORITHM_NAME = "manual_roi_grayscale_fluorescence_v1"
ALGORITHM_VERSION = "L4B.1-review-export"


def validate_roi_bounds(roi: FluorescenceROI, image_width: int, image_height: int) -> None:
    if roi.x + roi.width > image_width or roi.y + roi.height > image_height:
        raise ImageAnalysisError(
            f"{roi.label} 超出图片边界。图片尺寸为 {image_width} x {image_height} px，请重新设置 ROI。"
        )


def _roi_pixels(image: Image.Image, roi: FluorescenceROI) -> list[float]:
    crop = image.crop((roi.x, roi.y, roi.x + roi.width, roi.y + roi.height))
    if hasattr(crop, "get_flattened_data"):
        data = crop.get_flattened_data()
    else:  # pragma: no cover - compatibility for older Pillow versions.
        data = crop.getdata()
    return [float(value) for value in data]


def _mean(values: list[float], label: str) -> float:
    if not values:
        raise ImageAnalysisError(f"{label} ROI 没有可计算像素。")
    return sum(values) / len(values)


def analyze_fluorescence_roi(parameters: FluorescenceAnalysisParameters, *, task_id: str | None = None) -> FluorescenceAnalysisResult:
    path = validate_image_path(parameters.image_path)
    try:
        with Image.open(path) as source_image:
            image = source_image.convert("L")
            image_width, image_height = image.size
            validate_roi_bounds(parameters.signal_roi, image_width, image_height)
            validate_roi_bounds(parameters.background_roi, image_width, image_height)
            signal_values = _roi_pixels(image, parameters.signal_roi)
            background_values = _roi_pixels(image, parameters.background_roi)
    except ImageAnalysisError:
        raise
    except (OSError, UnidentifiedImageError) as exc:
        raise ImageAnalysisError("图片无法读取，请确认文件完整且格式受支持。") from exc

    signal_sum = float(sum(signal_values))
    signal_area = parameters.signal_roi.area_pixels
    signal_mean = _mean(signal_values, "signal")
    background_mean = _mean(background_values, "background")
    if parameters.background_correction_enabled:
        corrected_total = signal_sum - signal_area * background_mean
    else:
        corrected_total = signal_sum
    metrics = FluorescenceAnalysisMetrics(
        roi_area_pixels=signal_area,
        mean_intensity=signal_mean,
        integrated_density=signal_sum,
        background_mean_intensity=background_mean,
        corrected_total_fluorescence=corrected_total,
        min_intensity=float(min(signal_values)),
        max_intensity=float(max(signal_values)),
    )
    result = FluorescenceAnalysisResult(
        task_id=task_id or f"fluorescence_task_{uuid4().hex[:12]}",
        parameters=parameters,
        metrics=metrics,
        image_width=image_width,
        image_height=image_height,
    )
    return replace(result, warnings=evaluate_fluorescence_quality(result))


def create_fluorescence_audit_records(
    result: FluorescenceAnalysisResult,
    *,
    source_path: str | Path,
) -> tuple[ImageAnalysisAuditRecord, ...]:
    return (
        ImageAnalysisAuditRecord(
            event_type="fluorescence_analysis_completed",
            message="已完成手动 ROI 荧光强度分析。",
            details={
                "algorithm_name": ALGORITHM_NAME,
                "algorithm_version": ALGORITHM_VERSION,
                "source_path": str(source_path),
                "source_filename": Path(source_path).name,
                "image_dimensions": result.image_dimensions_dict(),
                "result_id": result.result_id,
                "task_id": result.task_id,
                "manual_roi_required": True,
                "background_correction_enabled": result.parameters.background_correction_enabled,
                "formula": result.formula,
                "warnings": list(result.warnings),
                "review_notice": result.review_notice,
            },
        ),
    )
