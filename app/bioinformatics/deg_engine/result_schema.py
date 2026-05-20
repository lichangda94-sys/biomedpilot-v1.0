from __future__ import annotations

from typing import Any

from .models import REQUIRED_DEG_RESULT_COLUMNS


def validate_deg_result_entry(row: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_column:{column}" for column in REQUIRED_DEG_RESULT_COLUMNS if column not in row]
    for numeric in ("case_mean", "control_mean", "p_value", "adjusted_p_value"):
        if numeric in row and row[numeric] is not None:
            try:
                float(row[numeric])
            except (TypeError, ValueError):
                blockers.append(f"non_numeric:{numeric}")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": []}


def validate_deg_result_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    for field_name in (
        "result_semantics",
        "engine_name",
        "engine_version",
        "input_package_id",
        "deg_ready_package_id",
        "parameters_manifest",
        "dependency_snapshot",
        "rows",
    ):
        if field_name not in bundle:
            blockers.append(f"missing_field:{field_name}")
    if bundle.get("result_semantics") == "formal_computed_result":
        if not bundle.get("dependency_snapshot"):
            blockers.append("formal_deg_missing_dependency_snapshot")
        if not bundle.get("parameters_manifest"):
            blockers.append("formal_deg_missing_parameters_manifest")
    for index, row in enumerate(bundle.get("rows", []) or []):
        if isinstance(row, dict):
            result = validate_deg_result_entry(row)
            blockers.extend(f"row_{index}:{item}" for item in result["blockers"])
        else:
            blockers.append(f"row_{index}:not_a_dict")
    if not bundle.get("rows") and bundle.get("result_semantics") == "formal_computed_result":
        warnings.append("formal_deg_result_has_no_rows")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": warnings}
