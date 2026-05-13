from __future__ import annotations

from dataclasses import dataclass
from app.meta_analysis.literature_import_core import normalize_record_payload


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
    authors_normalized: list[str]
    journal_normalized: str
    year_normalized: int | None


class PrepareScreeningAdapter:
    def normalize_records(
        self,
        *,
        project_id: str,
        batch_id: str,
        source_type: str,
        records: list[dict[str, object]],
    ) -> list[ScreeningReadyRecord]:
        return [
            ScreeningReadyRecord(
                record_id=str(payload.get("record_id", "")),
                title=str(payload.get("title", "")),
                abstract=str(payload.get("abstract", "")),
                authors=list(payload.get("authors", [])),
                journal=str(payload.get("journal", "")),
                year=payload.get("year") if isinstance(payload.get("year"), int) else None,
                doi=str(payload.get("doi", "")),
                pmid=str(payload.get("pmid", "")),
                title_normalized=str(payload.get("title_normalized", "")),
                doi_normalized=str(payload.get("doi_normalized", "")),
                pmid_normalized=str(payload.get("pmid_normalized", "")),
                authors_normalized=list(payload.get("authors_normalized", [])),
                journal_normalized=str(payload.get("journal_normalized", "")),
                year_normalized=payload.get("year_normalized") if isinstance(payload.get("year_normalized"), int) else None,
            )
            for payload in (
                normalize_record_payload(record, batch_id=batch_id, project_id=project_id, source_type=source_type)
                for record in records
            )
        ]
