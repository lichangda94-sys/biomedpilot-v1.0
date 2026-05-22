from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .formal_deg import evaluate_formal_deg_report_ready_gate
from .gsea import evaluate_gsea_report_ready_gate
from .ora import evaluate_ora_report_ready_gate
from .renderer_capability import build_report_renderer_capability_snapshot
from .renderer_runtime_policy import build_full_integrated_renderer_runtime_packaging_policy
from .survival_clinical import evaluate_cox_report_ready_gate, evaluate_km_logrank_report_ready_gate


FULL_INTEGRATED_REPORT_READY_SCHEMA_VERSION = "biomedpilot.full_integrated_report_gate.v1"
FULL_INTEGRATED_REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.full_integrated_report_package.v1"
FULL_INTEGRATED_REPORT_RENDERER_GATE_SCHEMA_VERSION = "biomedpilot.full_integrated_report_renderer_gate.v1"
FULL_INTEGRATED_DOCX_PREFLIGHT_SCHEMA_VERSION = "biomedpilot.full_integrated_docx_preflight_gate.v1"
FULL_INTEGRATED_RENDERED_EXPORTS_SCHEMA_VERSION = "biomedpilot.full_integrated_rendered_exports.v1"
FULL_INTEGRATED_DOCX_CONVERSION_LOG_SCHEMA_VERSION = "biomedpilot.full_integrated_docx_conversion_log.v1"
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
SURVIVAL_CLINICAL_SECTION_SCOPES = {
    "survival_km_logrank": "survival_km_logrank_only",
    "cox": "cox_univariate_only",
}
SURVIVAL_CLINICAL_SECTION_PACKAGE_FILES = {
    "survival_km_logrank": "km_logrank_report.md",
    "cox": "cox_univariate_report.md",
}
SECTION_PACKAGE_REQUIRED_FILES = (
    "README_limitations.md",
    "manifests/gate_snapshot.json",
    "manifests/result_index_snapshot.json",
    "manifests/source_result_entry.json",
    "manifests/parameters_manifest.json",
    "manifests/dependency_snapshot.json",
    "manifests/table_validation.json",
    "manifests/plot_artifacts.json",
    "manifests/warnings_limitations.json",
    "manifests/package_inventory.json",
    "provenance/provenance.json",
)


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
        "renderer_preflight_policy": _renderer_preflight_policy(str(renderer_gate.get("export_format") or export_format)),
        "renderer_runtime_packaging_policy": build_full_integrated_renderer_runtime_packaging_policy(),
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


