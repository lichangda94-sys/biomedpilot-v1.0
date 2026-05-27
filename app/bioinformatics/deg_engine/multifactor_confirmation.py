from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .multifactor_schema import validate_multifactor_deg_parameters_manifest


MULTIFACTOR_CONFIRMATION_SCHEMA_VERSION = "biomedpilot.multifactor_deg_parameter_confirmation.v1"
MULTIFACTOR_CONFIRMATION_PATH = Path("manifests") / "multifactor_deg_parameter_confirmation.json"


def build_multifactor_deg_parameter_manifest(
    deg_ready_package: dict[str, Any],
    *,
    design_manifest: dict[str, Any],
    method: str,
    dependency_snapshot: dict[str, Any],
) -> dict[str, Any]:
    manifest = {
        "schema_version": "biomedpilot.multifactor_deg_parameters.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_package_id": str(deg_ready_package.get("source_input_package_id") or deg_ready_package.get("input_package_id") or ""),
        "deg_ready_package_id": str(deg_ready_package.get("deg_ready_package_id") or ""),
        "design_formula": str(design_manifest.get("design_formula") or ""),
        "contrast": design_manifest.get("contrast") if isinstance(design_manifest.get("contrast"), dict) else {},
        "covariates": list(design_manifest.get("covariates", []) or []) if isinstance(design_manifest.get("covariates", []), list) else list((design_manifest.get("covariates") or {}).keys()),
        "batch_variables": _batch_variables(design_manifest),
        "design_rank": int(design_manifest.get("design_rank") or 3),
        "residual_degrees_of_freedom": int(design_manifest.get("residual_degrees_of_freedom") or 1),
        "contrast_estimability": str(design_manifest.get("contrast_estimability") or "estimable"),
        "backend_method": method,
        "method": method,
        "value_type": str(deg_ready_package.get("value_type") or "unknown"),
        "value_type_policy": _value_type_policy(str(deg_ready_package.get("value_type") or "unknown"), method),
        "dependency_snapshot": dependency_snapshot,
        "warnings": [],
        "blockers": [],
    }
    validation = validate_multifactor_deg_parameters_manifest(manifest)
    blockers = list(validation["blockers"])
    if str(manifest.get("value_type_policy") or "").startswith("blocked"):
        blockers.append(str(manifest["value_type_policy"]))
    manifest["blockers"] = list(dict.fromkeys(blockers))
    manifest["status"] = "blocked" if manifest["blockers"] else "passed"
    return manifest


