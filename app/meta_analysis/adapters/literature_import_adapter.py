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
    title: str
    source_record_id: str
    doi: str
    pmid: str
    year: int | None


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
                    doi=record.doi,
                    pmid=record.pmid,
                    year=record.year,
                )
                for record in records
            ],
        )


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

