from __future__ import annotations

import hashlib
import html
import importlib.util
import json
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from app.bioinformatics.plots.models import PlotArtifact
from app.bioinformatics.plots.schema import validate_plot_artifact
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry, save_registry

from ._io import parse_float, read_table


RISK_SCORE_PLOT_ARTIFACT_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_plot_artifact_activation_gate.v1"
RISK_SCORE_PLOT_ARTIFACT_SCHEMA_VERSION = "biomedpilot.risk_score_plot_artifact.v1"
RISK_SCORE_PLOT_ARTIFACT_SCOPE = "formal_risk_score_plot_artifact"
RISK_SCORE_PLOT_ENGINE_NAME = "biomedpilot_risk_score_visualization_renderer"
RISK_SCORE_PLOT_ENGINE_VERSION = "0.1.0"
RISK_SCORE_REAL_PLOT_MANIFEST_SCHEMA_VERSION = "biomedpilot.risk_score_real_plot_manifest.v1"
SUPPORTED_RISK_SCORE_PLOT_TYPES = (
    "risk_score_distribution_plot",
    "risk_score_nomogram",
    "risk_score_calibration_curve",
    "risk_score_decision_curve",
)
FORBIDDEN_RISK_SCORE_PLOT_FIELDS = (
    "risk_group",
    "high_risk_group",
    "low_risk_group",
    "clinical_risk_group",
    "prognosis_label",
    "diagnosis",
    "treatment_recommendation",
    "clinical_conclusion",
    "clinical_decision_recommendation",
    "report_ready_package",
)


