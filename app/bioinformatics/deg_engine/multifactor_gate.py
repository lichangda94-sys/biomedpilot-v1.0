from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .design_quality import build_deg_design_quality_gate


MULTIFACTOR_DEG_GATE_SCHEMA_VERSION = "biomedpilot.multifactor_deg_controlled_gate.v1"
COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "CPM", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}


def build_multifactor_deg_controlled_gate(
    deg_ready_package: dict[str, Any] | None,
    *,
    design_manifest: dict[str, Any] | None,
    dependency_snapshot: dict[str, Any] | None,
    method_family: str,
) -> dict[str, Any]:
    ready = deg_ready_package or {}
    design = design_manifest or {}
    dependency = dependency_snapshot or {}
    blockers: list[str] = []
    warnings: list[str] = []
    method = method_family.strip()
    if not ready:
        blockers.append("missing_deg_ready_package")
    if not design:
        blockers.append("missing_multifactor_design_manifest")
    if not str(design.get("design_formula") or ""):
        blockers.append("missing_design_formula")
    if not isinstance(design.get("contrast"), dict):
        blockers.append("missing_contrast_manifest")
    elif not str(design["contrast"].get("contrast_id") or ""):
        blockers.append("missing_contrast_id")
    if method not in {"limma", "DESeq2", "edgeR"}:
        blockers.append("unsupported_multifactor_deg_method")
    value_type = str(ready.get("value_type") or "unknown")
    if method in {"DESeq2", "edgeR"} and value_type not in COUNT_VALUE_TYPES:
        blockers.append("count_model_multifactor_requires_raw_counts")
    if method == "limma" and value_type not in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES:
        blockers.append("limma_multifactor_requires_supported_expression_values")
    design_gate = build_deg_design_quality_gate(ready, design_manifest=design, method_family=method)
    blockers.extend(str(item) for item in design_gate.get("blockers", []) or [])
    warnings.extend(str(item) for item in design_gate.get("warnings", []) or [])
    if dependency.get("status") != "passed":
        blockers.extend(str(item) for item in dependency.get("blockers", []) or ["dependency_snapshot_not_passed"])
    if method and not _backend_available(dependency, method):
        blockers.append(f"r_backend_package_missing:{method}")
    blockers = _dedupe(blockers)
    return {
        "schema_version": MULTIFACTOR_DEG_GATE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "input_package_id": str(ready.get("source_input_package_id") or ready.get("input_package_id") or ""),
        "deg_ready_package_id": str(ready.get("deg_ready_package_id") or ""),
        "method_family": method,
        "design_formula": str(design.get("design_formula") or ""),
        "contrast": design.get("contrast") if isinstance(design.get("contrast"), dict) else {},
        "design_quality_gate": design_gate,
        "formal_execution_enabled": False,
        "activation_required": "future_multifactor_runtime_and_result_schema_activation_required",
        "blockers": blockers,
        "warnings": _dedupe(warnings),
        "semantic_boundary": "multifactor_readiness_gate_only_not_execution",
    }


def _backend_available(dependency: dict[str, Any], method: str) -> bool:
    r_backend = dependency.get("r_backend") if isinstance(dependency.get("r_backend"), dict) else {}
    packages = r_backend.get("packages") if isinstance(r_backend.get("packages"), dict) else {}
    value = packages.get(method)
    if isinstance(value, dict):
        return bool(value.get("available"))
    return str(value or "").lower() not in {"", "missing", "not_checked", "false"}


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
