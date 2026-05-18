from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.image_models import utc_timestamp
from app.labtools.image_analysis.task_store import ImageAnalysisTaskStore, ImageAnalysisTaskWorkspace

WB_ROI_SCHEMA_VERSION = "labtools_wb_rectangle_roi.v1"
WB_ROI_TYPES = {"target_band": "目标蛋白", "control_band": "内参蛋白", "total_protein_lane": "总蛋白 / Lane", "background": "背景"}
WB_ROI_CSV_FIELDS = ("roi_id", "image_id", "image_path", "roi_type", "label", "lane_index", "sample_name", "x", "y", "width", "height", "linked_background_roi_id", "notes")


class WBROIAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class WBRectangleROI:
    image_id: str
    image_path: str
    roi_type: str
    x: float
    y: float
    width: float
    height: float
    label: str = ""
    lane_index: int = 1
    sample_name: str = ""
    linked_target_roi_id: str = ""
    linked_control_roi_id: str = ""
    linked_total_protein_roi_id: str = ""
    linked_background_roi_id: str = ""
    notes: str = ""
    roi_id: str = field(default_factory=lambda: f"wb_roi_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=utc_timestamp)
    updated_at: str = field(default_factory=utc_timestamp)
    schema_version: str = WB_ROI_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.roi_type not in WB_ROI_TYPES:
            raise WBROIAnalysisError(f"不支持的 WB ROI 类型：{self.roi_type}")
        if self.width <= 0 or self.height <= 0:
            raise WBROIAnalysisError("ROI width 和 height 必须大于 0。")
        if self.lane_index < 1:
            raise WBROIAnalysisError("lane_index 必须大于 0。")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Any) -> "WBRectangleROI":
        if not isinstance(payload, dict):
            raise WBROIAnalysisError("WB ROI payload 必须是 JSON object。")
        values = {key: payload.get(key) for key in cls.__dataclass_fields__ if key in payload}
        values["lane_index"] = int(values.get("lane_index") or 1)
        for key in ("x", "y", "width", "height"):
            values[key] = float(values.get(key) or 0)
        return cls(**values)

    def csv_row(self) -> dict[str, str]:
        payload = self.to_dict()
        return {key: str(payload.get(key, "")) for key in WB_ROI_CSV_FIELDS}

    def with_updates(self, **changes: Any) -> "WBRectangleROI":
        payload = self.to_dict()
        payload.update(changes)
        payload["updated_at"] = utc_timestamp()
        return WBRectangleROI.from_dict(payload)


@dataclass(frozen=True)
class CoordinateMapper:
    image_width: float
    image_height: float
    display_width: float
    display_height: float

    @property
    def scale(self) -> float:
        if min(self.image_width, self.image_height, self.display_width, self.display_height) <= 0:
            raise WBROIAnalysisError("图片和显示区域尺寸必须大于 0。")
        return min(self.display_width / self.image_width, self.display_height / self.image_height)

    @property
    def offset_x(self) -> float:
        return (self.display_width - self.image_width * self.scale) / 2

    @property
    def offset_y(self) -> float:
        return (self.display_height - self.image_height * self.scale) / 2

    def display_to_image_rect(self, x: float, y: float, width: float, height: float) -> tuple[float, float, float, float]:
        scale = self.scale
        return (max(0, (x - self.offset_x) / scale), max(0, (y - self.offset_y) / scale), max(1, width / scale), max(1, height / scale))

    def image_to_display_rect(self, x: float, y: float, width: float, height: float) -> tuple[float, float, float, float]:
        scale = self.scale
        return (x * scale + self.offset_x, y * scale + self.offset_y, width * scale, height * scale)


@dataclass(frozen=True)
class FixedROISize:
    width: float
    height: float


