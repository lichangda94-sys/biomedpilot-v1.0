from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .formal_deg import evaluate_formal_deg_report_ready_gate
from .gsea import evaluate_gsea_report_ready_gate
from .ora import evaluate_ora_report_ready_gate


FULL_INTEGRATED_REPORT_READY_SCHEMA_VERSION = "biomedpilot.full_integrated_report_gate.v1"
FULL_INTEGRATED_REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.full_integrated_report_package.v1"
FULL_INTEGRATED_REPORT_RENDERER_GATE_SCHEMA_VERSION = "biomedpilot.full_integrated_report_renderer_gate.v1"
REQUIRED_SECTION_IDS = ("formal_deg", "ora_enrichment", "gsea_preranked", "survival_km_logrank", "cox")
PACKAGE_DIRECTORIES = ("sections", "tables", "plots", "manifests", "logs", "provenance")
PACKAGE_REQUIRED_FILES = (
    "integrated_report.md",
    "README_limitations.md",
    "integrated_report_package_manifest.json",
    "manifests/full_integrated_gate_snapshot.json",
    "manifests/result_index_snapshot.json",
    "manifests/section_manifest.json",
    "manifests/dependency_snapshot.json",
    "manifests/warnings_limitations.json",
    "manifests/package_inventory.json",
)
SECTION_TASK_TYPES = {
    "formal_deg": ("deg",),
    "ora_enrichment": ("ora_enrichment",),
    "gsea_preranked": ("gsea_preranked",),
    "survival_km_logrank": ("survival_km_logrank",),
    "cox": ("cox_univariate", "cox_multivariate"),
}
SECTION_LABELS = {
    "formal_deg": "Formal DEG",
    "ora_enrichment": "ORA enrichment",
    "gsea_preranked": "Preranked GSEA",
    "survival_km_logrank": "KM/log-rank survival",
    "cox": "Cox clinical association",
}
SECTION_PLOT_REQUIREMENTS = {
    "formal_deg": "formal_deg_plot_or_explicit_table_only_mode",
    "ora_enrichment": "ora_plot_or_explicit_table_only_mode",
    "gsea_preranked": "gsea_plot_or_explicit_table_only_mode",
    "survival_km_logrank": "formal_km_plot_artifact_required_after_survival_report_ready_exists",
    "cox": "formal_cox_plot_artifact_required_after_survival_report_ready_exists",
}
SUPPORTED_EXPORT_FORMATS = ("markdown", "pdf", "docx")


