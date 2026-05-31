from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from app.labtools.calculators.unit_conversion import format_number
from app.labtools.image_analysis.wound_healing.wound_models import WoundHealingResult


def wound_result_to_json_dict(result: WoundHealingResult) -> dict[str, Any]:
    return {
        "result_id": result.result_id,
        "task_id": result.task_id,
        "status": result.status,
        "image_filename": _filename_from_path(result.parameters.image_path),
        "source_path_summary": _source_path_summary(result.parameters.image_path),
        "image_dimensions": result.image_dimensions_dict(),
        "roi": result.parameters.roi.to_dict(),
        "threshold": result.parameters.threshold,
        "scratch_mode": result.parameters.scratch_mode,
        "metrics": result.metrics.to_dict(),
        "formula": result.formula,
        "warnings": list(result.warnings),
        "review_notice": result.review_notice,
        "generated_at": result.generated_at,
    }


def wound_csv_rows(result: WoundHealingResult) -> list[dict[str, str]]:
    metrics = result.metrics
    return [
        _row("roi_area_pixels", metrics.roi_area_pixels, "pixels", "manual ROI area"),
        _row(
            "scratch_area_pixels",
            metrics.scratch_area_pixels,
            "pixels",
            "基于用户阈值的疑似划痕区域估算",
        ),
        _row(
            "scratch_area_fraction",
            metrics.scratch_area_fraction,
            "fraction",
            "scratch_area_pixels / ROI area",
        ),
        _row(
            "non_scratch_area_pixels",
            metrics.non_scratch_area_pixels,
            "pixels",
            "ROI area - scratch_area_pixels",
        ),
        _row(
            "non_scratch_area_fraction",
            metrics.non_scratch_area_fraction,
            "fraction",
            "基于阈值的 covered / migrated fraction 估算",
        ),
        _row("threshold", metrics.threshold, "grayscale intensity", "user selected threshold"),
        _row("scratch_mode", metrics.scratch_mode, "mode", "bright: >= threshold; dark: <= threshold"),
    ]


def wound_csv_text(result: WoundHealingResult) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=("metric", "value", "unit", "note"), lineterminator="\n")
    writer.writeheader()
    writer.writerows(wound_csv_rows(result))
    return output.getvalue()


def wound_json_preview(result: WoundHealingResult) -> str:
    payload = wound_result_to_json_dict(result)
    dimensions = payload["image_dimensions"]
    warning_text = "；".join(payload["warnings"]) if payload["warnings"] else "无"
    return "\n".join(
        [
            "JSON-compatible dict 预览",
            f"result_id: {payload['result_id']}",
            f"task_id: {payload['task_id']}",
            f"image_filename: {payload['image_filename']}",
            f"image_dimensions: {dimensions['width']} x {dimensions['height']} px",
            f"roi: x={payload['roi']['x']}, y={payload['roi']['y']}, "
            f"w={payload['roi']['width']}, h={payload['roi']['height']}",
            f"threshold: {payload['threshold']}",
            f"scratch_mode: {payload['scratch_mode']}",
            f"warnings: {warning_text}",
        ]
    )


def _row(metric: str, value: float | int | str, unit: str, note: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": format_number(value) if isinstance(value, int | float) else value,
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
