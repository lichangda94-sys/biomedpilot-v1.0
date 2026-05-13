from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.extraction_adapter import ExtractionAdapter, ExtractionPoolRecord
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class ExtractionPoolResult:
    success: bool
    project_id: str
    source_path: str
    total_screening_records: int
    included_records: int
    extraction_records: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class ExtractionService:
    def __init__(
        self,
        *,
        adapter: ExtractionAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or ExtractionAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def create_pool(self, *, project_id: str, screening_queue_path: str) -> ExtractionPoolResult:
        task = self._start_task(project_id=project_id, source_path=screening_queue_path)
        validation_error = self._validate(screening_queue_path)
        if validation_error is not None:
            result = ExtractionPoolResult(
                success=False,
                project_id=project_id,
                source_path=screening_queue_path,
                total_screening_records=0,
                included_records=0,
                extraction_records=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(screening_queue_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            screening_records = list(payload.get("screening_records", []))
            batch_id = str(payload.get("batch_id", f"batch-{uuid4().hex[:12]}"))
            included_count = sum(
                1 for record in screening_records if str(record.get("decision", "")).lower() == "included"
            )
            extraction_records = self._adapter.create_extraction_pool(
                project_id=project_id,
                screening_records=screening_records,
            )
            output_path = self._write_output(
                project_id=project_id,
                batch_id=batch_id,
                source_path=source_path,
                extraction_records=extraction_records,
            )
            message = (
                f"Extraction 提取池已生成：{len(extraction_records)} 条记录。"
                if extraction_records
                else "Extraction 提取池已生成，但当前没有 included 记录；请先完成人工筛选决策。"
            )
            result = ExtractionPoolResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                total_screening_records=len(screening_records),
                included_records=included_count,
                extraction_records=len(extraction_records),
                output_path=str(output_path),
                message=message,
                details={
                    "batch_id": batch_id,
                    "source_stage": payload.get("stage", ""),
                    "manual_data_entry_enabled": False,
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="extraction_pool",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = ExtractionPoolResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                total_screening_records=0,
                included_records=0,
                extraction_records=0,
                output_path="",
                message="Extraction 提取池生成失败，请确认输入来自 Screening 队列输出。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, screening_queue_path: str) -> str | None:
        if not screening_queue_path.strip():
            return "请选择 Screening 生成的 JSON 队列文件。"
        path = Path(screening_queue_path).expanduser()
        if not path.exists():
            return "Screening 队列文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "Extraction 需要 Screening 生成的 JSON 文件。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.EXTRACTION,
            module="meta_analysis",
            title="Extraction",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating extraction pool from {source_path}" if source_path else "Waiting for screening queue",
        )

    def _finish_task(self, task: TaskRecord, result: ExtractionPoolResult) -> None:
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

    def _write_output(
        self,
        *,
        project_id: str,
        batch_id: str,
        source_path: Path,
        extraction_records: list[ExtractionPoolRecord],
    ) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "extraction"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_extraction_pool.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "manual_data_entry_enabled": False,
            "extraction_records": [asdict(record) for record in extraction_records],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
