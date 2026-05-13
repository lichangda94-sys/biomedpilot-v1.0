from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class FigureArtifact:
    figure_id: str
    project_id: str
    analysis_result_id: str
    figure_type: str
    file_path: str
    format: str
    dpi: int
    created_at: str
    source_summary: dict[str, Any]


def new_figure_id() -> str:
    return f"fig-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def figure_artifact_to_dict(artifact: FigureArtifact) -> dict[str, Any]:
    return asdict(artifact)


def figure_artifact_from_dict(payload: dict[str, Any]) -> FigureArtifact:
    return FigureArtifact(
        figure_id=str(payload["figure_id"]),
        project_id=str(payload["project_id"]),
        analysis_result_id=str(payload["analysis_result_id"]),
        figure_type=str(payload["figure_type"]),
        file_path=str(payload["file_path"]),
        format=str(payload["format"]),
        dpi=int(payload["dpi"]),
        created_at=str(payload["created_at"]),
        source_summary=dict(payload.get("source_summary", {})),
    )
