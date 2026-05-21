from __future__ import annotations

import hashlib
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry, save_registry

from .models import PlotArtifact
from .schema import validate_plot_artifact


def create_cox_forest_plot_artifact(project_root: str, source_result_id: str) -> dict[str, Any]:
    registry = load_registry(project_root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    source = next((entry for entry in entries if entry.get("result_id") == source_result_id), None)
    if source is None:
        return _blocked(source_result_id, ["missing_source_result"])
    semantics = normalize_result_semantics(source.get("result_semantics"))
    blockers: list[str] = []
    if source.get("task_type") != "cox_univariate":
        blockers.append("cox_forest_plot_requires_cox_univariate_result")
    if semantics != "formal_computed_result":
        blockers.append("cox_forest_plot_requires_formal_computed_result_source")
    if source.get("validation_status") not in {"passed", "warning"} or source.get("blockers"):
        blockers.append("cox_forest_plot_requires_valid_source_result")
    artifact_paths = {str(item.get("artifact_type") or ""): str(item.get("path") or "") for item in source.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "cox_result_table" not in artifact_paths:
        blockers.append("cox_forest_plot_requires_cox_result_table")
    spec = {
        "schema_version": "biomedpilot.cox_forest_plot_spec.v1",
        "plot_type": "cox_forest_plot",
        "covariate_label_field": "covariate_label",
        "hazard_ratio_field": "hazard_ratio",
        "ci_lower_field": "ci_lower",
        "ci_upper_field": "ci_upper",
        "p_value_field": "p_value",
        "show_reference_line": True,
        "source_result_id": source_result_id,
        "source_cox_result_table": artifact_paths.get("cox_result_table", ""),
        "rendering": "spec_only_no_image_dependency",
    }
    parameters = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    artifact = PlotArtifact(
        plot_id=_plot_id(source_result_id),
        plot_type="cox_forest_plot",
        source_result_id=source_result_id,
        source_result_semantics=semantics,
        source_task_type=str(source.get("task_type") or ""),
        plot_semantics=semantics,
        plot_artifact_scope="formal_cox_forest_plot_spec",
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest=parameters,
        plot_parameters={"show_reference_line": True, "rendering": "spec_only_no_image_dependency"},
        plot_spec_artifact=spec,
        image_artifacts=(),
        table_artifacts=({"artifact_type": "cox_result_table", "path": artifact_paths.get("cox_result_table", "")},),
        engine_name="biomedpilot_cox_forest_plot_spec",
        engine_version="0.1.0",
        dependency_snapshot=source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {},
        warnings=("Cox forest plot artifact is spec-only; no PNG/SVG/PDF image generated in B14.",),
        blockers=tuple(blockers),
    ).to_dict()
    validation = validate_plot_artifact(artifact)
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation.get("blockers", [])]))
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation.get("warnings", [])]))
    if not artifact["blockers"]:
        source["plot_artifacts"] = [*(source.get("plot_artifacts", []) or []), artifact]
        source["report_ready_eligible"] = False
        save_registry(project_root, entries)
    return artifact


def _blocked(source_result_id: str, blockers: list[str]) -> dict[str, Any]:
    return PlotArtifact(
        plot_id=_plot_id(source_result_id or "missing"),
        plot_type="cox_forest_plot",
        source_result_id=source_result_id,
        source_result_semantics="blocked",
        source_task_type="",
        plot_semantics="blocked",
        plot_artifact_scope="formal_cox_forest_plot_spec",
        blockers=tuple(blockers),
    ).to_dict()


def _plot_id(source_result_id: str) -> str:
    return f"plot-cox-{hashlib.sha1(source_result_id.encode('utf-8')).hexdigest()[:12]}"