def create_full_integrated_report_package(
    project_root: str | Path,
    *,
    section_result_ids: dict[str, str] | None = None,
    include_sections: list[str] | None = None,
    export_format: str = "markdown",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = evaluate_full_integrated_report_gate(root, section_result_ids=section_result_ids, include_sections=include_sections)
    renderer_gate = evaluate_full_integrated_report_renderer_gate(export_format)
    package_plan = build_full_integrated_report_package_plan(root, gate=gate, export_format=export_format, renderer_gate=renderer_gate)
    renderer_blockers = list(renderer_gate.get("blockers", []) or [])
    if gate.get("status") != "eligible_for_full_integrated_report" or renderer_gate.get("status") != "passed":
        return {
            "schema_version": FULL_INTEGRATED_REPORT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "user_visible_package_path": "",
            "overwrite_policy": "create_new_timestamped_package_directory_when_gate_passes",
            "gate": gate,
            "package_plan": package_plan,
            "renderer_gate": renderer_gate,
            "blockers": list(dict.fromkeys([*list(gate.get("blockers", []) or []), *renderer_blockers])),
            "warnings": list(gate.get("warnings", []) or []),
        }
    package_dir = _next_package_dir(root)
    _create_package_directories(package_dir)
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected_entries = _selected_entries(entries, gate.get("section_rows", []) or [])
    section_manifest = _section_manifest(gate.get("section_rows", []) or [], selected_entries)
    _write_json(package_dir / "manifests" / "full_integrated_gate_snapshot.json", gate)
    _write_json(package_dir / "manifests" / "result_index_snapshot.json", registry)
    _write_json(package_dir / "manifests" / "section_manifest.json", section_manifest)
    _write_json(package_dir / "manifests" / "dependency_snapshot.json", _dependency_snapshot(selected_entries))
    _write_json(package_dir / "manifests" / "warnings_limitations.json", _warnings_limitations(gate, selected_entries))
    _write_section_markdown(package_dir / "sections", selected_entries)
    _copy_registered_artifacts(root, selected_entries, package_dir=package_dir)
    (package_dir / "integrated_report.md").write_text(_integrated_report_markdown(gate, selected_entries), encoding="utf-8")
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(), encoding="utf-8")
    manifest = {
        "schema_version": FULL_INTEGRATED_REPORT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "full_integrated_report_package_created",
        "section_scope": "full_integrated_report",
        "package_path": str(package_dir),
        "user_visible_package_path": str(package_dir),
        "overwrite_policy": "create_new_timestamped_package_directory",
        "export_format": export_format,
        "gate": gate,
        "renderer_gate": renderer_gate,
        "package_plan": package_plan,
        "package_inventory": {},
    }
    _write_json(package_dir / "integrated_report_package_manifest.json", manifest)
    inventory = _package_inventory(package_dir)
    _write_json(package_dir / "manifests" / "package_inventory.json", inventory)
    manifest["package_inventory"] = inventory
    _write_json(package_dir / "integrated_report_package_manifest.json", manifest)
    return manifest


