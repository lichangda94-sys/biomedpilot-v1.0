from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.prepare_screening_adapter import PrepareScreeningAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class PrepareScreeningResult:
    success: bool
    project_id: str
    source_path: str
    total_records: int
    prepared_records: int
    skipped_records: int
    error_count: int
    output_path: str
    message: str
    details: dict[str, object] = field(default_factory=dict)


class PrepareScreeningService:
    def __init__(
        self,
        *,
        adapter: PrepareScreeningAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or PrepareScreeningAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def prepare(self, *, project_id: str, import_output_path: str) -> PrepareScreeningResult:
        task = self._start_task(project_id=project_id, source_path=import_output_path)
        validation_error = self._validate(import_output_path)
        if validation_error is not None:
            result = PrepareScreeningResult(
                success=False,
                project_id=project_id,
                source_path=import_output_path,
                total_records=0,
                prepared_records=0,
                skipped_records=0,
                error_count=1,
                output_path="",
                message=validation_error,
                details={},
            )
            self._finish_task(task, result)
            return result

        source_path = Path(import_output_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            records = list(payload.get("records", []))
            batch_id = str(payload.get("batch_id", f"batch-{uuid4().hex[:12]}"))
            source_type = str(payload.get("source_type", "unknown"))
            ready_records = self._adapter.normalize_records(
                project_id=project_id,
                batch_id=batch_id,
                source_type=source_type,
                records=records,
            )
            output_path = self._write_output(project_id, batch_id, source_path, ready_records)
            result = PrepareScreeningResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                total_records=len(records),
                prepared_records=len(ready_records),
                skipped_records=max(len(records) - len(ready_records), 0),
                error_count=0,
                output_path=str(output_path),
                message=f"筛选准备完成：{len(ready_records)} 条文献记录已标准化。",
                details={
                    "batch_id": batch_id,
                    "preview_titles": [record.title for record in ready_records[:5]],
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="screening_ready_records",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = PrepareScreeningResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                total_records=0,
                prepared_records=0,
                skipped_records=0,
                error_count=1,
                output_path="",
                message="筛选准备失败，请确认导入结果文件来自 Literature Import。",
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, import_output_path: str) -> str | None:
        if not import_output_path.strip():
            return "请选择 Literature Import 生成的结果文件。"
        path = Path(import_output_path).expanduser()
        if not path.exists():
            return "导入结果文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "筛选准备需要 Literature Import 生成的 JSON 结果文件。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.PREPARE_SCREENING,
            module="meta_analysis",
            title="Prepare for Screening",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Preparing screening records from {source_path}" if source_path else "Waiting for import output",
        )

    def _finish_task(self, task: TaskRecord, result: PrepareScreeningResult) -> None:
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

    def _write_output(self, project_id: str, batch_id: str, source_path: Path, records: list[object]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "prepare_screening"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_screening_ready.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "records": [asdict(record) for record in records],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
