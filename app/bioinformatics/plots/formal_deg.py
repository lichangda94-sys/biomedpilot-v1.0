from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from app.bioinformatics.deg_engine.result_schema import validate_formal_deg_result_index_entry
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry

from .basic_renderers import build_basic_plot_spec
from .models import PlotArtifact
from .schema import validate_plot_artifact


FORMAL_DEG_PLOT_GATE_SCHEMA_VERSION = "biomedpilot.formal_deg_plot_gate.v1"
FORMAL_DEG_PLOT_PRODUCTION_GATE_SCHEMA_VERSION = "biomedpilot.formal_deg_plot_production_gate.v1"
FORMAL_DEG_PLOT_TYPES = {"volcano_plot", "deg_heatmap"}
FORMAL_DEG_PLOT_GUARD_COPY = (
    "Formal DEG plot artifacts visualize statistical analysis results only. "
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


def build_formal_deg_plot_production_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    plot_type: str = "volcano_plot",
    renderer_capability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_gate = build_formal_deg_plot_gate(project_root, result_id=result_id, plot_type=plot_type)
    renderer = renderer_capability or _default_renderer_capability(plot_type)
    blockers = list(base_gate.get("blockers", []) or [])
    warnings = list(base_gate.get("warnings", []) or [])
    if renderer.get("status") != "passed":
        blockers.extend(str(item) for item in renderer.get("blockers", []) or ["plot_renderer_capability_not_passed"])
    return {
        "schema_version": FORMAL_DEG_PLOT_PRODUCTION_GATE_SCHEMA_VERSION,
        "status": "blocked" if blockers else "passed",
        "selected_result_id": base_gate.get("selected_result_id", ""),
        "plot_type": plot_type,
        "source_result_semantics": base_gate.get("source_result_semantics", ""),
        "base_plot_gate": base_gate,
        "renderer_capability": renderer,
        "registers_to_result_index": True,
        "inherits_source_semantics": True,
        "report_ready_eligible_changed": False,
        "clinical_conclusion_enabled": False,
        "guard_copy": FORMAL_DEG_PLOT_GUARD_COPY,
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
    spec = build_basic_plot_spec(source, plot_type, parameters=parameters)
    image_artifacts: list[dict[str, Any]] = []
    renderer_warnings: list[str] = []
    renderer_blockers: list[str] = []
    renderer_log_artifact: dict[str, Any] = {}
    if plot_type == "volcano_plot":
        rendered = _render_volcano_svg(root, source, plot_type, parameters=parameters or {})
    elif plot_type == "deg_heatmap":
        rendered = _render_heatmap_svg(root, source, plot_type, parameters=parameters or {})
    else:
        rendered = {"image_artifacts": [], "warnings": [], "blockers": []}
    if plot_type in {"volcano_plot", "deg_heatmap"}:
        image_artifacts = rendered.get("image_artifacts", [])
        renderer_warnings = rendered.get("warnings", [])
        renderer_blockers = rendered.get("blockers", [])
        renderer_log_artifact = rendered.get("renderer_log_artifact", {})
    artifact = PlotArtifact(
        plot_id=_formal_plot_id(source, plot_type),
        plot_type=plot_type,
        source_result_id=str(source.get("result_id") or ""),
        source_result_semantics=source_semantics,
        plot_semantics=source_semantics,
        plot_artifact_scope="formal_deg_plot",
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest={
            "source_parameters_manifest": source.get("parameters_manifest", {}),
            "multifactor_design_provenance": _multifactor_design_provenance(source),
            "plot_parameters": parameters or {},
            "plot_policy": "formal_deg_plot_artifact_only_not_report_ready",
        },
        plot_spec_artifact=spec,
        image_artifacts=tuple(image_artifacts),
        table_artifacts=tuple(_source_deg_tables(source)),
        engine_name=_renderer_engine_name(plot_type),
        engine_version="0.1.0" if plot_type == "volcano_plot" else "0.1.0",
        dependency_snapshot={
            **(source.get("dependency_snapshot") if isinstance(source.get("dependency_snapshot"), dict) else {}),
            "plot_renderer": _default_renderer_capability(plot_type),
        },
        warnings=tuple([*(spec.get("warnings", []) or []), *renderer_warnings]),
        blockers=tuple([*(spec.get("blockers", []) or []), *renderer_blockers]),
    ).to_dict()
    if renderer_log_artifact:
        artifact["renderer_log_artifact"] = renderer_log_artifact
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


def _multifactor_design_provenance(entry: dict[str, Any]) -> dict[str, Any]:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    keys = ("design_formula", "contrast", "covariates", "batch_variables", "design_rank", "residual_degrees_of_freedom", "contrast_estimability", "backend_method")
    return {key: parameters.get(key) for key in keys if key in parameters}


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


def _renderer_engine_name(plot_type: str) -> str:
    if plot_type == "volcano_plot":
        return "biomedpilot_svg_volcano_renderer"
    if plot_type == "deg_heatmap":
        return "biomedpilot_svg_deg_summary_heatmap_renderer"
    return "biomedpilot_plot_spec"


def _default_renderer_capability(plot_type: str) -> dict[str, Any]:
    if plot_type == "volcano_plot":
        return {
            "status": "passed",
            "renderer": "biomedpilot_builtin_svg_volcano",
            "version": "0.1.0",
            "output_formats": ["svg"],
            "dependency_policy": "stdlib_only_no_external_renderer",
            "blockers": [],
        }
    if plot_type == "deg_heatmap":
        return {
            "status": "passed",
            "renderer": "biomedpilot_builtin_svg_deg_summary_heatmap",
            "version": "0.1.0",
            "output_formats": ["svg"],
            "dependency_policy": "stdlib_only_no_external_renderer",
            "blockers": [],
        }
    return {"status": "blocked", "renderer": "spec_only", "blockers": ["real_deg_plot_renderer_not_activated"]}


def _render_volcano_svg(root: Path, source: dict[str, Any], plot_type: str, *, parameters: dict[str, Any]) -> dict[str, Any]:
    table = _source_table_path(root, source)
    rows = _read_deg_rows(table)
    blockers: list[str] = []
    warnings: list[str] = []
    if not rows:
        blockers.append("volcano_renderer_requires_non_empty_deg_table")
        return {"image_artifacts": [], "renderer_log_artifact": {}, "warnings": warnings, "blockers": blockers}
    points = []
    for row in rows:
        try:
            log2fc = float(str(row.get("log2_fold_change") or row.get("log2FC") or ""))
            adjusted = float(str(row.get("adjusted_p_value") or row.get("FDR") or row.get("fdr") or ""))
        except (TypeError, ValueError):
            warnings.append("volcano_renderer_skipped_non_numeric_row")
            continue
        if adjusted <= 0:
            adjusted = 1e-300
        points.append(
            {
                "feature_id": str(row.get("feature_id") or ""),
                "gene_symbol": str(row.get("gene_symbol") or row.get("feature_id") or ""),
                "x": log2fc,
                "y": -math.log10(adjusted),
                "significance_label": str(row.get("significance_label") or ""),
            }
        )
    if not points:
        blockers.append("volcano_renderer_no_numeric_points")
        return {"image_artifacts": [], "renderer_log_artifact": {}, "warnings": warnings, "blockers": blockers}
    result_id = str(source.get("result_id") or "formal_deg")
    plot_id = _formal_plot_id(source, plot_type)
    plot_dir = root / "plots" / "formal_deg" / _safe_name(result_id)
    plot_dir.mkdir(parents=True, exist_ok=True)
    svg_path = plot_dir / f"{plot_id}.svg"
    log_path = plot_dir / f"{plot_id}.renderer_log.json"
    svg_path.write_text(_volcano_svg(points, result_id=result_id, parameters=parameters), encoding="utf-8")
    checksum = hashlib.sha256(svg_path.read_bytes()).hexdigest()
    log_payload = {
        "schema_version": "biomedpilot.formal_deg_volcano_renderer_log.v1",
        "plot_id": plot_id,
        "source_result_id": result_id,
        "renderer": "biomedpilot_builtin_svg_volcano",
        "format": "svg",
        "point_count": len(points),
        "warnings": warnings,
        "blockers": blockers,
        "clinical_conclusion_enabled": False,
    }
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "image_artifacts": [
            {
                "artifact_type": "formal_deg_volcano_svg",
                "path": str(svg_path.relative_to(root)),
                "format": "svg",
                "mime_type": "image/svg+xml",
                "sha256": checksum,
                "renderer": "biomedpilot_builtin_svg_volcano",
                "semantic_boundary": "statistical_visualization_only_not_clinical_conclusion",
            }
        ],
        "renderer_log_artifact": {
            "artifact_type": "formal_deg_plot_renderer_log",
            "path": str(log_path.relative_to(root)),
            "schema": "biomedpilot.formal_deg_volcano_renderer_log.v1",
        },
        "warnings": warnings,
        "blockers": blockers,
    }


def _source_table_path(root: Path, source: dict[str, Any]) -> Path:
    tables = _source_deg_tables(source)
    if not tables:
        return root / "__missing_deg_table__"
    raw = Path(str(tables[0].get("path") or tables[0].get("file_path") or ""))
    return raw if raw.is_absolute() else root / raw


def _render_heatmap_svg(root: Path, source: dict[str, Any], plot_type: str, *, parameters: dict[str, Any]) -> dict[str, Any]:
    table = _source_table_path(root, source)
    rows = _read_deg_rows(table)
    blockers: list[str] = []
    warnings: list[str] = []
    heatmap_rows = []
    top_n = int(parameters.get("top_n") or 25)
    for row in rows:
        try:
            case_mean = float(str(row.get("case_mean") or row.get("case") or ""))
            control_mean = float(str(row.get("control_mean") or row.get("control") or ""))
            fdr = float(str(row.get("adjusted_p_value") or row.get("FDR") or row.get("fdr") or "1"))
        except (TypeError, ValueError):
            warnings.append("heatmap_renderer_skipped_row_without_case_control_means")
            continue
        heatmap_rows.append(
            {
                "gene_symbol": str(row.get("gene_symbol") or row.get("feature_id") or "feature"),
                "case_mean": case_mean,
                "control_mean": control_mean,
                "rank": fdr,
            }
        )
    heatmap_rows = sorted(heatmap_rows, key=lambda item: item["rank"])[:top_n]
    if not heatmap_rows:
        blockers.append("deg_heatmap_renderer_requires_case_control_mean_columns")
        return {"image_artifacts": [], "renderer_log_artifact": {}, "warnings": warnings, "blockers": blockers}
    result_id = str(source.get("result_id") or "formal_deg")
    plot_id = _formal_plot_id(source, plot_type)
    plot_dir = root / "plots" / "formal_deg" / _safe_name(result_id)
    plot_dir.mkdir(parents=True, exist_ok=True)
    svg_path = plot_dir / f"{plot_id}.svg"
    log_path = plot_dir / f"{plot_id}.renderer_log.json"
    svg_path.write_text(_heatmap_svg(heatmap_rows, result_id=result_id), encoding="utf-8")
    checksum = hashlib.sha256(svg_path.read_bytes()).hexdigest()
    log_payload = {
        "schema_version": "biomedpilot.formal_deg_heatmap_renderer_log.v1",
        "plot_id": plot_id,
        "source_result_id": result_id,
        "renderer": "biomedpilot_builtin_svg_deg_summary_heatmap",
        "format": "svg",
        "row_count": len(heatmap_rows),
        "warnings": warnings,
        "blockers": blockers,
        "semantic_note": "summary heatmap from DEG case/control means, not sample-level expression heatmap",
        "clinical_conclusion_enabled": False,
    }
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "image_artifacts": [
            {
                "artifact_type": "formal_deg_summary_heatmap_svg",
                "path": str(svg_path.relative_to(root)),
                "format": "svg",
                "mime_type": "image/svg+xml",
                "sha256": checksum,
                "renderer": "biomedpilot_builtin_svg_deg_summary_heatmap",
                "semantic_boundary": "deg_summary_heatmap_not_sample_level_expression_heatmap",
            }
        ],
        "renderer_log_artifact": {
            "artifact_type": "formal_deg_plot_renderer_log",
            "path": str(log_path.relative_to(root)),
            "schema": "biomedpilot.formal_deg_heatmap_renderer_log.v1",
        },
        "warnings": warnings,
        "blockers": blockers,
    }


