from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


@dataclass(frozen=True)
class DuplicateCandidateGroupResult:
    duplicate_group_id: str
    candidate_record_ids: list[str]
    match_reason: str
    confidence: float
    suggested_primary_record_id: str


class DuplicateReviewAdapter:
    def identify_duplicate_groups(self, *, project_id: str, records: list[dict[str, object]]) -> list[DuplicateCandidateGroupResult]:
        with _legacy_path():
            from literature.dedup import DuplicateDetectionService
            from literature.models import NormalizedLiteratureRecord

            normalized_records = [
                NormalizedLiteratureRecord(
                    record_id=str(record.get("record_id", "")),
                    batch_id=str(record.get("batch_id", "")),
                    project_id=project_id,
                    source=str(record.get("source", "")),
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
                    title_normalized=str(record.get("title_normalized", "")),
                    doi_normalized=str(record.get("doi_normalized", "")),
                    pmid_normalized=str(record.get("pmid_normalized", "")),
                    authors_normalized=list(record.get("authors_normalized", [])),
                    journal_normalized=str(record.get("journal_normalized", "")),
                    year_normalized=record.get("year_normalized") if isinstance(record.get("year_normalized"), int) else None,
                    source_trace=list(record.get("source_trace", [str(record.get("record_id", ""))])),
                )
                for record in records
            ]
            groups = DuplicateDetectionService().identify_groups(project_id, normalized_records)

        return [
            DuplicateCandidateGroupResult(
                duplicate_group_id=group.duplicate_group_id,
                candidate_record_ids=list(group.candidate_record_ids),
                match_reason=group.match_reason,
                confidence=group.confidence,
                suggested_primary_record_id=group.suggested_primary_record_id,
            )
            for group in groups
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
