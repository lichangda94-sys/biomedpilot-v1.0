from __future__ import annotations

import json
from pathlib import Path

from fulltext.models import FullTextRecord


class FullTextStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "fulltext"
        self._records_file = self._module_dir / "fulltext_records.json"

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_records(
        self,
        *,
        project_id: str | None = None,
    ) -> list[FullTextRecord]:
        payload = self._read_json(self._records_file)
        records = [FullTextRecord.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        return records

    def get_record(self, fulltext_record_id: str) -> FullTextRecord | None:
        for record in self.list_records():
            if record.fulltext_record_id == fulltext_record_id:
                return record
        return None

    def get_by_screening_record(self, screening_record_id: str) -> FullTextRecord | None:
        for record in self.list_records():
            if record.screening_record_id == screening_record_id:
                return record
        return None

    def save_record(self, record: FullTextRecord) -> FullTextRecord:
        records = self.list_records()
        self._write_records(
            self._records_file,
            self._upsert_by_key(records, record, "fulltext_record_id"),
        )
        return record

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(self, file_path: Path, records: list[FullTextRecord]) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list[FullTextRecord],
        record: FullTextRecord,
        key: str,
    ) -> list[FullTextRecord]:
        record_key = getattr(record, key)
        updated: list[FullTextRecord] = []
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
