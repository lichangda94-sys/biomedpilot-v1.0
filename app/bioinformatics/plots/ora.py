from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment.models import REQUIRED_ORA_TABLE_COLUMNS
from app.bioinformatics.enrichment.result_schema import validate_ora_result_index_entry, validate_ora_result_table_row
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry

from .models import PlotArtifact
from .schema import validate_plot_artifact


ORA_PLOT_GATE_SCHEMA_VERSION = "biomedpilot.ora_plot_gate.v1"
ORA_PLOT_TYPES = {"ora_barplot", "ora_dotplot"}
ORA_PLOT_SORT_FIELDS = {"adjusted_p_value", "p_value", "enrichment_ratio", "overlap_count", "input_order"}
ORA_PLOT_GUARD_COPY = (
    "ORA plot artifacts are spec-only pathway over-representation visualizations. "
    "They do not render PNG/SVG/PDF, do not prove pathway activation or inhibition, "
    "and are not clinical interpretation or treatment recommendation."
)


def build_ora_plot_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    plot_type: str = "ora_barplot",
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_entry(entries, result_id)
    params = _plot_parameters(plot_type, parameters)
    blockers: list[str] = []
    warnings: list[str] = []
    if plot_type not in ORA_PLOT_TYPES:
        blockers.append(f"unsupported_ora_plot_type:{plot_type}")
    if selected is None:
        blockers.append("ora_result_not_found")
    else:
        source_validation = _validate_ora_plot_source(root, selected, params)
        blockers.extend(source_validation["blockers"])
        warnings.extend(source_validation["warnings"])
    return {
        "schema_version": ORA_PLOT_GATE_SCHEMA_VERSION,
        "status": "blocked" if blockers else "passed",
        "selected_result_id": str(selected.get("result_id") or "") if selected else str(result_id or ""),
        "plot_type": plot_type,
        "allowed_plot_types": sorted(ORA_PLOT_TYPES),
        "source_result_semantics": normalize_result_semantics((selected or {}).get("canonical_result_semantics") or (selected or {}).get("result_semantics"), default=""),
        "source_result_source_semantics": str((selected or {}).get("source_result_semantics") or ""),
        "existing_plot_artifacts": list((selected or {}).get("plot_artifacts", []) or []),
        "result_options": _result_options(entries),
        "result_index_path": str(root / RESULT_INDEX),
        "guard_copy": ORA_PLOT_GUARD_COPY,
        "plot_parameters": params,
        "report_ready_eligible": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_ora_plot_artifact(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    plot_type: str = "ora_barplot",
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    params = _plot_parameters(plot_type, parameters)
    gate = build_ora_plot_gate(root, result_id=result_id, plot_type=plot_type, parameters=params)
    if gate.get("status") != "passed":
        return {
            "schema_version": ORA_PLOT_GATE_SCHEMA_VERSION,
            "status": "blocked",
            "plot_type": plot_type,
            "result_id": str(result_id or gate.get("selected_result_id") or ""),
            "plot_artifact": {},
            "plot_artifacts": [],
            "report_artifacts": [],
            "report_ready_eligible": False,
            "blockers": list(gate.get("blockers", []) or []),
            "warnings": list(gate.get("warnings", []) or []),
        }
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    source = next(entry for entry in entries if str(entry.get("result_id") or "") == str(gate.get("selected_result_id") or ""))
    source_semantics = normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="")
    source_table = _source_ora_table(root, source) or Path()
    source_table_ref = _registry_path(source_table, root)
    spec = _plot_spec(source, plot_type, params, source_table_ref)
    warnings = list(dict.fromkeys([str(item) for item in source.get("warnings", []) or []] + list(gate.get("warnings", []) or [])))
    artifact = PlotArtifact(
        plot_id=_ora_plot_id(source, plot_type),
        plot_type=plot_type,
        source_result_id=str(source.get("result_id") or ""),
        source_result_semantics=source_semantics,
        plot_semantics=source_semantics,
        plot_artifact_scope="ora_plot_spec",
        input_package_id=str(source.get("ora_input_id") or source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest={
            "source_parameters_manifest": source.get("parameters_manifest", {}),
            "plot_parameters": params,
            "plot_policy": "ora_plot_artifact_spec_only_not_report_ready",
        },
        plot_spec_artifact=spec,
        image_artifacts=(),
        table_artifacts=({"artifact_type": "ora_result_table", "path": source_table_ref},),
        dependency_snapshot={"plot_rendering": {"available": False, "reason": "spec_only_no_image_dependency"}},
        warnings=tuple(warnings),
        blockers=tuple(spec.get("blockers", []) or []),
    ).to_dict()
    artifact.update(
        {
            "source_task_type": "ora_enrichment",
            "source_ora_table": source_table_ref,
            "source_result_source_semantics": str(source.get("source_result_semantics") or ""),
        }
    )
    validation = validate_plot_artifact(artifact)
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation.get("warnings", [])]))
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation.get("blockers", [])]))
    if artifact["blockers"]:
        return {
            "schema_version": ORA_PLOT_GATE_SCHEMA_VERSION,
            "status": "blocked",
            "plot_type": plot_type,
            "result_id": str(source.get("result_id") or ""),
            "plot_artifact": artifact,
            "plot_artifacts": list(source.get("plot_artifacts", []) or []),
            "report_artifacts": list(source.get("report_artifacts", []) or []),
            "report_ready_eligible": False,
            "blockers": artifact["blockers"],
            "warnings": artifact["warnings"],
        }
    existing = [item for item in source.get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_id") != artifact["plot_id"]]
    source["plot_artifacts"] = [*existing, artifact]
    source["report_artifacts"] = list(source.get("report_artifacts", []) or [])
    source["report_ready_eligible"] = False
    save_registry(root, entries)
    return {
        "schema_version": ORA_PLOT_GATE_SCHEMA_VERSION,
        "status": "passed",
        "plot_type": plot_type,
        "result_id": str(source.get("result_id") or ""),
        "plot_artifact": artifact,
        "plot_artifacts": list(source.get("plot_artifacts", []) or []),
        "report_artifacts": list(source.get("report_artifacts", []) or []),
        "report_ready_eligible": False,
        "result_index_path": str(root / RESULT_INDEX),
        "guard_copy": ORA_PLOT_GUARD_COPY,
        "blockers": [],
        "warnings": artifact["warnings"],
    }


def _validate_ora_plot_source(root: Path, entry: dict[str, Any], params: dict[str, Any]) -> dict[str, list[str]]:
    blockers: list[str] = []
    warnings: list[str] = [str(item) for item in entry.get("warnings", []) or []]
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    source_semantics = str(entry.get("source_result_semantics") or "")
    if semantics not in {"formal_computed_result", "imported_external_result"}:
        blockers.append(f"ora_plot_source_semantics_not_allowed:{semantics or 'unknown'}")
    if semantics == "formal_computed_result" and source_semantics != "formal_computed_result":
        blockers.append("formal_ora_plot_requires_formal_source_result_semantics")
    if semantics == "imported_external_result":
        if source_semantics != "imported_external_result":
            blockers.append("imported_ora_plot_requires_imported_source_result_semantics")
        warnings.append("imported_ora_derived_plot_not_biomedpilot_recomputed_formal_plot")
    if str(entry.get("task_type") or "") != "ora_enrichment":
        blockers.append("ora_plot_requires_ora_enrichment_task_type")
    if entry.get("validation_status") in {"blocked", "failed"}:
        blockers.append("ora_plot_source_validation_status_blocked")
    if entry.get("blockers"):
        blockers.append("ora_plot_source_result_has_blockers")
    schema_validation = validate_ora_result_index_entry(entry)
    blockers.extend(str(item) for item in schema_validation.get("blockers", []) or [])
    warnings.extend(
        str(item)
        for item in schema_validation.get("warnings", []) or []
        if str(item) != "ora_plot_artifacts_not_activated_in_b10_1"
    )
    table = _source_ora_table(root, entry)
    if table is None:
        blockers.append("ora_plot_requires_ora_result_table")
    elif not table.is_file():
        blockers.append("ora_plot_source_table_missing")
    else:
        table_validation = _validate_ora_table(table)
        blockers.extend(table_validation["blockers"])
        warnings.extend(table_validation["warnings"])
    blockers.extend(_parameter_blockers(params))
    return {"blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _validate_ora_table(path: Path) -> dict[str, list[str]]:
    rows = _read_rows(path)
    blockers: list[str] = []
    warnings: list[str] = []
    if not rows:
        blockers.append("ora_plot_requires_non_empty_table")
        return {"blockers": blockers, "warnings": warnings}
    header = set(rows[0].keys())
    for column in REQUIRED_ORA_TABLE_COLUMNS:
        if column not in header:
            blockers.append(f"ora_plot_missing_table_column:{column}")
    for index, row in enumerate(rows):
        validation = validate_ora_result_table_row(row)
        blockers.extend(f"row_{index}:{item}" for item in validation.get("blockers", []) or [])
        if not str(row.get("term_id") or "").strip():
            blockers.append(f"row_{index}:missing_term_id")
        if not str(row.get("term_name") or "").strip():
            blockers.append(f"row_{index}:missing_term_name")
    return {"blockers": blockers, "warnings": warnings}


def _plot_parameters(plot_type: str, parameters: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(parameters or {})
    payload.setdefault("plot_type", plot_type)
    payload.setdefault("top_n", 15)
    payload.setdefault("sort_by", "adjusted_p_value")
    payload.setdefault("fdr_threshold", 0.05)
    payload.setdefault("x_field", "enrichment_ratio" if plot_type == "ora_barplot" else "enrichment_ratio")
    payload.setdefault("y_field", "term_name")
    payload.setdefault("size_field", "overlap_count")
    payload.setdefault("color_field", "adjusted_p_value")
    payload.setdefault("term_label_field", "term_name")
    return payload


def _parameter_blockers(parameters: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    try:
        if int(parameters.get("top_n") or 0) <= 0:
            blockers.append("ora_plot_invalid_top_n")
    except (TypeError, ValueError):
        blockers.append("ora_plot_invalid_top_n")
    if str(parameters.get("sort_by") or "") not in ORA_PLOT_SORT_FIELDS:
        blockers.append("ora_plot_invalid_sort_by")
    try:
        fdr = float(parameters.get("fdr_threshold"))
        if fdr < 0 or fdr > 1:
            blockers.append("ora_plot_invalid_fdr_threshold")
    except (TypeError, ValueError):
        blockers.append("ora_plot_invalid_fdr_threshold")
    return blockers


def _plot_spec(source: dict[str, Any], plot_type: str, parameters: dict[str, Any], source_table: str) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.ora_plot_spec.v1",
        "plot_type": plot_type,
        "top_n": int(parameters.get("top_n") or 15),
        "sort_by": str(parameters.get("sort_by") or "adjusted_p_value"),
        "x_field": str(parameters.get("x_field") or "enrichment_ratio"),
        "y_field": str(parameters.get("y_field") or "term_name"),
        "size_field": str(parameters.get("size_field") or "overlap_count"),
        "color_field": str(parameters.get("color_field") or "adjusted_p_value"),
        "term_label_field": str(parameters.get("term_label_field") or "term_name"),
        "fdr_threshold": float(parameters.get("fdr_threshold") or 0.05),
        "source_result_id": str(source.get("result_id") or ""),
        "source_table": source_table,
        "rendering": "spec_only_no_image_dependency",
        "image_output": "none",
        "blockers": [],
        "warnings": [],
    }


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if _is_ora_candidate(entry)]
    return candidates[-1] if candidates else None


def _is_ora_candidate(entry: dict[str, Any]) -> bool:
    return str(entry.get("task_type") or "") == "ora_enrichment" and normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") in {"formal_computed_result", "imported_external_result"}


def _source_ora_table(root: Path, entry: dict[str, Any]) -> Path | None:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "ora_result_table"), {})
    raw = str(artifact.get("path") or "")
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return [dict(row) for row in csv.DictReader([first, *handle.readlines()], delimiter=delimiter)]


def _result_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "result_id": str(entry.get("result_id") or ""),
            "task_type": str(entry.get("task_type") or ""),
            "result_semantics": normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default=""),
        }
        for entry in entries
    ]


def _ora_plot_id(source: dict[str, Any], plot_type: str) -> str:
    return f"{source.get('result_id') or 'ora'}-{plot_type}-artifact"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _registry_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root) if _is_within(path, root) else path)
