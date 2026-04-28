from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.duplicate_review_adapter import DuplicateReviewAdapter
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class DuplicateReviewResult:
    success: bool
    project_id: str
    source_path: str
    total_records: int
    duplicate_group_count: int
    candidate_record_count: int
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class DuplicateReviewService:
    def __init__(
        self,
        *,
        adapter: DuplicateReviewAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._adapter = adapter or DuplicateReviewAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def review(self, *, project_id: str, screening_ready_path: str) -> DuplicateReviewResult:
        task = self._start_task(project_id=project_id, source_path=screening_ready_path)
        validation_error = self._validate(screening_ready_path)
        if validation_error is not None:
            result = DuplicateReviewResult(
                success=False,
                project_id=project_id,
                source_path=screening_ready_path,
                total_records=0,
                duplicate_group_count=0,
                candidate_record_count=0,
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        source_path = Path(screening_ready_path).expanduser().resolve()
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            records = list(payload.get("records", []))
            batch_id = str(payload.get("batch_id", f"batch-{uuid4().hex[:12]}"))
            groups = self._adapter.identify_duplicate_groups(project_id=project_id, records=records)
            output_path = self._write_output(project_id, batch_id, source_path, groups)
            candidate_record_ids = {
                record_id
                for group in groups
                for record_id in group.candidate_record_ids
            }
            result = DuplicateReviewResult(
                success=True,
                project_id=project_id,
                source_path=str(source_path),
                total_records=len(records),
                duplicate_group_count=len(groups),
                candidate_record_count=len(candidate_record_ids),
                output_path=str(output_path),
                message=f"Duplicate Review 完成：发现 {len(groups)} 组重复候选。",
                details={
                    "batch_id": batch_id,
                    "preview_group_ids": [group.duplicate_group_id for group in groups[:5]],
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="duplicate_candidate_groups",
                source_path=str(source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = DuplicateReviewResult(
                success=False,
                project_id=project_id,
                source_path=str(source_path),
                total_records=0,
                duplicate_group_count=0,
                candidate_record_count=0,
                output_path="",
                message="Duplicate Review 失败，请确认输入来自 Prepare for Screening。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _validate(self, screening_ready_path: str) -> str | None:
        if not screening_ready_path.strip():
            return "请选择 Prepare for Screening 生成的 JSON 文件。"
        path = Path(screening_ready_path).expanduser()
        if not path.exists():
            return "筛选准备文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "Duplicate Review 需要 Prepare for Screening 生成的 JSON 文件。"
        return None

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.DUPLICATE_REVIEW,
            module="meta_analysis",
            title="Duplicate Review",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Reviewing duplicate candidates from {source_path}" if source_path else "Waiting for screening-ready records",
        )

    def _finish_task(self, task: TaskRecord, result: DuplicateReviewResult) -> None:
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

    def _write_output(self, project_id: str, batch_id: str, source_path: Path, groups: list[object]) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "duplicate_review"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_duplicate_groups.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "duplicate_groups": [asdict(group) for group in groups],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

