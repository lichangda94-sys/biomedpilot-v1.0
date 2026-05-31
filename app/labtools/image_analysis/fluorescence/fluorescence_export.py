from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from app.labtools.calculators.unit_conversion import format_number
from app.labtools.image_analysis.fluorescence.fluorescence_models import FluorescenceAnalysisResult


def fluorescence_result_to_json_dict(result: FluorescenceAnalysisResult) -> dict[str, Any]:
    dimensions = result.image_dimensions_dict()
    return {
        "result_id": result.result_id,
        "task_id": result.task_id,
        "status": result.status,
        "image_filename": _filename_from_path(result.parameters.image_path),
        "source_path_summary": _source_path_summary(result.parameters.image_path),
        "image_dimensions": dimensions,
        "signal_roi": result.parameters.signal_roi.to_dict(),
        "background_roi": result.parameters.background_roi.to_dict(),
        "metrics": result.metrics.to_dict(),
        "formula": result.formula,
        "warnings": list(result.warnings),
        "review_notice": result.review_notice,
        "generated_at": result.generated_at,
    }


def fluorescence_csv_rows(result: FluorescenceAnalysisResult) -> list[dict[str, str]]:
    metrics = result.metrics
    return [
        _row("roi_area_pixels", metrics.roi_area_pixels, "pixels", "signal ROI area"),
        _row("mean_intensity", metrics.mean_intensity, "grayscale intensity", "signal ROI mean"),
        _row("integrated_density", metrics.integrated_density, "intensity sum", "signal ROI pixel sum"),
        _row(
            "background_mean_intensity",
            metrics.background_mean_intensity,
            "grayscale intensity",
            "background ROI mean",
        ),
        _row(
            "corrected_total_fluorescence",
            metrics.corrected_total_fluorescence,
            "intensity sum",
            result.formula,
        ),
        _row("min_intensity", metrics.min_intensity, "grayscale intensity", "signal ROI min"),
        _row("max_intensity", metrics.max_intensity, "grayscale intensity", "signal ROI max"),
    ]


def fluorescence_csv_text(result: FluorescenceAnalysisResult) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=("metric", "value", "unit", "note"), lineterminator="\n")
    writer.writeheader()
    writer.writerows(fluorescence_csv_rows(result))
    return output.getvalue()


def fluorescence_json_preview(result: FluorescenceAnalysisResult) -> str:
    payload = fluorescence_result_to_json_dict(result)
    dimensions = payload["image_dimensions"]
    warning_text = "；".join(payload["warnings"]) if payload["warnings"] else "无"
    return "\n".join(
        [
            "JSON-compatible dict 预览",
            f"result_id: {payload['result_id']}",
            f"task_id: {payload['task_id']}",
            f"image_filename: {payload['image_filename']}",
            f"image_dimensions: {dimensions['width']} x {dimensions['height']} px",
            f"signal_roi: x={payload['signal_roi']['x']}, y={payload['signal_roi']['y']}, "
            f"w={payload['signal_roi']['width']}, h={payload['signal_roi']['height']}",
            f"background_roi: x={payload['background_roi']['x']}, y={payload['background_roi']['y']}, "
            f"w={payload['background_roi']['width']}, h={payload['background_roi']['height']}",
            f"warnings: {warning_text}",
        ]
    )


def _row(metric: str, value: float | int, unit: str, note: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": format_number(value),
        "unit": unit,
        "note": note,
    }


def _filename_from_path(path: str) -> str:
    name = Path(path).name
    return name or "未命名图片"


def _source_path_summary(path: str) -> str:
    candidate = Path(path)
    if candidate.name:
        return candidate.name
    return str(candidate)
