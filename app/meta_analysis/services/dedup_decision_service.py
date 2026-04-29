from __future__ import annotations

import csv
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
    MergePreview,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
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
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._task_center = task_center or TaskCenter.default()
        self._data_center = data_center or DataCenter.default()
        self._storage_root = storage_root or default_storage_root()
        self._audit_log = audit_log or MetaAuditLogService()

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
                for record_id in list(raw_group.get("candidate_record_ids") or raw_group.get("record_ids", []))
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
                    match_reason=str(raw_group.get("match_reason") or raw_group.get("reason", "")),
                    confidence=float(raw_group.get("confidence", 0.0) or 0.0),
                    status=status,
                    reason=str(raw_group.get("reason") or raw_group.get("match_reason", "")),
                    record_ids=record_ids,
                    created_at=str(raw_group.get("created_at", "")),
                )
            )
        return groups

    def preview_merge(self, *, duplicate_review_path: str, group_id: str, master_record_id: str = "") -> MergePreview:
        review_path = self._resolve_review_path(duplicate_review_path)
        groups = {group.group_id: group for group in self.load_groups(duplicate_review_path=str(review_path))}
        if group_id not in groups:
            raise ValueError("未找到指定的重复候选组。")
        return self._merge_preview(groups[group_id], master_record_id=master_record_id)

    def export_duplicate_review_queue(self, *, duplicate_review_path: str, output_path: str = "") -> str:
        review_path = self._resolve_review_path(duplicate_review_path)
        groups = self.load_groups(duplicate_review_path=str(review_path))
        target_path = Path(output_path).expanduser() if output_path else review_path.with_name(
            review_path.name.replace("_duplicate_groups.json", "_duplicate_review_queue.csv")
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "group_id",
                    "duplicate_type",
                    "record_ids",
                    "reason",
                    "confidence",
                    "master_candidate_id",
                    "merge_preview_available",
                    "status",
                ],
            )
            writer.writeheader()
            for group in groups:
                record_ids = group.record_ids or [str(record.get("record_id", "")) for record in group.records if record.get("record_id")]
                writer.writerow(
                    {
                        "group_id": group.group_id,
                        "duplicate_type": _duplicate_type(group.match_reason or group.reason),
                        "record_ids": "|".join(record_ids),
                        "reason": group.match_reason or group.reason,
                        "confidence": group.confidence,
                        "master_candidate_id": _master_candidate_id(group),
                        "merge_preview_available": "yes" if len(record_ids) >= 2 or len(group.records) >= 2 else "no",
                        "status": group.status,
                    }
                )
        return str(target_path)

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
            final_merged_record = dict(merged_record or self._merge_preview(group).merged_record)
        if normalized_decision == DedupDecisionType.SET_MASTER_RECORD:
            final_merged_record = dict(merged_record or self._merge_preview(group, master_record_id=selected_record_id).merged_record)

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
        self._audit_log.record_event(
            self._project_dir(review_path),
            event_type="duplicate_decision",
            project_id=self._project_id_from_review(review_path),
            target_type="duplicate_group",
            target_id=group_id,
            source_path=str(review_path),
            output_path=str(self._decisions_path(review_path)),
            summary=f"Duplicate decision saved: {normalized_decision.value}",
            details={"selected_record_id": selected_record_id},
        )
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
            if decision.decision in {DedupDecisionType.MARK_NOT_DUPLICATE.value, DedupDecisionType.KEEP_BOTH.value}:
                continue
            if decision.decision in {DedupDecisionType.MERGE.value, DedupDecisionType.SET_MASTER_RECORD.value}:
                removed_ids.update(group_ids)
                replacement_records.append(dict(decision.merged_record or self._merge_preview(group, master_record_id=decision.selected_record_id).merged_record))
                excluded_records.extend(self._excluded_records(group, kept_record_id=""))
                continue
            if decision.decision == DedupDecisionType.EXCLUDE_DUPLICATE.value:
                removed_ids.update(group_ids)
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
        return self._merge_preview(group).merged_record

    def _merge_preview(self, group: DuplicateGroup, *, master_record_id: str = "") -> MergePreview:
        if not group.records:
            return MergePreview(group.group_id, {}, [], {}, [], ["merge_preview_no_records"])
        records = list(group.records)
        if master_record_id:
            records = sorted(records, key=lambda record: 0 if str(record.get("record_id", "")) == master_record_id else 1)
        merged: dict[str, object] = {"record_id": f"merged-{group.group_id}", "dedup_status": "deduplicated_merged"}
        field_sources: dict[str, str] = {}
        provenance: list[str] = []
        warnings: list[str] = []
        merged["pmid"] = _choose_pmid(records)
        if merged["pmid"]:
            field_sources["pmid"] = _source_for(records, "pmid", merged["pmid"])
        merged["doi"] = _choose_non_empty(records, "doi")
        if merged["doi"]:
            field_sources["doi"] = _source_for(records, "doi", merged["doi"])
        merged["title"] = _choose_longest(records, "title")
        if merged["title"]:
            field_sources["title"] = _source_for(records, "title", merged["title"])
        merged["abstract"] = _choose_longest(records, "abstract")
        if merged["abstract"]:
            field_sources["abstract"] = _source_for(records, "abstract", merged["abstract"])
        creators = _choose_longest_list(records, "creators")
        authors = _choose_longest_list(records, "authors")
        if creators:
            merged["creators"] = creators
            field_sources["creators"] = _source_for(records, "creators", creators)
        if authors:
            merged["authors"] = authors
            field_sources["authors"] = _source_for(records, "authors", authors)
        merged["journal"] = _choose_non_empty(records, "journal_normalized") or _choose_non_empty(records, "journal")
        if merged["journal"]:
            field_sources["journal"] = _source_for(records, "journal", merged["journal"]) or _source_for(records, "journal_normalized", merged["journal"])
        publication_types = sorted({str(record.get("publication_type", "")) for record in records if record.get("publication_type")})
        if publication_types:
            merged["publication_type"] = publication_types[0] if len(publication_types) == 1 else publication_types
        for record in records:
            for key, value in record.items():
                if key == "record_id":
                    continue
                if key in merged and merged[key] not in ("", None, []):
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
                    field_sources.setdefault(key, str(record.get("record_id", "")))
            provenance.extend(_record_provenance(record))
        merged["merged_from_record_ids"] = [str(record.get("record_id", "")) for record in records]
        merged["provenance_sources"] = sorted(set(provenance))
        if len(records) < 2:
            warnings.append("merge_preview_requires_multiple_records")
        return MergePreview(
            group_id=group.group_id,
            merged_record=merged,
            merged_from_record_ids=list(merged["merged_from_record_ids"]),
            field_sources=field_sources,
            provenance_sources=list(merged["provenance_sources"]),
            warnings=warnings,
        )

    def _selected_record_id(self, group: DuplicateGroup, decision: DedupDecisionType) -> str:
        if decision == DedupDecisionType.KEEP_FIRST:
            return str(group.records[0].get("record_id", "")) if group.records else ""
        if decision == DedupDecisionType.KEEP_SECOND:
            if len(group.records) < 2:
                raise ValueError("keep_second 需要至少两条候选记录。")
            return str(group.records[1].get("record_id", ""))
        if decision == DedupDecisionType.SET_MASTER_RECORD:
            return str(group.records[0].get("record_id", "")) if group.records else ""
        return ""

    def _normalize_decision(self, decision: str) -> DedupDecisionType:
        try:
            return DedupDecisionType(decision.strip().lower())
        except ValueError as exc:
            raise ValueError("去重决策必须是 keep_first、keep_second、merge、keep_both、mark_not_duplicate、exclude_duplicate、set_master_record 或 skip。") from exc

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

    def _project_dir(self, review_path: Path) -> Path:
        parts = review_path.parts
        if "meta_analysis" in parts:
            index = parts.index("meta_analysis")
            return Path(*parts[: index + 1])
        return review_path.parent

    def _project_id_from_review(self, review_path: Path) -> str:
        project_dir = self._project_dir(review_path)
        return project_dir.parent.name if project_dir.name == "meta_analysis" else project_dir.name


