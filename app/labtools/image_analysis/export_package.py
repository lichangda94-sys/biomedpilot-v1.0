from __future__ import annotations

import json
import re
from csv import DictWriter
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from app.labtools.image_analysis.fluorescence.fluorescence_analyzer import (
    ALGORITHM_NAME as FLUORESCENCE_ALGORITHM_NAME,
    ALGORITHM_VERSION as FLUORESCENCE_ALGORITHM_VERSION,
)
from app.labtools.image_analysis.fluorescence.fluorescence_export import (
    fluorescence_csv_rows,
    fluorescence_result_to_json_dict,
)
from app.labtools.image_analysis.fluorescence.fluorescence_models import FluorescenceAnalysisResult
from app.labtools.image_analysis.image_models import ImageAnalysisError
from app.labtools.image_analysis.wound_healing.wound_analyzer import (
    ALGORITHM_NAME as WOUND_ALGORITHM_NAME,
    ALGORITHM_VERSION as WOUND_ALGORITHM_VERSION,
)
from app.labtools.image_analysis.wound_healing.wound_export import wound_csv_rows, wound_result_to_json_dict
from app.labtools.image_analysis.wound_healing.wound_models import WoundHealingResult


LABTOOLS_ROI_EXPORT_SCHEMA_VERSION = "labtools_roi_export_manifest.v1"
EXPORT_SCHEMA_VERSION = LABTOOLS_ROI_EXPORT_SCHEMA_VERSION
ROI_EXPORT_TYPE = "labtools_image_roi_export_package"
SOFTWARE_CHANNEL = "Developer Preview / testing"
REVIEW_STATUS = "manual_review_required"
OUTPUT_FILE_ROLES = ("manifest_json", "summary_csv", "markdown_fragment", "roi_overlay_png")
CSV_FIELDNAMES = (
    "export_schema_version",
    "tool_slug",
    "review_status",
    "measurement_id",
    "roi_id",
    "measurement_name",
    "value",
    "unit",
    "note",
    "roi_area_pixels",
    "threshold_value",
    "threshold_mode",
)
FLUORESCENCE_EXPORT_NOTICE = (
    "荧光结果为 manual ROI grayscale measurement assistance；需人工复核 ROI、背景区域、曝光条件和实验 SOP。"
)
WOUND_EXPORT_NOTICE = (
    "划痕结果为 manual ROI + user threshold semi-quantitative area estimation；"
    "需人工复核 ROI、阈值、原图质量和实验设计。"
)


@dataclass(frozen=True)
class ImageAnalysisExportPackage:
    success: bool
    analysis_type: str
    basename: str
    output_dir: str
    manifest_path: str
    csv_path: str
    markdown_path: str
    overlay_path: str
    files: dict[str, str]
    review_notice: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "analysis_type": self.analysis_type,
            "basename": self.basename,
            "output_dir": self.output_dir,
            "manifest_path": self.manifest_path,
            "csv_path": self.csv_path,
            "markdown_path": self.markdown_path,
            "overlay_path": self.overlay_path,
            "files": dict(self.files),
            "review_notice": self.review_notice,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def export_fluorescence_analysis_package(
    result: FluorescenceAnalysisResult,
    output_dir: str | Path | None,
) -> ImageAnalysisExportPackage:
    """Write a user-confirmed fluorescence ROI export package."""

    directory = _prepare_output_dir(output_dir)
    created_at = _utc_now()
    basename = build_export_basename("fluorescence_manual_roi", created_at, _short_token(result.result_id))
    paths = resolve_non_overwriting_paths(directory, basename)
    payload = fluorescence_result_to_json_dict(result)
    manifest = _manifest(
        tool_slug="fluorescence_manual_roi",
        tool_label="荧光图像手动 ROI 分析",
        analysis_mode="manual_roi_auxiliary_analysis",
        algorithm_name=FLUORESCENCE_ALGORITHM_NAME,
        algorithm_version=FLUORESCENCE_ALGORITHM_VERSION,
        result_payload=payload,
        parameters=_fluorescence_parameters(result),
        result_summary=_fluorescence_result_summary(result),
        result_semantics=FLUORESCENCE_EXPORT_NOTICE,
        created_at=created_at.isoformat(timespec="seconds"),
        files=paths,
    )

    _write_package_files(
        paths=paths,
        write_overlay=lambda path: _write_fluorescence_overlay(result, path),
        manifest=manifest,
        csv_text=_export_csv_text("fluorescence_manual_roi", fluorescence_csv_rows(result), result.parameters.signal_roi.roi_id),
        markdown_text=_export_markdown_fragment(
            tool_label="荧光图像手动 ROI 分析",
            tool_slug="fluorescence_manual_roi",
            created_at=created_at.isoformat(timespec="seconds"),
            manifest=manifest,
        ),
    )
    return _package_result("fluorescence_intensity", directory, paths, result.review_notice, result.warnings)


