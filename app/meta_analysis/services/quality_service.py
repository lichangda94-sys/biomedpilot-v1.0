from __future__ import annotations

import csv
import json
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.systematic_review import (
    QualityAssessment,
    new_quality_assessment_id,
    now_utc,
    quality_assessment_from_dict,
    quality_assessment_to_dict,
)
from app.meta_analysis.quality.tool_registry import get_quality_tool, list_quality_tools
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class QualityAssessmentService:
    def __init__(self, *, task_center: TaskCenter | None = None, data_center: DataCenter | None = None) -> None:
        self._task_center = task_center
        self._data_center = data_center

    def create_quality_assessment(
        self,
        *,
        project_id: str,
        study_id: str,
        record_id: str,
        tool_name: str,
        domains: dict[str, str],
        overall_judgement: str,
        reviewer_id: str,
        notes: str = "",
    ) -> QualityAssessment:
        if get_quality_tool(tool_name) is None:
            raise ValueError("unsupported_quality_tool")
        return QualityAssessment(
            assessment_id=new_quality_assessment_id(),
            project_id=project_id,
            study_id=study_id,
            record_id=record_id,
            tool_name=tool_name,
            domains=dict(domains),
            overall_judgement=overall_judgement,
            reviewer_id=reviewer_id,
            notes=notes,
            created_at=now_utc(),
        )

    def save_quality_assessment(self, project_dir: Path, assessment: QualityAssessment) -> Path:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=assessment.project_id, task_type=TaskType.QUALITY_ASSESSMENT_SAVE, title="Quality Assessment Save")
        assessments = [existing for existing in self.load_quality_assessments(project_dir) if existing.assessment_id != assessment.assessment_id]
        assessments.append(assessment)
        output_path = self._assessments_path(project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"project_id": assessment.project_id, "quality_assessments": [quality_assessment_to_dict(item) for item in assessments]}
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(project_id=assessment.project_id, data_type="quality_assessments", source_path=str(project_dir), output_path=str(output_path))
        self._finish_task(task, success=True, summary=f"Quality assessment saved: {assessment.assessment_id}")
        return output_path

    def load_quality_assessments(self, project_dir: Path) -> list[QualityAssessment]:
        path = self._assessments_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [quality_assessment_from_dict(item) for item in payload.get("quality_assessments", [])]

    def summarize_quality_assessments(self, project_dir: Path) -> dict[str, object]:
        assessments = self.load_quality_assessments(project_dir)
        by_tool: dict[str, int] = {}
        by_overall: dict[str, int] = {}
        for assessment in assessments:
            by_tool[assessment.tool_name] = by_tool.get(assessment.tool_name, 0) + 1
            by_overall[assessment.overall_judgement] = by_overall.get(assessment.overall_judgement, 0) + 1
        return {"assessment_count": len(assessments), "by_tool": by_tool, "by_overall_judgement": by_overall}

    def export_quality_table_csv(self, project_dir: Path) -> Path:
        project_dir = project_dir.expanduser().resolve()
        assessments = self.load_quality_assessments(project_dir)
        task = self._start_task(project_id=project_dir.name, task_type=TaskType.QUALITY_ASSESSMENT_EXPORT, title="Quality Assessment Export")
        output_path = project_dir / "exports" / "quality_assessment_table.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        domain_names = sorted({domain for assessment in assessments for domain in assessment.domains})
        fieldnames = ["assessment_id", "study_id", "record_id", "tool_name", "overall_judgement", "reviewer_id", *domain_names, "notes", "created_at"]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for assessment in assessments:
                row = {
                    "assessment_id": assessment.assessment_id,
                    "study_id": assessment.study_id,
                    "record_id": assessment.record_id,
                    "tool_name": assessment.tool_name,
                    "overall_judgement": assessment.overall_judgement,
                    "reviewer_id": assessment.reviewer_id,
                    "notes": assessment.notes,
                    "created_at": assessment.created_at,
                }
                row.update(assessment.domains)
                writer.writerow(row)
        self._register_asset(project_id=project_dir.name, data_type="quality_assessment_table", source_path=str(self._assessments_path(project_dir)), output_path=str(output_path))
        self._finish_task(task, success=True, summary=f"Quality assessment table exported: {output_path}")
        return output_path

    def list_quality_tools(self) -> list[str]:
        return [tool.tool_name for tool in list_quality_tools()]

    def _assessments_path(self, project_dir: Path) -> Path:
        return project_dir / "quality" / "quality_assessments.json"

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(project_id=project_id, module="meta_analysis", data_type=data_type, source_path=source_path, output_path=output_path, status="available")

    def _start_task(self, *, project_id: str, task_type: TaskType, title: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, status=TaskStatus.RUNNING, module="meta_analysis", title=title, created_at=now, updated_at=now, project_id=project_id, started_at=now)
        return self._task_center.register_task(task_id=f"task-{uuid4().hex[:12]}", task_type=task_type, module="meta_analysis", title=title, project_id=project_id, status=TaskStatus.RUNNING, started_at=now)

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(TaskRecord(task_id=task.task_id, task_type=task.task_type, status=TaskStatus.COMPLETED if success else TaskStatus.FAILED, module=task.module, title=task.title, created_at=task.created_at, updated_at=now, project_id=task.project_id, started_at=task.started_at, finished_at=now, summary=summary, error_message="" if success else summary))
