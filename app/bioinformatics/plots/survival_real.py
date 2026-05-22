from __future__ import annotations

import hashlib
import html
import importlib.util
import json
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry, save_registry
from app.bioinformatics.survival_clinical._io import parse_float, read_table

from .models import PlotArtifact
from .schema import validate_plot_artifact


ENGINE_NAME = "biomedpilot_survival_svg_renderer"
ENGINE_VERSION = "0.1.0"
REAL_PLOT_SCOPE = "formal_survival_real_plot_artifact"
SUPPORTED_TASKS = {"survival_km_logrank", "cox_univariate", "cox_multivariate"}


def check_survival_plot_renderer_dependencies(*, renderer: str = "builtin_svg") -> dict[str, Any]:
    if renderer == "builtin_svg":
        return {
            "schema_version": "biomedpilot.survival_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "passed",
            "packages": {"biomedpilot_builtin_svg": {"available": True, "version": ENGINE_VERSION}},
            "blockers": [],
            "warnings": ["builtin_svg_renderer_no_external_plot_dependency"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "no_external_runtime_dependency_for_svg_survival_plots",
        }
    if renderer == "matplotlib_png":
        matplotlib = _package_status("matplotlib")
        return {
            "schema_version": "biomedpilot.survival_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "passed" if matplotlib["available"] else "blocked",
            "packages": {"matplotlib": matplotlib},
            "blockers": [] if matplotlib["available"] else ["matplotlib_missing_for_survival_plot_renderer"],
            "warnings": ["detect_first_no_auto_install"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "matplotlib_required_only_if_png_renderer_selected",
        }
    if renderer == "r_survminer":
        return {
            "schema_version": "biomedpilot.survival_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "blocked",
            "packages": {"R": {"available": False, "version": ""}, "survminer": {"available": False, "version": ""}},
            "blockers": ["r_survminer_renderer_not_configured"],
            "warnings": ["detect_first_no_auto_install"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "optional_external_r_renderer_not_bundled",
        }
    return {
        "schema_version": "biomedpilot.survival_plot_renderer_dependency_snapshot.v1",
        "renderer": renderer,
        "status": "blocked",
        "packages": {},
        "blockers": [f"unsupported_survival_plot_renderer:{renderer}"],
        "warnings": ["detect_first_no_auto_install"],
        "install_action": "none_detect_first_only",
        "packaging_impact": "unknown_renderer_not_bundled",
    }


def build_survival_real_plot_gate(project_root: str | Path, source_result_id: str, *, plot_type: str = "", renderer: str = "builtin_svg") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _source_entry(root, source_result_id)
    if source is None:
        return _gate("blocked", source_result_id, "", "", renderer, ["missing_source_result"], [], {})
    semantics = normalize_result_semantics(source.get("result_semantics"))
    task_type = str(source.get("task_type") or "")
    expected_plot_type = _plot_type_for_task(task_type, plot_type)
    blockers: list[str] = []
    warnings: list[str] = []
    if task_type not in SUPPORTED_TASKS:
        blockers.append("survival_real_plot_requires_formal_km_or_cox_result")
    if semantics != "formal_computed_result":
        blockers.append("survival_real_plot_requires_formal_computed_result_source")
    if source.get("validation_status") not in {"passed", "warning"} or source.get("blockers"):
        blockers.append("survival_real_plot_requires_valid_source_result")
    artifacts = _artifact_paths(source)
    required = _required_artifacts(task_type)
    missing = [name for name in required if not artifacts.get(name)]
    blockers.extend(f"missing_source_table:{name}" for name in missing)
    dependency = check_survival_plot_renderer_dependencies(renderer=renderer)
    if dependency.get("status") != "passed":
        blockers.extend(str(item) for item in dependency.get("blockers", []) or ["survival_plot_renderer_dependency_not_passed"])
    if renderer != "builtin_svg":
        blockers.append("survival_real_plot_png_r_renderer_not_enabled_in_b22")
    if not expected_plot_type:
        blockers.append("unsupported_survival_real_plot_source_task")
    return _gate("blocked" if blockers else "passed", source_result_id, task_type, expected_plot_type, renderer, blockers, warnings, dependency)


def create_survival_real_plot_artifact(project_root: str | Path, source_result_id: str, *, plot_type: str = "", renderer: str = "builtin_svg") -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_survival_real_plot_gate(root, source_result_id, plot_type=plot_type, renderer=renderer)
    source = _source_entry(root, source_result_id)
    if gate["status"] != "passed" or source is None:
        return _blocked_artifact(source_result_id, gate)
    task_type = str(source.get("task_type") or "")
    resolved_plot_type = str(gate.get("plot_type") or _plot_type_for_task(task_type, plot_type))
    artifact_paths = _artifact_paths(source)
    rows = _source_rows(root, task_type, artifact_paths)
    if not rows:
        gate["status"] = "blocked"
        gate["blockers"] = [*gate.get("blockers", []), "source_plot_table_has_no_rows"]
        return _blocked_artifact(source_result_id, gate)

    plot_id = _plot_id(source_result_id, resolved_plot_type)
    out_dir = root / "results" / "plots" / "survival"
    image_path = out_dir / f"{plot_id}.svg"
    manifest_path = out_dir / f"{plot_id}_manifest.json"
    if resolved_plot_type == "km_curve":
        svg_text = _km_svg(rows, source)
    else:
        svg_text = _cox_svg(rows, source, resolved_plot_type)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_text(svg_text, encoding="utf-8")

    semantics = normalize_result_semantics(source.get("result_semantics"))
    parameters = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    dependency = gate.get("renderer_dependency_snapshot") if isinstance(gate.get("renderer_dependency_snapshot"), dict) else {}
    artifact = PlotArtifact(
        plot_id=plot_id,
        plot_type=resolved_plot_type,
        source_result_id=source_result_id,
        source_result_semantics=semantics,
        source_task_type=task_type,
        plot_semantics=semantics,
        plot_artifact_scope=REAL_PLOT_SCOPE,
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest=parameters,
        plot_parameters={"renderer": renderer, "format": "svg", "clinical_interpretation": "not_allowed"},
        plot_spec_artifact={
            "schema_version": "biomedpilot.survival_real_plot_spec.v1",
            "plot_type": resolved_plot_type,
            "renderer": renderer,
            "format": "svg",
            "source_result_id": source_result_id,
            "source_task_type": task_type,
            "source_tables": artifact_paths,
            "rendering": "real_svg_artifact_no_report_ready",
        },
        image_artifacts=(
            {
                "artifact_type": f"{resolved_plot_type}_svg",
                "path": str(image_path),
                "format": "svg",
                "source_result_id": source_result_id,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
        ),
        table_artifacts=tuple({"artifact_type": key, "path": value} for key, value in artifact_paths.items() if key in _required_artifacts(task_type)),
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        dependency_snapshot=dependency,
        warnings=("Statistical plot artifact only; no clinical conclusion or report-ready export.",),
        blockers=(),
    ).to_dict()
    validation = validate_plot_artifact(artifact)
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation.get("blockers", [])]))
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation.get("warnings", [])]))
    artifact["plot_spec_artifact"]["plot_manifest_path"] = str(manifest_path)
    manifest = {
        "schema_version": "biomedpilot.survival_real_plot_manifest.v1",
        "plot_artifact": artifact,
        "gate_snapshot": gate,
        "report_ready_eligible": False,
        "limitations": ["statistical_plot_only", "no_clinical_conclusion", "no_survival_report_ready"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if artifact["blockers"]:
        return {"status": "blocked", "plot_artifact": artifact, "blockers": artifact["blockers"], "warnings": artifact["warnings"], "report_ready_eligible": False}

    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    for entry in entries:
        if entry.get("result_id") == source_result_id:
            entry["plot_artifacts"] = [*(entry.get("plot_artifacts", []) or []), artifact]
            entry["report_ready_eligible"] = False
            break
    save_registry(root, entries)
    return {"status": "passed", "plot_artifact": artifact, "plot_manifest_path": str(manifest_path), "report_ready_eligible": False, "warnings": artifact["warnings"], "blockers": []}


def _source_entry(root: Path, result_id: str) -> dict[str, Any] | None:
    registry = load_registry(root)
    for entry in registry.get("results", []) or []:
        if isinstance(entry, dict) and entry.get("result_id") == result_id:
            return entry
    return None


def _source_rows(root: Path, task_type: str, artifacts: dict[str, str]) -> list[dict[str, str]]:
    required = _required_artifacts(task_type)
    if not required:
        return []
    return read_table(str(_resolve_artifact_path(root, artifacts.get(required[0], ""))))


def _resolve_artifact_path(root: Path, path: str) -> Path:
    artifact = Path(path)
    return artifact if artifact.is_absolute() else root / artifact


def _artifact_paths(source: dict[str, Any]) -> dict[str, str]:
    return {str(item.get("artifact_type") or ""): str(item.get("path") or "") for item in source.get("output_artifacts", []) or [] if isinstance(item, dict)}


def _required_artifacts(task_type: str) -> tuple[str, ...]:
    if task_type == "survival_km_logrank":
        return ("km_curve_table",)
    if task_type == "cox_univariate":
        return ("cox_result_table",)
    if task_type == "cox_multivariate":
        return ("cox_multivariate_result_table",)
    return ()


def _plot_type_for_task(task_type: str, requested: str) -> str:
    if requested in {"km_curve", "cox_forest_plot"}:
        return requested
    if task_type == "survival_km_logrank":
        return "km_curve"
    if task_type in {"cox_univariate", "cox_multivariate"}:
        return "cox_forest_plot"
    return ""


def _gate(status: str, source_result_id: str, task_type: str, plot_type: str, renderer: str, blockers: list[str], warnings: list[str], dependency: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.survival_real_plot_gate.v1",
        "status": status,
        "source_result_id": source_result_id,
        "source_task_type": task_type,
        "plot_type": plot_type,
        "renderer": renderer,
        "image_format": "svg" if renderer == "builtin_svg" else "",
        "renderer_dependency_snapshot": dependency,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "report_ready_eligible": False,
    }


def _blocked_artifact(source_result_id: str, gate: dict[str, Any]) -> dict[str, Any]:
    plot_type = str(gate.get("plot_type") or "km_curve")
    artifact = PlotArtifact(
        plot_id=_plot_id(source_result_id or "missing", plot_type),
        plot_type=plot_type,
        source_result_id=source_result_id,
        source_result_semantics="blocked",
        source_task_type=str(gate.get("source_task_type") or ""),
        plot_semantics="blocked",
        plot_artifact_scope=REAL_PLOT_SCOPE,
        plot_parameters={"renderer": gate.get("renderer", ""), "format": gate.get("image_format", "")},
        plot_spec_artifact={"gate_snapshot": gate, "rendering": "blocked_no_image_artifact"},
        image_artifacts=(),
        dependency_snapshot=gate.get("renderer_dependency_snapshot") if isinstance(gate.get("renderer_dependency_snapshot"), dict) else {},
        blockers=tuple(str(item) for item in gate.get("blockers", []) or []),
        warnings=tuple(str(item) for item in gate.get("warnings", []) or []),
    ).to_dict()
    return {"status": "blocked", "plot_artifact": artifact, "report_ready_eligible": False, "warnings": artifact["warnings"], "blockers": artifact["blockers"]}


def _km_svg(rows: list[dict[str, str]], source: dict[str, Any]) -> str:
    width, height = 760, 440
    left, top, plot_w, plot_h = 70, 40, 610, 300
    times = [parse_float(row.get("time")) for row in rows]
    times = [value for value in times if value is not None]
    max_time = max(times) if times else 1.0
    groups = sorted({str(row.get("group") or "") for row in rows if str(row.get("group") or "")})
    colors = ["#2764c9", "#c43c39", "#2f8f5b", "#7a4fb3"]
    paths: list[str] = []
    for index, group in enumerate(groups):
        group_rows = [row for row in rows if str(row.get("group") or "") == group]
        points: list[str] = []
        for row in sorted(group_rows, key=lambda item: parse_float(item.get("time")) or 0.0):
            time = parse_float(row.get("time")) or 0.0
            survival = max(min(parse_float(row.get("survival_probability")) or 0.0, 1.0), 0.0)
            x = left + (time / max(max_time, 1.0)) * plot_w
            y = top + (1.0 - survival) * plot_h
            points.append(f"{x:.1f},{y:.1f}")
        if points:
            label_y = top + plot_h + 48 + index * 18
            color = colors[index % len(colors)]
            paths.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(points)}" />')
            paths.append(f'<line x1="{left}" y1="{label_y}" x2="{left + 24}" y2="{label_y}" stroke="{color}" stroke-width="2.5" />')
            paths.append(f'<text x="{left + 32}" y="{label_y + 5}" font-size="13">{html.escape(group)}</text>')
    title = html.escape(str(source.get("result_id") or "KM plot"))
    return _svg_frame(width, height, title, "Time", "Survival probability", paths)


def _cox_svg(rows: list[dict[str, str]], source: dict[str, Any], plot_type: str) -> str:
    width = 760
    row_h = 42
    height = max(260, 120 + len(rows) * row_h)
    left, top, plot_w = 250, 50, 420
    values = [_positive_float(row.get("hazard_ratio")) for row in rows]
    lows = [_positive_float(row.get("ci_lower")) for row in rows]
    highs = [_positive_float(row.get("ci_upper")) for row in rows]
    max_value = max([2.0, *values, *highs])
    parts: list[str] = []
    ref_x = left + (1.0 / max_value) * plot_w
    parts.append(f'<line x1="{ref_x:.1f}" y1="{top - 20}" x2="{ref_x:.1f}" y2="{height - 60}" stroke="#777" stroke-dasharray="4 4" />')
    for index, row in enumerate(rows):
        y = top + index * row_h
        label = html.escape(str(row.get("covariate_label") or row.get("covariate") or f"covariate {index + 1}"))
        hr = _positive_float(row.get("hazard_ratio"))
        lo = _positive_float(row.get("ci_lower"))
        hi = _positive_float(row.get("ci_upper"))
        p_value = html.escape(str(row.get("p_value") or ""))
        x = left + (hr / max_value) * plot_w
        x1 = left + (lo / max_value) * plot_w
        x2 = left + (hi / max_value) * plot_w
        parts.append(f'<text x="30" y="{y + 6}" font-size="13">{label}</text>')
        parts.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="#2d5b83" stroke-width="2" />')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#2d5b83" />')
        parts.append(f'<text x="{left + plot_w + 16}" y="{y + 5}" font-size="12">p={p_value}</text>')
    title = html.escape(f"{source.get('result_id') or plot_type} Cox forest plot")
    return _svg_frame(width, height, title, "Hazard ratio", "", parts)


