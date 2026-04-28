from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.literature_import_adapter import LiteratureImportAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


SUPPORTED_EXTENSIONS = {".nbib": "nbib", ".ris": "ris", ".csv": "csv"}


@dataclass(frozen=True)
class ImportResult:
    success: bool
    source_path: str
    source_type: str
    total_records: int
    imported_records: int
    skipped_records: int
    error_count: int
    output_path: str
    message: str
    details: dict[str, object] = field(default_factory=dict)


class LiteratureImportService:
    def __init__(
        self,
        *,
        adapter: LiteratureImportAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or LiteratureImportAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def import_file(self, *, project_id: str, source_path: str) -> ImportResult:
        validation_error = self._validate_source_path(source_path)
        source_type = self._source_type(source_path) if source_path else ""
        task = self._start_task(project_id=project_id, source_path=source_path)
        if validation_error is not None:
            result = ImportResult(
                success=False,
                source_path=source_path,
                source_type=source_type,
                total_records=0,
                imported_records=0,
                skipped_records=0,
                error_count=1,
                output_path="",
                message=validation_error,
                details={},
            )
            self._finish_task(task, result)
            return result

        path = Path(source_path).expanduser().resolve()
        try:
            adapter_result = self._adapter.parse_file(path, project_id, source_type)
            output_path = self._write_output(project_id, adapter_result.batch_id, path, source_type, adapter_result.records)
            result = ImportResult(
                success=True,
                source_path=str(path),
                source_type=source_type,
                total_records=len(adapter_result.records),
                imported_records=len(adapter_result.records),
                skipped_records=0,
                error_count=0,
                output_path=str(output_path),
                message=f"导入完成：{len(adapter_result.records)} 条文献记录。",
                details={
                    "batch_id": adapter_result.batch_id,
                    "preview_titles": [record.title for record in adapter_result.records[:5]],
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="literature_records",
                source_path=str(path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = ImportResult(
                success=False,
                source_path=str(path),
                source_type=source_type,
                total_records=0,
                imported_records=0,
                skipped_records=0,
                error_count=1,
                output_path="",
                message="文献导入失败，请检查文件格式或内容后重试。",
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate_source_path(self, source_path: str) -> str | None:
        if not source_path.strip():
            return "请选择要导入的 NBIB、RIS 或 CSV 文件。"
        path = Path(source_path).expanduser()
        if not path.exists():
            return "文件不存在，请检查路径。"
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return "暂不支持该文件类型；请选择 .nbib、.ris 或 .csv 文件。"
        return None

    def _source_type(self, source_path: str) -> str:
        return SUPPORTED_EXTENSIONS.get(Path(source_path).suffix.lower(), "")

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.LITERATURE_IMPORT,
            module="meta_analysis",
            title="Literature Import",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Importing {source_path}" if source_path else "Waiting for source file",
        )

    def _finish_task(self, task: TaskRecord, result: ImportResult) -> None:
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
        project_id: str,
        batch_id: str,
        source_path: Path,
        source_type: str,
        records: list[object],
    ) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "literature_import"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_records.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(source_path),
            "source_type": source_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "records": [asdict(record) for record in records],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

