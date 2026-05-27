from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DEG_METHOD_RECOMMENDATION_SCHEMA_VERSION = "biomedpilot.deg_method_recommendation_gate.v1"
COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "CPM", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}


def build_deg_method_recommendation_gate(
    *,
    input_adaptation_gate: dict[str, Any] | None = None,
    design_quality_gate: dict[str, Any] | None = None,
    data_quality_gate: dict[str, Any] | None = None,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    input_gate = input_adaptation_gate or {}
    design_gate = design_quality_gate or {}
    quality_gate = data_quality_gate or {}
    dependency = dependency_snapshot or {}
    blockers = _dedupe(
        [
            *(_list(input_gate.get("blockers")) if input_gate.get("status") == "blocked" else []),
            *(_list(design_gate.get("blockers")) if design_gate.get("status") == "blocked" else []),
            *(_list(quality_gate.get("blockers")) if quality_gate.get("status") == "blocked" else []),
        ]
    )
    value_type = str(input_gate.get("value_type") or "")
    sample_count = int(design_gate.get("sample_count") or quality_gate.get("sample_count") or 0)
    dependency_packages = dependency.get("packages") if isinstance(dependency.get("packages"), dict) else {}
    r_backend = dependency.get("r_backend") if isinstance(dependency.get("r_backend"), dict) else {}
    r_packages = r_backend.get("packages") if isinstance(r_backend.get("packages"), dict) else {}

    rows = [
        _method_row(
            "DESeq2",
            recommended=value_type in COUNT_VALUE_TYPES and not blockers,
            available=value_type in COUNT_VALUE_TYPES and _r_available(r_packages, "DESeq2") and not blockers,
            disabled_reason=_disabled_reason_for_count_model(value_type, blockers, r_packages, "DESeq2"),
            explanation="Recommended for raw count two-group DEG when the design and dependencies pass.",
        ),
        _method_row(
            "edgeR",
            recommended=False,
            available=value_type in COUNT_VALUE_TYPES and _r_available(r_packages, "edgeR") and not blockers,
            disabled_reason=_disabled_reason_for_count_model(value_type, blockers, r_packages, "edgeR"),
            explanation="Available for raw count two-group DEG after explicit user confirmation.",
        ),
        _method_row(
            "limma",
            recommended=value_type in DISPLAY_VALUE_TYPES and not blockers,
            available=value_type in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES and _r_available(r_packages, "limma") and not blockers,
            disabled_reason=_disabled_reason_for_limma(value_type, blockers, r_packages),
            explanation="Recommended for log/microarray values; limma-voom is a candidate for raw counts.",
        ),
        _method_row(
            "python_welch_or_mann_whitney",
            recommended=False,
            available=value_type in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES and _python_available(dependency_packages) and not blockers,
            disabled_reason=_disabled_reason_for_python(value_type, blockers, dependency_packages),
            explanation="Controlled two-group fallback; small-n and distribution assumptions must be reviewed.",
        ),
    ]
    warnings = []
    if 0 < sample_count < 6:
        warnings.append("small_sample_size_method_limitations_require_review")
    if value_type in DISPLAY_VALUE_TYPES:
        warnings.append("display_values_disable_count_model_methods")
    if not any(row["state"] in {"recommended", "available"} for row in rows):
        blockers.append("no_available_deg_method_after_gates")
    return {
        "schema_version": DEG_METHOD_RECOMMENDATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "value_type": value_type,
        "sample_count": sample_count,
        "methods": rows,
        "blockers": _dedupe(blockers),
        "warnings": warnings,
        "formal_execution_enabled": False,
        "semantic_boundary": "method_recommendation_only_user_confirmation_required",
    }


def _method_row(method: str, *, recommended: bool, available: bool, disabled_reason: str, explanation: str) -> dict[str, str]:
    state = "recommended" if recommended else ("available" if available else "disabled")
    return {"method": method, "state": state, "disabled_reason": "" if state != "disabled" else disabled_reason, "explanation": explanation}


def _disabled_reason_for_count_model(value_type: str, blockers: list[str], r_packages: dict[str, Any], package: str) -> str:
    if blockers:
        return "; ".join(blockers)
    if value_type in DISPLAY_VALUE_TYPES:
        return "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg"
    if value_type not in COUNT_VALUE_TYPES:
        return "raw_count_value_type_required"
    if not _r_available(r_packages, package):
        return f"r_package_missing:{package}"
    return ""


def _disabled_reason_for_limma(value_type: str, blockers: list[str], r_packages: dict[str, Any]) -> str:
    if blockers:
        return "; ".join(blockers)
    if value_type not in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES:
        return "supported_expression_value_type_required"
    if not _r_available(r_packages, "limma"):
        return "r_package_missing:limma"
    return ""


def _disabled_reason_for_python(value_type: str, blockers: list[str], packages: dict[str, Any]) -> str:
    if blockers:
        return "; ".join(blockers)
    if value_type not in COUNT_VALUE_TYPES | DISPLAY_VALUE_TYPES:
        return "supported_expression_value_type_required"
    missing = [name for name in ("numpy", "pandas", "scipy", "statsmodels") if not (isinstance(packages.get(name), dict) and packages[name].get("available"))]
    return f"missing_python_package:{','.join(missing)}" if missing else ""


def _r_available(packages: dict[str, Any], name: str) -> bool:
    value = packages.get(name)
    if isinstance(value, dict):
        return bool(value.get("available"))
    return str(value or "").lower() not in {"", "not_checked", "missing", "false"}


def _python_available(packages: dict[str, Any]) -> bool:
    return all(isinstance(packages.get(name), dict) and packages[name].get("available") for name in ("numpy", "pandas", "scipy", "statsmodels"))


def _list(value: object) -> list[str]:
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value if str(item)]
    return []


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
