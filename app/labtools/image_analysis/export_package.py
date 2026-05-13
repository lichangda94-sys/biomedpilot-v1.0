from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from app.labtools.image_analysis.fluorescence.fluorescence_analyzer import (
    ALGORITHM_NAME as FLUORESCENCE_ALGORITHM_NAME,
    ALGORITHM_VERSION as FLUORESCENCE_ALGORITHM_VERSION,
)
from app.labtools.image_analysis.fluorescence.fluorescence_export import (
    fluorescence_csv_text,
    fluorescence_result_to_json_dict,
)
from app.labtools.image_analysis.fluorescence.fluorescence_models import FluorescenceAnalysisResult
from app.labtools.image_analysis.fluorescence.fluorescence_report import fluorescence_markdown_report_fragment
from app.labtools.image_analysis.image_models import ImageAnalysisError, utc_timestamp
from app.labtools.image_analysis.wound_healing.wound_analyzer import (
    ALGORITHM_NAME as WOUND_ALGORITHM_NAME,
    ALGORITHM_VERSION as WOUND_ALGORITHM_VERSION,
)
from app.labtools.image_analysis.wound_healing.wound_export import wound_csv_text, wound_result_to_json_dict
from app.labtools.image_analysis.wound_healing.wound_models import WoundHealingResult
from app.labtools.image_analysis.wound_healing.wound_report import wound_markdown_report_fragment


EXPORT_SCHEMA_VERSION = "labtools_image_analysis_export_package_v1"
FLUORESCENCE_EXPORT_NOTICE = (
    "荧光结果为 manual ROI grayscale measurement assistance；需人工复核 ROI、背景区域、曝光条件和实验 SOP。"
)
WOUND_EXPORT_NOTICE = (
    "划痕结果为 manual ROI + user threshold semi-quantitative area estimation；"
    "需人工复核 ROI、阈值、原图质量和实验设计。"
)


@dataclass(frozen=True)
class ImageAnalysisExportPackage:
    analysis_type: str
    output_dir: str
    manifest_path: str
    csv_path: str
    markdown_path: str
    overlay_path: str
    files: tuple[str, ...]
    review_notice: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_type": self.analysis_type,
            "output_dir": self.output_dir,
            "manifest_path": self.manifest_path,
            "csv_path": self.csv_path,
            "markdown_path": self.markdown_path,
            "overlay_path": self.overlay_path,
            "files": list(self.files),
            "review_notice": self.review_notice,
            "warnings": list(self.warnings),
        }


def export_fluorescence_analysis_package(
    result: FluorescenceAnalysisResult,
    output_dir: str | Path,
) -> ImageAnalysisExportPackage:
    """Write a user-confirmed fluorescence ROI export package."""

    directory = _prepare_output_dir(output_dir)
    stem = _safe_stem(result.result_id or result.task_id, "fluorescence_result")
    paths = _package_paths(directory, stem)
    payload = fluorescence_result_to_json_dict(result)
    manifest = _manifest(
        analysis_type="fluorescence_intensity",
        algorithm_name=FLUORESCENCE_ALGORITHM_NAME,
        algorithm_version=FLUORESCENCE_ALGORITHM_VERSION,
        result_payload=payload,
        result_semantics=FLUORESCENCE_EXPORT_NOTICE,
        files=paths,
    )

    _write_fluorescence_overlay(result, paths["overlay"])
    _write_json(paths["manifest"], manifest)
    _write_text(paths["csv"], fluorescence_csv_text(result))
    _write_text(paths["markdown"], fluorescence_markdown_report_fragment(result))
    return _package_result("fluorescence_intensity", directory, paths, result.review_notice, result.warnings)


