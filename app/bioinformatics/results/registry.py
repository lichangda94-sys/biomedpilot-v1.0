from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .migration import migrate_result_entries
from .models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from .validation import validate_result_entry


RESULT_INDEX = Path("results") / "summaries" / "result_index.json"


def load_registry(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    path = root / RESULT_INDEX
    if not path.is_file():
        return {"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("results") or payload.get("entries") or []
    migrated = migrate_result_entries([entry for entry in entries if isinstance(entry, dict)])
    return {"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": migrated, "source_path": str(path)}


def save_registry(project_root: str | Path, entries: list[dict[str, Any] | ResultIndexEntry]) -> Path:
    root = Path(project_root).expanduser().resolve()
    path = root / RESULT_INDEX
    normalized = [entry.to_dict() if isinstance(entry, ResultIndexEntry) else dict(entry) for entry in entries]
    payload = {"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": normalized}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def register_result(project_root: str | Path, entry: dict[str, Any] | ResultIndexEntry) -> dict[str, Any]:
    payload = entry.to_dict() if isinstance(entry, ResultIndexEntry) else dict(entry)
    validation = validate_result_entry(payload)
    if validation["status"] == "blocked":
        payload["validation_status"] = "blocked"
        payload["blockers"] = list(dict.fromkeys([*payload.get("blockers", []), *validation["blockers"]]))
    registry = load_registry(project_root)
    entries = [item for item in registry.get("results", []) if isinstance(item, dict) and item.get("result_id") != payload.get("result_id")]
    entries.append(payload)
    save_registry(project_root, entries)
    return payload
