from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.dedup import (
    DedupDecision,
    DedupDecisionType,
    DedupResult,
    DuplicateGroup,
    DuplicateGroupStatus,
)
from app.shared.data_center.service import DataCenter
from app.shared.storage import default_storage_root
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class DedupDecisionService:
    def __init__(
        self,
        *,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()

    def load_groups(self, *, duplicate_review_path: str) -> list[DuplicateGroup]:
        review_path = self._resolve_review_path(duplicate_review_path)
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
        records = self._load_source_records(review_payload)
        records_by_id = {str(record.get("record_id", "")): record for record in records}
        decisions = self._load_decisions(self._decisions_path(review_path))

        groups: list[DuplicateGroup] = []
        for raw_group in list(review_payload.get("duplicate_groups", [])):
            group_id = str(raw_group.get("group_id") or raw_group.get("duplicate_group_id", ""))
            record_ids = [
                str(record_id)
                for record_id in list(raw_group.get("candidate_record_ids", []))
            ]
            group_records = list(raw_group.get("records", []))
            if not group_records:
                group_records = [records_by_id[record_id] for record_id in record_ids if record_id in records_by_id]
            latest_decision = decisions.get(group_id)
            status = DuplicateGroupStatus.PENDING.value
            if latest_decision is not None:
                status = (
                    DuplicateGroupStatus.SKIPPED.value
                    if latest_decision.decision == DedupDecisionType.SKIP.value
                    else DuplicateGroupStatus.RESOLVED.value
                )
            groups.append(
                DuplicateGroup(
                    group_id=group_id,
                    records=[dict(record) for record in group_records],
                    match_reason=str(raw_group.get("match_reason", "")),
                    confidence=float(raw_group.get("confidence", 0.0) or 0.0),
                    status=status,
                )
            )
        return groups

    def save_decision(
        self,
        *,
        duplicate_review_path: str,
        group_id: str,
        decision: str,
        note: str = "",
        merged_record: dict[str, object] | None = None,
    ) -> DedupDecision:
        review_path = self._resolve_review_path(duplicate_review_path)
        groups = {group.group_id: group for group in self.load_groups(duplicate_review_path=str(review_path))}
        if group_id not in groups:
            raise ValueError("未找到指定的重复候选组。")

        normalized_decision = self._normalize_decision(decision)
        group = groups[group_id]
        selected_record_id = self._selected_record_id(group, normalized_decision)
        final_merged_record: dict[str, object] = {}
        if normalized_decision == DedupDecisionType.MERGE:
            final_merged_record = dict(merged_record or self._merge_records(group))

        dedup_decision = DedupDecision(
            decision_id=f"dedup-decision-{uuid4().hex[:12]}",
            group_id=group_id,
            decision=normalized_decision.value,
            selected_record_id=selected_record_id,
            merged_record=final_merged_record,
            note=note.strip(),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._write_decision(review_path, dedup_decision)
        return dedup_decision

    def generate_deduplicated_literature(self, *, project_id: str, duplicate_review_path: str) -> DedupResult:
        task = self._start_task(project_id=project_id, source_path=duplicate_review_path)
        try:
            review_path = self._resolve_review_path(duplicate_review_path)
            review_payload = json.loads(review_path.read_text(encoding="utf-8"))
            records = self._load_source_records(review_payload)
            groups = self.load_groups(duplicate_review_path=str(review_path))
            decisions_path = self._decisions_path(review_path)
            decisions = self._load_decisions(decisions_path)
            deduplicated_records, excluded_records, unresolved_group_ids = self._apply_decisions(records, groups, decisions)
            output_path = self._write_result(
                project_id=project_id,
                review_path=review_path,
                batch_id=str(review_payload.get("batch_id", f"batch-{uuid4().hex[:12]}")),
                records=deduplicated_records,
                excluded_records=excluded_records,
                unresolved_group_ids=unresolved_group_ids,
                decisions_path=decisions_path,
            )
            resolved_count = len([decision for decision in decisions.values() if decision.decision != DedupDecisionType.SKIP.value])
            result = DedupResult(
                project_id=project_id,
                original_count=len(records),
                duplicate_group_count=len(groups),
                resolved_group_count=resolved_count,
                unique_count=len(deduplicated_records),
                output_path=str(output_path),
                decisions_path=str(decisions_path),
                message=f"去重文献库已生成：{len(deduplicated_records)} 条记录。",
                details={
                    "excluded_record_count": len(excluded_records),
                    "unresolved_group_ids": unresolved_group_ids,
                },
            )
            self._data_center.register_asset(
                project_id=project_id,
                module="meta_analysis",
                data_type="deduplicated_literature",
                source_path=str(review_path),
                output_path=str(output_path),
                status="available",
            )
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = DedupResult(
                project_id=project_id,
                original_count=0,
                duplicate_group_count=0,
                resolved_group_count=0,
                unique_count=0,
                output_path="",
                decisions_path="",
                message="生成去重文献库失败，请确认输入来自 Duplicate Review。",
                success=False,
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_task(task, result)
            return result

    def _apply_decisions(
        self,
        records: list[dict[str, object]],
        groups: list[DuplicateGroup],
        decisions: dict[str, DedupDecision],
    ) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
        records_by_id = {str(record.get("record_id", "")): dict(record) for record in records}
        removed_ids: set[str] = set()
        replacement_records: list[dict[str, object]] = []
        excluded_records: list[dict[str, object]] = []
        unresolved_group_ids: list[str] = []

        for group in groups:
            decision = decisions.get(group.group_id)
            group_ids = [str(record.get("record_id", "")) for record in group.records if record.get("record_id")]
            if decision is None or decision.decision == DedupDecisionType.SKIP.value:
                unresolved_group_ids.append(group.group_id)
                continue
            if decision.decision == DedupDecisionType.MARK_NOT_DUPLICATE.value:
                continue
            if decision.decision == DedupDecisionType.MERGE.value:
                removed_ids.update(group_ids)
                replacement_records.append(dict(decision.merged_record or self._merge_records(group)))
                excluded_records.extend(self._excluded_records(group, kept_record_id=""))
                continue

            kept_id = decision.selected_record_id
            removed_ids.update(record_id for record_id in group_ids if record_id != kept_id)
            excluded_records.extend(self._excluded_records(group, kept_record_id=kept_id))

        deduplicated_records = [
            record
            for record_id, record in records_by_id.items()
            if record_id not in removed_ids
        ]
        deduplicated_records.extend(replacement_records)
        return deduplicated_records, excluded_records, unresolved_group_ids

    def _excluded_records(self, group: DuplicateGroup, *, kept_record_id: str) -> list[dict[str, object]]:
        excluded: list[dict[str, object]] = []
        for record in group.records:
            record_id = str(record.get("record_id", ""))
            if kept_record_id and record_id == kept_record_id:
                continue
            marked = dict(record)
            marked["dedup_status"] = "duplicate_excluded"
            marked["duplicate_group_id"] = group.group_id
            excluded.append(marked)
        return excluded

    def _merge_records(self, group: DuplicateGroup) -> dict[str, object]:
        merged: dict[str, object] = {"record_id": f"merged-{group.group_id}", "dedup_status": "deduplicated_merged"}
        for record in group.records:
            for key, value in record.items():
                if key == "record_id":
                    continue
                if isinstance(value, list):
                    existing = list(merged.get(key, [])) if isinstance(merged.get(key), list) else []
                    for item in value:
                        if item not in existing:
                            existing.append(item)
                    if existing:
                        merged[key] = existing
                    continue
                if key not in merged and value not in ("", None, []):
                    merged[key] = value
        merged["merged_from_record_ids"] = [str(record.get("record_id", "")) for record in group.records]
        return merged

    def _selected_record_id(self, group: DuplicateGroup, decision: DedupDecisionType) -> str:
        if decision == DedupDecisionType.KEEP_FIRST:
            return str(group.records[0].get("record_id", "")) if group.records else ""
        if decision == DedupDecisionType.KEEP_SECOND:
            if len(group.records) < 2:
                raise ValueError("keep_second 需要至少两条候选记录。")
            return str(group.records[1].get("record_id", ""))
        return ""

    def _normalize_decision(self, decision: str) -> DedupDecisionType:
        try:
            return DedupDecisionType(decision.strip().lower())
        except ValueError as exc:
            raise ValueError("去重决策必须是 keep_first、keep_second、merge、mark_not_duplicate 或 skip。") from exc

    def _resolve_review_path(self, duplicate_review_path: str) -> Path:
        if not duplicate_review_path.strip():
            raise ValueError("请选择 Duplicate Review 生成的 JSON 文件。")
        path = Path(duplicate_review_path).expanduser()
        if not path.exists():
            raise ValueError("Duplicate Review 文件不存在，请检查路径。")
        if path.suffix.lower() != ".json":
            raise ValueError("Dedup 决策需要 Duplicate Review 生成的 JSON 文件。")
        return path.resolve()

    def _load_source_records(self, review_payload: dict[str, object]) -> list[dict[str, object]]:
        source_path = Path(str(review_payload.get("source_path", ""))).expanduser()
        if not source_path.exists():
            raise ValueError("Duplicate Review 输出缺少可读取的 Prepare for Screening 来源路径。")
        source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        return [dict(record) for record in list(source_payload.get("records", []))]

    def _decisions_path(self, review_path: Path) -> Path:
        return review_path.with_name(review_path.name.replace("_duplicate_groups.json", "_dedup_decisions.json"))

    def _load_decisions(self, decisions_path: Path) -> dict[str, DedupDecision]:
        if not decisions_path.exists():
            return {}
        payload = json.loads(decisions_path.read_text(encoding="utf-8"))
        decisions: dict[str, DedupDecision] = {}
        for item in list(payload.get("decisions", [])):
            decision = DedupDecision(
                decision_id=str(item.get("decision_id", "")),
                group_id=str(item.get("group_id", "")),
                decision=str(item.get("decision", "")),
                selected_record_id=str(item.get("selected_record_id", "")),
                merged_record=dict(item.get("merged_record", {})),
                note=str(item.get("note", "")),
                created_at=str(item.get("created_at", "")),
            )
            decisions[decision.group_id] = decision
        return decisions

    def _write_decision(self, review_path: Path, decision: DedupDecision) -> None:
        decisions_path = self._decisions_path(review_path)
        decisions = self._load_decisions(decisions_path)
        decisions[decision.group_id] = decision
        payload = {
            "duplicate_review_path": str(review_path),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "decisions": [asdict(item) for item in decisions.values()],
        }
        decisions_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_result(
        self,
        *,
        project_id: str,
        review_path: Path,
        batch_id: str,
        records: list[dict[str, object]],
        excluded_records: list[dict[str, object]],
        unresolved_group_ids: list[str],
        decisions_path: Path,
    ) -> Path:
        output_dir = self._storage_root / "projects" / project_id / "meta_analysis" / "dedup_decision"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{batch_id}_deduplicated_literature.json"
        payload = {
            "project_id": project_id,
            "batch_id": batch_id,
            "source_path": str(review_path),
            "decisions_path": str(decisions_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "records": records,
            "excluded_records": excluded_records,
            "unresolved_group_ids": unresolved_group_ids,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _start_task(self, *, project_id: str, source_path: str) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.DEDUP_DECISION,
            module="meta_analysis",
            title="Dedup Decision",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Generating deduplicated literature from {source_path}" if source_path else "Waiting for duplicate decisions",
        )

    def _finish_task(self, task: TaskRecord, result: DedupResult) -> None:
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
