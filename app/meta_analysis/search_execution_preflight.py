from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.meta_analysis.project_workspace import META_PROJECT_CONFIG, open_meta_analysis_project
from app.meta_analysis.search_config_draft import META_SEED_CONFIRMED_SEARCH_PLAN


PUBMED_SEARCH_EXECUTION_PLAN = "search_execution_plan.json"


@dataclass(frozen=True)
class PubMedSearchExecutionPlan:
    plan_status: str
    source_confirmed_search_plan_path: str
    database: str
    execution_mode: str
    search_execution_status: str
    online_retrieval_executed: bool
    query: str
    query_blocks: tuple[str, ...]
    fields: tuple[str, ...]
    limits: tuple[str, ...]
    guard_override_confirmed: bool
    warnings: tuple[str, ...]
    validation_messages: tuple[str, ...]
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_pubmed_search_execution_plan(
    project_root_or_confirmed_plan: str | Path,
) -> PubMedSearchExecutionPlan:
    confirmed_path = _resolve_confirmed_plan_path(project_root_or_confirmed_plan)
    confirmed = _read_json(confirmed_path)
    validation_messages = _validate_confirmed_search_plan(confirmed)
    query = str(confirmed.get("confirmed_pubmed_query_draft") or "").strip()
    user_edited_plan = confirmed.get("user_edited_plan") if isinstance(confirmed.get("user_edited_plan"), dict) else {}
    query_blocks = _strings(user_edited_plan.get("included_pubmed_query_blocks"))
    override_confirmed = bool(user_edited_plan.get("guard_override_confirmed"))
    warnings = tuple(_strings(confirmed.get("warnings")))

    return PubMedSearchExecutionPlan(
        plan_status="preflight_ready",
        source_confirmed_search_plan_path=str(confirmed_path),
        database="PubMed",
        execution_mode="manual_preflight_only",
        search_execution_status="not_executed",
        online_retrieval_executed=False,
        query=query,
        query_blocks=tuple(query_blocks) if query_blocks else (query,),
        fields=("MeSH Terms", "Title/Abstract", "Filter"),
        limits=("none_applied_by_executor",),
        guard_override_confirmed=override_confirmed,
        warnings=(
            *warnings,
            "Preflight only: PubMed was not queried and no records were downloaded.",
        ),
        validation_messages=tuple(validation_messages),
        created_at=_now(),
    )


def save_pubmed_search_execution_plan(project_root: str | Path) -> Path:
    validation = open_meta_analysis_project(project_root)
    if not validation.is_valid or validation.summary is None:
        raise ValueError("Cannot create search execution preflight for an invalid Meta project.")

    root = validation.summary.project_root
    plan = build_pubmed_search_execution_plan(root)
    plan_path = root / "search_strategy" / PUBMED_SEARCH_EXECUTION_PLAN
    _atomic_write_json(plan_path, plan.to_dict())
    _update_project_config(root, plan_path, plan)
    return plan_path


def _validate_confirmed_search_plan(confirmed: dict[str, object]) -> list[str]:
    messages: list[str] = []
    if confirmed.get("review_status") != "user_confirmed":
        raise ValueError("Confirmed search plan must have review_status=user_confirmed.")
    if confirmed.get("search_execution_status") != "not_executed":
        raise ValueError("Confirmed search plan must still be not_executed before preflight.")
    query = str(confirmed.get("confirmed_pubmed_query_draft") or "").strip()
    if not query:
        raise ValueError("Confirmed PubMed query draft is empty.")
    messages.append("confirmed_search_plan review_status=user_confirmed")
    messages.append("confirmed PubMed query is non-empty")

    user_edited_plan = confirmed.get("user_edited_plan")
    user_payload = user_edited_plan if isinstance(user_edited_plan, dict) else {}
    guard_overrides = user_payload.get("guard_overrides")
    has_guard_override = bool(guard_overrides)
    if has_guard_override and not bool(user_payload.get("guard_override_confirmed")):
        raise ValueError("Guard override warnings must be explicitly confirmed before PubMed preflight.")
    if has_guard_override:
        messages.append("guard override warnings explicitly confirmed")
    else:
        messages.append("no guard override warnings require confirmation")
    return messages


def _resolve_confirmed_plan_path(project_root_or_confirmed_plan: str | Path) -> Path:
    path = Path(project_root_or_confirmed_plan).expanduser().resolve()
    if path.is_file():
        return path
    validation = open_meta_analysis_project(path)
    if not validation.is_valid or validation.summary is None:
        raise ValueError("Path is neither a confirmed_search_plan.json file nor a valid Meta project.")
    return validation.summary.project_root / "search_strategy" / META_SEED_CONFIRMED_SEARCH_PLAN


def _update_project_config(root: Path, plan_path: Path, plan: PubMedSearchExecutionPlan) -> None:
    config_path = root / META_PROJECT_CONFIG
    payload: dict[str, object]
    if config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        payload = loaded if isinstance(loaded, dict) else {}
    else:
        payload = {}
    payload["updated_at"] = _now()
    payload["workflow_stage"] = "search_execution_preflight"
    payload["search_execution_preflight"] = {
        "type": "pubmed_search_execution_preflight",
        "path": str(plan_path),
        "plan_status": plan.plan_status,
        "database": plan.database,
        "execution_mode": plan.execution_mode,
        "search_execution_status": plan.search_execution_status,
        "online_retrieval_executed": plan.online_retrieval_executed,
    }
    _atomic_write_json(config_path, payload)


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Missing confirmed search plan: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Confirmed search plan payload must be a JSON object.")
    return payload


def _strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
