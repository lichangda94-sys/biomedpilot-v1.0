from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.analysis_inputs import resolve_analysis_inputs
from app.bioinformatics.deg_ready.builder import build_deg_ready_package

from .dependency_check import check_deg_backend_dependencies
from .parameter_gate import build_deg_parameter_manifest


CONFIRMATION_SCHEMA_VERSION = "biomedpilot.formal_deg_parameter_confirmation.v1"
CONFIRMATION_PATH = Path("manifests") / "formal_deg_parameter_confirmation.json"


def load_deg_parameter_confirmation(project_root: str | Path) -> dict[str, Any]:
    path = Path(project_root).expanduser().resolve() / CONFIRMATION_PATH
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def save_deg_parameter_confirmation(
    project_root: str | Path,
    *,
    method: str = "welch_t_test",
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    pseudocount: float = 1e-9,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    dependency = dependency_snapshot or check_deg_backend_dependencies()
    prepared = build_confirmation_parameter_manifest(
        root,
        method=method,
        log2fc_threshold=log2fc_threshold,
        p_value_threshold=p_value_threshold,
        fdr_threshold=fdr_threshold,
        pseudocount=pseudocount,
        dependency_snapshot=dependency,
    )
    parameter_manifest = prepared.get("parameter_manifest") if isinstance(prepared.get("parameter_manifest"), dict) else {}
    blockers = list(prepared.get("blockers", []) or [])
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or [])
    result_id = f"formal-deg-{uuid4().hex[:10]}"
    task_run_id = f"task-run-{uuid4().hex[:10]}"
    output_plan = {
        "task_run_id": task_run_id,
        "result_id": result_id,
        "result_table_path": f"results/tables/{result_id}.tsv",
        "task_run_log_path": f"analysis/formal_deg/{result_id}_run_log.json",
        "result_index_registry_path": "results/summaries/result_index.json",
    }
    confirmation = {
        "schema_version": CONFIRMATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "confirmed",
        "confirmation_semantics": "user_confirmed_formal_deg_parameters_not_execution",
        "confirmed_by_user": not blockers,
        "parameter_manifest": parameter_manifest,
        "dependency_snapshot": dependency,
        "output_plan": output_plan,
        "user_confirmation_summary": build_confirmation_summary(parameter_manifest, dependency, output_plan),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys([*(prepared.get("warnings", []) or []), *(parameter_manifest.get("warnings", []) or [])])),
    }
    path = root / CONFIRMATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(confirmation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return confirmation


def build_confirmation_parameter_manifest(
    project_root: str | Path,
    *,
    method: str = "welch_t_test",
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
    pseudocount: float = 1e-9,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    dependency = dependency_snapshot or check_deg_backend_dependencies()
    resolver = resolve_analysis_inputs(root).to_dict()
    package = next((item for item in resolver.get("packages", []) or [] if isinstance(item, dict) and item.get("package_type") == "deg_recompute"), None)
    if not package:
        return {"status": "blocked", "parameter_manifest": {}, "blockers": ["missing_deg_recompute_input_package"], "warnings": []}
    if package.get("blockers"):
        return {"status": "blocked", "parameter_manifest": {}, "blockers": list(package.get("blockers", []) or []), "warnings": list(package.get("warnings", []) or [])}
    deg_ready = build_deg_ready_package(package).to_dict()
    if deg_ready.get("blockers"):
        return {"status": "blocked", "parameter_manifest": {}, "blockers": list(deg_ready.get("blockers", []) or []), "warnings": list(deg_ready.get("warnings", []) or [])}
    parameter_manifest = build_deg_parameter_manifest(
        deg_ready,
        method=method,
        log2fc_threshold=log2fc_threshold,
        p_value_threshold=p_value_threshold,
        fdr_threshold=fdr_threshold,
        pseudocount=pseudocount,
        dependency_snapshot=dependency,
    )
    return {
        "status": parameter_manifest.get("status", "blocked"),
        "parameter_manifest": parameter_manifest,
        "deg_ready_package": deg_ready,
        "blockers": list(parameter_manifest.get("blockers", []) or []),
        "warnings": list(dict.fromkeys([*(deg_ready.get("warnings", []) or []), *(parameter_manifest.get("warnings", []) or [])])),
    }


def validate_deg_parameter_confirmation(
    confirmation: dict[str, Any] | None,
    *,
    parameter_manifest: dict[str, Any],
    dependency_snapshot: dict[str, Any],
) -> dict[str, Any]:
    payload = confirmation or {}
    blockers: list[str] = []
    warnings: list[str] = []
    if not payload:
        blockers.append("formal_deg_parameter_confirmation_missing")
        return _gate(blockers, warnings)
    if payload.get("schema_version") != CONFIRMATION_SCHEMA_VERSION:
        blockers.append("formal_deg_parameter_confirmation_schema_mismatch")
    if payload.get("status") != "confirmed" or payload.get("confirmed_by_user") is not True:
        blockers.append("formal_deg_parameters_not_user_confirmed")
    confirmed_parameters = payload.get("parameter_manifest") if isinstance(payload.get("parameter_manifest"), dict) else {}
    confirmed_dependency = payload.get("dependency_snapshot") if isinstance(payload.get("dependency_snapshot"), dict) else {}
    output_plan = payload.get("output_plan") if isinstance(payload.get("output_plan"), dict) else {}
    for field_name in (
        "input_package_id",
        "deg_ready_package_id",
        "comparison_id",
        "case_group",
        "control_group",
        "case_samples",
        "control_samples",
        "method",
        "method_family",
        "value_type",
        "value_type_policy",
        "gene_id_type",
        "gene_mapping_policy",
        "sample_alignment_policy",
        "log2fc_threshold",
        "p_value_threshold",
        "fdr_threshold",
        "fdr_policy",
        "pseudocount",
        "multiple_testing_policy",
    ):
        if confirmed_parameters.get(field_name) != parameter_manifest.get(field_name):
            blockers.append(f"formal_deg_confirmation_mismatch:{field_name}")
    if confirmed_parameters.get("status") != "passed":
        blockers.append("formal_deg_confirmation_parameter_manifest_not_passed")
    if confirmed_dependency.get("status") != "passed":
        blockers.append("formal_deg_confirmation_dependency_not_passed")
    if dependency_snapshot.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    for package_name in ("numpy", "pandas", "scipy", "statsmodels"):
        current = _package_version(dependency_snapshot, package_name)
        confirmed = _package_version(confirmed_dependency, package_name)
        if current != confirmed:
            blockers.append(f"formal_deg_confirmation_dependency_version_mismatch:{package_name}")
    for field_name in ("task_run_id", "result_id", "result_table_path", "task_run_log_path", "result_index_registry_path"):
        if not output_plan.get(field_name):
            blockers.append(f"formal_deg_confirmation_missing_output_plan:{field_name}")
    result_id = str(output_plan.get("result_id") or "")
    if result_id:
        if output_plan.get("result_table_path") != f"results/tables/{result_id}.tsv":
            blockers.append("formal_deg_confirmation_output_plan_result_table_mismatch")
        if output_plan.get("task_run_log_path") != f"analysis/formal_deg/{result_id}_run_log.json":
            blockers.append("formal_deg_confirmation_output_plan_log_mismatch")
    if output_plan.get("result_index_registry_path") != "results/summaries/result_index.json":
        blockers.append("formal_deg_confirmation_output_plan_registry_mismatch")
    return _gate(blockers, warnings)


def build_confirmation_summary(parameter_manifest: dict[str, Any], dependency_snapshot: dict[str, Any], output_plan: dict[str, Any]) -> dict[str, Any]:
    packages = dependency_snapshot.get("packages") if isinstance(dependency_snapshot.get("packages"), dict) else {}
    return {
        "comparison": {
            "comparison_id": parameter_manifest.get("comparison_id", ""),
            "case_group": parameter_manifest.get("case_group", ""),
            "control_group": parameter_manifest.get("control_group", ""),
            "case_sample_count": len(parameter_manifest.get("case_samples", []) or []),
            "control_sample_count": len(parameter_manifest.get("control_samples", []) or []),
            "case_samples": list(parameter_manifest.get("case_samples", []) or []),
            "control_samples": list(parameter_manifest.get("control_samples", []) or []),
        },
        "method": parameter_manifest.get("method", ""),
        "thresholds": {
            "log2fc_threshold": parameter_manifest.get("log2fc_threshold"),
            "p_value_threshold": parameter_manifest.get("p_value_threshold"),
            "fdr_threshold": parameter_manifest.get("fdr_threshold"),
            "pseudocount": parameter_manifest.get("pseudocount"),
        },
        "value_type_policy": {
            "value_type": parameter_manifest.get("value_type", ""),
            "value_type_policy": parameter_manifest.get("value_type_policy", ""),
            "gene_id_type": parameter_manifest.get("gene_id_type", ""),
            "gene_mapping_policy": parameter_manifest.get("gene_mapping_policy", ""),
        },
        "dependency_versions": {
            name: str(status.get("version") or "") for name, status in packages.items() if isinstance(status, dict) and name in {"numpy", "pandas", "scipy", "statsmodels"}
        },
        "output_plan": dict(output_plan),
    }


def confirmed_output_plan(confirmation: dict[str, Any]) -> dict[str, str]:
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    return {str(key): str(value) for key, value in output_plan.items() if str(value)}


def _package_version(snapshot: dict[str, Any], name: str) -> str:
    packages = snapshot.get("packages") if isinstance(snapshot.get("packages"), dict) else {}
    status = packages.get(name) if isinstance(packages.get(name), dict) else {}
    return str(status.get("version") or "")


def _gate(blockers: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.formal_deg_parameter_confirmation_gate.v1",
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "formal_deg_user_parameter_confirmation_required",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
