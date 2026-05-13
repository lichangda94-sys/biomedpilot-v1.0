from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.analysis_adapter import AnalysisAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class AnalysisPreflightResult:
    success: bool
    project_id: str
    source_path: str
    extraction_records: int
    outcome_records: int
    valid_outcome_records: int
    runnable: bool
    blocking_errors: list[str]
    warnings: list[str]
    recommended_action: str
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class AnalysisPreflightService:
    def __init__(
        self,
        *,
        adapter: AnalysisAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or AnalysisAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def run_preflight(self, *, project_id: str, extraction_pool_path: str) -> AnalysisPreflightResult:
        task = self._start_task(project_id=project_id, source_path=extraction_pool_path)
        validation_error = self._validate(extraction_pool_path)
        if validation_error is not None:
            result = AnalysisPreflightResult(
                success=False,
                project_id=project_id,
                source_path=extraction_pool_path,
                extraction_records=0,
                outcome_records=0,
                valid_outcome_records=0,
                runnable=False,
                blocking_errors=[validation_error],
                warnings=[],
                recommended_action="select_valid_extraction_pool",
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(extraction_pool_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if "extraction_records" not in payload:
                raise ValueError("Analysis 预检需要 Extraction 生成的 JSON 文件。")
            batch_id = str(payload.get("batch_id", f"batch-{uuid4().hex[:12]}"))
            readiness = self._adapter.evaluate_extraction_pool(payload)
            output_path = self._write_output(project_id, batch_id, source_path, readiness)
            message = (
                "Analysis 预检通过：数据结构已满足最小统计运行条件。"
                if readiness.runnable
                else "Analysis 预检完成：暂不能运行统计分析，请先处理阻断项。"
            )
            result = AnalysisPreflightResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                extraction_records=readiness.extraction_records,
                outcome_records=readiness.outcome_records,
                valid_outcome_records=readiness.valid_outcome_records,
                runnable=readiness.runnable,
                blocking_errors=list(readiness.blocking_errors),
                warnings=list(readiness.warnings),
                recommended_action=readiness.recommended_action,
                output_path=str(output_path),
                message=message,
                details={"batch_id": batch_id, "outcome_type_counts": dict(readiness.outcome_type_counts)},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="analysis_preflight",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = AnalysisPreflightResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                extraction_records=0,
                outcome_records=0,
                valid_outcome_records=0,
                runnable=False,
                blocking_errors=["analysis_preflight_failed"],
                warnings=[],
                recommended_action="select_valid_extraction_pool",
                output_path="",
                message="Analysis 预检失败，请确认输入来自 Extraction 输出。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, extraction_pool_path: str) -> str | None:
        if not extraction_pool_path.strip():
            return "请选择 Extraction 生成的 JSON 文件。"
        path = Path(extraction_pool_path).expanduser()
        if not path.exists():
            return "Extraction 文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "Analysis 预检需要 Extraction 生成的 JSON 文件。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.ANALYSIS,
            module="meta_analysis",
            title="Analysis Preflight",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Checking analysis readiness from {source_path}" if source_path else "Waiting for extraction pool",
        )

    def _finish_task(self, task: TaskRecord, result: AnalysisPreflightResult) -> None:
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

    def _write_output(self, project_id: str, batch_id: str, source_path: Path, readiness: object) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_analysis_preflight.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "preflight": asdict(readiness),
            "statistical_analysis_executed": False,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