def evaluate_full_integrated_docx_preflight_gate(
    package_path: str | Path,
    *,
    renderer_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package_dir = Path(package_path).expanduser().resolve()
    renderer_gate = renderer_gate or evaluate_full_integrated_report_renderer_gate("docx")
    blockers: list[str] = []
    warnings: list[str] = []
    manifest_path = package_dir / "integrated_report_package_manifest.json"
    markdown_path = package_dir / "integrated_report.md"
    planned_output_path = package_dir / "exports" / "integrated_report.docx"
    conversion_log_path = package_dir / "logs" / "docx_renderer_preflight.log"
    manifest = _read_json(manifest_path)
    markdown = ""

    if not package_dir.is_dir():
        blockers.append("docx_source_package_missing")
    if not manifest_path.is_file():
        blockers.append("docx_source_package_manifest_missing")
    if manifest:
        if manifest.get("status") != "full_integrated_report_package_created":
            blockers.append("docx_source_package_status_not_created")
        if manifest.get("section_scope") != "full_integrated_report":
            blockers.append("docx_source_package_scope_not_full_integrated_report")
        if manifest.get("export_format") != "markdown":
            blockers.append("docx_source_package_must_be_markdown_export")
        gate = manifest.get("gate") if isinstance(manifest.get("gate"), dict) else {}
        if gate.get("status") != "eligible_for_full_integrated_report":
            blockers.append("docx_source_full_integrated_gate_not_passed")
    if not markdown_path.is_file():
        blockers.append("docx_source_markdown_missing")
    else:
        markdown = markdown_path.read_text(encoding="utf-8")
        if not markdown.strip():
            blockers.append("docx_source_markdown_empty")
    for reference in _markdown_local_references(markdown):
        if not (package_dir / reference).resolve().is_file():
            blockers.append(f"docx_markdown_local_reference_missing:{reference}")
    forbidden = _forbidden_clinical_conclusion_terms(markdown)
    blockers.extend(f"docx_source_markdown_forbidden_clinical_conclusion:{term}" for term in forbidden)
    renderer_blockers = [str(item) for item in renderer_gate.get("blockers", []) or []]
    blockers.extend(renderer_blockers)
    blockers.append("full_integrated_docx_export_activation_required_b24_2")
    unique_blockers = list(dict.fromkeys(blockers))
    checks = {
        "source_package_exists": package_dir.is_dir(),
        "source_manifest_exists": manifest_path.is_file(),
        "source_package_full_integrated_markdown": bool(
            manifest
            and manifest.get("status") == "full_integrated_report_package_created"
            and manifest.get("section_scope") == "full_integrated_report"
            and manifest.get("export_format") == "markdown"
        ),
        "source_markdown_exists": markdown_path.is_file(),
        "source_markdown_nonempty": bool(markdown.strip()),
        "local_references_resolve": not any(item.startswith("docx_markdown_local_reference_missing:") for item in unique_blockers),
        "no_forbidden_clinical_conclusion": not any(item.startswith("docx_source_markdown_forbidden_clinical_conclusion:") for item in unique_blockers),
        "pandoc_detected": bool((renderer_gate.get("detected_dependencies", {}).get("pandoc") or {}).get("available")) if isinstance(renderer_gate.get("detected_dependencies"), dict) else False,
        "renderer_implementation_enabled": False,
        "detect_first_no_install_action": True,
        "no_conversion_invoked": True,
    }
    preflight_blockers = [item for item in unique_blockers if item != "full_integrated_docx_export_activation_required_b24_2"]
    preflight_status = "passed_pending_activation" if not preflight_blockers else "blocked"
    return {
        "schema_version": FULL_INTEGRATED_DOCX_PREFLIGHT_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked",
        "preflight_status": preflight_status,
        "source_package_path": str(package_dir),
        "source_manifest_path": str(manifest_path),
        "source_markdown_path": str(markdown_path),
        "export_format": "docx",
        "renderer_id": "pandoc_docx",
        "renderer_gate": renderer_gate,
        "runtime_packaging_policy": build_full_integrated_renderer_runtime_packaging_policy(),
        "planned_output_path": str(planned_output_path),
        "conversion_log_path": str(conversion_log_path),
        "overwrite_policy": "create_or_validate_inside_existing_timestamped_package_without_overwriting_markdown_source",
        "artifact_manifest_preview": {
            "artifact_type": "full_integrated_report_rendered_export",
            "source_package_id": str(manifest.get("created_at") or package_dir.name),
            "source_markdown_path": str(markdown_path),
            "export_format": "docx",
            "renderer_id": "pandoc_docx",
            "output_path": str(planned_output_path),
            "validation_status": "not_created_preflight_only",
        },
        "checks": checks,
        "disabled_reason": "; ".join(unique_blockers),
        "blockers": unique_blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_full_integrated_docx_rendered_export_skeleton(
    package_path: str | Path,
    *,
    renderer_gate: dict[str, Any] | None = None,
    failure_reason: str = "full_integrated_docx_conversion_not_enabled_b24_4",
) -> dict[str, Any]:
    package_dir = Path(package_path).expanduser().resolve()
    preflight_gate = evaluate_full_integrated_docx_preflight_gate(package_dir, renderer_gate=renderer_gate)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    output_path = _reserved_export_path(package_dir, "integrated_report", "docx", stamp=stamp)
    conversion_log_path = _reserved_log_path(package_dir, "docx_renderer", stamp=stamp)
    blockers = list(dict.fromkeys([*list(preflight_gate.get("blockers", []) or []), failure_reason]))
    log_payload = _docx_conversion_log_payload(
        package_dir,
        preflight_gate=preflight_gate,
        output_path=output_path,
        conversion_log_path=conversion_log_path,
        status="blocked",
        failure_reason="; ".join(blockers),
    )
    _write_json(conversion_log_path, log_payload)
    manifest = _rendered_exports_manifest(package_dir)
    attempt = {
        "artifact_id": f"docx_attempt_{stamp}",
        "artifact_type": "full_integrated_report_rendered_export_attempt",
        "source_package_id": _source_package_id(package_dir),
        "source_markdown_path": "integrated_report.md",
        "export_format": "docx",
        "renderer_id": "pandoc_docx",
        "renderer_version": _renderer_version_from_gate(preflight_gate),
        "renderer_dependency_snapshot": preflight_gate.get("renderer_gate", {}).get("detected_dependencies", {}),
        "output_path": str(output_path.relative_to(package_dir)) if _is_relative_to(output_path, package_dir) else str(output_path),
        "conversion_log_path": str(conversion_log_path.relative_to(package_dir)) if _is_relative_to(conversion_log_path, package_dir) else str(conversion_log_path),
        "validation_status": "blocked",
        "warnings": list(preflight_gate.get("warnings", []) or []),
        "blockers": blockers,
        "created_at": _now(),
    }
    manifest.setdefault("attempts", []).append(attempt)
    manifest["latest_attempt_status"] = "blocked"
    manifest["latest_attempt_log_path"] = attempt["conversion_log_path"]
    _write_json(package_dir / "manifests" / "rendered_exports.json", manifest)
    _update_package_manifest_rendered_exports(package_dir, manifest)
    return {
        "schema_version": "biomedpilot.full_integrated_docx_rendered_export_skeleton.v1",
        "created_at": _now(),
        "status": "blocked",
        "preflight_gate": preflight_gate,
        "rendered_exports_manifest_path": str(package_dir / "manifests" / "rendered_exports.json"),
        "conversion_log_path": str(conversion_log_path),
        "planned_output_path": str(output_path),
        "artifact_attempt": attempt,
        "blockers": blockers,
        "warnings": list(preflight_gate.get("warnings", []) or []),
    }


def evaluate_full_integrated_report_renderer_gate(export_format: str = "markdown") -> dict[str, Any]:
    canonical = _canonical_export_format(export_format)
    capability_snapshot = build_report_renderer_capability_snapshot(commands=("pandoc", "xelatex", "wkhtmltopdf"))
    capabilities = capability_snapshot.get("capabilities", {}) if isinstance(capability_snapshot.get("capabilities"), dict) else {}
    runtime_policy = build_full_integrated_renderer_runtime_packaging_policy()
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
        detected_dependencies = {name: dict(capabilities.get(name, {})) for name in required_dependencies}
        if not detected_dependencies["pandoc"]["available"]:
            blockers.append("renderer_dependency_missing:pandoc")
        blockers.append("full_integrated_docx_renderer_not_enabled_in_b23_4")
    elif canonical == "pdf":
        renderer_id = "pandoc_pdf"
        pandoc = dict(capabilities.get("pandoc", {}))
        latex = dict(capabilities.get("xelatex", {}))
        wkhtmltopdf = dict(capabilities.get("wkhtmltopdf", {}))
        required_dependencies = ["pandoc", "xelatex"]
        detected_dependencies = {"pandoc": pandoc, "xelatex": latex, "wkhtmltopdf": wkhtmltopdf}
        if not pandoc["available"]:
            blockers.append("renderer_dependency_missing:pandoc")
        if not latex["available"]:
            blockers.append("renderer_dependency_missing:xelatex")
        if wkhtmltopdf.get("available"):
            warnings.append("wkhtmltopdf_detected_but_not_selected_for_formal_full_integrated_pdf")
        blockers.append("full_integrated_pdf_renderer_not_enabled_in_b23_4")
    dependency_checks_passed = all(item.get("available") for item in detected_dependencies.values()) if canonical == "docx" else (
        bool(detected_dependencies.get("pandoc", {}).get("available"))
        and bool(detected_dependencies.get("xelatex", {}).get("available"))
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
        "renderer_capability_snapshot": capability_snapshot,
        "runtime_packaging_policy": runtime_policy,
        "checks": {
            "format_supported": canonical in SUPPORTED_EXPORT_FORMATS,
            "dependencies_detected": dependency_checks_passed,
            "implementation_enabled": implementation_enabled,
            "detect_first_no_install_action": True,
            "external_renderers_bundled": False,
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
        "all_required_section_ids_requested": set(section_ids) == set(REQUIRED_SECTION_IDS),
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
    if not checks["all_required_section_ids_requested"]:
        blockers.append("full_integrated_required_sections_not_complete")
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
    prerequisite_rows = _full_integrated_prerequisite_rows(section_rows, section_ids=section_ids)
    prerequisite_summary = _full_integrated_prerequisite_summary(prerequisite_rows)
    checks["full_integrated_content_prerequisites_passed"] = prerequisite_summary["blocked_count"] == 0
    checks["survival_clinical_report_ready_available"] = _survival_clinical_prerequisites_available(prerequisite_rows, section_ids)
    if not allow_missing_optional_sections:
        for check_name, passed in checks.items():
            if not passed:
                blockers.append(check_name)
    blockers.extend(row_blocker for row in prerequisite_rows for row_blocker in row.get("blockers", []) or [])
    export_activation_blocker = ""
    if prerequisite_summary["blocked_count"] != 0:
        export_activation_blocker = "full_integrated_report_export_waiting_for_section_prerequisites"
        blockers.append(export_activation_blocker)
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
        "survival_clinical_section_package_policy": "KM/Cox section-only packages may satisfy section prerequisites only after package integrity validation passes; they do not enable full integrated export by themselves.",
        "export_activation_status": "eligible_for_markdown_export" if status == "eligible_for_full_integrated_report" else "blocked_until_full_integrated_section_prerequisites_pass",
        "export_activation_blocker": export_activation_blocker,
        "enabled_export_formats": ["markdown"] if status == "eligible_for_full_integrated_report" else [],
        "disabled_export_formats": ["pdf", "docx"],
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
    package_validation = _survival_clinical_section_package_validation(root, entry, section_id)
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
        "section_package_validation": package_validation,
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
    if section_id == "survival_km_logrank":
        return evaluate_km_logrank_report_ready_gate(root, result_id=result_id)
    if section_id == "cox":
        return evaluate_cox_report_ready_gate(root, result_id=result_id)
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
        "survival_km_logrank": "eligible_for_km_logrank_report_ready",
        "cox": "eligible_for_cox_report_ready",
    }
    return "passed" if gate.get("status") == passing.get(section_id) else "blocked"


def _full_integrated_prerequisite_rows(section_rows: list[dict[str, Any]], *, section_ids: tuple[str, ...] = REQUIRED_SECTION_IDS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_id in section_ids:
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
            package_validation = section.get("section_package_validation") if isinstance(section.get("section_package_validation"), dict) else {}
            if package_validation.get("status") != "passed":
                blockers.append(f"full_integrated_prerequisite_survival_clinical_section_package_not_passed:{section_id}")
                blockers.extend(str(item) for item in package_validation.get("blockers", []) or [])
        if _has_section_only_report_scope(section) and not _section_only_package_satisfies_prerequisite(section_id, section):
            blockers.append(f"full_integrated_prerequisite_forbids_section_package_as_full_report:{section_id}")
        row_status = "passed" if not blockers else "blocked"
        section_package_validation = section.get("section_package_validation") if isinstance(section.get("section_package_validation"), dict) else {}
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
                "section_package_validation_status": str(section_package_validation.get("status") or "not_required"),
                "registered_report_scopes": list(section.get("registered_report_scopes", []) or []),
                "full_integrated_scope_required": True,
                "section_only_package_sufficient": _section_only_package_satisfies_prerequisite(section_id, section),
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
        "section_only_package_sufficient": all(
            row.get("section_only_package_sufficient")
            for row in rows
            if row.get("section_id") in SURVIVAL_CLINICAL_SECTION_SCOPES
        ),
    }


def _survival_clinical_prerequisites_available(rows: list[dict[str, Any]], section_ids: tuple[str, ...]) -> bool:
    required = [section_id for section_id in section_ids if section_id in SURVIVAL_CLINICAL_SECTION_SCOPES]
    if not required:
        return True
    by_section = {str(row.get("section_id") or ""): row for row in rows}
    return all(by_section.get(section_id, {}).get("section_only_package_sufficient") is True for section_id in required)


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


def _section_only_package_satisfies_prerequisite(section_id: str, section: dict[str, Any]) -> bool:
    if section_id not in SURVIVAL_CLINICAL_SECTION_SCOPES:
        return False
    validation = section.get("section_package_validation") if isinstance(section.get("section_package_validation"), dict) else {}
    return validation.get("status") == "passed"


def _survival_clinical_section_package_validation(root: Path, entry: dict[str, Any], section_id: str) -> dict[str, Any]:
    expected_scope = SURVIVAL_CLINICAL_SECTION_SCOPES.get(section_id)
    if not expected_scope:
        return {"status": "not_required", "blockers": [], "warnings": []}
    blockers: list[str] = []
    warnings: list[str] = []
    result_id = str(entry.get("result_id") or "")
    artifacts = [artifact for artifact in entry.get("report_artifacts", []) or [] if isinstance(artifact, dict)]
    matching = [artifact for artifact in artifacts if str(artifact.get("section_scope") or "") == expected_scope]
    if not matching:
        blockers.append(f"section_package_artifact_missing:{section_id}:{expected_scope}")
        return _section_package_validation_payload(section_id, expected_scope, "", "", blockers, warnings, {})
    artifact = matching[-1]
    manifest_path = _artifact_path(root, artifact)
    if not manifest_path.is_file():
        blockers.append(f"section_package_manifest_missing:{section_id}:{expected_scope}")
        return _section_package_validation_payload(section_id, expected_scope, str(manifest_path), "", blockers, warnings, {})
    manifest = _read_json(manifest_path)
    package_dir = Path(str(manifest.get("package_path") or manifest_path.parent)).expanduser()
    if not package_dir.is_absolute():
        package_dir = root / package_dir
    if not package_dir.is_dir():
        blockers.append(f"section_package_directory_missing:{section_id}")
    expected_status = f"{expected_scope}_report_ready_package_created"
    if manifest.get("status") != expected_status:
        blockers.append(f"section_package_status_invalid:{section_id}:{manifest.get('status') or 'missing'}")
    if manifest.get("section_scope") != expected_scope:
        blockers.append(f"section_package_scope_mismatch:{section_id}:{manifest.get('section_scope') or 'missing'}")
    if result_id not in [str(item) for item in manifest.get("included_result_ids", []) or []]:
        blockers.append(f"section_package_source_result_mismatch:{section_id}:{result_id}")
    if manifest.get("clinical_conclusion_enabled") is not False:
        blockers.append(f"section_package_clinical_conclusion_flag_not_false:{section_id}")
    if manifest.get("full_integrated_report_enabled") is not False:
        blockers.append(f"section_package_full_integrated_flag_not_false:{section_id}")
    required_files = [SURVIVAL_CLINICAL_SECTION_PACKAGE_FILES[section_id], *SECTION_PACKAGE_REQUIRED_FILES]
    missing_files = [relative for relative in required_files if not (package_dir / relative).is_file()]
    blockers.extend(f"section_package_required_file_missing:{section_id}:{relative}" for relative in missing_files)
    for dirname in ("tables", "plots", "manifests", "logs", "provenance"):
        if not (package_dir / dirname).is_dir():
            blockers.append(f"section_package_required_directory_missing:{section_id}:{dirname}")
    excluded = set(str(item) for item in manifest.get("excluded_result_semantics", []) or [])
    forbidden = {"imported_external_result", "testing_level", "exploratory", "preflight_only"}
    if not forbidden.issubset(excluded):
        blockers.append(f"section_package_forbidden_semantics_policy_incomplete:{section_id}")
    return _section_package_validation_payload(section_id, expected_scope, str(manifest_path), str(package_dir), blockers, warnings, manifest)


def _section_package_validation_payload(section_id: str, expected_scope: str, manifest_path: str, package_path: str, blockers: list[str], warnings: list[str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.full_integrated_survival_clinical_section_package_prerequisite_gate.v1",
        "section_id": section_id,
        "expected_section_scope": expected_scope,
        "status": "passed" if not blockers else "blocked",
        "manifest_path": manifest_path,
        "package_path": package_path,
        "manifest_status": str(manifest.get("status") or ""),
        "section_only_package_sufficient": not blockers,
        "full_integrated_export_enabled": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


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


def _rendered_exports_manifest(package_dir: Path) -> dict[str, Any]:
    path = package_dir / "manifests" / "rendered_exports.json"
    existing = _read_json(path)
    if existing:
        existing.setdefault("exports", [])
        existing.setdefault("attempts", [])
        return existing
    return {
        "schema_version": FULL_INTEGRATED_RENDERED_EXPORTS_SCHEMA_VERSION,
        "package_scope": "full_integrated_report",
        "source_package_id": _source_package_id(package_dir),
        "source_package_path": str(package_dir),
        "exports": [],
        "attempts": [],
        "created_at": _now(),
        "updated_at": _now(),
        "policy": {
            "rendered_exports_are_package_artifacts_not_analysis_results": True,
            "do_not_write_formal_computed_result": True,
            "docx_conversion_enabled": False,
            "pdf_conversion_enabled": False,
        },
    }


def _docx_conversion_log_payload(
    package_dir: Path,
    *,
    preflight_gate: dict[str, Any],
    output_path: Path,
    conversion_log_path: Path,
    status: str,
    failure_reason: str,
) -> dict[str, Any]:
    renderer_gate = preflight_gate.get("renderer_gate") if isinstance(preflight_gate.get("renderer_gate"), dict) else {}
    pandoc = renderer_gate.get("detected_dependencies", {}).get("pandoc", {}) if isinstance(renderer_gate.get("detected_dependencies"), dict) else {}
    return {
        "schema_version": FULL_INTEGRATED_DOCX_CONVERSION_LOG_SCHEMA_VERSION,
        "created_at": _now(),
        "source_package_path": str(package_dir),
        "source_markdown_path": str(package_dir / "integrated_report.md"),
        "requested_export_format": "docx",
        "renderer_id": "pandoc_docx",
        "renderer_command": str(pandoc.get("path") or "pandoc"),
        "renderer_version": str(pandoc.get("version") or ""),
        "environment": str(preflight_gate.get("renderer_gate", {}).get("renderer_capability_snapshot", {}).get("environment") or ""),
        "working_directory": str(package_dir),
        "output_path": str(output_path),
        "exit_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "duration_ms": 0,
        "status": status,
        "failure_reason": failure_reason,
        "preflight_status": str(preflight_gate.get("preflight_status") or ""),
        "preflight_blockers": list(preflight_gate.get("blockers", []) or []),
        "conversion_invoked": False,
        "temporary_output_removed": True,
        "markdown_package_preserved": True,
    }


def _reserved_export_path(package_dir: Path, stem: str, suffix: str, *, stamp: str) -> Path:
    exports_dir = package_dir / "exports"
    candidate = exports_dir / f"{stem}_{stamp}.{suffix}"
    counter = 1
    while candidate.exists():
        candidate = exports_dir / f"{stem}_{stamp}_{counter}.{suffix}"
        counter += 1
    return candidate


def _reserved_log_path(package_dir: Path, stem: str, *, stamp: str) -> Path:
    candidate = package_dir / "logs" / f"{stem}_{stamp}.log"
    counter = 1
    while candidate.exists():
        candidate = package_dir / "logs" / f"{stem}_{stamp}_{counter}.log"
        counter += 1
    return candidate


def _source_package_id(package_dir: Path) -> str:
    manifest = _read_json(package_dir / "integrated_report_package_manifest.json")
    return str(manifest.get("created_at") or package_dir.name)


def _renderer_version_from_gate(preflight_gate: dict[str, Any]) -> str:
    renderer_gate = preflight_gate.get("renderer_gate") if isinstance(preflight_gate.get("renderer_gate"), dict) else {}
    dependencies = renderer_gate.get("detected_dependencies") if isinstance(renderer_gate.get("detected_dependencies"), dict) else {}
    pandoc = dependencies.get("pandoc") if isinstance(dependencies.get("pandoc"), dict) else {}
    return str(pandoc.get("version") or "")


def _update_package_manifest_rendered_exports(package_dir: Path, rendered_exports: dict[str, Any]) -> None:
    manifest_path = package_dir / "integrated_report_package_manifest.json"
    manifest = _read_json(manifest_path)
    if not manifest:
        return
    manifest["rendered_exports_manifest"] = "manifests/rendered_exports.json"
    manifest["rendered_exports_summary"] = {
        "exports_count": len(rendered_exports.get("exports", []) or []),
        "attempts_count": len(rendered_exports.get("attempts", []) or []),
        "latest_attempt_status": rendered_exports.get("latest_attempt_status", ""),
        "docx_conversion_enabled": False,
        "pdf_conversion_enabled": False,
    }
    manifest["package_inventory"] = _package_inventory(package_dir)
    _write_json(manifest_path, manifest)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


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


def _renderer_preflight_policy(export_format: str) -> dict[str, Any]:
    canonical = _canonical_export_format(export_format)
    if canonical == "docx":
        return {
            "schema_version": "biomedpilot.full_integrated_docx_preflight_policy.v1",
            "source_package_required": "full_integrated markdown package",
            "required_renderer": "pandoc_docx",
            "activation_status": "disabled_until_docx_renderer_activation_stage",
            "runtime_packaging_policy_id": build_full_integrated_renderer_runtime_packaging_policy()["policy_id"],
            "runtime_provider": "user_system_pandoc_on_search_path",
            "planned_output": "exports/integrated_report.docx",
            "conversion_log": "logs/docx_renderer_preflight.log",
            "checks": [
                "source package manifest",
                "non-empty integrated_report.md",
                "local markdown references resolve",
                "pandoc detected",
                "no forbidden clinical conclusion wording",
                "rendered artifact manifest registration planned",
            ],
        }
    if canonical == "pdf":
        return {
            "schema_version": "biomedpilot.full_integrated_pdf_preflight_policy.v1",
            "source_package_required": "full_integrated markdown package",
            "required_renderer": "pandoc_pdf",
            "activation_status": "disabled_until_pdf_renderer_activation_stage",
            "runtime_packaging_policy_id": build_full_integrated_renderer_runtime_packaging_policy()["policy_id"],
            "runtime_provider": "disabled_detect_only_pandoc_xelatex_future_backend",
            "planned_output": "exports/integrated_report.pdf",
            "conversion_log": "logs/pdf_renderer_preflight.log",
            "checks": ["pandoc detected", "xelatex detected", "wkhtmltopdf detect-only not selected", "assets/fonts resolve", "rendered artifact manifest registration planned"],
        }
    return {
        "schema_version": "biomedpilot.full_integrated_markdown_renderer_policy.v1",
        "source_package_required": "full integrated report gate",
        "required_renderer": "builtin_markdown",
        "activation_status": "enabled_when_full_integrated_gate_passes",
    }


def _markdown_local_references(markdown: str) -> list[str]:
    references: list[str] = []
    for pattern in (r"!\[[^\]]*\]\(([^)]+)\)", r"<img\s+[^>]*src=[\"']([^\"']+)[\"']"):
        for match in re.finditer(pattern, markdown, flags=re.IGNORECASE):
            target = match.group(1).strip()
            if not target or target.startswith(("#", "http://", "https://", "data:", "mailto:")):
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1].strip()
            references.append(target.split("#", 1)[0])
    return list(dict.fromkeys(references))


def _forbidden_clinical_conclusion_terms(markdown: str) -> list[str]:
    lowered = markdown.lower()
    forbidden_patterns = {
        "clinical_diagnosis_statement": r"\bclinical diagnosis\s*:",
        "prognosis_statement": r"\bprognosis\s*:",
        "treatment_recommendation_statement": r"\btreatment recommendation\s*:",
        "recommended_treatment_statement": r"\brecommended treatment\s*:",
        "risk_score_statement": r"\brisk score\s*:",
        "nomogram_statement": r"\bnomogram\s*:",
    }
    return [name for name, pattern in forbidden_patterns.items() if re.search(pattern, lowered)]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
