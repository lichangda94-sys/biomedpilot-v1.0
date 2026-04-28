from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from app.shared.storage import default_storage_root

ProjectType = Literal["bioinformatics", "meta_analysis"]


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    project_name: str
    project_type: ProjectType
    created_at: str
    updated_at: str
    project_dir: str
    current_stage: str
    status: str

    def display_label(self) -> str:
        return f"{self.project_name} · {self.project_type} · {self.status}"

    @property
    def name(self) -> str:
        return self.project_name

    @property
    def path(self) -> str:
        return self.project_dir


class ProjectCenter:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> "ProjectCenter":
        return cls(default_storage_root() / "projects" / "projects.json")

    def create_project(
        self,
        name: str | None = None,
        project_type: ProjectType = "bioinformatics",
        path: str | None = None,
        *,
        project_id: str | None = None,
        project_name: str | None = None,
        project_dir: str | None = None,
        current_stage: str = "created",
        status: str = "active",
    ) -> ProjectRecord:
        now = datetime.now(timezone.utc).isoformat()
        resolved_name = project_name or name or f"{project_type}-project"
        resolved_project_id = project_id or self._new_project_id(project_type)
        resolved_project_dir = project_dir or path or str(default_storage_root() / "projects" / resolved_project_id)
        Path(resolved_project_dir).mkdir(parents=True, exist_ok=True)
        record = ProjectRecord(
            project_id=resolved_project_id,
            project_name=resolved_name,
            project_type=project_type,
            created_at=now,
            updated_at=now,
            project_dir=resolved_project_dir,
            current_stage=current_stage,
            status=status,
        )
        records = self.list_projects(limit=None)
        records = [existing for existing in records if existing.project_id != record.project_id]
        records.insert(0, record)
        self._write(records)
        return record

    def get_project(self, project_id: str) -> ProjectRecord | None:
        for record in self.list_projects(limit=None):
            if record.project_id == project_id:
                return record
        return None

    def recent_projects(self, limit: int = 5) -> list[ProjectRecord]:
        return self.list_projects(limit=limit)

    def list_projects(self, limit: int | None = None) -> list[ProjectRecord]:
        if not self.storage_path.exists():
            return []
        payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        records = [self._record_from_payload(item) for item in payload.get("projects", [])]
        return records if limit is None else records[:limit]

    def _write(self, records: list[ProjectRecord]) -> None:
        payload = {"projects": [asdict(record) for record in records]}
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _record_from_payload(self, item: dict[str, str]) -> ProjectRecord:
        if "project_name" not in item and "name" in item:
            item = {
                "project_id": item.get("project_id", self._new_project_id(item.get("project_type", "bioinformatics"))),
                "project_name": item["name"],
                "project_type": item["project_type"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "project_dir": item.get("project_dir", item.get("path", "")),
                "current_stage": item["current_stage"],
                "status": item["status"],
            }
        return ProjectRecord(**item)

    def _new_project_id(self, project_type: str) -> str:
        prefix = "bio" if project_type == "bioinformatics" else "meta"
        return f"{prefix}-{uuid4().hex[:8]}"
