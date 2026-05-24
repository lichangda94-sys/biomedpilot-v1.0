from __future__ import annotations

from collections.abc import Mapping as MappingABC
from datetime import UTC, datetime
from typing import Any, Mapping

from .multifactor_gate import build_multifactor_deg_preflight_manifest
from .r_adapter_contract import build_r_deg_adapter_contract, build_r_deg_runtime_gate
from .r_deseq2_planning import (
    build_r_deseq2_dry_run_acceptance_gate,
    build_r_deseq2_parameter_manifest,
    build_r_deseq2_rscript_adapter_plan,
    validate_r_deseq2_parameter_confirmation,
)
from .r_edger_planning import (
    build_r_edger_parameter_manifest,
    build_r_edger_rscript_adapter_plan,
    validate_r_edger_parameter_confirmation,
)


R_COUNT_MODEL_ACTIVATION_PLAN_SCHEMA_VERSION = "biomedpilot.r_count_model_activation_plan.v1"
COUNT_MODEL_METHODS = ("deseq2", "edger")


def build_r_count_model_activation_plan(
    method: str,
    *,
    deg_ready_package: Mapping[str, Any] | None = None,
    design_config: Mapping[str, Any] | None = None,
    external_capabilities: Mapping[str, Any] | None = None,
    dependency_snapshot: Mapping[str, Any] | None = None,
    parameter_confirmation: Mapping[str, Any] | None = None,
    dry_run_output_rows: list[Mapping[str, Any]] | None = None,
    count_fixture: Mapping[str, Any] | None = None,
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
    method_specific = _method_specific_plan(
        method_key,
        ready=ready,
        preflight=preflight,
        runtime_gate=runtime_gate,
        dependency_snapshot=dict(dependency_snapshot or {}),
        parameter_confirmation=dict(parameter_confirmation or {}),
        dry_run_output_rows=dry_run_output_rows,
        count_fixture=dict(count_fixture or {}),
    )
    activation_blockers = list(method_specific.get("activation_blockers", []) or [])
    blockers = _dedupe(
        [
            *activation_blockers,
            *[str(item) for item in method_specific.get("blockers", []) or []],
            *[str(item) for item in preflight.get("blockers", []) or []],
            *[str(item) for item in runtime_gate.get("blockers", []) or []],
        ]
    )
    formal_execution_enabled = method_key in {"deseq2", "edger"} and not blockers
    return {
        "schema_version": R_COUNT_MODEL_ACTIVATION_PLAN_SCHEMA_VERSION,
        "created_at": _now(),
        "method": method_key,
        "label": "DESeq2" if method_key == "deseq2" else "edgeR",
        "status": "ready_for_ui_execution" if formal_execution_enabled else "planned_not_enabled",
        "planning_stage": "B25.11 DESeq2 gated UI execution" if method_key == "deseq2" else "B25.14 edgeR gated UI execution",
        "formal_execution_enabled": formal_execution_enabled,
        "can_register_formal_result": formal_execution_enabled,
        "writes_result_index": formal_execution_enabled,
        "result_semantics": "formal_computed_result_when_run" if formal_execution_enabled else "not_executed",
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
        **method_specific.get("public_state", {}),
        "output_schema": contract["output_schema"],
        "blockers": blockers,
        "warnings": _dedupe(
            [
                "B25.11 enables controlled DESeq2 UI execution only when all method gates and user confirmation pass."
                if method_key == "deseq2"
                else "B25.14 enables controlled edgeR UI execution only when resolver, raw-count design preflight, runtime detection, user confirmation and result-index gates pass.",
                *[str(item) for item in method_specific.get("warnings", []) or []],
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
    method_external_capabilities: Mapping[str, Mapping[str, Any]] | None = None,
    method_dependency_snapshots: Mapping[str, Mapping[str, Any]] | None = None,
    parameter_confirmations: Mapping[str, Any] | None = None,
    dry_run_output_rows: Mapping[str, list[Mapping[str, Any]]] | None = None,
    count_fixtures: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    confirmations = parameter_confirmations if isinstance(parameter_confirmations, MappingABC) else {}
    method_caps = method_external_capabilities if isinstance(method_external_capabilities, MappingABC) else {}
    method_deps = method_dependency_snapshots if isinstance(method_dependency_snapshots, MappingABC) else {}
    dry_rows = dry_run_output_rows if isinstance(dry_run_output_rows, MappingABC) else {}
    fixtures = count_fixtures if isinstance(count_fixtures, MappingABC) else {}
    plans = {
        method: build_r_count_model_activation_plan(
            method,
            deg_ready_package=deg_ready_package,
            design_config=design_config,
            external_capabilities=method_caps.get(method) if isinstance(method_caps.get(method), MappingABC) else external_capabilities,
            dependency_snapshot=method_deps.get(method) if isinstance(method_deps.get(method), MappingABC) else dependency_snapshot,
            parameter_confirmation=confirmations.get(method) if isinstance(confirmations.get(method), MappingABC) else None,
            dry_run_output_rows=dry_rows.get(method) if isinstance(dry_rows.get(method), list) else None,
            count_fixture=fixtures.get(method) if isinstance(fixtures.get(method), MappingABC) else None,
        )
        for method in COUNT_MODEL_METHODS
    }
    return {
        "schema_version": "biomedpilot.r_count_model_activation_plan_matrix.v1",
        "status": "ready_for_ui_execution" if any(plan.get("formal_execution_enabled") for plan in plans.values()) else "planned_not_enabled",
        "formal_execution_enabled": any(bool(plan.get("formal_execution_enabled")) for plan in plans.values()),
        "writes_result_index": any(bool(plan.get("writes_result_index")) for plan in plans.values()),
        "plans": plans,
        "blockers": _dedupe([item for plan in plans.values() for item in plan.get("blockers", []) or []]),
        "warnings": _dedupe([item for plan in plans.values() for item in plan.get("warnings", []) or []]),
    }


def _method_specific_plan(
    method_key: str,
    *,
    ready: Mapping[str, Any],
    preflight: Mapping[str, Any],
    runtime_gate: Mapping[str, Any],
    dependency_snapshot: Mapping[str, Any],
    parameter_confirmation: Mapping[str, Any],
    dry_run_output_rows: list[Mapping[str, Any]] | None,
    count_fixture: Mapping[str, Any],
) -> dict[str, Any]:
    if method_key == "edger":
        parameter_manifest = build_r_edger_parameter_manifest(
            ready,
            multi_factor_preflight=preflight,
            dependency_snapshot=dependency_snapshot,
        )
        confirmation_gate = validate_r_edger_parameter_confirmation(
            parameter_confirmation,
            parameter_manifest=parameter_manifest,
            dependency_snapshot=dependency_snapshot,
        )
        adapter_plan = build_r_edger_rscript_adapter_plan(
            parameter_manifest=parameter_manifest,
            runtime_gate=runtime_gate,
            confirmation_gate=confirmation_gate,
        )
        return {
            "activation_blockers": [],
            "blockers": [
                *[str(item) for item in parameter_manifest.get("blockers", []) or []],
                *[str(item) for item in confirmation_gate.get("blockers", []) or []],
                *[str(item) for item in adapter_plan.get("blockers", []) or []],
            ],
            "warnings": [
                *[str(item) for item in adapter_plan.get("warnings", []) or []],
            ],
            "public_state": {
                "parameter_manifest": parameter_manifest,
                "parameter_confirmation_gate": confirmation_gate,
                "rscript_adapter_plan": adapter_plan,
            },
        }
    parameter_manifest = build_r_deseq2_parameter_manifest(
        ready,
        multi_factor_preflight=preflight,
        dependency_snapshot=dependency_snapshot,
    )
    confirmation_gate = validate_r_deseq2_parameter_confirmation(
        parameter_confirmation,
        parameter_manifest=parameter_manifest,
        dependency_snapshot=dependency_snapshot,
    )
    adapter_plan = build_r_deseq2_rscript_adapter_plan(
        parameter_manifest=parameter_manifest,
        runtime_gate=runtime_gate,
        confirmation_gate=confirmation_gate,
    )
    dry_run_acceptance_gate = build_r_deseq2_dry_run_acceptance_gate(
        parameter_manifest=parameter_manifest,
        dependency_snapshot=dependency_snapshot,
        output_rows=dry_run_output_rows,
        count_fixture=count_fixture,
    )
    return {
        "activation_blockers": [],
        "blockers": [
            *[str(item) for item in parameter_manifest.get("blockers", []) or []],
            *[str(item) for item in confirmation_gate.get("blockers", []) or []],
            *[str(item) for item in adapter_plan.get("blockers", []) or []],
        ],
        "warnings": [
            *[str(item) for item in adapter_plan.get("warnings", []) or []],
            *[str(item) for item in dry_run_acceptance_gate.get("warnings", []) or []],
        ],
        "public_state": {
            "parameter_manifest": parameter_manifest,
            "parameter_confirmation_gate": confirmation_gate,
            "rscript_adapter_plan": adapter_plan,
            "dry_run_acceptance_gate": dry_run_acceptance_gate,
        },
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
