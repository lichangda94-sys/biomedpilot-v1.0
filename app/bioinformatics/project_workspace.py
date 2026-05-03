from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


PROJECT_MANIFEST_FILENAME = "project_manifest.json"
PROJECT_CONFIG_FILENAME = "project_config.json"
PROJECT_CONTRACT_VERSION = "bioinformatics_project_workspace_v1"

BIOINFORMATICS_PROJECT_DIRECTORIES = (
    "raw_data",
    "acquisition",
    "recognized_data",
    "standardized_data",
    "analysis",
    "results",
    "reports",
    "logs",
    "manifests",
)


@dataclass(frozen=True)
class BioinformaticsProjectSummary:
    project_name: str
    project_root: Path
    created_at: str
    current_stage: str
    readiness_status: str
    warning_count: int
    recent_analysis_result: str
    manifest_path: Path
    config_path: Path


@dataclass(frozen=True)
class BioinformaticsProjectValidation:
    is_valid: bool
    project_root: Path
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    summary: BioinformaticsProjectSummary | None = None


def create_bioinformatics_project(project_name: str, save_location: str | Path) -> BioinformaticsProjectSummary:
    resolved_name = project_name.strip() or "未命名生信项目"
    project_root = _unique_project_root(Path(save_location).expanduser().resolve(), _slug(resolved_name))
    project_root.mkdir(parents=True, exist_ok=True)
    for directory in BIOINFORMATICS_PROJECT_DIRECTORIES:
        (project_root / directory).mkdir(parents=True, exist_ok=True)

    now = _now_iso()
    project_id = f"bio-{uuid4().hex[:8]}"
    directories = {name: str((project_root / name).resolve()) for name in BIOINFORMATICS_PROJECT_DIRECTORIES}
    manifest = {
        "contract_version": PROJECT_CONTRACT_VERSION,
        "project_type": "bioinformatics",
        "project_id": project_id,
        "project_name": resolved_name,
        "project_root": str(project_root),
        "created_at": now,
        "updated_at": now,
        "current_stage": "project_created",
        "readiness": {
            "status": "ready_for_data_source_selection",
            "warning_count": 0,
            "warnings": [],
        },
        "directories": directories,
        "recent_analysis_results": [],
    }
    config = {
        "contract_version": PROJECT_CONTRACT_VERSION,
        "project_id": project_id,
        "project_name": resolved_name,
        "project_root": str(project_root),
        "created_at": now,
        "ui_stage": "project_home",
        "data_source": "not_selected",
        "developer_preview": True,
    }
    _write_json(project_root / PROJECT_MANIFEST_FILENAME, manifest)
    _write_json(project_root / PROJECT_CONFIG_FILENAME, config)
    return load_bioinformatics_project_summary(project_root)


def open_bioinformatics_project(project_root: str | Path) -> BioinformaticsProjectValidation:
    return validate_bioinformatics_project(project_root)


def validate_bioinformatics_project(project_root: str | Path) -> BioinformaticsProjectValidation:
    root = Path(project_root).expanduser().resolve()
    manifest_path = root / PROJECT_MANIFEST_FILENAME
    errors: list[str] = []
    warnings: list[str] = []
    if not manifest_path.exists():
        return BioinformaticsProjectValidation(
            is_valid=False,
            project_root=root,
            errors=("该文件夹不是有效的生信分析项目，或缺少 project_manifest.json。",),
            warnings=(),
            summary=None,
        )
    try:
        manifest = _read_json(manifest_path)
    except Exception:
        return BioinformaticsProjectValidation(
            is_valid=False,
            project_root=root,
            errors=("该文件夹不是有效的生信分析项目，或缺少 project_manifest.json。",),
            warnings=(),
            summary=None,
        )

    if manifest.get("project_type") not in ("bioinformatics", None):
        errors.append("project_manifest.json 不是生信分析项目。")

    for directory in BIOINFORMATICS_PROJECT_DIRECTORIES:
        if not (root / directory).exists():
            warnings.append(f"缺少项目目录：{directory}/")

    summary = _summary_from_manifest(root, manifest)
    return BioinformaticsProjectValidation(
        is_valid=not errors,
        project_root=root,
        errors=tuple(errors),
        warnings=tuple(warnings),
        summary=summary if not errors else None,
    )


def load_bioinformatics_project_summary(project_root: str | Path) -> BioinformaticsProjectSummary:
    root = Path(project_root).expanduser().resolve()
    manifest = _read_json(root / PROJECT_MANIFEST_FILENAME)
    return _summary_from_manifest(root, manifest)


def _summary_from_manifest(root: Path, manifest: dict[str, object]) -> BioinformaticsProjectSummary:
    readiness = manifest.get("readiness")
    readiness_payload = readiness if isinstance(readiness, dict) else {}
    recent_results = manifest.get("recent_analysis_results")
    recent_result = "暂无最近分析结果"
    if isinstance(recent_results, list) and recent_results:
        recent_result = str(recent_results[0] or "暂无最近分析结果")
    return BioinformaticsProjectSummary(
        project_name=str(manifest.get("project_name") or "未知"),
        project_root=root,
        created_at=str(manifest.get("created_at") or "未记录"),
        current_stage=str(manifest.get("current_stage") or "未知"),
        readiness_status=str(readiness_payload.get("status") or "尚未生成"),
        warning_count=_int_or_zero(readiness_payload.get("warning_count")),
        recent_analysis_result=recent_result,
        manifest_path=root / PROJECT_MANIFEST_FILENAME,
        config_path=root / PROJECT_CONFIG_FILENAME,
    )


def _unique_project_root(save_location: Path, slug: str) -> Path:
    candidate = save_location / slug
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        numbered = save_location / f"{slug}-{index}"
        if not numbered.exists():
            return numbered
        index += 1


def _slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value.strip())
    return "_".join(part for part in cleaned.split("_") if part) or "bioinformatics_project"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _int_or_zero(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
