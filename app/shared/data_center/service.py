from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class DataAssetRecord:
    data_id: str
    project_id: str
    module: str
    data_type: str
    source_path: str
    output_path: str
    created_at: str
    status: str


class DataCenter:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> "DataCenter":
        return cls(default_storage_root() / "data" / "data_assets.json")

    def register_asset(
        self,
        *,
        project_id: str,
        module: str,
        data_type: str,
        source_path: str,
        output_path: str,
        status: str = "available",
        data_id: str | None = None,
    ) -> DataAssetRecord:
        record = DataAssetRecord(
            data_id=data_id or f"data-{uuid4().hex[:12]}",
            project_id=project_id,
            module=module,
            data_type=data_type,
            source_path=source_path,
            output_path=output_path,
            created_at=datetime.now(timezone.utc).isoformat(),
            status=status,
        )
        records = self.list_assets()
        records.insert(0, record)
        self._write(records)
        return record

    def list_assets(self, project_id: str | None = None) -> list[DataAssetRecord]:
        if not self.storage_path.exists():
            return []
        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        records = [DataAssetRecord(**item) for item in payload.get("data_assets", [])]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        return records

    def _write(self, records: list[DataAssetRecord]) -> None:
        payload = {"data_assets": [asdict(record) for record in records]}
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
