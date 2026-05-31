from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.labtools.image_analysis.audit_models import ImageAnalysisAuditRecord
from app.labtools.image_analysis.image_io import validate_image_path
from app.labtools.image_analysis.image_models import ImageAnalysisError
from app.labtools.image_analysis.wound_healing.wound_models import (
    WoundHealingMetrics,
    WoundHealingParameters,
    WoundHealingResult,
    WoundHealingROI,
)
from app.labtools.image_analysis.wound_healing.wound_quality import evaluate_wound_healing_quality


ALGORITHM_NAME = "manual_roi_threshold_wound_healing_v1"
ALGORITHM_VERSION = "L4C-MVP"


def validate_wound_roi_bounds(roi: WoundHealingROI, image_width: int, image_height: int) -> None:
    if roi.x + roi.width > image_width or roi.y + roi.height > image_height:
        raise ImageAnalysisError(
            f"{roi.label} 超出图片边界。图片尺寸为 {image_width} x {image_height} px，请重新设置 ROI。"
        )


def _roi_pixels(image: Image.Image, roi: WoundHealingROI) -> list[int]:
    crop = image.crop((roi.x, roi.y, roi.x + roi.width, roi.y + roi.height))
    if hasattr(crop, "get_flattened_data"):
        data = crop.get_flattened_data()
    else:  # pragma: no cover - compatibility for older Pillow versions.
        data = crop.getdata()
    return [int(value) for value in data]


def analyze_wound_healing_area(
    parameters: WoundHealingParameters,
    *,
    task_id: str | None = None,
) -> WoundHealingResult:
    path = validate_image_path(parameters.image_path)
    try:
        with Image.open(path) as source_image:
            image = source_image.convert("L")
            image_width, image_height = image.size
            validate_wound_roi_bounds(parameters.roi, image_width, image_height)
            roi_values = _roi_pixels(image, parameters.roi)
    except ImageAnalysisError:
        raise
    except (OSError, UnidentifiedImageError) as exc:
        raise ImageAnalysisError("图片无法读取，请确认文件完整且格式受支持。") from exc

    roi_area = parameters.roi.area_pixels
    if parameters.scratch_mode == "bright":
        scratch_area = sum(1 for value in roi_values if value >= parameters.threshold)
    else:
        scratch_area = sum(1 for value in roi_values if value <= parameters.threshold)
    non_scratch_area = roi_area - scratch_area
    scratch_fraction = scratch_area / roi_area
    non_scratch_fraction = 1 - scratch_fraction
    metrics = WoundHealingMetrics(
        roi_area_pixels=roi_area,
        scratch_area_pixels=scratch_area,
        scratch_area_fraction=scratch_fraction,
        non_scratch_area_pixels=non_scratch_area,
        non_scratch_area_fraction=non_scratch_fraction,
        threshold=parameters.threshold,
        scratch_mode=parameters.scratch_mode,
    )
    result = WoundHealingResult(
        task_id=task_id or f"wound_task_{uuid4().hex[:12]}",
        parameters=parameters,
        metrics=metrics,
        image_width=image_width,
        image_height=image_height,
    )
    return replace(result, warnings=evaluate_wound_healing_quality(result))


def create_wound_healing_audit_records(
    result: WoundHealingResult,
    *,
    source_path: str | Path,
) -> tuple[ImageAnalysisAuditRecord, ...]:
    return (
        ImageAnalysisAuditRecord(
            event_type="wound_healing_analysis_completed",
            message="已完成手动 ROI 阈值划痕面积估算。",
            details={
                "algorithm_name": ALGORITHM_NAME,
                "algorithm_version": ALGORITHM_VERSION,
                "source_path": str(source_path),
                "source_filename": Path(source_path).name,
                "image_dimensions": result.image_dimensions_dict(),
                "result_id": result.result_id,
                "task_id": result.task_id,
                "manual_roi_required": True,
                "threshold": result.parameters.threshold,
                "scratch_mode": result.parameters.scratch_mode,
                "formula": result.formula,
                "warnings": list(result.warnings),
                "review_notice": result.review_notice,
            },
        ),
    )
