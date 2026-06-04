from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.audit_models import ImageAnalysisAuditRecord
from app.labtools.image_analysis.image_models import IMAGE_REVIEW_NOTICE, ImageAnalysisError, LabImageRecord, utc_timestamp
from app.labtools.image_analysis.result_models import ImageAnalysisResult, placeholder_result
from app.labtools.image_analysis.roi_models import ROIRecord, empty_roi_placeholder


TASK_TYPES: dict[str, str] = {
    "wb_grayscale": "Western Blot 灰度分析",
    "wb_lane_band_measurement": "Western Blot Lane/Band 测量",
    "wb_fixed_rectangle_roi_measure": "Western Blot 固定矩形 ROI 灰度测量",
    "scratch_area": "划痕实验图像分析",
    "transwell_count": "Transwell 图像分析",
    "wound_healing": "划痕实验面积分析",
    "cell_counting": "细胞计数",
    "fluorescence_intensity": "荧光强度分析",
    "immunohistochemistry": "免疫组化 DAB 阳性面积分析",
    "densitometry": "灰度 / 墨值分析",
}

TASK_STATUSES = (
    "draft",
    "pending_configuration",
    "ready_to_run",
    "engine_missing",
    "run_request_created",
    "completed_placeholder",
    "algorithm_not_available",
    "completed",
    "failed",
)
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
    task_name: str = ""
    experiment_module: str = ""
    analysis_type: str = ""
    source_image_paths: tuple[str, ...] = ()
    import_mode: str = "reference_original_path"
    task_workspace: str = ""
    selected_macro_id: str = ""
    macro_template_path: str = ""
    output_dir: str = ""
    result_files: tuple[str, ...] = ()
    notes: str = ""

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
            "task_name": self.task_name,
            "task_type": self.task_type,
            "task_label": self.task_label,
            "experiment_module": self.experiment_module,
            "analysis_type": self.analysis_type or self.task_type,
            "source_image_paths": list(self.source_image_paths),
            "import_mode": self.import_mode,
            "task_workspace": self.task_workspace,
            "selected_macro_id": self.selected_macro_id,
            "macro_template_path": self.macro_template_path,
            "output_dir": self.output_dir,
            "result_files": list(self.result_files),
            "notes": self.notes,
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

    def with_workspace(
        self,
        *,
        task_workspace: str | None = None,
        output_dir: str | None = None,
        source_image_paths: tuple[str, ...] | None = None,
        macro_template_path: str | None = None,
        status: str | None = None,
    ) -> "ImageAnalysisTask":
        return ImageAnalysisTask(
            task_id=self.task_id,
            task_name=self.task_name,
            task_type=self.task_type,
            status=status or self.status,
            image_records=self.image_records,
            parameters=dict(self.parameters),
            roi_records=self.roi_records,
            result_records=self.result_records,
            audit_records=self.audit_records,
            created_at=self.created_at,
            updated_at=utc_timestamp(),
            review_notice=self.review_notice,
            experiment_module=self.experiment_module,
            analysis_type=self.analysis_type,
            source_image_paths=source_image_paths if source_image_paths is not None else self.source_image_paths,
            import_mode=self.import_mode,
            task_workspace=task_workspace if task_workspace is not None else self.task_workspace,
            selected_macro_id=self.selected_macro_id,
            macro_template_path=macro_template_path if macro_template_path is not None else self.macro_template_path,
            output_dir=output_dir if output_dir is not None else self.output_dir,
            result_files=self.result_files,
            notes=self.notes,
        )


def create_analysis_task(
    task_type: str,
    image_records: tuple[LabImageRecord, ...] = (),
    *,
    status: str | None = None,
) -> ImageAnalysisTask:
    if task_type not in TASK_TYPES:
        raise ImageAnalysisError(f"暂不支持该图像分析任务类型：{task_type}。")
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
        task_name=TASK_TYPES[task_type],
        task_type=task_type,
        status=task_status,
        image_records=image_records,
        source_image_paths=tuple(record.source_path for record in image_records),
        analysis_type=task_type,
        parameters={"algorithm_status": "not_available", "manual_review_required": True},
        roi_records=(empty_roi_placeholder(task_type),),
        result_records=(result,),
        audit_records=(audit,),
    )


def create_experiment_image_analysis_task(
    *,
    task_name: str,
    experiment_module: str,
    analysis_type: str,
    image_records: tuple[LabImageRecord, ...] = (),
    import_mode: str = "reference_original_path",
    parameters: dict[str, Any] | None = None,
    selected_macro_id: str = "",
    macro_template_path: str = "",
    notes: str = "",
) -> ImageAnalysisTask:
    task_id = f"image_task_{uuid4().hex[:12]}"
    result = placeholder_result(task_id, analysis_type)
    audit = ImageAnalysisAuditRecord(
        event_type="task_created",
        message="已创建实验图像分析任务；本阶段只生成运行请求，不执行真实图像识别。",
        details={"experiment_module": experiment_module, "analysis_type": analysis_type, "image_count": len(image_records)},
    )
    return ImageAnalysisTask(
        task_id=task_id,
        task_name=task_name or TASK_TYPES[analysis_type],
        task_type=analysis_type,
        status="draft",
        image_records=image_records,
        parameters=dict(parameters or {}),
        roi_records=(empty_roi_placeholder(analysis_type),),
        result_records=(result,),
        audit_records=(audit,),
        experiment_module=experiment_module,
        analysis_type=analysis_type,
        source_image_paths=tuple(record.source_path for record in image_records),
        import_mode=import_mode,
        selected_macro_id=selected_macro_id,
        macro_template_path=macro_template_path,
        notes=notes,
    )