def save_multifactor_deg_parameter_confirmation(
    project_root: str | Path,
    *,
    deg_ready_package: dict[str, Any],
    design_manifest: dict[str, Any],
    method: str,
    dependency_snapshot: dict[str, Any],
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    parameter_manifest = build_multifactor_deg_parameter_manifest(deg_ready_package, design_manifest=design_manifest, method=method, dependency_snapshot=dependency_snapshot)
    result_id = f"multifactor-deg-{method.lower()}-{uuid4().hex[:10]}"
    task_run_id = f"task-run-{uuid4().hex[:10]}"
    output_plan = {
        "task_run_id": task_run_id,
        "result_id": result_id,
        "result_table_path": f"results/tables/{result_id}.tsv",
        "task_run_log_path": f"analysis/formal_deg/{result_id}_run_log.json",
        "result_index_registry_path": "results/summaries/result_index.json",
    }
    blockers = list(parameter_manifest.get("blockers", []) or [])
    if dependency_snapshot.get("status") != "passed":
        blockers.extend(str(item) for item in dependency_snapshot.get("blockers", []) or ["dependency_snapshot_not_passed"])
    confirmation = {
        "schema_version": MULTIFACTOR_CONFIRMATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "confirmed",
        "confirmation_semantics": "user_confirmed_multifactor_deg_parameters_not_execution",
        "confirmed_by_user": not blockers,
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency_snapshot,
        "output_plan": output_plan,
        "user_confirmation_summary": build_multifactor_confirmation_summary(parameter_manifest, dependency_snapshot, output_plan),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }
    path = root / MULTIFACTOR_CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(confirmation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return confirmation


def load_multifactor_deg_parameter_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / MULTIFACTOR_CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def validate_multifactor_deg_parameter_confirmation(
    confirmation: dict[str, Any] | None,
    *,
    parameter_manifest: dict[str, Any],
    dependency_snapshot: dict[str, Any],
) -> dict[str, Any]:
    payload = confirmation or {}
    blockers: list[str] = []
    if not payload:
        blockers.append("multifactor_deg_parameter_confirmation_missing")
        return _gate(blockers)
    if payload.get("schema_version") != MULTIFACTOR_CONFIRMATION_SCHEMA_VERSION:
        blockers.append("multifactor_deg_parameter_confirmation_schema_mismatch")
    if payload.get("status") != "confirmed" or payload.get("confirmed_by_user") is not True:
        blockers.append("multifactor_deg_parameters_not_user_confirmed")
    confirmed_parameters = payload.get("parameter_manifest") if isinstance(payload.get("parameter_manifest"), dict) else {}
    for field in ("design_formula", "contrast", "covariates", "batch_variables", "backend_method", "value_type_policy"):
        if confirmed_parameters.get(field) != parameter_manifest.get(field):
            blockers.append(f"multifactor_deg_confirmation_mismatch:{field}")
    if dependency_snapshot.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    if (payload.get("dependency_snapshot") if isinstance(payload.get("dependency_snapshot"), dict) else {}).get("status") != "passed":
        blockers.append("multifactor_deg_confirmation_dependency_not_passed")
    output_plan = payload.get("output_plan") if isinstance(payload.get("output_plan"), dict) else {}
    for field in ("task_run_id", "result_id", "result_table_path", "task_run_log_path", "result_index_registry_path"):
        if not output_plan.get(field):
            blockers.append(f"multifactor_deg_confirmation_missing_output_plan:{field}")
    return _gate(blockers)


def build_multifactor_confirmation_summary(parameter_manifest: dict[str, Any], dependency_snapshot: dict[str, Any], output_plan: dict[str, Any]) -> dict[str, Any]:
    r_packages = ((dependency_snapshot.get("r_backend") or {}).get("packages") if isinstance(dependency_snapshot.get("r_backend"), dict) else {}) or {}
    return {
        "design_formula": parameter_manifest.get("design_formula", ""),
        "contrast": parameter_manifest.get("contrast", {}),
        "covariates": parameter_manifest.get("covariates", []),
        "batch_variables": parameter_manifest.get("batch_variables", []),
        "method": parameter_manifest.get("backend_method", ""),
        "value_type_policy": parameter_manifest.get("value_type_policy", ""),
        "dependency_versions": {name: _version(status) for name, status in r_packages.items() if name in {"R", "limma", "DESeq2", "edgeR"}},
        "output_plan": dict(output_plan),
    }


def _batch_variables(design_manifest: dict[str, Any]) -> list[str]:
    explicit = design_manifest.get("batch_variables")
    if isinstance(explicit, list):
        return [str(item) for item in explicit]
    assignments = design_manifest.get("batch_assignments")
    if isinstance(assignments, dict):
        return [str(key) for key in assignments.keys()]
    return []


def _value_type_policy(value_type: str, method: str) -> str:
    count_types = {"count", "raw_count", "raw_counts", "count_like_candidate"}
    display_types = {"TPM", "FPKM", "FPKM-UQ", "CPM", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}
    if method in {"DESeq2", "edgeR"} and value_type in count_types:
        return "passed_count_model_requires_raw_counts"
    if method in {"DESeq2", "edgeR"}:
        return "blocked_count_model_requires_raw_counts"
    if method == "limma" and value_type in count_types | display_types:
        return "passed_limma_supports_count_or_display_values_with_design_review"
    return "blocked_unsupported_value_type_or_method"


def _version(status: object) -> str:
    if isinstance(status, dict):
        return str(status.get("version") or "")
    return str(status or "")


def _gate(blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.multifactor_deg_parameter_confirmation_gate.v1",
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "multifactor_deg_user_parameter_confirmation_required",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }
