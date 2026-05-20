from __future__ import annotations

from typing import Any

from .models import RESULT_SEMANTICS, normalize_result_semantics


REQUIRED_RESULT_FIELDS = (
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


def validate_result_entry(entry: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_field:{field_name}" for field_name in REQUIRED_RESULT_FIELDS if field_name not in entry]
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("result_semantics"), default="")
    if semantics not in RESULT_SEMANTICS:
        blockers.append("unknown_result_semantics")
    if semantics == "formal_computed_result":
        for field_name in ("input_package_id", "parameters_manifest", "engine_name", "engine_version", "dependency_snapshot"):
            if not entry.get(field_name):
                blockers.append(f"formal_result_missing:{field_name}")
        if entry.get("validation_status") not in {"passed", "warning"}:
            blockers.append("formal_result_validation_not_passed")
    if semantics == "imported_external_result" and "recomputed" in str(entry.get("task_type") or "").lower():
        blockers.append("imported_result_must_not_be_labeled_recomputed")
    if semantics in {"testing_level", "exploratory", "imported_external_result"} and entry.get("report_ready_eligible"):
        warnings.append("non_formal_result_marked_report_ready_eligible")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": warnings}