def export_wound_healing_analysis_package(
    result: WoundHealingResult,
    output_dir: str | Path | None,
) -> ImageAnalysisExportPackage:
    """Write a user-confirmed wound healing ROI export package."""

    directory = _prepare_output_dir(output_dir)
    created_at = _utc_now()
    basename = build_export_basename("wound_manual_roi_threshold", created_at, _short_token(result.result_id))
    paths = resolve_non_overwriting_paths(directory, basename)
    payload = wound_result_to_json_dict(result)
    manifest = _manifest(
        tool_slug="wound_manual_roi_threshold",
        tool_label="Scratch/Wound 手动 ROI + threshold 面积估算",
        analysis_mode="manual_roi_threshold_area_estimation",
        algorithm_name=WOUND_ALGORITHM_NAME,
        algorithm_version=WOUND_ALGORITHM_VERSION,
        result_payload=payload,
        parameters=_wound_parameters(result),
        result_summary=_wound_result_summary(result),
        result_semantics=WOUND_EXPORT_NOTICE,
        created_at=created_at.isoformat(timespec="seconds"),
        files=paths,
    )

    _write_package_files(
        paths=paths,
        write_overlay=lambda path: _write_wound_overlay(result, path),
        manifest=manifest,
        csv_text=_export_csv_text(
            "wound_manual_roi_threshold",
            wound_csv_rows(result),
            result.parameters.roi.roi_id,
            threshold_value=result.parameters.threshold,
            threshold_mode=result.parameters.scratch_mode,
        ),
        markdown_text=_export_markdown_fragment(
            tool_label="Scratch/Wound 手动 ROI + threshold 面积估算",
            tool_slug="wound_manual_roi_threshold",
            created_at=created_at.isoformat(timespec="seconds"),
            manifest=manifest,
        ),
    )
    return _package_result("wound_healing", directory, paths, result.review_notice, result.warnings)


