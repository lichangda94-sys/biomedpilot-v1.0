from __future__ import annotations

import json
from pathlib import Path


RESULT_MANAGER = Path("manifests") / "result_manager.json"
RESULT_INDEX = Path("results") / "summaries" / "result_index.json"


def load_result_index(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    index_path = root / RESULT_INDEX
    manager_path = root / RESULT_MANAGER
    index = _read_json(index_path) if index_path.exists() else None
    manager = _read_json(manager_path) if manager_path.exists() else None
    entries = []
    if isinstance(index, dict):
        raw_entries = index.get("results") or index.get("entries") or []
        entries = [item for item in raw_entries if isinstance(item, dict)]
    warnings = []
    for entry in entries:
        path = Path(str(entry.get("path") or entry.get("file_path") or ""))
        if path and not path.is_absolute():
            path = root / path
        if path and not path.exists():
            warnings.append(f"结果文件缺失：{path}")
            entry["warning"] = entry.get("warning") or "文件缺失"
    return {
        "index": index,
        "manager": manager,
        "entries": entries,
        "warnings": warnings,
        "index_path": str(index_path),
        "manager_path": str(manager_path),
    }


def write_result_index(project_root: str | Path, entries: list[dict[str, object]]) -> Path:
    root = Path(project_root).expanduser().resolve()
    path = root / RESULT_INDEX
    payload = {"schema_version": "biomedpilot.result_index.v1", "results": entries}
    _write_json(path, payload)
    _write_json(root / RESULT_MANAGER, {"schema_version": "biomedpilot.result_manager.v1", "result_count": len(entries)})
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
