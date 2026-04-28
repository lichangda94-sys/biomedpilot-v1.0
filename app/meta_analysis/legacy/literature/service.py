from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from literature.models import (
    ImportFormatHint,
    ImportRecord,
    ImportRecordStatus,
    ImportSourceKind,
    LiteratureProject,
)
from literature.store import LiteratureStore


class LiteratureProjectService:
    def __init__(self, store: LiteratureStore) -> None:
        self._store = store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "LiteratureProjectService":
        return cls(LiteratureStore(root_dir))

    def create_project(
        self,
        name: str,
        *,
        description: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> LiteratureProject:
        project = LiteratureProject(
            project_id=f"proj-{uuid4().hex[:12]}",
            name=name,
            description=description,
            tags=list(tags or []),
            metadata=dict(metadata or {}),
        )
        return self._store.save_project(project)

    def register_import(
        self,
        project_id: str,
        source_path: str,
        *,
        source_kind: ImportSourceKind = ImportSourceKind.FILE,
        format_hint: ImportFormatHint = ImportFormatHint.UNKNOWN,
        note: str = "",
        metadata: dict[str, str] | None = None,
    ) -> ImportRecord:
        record = ImportRecord(
            import_id=f"imp-{uuid4().hex[:12]}",
            project_id=project_id,
            source_path=source_path,
            source_kind=source_kind,
            format_hint=format_hint,
            status=ImportRecordStatus.PENDING,
            note=note,
            metadata=dict(metadata or {}),
        )
        return self._store.save_import_record(record)
