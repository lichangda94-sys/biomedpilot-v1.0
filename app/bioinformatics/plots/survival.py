from __future__ import annotations

import hashlib
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry, save_registry

from .models import PlotArtifact
from .schema import validate_plot_artifact


def create_km_plot_artifact(project_root: str, source_result_id: str, *, show_censor_marks: bool = True, show_risk_table: bool = True, show_logrank_p_value: bool = True) -> dict[str, Any]:
    registry = load_registry(project_root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    source = next((entry for entry in entries if entry.get("result_id") == source_result_id), None)
    if source is None:
        return _blocked(source_result_id, ["missing_source_result"])
    semantics = normalize_result_semantics(source.get("result_semantics"))
    blockers: list[str] = []
    if source.get("task_type") != "survival_km_logrank":
        blockers.append("km_plot_requires_survival_km_logrank_result")
    if semantics != "formal_computed_result":
        blockers.append("km_plot_requires_formal_computed_result_source")
    if source.get("validation_status") not in {"passed", "warning"} or source.get("blockers"):
        blockers.append("km_plot_requires_valid_source_result")
    artifact_paths = {str(item.get("artifact_type") or ""): str(item.get("path") or "") for item in source.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "km_curve_table" not in artifact_paths or "logrank_result_table" not in artifact_paths:
        blockers.append("km_plot_requires_km_curve_and_logrank_tables")
    parameters = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    spec = {
        "schema_version": "biomedpilot.km_plot_spec.v1",
        "plot_type": "km_curve",
        "time_field": parameters.get("time_field", ""),
        "event_field": parameters.get("event_field", ""),
        "time_unit": parameters.get("time_unit", ""),
        "grouping_variable": parameters.get("grouping_variable", ""),
        "group_labels": [parameters.get("group_a", ""), parameters.get("group_b", "")],
        "show_censor_marks": show_censor_marks,
        "show_risk_table": show_risk_table,
        "show_logrank_p_value": show_logrank_p_value,
        "source_result_id": source_result_id,
        "source_km_curve_table": artifact_paths.get("km_curve_table", ""),
        "source_logrank_table": artifact_paths.get("logrank_result_table", ""),
        "rendering": "spec_only_no_image_dependency",
    }
    artifact = PlotArtifact(
        plot_id=_plot_id(source_result_id),
        plot_type="km_curve",
        source_result_id=source_result_id,
        source_result_semantics=semantics,
        source_task_type=str(source.get("task_type") or ""),
        plot_semantics=semantics,
        plot_artifact_scope="formal_survival_km_plot_spec",
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest=parameters,
        plot_parameters={"show_censor_marks": show_censor_marks, "show_risk_table": show_risk_table, "show_logrank_p_value": show_logrank_p_value},
        plot_spec_artifact=spec,
        image_artifacts=(),
        table_artifacts=(
            {"artifact_type": "km_curve_table", "path": artifact_paths.get("km_curve_table", "")},
            {"artifact_type": "logrank_result_table", "path": artifact_paths.get("logrank_result_table", "")},
        ),
        engine_name="biomedpilot_km_plot_spec",
        engine_version="0.1.0",
        dependency_snapshot=source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {},
        warnings=("KM plot artifact is spec-only; no PNG/SVG/PDF image generated in B13.",),
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
        plot_type="km_curve",
        source_result_id=source_result_id,
        source_result_semantics="blocked",
        source_task_type="",
        plot_semantics="blocked",
        plot_artifact_scope="formal_survival_km_plot_spec",
        blockers=tuple(blockers),
    ).to_dict()


def _plot_id(source_result_id: str) -> str:
    return f"plot-km-{hashlib.sha1(source_result_id.encode('utf-8')).hexdigest()[:12]}"
