from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
from pathlib import Path
from typing import Any, Literal


ProjectWorkspaceType = Literal["bioinformatics", "meta_analysis"]

PROJECT_MANIFEST_FILENAME = ".model9_project.json"


@dataclass(frozen=True)
class ProjectWorkspaceState:
    project_id: str
    name: str
    project_type: ProjectWorkspaceType
    project_dir: Path
    status: str
    last_saved_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "project_type": self.project_type,
            "project_dir": str(self.project_dir),
            "status": self.status,
            "last_saved_at": self.last_saved_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectWorkspaceState:
        project_type = data.get("project_type")
        if project_type not in ("bioinformatics", "meta_analysis"):
            raise ValueError(f"Unsupported project type: {project_type}")
        project_id = str(data.get("project_id", "")).strip()
        name = str(data.get("name", "")).strip()
        project_dir = Path(str(data.get("project_dir", "")).strip())
        if not project_id:
            raise ValueError("Project manifest is missing project_id.")
        if not name:
            raise ValueError("Project manifest is missing name.")
        if not str(project_dir):
            raise ValueError("Project manifest is missing project_dir.")
        return cls(
            project_id=project_id,
            name=name,
            project_type=project_type,
            project_dir=project_dir,
            status=str(data.get("status", "created")),
            last_saved_at=str(data.get("last_saved_at", "")),
        )


class ProjectWorkspaceStore:
    def __init__(self, projects_root: Path) -> None:
        self._projects_root = projects_root

    @property
    def projects_root(self) -> Path:
        return self._projects_root

    def create_project(
        self,
        *,
        project_type: ProjectWorkspaceType,
        name: str,
        project_id: str | None = None,
    ) -> ProjectWorkspaceState:
        if project_type not in ("bioinformatics", "meta_analysis"):
            raise ValueError(f"Unsupported project type: {project_type}")
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Project name is required.")
        normalized_id = _safe_project_id(project_id or normalized_name)
        project_dir = self._projects_root / project_type / normalized_id
        state = ProjectWorkspaceState(
            project_id=normalized_id,
            name=normalized_name,
            project_type=project_type,
            project_dir=project_dir,
            status="created",
            last_saved_at=_utc_timestamp(),
        )
        return self.save_project(state)

    def open_project(self, project_dir: Path) -> ProjectWorkspaceState:
        manifest_path = project_dir / PROJECT_MANIFEST_FILENAME
        if not manifest_path.exists():
            raise FileNotFoundError(f"Project manifest does not exist: {manifest_path}")
        return ProjectWorkspaceState.from_dict(
            json.loads(manifest_path.read_text(encoding="utf-8"))
        )

    def save_project(self, state: ProjectWorkspaceState) -> ProjectWorkspaceState:
        state.project_dir.mkdir(parents=True, exist_ok=True)
        updated = ProjectWorkspaceState(
            project_id=state.project_id,
            name=state.name,
            project_type=state.project_type,
            project_dir=state.project_dir,
            status="saved",
            last_saved_at=_utc_timestamp(),
        )
        manifest_path = updated.project_dir / PROJECT_MANIFEST_FILENAME
        manifest_path.write_text(
            json.dumps(updated.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return updated


def _safe_project_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return normalized.lower() or "project"


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
