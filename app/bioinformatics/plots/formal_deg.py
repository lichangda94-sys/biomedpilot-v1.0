from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.deg_engine.result_schema import validate_formal_deg_result_index_entry
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry

from .models import PlotArtifact
from .real_svg import ENGINE_NAME as REAL_SVG_ENGINE_NAME
from .real_svg import ENGINE_VERSION as REAL_SVG_ENGINE_VERSION
from .real_svg import build_real_svg_payload, read_delimited_rows, write_plot_manifest
from .schema import validate_plot_artifact


FORMAL_DEG_PLOT_GATE_SCHEMA_VERSION = "biomedpilot.formal_deg_plot_gate.v1"
FORMAL_DEG_PLOT_TYPES = {"volcano_plot", "deg_heatmap"}
FORMAL_DEG_PLOT_GUARD_COPY = (
    "Formal DEG plot artifacts render SVG statistical analysis visualizations only. "
    "They are not clinical conclusions or treatment recommendations."
)


def build_formal_deg_plot_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    plot_type: str = "volcano_plot",
) -> dict[str, Any]:
    registry = load_registry(project_root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_entry(entries, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    if plot_type not in FORMAL_DEG_PLOT_TYPES:
        blockers.append(f"unsupported_formal_deg_plot_type:{plot_type}")
    if selected is None:
        blockers.append("formal_deg_result_not_found")
    else:
        source_validation = _validate_formal_plot_source(selected)
        blockers.extend(source_validation["blockers"])
        warnings.extend(source_validation["warnings"])
    return {
        "schema_version": FORMAL_DEG_PLOT_GATE_SCHEMA_VERSION,
        "status": "blocked" if blockers else "passed",
        "selected_result_id": str(selected.get("result_id") or "") if selected else str(result_id or ""),
        "plot_type": plot_type,
        "allowed_plot_types": sorted(FORMAL_DEG_PLOT_TYPES),
        "source_result_semantics": normalize_result_semantics((selected or {}).get("canonical_result_semantics") or (selected or {}).get("result_semantics"), default=""),
        "existing_plot_artifacts": list((selected or {}).get("plot_artifacts", []) or []),
        "result_options": _result_options(entries),
        "result_index_path": str(Path(project_root).expanduser().resolve() / RESULT_INDEX),
        "guard_copy": FORMAL_DEG_PLOT_GUARD_COPY,
        "report_ready_eligible": bool((selected or {}).get("report_ready_eligible")),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_formal_deg_plot_artifact(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    plot_type: str = "volcano_plot",
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_formal_deg_plot_gate(root, result_id=result_id, plot_type=plot_type)
    if gate.get("status") != "passed":
        return {
            "schema_version": FORMAL_DEG_PLOT_GATE_SCHEMA_VERSION,
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
    source_table = _source_deg_table(root, source) or Path()
    source_table_ref = _registry_path(source_table, root)
    rows = read_delimited_rows(source_table) if source_table.is_file() else []
    plot_id = _formal_plot_id(source, plot_type)
    render = build_real_svg_payload(
        root,
        source=source,
        source_table=source_table,
        source_table_ref=source_table_ref,
        plot_id=plot_id,
        plot_type=plot_type,
        section="deg",
        rows=rows,
        parameters=parameters or {},
    )
    artifact = PlotArtifact(
        plot_id=plot_id,
        plot_type=plot_type,
        source_result_id=str(source.get("result_id") or ""),
        source_result_semantics=source_semantics,
        plot_semantics=source_semantics,
        plot_artifact_scope="formal_deg_plot",
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest={
            "source_parameters_manifest": source.get("parameters_manifest", {}),
            "plot_parameters": parameters or {},
            "plot_policy": "formal_deg_real_svg_plot_artifact_only_not_report_ready",
        },
        plot_spec_artifact=render.get("plot_spec_artifact", {}),
        image_artifacts=tuple(render.get("image_artifacts", []) or []),
        table_artifacts=tuple(_source_deg_tables(source)),
        engine_name=REAL_SVG_ENGINE_NAME,
        engine_version=REAL_SVG_ENGINE_VERSION,
        dependency_snapshot=render.get("dependency_snapshot") if isinstance(render.get("dependency_snapshot"), dict) else {},
        warnings=tuple(render.get("warnings", []) or []),
        blockers=tuple(render.get("blockers", []) or []),
    ).to_dict()
    validation = validate_plot_artifact(artifact)
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation.get("warnings", [])]))
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation.get("blockers", [])]))
    if artifact["blockers"]:
        return {
            "schema_version": FORMAL_DEG_PLOT_GATE_SCHEMA_VERSION,
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
    if render.get("manifest_path"):
        write_plot_manifest(
            str(render["manifest_path"]),
            plot_artifact=artifact,
            gate_snapshot=gate,
            limitations=["statistical_visualization_only", "no_clinical_conclusion", "no_report_ready_unlock"],
        )
    existing = [item for item in source.get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_id") != artifact["plot_id"]]
    source["plot_artifacts"] = [*existing, artifact]
    source["report_artifacts"] = list(source.get("report_artifacts", []) or [])
    source["report_ready_eligible"] = False
    save_registry(root, entries)
    return {
        "schema_version": FORMAL_DEG_PLOT_GATE_SCHEMA_VERSION,
        "status": "passed",
        "plot_type": plot_type,
        "result_id": str(source.get("result_id") or ""),
        "plot_artifact": artifact,
        "plot_artifacts": list(source.get("plot_artifacts", []) or []),
        "report_artifacts": list(source.get("report_artifacts", []) or []),
        "report_ready_eligible": False,
        "result_index_path": str(root / RESULT_INDEX),
        "guard_copy": FORMAL_DEG_PLOT_GUARD_COPY,
        "blockers": [],
        "warnings": artifact["warnings"],
    }


def _select_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    formal = [entry for entry in entries if _is_formal_deg_candidate(entry)]
    return formal[-1] if formal else None


def _validate_formal_plot_source(entry: dict[str, Any]) -> dict[str, list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"formal_deg_plot_requires_formal_computed_result_source:{semantics or 'unknown'}")
    if str(entry.get("task_type") or "").lower() != "deg":
        blockers.append("formal_deg_plot_requires_deg_task_type")
    if not _source_deg_tables(entry):
        blockers.append("formal_deg_plot_requires_deg_result_table")
    schema_validation = validate_formal_deg_result_index_entry(entry)
    blockers.extend(str(item) for item in schema_validation.get("blockers", []) or [])
    warnings.extend(str(item) for item in schema_validation.get("warnings", []) or [])
    return {"blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _is_formal_deg_candidate(entry: dict[str, Any]) -> bool:
    return (
        normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result"
        and str(entry.get("task_type") or "").lower() == "deg"
        and bool(_source_deg_tables(entry))
    )


def _source_deg_tables(entry: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    return [dict(item) for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"]


def _source_deg_table(root: Path, entry: dict[str, Any]) -> Path | None:
    tables = _source_deg_tables(entry)
    raw = str((tables[0] if tables else {}).get("path") or "")
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def _result_options(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "result_id": str(entry.get("result_id") or ""),
            "task_type": str(entry.get("task_type") or ""),
            "result_semantics": normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default=""),
        }
        for entry in entries
    ]


def _formal_plot_id(source: dict[str, Any], plot_type: str) -> str:
    return f"{source.get('result_id') or 'formal-deg'}-{plot_type}-artifact"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _registry_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root) if _is_within(path, root) else path)
