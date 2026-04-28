from __future__ import annotations

import json
from pathlib import Path

from bias.models import BiasDomainTemplate, BiasRecord


class BiasStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "bias"
        self._records_file = self._module_dir / "bias_records.json"
        self._templates_file = self._module_dir / "bias_templates.json"

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_records(
        self,
        *,
        project_id: str | None = None,
        screening_record_id: str | None = None,
    ) -> list[BiasRecord]:
        payload = self._read_json(self._records_file)
        records = [BiasRecord.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if screening_record_id is not None:
            records = [record for record in records if record.screening_record_id == screening_record_id]
        return records

    def get_record(self, bias_record_id: str) -> BiasRecord | None:
        for record in self.list_records():
            if record.bias_record_id == bias_record_id:
                return record
        return None

    def save_record(self, record: BiasRecord) -> BiasRecord:
        records = self.list_records()
        self._write_records(
            self._records_file,
            self._upsert_by_key(records, record, "bias_record_id"),
        )
        return record

    def list_templates(self, tool_name: str | None = None) -> list[BiasDomainTemplate]:
        payload = self._read_json(self._templates_file)
        records = [BiasDomainTemplate.from_dict(item) for item in payload]
        if tool_name is not None:
            records = [record for record in records if record.tool_name == tool_name]
        return records

    def replace_templates(self, tool_name: str, records: list[BiasDomainTemplate]) -> list[BiasDomainTemplate]:
        existing = self.list_templates()
        retained = [record for record in existing if record.tool_name != tool_name]
        updated = retained + list(records)
        self._write_records(self._templates_file, updated)
        return records

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: list[BiasRecord] | list[BiasDomainTemplate],
    ) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list[BiasRecord],
        record: BiasRecord,
        key: str,
    ) -> list[BiasRecord]:
        record_key = getattr(record, key)
        updated: list[BiasRecord] = []
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
