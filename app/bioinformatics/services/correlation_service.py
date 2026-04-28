from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.adapters.correlation_adapter import CorrelationAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class CorrelationPreflightResult:
    success: bool
    project_id: str
    source_path: str
    dataset_count: int
    ready_for_correlation_count: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class CorrelationService:
    def __init__(
        self,
        *,
        adapter: CorrelationAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or CorrelationAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_preflight(self, *, project_id: str, cleaning_plan_path: str) -> CorrelationPreflightResult:
        task = self._start_task(project_id=project_id, source_path=cleaning_plan_path)
        validation_error = self._validate(cleaning_plan_path)
        if validation_error is not None:
            result = CorrelationPreflightResult(
                success=False,
                project_id=project_id,
                source_path=cleaning_plan_path,
                dataset_count=0,
                ready_for_correlation_count=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(cleaning_plan_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if "cleaning_items" not in payload:
                raise ValueError("相关性分析预检需要数据清洗计划。")
            items = self._adapter.build_preflight(payload)
            ready_count = sum(1 for item in items if item.status == "ready_for_correlation_setup")
            output_path = self._write_output(project_id, source_path, items)
            result = CorrelationPreflightResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                dataset_count=len(items),
                ready_for_correlation_count=ready_count,
                output_path=str(output_path),
                message=f"相关性分析预检已生成：{ready_count}/{len(items)} 个数据集具备设置前置条件。",
                details={"correlation_executed": False, "network_used": False},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="bioinformatics",
                data_type="geo_correlation_preflight",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = CorrelationPreflightResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                dataset_count=0,
                ready_for_correlation_count=0,
                output_path="",
                message="相关性分析预检失败，请确认输入来自数据清洗计划。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, cleaning_plan_path: str) -> str | None:
        if not cleaning_plan_path.strip():
            return "请选择数据清洗计划 JSON 文件。"
        path = Path(cleaning_plan_path).expanduser()
        if not path.exists():
            return "数据清洗计划文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "相关性分析预检需要 JSON 输入。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.ANALYSIS,
            module="bioinformatics",
            title="Correlation Preflight",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating correlation preflight from {source_path}" if source_path else "Waiting for cleaning plan",
        )

    def _finish_task(self, task: TaskRecord, result: CorrelationPreflightResult) -> None:
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

    def _write_output(self, project_id: str, source_path: Path, items: list[object]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "bioinformatics" / "correlation"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"geo_correlation_preflight_{uuid4().hex[:12]}.json"
        payload = {
            "project_id": project_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "correlation_executed": False,
            "network_used": False,
            "preflight_items": [asdict(item) for item in items],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
