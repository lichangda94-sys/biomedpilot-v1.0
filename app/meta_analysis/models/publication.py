from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ProjectSnapshot:
    snapshot_id: str
    project_id: str
    created_at: str
    software_version: str
    artifact_manifest: list[dict[str, Any]]
    data_manifest: list[dict[str, Any]]
    task_manifest: list[dict[str, Any]]
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ArtifactLock:
    lock_id: str
    project_id: str
    artifact_type: str
    artifact_ref: str
    locked_at: str
    notes: str = ""


def new_snapshot_id() -> str:
    return f"snap-{uuid4().hex[:12]}"


def new_lock_id() -> str:
    return f"lock-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_snapshot_to_dict(snapshot: ProjectSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


def project_snapshot_from_dict(payload: dict[str, Any]) -> ProjectSnapshot:
    return ProjectSnapshot(
        snapshot_id=str(payload["snapshot_id"]),
        project_id=str(payload["project_id"]),
        created_at=str(payload["created_at"]),
        software_version=str(payload["software_version"]),
        artifact_manifest=[dict(item) for item in payload.get("artifact_manifest", [])],
        data_manifest=[dict(item) for item in payload.get("data_manifest", [])],
        task_manifest=[dict(item) for item in payload.get("task_manifest", [])],
        notes=[str(item) for item in payload.get("notes", [])],
    )


def artifact_lock_to_dict(lock: ArtifactLock) -> dict[str, Any]:
    return asdict(lock)


def artifact_lock_from_dict(payload: dict[str, Any]) -> ArtifactLock:
    return ArtifactLock(
        lock_id=str(payload["lock_id"]),
        project_id=str(payload["project_id"]),
        artifact_type=str(payload["artifact_type"]),
        artifact_ref=str(payload["artifact_ref"]),
        locked_at=str(payload["locked_at"]),
        notes=str(payload.get("notes", "")),
    )
