from __future__ import annotations

from dataclasses import dataclass


REVIEW_TIP = "请人工复核计算结果后再用于实验。"


class CalculationError(ValueError):
    """User-facing calculation validation error."""


@dataclass(frozen=True)
class CalculationResult:
    title: str
    input_summary: tuple[str, ...]
    formula: tuple[str, ...]
    result_lines: tuple[str, ...]
    review_tip: str = REVIEW_TIP
    result_value: float | None = None
    result_unit: str | None = None

    def as_text(self) -> str:
        sections = [
            "输入摘要",
            *self.input_summary,
            "",
            "计算公式",
            *self.formula,
            "",
            "结果",
            *self.result_lines,
            "",
            "复核提示",
            self.review_tip,
        ]
        return "\n".join(sections)
