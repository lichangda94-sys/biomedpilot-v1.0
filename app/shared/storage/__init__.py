from __future__ import annotations

from pathlib import Path


def default_storage_root() -> Path:
    return Path.cwd() / "project_storage"