def _read_deg_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return list(csv.DictReader([first, *handle.readlines()], delimiter=delimiter))


def _volcano_svg(points: list[dict[str, Any]], *, result_id: str, parameters: dict[str, Any]) -> str:
    width = 900
    height = 620
    margin_left = 82
    margin_right = 34
    margin_top = 52
    margin_bottom = 78
    xs = [float(point["x"]) for point in points]
    ys = [float(point["y"]) for point in points]
    x_abs = max(1.0, max(abs(min(xs)), abs(max(xs))))
    y_max = max(1.0, max(ys))
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    def sx(value: float) -> float:
        return margin_left + ((value + x_abs) / (2 * x_abs)) * plot_width

    def sy(value: float) -> float:
        return margin_top + (1 - value / y_max) * plot_height

    circles = []
    for point in points:
        label = _xml_escape(str(point.get("gene_symbol") or point.get("feature_id") or "feature"))
        x = sx(float(point["x"]))
        y = sy(float(point["y"]))
        color = _volcano_color(str(point.get("significance_label") or ""))
        circles.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.2" fill="{color}" opacity="0.82"><title>{label}</title></circle>')
    threshold = parameters.get("fdr_threshold", 0.05)
    threshold_line = ""
    try:
        threshold_y = sy(-math.log10(float(threshold)))
        threshold_line = f'<line x1="{margin_left}" y1="{threshold_y:.2f}" x2="{width - margin_right}" y2="{threshold_y:.2f}" stroke="#7a869a" stroke-dasharray="6 6" stroke-width="1.5"/>'
    except (TypeError, ValueError):
        threshold_line = ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620" role="img" aria-label="Formal DEG volcano plot">\n'
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#1f2937}.axis{stroke:#374151;stroke-width:1.4}.grid{stroke:#e5e7eb;stroke-width:1}</style>\n"
        f'<rect width="900" height="620" fill="#ffffff"/><text x="82" y="32" font-size="20" font-weight="650">Formal DEG Volcano Plot</text><text x="82" y="54" font-size="12">Result: {_xml_escape(result_id)} | statistical visualization only</text>\n'
        f'<line class="axis" x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}"/><line class="axis" x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}"/>\n'
        f'<line class="grid" x1="{sx(0):.2f}" y1="{margin_top}" x2="{sx(0):.2f}" y2="{height - margin_bottom}"/>{threshold_line}\n'
        + "\n".join(circles)
        + f'\n<text x="{width / 2 - 80:.0f}" y="{height - 28}" font-size="14">log2 fold change</text><text transform="translate(24 {height / 2 + 80:.0f}) rotate(-90)" font-size="14">-log10 adjusted p-value</text>\n'
        '<text x="82" y="594" font-size="11">No clinical diagnosis, prognosis, or treatment recommendation is implied.</text></svg>\n'
    )


