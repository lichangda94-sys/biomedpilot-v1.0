from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .formal_deg import evaluate_formal_deg_report_ready_gate
from .gsea import evaluate_gsea_report_ready_gate
from .ora import evaluate_ora_report_ready_gate


FULL_INTEGRATED_REPORT_READY_SCHEMA_VERSION = "biomedpilot.full_integrated_report_gate.v1"
REQUIRED_SECTION_IDS = ("formal_deg", "ora_enrichment", "gsea_preranked", "survival_km_logrank", "cox")
SECTION_TASK_TYPES = {
    "formal_deg": ("deg",),
    "ora_enrichment": ("ora_enrichment",),
    "gsea_preranked": ("gsea_preranked",),
    "survival_km_logrank": ("survival_km_logrank",),
    "cox": ("cox_univariate", "cox_multivariate"),
}


def evaluate_full_integrated_report_gate(
    project_root: str | Path,
    *,
    section_result_ids: dict[str, str] | None = None,
    include_sections: list[str] | None = None,
    allow_markdown_only: bool = True,
    allow_missing_optional_sections: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    section_ids = tuple(include_sections or REQUIRED_SECTION_IDS)
    explicit = section_result_ids or {}
    blockers: list[str] = []
    warnings: list[str] = []
    section_rows: list[dict[str, Any]] = []
    checks = {
        "result_index_exists": bool(entries),
        "required_sections_present": True,
        "all_sections_formal_computed": True,
        "all_sections_have_result_index_v2_fields": True,
        "all_sections_validation_passed": True,
        "all_sections_dependency_snapshot_passed": True,
        "all_sections_task_run_log_present": True,
        "all_sections_source_tables_present": True,
        "section_report_ready_gates_passed": True,
        "survival_clinical_report_ready_available": False,
        "warnings_limitations_provenance_included": True,
        "no_clinical_conclusion": True,
        "no_imported_testing_exploratory_or_preflight": True,
    }
    if not checks["result_index_exists"]:
        blockers.append("result_index_missing_or_empty")
    for section_id in section_ids:
        row = _section_row(root, entries, section_id, explicit.get(section_id, ""))
        section_rows.append(row)
        blockers.extend(row["blockers"])
        warnings.extend(row["warnings"])
        checks["required_sections_present"] = checks["required_sections_present"] and row["result_present"]
        checks["all_sections_formal_computed"] = checks["all_sections_formal_computed"] and row["result_semantics"] == "formal_computed_result"
        checks["all_sections_have_result_index_v2_fields"] = checks["all_sections_have_result_index_v2_fields"] and row["result_index_v2_fields_present"]
        checks["all_sections_validation_passed"] = checks["all_sections_validation_passed"] and row["validation_status"] in {"passed", "warning"}
        checks["all_sections_dependency_snapshot_passed"] = checks["all_sections_dependency_snapshot_passed"] and row["dependency_snapshot_passed"]
        checks["all_sections_task_run_log_present"] = checks["all_sections_task_run_log_present"] and row["task_run_log_present"]
        checks["all_sections_source_tables_present"] = checks["all_sections_source_tables_present"] and row["source_tables_present"]
        checks["section_report_ready_gates_passed"] = checks["section_report_ready_gates_passed"] and row["section_report_ready_status"] == "passed"
        checks["no_imported_testing_exploratory_or_preflight"] = checks["no_imported_testing_exploratory_or_preflight"] and row["result_semantics"] not in {"imported_external_result", "testing_level", "exploratory", "preflight_only"}
    if not allow_missing_optional_sections:
        for check_name, passed in checks.items():
            if not passed and check_name not in {"survival_clinical_report_ready_available"}:
                blockers.append(check_name)
    blockers.append("survival_clinical_report_ready_not_implemented")
    blockers.append("full_integrated_report_export_not_enabled_in_b23_1")
    status = "blocked" if blockers else "eligible_for_full_integrated_report"
    return {
        "schema_version": FULL_INTEGRATED_REPORT_READY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": status,
        "section_scope": "full_integrated_report",
        "result_index_path": str(root / RESULT_INDEX),
        "allow_markdown_only": allow_markdown_only,
        "allow_missing_optional_sections": allow_missing_optional_sections,
        "required_sections": list(section_ids),
        "section_rows": section_rows,
        "checks": checks,
        "package_layout": [
            "integrated_report.md",
            "sections/",
            "tables/",
            "plots/",
            "manifests/",
            "logs/",
            "provenance/",
            "README_limitations.md",
        ],
        "limitations_required": [
            "Statistical research report only.",
            "No clinical diagnosis, prognosis, or treatment recommendation.",
            "Section-only reports are not full integrated reports.",
            "Warnings, blockers, dependencies, and provenance must remain attached.",
        ],
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _section_row(root: Path, entries: list[dict[str, Any]], section_id: str, explicit_result_id: str) -> dict[str, Any]:
    entry = _select_entry(entries, section_id, explicit_result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    if entry is None:
        blockers.append(f"section_result_missing:{section_id}")
        return {
            "section_id": section_id,
            "result_present": False,
            "result_id": explicit_result_id,
            "task_type": "",
            "result_semantics": "",
            "validation_status": "",
            "result_index_v2_fields_present": False,
            "dependency_snapshot_passed": False,
            "task_run_log_present": False,
            "source_tables_present": False,
            "plot_artifact_status": "missing",
            "section_report_ready_status": "missing",
            "section_report_ready_gate": {},
            "blockers": blockers,
            "warnings": warnings,
        }
    result_id = str(entry.get("result_id") or "")
    task_type = str(entry.get("task_type") or "")
    semantics = normalize_result_semantics(entry.get("result_semantics"), default="")
    if semantics != "formal_computed_result":
        blockers.append(f"section_result_not_formal:{section_id}:{result_id}")
        if semantics in {"imported_external_result", "testing_level", "exploratory", "preflight_only"}:
            blockers.append(f"non_formal_result_forbidden_in_full_integrated_report:{result_id}")
    if task_type not in SECTION_TASK_TYPES.get(section_id, ()):
        blockers.append(f"section_task_type_mismatch:{section_id}:{task_type or 'missing'}")
    required_fields = ("result_id", "task_run_id", "task_type", "result_semantics", "input_package_id", "parameters_manifest", "engine_name", "engine_version", "dependency_snapshot", "output_artifacts", "validation_status", "log_artifacts")
    fields_present = all(entry.get(field_name) not in (None, "", []) for field_name in required_fields)
    if not fields_present:
        missing = [field_name for field_name in required_fields if entry.get(field_name) in (None, "", [])]
        blockers.extend(f"section_result_index_missing_field:{section_id}:{field_name}" for field_name in missing)
    dependency = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    dependency_passed = dependency.get("status") == "passed"
    if not dependency_passed:
        blockers.append(f"section_dependency_snapshot_not_passed:{section_id}:{result_id}")
    validation_status = str(entry.get("validation_status") or "")
    if validation_status not in {"passed", "warning"}:
        blockers.append(f"section_validation_not_passed:{section_id}:{result_id}")
    if entry.get("blockers"):
        blockers.append(f"section_result_has_blockers:{section_id}:{result_id}")
    task_log_present = _task_log_present(root, entry)
    if not task_log_present:
        blockers.append(f"section_task_run_log_missing:{section_id}:{result_id}")
    source_tables = _source_tables_present(root, entry)
    if not source_tables:
        blockers.append(f"section_source_table_missing:{section_id}")
    plot_status = _plot_status(entry)
    report_gate = _section_report_gate(root, section_id, result_id)
    report_status = _section_report_status(section_id, report_gate)
    if report_status != "passed":
        blockers.append(f"section_report_ready_not_passed:{section_id}:{result_id}")
        if section_id in {"survival_km_logrank", "cox"}:
            blockers.append(f"section_report_ready_gate_missing:{section_id}")
    warnings.extend(str(item) for item in entry.get("warnings", []) or [])
    return {
        "section_id": section_id,
        "result_present": True,
        "result_id": result_id,
        "task_type": task_type,
        "result_semantics": semantics,
        "validation_status": validation_status,
        "result_index_v2_fields_present": fields_present,
        "dependency_snapshot_passed": dependency_passed,
        "task_run_log_present": task_log_present,
        "source_tables_present": source_tables,
        "plot_artifact_status": plot_status,
        "section_report_ready_status": report_status,
        "section_report_ready_gate": report_gate,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _select_entry(entries: list[dict[str, Any]], section_id: str, explicit_result_id: str) -> dict[str, Any] | None:
    if explicit_result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == explicit_result_id), None)
    task_types = SECTION_TASK_TYPES.get(section_id, ())
    candidates = [entry for entry in entries if str(entry.get("task_type") or "") in task_types]
    formal = [entry for entry in candidates if normalize_result_semantics(entry.get("result_semantics"), default="") == "formal_computed_result"]
    return (formal or candidates or [None])[-1]


def _section_report_gate(root: Path, section_id: str, result_id: str) -> dict[str, Any]:
    if section_id == "formal_deg":
        return evaluate_formal_deg_report_ready_gate(root, result_id=result_id)
    if section_id == "ora_enrichment":
        return evaluate_ora_report_ready_gate(root, result_id=result_id, allow_imported_derived_report=False)
    if section_id == "gsea_preranked":
        return evaluate_gsea_report_ready_gate(root, result_id=result_id, allow_imported_derived_report=False)
    return {
        "schema_version": "biomedpilot.survival_clinical_report_ready_gate.placeholder.v1",
        "status": "blocked",
        "selected_result_id": result_id,
        "blockers": ["survival_clinical_report_ready_not_implemented"],
        "warnings": [],
    }


def _section_report_status(section_id: str, gate: dict[str, Any]) -> str:
    passing = {
        "formal_deg": "eligible_for_formal_deg_report_ready",
        "ora_enrichment": "eligible_for_ora_report_ready",
        "gsea_preranked": "eligible_for_gsea_report_ready",
    }
    return "passed" if gate.get("status") == passing.get(section_id) else "blocked"


def _source_tables_present(root: Path, entry: dict[str, Any]) -> bool:
    artifacts = [item for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict)]
    if not artifacts:
        return False
    for artifact in artifacts:
        path = _artifact_path(root, artifact)
        if path.is_file():
            return True
    return False


def _task_log_present(root: Path, entry: dict[str, Any]) -> bool:
    for artifact in entry.get("log_artifacts", []) or []:
        if isinstance(artifact, dict) and _artifact_path(root, artifact).is_file():
            return True
    return False


def _plot_status(entry: dict[str, Any]) -> str:
    plots = [item for item in entry.get("plot_artifacts", []) or [] if isinstance(item, dict)]
    if not plots:
        return "missing"
    real_images = any(item.get("image_artifacts") for item in plots)
    return "real_artifact_registered" if real_images else "spec_or_manifest_registered"


def _artifact_path(root: Path, artifact: dict[str, Any]) -> Path:
    path = Path(str(artifact.get("path") or artifact.get("file_path") or "")).expanduser()
    return path if path.is_absolute() else root / path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
