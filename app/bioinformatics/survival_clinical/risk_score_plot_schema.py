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
RISK_SCORE_ADVANCED_VISUALIZATION_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_advanced_visualization_planning_gate.v1"
RISK_SCORE_ADVANCED_VISUALIZATION_RUNTIME_PLAN_SCHEMA_VERSION = "biomedpilot.risk_score_advanced_visualization_runtime_plan.v1"
RISK_SCORE_ADVANCED_VISUALIZATION_PREFLIGHT_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_advanced_visualization_preflight_gate.v1"
RISK_SCORE_ADVANCED_VISUALIZATION_ARTIFACT_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_advanced_visualization_artifact_gate.v1"
RISK_SCORE_PLOT_ARTIFACT_SCOPE = "formal_risk_score_plot_artifact"
RISK_SCORE_PLOT_ENGINE_NAME = "biomedpilot_risk_score_visualization_renderer"
RISK_SCORE_PLOT_ENGINE_VERSION = "0.1.0"
RISK_SCORE_REAL_PLOT_MANIFEST_SCHEMA_VERSION = "biomedpilot.risk_score_real_plot_manifest.v1"
RISK_SCORE_ADVANCED_VISUALIZATION_MANIFEST_SCHEMA_VERSION = "biomedpilot.risk_score_advanced_visualization_manifest.v1"
SUPPORTED_RISK_SCORE_PLOT_TYPES = (
    "risk_score_distribution_plot",
    "risk_score_nomogram",
    "risk_score_calibration_curve",
    "risk_score_decision_curve",
)
B42_ENABLED_ADVANCED_RISK_SCORE_PLOT_TYPES = {"risk_score_nomogram"}
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


