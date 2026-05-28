from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from labtools.shared.storage import default_storage_root


@dataclass(frozen=True)
class LabToolsLocalDataPaths:
    root: Path
    data_store: Path
    record_index: Path
    audit_log: Path
    backups: Path
    exports: Path


def default_labtools_local_data_root() -> Path:
    return default_storage_root() / "labtools"


def resolve_labtools_local_data_paths(root: str | Path | None = None) -> LabToolsLocalDataPaths:
    labtools_root = Path(root).expanduser().resolve() if root is not None else default_labtools_local_data_root()
    return LabToolsLocalDataPaths(
        root=labtools_root,
        data_store=labtools_root / "labtools_data_store.json",
        record_index=labtools_root / "labtools_record_index.json",
        audit_log=labtools_root / "labtools_audit_log.json",
        backups=labtools_root / "backups",
        exports=labtools_root / "exports",
    )
