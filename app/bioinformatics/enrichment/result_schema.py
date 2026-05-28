from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry

from .models import ORA_RESULT_SCHEMA_GATE_VERSION, ORA_RESULT_TASK_TYPE, REQUIRED_ORA_RESULT_INDEX_FIELDS, REQUIRED_ORA_TABLE_COLUMNS


def validate_ora_result_table_row(row: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_column:{column}" for column in REQUIRED_ORA_TABLE_COLUMNS if column not in row]
    for column in ("gene_set_size", "overlap_count", "background_size", "selected_gene_count", "p_value", "adjusted_p_value", "enrichment_ratio"):
        if column in row and row[column] is not None:
            try:
                float(row[column])
            except (TypeError, ValueError):
                blockers.append(f"non_numeric:{column}")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": []}


def validate_ora_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_field:{field}" for field in REQUIRED_ORA_RESULT_INDEX_FIELDS if field not in entry]
    warnings: list[str] = []
    if str(entry.get("task_type") or "") != ORA_RESULT_TASK_TYPE:
        blockers.append("ora_result_task_type_must_be_ora_enrichment")
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics not in {"formal_computed_result", "imported_external_result"}:
        blockers.append(f"ora_result_semantics_not_allowed:{semantics or 'unknown'}")
    if semantics == "formal_computed_result" and not entry.get("source_deg_result_id"):
        blockers.append("formal_ora_missing_source_deg_result_id")
    if not entry.get("ora_input_id") and not entry.get("input_package_id"):
        blockers.append("ora_result_missing_input_package_or_ora_input_id")
    if not entry.get("gene_set_resource_id"):
        blockers.append("ora_result_missing_gene_set_resource_id")
    if not entry.get("parameters_manifest"):
        blockers.append("ora_result_missing_parameters_manifest")
    if not entry.get("dependency_snapshot"):
        blockers.append("ora_result_missing_dependency_snapshot")
    if not entry.get("engine_name") or not entry.get("engine_version"):
        blockers.append("ora_result_missing_engine_or_version")
    if not entry.get("output_artifacts"):
        blockers.append("ora_result_missing_output_artifact")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("ora_result_validation_status_not_passed")
    if entry.get("blockers"):
        blockers.append("ora_result_has_blockers")
    if entry.get("report_ready_eligible"):
        blockers.append("ora_result_must_not_be_report_ready_in_b10_1")
    if entry.get("plot_artifacts"):
        warnings.append("ora_plot_artifacts_not_activated_in_b10_1")
    if entry.get("report_artifacts"):
        warnings.append("ora_report_artifacts_not_activated_in_b10_1")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def build_ora_result_schema_gate(
    *,
    parameter_manifest: dict[str, Any] | None = None,
    result_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    parameter_manifest = parameter_manifest or {}
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or [])
        blockers.append("ora_parameter_gate_not_passed")
    if result_entry is not None:
        validation = validate_ora_result_index_entry(result_entry)
        blockers.extend(str(item) for item in validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in validation.get("warnings", []) or [])
    return {
        "schema_version": ORA_RESULT_SCHEMA_GATE_VERSION,
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "ora_future_result_index_v2_acceptance_gate_only",
        "task_type": ORA_RESULT_TASK_TYPE,
        "required_result_index_fields": list(REQUIRED_ORA_RESULT_INDEX_FIELDS),
        "required_ora_table_columns": list(REQUIRED_ORA_TABLE_COLUMNS),
        "report_ready_eligible": False,
        "plot_artifacts_allowed": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }
