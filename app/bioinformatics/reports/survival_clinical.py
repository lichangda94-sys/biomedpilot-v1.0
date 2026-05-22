from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry
from app.bioinformatics.survival_clinical._io import read_table
from app.bioinformatics.survival_clinical.cox_result_schema import validate_cox_result_index_entry, validate_cox_result_table
from app.bioinformatics.survival_clinical.km_result_schema import validate_km_result_index_entry, validate_km_result_tables


KM_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.km_logrank_report_ready_gate.v1"
COX_REPORT_READY_GATE_SCHEMA_VERSION = "biomedpilot.cox_univariate_report_ready_gate.v1"
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
    blockers.extend(_base_entry_blockers(root, entry, required_artifacts=("km_curve_table", "logrank_result_table")))
    schema_gate = validate_km_result_index_entry(entry)
    blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
    table_paths = _artifact_paths(entry)
    km_rows = read_table(_resolve(root, table_paths.get("km_curve_table", "")))
    logrank_rows = read_table(_resolve(root, table_paths.get("logrank_result_table", "")))
    table_gate = validate_km_result_tables(km_rows, logrank_rows)
    blockers.extend(str(item) for item in table_gate.get("blockers", []) or [])
    warnings.extend(str(item) for item in table_gate.get("warnings", []) or [])
    blockers.extend(_parameter_blockers(entry, ("survival_clinical_input_id", "survival_outcome_gate_id", "time_field", "event_field", "grouping_variable", "group_a", "group_b", "censoring_policy", "missingness_policy")))
    if not allow_table_only_report and not _has_formal_plot(entry, "km_curve"):
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
    entry = _select_entry(root, "cox_univariate", result_id)
    if entry is None:
        return _gate(
            COX_REPORT_READY_GATE_SCHEMA_VERSION,
            "blocked",
            result_id or "",
            "cox_univariate",
            allow_table_only_report,
            ["missing_cox_univariate_result"],
            [],
            {},
        )
    blockers: list[str] = []
    warnings: list[str] = [str(item) for item in entry.get("warnings", []) or []]
    if normalize_result_semantics(entry.get("result_semantics"), default="") != "formal_computed_result":
        blockers.append("cox_report_ready_requires_formal_computed_result")
    if entry.get("task_type") != "cox_univariate":
        blockers.append("cox_report_ready_requires_cox_univariate_task")
    blockers.extend(_base_entry_blockers(root, entry, required_artifacts=("cox_result_table",)))
    schema_gate = validate_cox_result_index_entry(entry)
    blockers.extend(str(item) for item in schema_gate.get("blockers", []) or [])
    table_paths = _artifact_paths(entry)
    cox_rows = read_table(_resolve(root, table_paths.get("cox_result_table", "")))
    table_gate = validate_cox_result_table(cox_rows)
    blockers.extend(str(item) for item in table_gate.get("blockers", []) or [])
    warnings.extend(str(item) for item in table_gate.get("warnings", []) or [])
    blockers.extend(_parameter_blockers(entry, ("survival_clinical_input_id", "survival_outcome_gate_id", "time_field", "event_field", "covariate", "covariate_type", "missing_value_policy", "minimum_event_count")))
    if not allow_table_only_report and not _has_formal_plot(entry, "cox_forest_plot"):
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


def _gate(schema: str, status: str, selected_result_id: str, task_type: str, allow_table_only: bool, blockers: list[str], warnings: list[str], diagnostics: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": schema,
        "status": status,
        "selected_result_id": selected_result_id,
        "task_type": task_type,
        "section_scope": f"{task_type}_only",
        "package_creation_enabled": False,
        "allow_table_only_report": allow_table_only,
        "report_ready_eligible": False,
        "clinical_boundary": "Statistical research section only; no clinical diagnosis, prognosis, treatment recommendation, or validated risk score.",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "diagnostics": diagnostics,
    }


def _select_entry(root: Path, task_type: str, result_id: str | None) -> dict[str, Any] | None:
    entries = [entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict)]
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if str(entry.get("task_type") or "") == task_type]
    formal = [entry for entry in candidates if normalize_result_semantics(entry.get("result_semantics"), default="") == "formal_computed_result"]
    return (formal or candidates or [None])[-1]


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
        blockers.append("source_result_already_has_report_artifacts")
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


def _has_existing_artifact_file(root: Path, artifacts: object) -> bool:
    for artifact in artifacts if isinstance(artifacts, list | tuple) else []:
        if isinstance(artifact, dict) and _resolve(root, str(artifact.get("path") or artifact.get("file_path") or "")).is_file():
            return True
    return False


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
    text = str({key: value for key, value in entry.items() if key not in {"warnings"}}).lower()
    return any(phrase.lower() in text for phrase in FORBIDDEN_CLINICAL_PHRASES)


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else root / candidate
