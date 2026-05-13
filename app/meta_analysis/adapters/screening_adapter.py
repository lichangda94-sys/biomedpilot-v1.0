from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class ScreeningQueueRecord:
    screening_record_id: str
    project_id: str
    source_record_id: str
    normalized_record_id: str
    title: str
    abstract: str
    stage: str
    decision: str
    exclusion_reason_code: str
    exclusion_reason_text: str
    reviewer_id: str | None
    notes: str


class ScreeningAdapter:
    def create_title_abstract_queue(
        self,
        *,
        project_id: str,
        records: list[dict[str, object]],
        duplicate_groups: list[dict[str, object]] | None = None,
    ) -> list[ScreeningQueueRecord]:
        eligible_records = self._eligible_title_abstract_records(records, duplicate_groups or [])
        return [
            ScreeningQueueRecord(
                screening_record_id=f"screen-{uuid4().hex[:12]}",
                project_id=project_id,
                source_record_id=str(record.get("source_record_id") or record.get("record_id", "")),
                normalized_record_id=str(record.get("record_id", "")),
                title=str(record.get("title", "")),
                abstract=str(record.get("abstract", "")),
                stage="title_abstract_screening",
                decision="pending",
                exclusion_reason_code="",
                exclusion_reason_text="",
                reviewer_id=None,
                notes="",
            )
            for record in eligible_records
        ]

    def _eligible_title_abstract_records(
        self,
        records: list[dict[str, object]],
        duplicate_groups: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        if not duplicate_groups:
            return records

        candidate_ids = {
            str(record_id)
            for group in duplicate_groups
            for record_id in list(group.get("candidate_record_ids", []))
        }
        allowed_primary_ids = {
            str(group.get("suggested_primary_record_id", ""))
            for group in duplicate_groups
            if group.get("suggested_primary_record_id")
        }
        return [
            record
            for record in records
            if str(record.get("record_id", "")) not in candidate_ids
            or str(record.get("record_id", "")) in allowed_primary_ids
        ]
