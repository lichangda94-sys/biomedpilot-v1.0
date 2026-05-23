from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from .multifactor_gate import build_multifactor_deg_preflight_manifest
from .r_adapter_contract import build_r_deg_adapter_contract, build_r_deg_runtime_gate


R_COUNT_MODEL_ACTIVATION_PLAN_SCHEMA_VERSION = "biomedpilot.r_count_model_activation_plan.v1"
COUNT_MODEL_METHODS = ("deseq2", "edger")


def build_r_count_model_activation_plan(
    method: str,
    *,
    deg_ready_package: Mapping[str, Any] | None = None,
    design_config: Mapping[str, Any] | None = None,
    external_capabilities: Mapping[str, Any] | None = None,
    dependency_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    method_key = _method_key(method)
    if method_key not in COUNT_MODEL_METHODS:
        return {
            "schema_version": R_COUNT_MODEL_ACTIVATION_PLAN_SCHEMA_VERSION,
            "created_at": _now(),
            "method": method_key,
            "status": "unsupported",
            "formal_execution_enabled": False,
            "can_register_formal_result": False,
            "writes_result_index": False,
            "blockers": [f"unsupported_r_count_model_method:{method_key}"],
            "warnings": [],
        }

    ready = dict(deg_ready_package or {})
    preflight = build_multifactor_deg_preflight_manifest(
        ready,
        design_config=dict(design_config or {}),
        method=method_key,
        dependency_snapshot=dict(dependency_snapshot or {}),
    )
    runtime_gate = build_r_deg_runtime_gate(
        method=method_key,
        multi_factor_preflight=preflight,
        external_capabilities=dict(external_capabilities or {}),
        dependency_snapshot=dict(dependency_snapshot or {}),
    )
    contract = build_r_deg_adapter_contract(method_key)
    activation_blockers = [
        f"b25_6_count_model_planning_only:{method_key}",
        f"{method_key}_rscript_execution_adapter_not_implemented",
        f"{method_key}_parameter_confirmation_contract_not_implemented",
        f"{method_key}_result_registration_handoff_not_implemented",
    ]
    blockers = _dedupe(
        [
            *activation_blockers,
            *[str(item) for item in preflight.get("blockers", []) or []],
            *[str(item) for item in runtime_gate.get("blockers", []) or []],
        ]
    )
    return {
        "schema_version": R_COUNT_MODEL_ACTIVATION_PLAN_SCHEMA_VERSION,
        "created_at": _now(),
        "method": method_key,
        "label": "DESeq2" if method_key == "deseq2" else "edgeR",
        "status": "planned_not_enabled",
        "planning_stage": "B25.6 count-model activation planning",
        "formal_execution_enabled": False,
        "can_register_formal_result": False,
        "writes_result_index": False,
        "result_semantics": "not_executed",
        "input_policy": contract["input_policy"],
        "required_gates": [
            "B8 resolver deg_recompute package",
            "raw integer count matrix selected as standardized expression asset",
            "B18/B25 count-model design preflight passed",
            "detect-only R/Bioconductor method dependency snapshot passed",
            "method-specific parameter confirmation manifest",
            "method-specific Rscript execution adapter",
            "method-specific output schema validation",
            "result_index_v2 formal DEG registration gate",
        ],
        "preflight": preflight,
        "runtime_gate": runtime_gate,
        "output_schema": contract["output_schema"],
        "blockers": blockers,
        "warnings": _dedupe(
            [
                "B25.6 records DESeq2/edgeR activation requirements only; it does not execute R or register formal results.",
                *[str(item) for item in preflight.get("warnings", []) or []],
                *[str(item) for item in runtime_gate.get("warnings", []) or []],
            ]
        ),
        "disabled_reason": "; ".join(blockers),
    }


def build_r_count_model_activation_plans(
    *,
    deg_ready_package: Mapping[str, Any] | None = None,
    design_config: Mapping[str, Any] | None = None,
    external_capabilities: Mapping[str, Any] | None = None,
    dependency_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    plans = {
        method: build_r_count_model_activation_plan(
            method,
            deg_ready_package=deg_ready_package,
            design_config=design_config,
            external_capabilities=external_capabilities,
            dependency_snapshot=dependency_snapshot,
        )
        for method in COUNT_MODEL_METHODS
    }
    return {
        "schema_version": "biomedpilot.r_count_model_activation_plan_matrix.v1",
        "status": "planned_not_enabled",
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "plans": plans,
        "blockers": _dedupe([item for plan in plans.values() for item in plan.get("blockers", []) or []]),
        "warnings": _dedupe([item for plan in plans.values() for item in plan.get("warnings", []) or []]),
    }


def _method_key(method: str) -> str:
    value = str(method or "").strip().lower().replace("-", "_")
    if value == "edger":
        return "edger"
    return value


def _dedupe(values: list[object]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in values if str(item)))


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
