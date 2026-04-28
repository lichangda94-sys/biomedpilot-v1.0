from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
from uuid import uuid4


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


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
        with _legacy_path():
            from literature.models import ScreeningDecision, ScreeningRecord, ScreeningStage

            legacy_records = [
                ScreeningRecord(
                    screening_record_id=f"screen-{uuid4().hex[:12]}",
                    project_id=project_id,
                    source_record_id=str(record.get("source_record_id") or record.get("record_id", "")),
                    normalized_record_id=str(record.get("record_id", "")),
                    stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
                    decision=ScreeningDecision.PENDING,
                )
                for record in eligible_records
            ]

        records_by_id = {str(record.get("record_id", "")): record for record in eligible_records}
        return [
            ScreeningQueueRecord(
                screening_record_id=legacy_record.screening_record_id,
                project_id=legacy_record.project_id,
                source_record_id=legacy_record.source_record_id,
                normalized_record_id=legacy_record.normalized_record_id,
                title=str(records_by_id.get(legacy_record.normalized_record_id, {}).get("title", "")),
                abstract=str(records_by_id.get(legacy_record.normalized_record_id, {}).get("abstract", "")),
                stage=legacy_record.stage.value,
                decision=legacy_record.decision.value,
                exclusion_reason_code=legacy_record.exclusion_reason_code,
                exclusion_reason_text=legacy_record.exclusion_reason_text,
                reviewer_id=legacy_record.reviewer_id,
                notes=legacy_record.notes,
            )
            for legacy_record in legacy_records
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


@contextmanager
def _legacy_path():
    legacy_text = str(LEGACY_ROOT)
    inserted = False
    if legacy_text not in sys.path:
        sys.path.insert(0, legacy_text)
        inserted = True
    try:
        yield
    finally:
        if inserted:
            try:
                sys.path.remove(legacy_text)
            except ValueError:
                pass
