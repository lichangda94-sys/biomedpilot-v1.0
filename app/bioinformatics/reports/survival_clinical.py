from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry
from app.bioinformatics.survival_clinical._io import read_table
from app.bioinformatics.survival_clinical.cox_multivariate_result_schema import validate_cox_multivariate_result_index_entry, validate_cox_multivariate_result_table
from app.bioinformatics.survival_clinical.cox_result_schema import validate_cox_result_index_entry, validate_cox_result_table
from app.bioinformatics.survival_clinical.km_result_schema import validate_km_result_index_entry, validate_km_result_tables
from app.bioinformatics.survival_clinical.risk_score_result_schema import validate_risk_score_result_index_entry, validate_risk_score_result_table


KM_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.km_logrank_report_ready_gate.v1"
COX_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.cox_univariate_report_ready_gate.v1"
COX_MULTIVARIATE_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.cox_multivariate_report_ready_gate.v1"
RISK_SCORE_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.risk_score_report_ready_gate.v1"
SURVIVAL_CLINICAL_REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.survival_clinical_report_ready_package.v1"
FORBIDDEN_CLINICAL_PHRASES = (
    "clinical_conclusion",
    "prognosis_conclusion",
    "treatment_recommendation",
    "validated_risk_score",
    "clinical advice",
    "medical advice",
    "治疗建议",
    "临床结论",
)


def evaluate_km_logrank_report_ready_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entry = _select_entry(root, "survival_km_logrank", result_id)
    if entry is None:
        return _gate(
            KM_REPORT_READY_GATE_SCHEMA_VERSION,
            "blocked",
            result_id or "",
            "survival_km_logrank",
            allow_table_only_report,
            ["missing_km_logrank_result"],
            [],
            {},
        )
    blockers: list[str] = []
    warnings: list[str] = [str(item) for item in entry.get("warnings", []) or []]
    if normalize_result_semantics(entry.get("result_semantics"), default="") != "formal_computed_result":
        blockers.append("km_report_ready_requires_formal_computed_result")
    if entry.get("task_type") != "survival_km_logrank":
        blockers.append("km_report_ready_requires_survival_km_logrank_task")
    legacy_entry = _is_legacy_section_entry(entry, "km_curve_table")
    blockers.extend(_base_entry_blockers(root, entry, required_artifacts=("km_curve_table",) if legacy_entry else ("km_curve_table", "logrank_result_table")))
    table_paths = _artifact_paths(entry)
    km_rows = read_table(_resolve(root, table_paths.get("km_curve_table", "")))
    logrank_rows = read_table(_resolve(root, table_paths.get("logrank_result_table", ""))) if not legacy_entry else []
    schema_gate: dict[str, Any] = {"status": "skipped_legacy_section_entry", "blockers": [], "warnings": []}
    table_gate: dict[str, Any] = {"status": "skipped_legacy_section_entry", "blockers": [], "warnings": []}
    if not legacy_entry:
        schema_gate = validate_km_result_index_entry(_schema_validation_view(entry))
        blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
        table_gate = validate_km_result_tables(km_rows, logrank_rows)
        blockers.extend(str(item) for item in table_gate.get("blockers", []) or [])
        warnings.extend(str(item) for item in table_gate.get("warnings", []) or [])
        blockers.extend(_parameter_blockers(entry, ("survival_clinical_input_id", "survival_outcome_gate_id", "time_field", "event_field", "grouping_variable", "group_a", "group_b", "censoring_policy", "missingness_policy")))
    if not legacy_entry and not allow_table_only_report and not _has_formal_plot(entry, "km_curve"):
        blockers.append("km_report_ready_requires_formal_km_plot_artifact_or_explicit_table_only_mode")
    if _clinical_text_detected(entry):
        blockers.append("clinical_conclusion_text_forbidden")
    status = "eligible_for_km_logrank_report_ready" if not blockers else "blocked"
    return _gate(
        KM_REPORT_READY_GATE_SCHEMA_VERSION,
        status,
        str(entry.get("result_id") or ""),
        "survival_km_logrank",
        allow_table_only_report,
        blockers,
        warnings,
        {
            "result_index_path": str(root / RESULT_INDEX),
            "km_curve_row_count": len(km_rows),
            "logrank_row_count": len(logrank_rows),
            "plot_artifact_count": len(entry.get("plot_artifacts", []) or []),
            "table_validation": table_gate,
            "result_schema_validation": schema_gate,
        },
    )


