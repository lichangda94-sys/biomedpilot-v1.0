from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry as validate_result_index_entry

from .models import REQUIRED_DEG_RESULT_COLUMNS


FORMAL_DEG_RESULT_SCHEMA_GATE_VERSION = "biomedpilot.deg_result_schema_gate.v1"

REQUIRED_FORMAL_DEG_INDEX_FIELDS = (
    "result_id",
    "task_run_id",
    "task_type",
    "result_semantics",
    "input_package_id",
    "source_dataset_id",
    "source_repository_manifest",
    "parameters_manifest",
    "engine_name",
    "engine_version",
    "dependency_snapshot",
    "output_artifacts",
    "plot_artifacts",
    "report_artifacts",
    "validation_status",
    "warnings",
    "blockers",
    "log_artifacts",
    "failure_reason",
    "created_at",
    "updated_at",
    "schema_version",
    "report_ready_eligible",
    "migration_status",
)

NON_FORMAL_SEMANTICS = {"testing_level", "exploratory", "imported_external_result", "preflight_only", "configured_not_run", "blocked", "failed"}


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
        if not bundle.get("input_package_id"):
            blockers.append("formal_deg_missing_input_package_id")
        if not bundle.get("engine_name") or not bundle.get("engine_version"):
            blockers.append("formal_deg_missing_engine_or_version")
        if bundle.get("blockers"):
            blockers.append("formal_deg_bundle_has_blockers")
    for index, row in enumerate(bundle.get("rows", []) or []):
        if isinstance(row, dict):
            result = validate_deg_result_entry(row)
            blockers.extend(f"row_{index}:{item}" for item in result["blockers"])
        else:
            blockers.append(f"row_{index}:not_a_dict")
    if not bundle.get("rows") and bundle.get("result_semantics") == "formal_computed_result":
        warnings.append("formal_deg_result_has_no_rows")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": warnings}


def validate_formal_deg_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_field:{field_name}" for field_name in REQUIRED_FORMAL_DEG_INDEX_FIELDS if field_name not in entry]
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    raw_semantics = str(entry.get("result_semantics") or "")
    canonical = str(entry.get("canonical_result_semantics") or "")
    if semantics != "formal_computed_result":
        blockers.append(f"non_formal_semantics:{semantics or raw_semantics}")
    if raw_semantics in NON_FORMAL_SEMANTICS or canonical in NON_FORMAL_SEMANTICS:
        blockers.append("non_formal_result_marked_for_formal_deg_schema")
    if not entry.get("input_package_id"):
        blockers.append("missing_input_package_id")
    if not entry.get("parameters_manifest"):
        blockers.append("missing_parameters_manifest")
    if not entry.get("dependency_snapshot"):
        blockers.append("missing_dependency_snapshot")
    if not entry.get("engine_name") or not entry.get("engine_version"):
        blockers.append("missing_engine_or_version")
    if not entry.get("output_artifacts"):
        blockers.append("missing_output_artifact")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("validation_status_failed_or_blocked")
    if entry.get("blockers"):
        blockers.append("formal_result_has_blockers")
    base_validation = validate_result_index_entry(entry)
    blockers.extend(str(item) for item in base_validation.get("blockers", []) or [])
    warnings.extend(str(item) for item in base_validation.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def build_formal_deg_result_schema_gate(
    *,
    parameter_manifest: dict[str, Any] | None = None,
    dependency_snapshot: dict[str, Any] | None = None,
    result_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parameter_manifest = parameter_manifest or {}
    dependency_snapshot = dependency_snapshot or {}
    blockers: list[str] = []
    warnings: list[str] = []
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or [])
        if not blockers:
            blockers.append("parameter_gate_not_passed")
    if dependency_snapshot.get("status") != "passed":
        blockers.extend(str(item) for item in dependency_snapshot.get("blockers", []) or [])
        if not dependency_snapshot:
            blockers.append("dependency_snapshot_missing")
        elif not blockers:
            blockers.append("dependency_snapshot_not_passed")
    if result_entry is not None:
        validation = validate_formal_deg_result_index_entry(result_entry)
        blockers.extend(str(item) for item in validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in validation.get("warnings", []) or [])
    return {
        "schema_version": FORMAL_DEG_RESULT_SCHEMA_GATE_VERSION,
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "formal_deg_result_index_v2_acceptance_gate",
        "required_result_index_fields": list(REQUIRED_FORMAL_DEG_INDEX_FIELDS),
        "required_deg_table_columns": list(REQUIRED_DEG_RESULT_COLUMNS),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