@dataclass
class WBROICollection:
    rois: list[WBRectangleROI] = field(default_factory=list)
    fixed_size: FixedROISize | None = None

    def add_roi(self, roi: WBRectangleROI) -> WBRectangleROI:
        if self.fixed_size:
            roi = roi.with_updates(width=self.fixed_size.width, height=self.fixed_size.height)
        self.rois.append(roi)
        return roi

    def selected(self, roi_id: str) -> WBRectangleROI:
        for roi in self.rois:
            if roi.roi_id == roi_id:
                return roi
        raise WBROIAnalysisError("ROI 不存在。")

    def set_fixed_size_from_roi(self, roi_id: str) -> FixedROISize:
        roi = self.selected(roi_id)
        self.fixed_size = FixedROISize(roi.width, roi.height)
        return self.fixed_size

    def unify_size(self, roi_ids: tuple[str, ...] | list[str] | None = None) -> None:
        if not self.fixed_size:
            raise WBROIAnalysisError("请先设置固定 ROI 尺寸。")
        selected = set(roi_ids or [roi.roi_id for roi in self.rois])
        self.rois = [roi.with_updates(width=self.fixed_size.width, height=self.fixed_size.height) if roi.roi_id in selected else roi for roi in self.rois]

    def copy_to_next_lane(self, roi_id: str, *, x_offset: float = 0) -> WBRectangleROI:
        source = self.selected(roi_id)
        copied = source.with_updates(roi_id=f"wb_roi_{uuid4().hex[:12]}", lane_index=source.lane_index + 1, x=source.x + (x_offset or source.width))
        self.rois.append(copied)
        return copied

    def copy_to_all_lanes(self, roi_id: str, lane_count: int, *, x_step: float | None = None) -> tuple[WBRectangleROI, ...]:
        source = self.selected(roi_id)
        step = source.width if x_step is None else x_step
        copied = []
        for lane in range(1, lane_count + 1):
            if lane != source.lane_index:
                clone = source.with_updates(roi_id=f"wb_roi_{uuid4().hex[:12]}", lane_index=lane, x=source.x + (lane - source.lane_index) * step)
                self.rois.append(clone)
                copied.append(clone)
        return tuple(copied)

    def delete_roi(self, roi_id: str) -> None:
        self.rois = [roi for roi in self.rois if roi.roi_id != roi_id]

    def clear(self) -> None:
        self.rois.clear()


def export_wb_roi_csv(rois: tuple[WBRectangleROI, ...] | list[WBRectangleROI], path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WB_ROI_CSV_FIELDS)
        writer.writeheader()
        for roi in rois:
            writer.writerow(roi.csv_row())
    return resolved


