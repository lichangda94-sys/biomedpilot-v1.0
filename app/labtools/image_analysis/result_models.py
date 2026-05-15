from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.image_models import IMAGE_REVIEW_NOTICE, utc_timestamp


@dataclass(frozen=True)
class ImageAnalysisResult:
    task_id: str
    result_type: str
    status: str = "algorithm_not_available"
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ("算法开发中，未生成定量结果。",)
    review_notice: str = IMAGE_REVIEW_NOTICE
    generated_at: str = field(default_factory=utc_timestamp)
    result_id: str = field(default_factory=lambda: f"image_result_{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if self.status == "completed":
            raise ValueError("L4A 阶段不允许创建 completed 图像分析结果。")
        if self.metrics:
            raise ValueError("L4A 阶段不允许生成面积、细胞数、荧光或灰度等定量指标。")

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "result_type": self.result_type,
            "status": self.status,
            "metrics": dict(self.metrics),
            "warnings": list(self.warnings),
            "review_notice": self.review_notice,
            "generated_at": self.generated_at,
        }


def placeholder_result(task_id: str, result_type: str) -> ImageAnalysisResult:
    return ImageAnalysisResult(task_id=task_id, result_type=result_type, status="algorithm_not_available")
