from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COX_CONFIRMATION_SCHEMA_VERSION = "biomedpilot.cox_univariate_parameter_confirmation.v1"
COX_CONFIRMATION_PATH = Path("manifests") / "cox_univariate_parameter_confirmation.json"


def confirm_cox_univariate_parameters(project_root: str | Path, parameter_manifest: dict[str, Any], *, confirmed_by_user: bool = True) -> dict[str, Any]:
    digest = _manifest_digest(parameter_manifest)
    result_id = f"cox-uni-{digest[:10]}"
    output_plan = {
        "task_run_id": f"task-run-cox-{digest[:10]}",
        "result_id": result_id,
        "cox_result_table_path": f"results/tables/survival/{result_id}_cox.tsv",
        "task_run_log_path": f"analysis/survival_cox/{result_id}_run_log.json",
        "result_index_registry_path": "results/summaries/result_index.json",
    }
    blockers = []
    if parameter_manifest.get("status") != "passed":
        blockers.append("cox_parameter_manifest_not_passed")
    if not confirmed_by_user:
        blockers.append("cox_univariate_parameters_not_user_confirmed")
    payload = {
        "schema_version": COX_CONFIRMATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "confirmed",
        "confirmation_semantics": "user_confirmed_single_variable_cox_parameters_not_multivariate",
        "confirmed_by_user": confirmed_by_user and not blockers,
        "parameter_manifest_digest": digest,
        "parameter_manifest": dict(parameter_manifest),
        "dependency_snapshot": dict(parameter_manifest.get("dependency_snapshot") or {}),
        "output_plan": output_plan,
        "blockers": blockers,
        "warnings": list(parameter_manifest.get("warnings", []) or []),
    }
    path = Path(project_root).expanduser().resolve() / COX_CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_cox_univariate_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / COX_CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def validate_cox_univariate_confirmation(confirmation: dict[str, Any] | None, parameter_manifest: dict[str, Any]) -> dict[str, Any]:
    payload = dict(confirmation or {})
    blockers: list[str] = []
    warnings: list[str] = []
    if not payload:
        blockers.append("cox_univariate_parameter_confirmation_missing")
        return _gate(blockers, warnings)
    if payload.get("schema_version") != COX_CONFIRMATION_SCHEMA_VERSION:
        blockers.append("cox_univariate_confirmation_schema_mismatch")
    if payload.get("status") != "confirmed" or payload.get("confirmed_by_user") is not True:
        blockers.append("cox_univariate_parameters_not_user_confirmed")
    if payload.get("parameter_manifest_digest") != _manifest_digest(parameter_manifest):
        blockers.append("cox_univariate_confirmation_manifest_mismatch")
    if parameter_manifest.get("status") != "passed":
        blockers.append("cox_parameter_manifest_not_passed")
    if (parameter_manifest.get("dependency_snapshot") or {}).get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    confirmed_dependency = payload.get("dependency_snapshot") if isinstance(payload.get("dependency_snapshot"), dict) else {}
    if confirmed_dependency.get("status") != "passed":
        blockers.append("cox_univariate_confirmation_dependency_not_passed")
    output_plan = payload.get("output_plan") if isinstance(payload.get("output_plan"), dict) else {}
    for field_name in ("task_run_id", "result_id", "cox_result_table_path", "task_run_log_path", "result_index_registry_path"):
        if not output_plan.get(field_name):
            blockers.append(f"cox_univariate_confirmation_missing_output_plan:{field_name}")
    return _gate(blockers, warnings)


def _manifest_digest(parameter_manifest: dict[str, Any]) -> str:
    stable = json.dumps(parameter_manifest, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(stable.encode("utf-8")).hexdigest()


def _gate(blockers: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.cox_univariate_parameter_confirmation_gate.v1",
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "single_variable_cox_user_parameter_confirmation_required",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