def evaluate_cox_report_ready_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entry = _select_entry(root, ("cox_univariate", "cox_multivariate"), result_id)
    if entry is None:
        return _gate(
            COX_REPORT_READY_GATE_SCHEMA_VERSION,
            "blocked",
            result_id or "",
            "cox",
            allow_table_only_report,
            ["missing_cox_result"],
            [],
            {},
        )
    if entry.get("task_type") == "cox_multivariate":
        return _evaluate_cox_multivariate_report_ready_gate(root, entry, allow_table_only_report=allow_table_only_report)
    blockers: list[str] = []
    warnings: list[str] = [str(item) for item in entry.get("warnings", []) or []]
    if normalize_result_semantics(entry.get("result_semantics"), default="") != "formal_computed_result":
        blockers.append("cox_report_ready_requires_formal_computed_result")
    if entry.get("task_type") != "cox_univariate":
        blockers.append("cox_report_ready_requires_cox_univariate_task")
    legacy_entry = _is_legacy_section_entry(entry, "cox_result_table")
    blockers.extend(_base_entry_blockers(root, entry, required_artifacts=("cox_result_table",)))
    table_paths = _artifact_paths(entry)
    cox_rows = read_table(_resolve(root, table_paths.get("cox_result_table", "")))
    schema_gate: dict[str, Any] = {"status": "skipped_legacy_section_entry", "blockers": [], "warnings": []}
    table_gate: dict[str, Any] = {"status": "skipped_legacy_section_entry", "blockers": [], "warnings": []}
    if not legacy_entry:
        schema_gate = validate_cox_result_index_entry(_schema_validation_view(entry))
        blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
        table_gate = validate_cox_result_table(cox_rows)
        blockers.extend(str(item) for item in table_gate.get("blockers", []) or [])
        warnings.extend(str(item) for item in table_gate.get("warnings", []) or [])
        blockers.extend(_parameter_blockers(entry, ("survival_clinical_input_id", "survival_outcome_gate_id", "time_field", "event_field", "covariate", "covariate_type", "missing_value_policy", "minimum_event_count")))
    if not legacy_entry and not allow_table_only_report and not _has_formal_plot(entry, "cox_forest_plot"):
        blockers.append("cox_report_ready_requires_formal_cox_plot_artifact_or_explicit_table_only_mode")
    if _clinical_text_detected(entry):
        blockers.append("clinical_conclusion_text_forbidden")
    status = "eligible_for_cox_report_ready" if not blockers else "blocked"
    return _gate(
        COX_REPORT_READY_GATE_SCHEMA_VERSION,
        status,
        str(entry.get("result_id") or ""),
        "cox_univariate",
        allow_table_only_report,
        blockers,
        warnings,
        {
            "result_index_path": str(root / RESULT_INDEX),
            "cox_row_count": len(cox_rows),
            "plot_artifact_count": len(entry.get("plot_artifacts", []) or []),
            "table_validation": table_gate,
            "result_schema_validation": schema_gate,
        },
    )