def check_risk_score_plot_renderer_dependencies(*, renderer: str = "builtin_svg") -> dict[str, Any]:
    if renderer == "builtin_svg":
        return {
            "schema_version": "biomedpilot.risk_score_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "passed",
            "packages": {"biomedpilot_builtin_svg": {"available": True, "version": RISK_SCORE_PLOT_ENGINE_VERSION}},
            "blockers": [],
            "warnings": ["builtin_svg_renderer_no_external_plot_dependency", "detect_first_no_auto_install"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "no_external_runtime_dependency_for_future_svg_risk_score_plots",
        }
    if renderer == "matplotlib_png":
        matplotlib = _package_status("matplotlib")
        return {
            "schema_version": "biomedpilot.risk_score_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "passed" if matplotlib["available"] else "blocked",
            "packages": {"matplotlib": matplotlib},
            "blockers": [] if matplotlib["available"] else ["matplotlib_missing_for_risk_score_plot_renderer"],
            "warnings": ["detect_first_no_auto_install"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "optional_matplotlib_png_renderer_not_required_for_b37",
        }
    if renderer == "r_rms_nomogram":
        return {
            "schema_version": "biomedpilot.risk_score_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "blocked",
            "packages": {
                "Rscript": {"available": False, "version": ""},
                "rms": {"available": False, "version": ""},
            },
            "blockers": ["r_rms_nomogram_renderer_not_enabled"],
            "warnings": ["detect_first_no_auto_install", "external_r_renderer_not_bundled"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "optional_external_r_renderer_requires_separate_runtime_acceptance",
        }
    return {
        "schema_version": "biomedpilot.risk_score_plot_renderer_dependency_snapshot.v1",
        "renderer": renderer,
        "status": "blocked",
        "packages": {},
        "blockers": [f"unsupported_risk_score_plot_renderer:{renderer}"],
        "warnings": ["detect_first_no_auto_install"],
        "install_action": "none_detect_first_only",
        "packaging_impact": "unknown_renderer_not_bundled",
    }


def build_risk_score_plot_artifact_activation_gate(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    plot_type: str = "risk_score_distribution_plot",
    renderer: str = "builtin_svg",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _select_source(root, result_id)
    dependency = check_risk_score_plot_renderer_dependencies(renderer=renderer)
    blockers: list[str] = []
    warnings = [
        "risk_score_plot_schema_defined_but_execution_disabled",
        "no_plot_artifact_created_in_b37",
        "no_nomogram_generated_in_b37",
        "no_report_ready_unlock",
        "no_clinical_interpretation",
    ]
    if source is None:
        blockers.append("formal_risk_score_result_not_found")
    else:
        blockers.extend(_source_blockers(source))
    if plot_type not in SUPPORTED_RISK_SCORE_PLOT_TYPES:
        blockers.append(f"unsupported_risk_score_plot_type:{plot_type}")
    if dependency.get("status") != "passed":
        blockers.extend(str(item) for item in dependency.get("blockers", []) or ["risk_score_plot_renderer_dependency_not_passed"])
    if plot_type != "risk_score_distribution_plot":
        blockers.append(f"risk_score_plot_type_not_enabled_in_b38:{plot_type}")
    if renderer != "builtin_svg":
        blockers.append(f"risk_score_plot_renderer_not_enabled_in_b38:{renderer}")

    schema_candidate = build_risk_score_plot_artifact_schema_candidate(
        source or {},
        plot_type=plot_type if plot_type in SUPPORTED_RISK_SCORE_PLOT_TYPES else "risk_score_distribution_plot",
        renderer=renderer,
        dependency_snapshot=dependency,
    )
    schema_validation = validate_risk_score_plot_artifact_schema(schema_candidate)
    schema_blockers = [str(item) for item in schema_validation.get("blockers", []) or [] if item != "missing_source_result_id"]
    blockers.extend(schema_blockers)
    source_ready = bool(source) and not blockers
    status = "passed" if source_ready else "blocked"
    return {
        "schema_version": RISK_SCORE_PLOT_ARTIFACT_GATE_SCHEMA_VERSION,
        "status": status,
        "source_ready_for_future_activation": source_ready,
        "selected_result_id": str((source or {}).get("result_id") or result_id or ""),
        "source_result_semantics": normalize_result_semantics((source or {}).get("result_semantics"), default="blocked"),
        "source_task_type": str((source or {}).get("task_type") or ""),
        "plot_type": plot_type,
        "renderer": renderer,
        "renderer_dependency_snapshot": dependency,
        "artifact_schema_candidate": schema_candidate,
        "artifact_schema_validation": schema_validation,
        "formal_execution_enabled": False,
        "writes_result_index": source_ready,
        "creates_plot_artifact": source_ready,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "minimum_conditions": {
            "formal_risk_score_result": "required",
            "risk_score_result_table": "required",
            "parameter_confirmation": "required",
            "dependency_snapshot_passed": "required",
            "renderer_dependency_passed": "required",
            "artifact_schema_validation": "required",
            "b38_renderer_execution_audit": "passed_for_builtin_svg_distribution_only" if source_ready else "required_before_artifact_creation",
        },
        "forbidden_outputs": list(FORBIDDEN_RISK_SCORE_PLOT_FIELDS),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_risk_score_plot_artifact(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    plot_type: str = "risk_score_distribution_plot",
    renderer: str = "builtin_svg",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_risk_score_plot_artifact_activation_gate(root, result_id=result_id, plot_type=plot_type, renderer=renderer)
    source = _select_source(root, result_id)
    if gate.get("status") != "passed" or source is None:
        return _blocked_artifact(str(result_id or gate.get("selected_result_id") or ""), gate)

    table_path = _risk_score_table_path(root, source)
    rows = _risk_score_rows(table_path)
    if not rows:
        blocked_gate = {**gate, "status": "blocked", "blockers": [*gate.get("blockers", []), "risk_score_plot_source_table_empty"]}
        return _blocked_artifact(str(source.get("result_id") or ""), blocked_gate)

    plot_id = _plot_id(str(source.get("result_id") or ""), plot_type)
    out_dir = root / "results" / "plots" / "risk_score"
    image_path = out_dir / f"{plot_id}.svg"
    manifest_path = out_dir / f"{plot_id}_manifest.json"
    dependency = gate.get("renderer_dependency_snapshot") if isinstance(gate.get("renderer_dependency_snapshot"), dict) else {}
    artifact = _plot_artifact(source, plot_id, plot_type, renderer, dependency, table_path, image_path)
    validation = validate_risk_score_plot_artifact_schema(artifact)
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation.get("blockers", [])]))
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation.get("warnings", [])]))
    if artifact["blockers"]:
        return {"status": "blocked", "plot_artifact": artifact, "report_ready_eligible": False, "warnings": artifact["warnings"], "blockers": artifact["blockers"]}

    out_dir.mkdir(parents=True, exist_ok=True)
    image_path.write_text(_distribution_svg(rows, source), encoding="utf-8")
    artifact["plot_spec_artifact"]["plot_manifest_path"] = str(manifest_path)
    manifest = {
        "schema_version": RISK_SCORE_REAL_PLOT_MANIFEST_SCHEMA_VERSION,
        "plot_artifact": artifact,
        "gate_snapshot": gate,
        "source_row_count": len(rows),
        "report_ready_eligible": False,
        "limitations": [
            "statistical_visualization_only",
            "no_risk_group_generation",
            "no_clinical_conclusion",
            "no_report_ready_unlock",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    for entry in entries:
        if entry.get("result_id") == source.get("result_id"):
            existing = [item for item in entry.get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_id") != plot_id]
            entry["plot_artifacts"] = [*existing, artifact]
            entry["report_ready_eligible"] = False
            break
    save_registry(root, entries)
    return {
        "status": "passed",
        "plot_artifact": artifact,
        "plot_manifest_path": str(manifest_path),
        "report_ready_eligible": False,
        "warnings": artifact["warnings"],
        "blockers": [],
    }


def build_risk_score_plot_artifact_schema_candidate(
    source: dict[str, Any],
    *,
    plot_type: str,
    renderer: str,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_result_id = str(source.get("result_id") or "")
    semantics = normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="blocked")
    parameters = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    table_artifacts = [
        {"artifact_type": str(item.get("artifact_type") or ""), "path": str(item.get("path") or "")}
        for item in source.get("output_artifacts", []) or []
        if isinstance(item, dict) and item.get("artifact_type") == "risk_score_result_table"
    ]
    return PlotArtifact(
        plot_id=f"plot-risk-score-schema-{source_result_id or 'missing'}-{plot_type}",
        plot_type=plot_type,
        source_result_id=source_result_id,
        source_result_semantics=semantics,
        source_task_type=str(source.get("task_type") or ""),
        plot_semantics=semantics,
        plot_artifact_scope=RISK_SCORE_PLOT_ARTIFACT_SCOPE,
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest=parameters,
        plot_parameters={
            "renderer": renderer,
            "format": "svg" if renderer == "builtin_svg" else "",
            "risk_group_generation": "forbidden",
            "clinical_interpretation": "forbidden",
            "report_ready_unlock": False,
        },
        plot_spec_artifact={
            "schema_version": RISK_SCORE_PLOT_ARTIFACT_SCHEMA_VERSION,
            "plot_type": plot_type,
            "renderer": renderer,
            "source_result_id": source_result_id,
            "source_task_type": str(source.get("task_type") or ""),
            "rendering": "schema_only_no_image_artifact_in_b37",
            "allowed_data_columns": ["sample_id", "case_id", "risk_score"],
            "forbidden_outputs": list(FORBIDDEN_RISK_SCORE_PLOT_FIELDS),
        },
        image_artifacts=(),
        table_artifacts=tuple(table_artifacts),
        engine_name=RISK_SCORE_PLOT_ENGINE_NAME,
        engine_version=RISK_SCORE_PLOT_ENGINE_VERSION,
        dependency_snapshot=dependency_snapshot or {},
        warnings=("Risk score visualization schema only; no clinical conclusion or report-ready export.",),
        blockers=(),
    ).to_dict()


def validate_risk_score_plot_artifact_schema(artifact: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if artifact.get("plot_type") not in SUPPORTED_RISK_SCORE_PLOT_TYPES:
        blockers.append(f"unsupported_risk_score_plot_type:{artifact.get('plot_type')}")
    if artifact.get("plot_artifact_scope") != RISK_SCORE_PLOT_ARTIFACT_SCOPE:
        blockers.append("risk_score_plot_artifact_scope_required")
    if normalize_result_semantics(artifact.get("source_result_semantics"), default="") != "formal_computed_result":
        blockers.append("risk_score_plot_requires_formal_computed_result_source")
    if normalize_result_semantics(artifact.get("plot_semantics"), default="") != normalize_result_semantics(artifact.get("source_result_semantics"), default=""):
        blockers.append("risk_score_plot_semantics_must_inherit_source")
    if artifact.get("source_task_type") != "risk_score":
        blockers.append("risk_score_plot_requires_risk_score_source_task")
    if not artifact.get("source_result_id"):
        blockers.append("missing_source_result_id")
    if not artifact.get("input_package_id"):
        blockers.append("missing_input_package_id")
    if not artifact.get("task_run_id"):
        blockers.append("missing_task_run_id")
    if not artifact.get("parameters_manifest"):
        blockers.append("missing_parameters_manifest")
    dependency = artifact.get("dependency_snapshot") if isinstance(artifact.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("risk_score_plot_dependency_snapshot_not_passed")
    if not any(isinstance(item, dict) and item.get("artifact_type") == "risk_score_result_table" for item in artifact.get("table_artifacts", []) or []):
        blockers.append("risk_score_plot_requires_result_table_artifact")
    _scan_forbidden_fields(artifact, blockers)
    generic = validate_plot_artifact(artifact)
    blockers.extend(str(item) for item in generic.get("blockers", []) or [])
    warnings.extend(str(item) for item in generic.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _plot_artifact(
    source: dict[str, Any],
    plot_id: str,
    plot_type: str,
    renderer: str,
    dependency: dict[str, Any],
    table_path: Path,
    image_path: Path,
) -> dict[str, Any]:
    semantics = normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="blocked")
    parameters = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    return PlotArtifact(
        plot_id=plot_id,
        plot_type=plot_type,
        source_result_id=str(source.get("result_id") or ""),
        source_result_semantics=semantics,
        source_task_type=str(source.get("task_type") or ""),
        plot_semantics=semantics,
        plot_artifact_scope=RISK_SCORE_PLOT_ARTIFACT_SCOPE,
        input_package_id=str(source.get("input_package_id") or ""),
        task_run_id=str(source.get("task_run_id") or ""),
        parameters_manifest=parameters,
        plot_parameters={
            "renderer": renderer,
            "format": "svg",
            "risk_group_generation": "forbidden",
            "clinical_interpretation": "forbidden",
            "report_ready_unlock": False,
        },
        plot_spec_artifact={
            "schema_version": RISK_SCORE_PLOT_ARTIFACT_SCHEMA_VERSION,
            "plot_type": plot_type,
            "renderer": renderer,
            "format": "svg",
            "source_result_id": str(source.get("result_id") or ""),
            "source_task_type": str(source.get("task_type") or ""),
            "rendering": "real_svg_artifact_no_report_ready",
            "allowed_data_columns": ["sample_id", "case_id", "risk_score"],
            "forbidden_outputs": list(FORBIDDEN_RISK_SCORE_PLOT_FIELDS),
        },
        image_artifacts=(
            {
                "artifact_type": f"{plot_type}_svg",
                "path": str(image_path),
                "format": "svg",
                "source_result_id": str(source.get("result_id") or ""),
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
        ),
        table_artifacts=({"artifact_type": "risk_score_result_table", "path": str(table_path)},),
        engine_name=RISK_SCORE_PLOT_ENGINE_NAME,
        engine_version=RISK_SCORE_PLOT_ENGINE_VERSION,
        dependency_snapshot=dependency,
        warnings=("Statistical risk score visualization only; no risk groups, clinical conclusion, or report-ready export.",),
        blockers=(),
    ).to_dict()


def _blocked_artifact(source_result_id: str, gate: dict[str, Any]) -> dict[str, Any]:
    plot_type = str(gate.get("plot_type") or "risk_score_distribution_plot")
    artifact = PlotArtifact(
        plot_id=_plot_id(source_result_id or "missing", plot_type),
        plot_type=plot_type,
        source_result_id=source_result_id,
        source_result_semantics="blocked",
        source_task_type=str(gate.get("source_task_type") or ""),
        plot_semantics="blocked",
        plot_artifact_scope=RISK_SCORE_PLOT_ARTIFACT_SCOPE,
        plot_parameters={"renderer": gate.get("renderer", ""), "format": "svg" if gate.get("renderer") == "builtin_svg" else ""},
        plot_spec_artifact={"gate_snapshot": gate, "rendering": "blocked_no_image_artifact"},
        image_artifacts=(),
        dependency_snapshot=gate.get("renderer_dependency_snapshot") if isinstance(gate.get("renderer_dependency_snapshot"), dict) else {},
        blockers=tuple(str(item) for item in gate.get("blockers", []) or []),
        warnings=tuple(str(item) for item in gate.get("warnings", []) or []),
    ).to_dict()
    return {"status": "blocked", "plot_artifact": artifact, "report_ready_eligible": False, "warnings": artifact["warnings"], "blockers": artifact["blockers"]}


def _risk_score_table_path(root: Path, source: dict[str, Any]) -> Path:
    artifacts = source.get("output_artifacts") if isinstance(source.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "risk_score_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _risk_score_rows(table_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_table(table_path):
        score = parse_float(row.get("risk_score"))
        if score is None:
            continue
        rows.append({"sample_id": str(row.get("sample_id") or ""), "case_id": str(row.get("case_id") or ""), "risk_score": score})
    return rows


def _distribution_svg(rows: list[dict[str, Any]], source: dict[str, Any]) -> str:
    width, height = 760, 420
    left, top, plot_w, plot_h = 76, 44, 610, 260
    scores = [float(row["risk_score"]) for row in rows]
    min_score = min(scores)
    max_score = max(scores)
    span = max(max_score - min_score, 1.0)
    ordered = sorted(enumerate(scores), key=lambda item: item[1])
    parts: list[str] = []
    zero_y = top + plot_h - ((0.0 - min_score) / span) * plot_h
    if top <= zero_y <= top + plot_h:
        parts.append(f'<line x1="{left}" y1="{zero_y:.1f}" x2="{left + plot_w}" y2="{zero_y:.1f}" stroke="#9aa0a6" stroke-dasharray="4 4" />')
    for rank, (index, score) in enumerate(ordered):
        x = left + (rank / max(len(ordered) - 1, 1)) * plot_w
        y = top + plot_h - ((score - min_score) / span) * plot_h
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#315f9f" />')
        if len(ordered) <= 12:
            label = html.escape(str(rows[index].get("sample_id") or rows[index].get("case_id") or index + 1))
            parts.append(f'<text x="{x - 16:.1f}" y="{top + plot_h + 22}" font-size="11" transform="rotate(45 {x:.1f},{top + plot_h + 22})">{label}</text>')
    title = html.escape(f"{source.get('result_id') or 'risk score'} distribution")
    summary = html.escape(f"samples={len(scores)}; min={min_score:.3g}; max={max_score:.3g}; mean={(sum(scores) / len(scores)):.3g}")
    frame = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />',
        f'<text x="{left}" y="26" font-size="16" font-weight="600">{title}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#202124" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#202124" />',
        f'<text x="{left}" y="{top + plot_h + 48}" font-size="13">Samples ordered by risk score</text>',
        f'<text x="16" y="{top + 125}" font-size="13">Risk score</text>',
        f'<text x="{left}" y="{height - 52}" font-size="12" fill="#444">{summary}</text>',
        f'<text x="{left}" y="{height - 26}" font-size="12" fill="#555">Statistical visualization only; no risk group, prognosis label, clinical conclusion, or treatment recommendation.</text>',
    ]
    return "<svg xmlns=\"http://www.w3.org/2000/svg\" " f"width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">\n" + "\n".join([*frame, *parts]) + "\n</svg>\n"


def _select_source(root: Path, result_id: str | None) -> dict[str, Any] | None:
    registry = load_registry(root)
    candidates = [
        entry
        for entry in registry.get("results", []) or []
        if isinstance(entry, dict)
        and str(entry.get("task_type") or "").lower() == "risk_score"
        and normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result"
    ]
    if result_id:
        return next((entry for entry in candidates if str(entry.get("result_id") or "") == result_id), None)
    return candidates[-1] if candidates else None


def _source_blockers(entry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("risk_score_source_validation_not_passed")
    if entry.get("blockers"):
        blockers.append("risk_score_source_has_blockers")
    if entry.get("report_ready_eligible") is True:
        blockers.append("risk_score_source_must_not_be_report_ready")
    if entry.get("report_artifacts"):
        blockers.append("risk_score_report_artifacts_not_allowed_for_plot_source")
    if not entry.get("risk_score_parameter_confirmation"):
        blockers.append("risk_score_parameter_confirmation_missing")
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    artifact_types = {str(item.get("artifact_type") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}
    if "risk_score_result_table" not in artifact_types:
        blockers.append("risk_score_result_table_missing")
    return blockers


def _scan_forbidden_fields(value: Any, blockers: list[str], prefix: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in FORBIDDEN_RISK_SCORE_PLOT_FIELDS:
                blockers.append(f"forbidden_risk_score_plot_field:{path}")
            _scan_forbidden_fields(item, blockers, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden_fields(item, blockers, f"{prefix}[{index}]")


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
    return f"plot-risk-score-{digest}"
