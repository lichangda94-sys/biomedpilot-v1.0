from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.bioinformatics.deg_ready.builder import build_deg_ready_package

from .data_quality import build_deg_data_quality_gate
from .design_quality import build_deg_design_quality_gate
from .input_adaptation import build_deg_input_adaptation_gate
from .method_recommendation import build_deg_method_recommendation_gate


DEG_CROSS_PROJECT_ACCEPTANCE_SCHEMA_VERSION = "biomedpilot.deg_cross_project_acceptance_gate.v1"


def evaluate_deg_cross_project_scenario(
    input_package: dict[str, Any],
    *,
    scenario_id: str,
    dependency_snapshot: dict[str, Any],
    design_manifest: dict[str, Any] | None = None,
    requested_method_family: str = "",
) -> dict[str, Any]:
    deg_ready = build_deg_ready_package(input_package).to_dict()
    input_gate = build_deg_input_adaptation_gate(input_package, deg_ready, requested_method_family=requested_method_family)
    design_gate = build_deg_design_quality_gate(deg_ready, design_manifest=design_manifest, method_family=requested_method_family)
    data_gate = build_deg_data_quality_gate(deg_ready)
    method_gate = build_deg_method_recommendation_gate(
        input_adaptation_gate=input_gate,
        design_quality_gate=design_gate,
        data_quality_gate=data_gate,
        dependency_snapshot=dependency_snapshot,
    )
    blockers = _dedupe(
        [
            *deg_ready.get("blockers", []),
            *_blocking_items(input_gate),
            *_blocking_items(design_gate),
            *_blocking_items(data_gate),
            *_blocking_items(method_gate),
            *(dependency_snapshot.get("blockers", []) if dependency_snapshot.get("status") != "passed" else []),
        ]
    )
    warnings = _dedupe(
        [
            *deg_ready.get("warnings", []),
            *input_gate.get("warnings", []),
            *design_gate.get("warnings", []),
            *data_gate.get("warnings", []),
            *method_gate.get("warnings", []),
            *(dependency_snapshot.get("warnings", []) or []),
        ]
    )
    return {
        "schema_version": DEG_CROSS_PROJECT_ACCEPTANCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario_id": scenario_id,
        "status": "blocked" if blockers else "passed",
        "input_package_id": str(input_package.get("input_package_id") or ""),
        "value_type": str(input_gate.get("value_type") or ""),
        "gene_id_type": str(input_gate.get("gene_id_type") or ""),
        "dependency_status": str(dependency_snapshot.get("status") or "unknown"),
        "gates": {
            "deg_ready": deg_ready,
            "input_adaptation": input_gate,
            "design_quality": design_gate,
            "data_quality": data_gate,
            "method_recommendation": method_gate,
        },
        "result_index_v2_required": True,
        "formal_result_allowed_only_after_all_gates_pass": not blockers,
        "blockers": blockers,
        "warnings": warnings,
    }


def build_deg_cross_project_acceptance_gate(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [f"{item.get('scenario_id')}:{blocker}" for item in scenarios for blocker in item.get("blockers", []) or []]
    return {
        "schema_version": DEG_CROSS_PROJECT_ACCEPTANCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "scenario_count": len(scenarios),
        "passed_scenarios": [str(item.get("scenario_id") or "") for item in scenarios if item.get("status") == "passed"],
        "blocked_scenarios": [str(item.get("scenario_id") or "") for item in scenarios if item.get("status") == "blocked"],
        "scenarios": scenarios,
        "blockers": blockers,
        "warnings": _dedupe([warning for item in scenarios for warning in item.get("warnings", []) or []]),
        "semantic_boundary": "acceptance_gate_only_not_execution",
    }


def _blocking_items(gate: dict[str, Any]) -> list[str]:
    return [str(item) for item in gate.get("blockers", []) or []] if gate.get("status") == "blocked" else []


def _dedupe(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
