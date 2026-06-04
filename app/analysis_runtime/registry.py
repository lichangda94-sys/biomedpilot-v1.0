from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "analysis_modules.json"


def load_analysis_module_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve() if path else ANALYSIS_REGISTRY_PATH
    return json.loads(registry_path.read_text(encoding="utf-8"))


def get_analysis_module(module_id: str, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = registry or load_analysis_module_registry()
    for item in payload.get("modules", []):
        if isinstance(item, dict) and item.get("module_id") == module_id:
            return item
    raise ValueError(f"analysis_module_not_registered:{module_id}")
