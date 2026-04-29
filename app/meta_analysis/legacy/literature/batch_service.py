from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from literature.adapters import CsvImportAdapter, ManualImportAdapter, NbibImportAdapter, RisImportAdapter
from literature.import_diagnostics import build_import_diagnostics, write_import_diagnostics
from literature.models import (
    ImportBatch,
    ImportBatchStatus,
    ImportFormatHint,
    ImportSourceKind,
    ParsedLiteratureRecord,
)
from literature.parser import ImportParseContext, LiteratureParser, UnsupportedParserError
from literature.store import LiteratureStore


class ImportBatchService:
    def __init__(
        self,
        store: LiteratureStore,
        *,
        parsers: dict[ImportFormatHint, LiteratureParser] | None = None,
    ) -> None:
        self._store = store
        self._parsers = parsers or {
            ImportFormatHint.RIS: RisImportAdapter(),
            ImportFormatHint.NBIB: NbibImportAdapter(),
            ImportFormatHint.CSV: CsvImportAdapter(),
            ImportFormatHint.MANUAL: ManualImportAdapter(),
        }

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "ImportBatchService":
        return cls(LiteratureStore(root_dir))

    def create_batch(
        self,
        project_id: str,
        input_path: str,
        *,
        source_type: ImportSourceKind = ImportSourceKind.FILE,
        format_hint: ImportFormatHint = ImportFormatHint.UNKNOWN,
        metadata: dict[str, str] | None = None,
    ) -> ImportBatch:
        project = self._store.get_project(project_id)
        if project is None:
            raise ValueError(f"Project does not exist: {project_id}")

        batch = ImportBatch(
            batch_id=f"batch-{uuid4().hex[:12]}",
            project_id=project_id,
            source_type=source_type,
            input_path=input_path,
            format_hint=format_hint,
            status=ImportBatchStatus.PENDING,
            metadata=dict(metadata or {}),
        )
        return self._store.save_import_batch(batch)

    def execute_batch(self, batch_id: str) -> ImportBatch:
        batch = self._store.get_import_batch(batch_id)
        if batch is None:
            raise ValueError(f"Import batch does not exist: {batch_id}")

        batch.mark_running()
        self._store.save_import_batch(batch)

        try:
            parser = self._get_parser(batch.format_hint)
            context = ImportParseContext(
                batch_id=batch.batch_id,
                project_id=batch.project_id,
                input_path=batch.input_path,
                format_hint=batch.format_hint,
                source_type=batch.source_type,
                metadata=dict(batch.metadata),
            )
            parsed_records = parser.parse(Path(batch.input_path), context)
            normalized_records = [
                self._normalize_parsed_record(record, batch)
                for record in parsed_records
            ]
            self._store.replace_parsed_records(batch.batch_id, normalized_records)
            diagnostics = build_import_diagnostics(batch.batch_id, [record.to_dict() for record in normalized_records])
            write_import_diagnostics(self._store.module_dir.parent, diagnostics)
            batch.mark_completed(
                total_records=len(normalized_records),
                imported_records=len(normalized_records),
                failed_records=0,
                warning_count=diagnostics.warning_count,
                raw_record_count=diagnostics.raw_record_count,
                parsed_record_count=diagnostics.parsed_record_count,
                normalized_record_count=diagnostics.normalized_record_count,
                duplicate_candidate_count=diagnostics.duplicate_candidate_count,
                records_after_dedup_count=diagnostics.records_after_dedup_count,
            )
            return self._store.save_import_batch(batch)
        except Exception as exc:
            batch.mark_failed(str(exc))
            self._store.save_import_batch(batch)
            raise

    def _get_parser(self, format_hint: ImportFormatHint) -> LiteratureParser:
        parser = self._parsers.get(format_hint)
        if parser is None:
            raise UnsupportedParserError(
                f"Unsupported import format: {format_hint.value}"
            )
        return parser

    def _normalize_parsed_record(
        self,
        record: ParsedLiteratureRecord,
        batch: ImportBatch,
    ) -> ParsedLiteratureRecord:
        return ParsedLiteratureRecord(
            record_id=record.record_id or f"prec-{uuid4().hex[:12]}",
            batch_id=batch.batch_id,
            project_id=batch.project_id,
            source=record.source or batch.format_hint.value,
            source_record_id=record.source_record_id,
            title=record.title,
            abstract=record.abstract,
            authors=list(record.authors),
            authors_text=record.authors_text,
            creators=list(record.creators),
            first_author=record.first_author,
            journal=record.journal,
            publication_title=record.publication_title,
            date=record.date,
            year=record.year,
            doi=record.doi,
            pmid=record.pmid,
            keywords=list(record.keywords),
            publication_type=record.publication_type,
            clinical_trials_ids=list(record.clinical_trials_ids),
            external_key=record.external_key,
            language=record.language,
            raw_payload=dict(record.raw_payload),
        )
