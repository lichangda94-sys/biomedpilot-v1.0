from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.labtools.image_analysis.image_models import ImageAnalysisError, utc_timestamp
from app.shared.local_engines import (
    IMAGE_ANALYSIS_ENGINE_REQUIREMENT_FIJI,
    IMAGE_ANALYSIS_ENGINE_REQUIREMENT_IMAGEJ,
    IMAGE_ANALYSIS_ENGINE_REQUIREMENTS,
)


MACRO_REGISTRY_SCHEMA_VERSION = "labtools_image_analysis_macro_registry.v1"


@dataclass(frozen=True)
class MacroTemplate:
    macro_id: str
    macro_name: str
    analysis_type: str
    experiment_module: str
    macro_file_path: str
    version: str
    description: str
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    parameter_schema: dict[str, Any] = field(default_factory=dict)
    minimum_engine_requirement: str = IMAGE_ANALYSIS_ENGINE_REQUIREMENT_IMAGEJ
    is_builtin: bool = True
    is_user_custom: bool = False
    created_at: str = field(default_factory=utc_timestamp)
    updated_at: str = field(default_factory=utc_timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "macro_id": self.macro_id,
            "macro_name": self.macro_name,
            "analysis_type": self.analysis_type,
            "experiment_module": self.experiment_module,
            "macro_file_path": self.macro_file_path,
            "version": self.version,
            "description": self.description,
            "required_inputs": list(self.required_inputs),
            "expected_outputs": list(self.expected_outputs),
            "parameter_schema": dict(self.parameter_schema),
            "minimum_engine_requirement": self.minimum_engine_requirement,
            "is_builtin": self.is_builtin,
            "is_user_custom": self.is_user_custom,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def path(self) -> Path:
        return Path(self.macro_file_path)


def built_in_macro_root() -> Path:
    return Path(__file__).resolve().parent / "macros"


def _template(
    macro_id: str,
    macro_name: str,
    experiment_module: str,
    analysis_type: str,
    relative_path: str,
    *,
    parameter_schema: dict[str, Any] | None = None,
    minimum_engine_requirement: str = IMAGE_ANALYSIS_ENGINE_REQUIREMENT_IMAGEJ,
    version: str = "0.1-placeholder",
    description: str = "占位 Macro：仅用于生成可复现运行请求，不执行真实图像识别算法。",
    expected_outputs: tuple[str, ...] = ("outputs/results.csv", "outputs/summary.txt", "logs/run_log.txt", "review/manual_review.json"),
) -> MacroTemplate:
    if minimum_engine_requirement not in IMAGE_ANALYSIS_ENGINE_REQUIREMENTS:
        raise ImageAnalysisError(f"暂不支持该 Macro 外部引擎要求：{minimum_engine_requirement}")
    return MacroTemplate(
        macro_id=macro_id,
        macro_name=macro_name,
        experiment_module=experiment_module,
        analysis_type=analysis_type,
        macro_file_path=str(built_in_macro_root() / relative_path),
        version=version,
        description=description,
        required_inputs=("input_images", "output_dir", "parameters"),
        expected_outputs=expected_outputs,
        parameter_schema=parameter_schema or {},
        minimum_engine_requirement=minimum_engine_requirement,
    )


BUILTIN_MACRO_TEMPLATES: tuple[MacroTemplate, ...] = (
    _template(
        "wb_grayscale_basic",
        "Western Blot 灰度分析占位 Macro",
        "western_blot",
        "wb_grayscale",
        "western_blot/wb_grayscale_basic.ijm",
        parameter_schema={"lane_count": "int", "target_protein": "str", "reference_protein": "str", "output_format": "CSV/TXT"},
    ),
    _template(
        "wb_lane_band_measurement",
        "Western Blot Lane/Band 测量占位 Macro",
        "western_blot",
        "wb_lane_band_measurement",
        "western_blot/wb_lane_band_measurement.ijm",
        parameter_schema={"lane_count": "int", "invert_image": "bool", "convert_to_8bit": "bool"},
    ),
    _template(
        "wb_batch_preprocess",
        "Western Blot 批量预处理 Macro",
        "western_blot",
        "wb_preprocess",
        "western_blot/wb_batch_preprocess.ijm",
        parameter_schema={"convert_to_8bit": "bool", "invert_mode": "auto/invert/no_invert", "subtract_background": "bool", "rolling_ball_radius": "number", "output_format": "tif/png"},
    ),
    _template(
        "wb_fixed_rectangle_roi_measure",
        "Western Blot 固定矩形 ROI 灰度测量 Macro",
        "western_blot",
        "wb_fixed_rectangle_roi_measure",
        "western_blot/wb_fixed_rectangle_roi_measure.ijm",
        parameter_schema={"roi_csv_path": "path", "output_csv_path": "path", "measurement_items": "Area/Mean/IntDen/RawIntDen"},
    ),
    _template(
        "scratch_area_basic",
        "划痕实验面积分析 ImageJ Macro",
        "cell_experiment",
        "scratch_area",
        "cell_experiment/scratch_area_basic.ijm",
        parameter_schema={"threshold_method": "str", "gap_polarity": "bright/dark", "blur_sigma": "number", "min_gap_area_px": "int", "saturated_percent": "number"},
        version="0.2-imagej-workflow",
        description="真实 ImageJ macro 生成模板：批量估算划痕空白区域面积和闭合比例；执行仍受外部引擎 gate 控制。",
        expected_outputs=("outputs/wound_scratch_results.csv", "logs/run_log.txt", "review/manual_review.json"),
    ),
    _template(
        "transwell_count_basic",
        "Transwell 颗粒计数 ImageJ Macro",
        "cell_experiment",
        "transwell_count",
        "cell_experiment/transwell_count_basic.ijm",
        parameter_schema={"threshold_method": "str", "cell_polarity": "dark/bright", "blur_sigma": "number", "min_particle_area_px": "int", "max_particle_area_px": "int/Infinity", "watershed": "bool"},
        version="0.2-imagej-workflow",
        description="真实 ImageJ macro 生成模板：批量统计 Transwell 染色图像颗粒数量和面积；执行仍受外部引擎 gate 控制。",
        expected_outputs=("outputs/transwell_results.csv", "logs/run_log.txt", "review/manual_review.json"),
    ),
    _template(
        "fluorescence_intensity_basic",
        "荧光强度分析占位 Macro",
        "cell_experiment",
        "fluorescence_intensity",
        "cell_experiment/fluorescence_intensity_basic.ijm",
        parameter_schema={"channel": "Red/Green/Blue/Gray/custom", "roi_mode": "placeholder", "metric": "mean/integrated_density"},
    ),
    _template(
        "ihc_dab_area_basic",
        "免疫组化 DAB 阳性面积 ImageJ Macro",
        "cell_experiment",
        "immunohistochemistry",
        "cell_experiment/ihc_dab_area_basic.ijm",
        parameter_schema={"threshold_method": "str", "positive_polarity": "dark/bright", "blur_sigma": "number", "min_positive_area_px": "int", "saturated_percent": "number"},
        version="0.2-imagej-workflow",
        description="真实 ImageJ macro 生成模板：批量估算 IHC/DAB 阳性面积比例和平均灰度；执行仍受外部引擎 gate 控制。",
        expected_outputs=("outputs/ihc_dab_area_results.csv", "logs/run_log.txt", "review/manual_review.json"),
    ),
    _template("convert_to_8bit", "转换 8-bit 占位 Macro", "common", "preprocess", "common/convert_to_8bit.ijm"),
    _template("batch_preprocess", "批量预处理占位 Macro", "common", "preprocess", "common/batch_preprocess.ijm"),
)

DEFAULT_MACRO_BY_ANALYSIS: dict[tuple[str, str], str] = {
    ("western_blot", "wb_grayscale"): "wb_grayscale_basic",
    ("western_blot", "wb_lane_band_measurement"): "wb_lane_band_measurement",
    ("western_blot", "wb_preprocess"): "wb_batch_preprocess",
    ("western_blot", "wb_fixed_rectangle_roi_measure"): "wb_fixed_rectangle_roi_measure",
    ("cell_experiment", "scratch_area"): "scratch_area_basic",
    ("cell_experiment", "transwell_count"): "transwell_count_basic",
    ("cell_experiment", "fluorescence_intensity"): "fluorescence_intensity_basic",
    ("cell_experiment", "immunohistochemistry"): "ihc_dab_area_basic",
}


def builtin_macro_registry() -> tuple[MacroTemplate, ...]:
    return BUILTIN_MACRO_TEMPLATES


def get_macro_template(macro_id: str) -> MacroTemplate:
    for template in BUILTIN_MACRO_TEMPLATES:
        if template.macro_id == macro_id:
            if not template.path.exists():
                raise ImageAnalysisError(f"内置 Macro 文件不存在：{template.macro_file_path}")
            return template
    raise ImageAnalysisError(f"未知 Macro 模板：{macro_id}")


def default_macro_for_analysis(experiment_module: str, analysis_type: str) -> MacroTemplate:
    macro_id = DEFAULT_MACRO_BY_ANALYSIS.get((experiment_module, analysis_type))
    if not macro_id:
        raise ImageAnalysisError(f"暂未登记该实验图像分析类型的 Macro：{experiment_module}/{analysis_type}")
    return get_macro_template(macro_id)
