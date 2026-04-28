from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.reporting_adapter import ReportingAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class ReportExportResult:
    success: bool
    project_id: str
    source_path: str
    report_path: str
    report_type: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class ReportingService:
    def __init__(
        self,
        *,
        adapter: ReportingAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or ReportingAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def export_preflight_report(self, *, project_id: str, analysis_preflight_path: str) -> ReportExportResult:
        task = self._start_task(project_id=project_id, source_path=analysis_preflight_path)
        validation_error = self._validate(analysis_preflight_path)
        if validation_error is not None:
            result = ReportExportResult(
                success=False,
                project_id=project_id,
                source_path=analysis_preflight_path,
                report_path="",
                report_type="analysis_preflight_markdown",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(analysis_preflight_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if "preflight" not in payload:
                raise ValueError("Reporting 需要 Analysis preflight 输出。")
            batch_id = str(payload.get("batch_id", f"batch-{uuid4().hex[:12]}"))
            draft = self._adapter.build_analysis_preflight_report(payload)
            report_path = self._write_report(project_id, batch_id, draft.markdown)
            result = ReportExportResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                report_path=str(report_path),
                report_type="analysis_preflight_markdown",
                message=draft.summary,
                details={
                    "title": draft.title,
                    "source_runnable": draft.source_runnable,
                    "formal_report": False,
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="meta_analysis_report",
                source_path=str(source_path),
                output_path=str(report_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = ReportExportResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                report_path="",
                report_type="analysis_preflight_markdown",
                message="Reporting 导出失败，请确认输入来自 Analysis 预检输出。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, analysis_preflight_path: str) -> str | None:
        if not analysis_preflight_path.strip():
            return "请选择 Analysis 预检生成的 JSON 文件。"
        path = Path(analysis_preflight_path).expanduser()
        if not path.exists():
            return "Analysis 预检文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "Reporting 需要 Analysis 预检生成的 JSON 文件。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.REPORT_EXPORT,
            module="meta_analysis",
            title="Reporting",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Exporting report from {source_path}" if source_path else "Waiting for analysis preflight output",
        )

    def _finish_task(self, task: TaskRecord, result: ReportExportResult) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )

    def _write_report(self, project_id: str, batch_id: str, markdown: str) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "reporting"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"{batch_id}_analysis_preflight_report.md"
        report_path.write_text(markdown, encoding="utf-8")
        return report_path