def sanitize_filename_component(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    normalized = normalized.strip("._-")
    return normalized[:80] or "labtools_export"


def build_export_basename(tool_slug: str, created_at: datetime, token: str | None = None) -> str:
    timestamp = created_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parts = [sanitize_filename_component(tool_slug), timestamp]
    safe_token = sanitize_filename_component(token or "")
    if safe_token and safe_token != "labtools_export":
        parts.append(safe_token[:12])
    return "_".join(parts)[:140]


def resolve_non_overwriting_paths(output_dir: Path, basename: str) -> dict[str, Path]:
    stem = sanitize_filename_component(basename)
    for index in range(1000):
        candidate = stem if index == 0 else f"{stem}_{index:03d}"
        paths = _package_paths(output_dir, candidate)
        if not any(path.exists() for path in paths.values()):
            return paths
    raise ImageAnalysisError("导出目录中同名文件过多，请选择新的导出目录。")


def _manifest(
    *,
    tool_slug: str,
    tool_label: str,
    analysis_mode: str,
    algorithm_name: str,
    algorithm_version: str,
    result_payload: dict[str, Any],
    parameters: dict[str, Any],
    result_summary: dict[str, Any],
    result_semantics: str,
    created_at: str,
    files: dict[str, Path],
) -> dict[str, Any]:
    return {
        "schema_version": LABTOOLS_ROI_EXPORT_SCHEMA_VERSION,
        "export_type": ROI_EXPORT_TYPE,
        "tool_slug": tool_slug,
        "tool_label": tool_label,
        "analysis_mode": analysis_mode,
        "created_at": created_at,
        "app_channel": SOFTWARE_CHANNEL,
        "software_channel": SOFTWARE_CHANNEL,
        "algorithm": {
            "name": algorithm_name,
            "version": algorithm_version,
        },
        "manual_review_required": True,
        "review_status": REVIEW_STATUS,
        "semi_quantitative": tool_slug == "wound_manual_roi_threshold",
        "interpretation_note": result_semantics,
        "safety_note": (
            "本导出包来自手动 ROI / threshold 辅助分析，结果需人工复核，"
            "不构成自动图像算法结论、临床诊断或正式实验 SOP。"
        ),
        "source_image": {
            "source_image_name": result_payload.get("image_filename"),
            "source_image_reference": result_payload.get("source_path_summary"),
            "image_dimensions": result_payload.get("image_dimensions"),
        },
        "parameters": parameters,
        "result_summary": result_summary,
        "result": result_payload,
        "output_files": _output_file_manifest(files),
        "generated_files_count": len(files),
        "persistence_note": "仅在用户明确选择导出目录后写入本地文件；不自动保存、不上传、不联网。",
    }


def _prepare_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is None or str(output_dir).strip() == "":
        raise ImageAnalysisError("请选择 ROI 结果导出目录。")
    directory = Path(output_dir).expanduser()
    if directory.exists() and not directory.is_dir():
        raise ImageAnalysisError("导出位置必须是文件夹。")
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ImageAnalysisError("无法创建导出目录，请检查路径权限。") from exc
    if not _is_writable_directory(directory):
        raise ImageAnalysisError("导出目录不可写，请选择其它文件夹。")
    return directory


def _package_paths(directory: Path, stem: str) -> dict[str, Path]:
    return {
        "manifest_json": directory / f"{stem}_manifest.json",
        "summary_csv": directory / f"{stem}_summary.csv",
        "markdown_fragment": directory / f"{stem}_fragment.md",
        "roi_overlay_png": directory / f"{stem}_overlay.png",
    }


def _package_result(
    analysis_type: str,
    directory: Path,
    paths: dict[str, Path],
    review_notice: str,
    warnings: tuple[str, ...],
) -> ImageAnalysisExportPackage:
    files = {role: str(path) for role, path in paths.items()}
    return ImageAnalysisExportPackage(
        success=True,
        analysis_type=analysis_type,
        basename=_basename_from_paths(paths),
        output_dir=str(directory),
        manifest_path=str(paths["manifest_json"]),
        csv_path=str(paths["summary_csv"]),
        markdown_path=str(paths["markdown_fragment"]),
        overlay_path=str(paths["roi_overlay_png"]),
        files=files,
        review_notice=review_notice,
        warnings=warnings,
    )


def _basename_from_paths(paths: dict[str, Path]) -> str:
    return paths["manifest_json"].name.removesuffix("_manifest.json")


def _write_package_files(
    *,
    paths: dict[str, Path],
    write_overlay,
    manifest: dict[str, Any],
    csv_text: str,
    markdown_text: str,
) -> None:
    created: list[Path] = []
    try:
        write_overlay(paths["roi_overlay_png"])
        created.append(paths["roi_overlay_png"])
        _write_json(paths["manifest_json"], manifest)
        created.append(paths["manifest_json"])
        _write_text(paths["summary_csv"], csv_text)
        created.append(paths["summary_csv"])
        _write_text(paths["markdown_fragment"], markdown_text)
        created.append(paths["markdown_fragment"])
    except OSError as exc:
        _remove_created_files(created)
        raise ImageAnalysisError("导出写盘失败，请检查导出目录权限和可用空间。") from exc
    except ImageAnalysisError:
        _remove_created_files(created)
        raise


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _assert_output_path_available(path)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _write_text(path: Path, text: str) -> None:
    _assert_output_path_available(path)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _remove_created_files(paths: list[Path]) -> None:
    for path in paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def _is_writable_directory(directory: Path) -> bool:
    probe = directory / ".labtools_write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


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
    _assert_output_path_available(output_path)
    image.save(output_path)


def _write_wound_overlay(result: WoundHealingResult, output_path: Path) -> None:
    image = _load_rgb_image(result.parameters.image_path)
    draw = ImageDraw.Draw(image)
    roi = result.parameters.roi
    _draw_roi(draw, roi.x, roi.y, roi.width, roi.height, "#FB8C00")
    _assert_output_path_available(output_path)
    image.save(output_path)


def _draw_roi(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, color: str) -> None:
    x2 = max(x, x + width - 1)
    y2 = max(y, y + height - 1)
    draw.rectangle((x, y, x2, y2), outline=color, width=2)


def _assert_output_path_available(path: Path) -> None:
    if path.exists():
        raise ImageAnalysisError("导出目标文件已存在，已停止以避免覆盖。")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _short_token(value: str) -> str:
    return sanitize_filename_component(value)[-12:]


def _output_file_manifest(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    formats = {
        "manifest_json": ("json", "application/json"),
        "summary_csv": ("csv", "text/csv"),
        "markdown_fragment": ("markdown", "text/markdown"),
        "roi_overlay_png": ("png", "image/png"),
    }
    return {
        role: {
            "role": role,
            "filename": path.name,
            "relative_path": path.name,
            "format": formats[role][0],
            "media_type": formats[role][1],
        }
        for role, path in paths.items()
    }


def _fluorescence_parameters(result: FluorescenceAnalysisResult) -> dict[str, Any]:
    return {
        "manual_roi": True,
        "roi_count": 2,
        "rois": {
            "signal": result.parameters.signal_roi.to_dict(),
            "background": result.parameters.background_roi.to_dict(),
        },
        "measurement_fields": [row["metric"] for row in fluorescence_csv_rows(result)],
        "channel_mode": result.parameters.channel_mode,
        "background_correction_enabled": result.parameters.background_correction_enabled,
    }


def _wound_parameters(result: WoundHealingResult) -> dict[str, Any]:
    return {
        "manual_roi": True,
        "roi_count": 1,
        "roi": result.parameters.roi.to_dict(),
        "threshold_value": result.parameters.threshold,
        "threshold_mode": result.parameters.scratch_mode,
        "measurement_fields": [row["metric"] for row in wound_csv_rows(result)],
        "channel_mode": result.parameters.channel_mode,
    }


def _fluorescence_result_summary(result: FluorescenceAnalysisResult) -> dict[str, Any]:
    metrics = result.metrics
    return {
        "roi_area_pixels": metrics.roi_area_pixels,
        "mean_intensity": metrics.mean_intensity,
        "integrated_density": metrics.integrated_density,
        "background_mean_intensity": metrics.background_mean_intensity,
        "corrected_total_fluorescence": metrics.corrected_total_fluorescence,
        "review_status": REVIEW_STATUS,
        "interpretation": "manual ROI auxiliary output; requires human review",
    }


def _wound_result_summary(result: WoundHealingResult) -> dict[str, Any]:
    metrics = result.metrics
    return {
        "roi_area_pixels": metrics.roi_area_pixels,
        "scratch_area_pixels": metrics.scratch_area_pixels,
        "scratch_area_fraction": metrics.scratch_area_fraction,
        "non_scratch_area_pixels": metrics.non_scratch_area_pixels,
        "non_scratch_area_fraction": metrics.non_scratch_area_fraction,
        "threshold_value": metrics.threshold,
        "threshold_mode": metrics.scratch_mode,
        "review_status": REVIEW_STATUS,
        "interpretation": "manual ROI threshold area estimation; requires human review",
    }


def _export_csv_text(
    tool_slug: str,
    metric_rows: list[dict[str, str]],
    roi_id: str,
    *,
    threshold_value: int | str = "",
    threshold_mode: str = "",
) -> str:
    output = StringIO()
    writer = DictWriter(output, fieldnames=CSV_FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    for row in metric_rows:
        writer.writerow(
            {
                "export_schema_version": LABTOOLS_ROI_EXPORT_SCHEMA_VERSION,
                "tool_slug": tool_slug,
                "review_status": REVIEW_STATUS,
                "measurement_id": row["metric"],
                "roi_id": roi_id,
                "measurement_name": row["metric"],
                "value": row["value"],
                "unit": row["unit"],
                "note": row["note"],
                "roi_area_pixels": row["value"] if row["metric"] == "roi_area_pixels" else "",
                "threshold_value": str(threshold_value),
                "threshold_mode": threshold_mode,
            }
        )
    return output.getvalue()


def _export_markdown_fragment(
    *,
    tool_label: str,
    tool_slug: str,
    created_at: str,
    manifest: dict[str, Any],
) -> str:
    summary = manifest["result_summary"]
    output_files = manifest["output_files"]
    lines = [
        "## LabTools 手动 ROI 辅助分析导出片段",
        "",
        f"- 工具名称：{tool_label}",
        f"- 工具标识：`{tool_slug}`",
        f"- 导出时间：{created_at}",
        f"- 软件状态：{SOFTWARE_CHANNEL}",
        f"- 复核状态：{REVIEW_STATUS}",
        "",
        "### 结果摘要",
    ]
    lines.extend(f"- {key}: {value}" for key, value in summary.items())
    lines.extend(
        [
            "",
            "### 输出文件",
            *[f"- {value['role']}：`{value['filename']}`" for value in output_files.values()],
            "",
            "### 人工复核提示",
            "本片段来自手动 ROI / threshold 辅助分析，结果需结合原始图像和实验 SOP 人工复核。",
            "本片段不构成自动图像算法结论或实验 SOP。",
        ]
    )
    return "\n".join(lines)