def _heatmap_svg(rows: list[dict[str, Any]], *, result_id: str) -> str:
    width = 760
    row_height = 24
    margin_left = 180
    margin_top = 74
    cell_width = 150
    height = margin_top + len(rows) * row_height + 70
    values = [float(row["case_mean"]) for row in rows] + [float(row["control_mean"]) for row in rows]
    v_min = min(values)
    v_max = max(values)
    span = v_max - v_min or 1.0

    def color(value: float) -> str:
        ratio = (value - v_min) / span
        red = int(245 * ratio + 37 * (1 - ratio))
        blue = int(49 * ratio + 153 * (1 - ratio))
        green = int(89 * ratio + 99 * (1 - ratio))
        return f"#{red:02x}{green:02x}{blue:02x}"

    cells = []
    for index, row in enumerate(rows):
        y = margin_top + index * row_height
        label = _xml_escape(str(row["gene_symbol"]))
        cells.append(f'<text x="24" y="{y + 16}" font-size="12">{label}</text>')
        for col, key in enumerate(("case_mean", "control_mean")):
            x = margin_left + col * cell_width
            value = float(row[key])
            cells.append(f'<rect x="{x}" y="{y}" width="{cell_width - 2}" height="{row_height - 2}" fill="{color(value)}"><title>{label} {key}: {value:.4g}</title></rect>')
            cells.append(f'<text x="{x + 10}" y="{y + 16}" font-size="11" fill="#ffffff">{value:.3g}</text>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Formal DEG summary heatmap">\n'
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#1f2937}</style>\n"
        f'<rect width="{width}" height="{height}" fill="#ffffff"/><text x="24" y="32" font-size="20" font-weight="650">Formal DEG Summary Heatmap</text><text x="24" y="54" font-size="12">Result: {_xml_escape(result_id)} | case/control means, not sample-level expression</text>\n'
        f'<text x="{margin_left + 42}" y="68" font-size="12" font-weight="650">Case mean</text><text x="{margin_left + cell_width + 32}" y="68" font-size="12" font-weight="650">Control mean</text>\n'
        + "\n".join(cells)
        + f'\n<text x="24" y="{height - 24}" font-size="11">Statistical visualization only. No clinical conclusion or treatment recommendation is implied.</text></svg>\n'
    )


def _volcano_color(label: str) -> str:
    normalized = label.lower()
    if "up" in normalized:
        return "#c2410c"
    if "down" in normalized:
        return "#2563eb"
    if "significant" in normalized:
        return "#7c3aed"
    return "#64748b"


def _xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "formal_deg"
