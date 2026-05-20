from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics

from .models import PLOT_TYPES


REQUIRED_PLOT_FIELDS = (
    "plot_id",
    "plot_type",
    "source_result_id",
    "source_result_semantics",
    "input_package_id",
    "task_run_id",
    "parameters_manifest",
    "plot_spec_artifact",
    "image_artifacts",
    "table_artifacts",
    "engine_name",
    "engine_version",
    "dependency_snapshot",
    "warnings",
    "blockers",
    "created_at",
    "schema_version",
)


def validate_plot_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    blockers = [f"missing_field:{field_name}" for field_name in REQUIRED_PLOT_FIELDS if field_name not in artifact]
    warnings: list[str] = []
    if artifact.get("plot_type") not in PLOT_TYPES:
        blockers.append(f"unsupported_plot_type:{artifact.get('plot_type')}")
    semantics = normalize_result_semantics(artifact.get("source_result_semantics"))
    if semantics == "preflight_only":
        blockers.append("preflight_only_source_cannot_generate_formal_plot")
    if semantics == "testing_level":
        warnings.append("plot_inherits_testing_level_semantics")
    if semantics == "exploratory":
        warnings.append("plot_inherits_exploratory_semantics")
    if semantics == "imported_external_result":
        warnings.append("plot_source_is_imported_external_result")
    return {"status": "blocked" if blockers else "passed", "blockers": blockers, "warnings": warnings}
