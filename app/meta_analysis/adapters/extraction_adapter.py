from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
from uuid import uuid4


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


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
        with _legacy_path():
            from extraction.models import ExtractionRecord

            legacy_records = [
                ExtractionRecord(
                    extraction_record_id=f"extr-{uuid4().hex[:12]}",
                    project_id=project_id,
                    screening_record_id=str(record.get("screening_record_id", "")),
                    normalized_record_id=str(record.get("normalized_record_id", "")),
                    study_title=str(record.get("title", "")),
                )
                for record in included_records
            ]

        return [
            ExtractionPoolRecord(
                extraction_record_id=record.extraction_record_id,
                project_id=record.project_id,
                screening_record_id=record.screening_record_id,
                normalized_record_id=record.normalized_record_id,
                study_title=record.study_title,
                study_design=record.study_design,
                population=record.population,
                condition=record.condition,
                intervention=record.intervention,
                comparator=record.comparator,
                sample_size_total=record.sample_size_total,
                follow_up=record.follow_up,
                country=record.country,
                notes=record.notes,
            )
            for record in legacy_records
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
