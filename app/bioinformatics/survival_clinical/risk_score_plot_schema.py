from __future__ import annotations

import importlib.util
from importlib import metadata
from pathlib import Path
from typing import Any

from app.bioinformatics.plots.models import PlotArtifact
from app.bioinformatics.plots.schema import validate_plot_artifact
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry


RISK_SCORE_PLOT_ARTIFACT_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_plot_artifact_activation_gate.v1"
RISK_SCORE_PLOT_ARTIFACT_SCHEMA_VERSION = "biomedpilot.risk_score_plot_artifact.v1"
RISK_SCORE_PLOT_ARTIFACT_SCOPE = "formal_risk_score_plot_artifact"
RISK_SCORE_PLOT_ENGINE_NAME = "biomedpilot_risk_score_visualization_renderer"
RISK_SCORE_PLOT_ENGINE_VERSION = "0.1.0"
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

    schema_candidate = build_risk_score_plot_artifact_schema_candidate(
        source or {},
        plot_type=plot_type if plot_type in SUPPORTED_RISK_SCORE_PLOT_TYPES else "risk_score_distribution_plot",
        renderer=renderer,
        dependency_snapshot=dependency,
    )
    schema_validation = validate_risk_score_plot_artifact_schema(schema_candidate)
    schema_blockers = [str(item) for item in schema_validation.get("blockers", []) or [] if item != "missing_source_result_id"]
    blockers.extend(schema_blockers)
    blockers.append("b38_risk_score_plot_renderer_execution_required")
    source_ready = bool(source) and not [item for item in blockers if item != "b38_risk_score_plot_renderer_execution_required"]
    return {
        "schema_version": RISK_SCORE_PLOT_ARTIFACT_GATE_SCHEMA_VERSION,
        "status": "blocked_activation_required",
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
        "writes_result_index": False,
        "creates_plot_artifact": False,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "minimum_conditions": {
            "formal_risk_score_result": "required",
            "risk_score_result_table": "required",
            "parameter_confirmation": "required",
            "dependency_snapshot_passed": "required",
            "renderer_dependency_passed": "required",
            "artifact_schema_validation": "required",
            "b38_renderer_execution_audit": "required_before_artifact_creation",
        },
        "forbidden_outputs": list(FORBIDDEN_RISK_SCORE_PLOT_FIELDS),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
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
