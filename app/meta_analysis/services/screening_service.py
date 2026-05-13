from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.adapters.screening_adapter import ScreeningAdapter, ScreeningQueueRecord
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class ScreeningQueueResult:
    success: bool
    project_id: str
    source_path: str
    total_records: int
    queued_records: int
    decision_counts: dict[str, int]
    output_path: str
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ScreeningDecisionUpdateResult:
    success: bool
    project_id: str
    queue_path: str
    screening_record_id: str
    decision: str
    decision_counts: dict[str, int]
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class ScreeningService:
    def __init__(
        self,
        *,
        adapter: ScreeningAdapter | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._adapter = adapter or ScreeningAdapter()
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()
        self._audit_log = audit_log or MetaAuditLogService()

    def create_queue(self, *, project_id: str, source_path: str) -> ScreeningQueueResult:
        task = self._start_task(project_id=project_id, source_path=source_path)
        validation_error = self._validate(source_path)
        if validation_error is not None:
            result = ScreeningQueueResult(
                success=False,
                project_id=project_id,
                source_path=source_path,
                total_records=0,
                queued_records=0,
                decision_counts={},
                output_path="",
                message=validation_error,
                error_count=1,
            )
            self._finish_task(task, result)
            return result

        resolved_source_path = Path(source_path).expanduser().resolve()
        try:
            records, duplicate_groups, batch_id, normalized_source_path = self._load_source(resolved_source_path)
            queue_records = self._adapter.create_title_abstract_queue(
                project_id=project_id,
                records=records,
                duplicate_groups=duplicate_groups,
            )
            output_path = self._write_output(
                project_id=project_id,
                batch_id=batch_id,
                source_path=resolved_source_path,
                normalized_source_path=normalized_source_path,
                queue_records=queue_records,
            )
            decision_counts = self._decision_counts(queue_records)
            result = ScreeningQueueResult(
                success=True,
                project_id=project_id,
                source_path=str(resolved_source_path),
                total_records=len(records),
                queued_records=len(queue_records),
                decision_counts=decision_counts,
                output_path=str(output_path),
                message=f"Screening 队列已生成：{len(queue_records)} 条记录等待标题摘要筛选。",
                details={
                    "batch_id": batch_id,
                    "stage": "title_abstract_screening",
                    "duplicate_groups_used": len(duplicate_groups),
                    "normalized_source_path": str(normalized_source_path),
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="screening_queue",
                source_path=str(resolved_source_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = ScreeningQueueResult(
                success=False,
                project_id=project_id,
                source_path=str(resolved_source_path),
                total_records=0,
                queued_records=0,
                decision_counts={},
                output_path="",
                message="Screening 队列生成失败，请确认输入来自 Prepare for Screening 或 Duplicate Review。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def update_decision(
        self,
        *,
        project_id: str,
        queue_path: str,
        screening_record_id: str,
        decision: str,
        exclusion_reason_text: str = "",
        reviewer_id: str = "",
        notes: str = "",
    ) -> ScreeningDecisionUpdateResult:
        task = self._start_decision_task(
            project_id=project_id,
            queue_path=queue_path,
            screening_record_id=screening_record_id,
        )
        validation_error = self._validate_decision_input(
            queue_path=queue_path,
            screening_record_id=screening_record_id,
            decision=decision,
            exclusion_reason_text=exclusion_reason_text,
        )
        if validation_error is not None:
            result = ScreeningDecisionUpdateResult(
                success=False,
                project_id=project_id,
                queue_path=queue_path,
                screening_record_id=screening_record_id,
                decision=decision,
                decision_counts={},
                message=validation_error,
                error_count=1,
            )
            self._finish_decision_task(task, result)
            return result

        resolved_queue_path = Path(queue_path).expanduser().resolve()
        normalized_decision = decision.strip().lower()
        try:
            payload = json.loads(resolved_queue_path.read_text(encoding="utf-8"))
            records = list(payload.get("screening_records", []))
            updated = False
            for record in records:
                if str(record.get("screening_record_id", "")) != screening_record_id:
                    continue
                record["decision"] = normalized_decision
                record["exclusion_reason_text"] = exclusion_reason_text.strip() if normalized_decision == "excluded" else ""
                record["reviewer_id"] = reviewer_id.strip() or None
                record["notes"] = notes.strip()
                record["decided_at"] = datetime.now(timezone.utc).isoformat() if normalized_decision != "pending" else None
                updated = True
                break
            if not updated:
                raise ValueError("Screening record not found.")

            payload["screening_records"] = records
            payload["decision_counts"] = self._decision_counts_from_dicts(records)
            payload["updated_at"] = datetime.now(timezone.utc).isoformat()
            resolved_queue_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            result = ScreeningDecisionUpdateResult(
                success=True,
                project_id=project_id,
                queue_path=str(resolved_queue_path),
                screening_record_id=screening_record_id,
                decision=normalized_decision,
                decision_counts=dict(payload["decision_counts"]),
                message=f"Screening 决策已保存：{screening_record_id} → {normalized_decision}。",
                details={"updated_record_id": screening_record_id},
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="screening_decisions",
                source_path=str(resolved_queue_path),
                output_path=str(resolved_queue_path),
                status="available",
            )
            self._finish_decision_task(task, result)
            self._audit_log.record_event(
                self._project_dir(project_id),
                event_type="screening_decision",
                project_id=project_id,
                target_type="screening_record",
                target_id=screening_record_id,
                source_path=str(resolved_queue_path),
                output_path=str(resolved_queue_path),
                summary=f"Screening decision saved: {normalized_decision}",
                details={"reviewer_id": reviewer_id, "exclusion_reason_text": exclusion_reason_text},
            )
            return result
        except Exception as exc:
            result = ScreeningDecisionUpdateResult(
                success=False,
                project_id=project_id,
                queue_path=str(resolved_queue_path),
                screening_record_id=screening_record_id,
                decision=normalized_decision,
                decision_counts={},
                message="Screening 决策保存失败，请确认记录 ID 来自当前 Screening 队列。",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_decision_task(task, result)
            return result

    def _validate(self, source_path: str) -> str | None:
        if not source_path.strip():
            return "请选择 Prepare for Screening 或 Duplicate Review 生成的 JSON 文件。"
        path = Path(source_path).expanduser()
        if not path.exists():
            return "筛选来源文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "Screening 需要 Prepare for Screening 或 Duplicate Review 生成的 JSON 文件。"
        return None

    def _validate_decision_input(
        self,
        *,
        queue_path: str,
        screening_record_id: str,
        decision: str,
        exclusion_reason_text: str,
    ) -> str | None:
        if not queue_path.strip():
            return "请选择 Screening 队列 JSON 文件。"
        path = Path(queue_path).expanduser()
        if not path.exists():
            return "Screening 队列文件不存在，请检查路径。"
        if path.suffix.lower() != ".json":
            return "Screening 决策需要 JSON 队列文件。"
        if not screening_record_id.strip():
            return "请输入要更新的 screening_record_id。"
        normalized_decision = decision.strip().lower()
        if normalized_decision not in {"pending", "included", "excluded", "maybe"}:
            return "决策值必须是 pending、included、excluded 或 maybe。"
        if normalized_decision == "excluded" and not exclusion_reason_text.strip():
            return "选择 excluded 时需要填写排除原因。"
        return None

    def _load_source(self, source_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], str, Path]:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        batch_id = str(payload.get("batch_id", f"batch-{uuid4().hex[:12]}"))
        if "records" in payload:
            return list(payload.get("records", [])), [], batch_id, source_path

        if "duplicate_groups" in payload:
            normalized_source_path = Path(str(payload.get("source_path", ""))).expanduser()
            if not normalized_source_path.exists():
                raise ValueError("Duplicate Review 输出缺少可读取的 Prepare for Screening 来源路径。")
            normalized_payload = json.loads(normalized_source_path.read_text(encoding="utf-8"))
            return (
                list(normalized_payload.get("records", [])),
                list(payload.get("duplicate_groups", [])),
                batch_id,
                normalized_source_path.resolve(),
            )

        raise ValueError("JSON 文件不包含可识别的 records 或 duplicate_groups。")

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.SCREENING,
            module="meta_analysis",
            title="Screening",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Creating screening queue from {source_path}" if source_path else "Waiting for screening source",
        )

    def _start_decision_task(self, *, project_id: str, queue_path: str, screening_record_id: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.SCREENING_DECISION,
            module="meta_analysis",
            title="Screening Decision",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Updating {screening_record_id} in {queue_path}" if queue_path else "Waiting for screening decision input",
        )

    def _finish_task(self, task: TaskRecord, result: ScreeningQueueResult) -> None:
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

    def _finish_decision_task(self, task: TaskRecord, result: ScreeningDecisionUpdateResult) -> None:
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

    def _project_dir(self, project_id: str) -> Path:
        return self._storage_root / "projects" / project_id / "meta_analysis"

    def _write_output(
        self,
        *,
        project_id: str,
        batch_id: str,
        source_path: Path,
        normalized_source_path: Path,
        queue_records: list[ScreeningQueueRecord],
    ) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "screening"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_screening_queue.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(source_path),
            "normalized_source_path": str(normalized_source_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": "title_abstract_screening",
            "screening_records": [asdict(record) for record in queue_records],
            "decision_counts": self._decision_counts(queue_records),
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _decision_counts(self, queue_records: list[ScreeningQueueRecord]) -> dict[str, int]:
        counts: dict[str, int] = {"pending": 0, "included": 0, "excluded": 0, "maybe": 0}
        for record in queue_records:
            counts[record.decision] = counts.get(record.decision, 0) + 1
        counts["total"] = len(queue_records)
        return counts

    def _decision_counts_from_dicts(self, queue_records: list[dict[str, object]]) -> dict[str, int]:
        counts: dict[str, int] = {"pending": 0, "included": 0, "excluded": 0, "maybe": 0}
        for record in queue_records:
            decision = str(record.get("decision", "pending")).lower()
            counts[decision] = counts.get(decision, 0) + 1
        counts["total"] = len(queue_records)
        return counts
