from __future__ import annotations

from typing import Any


def build_basic_plot_spec(result_entry: dict[str, Any], plot_type: str, *, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    semantics = str(result_entry.get("result_semantics") or "")
    task_type = str(result_entry.get("task_type") or "")
    spec = {
        "schema_version": "biomedpilot.plot_spec.v1",
        "plot_type": plot_type,
        "source_result_id": result_entry.get("result_id") or "",
        "source_result_semantics": semantics,
        "parameters": parameters or {},
        "encoding": {},
        "data_source": "result_index_output_artifacts",
        "rendering": "spec_only_no_image_dependency",
    }
    if plot_type == "volcano_plot":
        spec["encoding"] = {"x": "log2_fold_change", "y": "-log10(adjusted_p_value)", "label": "gene_symbol", "color": "significance_label"}
    elif plot_type == "deg_heatmap":
        spec["encoding"] = {"rows": "top_differential_features", "columns": "samples", "value": "expression"}
    elif plot_type in {"ora_barplot", "ora_dotplot"}:
        spec["encoding"] = {"term": "pathway_or_term", "score": "enrichment_score_or_count", "fdr": "adjusted_p_value"}
    elif plot_type == "correlation_scatter":
        spec["encoding"] = {"x": "feature_a_expression", "y": "feature_b_expression", "label": "sample_id"}
    elif plot_type == "km_plot":
        spec["encoding"] = {"time": "survival_time", "event": "event_status", "group": "group_label"}
    spec["blockers"] = _plot_blockers(task_type, semantics, plot_type)
    spec["warnings"] = _plot_warnings(semantics)
    return spec


def _plot_blockers(task_type: str, semantics: str, plot_type: str) -> list[str]:
    blockers: list[str] = []
    if semantics == "preflight_only":
        blockers.append("preflight_only_source_cannot_generate_formal_plot")
    if plot_type == "volcano_plot" and "deg" not in task_type.lower() and "differential" not in task_type.lower():
        blockers.append("volcano_plot_requires_deg_result_schema")
    if plot_type == "km_plot":
        blockers.append("km_plot_disabled_until_survival_result_schema_exists")
    return blockers


def _plot_warnings(semantics: str) -> list[str]:
    if semantics == "testing_level":
        return ["plot_inherits_testing_level_semantics"]
    if semantics == "exploratory":
        return ["plot_inherits_exploratory_semantics"]
    if semantics == "imported_external_result":
        return ["plot_source_is_imported_external_result"]
    return []