def evaluate_risk_score_report_ready_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entry = _select_entry(root, "risk_score", result_id)
    if entry is None:
        return _gate(
            RISK_SCORE_REPORT_READY_GATE_SCHEMA_VERSION,
            "blocked",
            result_id or "",
            "risk_score",
            allow_table_only_report,
            ["missing_risk_score_result"],
            [],
            {},
            section_scope="risk_score_validation_only",
        )
    blockers: list[str] = []
    warnings: list[str] = [str(item) for item in entry.get("warnings", []) or []]
    if normalize_result_semantics(entry.get("result_semantics"), default="") != "formal_computed_result":
        blockers.append("risk_score_report_ready_requires_formal_computed_result")
    if entry.get("task_type") != "risk_score":
        blockers.append("risk_score_report_ready_requires_risk_score_task")
    blockers.extend(
        _base_entry_blockers(
            root,
            entry,
            required_artifacts=(
                "risk_score_result_table",
                "risk_score_calibration_statistics_table",
                "risk_score_decision_curve_statistics_table",
            ),
        )
    )
    schema_gate = validate_risk_score_result_index_entry(_schema_validation_view(entry))
    blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
    table_paths = _artifact_paths(entry)
    risk_rows = read_table(_resolve(root, table_paths.get("risk_score_result_table", "")))
    risk_table_gate = validate_risk_score_result_table(risk_rows)
    blockers.extend(str(item) for item in risk_table_gate.get("blockers", []) or [])
    warnings.extend(str(item) for item in risk_table_gate.get("warnings", []) or [])
    blockers.extend(_parameter_blockers(entry, ("status",)))
    if not _has_formal_plot(entry, "risk_score_nomogram"):
        blockers.append("risk_score_report_ready_requires_b42_nomogram_plot_artifact")
    if not allow_table_only_report and not _has_formal_plot(entry, "risk_score_calibration_curve"):
        blockers.append("risk_score_report_ready_requires_b45_calibration_plot_artifact_or_explicit_table_only_mode")
    if not allow_table_only_report and not _has_formal_plot(entry, "risk_score_decision_curve"):
        blockers.append("risk_score_report_ready_requires_b45_decision_curve_plot_artifact_or_explicit_table_only_mode")
    if _clinical_text_detected(entry):
        blockers.append("clinical_conclusion_text_forbidden")
    status = "eligible_for_risk_score_report_ready" if not blockers else "blocked"
    return _gate(
        RISK_SCORE_REPORT_READY_GATE_SCHEMA_VERSION,
        status,
        str(entry.get("result_id") or ""),
        "risk_score",
        allow_table_only_report,
        blockers,
        warnings,
        {
            "result_index_path": str(root / RESULT_INDEX),
            "risk_score_row_count": len(risk_rows),
            "statistics_artifact_types": [
                artifact_type
                for artifact_type in ("risk_score_calibration_statistics_table", "risk_score_decision_curve_statistics_table")
                if table_paths.get(artifact_type)
            ],
            "plot_artifact_types": [str(item.get("plot_type") or "") for item in entry.get("plot_artifacts", []) or [] if isinstance(item, dict)],
            "table_validation": risk_table_gate,
            "result_schema_validation": schema_gate,
        },
        section_scope="risk_score_validation_only",
    )