def build_full_integrated_report_package_plan(
    project_root: str | Path,
    *,
    gate: dict[str, Any] | None = None,
    export_format: str = "markdown",
    renderer_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = gate or evaluate_full_integrated_report_gate(root)
    renderer_gate = renderer_gate or evaluate_full_integrated_report_renderer_gate(export_format)
    disabled_reasons = _package_plan_disabled_reasons(gate, renderer_gate)
    return {
        "schema_version": "biomedpilot.full_integrated_report_package_plan.v1",
        "section_scope": "full_integrated_report",
        "export_format": renderer_gate.get("export_format", _canonical_export_format(export_format)),
        "package_root_policy": "report_package/integrated/<timestamp>_<project_name>",
        "required_directories": list(PACKAGE_DIRECTORIES),
        "required_files": list(PACKAGE_REQUIRED_FILES),
        "prerequisite_summary": gate.get("prerequisite_summary", {}),
        "renderer_gate": renderer_gate,
        "renderer_status": renderer_gate.get("status", "blocked"),
        "renderer_id": renderer_gate.get("renderer_id", ""),
        "renderer_disabled_reason": renderer_gate.get("disabled_reason", ""),
        "renderer_dependencies": list(renderer_gate.get("required_dependencies", []) or []),
        "artifact_policy": {
            "tables": "copy only registered source result output_artifacts",
            "plots": "copy only registered plot artifacts and image_artifacts",
            "logs": "copy only registered task-run log_artifacts",
            "manifests": "write gate, result index, section, dependency, warnings and inventory snapshots",
            "forbidden_sources": ["preflight_only", "testing_level", "exploratory", "imported_external_result", "legacy_only"],
        },
        "can_create_package": gate.get("status") == "eligible_for_full_integrated_report" and renderer_gate.get("status") == "passed",
        "disabled_reasons": disabled_reasons,
        "blocked_reason": "; ".join(disabled_reasons),
    }


def evaluate_full_integrated_report_renderer_gate(export_format: str = "markdown") -> dict[str, Any]:
    canonical = _canonical_export_format(export_format)
    blockers: list[str] = []
    warnings: list[str] = []
    required_dependencies: list[str] = []
    detected_dependencies: dict[str, dict[str, Any]] = {}
    renderer_id = ""
    implementation_enabled = False
    if canonical not in SUPPORTED_EXPORT_FORMATS:
        blockers.append(f"full_integrated_export_format_unsupported:{canonical or 'missing'}")
    elif canonical == "markdown":
        renderer_id = "builtin_markdown"
        implementation_enabled = True
    elif canonical == "docx":
        renderer_id = "pandoc_docx"
        required_dependencies = ["pandoc"]
        detected_dependencies = {name: _detect_renderer_dependency(name) for name in required_dependencies}
        if not detected_dependencies["pandoc"]["available"]:
            blockers.append("renderer_dependency_missing:pandoc")
        blockers.append("full_integrated_docx_renderer_not_enabled_in_b23_4")
    elif canonical == "pdf":
        renderer_id = "pandoc_pdf"
        pandoc = _detect_renderer_dependency("pandoc")
        latex = _detect_renderer_dependency("xelatex")
        wkhtmltopdf = _detect_renderer_dependency("wkhtmltopdf")
        required_dependencies = ["pandoc", "xelatex_or_wkhtmltopdf"]
        detected_dependencies = {"pandoc": pandoc, "xelatex": latex, "wkhtmltopdf": wkhtmltopdf}
        if not pandoc["available"]:
            blockers.append("renderer_dependency_missing:pandoc")
        if not latex["available"] and not wkhtmltopdf["available"]:
            blockers.append("renderer_dependency_missing:xelatex_or_wkhtmltopdf")
        blockers.append("full_integrated_pdf_renderer_not_enabled_in_b23_4")
    dependency_checks_passed = all(item.get("available") for item in detected_dependencies.values()) if canonical == "docx" else (
        bool(detected_dependencies.get("pandoc", {}).get("available"))
        and (bool(detected_dependencies.get("xelatex", {}).get("available")) or bool(detected_dependencies.get("wkhtmltopdf", {}).get("available")))
        if canonical == "pdf"
        else canonical == "markdown"
    )
    status = "passed" if not blockers and implementation_enabled else "blocked"
    disabled_reason = "; ".join(blockers)
    return {
        "schema_version": FULL_INTEGRATED_REPORT_RENDERER_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": status,
        "export_format": canonical,
        "requested_format": export_format,
        "renderer_id": renderer_id,
        "renderer_scope": "full_integrated_report_export_format",
        "required_dependencies": required_dependencies,
        "detected_dependencies": detected_dependencies,
        "checks": {
            "format_supported": canonical in SUPPORTED_EXPORT_FORMATS,
            "dependencies_detected": dependency_checks_passed,
            "implementation_enabled": implementation_enabled,
            "detect_first_no_install_action": True,
        },
        "disabled_reason": disabled_reason,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
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
    prerequisite_rows = _full_integrated_prerequisite_rows(section_rows)
    prerequisite_summary = _full_integrated_prerequisite_summary(prerequisite_rows)
    checks["full_integrated_content_prerequisites_passed"] = prerequisite_summary["blocked_count"] == 0
    if not allow_missing_optional_sections:
        for check_name, passed in checks.items():
            if not passed and check_name not in {"survival_clinical_report_ready_available"}:
                blockers.append(check_name)
    blockers.extend(row_blocker for row in prerequisite_rows for row_blocker in row.get("blockers", []) or [])
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
        "prerequisite_rows": prerequisite_rows,
        "prerequisite_summary": prerequisite_summary,
        "survival_clinical_report_ready_required": True,
        "export_activation_status": "blocked_until_full_integrated_content_gate_and_renderer_gate_pass",
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
            "section_report_ready_gate_schema": "",
            "section_package_scope": "",
            "registered_report_scopes": [],
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
        "section_report_ready_gate_schema": str(report_gate.get("schema_version") or ""),
        "section_package_scope": _section_package_scope(report_gate),
        "registered_report_scopes": _registered_report_scopes(entry),
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


def _full_integrated_prerequisite_rows(section_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_id in REQUIRED_SECTION_IDS:
        section = next((row for row in section_rows if row.get("section_id") == section_id), {})
        blockers: list[str] = []
        if not section.get("result_present"):
            blockers.append(f"full_integrated_prerequisite_missing_result:{section_id}")
        if section.get("result_semantics") != "formal_computed_result":
            blockers.append(f"full_integrated_prerequisite_requires_formal_result:{section_id}")
        if section.get("validation_status") not in {"passed", "warning"}:
            blockers.append(f"full_integrated_prerequisite_validation_not_passed:{section_id}")
        if not section.get("dependency_snapshot_passed"):
            blockers.append(f"full_integrated_prerequisite_dependency_not_passed:{section_id}")
        if not section.get("task_run_log_present"):
            blockers.append(f"full_integrated_prerequisite_task_log_missing:{section_id}")
        if not section.get("source_tables_present"):
            blockers.append(f"full_integrated_prerequisite_source_table_missing:{section_id}")
        if section.get("section_report_ready_status") != "passed":
            blockers.append(f"full_integrated_prerequisite_section_report_ready_not_passed:{section_id}")
        if section_id in {"survival_km_logrank", "cox"}:
            blockers.append(f"full_integrated_prerequisite_survival_clinical_report_ready_missing:{section_id}")
        if _has_section_only_report_scope(section):
            blockers.append(f"full_integrated_prerequisite_forbids_section_package_as_full_report:{section_id}")
        row_status = "passed" if not blockers else "blocked"
        rows.append(
            {
                "section_id": section_id,
                "section_label": SECTION_LABELS.get(section_id, section_id),
                "result_id": str(section.get("result_id") or ""),
                "required_result_semantics": "formal_computed_result",
                "observed_result_semantics": str(section.get("result_semantics") or ""),
                "result_index_v2_status": "passed" if section.get("result_index_v2_fields_present") else "blocked",
                "validation_status": str(section.get("validation_status") or ""),
                "dependency_status": "passed" if section.get("dependency_snapshot_passed") else "blocked",
                "task_run_log_status": "present" if section.get("task_run_log_present") else "missing",
                "source_table_status": "present" if section.get("source_tables_present") else "missing",
                "plot_requirement": SECTION_PLOT_REQUIREMENTS.get(section_id, "section_plot_or_table_only_requirement"),
                "plot_artifact_status": str(section.get("plot_artifact_status") or ""),
                "section_report_ready_status": str(section.get("section_report_ready_status") or ""),
                "section_report_ready_gate_schema": str(section.get("section_report_ready_gate_schema") or ""),
                "section_package_scope": str(section.get("section_package_scope") or ""),
                "registered_report_scopes": list(section.get("registered_report_scopes", []) or []),
                "full_integrated_scope_required": True,
                "section_only_package_sufficient": False,
                "status": row_status,
                "disabled_reason": "; ".join(dict.fromkeys(blockers)),
                "blockers": list(dict.fromkeys(blockers)),
            }
        )
    return rows


def _full_integrated_prerequisite_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for row in rows if row.get("status") == "passed")
    blocked = len(rows) - passed
    return {
        "schema_version": "biomedpilot.full_integrated_report_prerequisite_summary.v1",
        "required_section_count": len(rows),
        "passed_count": passed,
        "blocked_count": blocked,
        "status": "passed" if blocked == 0 else "blocked",
        "blocked_sections": [row.get("section_id") for row in rows if row.get("status") != "passed"],
        "survival_clinical_report_ready_required": True,
        "section_only_package_sufficient": False,
    }


def _section_package_scope(gate: dict[str, Any]) -> str:
    scope = gate.get("section_scope") or gate.get("package_scope")
    if scope:
        return str(scope)
    return str((gate.get("manifest") or {}).get("section_scope") or "") if isinstance(gate.get("manifest"), dict) else ""


def _registered_report_scopes(entry: dict[str, Any]) -> list[str]:
    scopes: list[str] = []
    for artifact in entry.get("report_artifacts", []) or []:
        if isinstance(artifact, dict) and artifact.get("section_scope"):
            scopes.append(str(artifact.get("section_scope")))
    return list(dict.fromkeys(scopes))


def _has_section_only_report_scope(section: dict[str, Any]) -> bool:
    scopes = [str(section.get("section_package_scope") or ""), *(str(item) for item in section.get("registered_report_scopes", []) or [])]
    return any(scope and scope != "full_integrated_report" and scope.endswith("_only") for scope in scopes)


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


def _next_package_dir(root: Path) -> Path:
    base = root / "report_package" / "integrated"
    project_name = _safe_name(root.name or "project")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    candidate = base / f"{stamp}_{project_name}"
    counter = 1
    while candidate.exists():
        candidate = base / f"{stamp}_{project_name}_{counter}"
        counter += 1
    return candidate


def _create_package_directories(package_dir: Path) -> None:
    for directory in PACKAGE_DIRECTORIES:
        (package_dir / directory).mkdir(parents=True, exist_ok=True)


def _selected_entries(entries: list[dict[str, Any]], section_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result_ids = [str(row.get("result_id") or "") for row in section_rows if isinstance(row, dict)]
    return [entry for result_id in result_ids for entry in entries if str(entry.get("result_id") or "") == result_id]


def _section_manifest(section_rows: list[dict[str, Any]], entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {str(entry.get("result_id") or ""): entry for entry in entries}
    sections = []
    for row in section_rows:
        if not isinstance(row, dict):
            continue
        entry = by_id.get(str(row.get("result_id") or ""), {})
        sections.append(
            {
                "section_id": str(row.get("section_id") or ""),
                "result_id": str(row.get("result_id") or ""),
                "task_type": str(row.get("task_type") or ""),
                "result_semantics": str(row.get("result_semantics") or ""),
                "validation_status": str(row.get("validation_status") or ""),
                "input_package_id": str(entry.get("input_package_id") or ""),
                "source_dataset_id": str(entry.get("source_dataset_id") or ""),
                "engine_name": str(entry.get("engine_name") or ""),
                "engine_version": str(entry.get("engine_version") or ""),
                "plot_artifact_status": str(row.get("plot_artifact_status") or ""),
                "section_report_ready_status": str(row.get("section_report_ready_status") or ""),
            }
        )
    return {"schema_version": "biomedpilot.full_integrated_section_manifest.v1", "sections": sections}


def _dependency_snapshot(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        str(entry.get("result_id") or ""): entry.get("dependency_snapshot")
        for entry in entries
        if isinstance(entry.get("dependency_snapshot"), dict)
    }


def _warnings_limitations(gate: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    result_warnings = {
        str(entry.get("result_id") or ""): list(entry.get("warnings", []) or [])
        for entry in entries
    }
    return {
        "schema_version": "biomedpilot.full_integrated_warnings_limitations.v1",
        "gate_warnings": list(gate.get("warnings", []) or []),
        "result_warnings": result_warnings,
        "limitations": list(gate.get("limitations_required", []) or []),
        "clinical_boundary": "No clinical diagnosis, prognosis, treatment recommendation, or validated risk score interpretation.",
    }


def _write_section_markdown(target: Path, entries: list[dict[str, Any]]) -> None:
    for entry in entries:
        section = _section_id_from_task(str(entry.get("task_type") or "section"))
        path = target / f"{section}.md"
        path.write_text(
            f"# {section}\n\n"
            f"- result_id: `{entry.get('result_id', '')}`\n"
            f"- task_type: `{entry.get('task_type', '')}`\n"
            f"- result_semantics: `{entry.get('result_semantics', '')}`\n"
            f"- validation_status: `{entry.get('validation_status', '')}`\n\n"
            "This section is a statistical research summary only and is not a clinical conclusion.\n",
            encoding="utf-8",
        )


def _copy_registered_artifacts(root: Path, entries: list[dict[str, Any]], *, package_dir: Path) -> None:
    for entry in entries:
        _copy_artifact_group(root, entry.get("output_artifacts", []) or [], package_dir / "tables")
        _copy_artifact_group(root, entry.get("log_artifacts", []) or [], package_dir / "logs")
        for plot in entry.get("plot_artifacts", []) or []:
            if not isinstance(plot, dict):
                continue
            _write_json(package_dir / "plots" / f"{_safe_name(str(plot.get('plot_id') or 'plot'))}.json", plot)
            _copy_artifact_group(root, plot.get("image_artifacts", []) or [], package_dir / "plots")


def _copy_artifact_group(root: Path, artifacts: object, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts if isinstance(artifacts, list | tuple) else []:
        if not isinstance(artifact, dict):
            continue
        path = _artifact_path(root, artifact)
        if path.is_file():
            shutil.copy2(path, target / path.name)


def _integrated_report_markdown(gate: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Bioinformatics Full Integrated Report",
        "",
        "This is a statistical research report package. It is not clinical advice, diagnosis, prognosis, or treatment recommendation.",
        "",
        "## Included Sections",
        "",
    ]
    for entry in entries:
        lines.append(f"- `{entry.get('result_id', '')}`: {entry.get('task_type', '')} / {entry.get('result_semantics', '')}")
    lines.extend(["", "## Gate Summary", "", f"- gate_status: `{gate.get('status', '')}`", ""])
    return "\n".join(lines)


def _limitations_markdown() -> str:
    return (
        "# Limitations\n\n"
        "- This package is a statistical research report only.\n"
        "- This package does not provide clinical diagnosis, prognosis, treatment recommendation, or validated risk score interpretation.\n"
        "- Section-only report packages are not equivalent to this full integrated report package.\n"
        "- All result semantics, dependency snapshots, warnings, blockers, and provenance must remain attached.\n"
    )


def _package_inventory(package_dir: Path) -> dict[str, Any]:
    files = sorted(str(path.relative_to(package_dir)) for path in package_dir.rglob("*") if path.is_file())
    return {
        "schema_version": "biomedpilot.full_integrated_package_inventory.v1",
        "package_root": str(package_dir),
        "files": files,
        "required_directories": {name: (package_dir / name).is_dir() for name in PACKAGE_DIRECTORIES},
        "required_files": {name: (package_dir / name).is_file() for name in PACKAGE_REQUIRED_FILES},
    }


def _section_id_from_task(task_type: str) -> str:
    if task_type == "deg":
        return "formal_deg"
    if task_type == "ora_enrichment":
        return "ora"
    if task_type == "gsea_preranked":
        return "gsea"
    if task_type == "survival_km_logrank":
        return "survival_km"
    if task_type in {"cox_univariate", "cox_multivariate"}:
        return "cox"
    return _safe_name(task_type or "section")


def _safe_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return safe.strip("_") or "item"


def _canonical_export_format(value: str) -> str:
    text = str(value or "").strip().lower()
    return "markdown" if text in {"markdown", "md"} else text


def _package_plan_disabled_reasons(gate: dict[str, Any], renderer_gate: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if gate.get("status") != "eligible_for_full_integrated_report":
        reasons.extend(str(item) for item in gate.get("blockers", []) or [])
    if renderer_gate.get("status") != "passed":
        reasons.extend(str(item) for item in renderer_gate.get("blockers", []) or [])
    return list(dict.fromkeys(reasons))


def _detect_renderer_dependency(command: str) -> dict[str, Any]:
    executable = shutil.which(command)
    payload = {
        "command": command,
        "available": bool(executable),
        "path": executable or "",
        "version": "",
        "missing_reason": "" if executable else f"{command}_not_found_on_path",
    }
    if executable:
        payload["version"] = _renderer_dependency_version(executable)
    return payload


def _renderer_dependency_version(executable: str) -> str:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return "version_unavailable"
    text = (completed.stdout or completed.stderr or "").splitlines()
    return text[0].strip() if text else "version_unavailable"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
