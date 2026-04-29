from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
from uuid import uuid4


LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


@dataclass(frozen=True)
class LegacyParsedRecord:
    record_id: str
    title: str = ""
    source_record_id: str = ""
    abstract: str = ""
    authors: list[str] | None = None
    authors_text: str = ""
    creators: list[dict[str, object]] | None = None
    first_author: str = ""
    journal: str = ""
    publication_title: str = ""
    date: str = ""
    doi: str = ""
    pmid: str = ""
    year: int | None = None
    keywords: list[str] | None = None
    publication_type: str = "unknown"
    clinical_trials_ids: list[str] | None = None
    external_key: str = ""
    language: str = ""
    raw_payload: dict[str, object] | None = None


@dataclass(frozen=True)
class LegacyImportAdapterResult:
    batch_id: str
    records: list[LegacyParsedRecord]


class LiteratureImportAdapter:
    def parse_file(self, source_path: Path, project_id: str, source_type: str) -> LegacyImportAdapterResult:
        with _legacy_path():
            from literature.adapters import CsvImportAdapter, NbibImportAdapter, RisImportAdapter
            from literature.models import ImportFormatHint, ImportSourceKind
            from literature.parser import ImportParseContext

            format_hint = {
                "csv": ImportFormatHint.CSV,
                "nbib": ImportFormatHint.NBIB,
                "ris": ImportFormatHint.RIS,
            }[source_type]
            parser = {
                "csv": CsvImportAdapter(),
                "nbib": NbibImportAdapter(),
                "ris": RisImportAdapter(),
            }[source_type]
            batch_id = f"batch-{uuid4().hex[:12]}"
            context = ImportParseContext(
                batch_id=batch_id,
                project_id=project_id,
                input_path=str(source_path),
                format_hint=format_hint,
                source_type=ImportSourceKind.FILE,
                metadata={"adapter": "BioMedPilot LiteratureImportAdapter"},
            )
            records = parser.parse(source_path, context)
        return LegacyImportAdapterResult(
            batch_id=batch_id,
            records=[
                LegacyParsedRecord(
                    record_id=record.record_id or f"prec-{uuid4().hex[:12]}",
                    title=record.title,
                    source_record_id=record.source_record_id,
                    abstract=record.abstract,
                    authors=list(record.authors),
                    authors_text=record.authors_text or "; ".join(record.authors),
                    creators=_creator_dicts(record),
                    first_author=record.first_author or _first_author(record),
                    journal=record.journal,
                    publication_title=record.publication_title,
                    date=record.date,
                    doi=record.doi,
                    pmid=record.pmid,
                    year=record.year,
                    keywords=list(record.keywords),
                    publication_type=record.publication_type,
                    clinical_trials_ids=list(record.clinical_trials_ids),
                    external_key=record.external_key,
                    language=record.language,
                    raw_payload=dict(record.raw_payload),
                )
                for record in records
            ],
        )


def _creator_dicts(record: object) -> list[dict[str, object]]:
    creators = getattr(record, "creators", [])
    if creators:
        return [creator.to_dict() for creator in creators]
    authors = list(getattr(record, "authors", []) or [])
    return [_creator_from_author(author, index) for index, author in enumerate(authors, start=1) if str(author).strip()]


def _creator_from_author(author: str, order: int) -> dict[str, object]:
    raw = str(author).strip()
    if "," in raw:
        last_name, first_name = [part.strip() for part in raw.split(",", 1)]
        full_name = " ".join(part for part in (first_name, last_name) if part)
    else:
        parts = raw.split()
        first_name = " ".join(parts[:-1]) if len(parts) > 1 else ""
        last_name = parts[-1] if parts else ""
        full_name = raw
    return {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "creator_type": "author",
        "order": order,
        "raw": raw,
    }


def _first_author(record: object) -> str:
    creators = _creator_dicts(record)
    for creator in creators:
        if creator.get("creator_type") in {"author", "group_author", "corresponding_author"}:
            return str(creator.get("full_name", "")).strip()
    authors = list(getattr(record, "authors", []) or [])
    return str(authors[0]).strip() if authors else ""


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
