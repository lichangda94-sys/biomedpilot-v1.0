from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.version import APP_VERSION

META_PROJECT_MANIFEST = "meta_project_manifest.json"
META_PROJECT_CONFIG = "meta_project_config.json"
META_PROJECT_CONTRACT_VERSION = "meta_analysis_project_workspace_v1"

META_PROJECT_DIRECTORIES = (
    "research_question",
    "search_strategy",
    "literature_library",
    "screening",
    "extraction",
    "quality_assessment",
    "analysis",
    "prisma",
    "reports",
    "logs",
    "exports",
)

META_COMPATIBILITY_DIRECTORIES = (
    "protocol",
    "literature",
    "deduplication",
    "fulltext",
    "quality",
    "figures",
    "audit",
)


@dataclass(frozen=True)
class MetaProjectSummary:
    project_id: str
    project_name: str
    project_root: Path
    created_at: str
    updated_at: str
    workflow_stage: str
    status: str
    research_topic: str
    manifest_path: Path
    config_path: Path


@dataclass(frozen=True)
class MetaProjectValidation:
    is_valid: bool
    project_root: Path
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    summary: MetaProjectSummary | None = None


def create_meta_analysis_project(
    project_name: str,
    save_location: str | Path,
    *,
    research_topic: str = "",
    allow_existing_nonempty: bool = False,
) -> MetaProjectSummary:
    resolved_name = project_name.strip() or "未命名 Meta 项目"
    base = Path(save_location).expanduser().resolve()
    project_root = base / _slug(resolved_name)
    if project_root.exists() and any(project_root.iterdir()) and not allow_existing_nonempty:
        raise FileExistsError(f"项目目录已存在且不是空文件夹：{project_root}")
    project_root.mkdir(parents=True, exist_ok=True)
    for directory in (*META_PROJECT_DIRECTORIES, *META_COMPATIBILITY_DIRECTORIES):
        (project_root / directory).mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    project_id = f"meta-{uuid4().hex[:8]}"
    directories = {name: str((project_root / name).resolve()) for name in (*META_PROJECT_DIRECTORIES, *META_COMPATIBILITY_DIRECTORIES)}
    manifest = {
        "contract_version": META_PROJECT_CONTRACT_VERSION,
        "project_id": project_id,
        "project_name": resolved_name,
        "project_type": "meta_analysis",
        "created_at": now,
        "updated_at": now,
        "root_path": str(project_root),
        "app_version": APP_VERSION,
        "workflow_stage": "project_home",
        "developer_preview": True,
        "status": "created",
        "research_topic": research_topic.strip(),
        "directories": directories,
    }
    config = {
        "contract_version": META_PROJECT_CONTRACT_VERSION,
        "project_id": project_id,
        "project_name": resolved_name,
        "project_type": "meta_analysis",
        "root_path": str(project_root),
        "created_at": now,
        "updated_at": now,
        "workflow_stage": "project_home",
        "developer_preview": True,
        "research_topic": research_topic.strip(),
        "ui": {"current_page": "workflow_home", "language": "zh-CN"},
    }
    _atomic_write_json(project_root / META_PROJECT_MANIFEST, manifest)
    _atomic_write_json(project_root / META_PROJECT_CONFIG, config)
    return load_meta_project_summary(project_root)


def open_meta_analysis_project(project_root: str | Path) -> MetaProjectValidation:
    return validate_meta_analysis_project(project_root)


def validate_meta_analysis_project(project_root: str | Path) -> MetaProjectValidation:
    root = Path(project_root).expanduser().resolve()
    manifest_path = root / META_PROJECT_MANIFEST
    if not manifest_path.exists():
        return MetaProjectValidation(False, root, ("该文件夹不是有效的 Meta 项目，或缺少项目识别文件。",), (), None)
    try:
        manifest = _read_json(manifest_path)
    except Exception:
        return MetaProjectValidation(False, root, ("无法读取项目识别文件，请确认该文件未损坏。",), (), None)
    errors: list[str] = []
    warnings: list[str] = []
    if manifest.get("project_type") != "meta_analysis":
        errors.append("项目识别文件不是 Meta 分析项目。")
    for directory in META_PROJECT_DIRECTORIES:
        if not (root / directory).exists():
            warnings.append(f"缺少项目目录：{directory}/")
    summary = _summary_from_manifest(root, manifest)
    return MetaProjectValidation(not errors, root, tuple(errors), tuple(warnings), summary if not errors else None)


def load_meta_project_summary(project_root: str | Path) -> MetaProjectSummary:
    root = Path(project_root).expanduser().resolve()
    return _summary_from_manifest(root, _read_json(root / META_PROJECT_MANIFEST))


def _summary_from_manifest(root: Path, manifest: dict[str, object]) -> MetaProjectSummary:
    return MetaProjectSummary(
        project_id=str(manifest.get("project_id") or ""),
        project_name=str(manifest.get("project_name") or root.name),
        project_root=root,
        created_at=str(manifest.get("created_at") or "未记录"),
        updated_at=str(manifest.get("updated_at") or "未记录"),
        workflow_stage=str(manifest.get("workflow_stage") or "project_home"),
        status=str(manifest.get("status") or "created"),
        research_topic=str(manifest.get("research_topic") or ""),
        manifest_path=root / META_PROJECT_MANIFEST,
        config_path=root / META_PROJECT_CONFIG,
    )


def _slug(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in value.strip())
    return "_".join(part for part in cleaned.split("_") if part) or "Meta_Project"


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
