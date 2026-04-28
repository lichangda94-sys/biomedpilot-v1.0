from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


@dataclass(frozen=True)
class ScreeningReadyRecord:
    record_id: str
    title: str
    abstract: str
    authors: list[str]
    journal: str
    year: int | None
    doi: str
    pmid: str
    title_normalized: str
    doi_normalized: str
    pmid_normalized: str


class PrepareScreeningAdapter:
    def normalize_records(
        self,
        *,
        project_id: str,
        batch_id: str,
        source_type: str,
        records: list[dict[str, object]],
    ) -> list[ScreeningReadyRecord]:
        with _legacy_path():
            from literature.models import ParsedLiteratureRecord
            from literature.normalize import RecordNormalizationService

            parsed_records = [
                ParsedLiteratureRecord(
                    record_id=str(record.get("record_id", "")),
                    batch_id=batch_id,
                    project_id=project_id,
                    source=source_type,
                    source_record_id=str(record.get("source_record_id", "")),
                    title=str(record.get("title", "")),
                    abstract=str(record.get("abstract", "")),
                    authors=list(record.get("authors", [])),
                    journal=str(record.get("journal", "")),
                    year=record.get("year") if isinstance(record.get("year"), int) else None,
                    doi=str(record.get("doi", "")),
                    pmid=str(record.get("pmid", "")),
                    keywords=list(record.get("keywords", [])),
                    language=str(record.get("language", "")),
                    raw_payload={},
                )
                for record in records
            ]
            normalized_records = RecordNormalizationService().normalize_records(parsed_records)

        return [
            ScreeningReadyRecord(
                record_id=record.record_id,
                title=record.title,
                abstract=record.abstract,
                authors=list(record.authors),
                journal=record.journal,
                year=record.year,
                doi=record.doi,
                pmid=record.pmid,
                title_normalized=record.title_normalized,
                doi_normalized=record.doi_normalized,
                pmid_normalized=record.pmid_normalized,
            )
            for record in normalized_records
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
