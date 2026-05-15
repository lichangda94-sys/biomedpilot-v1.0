from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.audit_models import ImageAnalysisAuditRecord
from app.labtools.image_analysis.image_models import IMAGE_REVIEW_NOTICE, ImageAnalysisError, LabImageRecord, utc_timestamp
from app.labtools.image_analysis.result_models import ImageAnalysisResult, placeholder_result
from app.labtools.image_analysis.roi_models import ROIRecord, empty_roi_placeholder


TASK_TYPES: dict[str, str] = {
    "wound_healing": "划痕实验面积分析",
    "cell_counting": "细胞计数",
    "fluorescence_intensity": "荧光强度分析",
    "densitometry": "灰度 / 墨值分析",
}

TASK_STATUSES = ("draft", "pending_configuration", "algorithm_not_available", "completed", "failed")
NON_COMPLETED_RESULT_STATUSES = ("draft", "algorithm_not_available")


@dataclass(frozen=True)
class ImageAnalysisTask:
    task_type: str
    status: str
    image_records: tuple[LabImageRecord, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)
    roi_records: tuple[ROIRecord, ...] = ()
    result_records: tuple[ImageAnalysisResult, ...] = ()
    audit_records: tuple[ImageAnalysisAuditRecord, ...] = ()
    created_at: str = field(default_factory=utc_timestamp)
    updated_at: str = field(default_factory=utc_timestamp)
    review_notice: str = IMAGE_REVIEW_NOTICE
    task_id: str = field(default_factory=lambda: f"image_task_{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if self.task_type not in TASK_TYPES:
            raise ImageAnalysisError(f"暂不支持该图像分析任务类型：{self.task_type}。")
        if self.status not in TASK_STATUSES:
            raise ImageAnalysisError(f"暂不支持该任务状态：{self.status}。")
        if self.status == "completed":
            raise ImageAnalysisError("当前阶段不允许创建 completed 图像分析任务。")
        for result in self.result_records:
            if result.status not in NON_COMPLETED_RESULT_STATUSES:
                raise ImageAnalysisError("当前阶段图像结果只能是 draft 或 algorithm_not_available。")
            if result.metrics:
                raise ImageAnalysisError("当前阶段不生成图像定量指标。")

    @property
    def task_label(self) -> str:
        return TASK_TYPES[self.task_type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "task_label": self.task_label,
            "status": self.status,
            "image_records": [record.to_dict() for record in self.image_records],
            "parameters": dict(self.parameters),
            "roi_records": [record.to_dict() for record in self.roi_records],
            "result_records": [record.to_dict() for record in self.result_records],
            "audit_records": [record.to_dict() for record in self.audit_records],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "review_notice": self.review_notice,
        }


def create_analysis_task(
    task_type: str,
    image_records: tuple[LabImageRecord, ...] = (),
    *,
    status: str | None = None,
) -> ImageAnalysisTask:
    task_status = status or ("pending_configuration" if image_records else "draft")
    task_id = f"image_task_{uuid4().hex[:12]}"
    result = placeholder_result(task_id, task_type)
    audit = ImageAnalysisAuditRecord(
        event_type="task_created",
        message="已创建图像分析任务草稿；算法尚未启用。",
        details={"task_type": task_type, "image_count": len(image_records)},
    )
    return ImageAnalysisTask(
        task_id=task_id,
        task_type=task_type,
        status=task_status,
        image_records=image_records,
        parameters={"algorithm_status": "not_available", "manual_review_required": True},
        roi_records=(empty_roi_placeholder(task_type),),
        result_records=(result,),
        audit_records=(audit,),
    )