def export_wb_roi_json(rois: tuple[WBRectangleROI, ...] | list[WBRectangleROI], path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps({"schema_version": WB_ROI_SCHEMA_VERSION, "rois": [roi.to_dict() for roi in rois]}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


@dataclass(frozen=True)
class WBMeasurement:
    roi_id: str
    image_id: str
    image_path: str
    roi_type: str
    label: str
    lane_index: int
    sample_name: str
    x: float
    y: float
    width: float
    height: float
    area: float
    mean_gray_value: float
    integrated_density: float
    raw_integrated_density: float
    background_roi_id: str = ""
    notes: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "WBMeasurement":
        def number(*keys: str) -> float:
            return next((float(row[key]) for key in keys if row.get(key) not in (None, "")), 0.0)

        return cls(row.get("roi_id", ""), row.get("image_id", ""), row.get("image_path", ""), row.get("roi_type", ""), row.get("label", ""), int(float(row.get("lane_index") or 0)), row.get("sample_name", ""), number("x"), number("y"), number("width"), number("height"), number("area", "Area"), number("mean_gray_value", "Mean"), number("integrated_density", "IntDen"), number("raw_integrated_density", "RawIntDen"), row.get("background_roi_id") or row.get("linked_background_roi_id", ""), row.get("notes", ""))


@dataclass(frozen=True)
class WBNormalizedResult:
    lane_index: int
    sample_name: str
    target_density: float | None = None
    control_density: float | None = None
    total_protein_density: float | None = None
    target_control_ratio: float | None = None
    target_total_protein_ratio: float | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_wb_measurement_csv(path: str | Path) -> tuple[WBMeasurement, ...]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return tuple(WBMeasurement.from_csv_row(row) for row in csv.DictReader(handle))


def background_corrected_density(measurement: WBMeasurement, background: WBMeasurement | None) -> float:
    return measurement.raw_integrated_density - measurement.area * (background.mean_gray_value if background else 0)


def calculate_wb_normalization(measurements: tuple[WBMeasurement, ...] | list[WBMeasurement]) -> tuple[WBNormalizedResult, ...]:
    by_roi = {measurement.roi_id: measurement for measurement in measurements}
    results = []
    for lane in sorted({measurement.lane_index for measurement in measurements if measurement.lane_index > 0}):
        rows = [measurement for measurement in measurements if measurement.lane_index == lane]
        target = _first(rows, "target_band")
        control = _first(rows, "control_band")
        total = _first(rows, "total_protein_lane")
        sample = next((row.sample_name for row in rows if row.sample_name), "")
        if not target:
            results.append(WBNormalizedResult(lane, sample, error="缺少目标蛋白 ROI。"))
            continue
        target_density = background_corrected_density(target, by_roi.get(target.background_roi_id))
        control_density = background_corrected_density(control, by_roi.get(control.background_roi_id)) if control else None
        total_density = background_corrected_density(total, by_roi.get(total.background_roi_id)) if total else None
        error = "缺少内参蛋白 ROI，无法计算目标/内参比值。" if not control else ("内参背景扣除密度为 0，无法计算目标/内参比值。" if control_density == 0 else "")
        results.append(WBNormalizedResult(lane, sample, target_density, control_density, total_density, None if error else target_density / control_density, None if not total_density else target_density / total_density, error))
    return tuple(results)


def export_wb_normalized_results(results: tuple[WBNormalizedResult, ...] | list[WBNormalizedResult], path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    fields = ("lane_index", "sample_name", "target_density", "control_density", "total_protein_density", "target_control_ratio", "target_total_protein_ratio", "error")
    with resolved.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())
    return resolved


def create_wb_roi_run_request_workspace(*, image_path: str, rois: tuple[WBRectangleROI, ...] | list[WBRectangleROI], parameters: dict[str, Any] | None = None, task_store: ImageAnalysisTaskStore | None = None) -> ImageAnalysisTaskWorkspace:
    store = task_store or ImageAnalysisTaskStore()
    workspace = store.create_workspace(task_name="Western Blot ROI 灰度测量", experiment_module="western_blot", analysis_type="wb_fixed_rectangle_roi_measure", image_paths=(image_path,), import_mode="reference_original_path", parameters=parameters or {})
    roi_csv = export_wb_roi_csv(rois, workspace.task_dir / "rois" / "wb_rois.csv")
    export_wb_roi_json(rois, workspace.task_dir / "rois" / "wb_rois.json")
    payload = json.loads(workspace.generated_parameters_path.read_text(encoding="utf-8"))
    payload.update({"roi_csv_path": str(roi_csv), "output_csv_path": str(workspace.output_dir / "wb_measurements.csv"), "output_log_path": str(workspace.log_dir / "run_log.txt")})
    workspace.generated_parameters_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return store.create_run_request(workspace)


def unsupported_image_format_message(path: str | Path) -> str:
    return "" if Path(path).suffix.lower() in {".tif", ".tiff", ".png", ".jpg", ".jpeg"} else "当前文件格式暂不支持直接分析。请先从凝胶成像仪软件导出为 TIFF、PNG 或 JPG 后再导入。"


def _first(measurements: list[WBMeasurement], roi_type: str) -> WBMeasurement | None:
    return next((measurement for measurement in measurements if measurement.roi_type == roi_type), None)