def build_risk_score_advanced_visualization_planning_gate(project_root: str | Path, result_id: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _select_source(root, result_id)
    blockers: list[str] = []
    warnings = [
        "risk_score_advanced_visualization_planning_only",
        "nomogram_not_generated",
        "calibration_curve_not_generated",
        "decision_curve_not_generated",
        "no_risk_group_generation",
        "no_clinical_interpretation",
        "no_report_ready_unlock",
    ]
    if source is None:
        blockers.append("formal_risk_score_result_not_found")
    else:
        blockers.extend(_source_blockers(source))
    blockers.append("b40_risk_score_advanced_visualization_activation_required")
    return {
        "schema_version": RISK_SCORE_ADVANCED_VISUALIZATION_GATE_SCHEMA_VERSION,
        "status": "blocked_planning_only",
        "selected_result_id": str((source or {}).get("result_id") or result_id or ""),
        "source_result_semantics": normalize_result_semantics((source or {}).get("result_semantics"), default="blocked"),
        "source_task_type": str((source or {}).get("task_type") or ""),
        "planned_artifacts": [
            {
                "artifact_type": "risk_score_nomogram",
                "activation_status": "planned_disabled",
                "minimum_conditions": [
                    "formal_risk_score_result",
                    "source_cox_multivariate_coefficients",
                    "coefficient_provenance",
                    "nomogram_scale_policy",
                    "external_renderer_runtime_acceptance",
                    "clinical_boundary_acknowledgement",
                ],
                "forbidden_outputs": ["clinical_prognosis", "treatment_recommendation", "diagnosis"],
            },
            {
                "artifact_type": "risk_score_calibration_curve",
                "activation_status": "planned_disabled",
                "minimum_conditions": [
                    "formal_risk_score_result",
                    "time_horizon_policy",
                    "observed_outcome_mapping",
                    "calibration_method_policy",
                    "validation_or_bootstrap_policy",
                    "low_event_count_blocker",
                ],
                "forbidden_outputs": ["model_claim_of_clinical_validity", "prognosis_label"],
            },
            {
                "artifact_type": "risk_score_decision_curve",
                "activation_status": "planned_disabled",
                "minimum_conditions": [
                    "formal_risk_score_result",
                    "threshold_probability_grid",
                    "net_benefit_formula_policy",
                    "clinical_utility_boundary_acknowledgement",
                    "decision_recommendation_forbidden",
                ],
                "forbidden_outputs": ["clinical_decision_recommendation", "treatment_recommendation"],
            },
        ],
        "minimum_conditions": {
            "source_formal_risk_score": "required",
            "distribution_plot_artifact": "optional_input_not_sufficient",
            "nomogram_renderer": "future_detect_first_external_runtime",
            "calibration_validation_policy": "required_before_activation",
            "decision_curve_policy": "required_before_activation",
            "clinical_boundary_acknowledgement": "required_before_activation",
            "report_ready_gate": "separate_future_stage",
        },
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "creates_plot_artifact": False,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_risk_score_advanced_visualization_runtime_plan(project_root: str | Path, result_id: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _select_source(root, result_id)
    blockers: list[str] = []
    warnings = [
        "risk_score_advanced_visualization_runtime_planning_only",
        "no_nomogram_artifact_created",
        "no_calibration_curve_artifact_created",
        "no_decision_curve_artifact_created",
        "no_report_ready_unlock",
        "no_clinical_interpretation",
    ]
    if source is None:
        blockers.append("formal_risk_score_result_not_found")
    else:
        blockers.extend(_source_blockers(source))
    blockers.append("b41_risk_score_advanced_visualization_execution_required")
    return {
        "schema_version": RISK_SCORE_ADVANCED_VISUALIZATION_RUNTIME_PLAN_SCHEMA_VERSION,
        "status": "blocked_runtime_planning_only",
        "selected_result_id": str((source or {}).get("result_id") or result_id or ""),
        "source_result_semantics": normalize_result_semantics((source or {}).get("result_semantics"), default="blocked"),
        "source_task_type": str((source or {}).get("task_type") or ""),
        "runtime_policy": {
            "renderer_detection": "detect_first_no_install_no_download",
            "external_r_policy": "system_Rscript_only_not_bundled",
            "python_renderer_policy": "builtin_svg_or_existing_python_packages_only",
            "result_index_policy": "future_artifacts_must_attach_to_formal_risk_score_source",
            "report_ready_policy": "separate_future_gate",
        },
        "artifact_runtime_plans": [
            {
                "artifact_type": "risk_score_nomogram",
                "status": "blocked_runtime_planning_only",
                "renderer_candidates": [
                    {"renderer": "r_rms_nomogram", "status": "blocked", "reason": "external_r_runtime_acceptance_required"},
                    {"renderer": "builtin_svg_nomogram_spec", "status": "blocked", "reason": "nomogram_scale_mapping_not_validated"},
                ],
                "required_runtime_inputs": [
                    "formal_risk_score_result",
                    "source_cox_multivariate_coefficients",
                    "coefficient_units",
                    "nomogram_scale_policy",
                    "axis_label_policy",
                    "clinical_boundary_acknowledgement",
                ],
            },
            {
                "artifact_type": "risk_score_calibration_curve",
                "status": "blocked_runtime_planning_only",
                "renderer_candidates": [
                    {"renderer": "builtin_svg_calibration", "status": "blocked", "reason": "calibration_statistics_not_activated"},
                ],
                "required_runtime_inputs": [
                    "formal_risk_score_result",
                    "time_horizon",
                    "observed_event_mapping",
                    "predicted_probability_policy",
                    "bootstrap_or_validation_policy",
                    "minimum_event_count_policy",
                ],
            },
            {
                "artifact_type": "risk_score_decision_curve",
                "status": "blocked_runtime_planning_only",
                "renderer_candidates": [
                    {"renderer": "builtin_svg_decision_curve", "status": "blocked", "reason": "net_benefit_statistics_not_activated"},
                ],
                "required_runtime_inputs": [
                    "formal_risk_score_result",
                    "threshold_probability_grid",
                    "net_benefit_formula_policy",
                    "treat_all_none_baselines",
                    "clinical_decision_recommendation_forbidden",
                ],
            },
        ],
        "validation_gates": {
            "low_event_count": "must_block_before_calibration_or_decision_curve",
            "missing_outcome_mapping": "must_block",
            "missing_prediction_time_horizon": "must_block",
            "invalid_threshold_grid": "must_block",
            "source_has_clinical_conclusion": "must_block",
            "report_ready_unlock": "forbidden",
        },
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "creates_plot_artifact": False,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_risk_score_advanced_visualization_preflight_gate(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    preflight_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _select_source(root, result_id)
    config = _advanced_preflight_config(source or {}, preflight_config or {})
    blockers: list[str] = []
    warnings = [
        "risk_score_advanced_visualization_preflight_only",
        "no_advanced_visualization_artifact_created",
        "no_report_ready_unlock",
        "no_clinical_interpretation",
    ]
    if source is None:
        blockers.append("formal_risk_score_result_not_found")
    else:
        blockers.extend(_source_blockers(source))
    blockers.extend(_time_horizon_blockers(config))
    blockers.extend(_outcome_mapping_blockers(config))
    blockers.extend(_event_count_blockers(config))
    blockers.extend(_threshold_grid_blockers(config))
    if config.get("clinical_boundary_acknowledged") is not True:
        blockers.append("clinical_boundary_acknowledgement_missing")
    blockers = list(dict.fromkeys(blockers))
    return {
        "schema_version": RISK_SCORE_ADVANCED_VISUALIZATION_PREFLIGHT_GATE_SCHEMA_VERSION,
        "status": "blocked" if blockers else "passed_preflight_only",
        "selected_result_id": str((source or {}).get("result_id") or result_id or ""),
        "source_result_semantics": normalize_result_semantics((source or {}).get("result_semantics"), default="blocked"),
        "source_task_type": str((source or {}).get("task_type") or ""),
        "preflight_config": config,
        "checks": {
            "time_horizon_present": not any(item.startswith("time_horizon_") for item in blockers),
            "outcome_mapping_present": not any(item.startswith("outcome_") for item in blockers),
            "minimum_event_count_met": "minimum_event_count_not_met_for_advanced_visualization" not in blockers,
            "threshold_grid_valid": not any(item.startswith("threshold_probability_grid") for item in blockers),
            "clinical_boundary_acknowledged": "clinical_boundary_acknowledgement_missing" not in blockers,
        },
        "validated_future_artifacts": ["risk_score_nomogram", "risk_score_calibration_curve", "risk_score_decision_curve"],
        "formal_execution_enabled": False,
        "writes_result_index": False,
        "creates_plot_artifact": False,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "next_required_stage": "b42_risk_score_advanced_visualization_artifact_execution_audit",
        "blockers": blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_risk_score_advanced_visualization_artifact_gate(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    plot_type: str = "risk_score_nomogram",
    renderer: str = "builtin_svg",
    preflight_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _select_source(root, result_id)
    preflight = build_risk_score_advanced_visualization_preflight_gate(root, result_id=result_id, preflight_config=preflight_config)
    dependency = check_risk_score_plot_renderer_dependencies(renderer=renderer)
    blockers: list[str] = []
    warnings = [
        "risk_score_advanced_visualization_artifact_statistical_only",
        "b42_nomogram_scale_svg_only",
        "calibration_curve_not_enabled_in_b42",
        "decision_curve_not_enabled_in_b42",
        "no_risk_group_generation",
        "no_report_ready_unlock",
        "no_clinical_interpretation",
    ]
    if preflight.get("status") != "passed_preflight_only":
        blockers.extend(str(item) for item in preflight.get("blockers", []) or [])
        blockers.append("risk_score_advanced_visualization_preflight_not_passed")
    if plot_type not in SUPPORTED_RISK_SCORE_PLOT_TYPES:
        blockers.append(f"unsupported_risk_score_plot_type:{plot_type}")
    elif plot_type not in B42_ENABLED_ADVANCED_RISK_SCORE_PLOT_TYPES:
        blockers.append(f"risk_score_advanced_plot_type_not_enabled_in_b42:{plot_type}")
    if renderer != "builtin_svg":
        blockers.append(f"risk_score_advanced_renderer_not_enabled_in_b42:{renderer}")
    if dependency.get("status") != "passed":
        blockers.extend(str(item) for item in dependency.get("blockers", []) or ["risk_score_plot_renderer_dependency_not_passed"])
    table_path = _risk_score_table_path(root, source) if source else root / ""
    rows = _risk_score_rows(table_path) if source and table_path.exists() else []
    if source and not rows:
        blockers.append("risk_score_plot_source_table_empty")
    schema_candidate = _advanced_plot_artifact(
        source or {},
        _plot_id(str((source or {}).get("result_id") or result_id or "missing"), plot_type),
        plot_type,
        renderer,
        dependency,
        table_path,
        root / "results" / "plots" / "risk_score" / "advanced" / "candidate.svg",
        preflight,
    )
    validation = validate_risk_score_plot_artifact_schema(schema_candidate)
    blockers.extend(str(item) for item in validation.get("blockers", []) or [] if item != "missing_source_result_id")
    blockers = list(dict.fromkeys(blockers))
    return {
        "schema_version": RISK_SCORE_ADVANCED_VISUALIZATION_ARTIFACT_GATE_SCHEMA_VERSION,
        "status": "passed" if not blockers else "blocked",
        "selected_result_id": str((source or {}).get("result_id") or result_id or ""),
        "source_result_semantics": normalize_result_semantics((source or {}).get("result_semantics"), default="blocked"),
        "plot_type": plot_type,
        "renderer": renderer,
        "preflight_gate": preflight,
        "renderer_dependency_snapshot": dependency,
        "artifact_schema_candidate": schema_candidate,
        "artifact_schema_validation": validation,
        "formal_execution_enabled": False,
        "writes_result_index": not blockers,
        "creates_plot_artifact": not blockers,
        "creates_report_artifact": False,
        "report_ready_eligible": False,
        "enabled_plot_types": sorted(B42_ENABLED_ADVANCED_RISK_SCORE_PLOT_TYPES),
        "blocked_future_plot_types": ["risk_score_calibration_curve", "risk_score_decision_curve"],
        "blockers": blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_risk_score_advanced_visualization_artifact(
    project_root: str | Path,
    result_id: str | None = None,
    *,
    plot_type: str = "risk_score_nomogram",
    renderer: str = "builtin_svg",
    preflight_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = build_risk_score_advanced_visualization_artifact_gate(root, result_id=result_id, plot_type=plot_type, renderer=renderer, preflight_config=preflight_config)
    source = _select_source(root, result_id)
    if gate.get("status") != "passed" or source is None:
        return _blocked_artifact(str(result_id or gate.get("selected_result_id") or ""), {**gate, "plot_type": plot_type, "renderer": renderer})
    table_path = _risk_score_table_path(root, source)
    rows = _risk_score_rows(table_path)
    if not rows:
        blocked_gate = {**gate, "status": "blocked", "blockers": [*gate.get("blockers", []), "risk_score_plot_source_table_empty"]}
        return _blocked_artifact(str(source.get("result_id") or ""), blocked_gate)

    plot_id = _plot_id(str(source.get("result_id") or ""), plot_type)
    out_dir = root / "results" / "plots" / "risk_score" / "advanced"
    image_path = out_dir / f"{plot_id}.svg"
    manifest_path = out_dir / f"{plot_id}_manifest.json"
    dependency = gate.get("renderer_dependency_snapshot") if isinstance(gate.get("renderer_dependency_snapshot"), dict) else {}
    preflight = gate.get("preflight_gate") if isinstance(gate.get("preflight_gate"), dict) else {}
    artifact = _advanced_plot_artifact(source, plot_id, plot_type, renderer, dependency, table_path, image_path, preflight)
    validation = validate_risk_score_plot_artifact_schema(artifact)
    artifact["blockers"] = list(dict.fromkeys([*artifact.get("blockers", []), *validation.get("blockers", [])]))
    artifact["warnings"] = list(dict.fromkeys([*artifact.get("warnings", []), *validation.get("warnings", [])]))
    if artifact["blockers"]:
        return {"status": "blocked", "plot_artifact": artifact, "report_ready_eligible": False, "warnings": artifact["warnings"], "blockers": artifact["blockers"]}

    out_dir.mkdir(parents=True, exist_ok=True)
    image_path.write_text(_nomogram_svg(rows, source, preflight), encoding="utf-8")
    artifact["plot_spec_artifact"]["plot_manifest_path"] = str(manifest_path)
    manifest = {
        "schema_version": RISK_SCORE_ADVANCED_VISUALIZATION_MANIFEST_SCHEMA_VERSION,
        "plot_artifact": artifact,
        "gate_snapshot": gate,
        "source_row_count": len(rows),
        "report_ready_eligible": False,
        "limitations": [
            "statistical_visualization_only",
            "nomogram_scale_svg_only",
            "no_calibration_curve",
            "no_decision_curve",
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


def _advanced_preflight_config(source: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    confirmation = source.get("risk_score_parameter_confirmation") if isinstance(source.get("risk_score_parameter_confirmation"), dict) else {}
    source_params = confirmation.get("source_parameters_manifest") if isinstance(confirmation.get("source_parameters_manifest"), dict) else {}
    contract = confirmation.get("risk_score_contract_gate") if isinstance(confirmation.get("risk_score_contract_gate"), dict) else {}
    calibration_plan = confirmation.get("calibration_plan") if isinstance(confirmation.get("calibration_plan"), dict) else {}
    validation_plan = confirmation.get("validation_plan") if isinstance(confirmation.get("validation_plan"), dict) else {}
    boundary = contract.get("interpretation_boundary") if isinstance(contract.get("interpretation_boundary"), dict) else {}
    outcome_mapping = override.get("outcome_mapping") if isinstance(override.get("outcome_mapping"), dict) else {}
    threshold_grid = override.get("threshold_probability_grid")
    if threshold_grid is None:
        threshold_grid = override.get("threshold_grid")
    time_horizon = _first_present(
        override,
        ("time_horizon", "time_horizon_days"),
        calibration_plan,
        ("time_horizon", "time_horizon_days"),
        validation_plan,
        ("time_horizon",),
        default="",
    )
    return {
        "time_horizon": time_horizon,
        "time_unit": str(override.get("time_unit") or source_params.get("time_unit") or "days"),
        "outcome_mapping": {
            "time_field": str(outcome_mapping.get("time_field") or override.get("time_field") or source_params.get("time_field") or ""),
            "event_field": str(outcome_mapping.get("event_field") or override.get("event_field") or source_params.get("event_field") or ""),
            "event_positive_value": str(outcome_mapping.get("event_positive_value") or override.get("event_positive_value") or "1"),
            "censoring_policy": str(outcome_mapping.get("censoring_policy") or override.get("censoring_policy") or source_params.get("censoring_policy") or ""),
        },
        "event_count": override.get("event_count", source_params.get("event_count", validation_plan.get("event_count", ""))),
        "minimum_event_count": override.get("minimum_event_count", calibration_plan.get("minimum_event_count", validation_plan.get("minimum_event_count", 10))),
        "threshold_probability_grid": list(threshold_grid or []),
        "clinical_boundary_acknowledged": bool(
            override.get("clinical_boundary_acknowledged")
            or (
                boundary.get("clinical_conclusion_forbidden") is True
                and boundary.get("prognosis_label_forbidden") is True
                and boundary.get("treatment_recommendation_forbidden") is True
            )
        ),
}


def _first_present(
    primary: dict[str, Any],
    primary_keys: tuple[str, ...],
    secondary: dict[str, Any],
    secondary_keys: tuple[str, ...],
    tertiary: dict[str, Any],
    tertiary_keys: tuple[str, ...],
    *,
    default: Any,
) -> Any:
    for mapping, keys in ((primary, primary_keys), (secondary, secondary_keys), (tertiary, tertiary_keys)):
        for key in keys:
            if key in mapping and mapping.get(key) is not None and mapping.get(key) != "":
                return mapping.get(key)
    return default


def _time_horizon_blockers(config: dict[str, Any]) -> list[str]:
    horizon = parse_float(config.get("time_horizon"))
    if horizon is None:
        return ["time_horizon_missing"]
    if horizon <= 0:
        return ["time_horizon_invalid"]
    return []


def _outcome_mapping_blockers(config: dict[str, Any]) -> list[str]:
    outcome = config.get("outcome_mapping") if isinstance(config.get("outcome_mapping"), dict) else {}
    blockers: list[str] = []
    if not outcome.get("time_field"):
        blockers.append("outcome_time_field_missing")
    if not outcome.get("event_field"):
        blockers.append("outcome_event_field_missing")
    if not outcome.get("event_positive_value"):
        blockers.append("outcome_event_positive_value_missing")
    return blockers


def _event_count_blockers(config: dict[str, Any]) -> list[str]:
    event_count = parse_float(config.get("event_count"))
    minimum = parse_float(config.get("minimum_event_count"))
    if event_count is None:
        return ["event_count_missing"]
    if event_count < max(minimum or 10.0, 1.0):
        return ["minimum_event_count_not_met_for_advanced_visualization"]
    return []


def _threshold_grid_blockers(config: dict[str, Any]) -> list[str]:
    raw_grid = config.get("threshold_probability_grid") if isinstance(config.get("threshold_probability_grid"), list) else []
    if not raw_grid:
        return ["threshold_probability_grid_missing"]
    parsed: list[float] = []
    for value in raw_grid:
        probability = parse_float(value)
        if probability is None or probability <= 0 or probability >= 1:
            return ["threshold_probability_grid_invalid"]
        parsed.append(float(probability))
    if parsed != sorted(parsed) or len(set(parsed)) != len(parsed):
        return ["threshold_probability_grid_invalid"]
    return []


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


def _advanced_plot_artifact(
    source: dict[str, Any],
    plot_id: str,
    plot_type: str,
    renderer: str,
    dependency: dict[str, Any],
    table_path: Path,
    image_path: Path,
    preflight_gate: dict[str, Any],
) -> dict[str, Any]:
    semantics = normalize_result_semantics(source.get("canonical_result_semantics") or source.get("result_semantics"), default="blocked")
    parameters = source.get("parameters_manifest") if isinstance(source.get("parameters_manifest"), dict) else {}
    preflight_config = preflight_gate.get("preflight_config") if isinstance(preflight_gate.get("preflight_config"), dict) else {}
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
            "advanced_visualization_mode": "nomogram_scale_audit_only",
            "risk_group_generation": "forbidden",
            "clinical_interpretation": "forbidden",
            "report_ready_unlock": False,
            "time_horizon": preflight_config.get("time_horizon", ""),
            "time_unit": preflight_config.get("time_unit", ""),
        },
        plot_spec_artifact={
            "schema_version": RISK_SCORE_PLOT_ARTIFACT_SCHEMA_VERSION,
            "plot_type": plot_type,
            "renderer": renderer,
            "format": "svg",
            "source_result_id": str(source.get("result_id") or ""),
            "source_task_type": str(source.get("task_type") or ""),
            "rendering": "real_svg_artifact_no_report_ready",
            "b42_scope": "risk_score_nomogram_scale_only",
            "allowed_data_columns": ["sample_id", "case_id", "risk_score"],
            "forbidden_outputs": list(FORBIDDEN_RISK_SCORE_PLOT_FIELDS),
            "preflight_gate_schema": preflight_gate.get("schema_version", ""),
            "preflight_status": preflight_gate.get("status", ""),
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
        warnings=("Statistical risk score nomogram-scale visualization only; no risk groups, clinical conclusion, or report-ready export.",),
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


def _nomogram_svg(rows: list[dict[str, Any]], source: dict[str, Any], preflight_gate: dict[str, Any]) -> str:
    width, height = 820, 360
    left, axis_y, plot_w = 90, 150, 620
    scores = [float(row["risk_score"]) for row in rows]
    min_score = min(scores)
    max_score = max(scores)
    span = max(max_score - min_score, 1.0)
    ticks = [min_score + span * fraction for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)]
    parts: list[str] = []
    for value in ticks:
        x = left + ((value - min_score) / span) * plot_w
        label = html.escape(f"{value:.3g}")
        parts.append(f'<line x1="{x:.1f}" y1="{axis_y - 9}" x2="{x:.1f}" y2="{axis_y + 9}" stroke="#202124" />')
        parts.append(f'<text x="{x - 18:.1f}" y="{axis_y + 30}" font-size="12">{label}</text>')
    for row in rows[:40]:
        x = left + ((float(row["risk_score"]) - min_score) / span) * plot_w
        parts.append(f'<circle cx="{x:.1f}" cy="{axis_y}" r="4" fill="#315f9f" opacity="0.72" />')
    config = preflight_gate.get("preflight_config") if isinstance(preflight_gate.get("preflight_config"), dict) else {}
    horizon = html.escape(str(config.get("time_horizon") or ""))
    unit = html.escape(str(config.get("time_unit") or ""))
    event_count = html.escape(str(config.get("event_count") or ""))
    title = html.escape(f"{source.get('result_id') or 'risk score'} nomogram scale audit")
    frame = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />',
        f'<text x="{left}" y="34" font-size="17" font-weight="600">{title}</text>',
        f'<text x="{left}" y="62" font-size="12" fill="#444">Controlled B42 SVG artifact from formal risk score values; calibration and decision curve artifacts are not generated.</text>',
        f'<line x1="{left}" y1="{axis_y}" x2="{left + plot_w}" y2="{axis_y}" stroke="#202124" stroke-width="1.4" />',
        f'<text x="{left}" y="{axis_y - 22}" font-size="13">Risk score scale</text>',
        f'<text x="{left}" y="238" font-size="12" fill="#444">samples={len(scores)}; min={min_score:.3g}; max={max_score:.3g}; horizon={horizon} {unit}; events={event_count}</text>',
        f'<text x="{left}" y="264" font-size="12" fill="#555">Statistical visualization only. No high/low-risk group, prognosis label, clinical conclusion, treatment recommendation, or report-ready unlock.</text>',
        f'<text x="{left}" y="290" font-size="12" fill="#555">This is not a clinical nomogram interpretation and must remain attached to the source formal risk score result provenance.</text>',
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
