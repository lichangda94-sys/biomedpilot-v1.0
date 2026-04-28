from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass

from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class EnvironmentStatus:
    python_executable: str
    python_version: str
    pyside6_available: bool
    r_status: str
    storage_root: str


def check_local_environment() -> EnvironmentStatus:
    return EnvironmentStatus(
        python_executable=sys.executable,
        python_version=sys.version.split()[0],
        pyside6_available=importlib.util.find_spec("PySide6") is not None,
        r_status=shutil.which("R") or "not found",
        storage_root=str(default_storage_root()),
    )

