from __future__ import annotations

import json
from pathlib import Path

from extraction.models import ExtractionRecord, FieldSourceTrace, OutcomeRecord


class ExtractionStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "extraction"
        self._extractions_file = self._module_dir / "extraction_records.json"
        self._outcomes_file = self._module_dir / "outcome_records.json"
        self._field_sources_file = self._module_dir / "field_source_traces.json"

    @property
    def module_dir(self) -> Path:
        return self._module_dir

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_extraction_records(
        self,
        *,
        project_id: str | None = None,
    ) -> list[ExtractionRecord]:
        payload = self._read_json(self._extractions_file)
        records = [ExtractionRecord.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        return records

    def get_extraction_record(self, extraction_record_id: str) -> ExtractionRecord | None:
        for record in self.list_extraction_records():
            if record.extraction_record_id == extraction_record_id:
                return record
        return None

    def save_extraction_record(self, record: ExtractionRecord) -> ExtractionRecord:
        records = self.list_extraction_records()
        self._write_records(
            self._extractions_file,
            self._upsert_by_key(records, record, "extraction_record_id"),
        )
        return record

    def list_outcome_records(
        self,
        *,
        extraction_record_id: str | None = None,
    ) -> list[OutcomeRecord]:
        payload = self._read_json(self._outcomes_file)
        records = [OutcomeRecord.from_dict(item) for item in payload]
        if extraction_record_id is not None:
            records = [
                record for record in records if record.extraction_record_id == extraction_record_id
            ]
        return records

    def get_outcome_record(self, outcome_record_id: str) -> OutcomeRecord | None:
        for record in self.list_outcome_records():
            if record.outcome_record_id == outcome_record_id:
                return record
        return None

    def save_outcome_record(self, record: OutcomeRecord) -> OutcomeRecord:
        records = self.list_outcome_records()
        self._write_records(
            self._outcomes_file,
            self._upsert_by_key(records, record, "outcome_record_id"),
        )
        return record

    def list_field_source_traces(
        self,
        *,
        linked_object_id: str | None = None,
    ) -> list[FieldSourceTrace]:
        payload = self._read_json(self._field_sources_file)
        records = [FieldSourceTrace.from_dict(item) for item in payload]
        if linked_object_id is not None:
            records = [
                record for record in records if record.linked_object_id == linked_object_id
            ]
        return records

    def replace_field_source_traces(
        self,
        linked_object_id: str,
        records: list[FieldSourceTrace],
    ) -> list[FieldSourceTrace]:
        existing = self.list_field_source_traces()
        retained = [record for record in existing if record.linked_object_id != linked_object_id]
        updated = retained + list(records)
        self._write_records(self._field_sources_file, updated)
        return records

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: list[ExtractionRecord] | list[OutcomeRecord] | list[FieldSourceTrace],
    ) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list[ExtractionRecord] | list[OutcomeRecord],
        record: ExtractionRecord | OutcomeRecord,
        key: str,
    ) -> list[ExtractionRecord] | list[OutcomeRecord]:
        record_key = getattr(record, key)
        updated: list[ExtractionRecord] | list[OutcomeRecord] = []
        replaced = False
        for item in records:
            if getattr(item, key) == record_key:
                updated.append(record)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(record)
        return updated
