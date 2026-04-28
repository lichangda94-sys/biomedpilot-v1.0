from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.bio_report_adapter import BioReportAdapter, BioReportSourceSummary
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class BioReportExportResult:
    success: bool
    project_id: str
    source_paths: list[str]
    source_count: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class BioReportService:
    def __init__(
        self,
        *,
        adapter: BioReportAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or BioReportAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def export_summary_report(self, *, project_id: str, source_paths: list[str]) -> BioReportExportResult:
        task = self._start_task(project_id=project_id, source_paths=source_paths)
        validation_error = self._validate(source_paths)
        if validation_error is not None:
            result = BioReportExportResult(
                success=False,
                project_id=project_id,
                source_paths=source_paths,
                source_count=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        resolved_paths = [Path(path).expanduser().resolve() for path in source_paths if path.strip()]
        try:
            summaries = self._adapter.summarize_sources(resolved_paths)
            output_path = self._write_report(project_id, summaries)
            result = BioReportExportResult(
                success=True,
                project_id=project_id,
                source_paths=[str(path) for path in resolved_paths],
                source_count=len(summaries),
                output_path=str(output_path),
                message=f"生信测试报告摘要已导出：{len(summaries)} 个来源文件。",
                details={"formal_report_executed": False, "source_kinds": [summary.source_kind for summary in summaries]},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="bioinformatics_report_summary",
                source_path=";".join(str(path) for path in resolved_paths),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = BioReportExportResult(
                success=False,
                project_id=project_id,
                source_paths=[str(path) for path in resolved_paths],
                source_count=0,
                output_path="",
                message="生信测试报告摘要导出失败，请确认输入为 Bioinformatics 工作台生成的 JSON 文件。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, source_paths: list[str]) -> str | None:
        clean_paths = [path.strip() for path in source_paths if path.strip()]
        if not clean_paths:
            return "请至少选择一个 Bioinformatics 预检 JSON 文件。"
        for source_path in clean_paths:
            path = Path(source_path).expanduser()
            if not path.exists():
                return f"报告来源文件不存在：{source_path}"
            if path.suffix.lower() != ".json":
                return "生信测试报告摘要需要 JSON 输入。"
        return None

    def _start_task(self, *, project_id: str, source_paths: list[str]) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.REPORT_EXPORT,
            module="bioinformatics",
            title="Bioinformatics Test Report Export",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Exporting bioinformatics test summary from {len(source_paths)} source(s)",
        )

    def _finish_task(self, task: TaskRecord, result: BioReportExportResult) -> None:
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

    def _write_report(self, project_id: str, summaries: list[BioReportSourceSummary]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"bioinformatics_test_summary_{uuid4().hex[:12]}.md"
        lines = [
            "# Bioinformatics Test Summary",
            "",
            f"- Project ID: `{project_id}`",
            f"- Created At: `{datetime.now(timezone.utc).isoformat()}`",
            "- Formal analysis executed: `false`",
            "- Intended use: testing summary only",
            "",
            "| Source | Type | Dataset Count | Completed Execution |",
            "| --- | --- | ---: | --- |",
        ]
        for summary in summaries:
            lines.append(
                f"| `{summary.source_path}` | `{summary.source_kind}` | {summary.dataset_count} | `{str(summary.completed_execution).lower()}` |"
            )
        lines.append("")
        lines.append("This file does not contain formal differential expression, enrichment, correlation, or survival results.")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