def _svg_frame(width: int, height: int, title: str, x_label: str, y_label: str, body: list[str]) -> str:
    left, top, plot_w, plot_h = 70, 40, 610, min(300, max(height - 140, 120))
    axis = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />',
        f'<text x="{left}" y="24" font-size="16" font-weight="600">{title}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#222" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#222" />',
        f'<text x="{left + plot_w / 2 - 30:.1f}" y="{top + plot_h + 34}" font-size="13">{html.escape(x_label)}</text>',
        f'<text x="16" y="{top + plot_h / 2:.1f}" font-size="13">{html.escape(y_label)}</text>' if y_label else "",
        f'<text x="{left}" y="{height - 16}" font-size="12" fill="#555">Statistical visualization only; no clinical conclusion or treatment recommendation.</text>',
    ]
    return "<svg xmlns=\"http://www.w3.org/2000/svg\" " f"width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">\n" + "\n".join(item for item in [*axis, *body] if item) + "\n</svg>\n"


def _positive_float(value: Any) -> float:
    parsed = parse_float(value)
    if parsed is None:
        return 0.0
    return max(float(parsed), 0.0)


def _package_status(name: str) -> dict[str, Any]:
    available = importlib.util.find_spec(name) is not None
    version = ""
    if available:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = "unknown"
    return {"available": available, "version": version}


def _plot_id(source_result_id: str, plot_type: str) -> str:
    digest = hashlib.sha1(f"{source_result_id}:{plot_type}".encode("utf-8")).hexdigest()[:12]
    prefix = "km" if plot_type == "km_curve" else "cox"
    return f"plot-{prefix}-real-{digest}"