def _choose_pmid(records: list[dict[str, object]]) -> object:
    pubmed = [record for record in records if str(record.get("source", "")).lower() in {"pubmed", "nbib"}]
    return _choose_non_empty(pubmed or records, "pmid")


def _choose_non_empty(records: list[dict[str, object]], key: str) -> object:
    for record in records:
        value = record.get(key)
        if value not in ("", None, []):
            return value
    return ""


def _choose_longest(records: list[dict[str, object]], key: str) -> str:
    values = [str(record.get(key, "")).strip() for record in records if str(record.get(key, "")).strip()]
    return max(values, key=len) if values else ""


def _choose_longest_list(records: list[dict[str, object]], key: str) -> list[object]:
    values = [list(record.get(key, [])) for record in records if isinstance(record.get(key), list) and record.get(key)]
    return max(values, key=len) if values else []


def _source_for(records: list[dict[str, object]], key: str, selected: object) -> str:
    for record in records:
        if record.get(key) == selected:
            return str(record.get("record_id", ""))
    return ""


def _record_provenance(record: dict[str, object]) -> list[str]:
    values = []
    for key in ("source", "source_database", "source_file", "source_format"):
        if record.get(key):
            values.append(str(record[key]))
    source_trace = record.get("source_trace")
    if isinstance(source_trace, list):
        values.extend(str(item) for item in source_trace)
    return values


def _duplicate_type(reason: str) -> str:
    normalized = reason.lower().replace("-", "_")
    exact_tokens = ("pmid_exact", "doi_exact", "clinicaltrials_exact", "clinical_trial_exact", "clinicaltrials id", "clinical trial id")
    if any(token in normalized for token in exact_tokens):
        return "exact"
    if normalized.strip() in {"pmid", "doi", "clinicaltrials", "clinical_trial"}:
        return "exact"
    return "suspected"


def _master_candidate_id(group: DuplicateGroup) -> str:
    if group.records:
        return str(group.records[0].get("record_id", ""))
    if group.record_ids:
        return str(group.record_ids[0])
    return ""
