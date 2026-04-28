from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from app_meta.core.project_state import APP_VERSION, MetaProjectState, create_demo_project_state


PROJECT_JSON = "project.json"
PROJECT_FOLDERS = (
    "imported_records",
    "deduplication",
    "screening",
    "extraction",
    "analysis",
    "figures",
    "reports",
    "logs",
)


def create_project(parent_dir: str | Path, project_name: str) -> MetaProjectState:
    project_dir = Path(parent_dir).expanduser().resolve() / "meta_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    _ensure_structure(project_dir)
    now = _now()
    state = replace(
        create_demo_project_state(),
        project_id=_new_project_id(),
        project_name=project_name.strip() or "Untitled Meta Analysis Project",
        review_type="Treatment comparative meta-analysis",
        created_at=now,
        updated_at=now,
        progress_percent=5,
        current_outcome="Primary outcome",
        current_effect_size="Odds Ratio",
        project_dir=project_dir,
        project_status="Draft",
        app_version=APP_VERSION,
    )
    save_project(state, event="create")
    log_project_event(project_dir, f"project created: {state.project_id} {state.project_name}")
    return state


def open_project(project_json_path: str | Path) -> MetaProjectState:
    path = Path(project_json_path).expanduser().resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    project_dir = path.parent
    _ensure_structure(project_dir)
    state = replace(
        create_demo_project_state(),
        project_id=str(data.get("project_id", _new_project_id())),
        project_name=str(data.get("project_name", "Untitled Meta Analysis Project")),
        review_type=str(data.get("review_type", "Treatment comparative meta-analysis")),
        created_at=str(data.get("created_at", _now())),
        updated_at=str(data.get("updated_at", _now())),
        progress_percent=int(data.get("progress_percent", 0)),
        current_outcome=str(data.get("current_outcome", "Primary outcome")),
        current_effect_size=str(data.get("current_effect_size", "Odds Ratio")),
        project_dir=project_dir,
        project_status=str(data.get("project_status", "Draft")),
        app_version=str(data.get("app_version", APP_VERSION)),
    )
    log_project_event(project_dir, f"project opened: {state.project_id} {state.project_name}")
    return state


def save_project(state: MetaProjectState, event: str = "save") -> MetaProjectState:
    project_dir = state.project_dir.expanduser().resolve()
    _ensure_structure(project_dir)
    updated = replace(state, updated_at=_now(), app_version=APP_VERSION)
    metadata = project_metadata(updated)
    (project_dir / PROJECT_JSON).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log_project_event(project_dir, f"project {event}: {updated.project_id} {updated.project_name}")
    return updated


def export_project_attempt(state: MetaProjectState, export_label: str = "Export") -> None:
    _ensure_structure(state.project_dir)
    log_project_event(state.project_dir, f"export attempt: {export_label}")


def project_metadata(state: MetaProjectState) -> dict[str, object]:
    return {
        "project_id": state.project_id,
        "project_name": state.project_name,
        "review_type": state.review_type,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "progress_percent": state.progress_percent,
        "current_outcome": state.current_outcome,
        "current_effect_size": state.current_effect_size,
        "project_status": state.project_status,
        "app_version": state.app_version,
    }


def folder_status(project_dir: str | Path) -> dict[str, bool]:
    root = Path(project_dir)
    return {folder: (root / folder).is_dir() for folder in PROJECT_FOLDERS}


def log_project_event(project_dir: str | Path, message: str) -> None:
    logs_dir = Path(project_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    line = f"{_now()} {message}\n"
    with (logs_dir / "app.log").open("a", encoding="utf-8") as handle:
        handle.write(line)


def recent_log_lines(project_dir: str | Path, limit: int = 8) -> tuple[str, ...]:
    log_file = Path(project_dir) / "logs" / "app.log"
    if not log_file.exists():
        return ()
    return tuple(log_file.read_text(encoding="utf-8").splitlines()[-limit:])


def _ensure_structure(project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    for folder in PROJECT_FOLDERS:
        (project_dir / folder).mkdir(parents=True, exist_ok=True)


def _new_project_id() -> str:
    return f"MP-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
