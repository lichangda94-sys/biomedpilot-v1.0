from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ReducingAgentMode = Literal["none", "fixed_volume", "percent_of_final"]
LaneCountMode = Literal["auto", "fixed"]
LaneType = Literal["marker", "sample", "empty"]

WB_LOADING_REVIEW_NOTICE = (
    "本结果仅用于 Western Blot 上样体系计算。请根据实验室 SOP、试剂说明书和安全规范人工复核；"
    "本工具不判断实验设计合理性，也不进行图像分析或结果解释。"
)


class WBLoadingCalculatorError(ValueError):
    pass


@dataclass(frozen=True)
class WBLoadingConfig:
    experiment_name: str = "WB loading"
    target_protein_ug: float = 20
    final_volume_ul: float = 20
    loading_buffer_factor: float = 4
    reducing_agent_mode: ReducingAgentMode = "none"
    reducing_agent_name: str = ""
    reducing_agent_fixed_volume_ul: float = 0
    reducing_agent_percent: float = 0
    diluent_name: str = "ddH2O"
    marker_enabled: bool = True
    marker_name: str = "Protein Marker"
    marker_volume_ul: float = 5
    lane_count_mode: LaneCountMode = "auto"
    fixed_lane_count: int = 10
    min_pipette_volume_ul: float = 0.5


@dataclass(frozen=True)
class WBSampleInput:
    sample_name: str
    concentration_ug_per_ul: float
    note: str = ""


@dataclass(frozen=True)
class WBLoadingResultRow:
    sample_name: str
    concentration_ug_per_ul: float
    target_protein_ug: float
    sample_volume_ul: float
    loading_buffer_volume_ul: float
    reducing_agent_volume_ul: float
    diluent_volume_ul: float
    final_volume_ul: float
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    note: str = ""

    @property
    def status(self) -> str:
        if self.errors:
            return "Error"
        if self.warnings:
            return "Warning"
        return "OK"


@dataclass(frozen=True)
class WBLane:
    lane_index: int
    lane_label: str
    lane_type: LaneType
    sample_name: str = ""
    marker_volume_ul: float = 0
    result_row: WBLoadingResultRow | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class WBLoadingResult:
    config: WBLoadingConfig
    rows: tuple[WBLoadingResultRow, ...]
    lanes: tuple[WBLane, ...]
    lane_layout_table: tuple[tuple[str, ...], ...]
    steps: tuple[str, ...]
    review_notice: str
    summary_warnings: tuple[str, ...]
    summary_errors: tuple[str, ...]

    def as_text(self) -> str:
        lines = [
            f"{self.config.experiment_name} Western Blot 上样计算器",
            "Western Blot 上样体系辅助计算草稿",
            f"目标上样蛋白量：{_fmt(self.config.target_protein_ug)} µg / lane",
            f"目标终体积：{_fmt(self.config.final_volume_ul)} µL / lane",
            f"{_fmt(self.config.loading_buffer_factor)}X loading buffer：{_fmt(self.config.final_volume_ul / self.config.loading_buffer_factor)} µL / lane",
            f"总 loading buffer 体积：{_fmt(sum(row.loading_buffer_volume_ul for row in self.rows))} µL",
            "",
            "纵向计算明细表",
            "样本\t浓度(µg/µL)\t目标蛋白(µg)\t样本体积(µL)\tLoading buffer(µL)\t还原剂(µL)\t补足液(µL)\t终体积(µL)\t状态",
        ]
        for row in self.rows:
            lines.append(
                "\t".join(
                    (
                        row.sample_name,
                        _fmt(row.concentration_ug_per_ul),
                        _fmt(row.target_protein_ug),
                        _fmt(row.sample_volume_ul),
                        _fmt(row.loading_buffer_volume_ul),
                        _fmt(row.reducing_agent_volume_ul),
                        _fmt(row.diluent_volume_ul),
                        _fmt(row.final_volume_ul),
                        row.status,
                    )
                )
            )
            for warning in row.warnings:
                lines.append(f"  警告：{warning}")
            for error in row.errors:
                lines.append(f"  错误：{error}")
        lines.extend(["", "横向 lane layout"])
        lines.extend("\t".join(item for item in row) for row in self.lane_layout_table)
        if self.summary_warnings:
            lines.extend(["", "汇总 warning", *self.summary_warnings])
        if self.summary_errors:
            lines.extend(["", "汇总 error", *self.summary_errors])
        lines.extend(["", "通用步骤", *self.steps, "", "复核提示", self.review_notice])
        return "\n".join(lines)


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
