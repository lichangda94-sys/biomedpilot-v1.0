from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.labtools.reagent_templates.models import LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION, utc_now
from app.labtools.reagent_templates.preparation_record import PreparationRecord, PreparationRecordError
from app.shared.storage import default_storage_root


def default_preparation_record_store_path() -> Path:
    return default_storage_root() / "labtools" / "reagent_templates" / "preparation_records.json"


@dataclass
class PreparationRecordStore:
    path: Path | None = None

    def resolved_path(self) -> Path:
        return self.path or default_preparation_record_store_path()

    def list_records(self) -> tuple[PreparationRecord, ...]:
        return self.load()

    def load(self) -> tuple[PreparationRecord, ...]:
        path = self.resolved_path()
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PreparationRecordError("配置试剂记录 JSON 不是有效 JSON。") from exc
        except OSError as exc:
            raise PreparationRecordError("无法读取配置试剂记录 JSON。") from exc
        return preparation_records_from_store_payload(payload)

    def save_record(self, record: PreparationRecord) -> PreparationRecord:
        records = list(self.load())
        updated = record.with_updated_timestamp()
        for index, existing in enumerate(records):
            if existing.record_id == record.record_id:
                records[index] = updated
                self.save_all(tuple(records))
                return updated
        records.append(updated)
        self.save_all(tuple(records))
        return updated

    def save_all(self, records: tuple[PreparationRecord, ...]) -> Path:
        path = self.resolved_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "records": [record.to_dict() for record in records],
        }
        try:
            _atomic_write_json(path, payload)
        except OSError as exc:
            raise PreparationRecordError("无法写入配置试剂记录 JSON，请检查路径权限。") from exc
        return path

    def get_record(self, record_id: str) -> PreparationRecord:
        for record in self.load():
            if record.record_id == record_id:
                return record
        raise PreparationRecordError("配置试剂记录不存在。")

    def delete_record(self, record_id: str, *, confirmed: bool = False) -> tuple[PreparationRecord, ...]:
        if not confirmed:
            raise PreparationRecordError("删除配置试剂记录前需要确认。")
        records = self.load()
        if not any(record.record_id == record_id for record in records):
            raise PreparationRecordError("配置试剂记录不存在。")
        remaining = tuple(record for record in records if record.record_id != record_id)
        self.save_all(remaining)
        return remaining


def preparation_records_from_store_payload(payload: Any) -> tuple[PreparationRecord, ...]:
    if not isinstance(payload, dict):
        raise PreparationRecordError("配置试剂记录 payload 必须是 JSON object。")
    if payload.get("schema_version") != LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION:
        raise PreparationRecordError("配置试剂记录 store schema 不匹配。")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise PreparationRecordError("配置试剂记录 JSON 缺少 records 列表。")
    return tuple(PreparationRecord.from_dict(item) for item in raw_records)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)