def export_wound_healing_analysis_package(
    result: WoundHealingResult,
    output_dir: str | Path,
) -> ImageAnalysisExportPackage:
    """Write a user-confirmed wound healing ROI export package."""

    directory = _prepare_output_dir(output_dir)
    stem = _safe_stem(result.result_id or result.task_id, "wound_result")
    paths = _package_paths(directory, stem)
    payload = wound_result_to_json_dict(result)
    manifest = _manifest(
        analysis_type="wound_healing",
        algorithm_name=WOUND_ALGORITHM_NAME,
        algorithm_version=WOUND_ALGORITHM_VERSION,
        result_payload=payload,
        result_semantics=WOUND_EXPORT_NOTICE,
        files=paths,
    )

    _write_wound_overlay(result, paths["overlay"])
    _write_json(paths["manifest"], manifest)
    _write_text(paths["csv"], wound_csv_text(result))
    _write_text(paths["markdown"], wound_markdown_report_fragment(result))
    return _package_result("wound_healing", directory, paths, result.review_notice, result.warnings)


def _manifest(
    *,
    analysis_type: str,
    algorithm_name: str,
    algorithm_version: str,
    result_payload: dict[str, Any],
    result_semantics: str,
    files: dict[str, Path],
) -> dict[str, Any]:
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": utc_timestamp(),
        "analysis_type": analysis_type,
        "algorithm": {
            "name": algorithm_name,
            "version": algorithm_version,
        },
        "manual_review_required": True,
        "semi_quantitative": analysis_type == "wound_healing",
        "result_semantics": result_semantics,
        "source_image": {
            "image_filename": result_payload.get("image_filename"),
            "source_path_summary": result_payload.get("source_path_summary"),
            "image_dimensions": result_payload.get("image_dimensions"),
        },
        "result": result_payload,
        "derived_files": {key: path.name for key, path in files.items()},
        "persistence_note": "仅在用户明确选择导出目录后写入本地文件；不自动保存、不上传、不联网。",
    }


def _prepare_output_dir(output_dir: str | Path) -> Path:
    directory = Path(output_dir).expanduser()
    if directory.exists() and not directory.is_dir():
        raise ImageAnalysisError("导出位置必须是文件夹。")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _package_paths(directory: Path, stem: str) -> dict[str, Path]:
    return {
        "manifest": directory / f"{stem}_manifest.json",
        "csv": directory / f"{stem}_summary.csv",
        "markdown": directory / f"{stem}_report.md",
        "overlay": directory / f"{stem}_roi_overlay.png",
    }


def _package_result(
    analysis_type: str,
    directory: Path,
    paths: dict[str, Path],
    review_notice: str,
    warnings: tuple[str, ...],
) -> ImageAnalysisExportPackage:
    files = tuple(str(path) for path in paths.values())
    return ImageAnalysisExportPackage(
        analysis_type=analysis_type,
        output_dir=str(directory),
        manifest_path=str(paths["manifest"]),
        csv_path=str(paths["csv"]),
        markdown_path=str(paths["markdown"]),
        overlay_path=str(paths["overlay"]),
        files=files,
        review_notice=review_notice,
        warnings=warnings,
    )


def _safe_stem(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    normalized = normalized.strip("._-")
    return normalized or fallback


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _load_rgb_image(path: str) -> Image.Image:
    try:
        with Image.open(path) as image:
            return image.convert("RGB")
    except OSError as exc:
        raise ImageAnalysisError("无法读取原图以生成 ROI overlay 预览。") from exc


def _write_fluorescence_overlay(result: FluorescenceAnalysisResult, output_path: Path) -> None:
    image = _load_rgb_image(result.parameters.image_path)
    draw = ImageDraw.Draw(image)
    signal = result.parameters.signal_roi
    background = result.parameters.background_roi
    _draw_roi(draw, signal.x, signal.y, signal.width, signal.height, "#E53935")
    _draw_roi(draw, background.x, background.y, background.width, background.height, "#1E88E5")
    image.save(output_path)


def _write_wound_overlay(result: WoundHealingResult, output_path: Path) -> None:
    image = _load_rgb_image(result.parameters.image_path)
    draw = ImageDraw.Draw(image)
    roi = result.parameters.roi
    _draw_roi(draw, roi.x, roi.y, roi.width, roi.height, "#FB8C00")
    image.save(output_path)


def _draw_roi(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, color: str) -> None:
    x2 = max(x, x + width - 1)
    y2 = max(y, y + height - 1)
    draw.rectangle((x, y, x2, y2), outline=color, width=2)
