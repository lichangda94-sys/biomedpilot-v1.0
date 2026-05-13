from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class ExtractionPoolRecord:
    extraction_record_id: str
    project_id: str
    screening_record_id: str
    normalized_record_id: str
    study_title: str
    study_design: str
    population: str
    condition: str
    intervention: str
    comparator: str
    sample_size_total: int | None
    follow_up: str
    country: str
    notes: str


class ExtractionAdapter:
    def create_extraction_pool(
        self,
        *,
        project_id: str,
        screening_records: list[dict[str, object]],
    ) -> list[ExtractionPoolRecord]:
        included_records = [
            record
            for record in screening_records
            if str(record.get("decision", "")).lower() == "included"
        ]
        return [
            ExtractionPoolRecord(
                extraction_record_id=f"extr-{uuid4().hex[:12]}",
                project_id=project_id,
                screening_record_id=str(record.get("screening_record_id", "")),
                normalized_record_id=str(record.get("normalized_record_id", "")),
                study_title=str(record.get("title", "")),
                study_design="",
                population="",
                condition="",
                intervention="",
                comparator="",
                sample_size_total=None,
                follow_up="",
                country="",
                notes="",
            )
            for record in included_records
        ]
