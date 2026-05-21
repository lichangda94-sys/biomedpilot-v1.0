from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.validation import validate_result_entry

from .models import GSEA_RESULT_SCHEMA_GATE_VERSION, GSEA_TASK_TYPE, REQUIRED_GSEA_RESULT_INDEX_FIELDS, REQUIRED_GSEA_RESULT_TABLE_COLUMNS


def build_gsea_result_schema_gate(
    *,
    parameter_manifest: dict[str, Any] | None = None,
    result_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parameter_manifest = parameter_manifest or {}
    blockers: list[str] = []
    warnings: list[str] = []
    if parameter_manifest.get("status") != "passed":
        blockers.extend(str(item) for item in parameter_manifest.get("blockers", []) or ["gsea_parameter_gate_not_passed"])
    if result_entry is not None:
        validation = validate_gsea_result_index_entry(result_entry)
        blockers.extend(str(item) for item in validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in validation.get("warnings", []) or [])
    return {
        "schema_version": GSEA_RESULT_SCHEMA_GATE_VERSION,
        "status": "blocked" if blockers else "passed",
        "gate_semantics": "future_gsea_preranked_result_index_v2_acceptance_gate_only",
        "task_type": GSEA_TASK_TYPE,
        "execution_enabled": False,
        "required_result_index_fields": list(REQUIRED_GSEA_RESULT_INDEX_FIELDS),
        "required_gsea_result_table_columns": list(REQUIRED_GSEA_RESULT_TABLE_COLUMNS),
        "plot_artifacts_allowed": False,
        "report_ready_eligible": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def validate_gsea_result_index_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_field:{field}" for field in REQUIRED_GSEA_RESULT_INDEX_FIELDS if field not in entry]
    warnings: list[str] = []
    if str(entry.get("task_type") or "") != GSEA_TASK_TYPE:
        blockers.append("gsea_result_task_type_must_be_gsea_preranked")
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics not in {"formal_computed_result", "imported_external_result"}:
        blockers.append(f"gsea_result_semantics_not_allowed:{semantics or 'unknown'}")
    if semantics == "formal_computed_result" and not entry.get("source_deg_result_id"):
        blockers.append("formal_gsea_missing_source_deg_result_id")
    if not entry.get("gsea_input_id") and not entry.get("input_package_id"):
        blockers.append("gsea_result_missing_input_package_or_gsea_input_id")
    if not entry.get("gene_set_resource_id"):
        blockers.append("gsea_result_missing_gene_set_resource_id")
    if not entry.get("parameters_manifest"):
        blockers.append("gsea_result_missing_parameters_manifest")
    if not entry.get("dependency_snapshot"):
        blockers.append("gsea_result_missing_dependency_snapshot")
    if not entry.get("engine_name") or not entry.get("engine_version"):
        blockers.append("gsea_result_missing_engine_or_version")
    if not entry.get("output_artifacts"):
        blockers.append("gsea_result_missing_output_artifact")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("gsea_result_validation_status_not_passed")
    if entry.get("blockers"):
        blockers.append("gsea_result_has_blockers")
    if entry.get("report_ready_eligible"):
        blockers.append("gsea_result_must_not_be_report_ready_in_b11_1")
    if entry.get("plot_artifacts"):
        warnings.append("gsea_plot_artifacts_not_activated_in_b11_1")
    if entry.get("report_artifacts"):
        warnings.append("gsea_report_artifacts_not_activated_in_b11_1")
    base = validate_result_entry(entry)
    blockers.extend(str(item) for item in base.get("blockers", []) or [])
    warnings.extend(str(item) for item in base.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def validate_gsea_result_table_row(row: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_column:{column}" for column in REQUIRED_GSEA_RESULT_TABLE_COLUMNS if column not in row]
    for column in ("set_size", "overlap_size", "enrichment_score", "normalized_enrichment_score", "p_value", "adjusted_p_value"):
        if column in row and row[column] is not None:
            try:
                float(row[column])
            except (TypeError, ValueError):
                blockers.append(f"non_numeric:{column}")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": []}