def create_km_logrank_report_ready_package(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    return _create_section_package(
        project_root,
        result_id=result_id,
        allow_table_only_report=allow_table_only_report,
        gate_fn=evaluate_km_logrank_report_ready_gate,
        task_type="survival_km_logrank",
        section_scope="survival_km_logrank_only",
        report_filename="km_logrank_report.md",
        manifest_filename="km_logrank_report_package_manifest.json",
        artifact_type="km_logrank_report_ready_package",
        table_artifact_types=("km_curve_table", "logrank_result_table"),
        section_title="KM/log-rank Survival Section",
    )


def create_cox_report_ready_package(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    config = _cox_package_config(project_root, result_id)
    return _create_section_package(
        project_root,
        result_id=result_id,
        allow_table_only_report=allow_table_only_report,
        gate_fn=evaluate_cox_report_ready_gate,
        task_type=config["task_type"],
        section_scope=config["section_scope"],
        report_filename=config["report_filename"],
        manifest_filename=config["manifest_filename"],
        artifact_type=config["artifact_type"],
        table_artifact_types=config["table_artifact_types"],
        section_title=config["section_title"],
    )


def create_risk_score_report_ready_package(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    return _create_section_package(
        project_root,
        result_id=result_id,
        allow_table_only_report=allow_table_only_report,
        gate_fn=evaluate_risk_score_report_ready_gate,
        task_type="risk_score",
        section_scope="risk_score_validation_only",
        report_filename="risk_score_validation_report.md",
        manifest_filename="risk_score_report_package_manifest.json",
        artifact_type="risk_score_report_ready_package",
        table_artifact_types=(
            "risk_score_result_table",
            "risk_score_calibration_statistics_table",
            "risk_score_decision_curve_statistics_table",
        ),
        section_title="Risk Score Validation Section",
    )


def _evaluate_cox_multivariate_report_ready_gate(root: Path, entry: dict[str, Any], *, allow_table_only_report: bool) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = [str(item) for item in entry.get("warnings", []) or []]
    if normalize_result_semantics(entry.get("result_semantics"), default="") != "formal_computed_result":
        blockers.append("cox_multivariate_report_ready_requires_formal_computed_result")
    if entry.get("task_type") != "cox_multivariate":
        blockers.append("cox_multivariate_report_ready_requires_cox_multivariate_task")
    blockers.extend(_base_entry_blockers(root, entry, required_artifacts=("cox_multivariate_result_table",)))
    schema_gate = validate_cox_multivariate_result_index_entry(_schema_validation_view(entry))
    blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
    table_paths = _artifact_paths(entry)
    cox_rows = read_table(_resolve(root, table_paths.get("cox_multivariate_result_table", "")))
    table_gate = validate_cox_multivariate_result_table(cox_rows)
    blockers.extend(str(item) for item in table_gate.get("blockers", []) or [])
    warnings.extend(str(item) for item in table_gate.get("warnings", []) or [])
    blockers.extend(_parameter_blockers(entry, ("survival_clinical_input_id", "survival_outcome_gate_id", "time_field", "event_field", "selected_covariates", "missingness_policy", "minimum_event_count")))
    if not allow_table_only_report and not _has_formal_plot(entry, "cox_forest_plot"):
        blockers.append("cox_multivariate_report_ready_requires_formal_cox_plot_artifact_or_explicit_table_only_mode")
    if _clinical_text_detected(entry):
        blockers.append("clinical_conclusion_text_forbidden")
    status = "eligible_for_cox_report_ready" if not blockers else "blocked"
    return _gate(
        COX_MULTIVARIATE_REPORT_READY_GATE_SCHEMA_VERSION,
        status,
        str(entry.get("result_id") or ""),
        "cox_multivariate",
        allow_table_only_report,
        blockers,
        warnings,
        {
            "result_index_path": str(root / RESULT_INDEX),
            "cox_row_count": len(cox_rows),
            "covariate_count": len(cox_rows),
            "plot_artifact_count": len(entry.get("plot_artifacts", []) or []),
            "table_validation": table_gate,
            "result_schema_validation": schema_gate,
        },
    )


def _gate(
    schema: str,
    status: str,
    selected_result_id: str,
    task_type: str,
    allow_table_only: bool,
    blockers: list[str],
    warnings: list[str],
    diagnostics: dict[str, Any],
    *,
    section_scope: str | None = None,
) -> dict[str, Any]:
    eligible = status in {"eligible_for_km_logrank_report_ready", "eligible_for_cox_report_ready", "eligible_for_risk_score_report_ready"}
    return {
        "schema_version": schema,
        "status": status,
        "selected_result_id": selected_result_id,
        "task_type": task_type,
        "section_scope": section_scope or f"{task_type}_only",
        "package_creation_enabled": eligible,
        "allow_table_only_report": allow_table_only,
        "report_ready_eligible": False,
        "clinical_boundary": "Statistical research section only; no clinical diagnosis, prognosis, treatment recommendation, or validated risk score.",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "diagnostics": diagnostics,
    }


def _select_entry(root: Path, task_type: str | tuple[str, ...], result_id: str | None) -> dict[str, Any] | None:
    entries = [entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict)]
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    task_types = {task_type} if isinstance(task_type, str) else set(task_type)
    candidates = [entry for entry in entries if str(entry.get("task_type") or "") in task_types]
    formal = [entry for entry in candidates if normalize_result_semantics(entry.get("result_semantics"), default="") == "formal_computed_result"]
    return (formal or candidates or [None])[-1]


def _cox_package_config(project_root: str | Path, result_id: str | None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    entry = _select_entry(root, ("cox_univariate", "cox_multivariate"), result_id)
    if entry and entry.get("task_type") == "cox_multivariate":
        return {
            "task_type": "cox_multivariate",
            "section_scope": "cox_multivariate_only",
            "report_filename": "cox_multivariate_report.md",
            "manifest_filename": "cox_multivariate_report_package_manifest.json",
            "artifact_type": "cox_multivariate_report_ready_package",
            "table_artifact_types": ("cox_multivariate_result_table",),
            "section_title": "Cox Multivariate Clinical Association Section",
        }
    return {
        "task_type": "cox_univariate",
        "section_scope": "cox_univariate_only",
        "report_filename": "cox_univariate_report.md",
        "manifest_filename": "cox_univariate_report_package_manifest.json",
        "artifact_type": "cox_univariate_report_ready_package",
        "table_artifact_types": ("cox_result_table",),
        "section_title": "Cox Univariate Clinical Association Section",
    }


def _create_section_package(
    project_root: str | Path,
    *,
    result_id: str | None,
    allow_table_only_report: bool,
    gate_fn,
    task_type: str,
    section_scope: str,
    report_filename: str,
    manifest_filename: str,
    artifact_type: str,
    table_artifact_types: tuple[str, ...],
    section_title: str,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = gate_fn(root, result_id=result_id, allow_table_only_report=allow_table_only_report)
    if gate.get("status") == "blocked":
        return {
            "schema_version": SURVIVAL_CLINICAL_REPORT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "user_visible_package_path": "",
            "section_scope": section_scope,
            "gate": gate,
            "blockers": list(gate.get("blockers", []) or []),
            "warnings": list(gate.get("warnings", []) or []),
        }
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = next(entry for entry in entries if str(entry.get("result_id") or "") == str(gate.get("selected_result_id") or ""))
    package_dir = _next_package_dir(root, section_scope, str(selected.get("result_id") or task_type))
    tables_dir = package_dir / "tables"
    plots_dir = package_dir / "plots"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    provenance_dir = package_dir / "provenance"
    for directory in (tables_dir, plots_dir, manifests_dir, logs_dir, provenance_dir):
        directory.mkdir(parents=True, exist_ok=True)
    artifact_paths = _artifact_paths(selected)
    for artifact_type_name in table_artifact_types:
        source = _resolve(root, artifact_paths.get(artifact_type_name, ""))
        if source.is_file():
            shutil.copy2(source, tables_dir / source.name)
    _copy_artifact_group(root, selected.get("log_artifacts", []) or [], logs_dir)
    _write_plot_artifact_files(root, plots_dir, selected.get("plot_artifacts", []) or [])
    _write_json(manifests_dir / "gate_snapshot.json", gate)
    _write_json(manifests_dir / "result_index_snapshot.json", registry)
    _write_json(manifests_dir / "source_result_entry.json", selected)
    _write_json(manifests_dir / "parameters_manifest.json", selected.get("parameters_manifest", {}))
    _write_json(manifests_dir / "dependency_snapshot.json", selected.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "table_validation.json", gate.get("diagnostics", {}).get("table_validation", {}) if isinstance(gate.get("diagnostics"), dict) else {})
    _write_json(manifests_dir / "plot_artifacts.json", selected.get("plot_artifacts", []) or [])
    _write_json(manifests_dir / "warnings_limitations.json", _warnings_limitations(gate, selected))
    _write_json(provenance_dir / "provenance.json", _provenance(gate, selected, root))
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(allow_table_only_report=allow_table_only_report), encoding="utf-8")
    (package_dir / report_filename).write_text(_section_report_markdown(section_title, selected, gate), encoding="utf-8")
    inventory = _package_inventory(package_dir)
    _write_json(manifests_dir / "package_inventory.json", inventory)
    manifest = {
        "schema_version": SURVIVAL_CLINICAL_REPORT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": f"{section_scope}_report_ready_package_created",
        "package_path": str(package_dir),
        "user_visible_package_path": str(package_dir),
        "overwrite_policy": "create_new_timestamped_package_directory",
        "section_scope": section_scope,
        "included_result_ids": [str(selected.get("result_id") or "")],
        "excluded_result_semantics": ["imported_external_result", "testing_level", "exploratory", "preflight_only"],
        "clinical_conclusion_enabled": False,
        "full_integrated_report_enabled": False,
        "allow_table_only_report": allow_table_only_report,
        "package_inventory": inventory,
        "gate": gate,
    }
    _write_json(package_dir / manifest_filename, manifest)
    selected["report_ready_eligible"] = True
    selected["report_artifacts"] = [
        *[item for item in selected.get("report_artifacts", []) or [] if isinstance(item, dict) and item.get("artifact_type") != artifact_type],
        {
            "artifact_type": artifact_type,
            "path": str((package_dir / manifest_filename).relative_to(root)),
            "schema": SURVIVAL_CLINICAL_REPORT_PACKAGE_SCHEMA_VERSION,
            "section_scope": section_scope,
        },
    ]
    selected["updated_at"] = _now()
    save_registry(root, entries)
    return manifest


def _base_entry_blockers(root: Path, entry: dict[str, Any], *, required_artifacts: tuple[str, ...]) -> list[str]:
    blockers: list[str] = []
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_not_passed")
    if entry.get("validation_status") not in {"passed", "warning"}:
        blockers.append("validation_status_not_passed")
    if entry.get("blockers"):
        blockers.append("source_result_has_blockers")
    if not entry.get("parameters_manifest"):
        blockers.append("missing_parameters_manifest")
    artifact_paths = _artifact_paths(entry)
    for artifact_type in required_artifacts:
        artifact_path = artifact_paths.get(artifact_type, "")
        if not artifact_path:
            blockers.append(f"missing_output_artifact:{artifact_type}")
        elif not _resolve(root, artifact_path).is_file():
            blockers.append(f"missing_output_artifact_file:{artifact_type}")
    if not _has_existing_artifact_file(root, entry.get("log_artifacts", []) or []):
        blockers.append("missing_task_run_log_artifact")
    if entry.get("report_artifacts"):
        scopes = _registered_report_scopes(entry)
        invalid = [scope for scope in scopes if scope not in {"survival_km_logrank_only", "cox_univariate_only", "cox_multivariate_only", "risk_score_validation_only"}]
        blockers.extend(f"invalid_existing_report_artifact_scope:{scope}" for scope in invalid)
    return blockers


def _parameter_blockers(entry: dict[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    params = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    blockers: list[str] = []
    for field in required_fields:
        if not params.get(field) and not entry.get(field):
            blockers.append(f"missing_parameter_field:{field}")
    return blockers


def _artifact_paths(entry: dict[str, Any]) -> dict[str, str]:
    return {str(item.get("artifact_type") or ""): str(item.get("path") or "") for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)}


def _is_legacy_section_entry(entry: dict[str, Any], required_artifact_type: str) -> bool:
    params = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    if any(params.get(field) for field in ("survival_clinical_input_id", "survival_outcome_gate_id", "time_field", "event_field")):
        return False
    if entry.get("survival_clinical_input_id") or entry.get("survival_outcome_gate_id"):
        return False
    if required_artifact_type not in _artifact_paths(entry):
        return False
    return (
        normalize_result_semantics(entry.get("result_semantics"), default="") == "formal_computed_result"
        and entry.get("validation_status") in {"passed", "warning"}
        and not entry.get("blockers")
    )


def _schema_validation_view(entry: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entry)
    payload["report_ready_eligible"] = False
    payload["report_artifacts"] = []
    return payload


def _has_existing_artifact_file(root: Path, artifacts: object) -> bool:
    for artifact in artifacts if isinstance(artifacts, list | tuple) else []:
        if isinstance(artifact, dict) and _resolve(root, str(artifact.get("path") or artifact.get("file_path") or "")).is_file():
            return True
    return False


def _registered_report_scopes(entry: dict[str, Any]) -> list[str]:
    scopes: list[str] = []
    for artifact in entry.get("report_artifacts", []) or []:
        if isinstance(artifact, dict) and artifact.get("section_scope"):
            scopes.append(str(artifact.get("section_scope")))
    return list(dict.fromkeys(scopes))


def _has_formal_plot(entry: dict[str, Any], plot_type: str) -> bool:
    result_id = str(entry.get("result_id") or "")
    for artifact in entry.get("plot_artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        if str(artifact.get("plot_type") or "") != plot_type:
            continue
        if str(artifact.get("source_result_id") or "") not in {"", result_id}:
            continue
        if normalize_result_semantics(artifact.get("plot_semantics") or artifact.get("source_result_semantics"), default="") != "formal_computed_result":
            continue
        if artifact.get("blockers"):
            continue
        return True
    return False


def _clinical_text_detected(entry: dict[str, Any]) -> bool:
    forbidden_keys = {
        "clinical_conclusion",
        "prognosis_conclusion",
        "treatment_recommendation",
        "validated_risk_score",
        "diagnosis",
        "prognosis_label",
        "clinical_risk_group",
    }
    text_phrases = {"clinical advice", "medical advice", "治疗建议", "临床结论"}

    def visit(value: Any, *, parent_key: str = "") -> bool:
        if parent_key in {"warnings", "forbidden_outputs", "forbidden_fields", "minimum_conditions", "validation_gates"}:
            return False
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                if key_text in forbidden_keys and item not in (None, "", [], {}):
                    return True
                if visit(item, parent_key=key_text):
                    return True
            return False
        if isinstance(value, list | tuple):
            return any(visit(item, parent_key=parent_key) for item in value)
        if isinstance(value, str):
            lowered = value.lower()
            return any(phrase in lowered for phrase in text_phrases)
        return False

    return visit(entry)


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else root / candidate


def _next_package_dir(root: Path, section_scope: str, result_id: str) -> Path:
    base = root / "survival_clinical_report_package" / section_scope
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    candidate = base / f"{stamp}_{_safe_name(result_id)}"
    counter = 1
    while candidate.exists():
        candidate = base / f"{stamp}_{_safe_name(result_id)}_{counter}"
        counter += 1
    return candidate


def _copy_artifact_group(root: Path, artifacts: object, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts if isinstance(artifacts, list | tuple) else []:
        if not isinstance(artifact, dict):
            continue
        source = _resolve(root, str(artifact.get("path") or artifact.get("file_path") or ""))
        if source.is_file():
            shutil.copy2(source, target / source.name)


def _write_plot_artifact_files(root: Path, target: Path, artifacts: object) -> None:
    target.mkdir(parents=True, exist_ok=True)
    serializable = [artifact for artifact in artifacts if isinstance(artifact, dict)] if isinstance(artifacts, list | tuple) else []
    _write_json(target / "plot_artifacts.json", serializable)
    for artifact in serializable:
        image_artifacts = artifact.get("image_artifacts", []) if isinstance(artifact.get("image_artifacts"), list | tuple) else []
        _copy_artifact_group(root, image_artifacts, target)


def _warnings_limitations(gate: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.survival_clinical_warnings_limitations.v1",
        "gate_warnings": list(gate.get("warnings", []) or []),
        "result_warnings": list(entry.get("warnings", []) or []),
        "limitations": [
            "Statistical research section only.",
            "No clinical diagnosis, prognosis, treatment recommendation, or validated risk score.",
            "Section-only package is not a full integrated report.",
            "Warnings, blockers, dependencies, and provenance must remain attached.",
        ],
    }


def _provenance(gate: dict[str, Any], entry: dict[str, Any], root: Path) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.survival_clinical_report_provenance.v1",
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "input_package_id": str(entry.get("input_package_id") or ""),
        "survival_clinical_input_id": str(entry.get("survival_clinical_input_id") or ""),
        "survival_outcome_gate_id": str(entry.get("survival_outcome_gate_id") or ""),
        "result_index_path": str(root / RESULT_INDEX),
        "gate_status": str(gate.get("status") or ""),
    }


def _limitations_markdown(*, allow_table_only_report: bool) -> str:
    table_only = "- Table-only mode was explicitly allowed; missing plot artifacts do not imply plot generation failure.\n" if allow_table_only_report else ""
    return (
        "# Limitations\n\n"
        "- This package is a statistical research section only.\n"
        "- This package does not provide clinical diagnosis, prognosis, treatment recommendation, or validated risk score.\n"
        "- This package is section-only and is not a full integrated report.\n"
        f"{table_only}"
        "- All provenance, dependency snapshots, warnings, and limitations must remain attached.\n"
    )


def _section_report_markdown(title: str, entry: dict[str, Any], gate: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "This is a statistical research section only. It is not clinical advice, diagnosis, prognosis, or treatment recommendation.",
            "",
            "## Source Result",
            "",
            f"- result_id: `{entry.get('result_id', '')}`",
            f"- task_type: `{entry.get('task_type', '')}`",
            f"- result_semantics: `{entry.get('result_semantics', '')}`",
            f"- validation_status: `{entry.get('validation_status', '')}`",
            f"- report_ready_gate_status: `{gate.get('status', '')}`",
            "",
            "## Boundary",
            "",
            "- No clinical conclusion is generated.",
            "- No full integrated report is generated.",
            "- No new risk score model, risk group, clinical conclusion, or treatment recommendation is generated.",
            "",
        ]
    )


def _package_inventory(package_dir: Path) -> dict[str, Any]:
    files = sorted(str(path.relative_to(package_dir)) for path in package_dir.rglob("*") if path.is_file())
    required = ["README_limitations.md", "manifests/gate_snapshot.json", "manifests/source_result_entry.json", "manifests/package_inventory.json", "provenance/provenance.json"]
    return {
        "schema_version": "biomedpilot.survival_clinical_report_package_inventory.v1",
        "package_root": str(package_dir),
        "files": files,
        "required_files": {name: (package_dir / name).is_file() for name in required},
        "required_directories": {name: (package_dir / name).is_dir() for name in ("tables", "plots", "manifests", "logs", "provenance")},
    }


def _safe_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return safe.strip("_") or "section"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
