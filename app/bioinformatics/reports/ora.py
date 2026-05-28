from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment.gene_set_gate import build_ora_gene_set_resource_gate
from app.bioinformatics.enrichment.models import REQUIRED_ORA_TABLE_COLUMNS
from app.bioinformatics.enrichment.result_schema import validate_ora_result_index_entry, validate_ora_result_table_row
from app.bioinformatics.plots.schema import validate_plot_artifact
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry


ORA_REPORT_READY_SCHEMA_VERSION = "biomedpilot.ora_report_ready_gate.v1"
ORA_REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.ora_report_ready_package.v1"
ORA_REPORT_GUARD_COPY = (
    "ORA identifies over-represented gene sets among selected DEG genes. "
    "It does not prove pathway activation or inhibition. "
    "It is not GSEA. It is not survival analysis. "
    "It is not clinical interpretation or treatment recommendation."
)


def evaluate_ora_report_ready_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
    allow_imported_derived_report: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_ora_entry(entries, result_id)
    blockers: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {
        "ora_result_present": selected is not None,
        "result_index_v2_complete": False,
        "result_semantics_allowed": False,
        "task_type_ora_enrichment": False,
        "source_deg_result_present": False,
        "source_deg_semantics_allowed": False,
        "ora_result_table_validation_passed": False,
        "parameter_manifest_present": False,
        "gene_set_resource_manifest_passed": False,
        "dependency_snapshot_passed": False,
        "task_run_log_present": False,
        "warnings_limitations_provenance_included": True,
        "plot_artifact_or_table_only_mode": False,
        "no_blockers": False,
        "no_gsea_survival_or_clinical_conclusion": True,
    }
    source_deg = None
    gene_set_manifest: dict[str, Any] = {}
    table_validation: dict[str, Any] = {}
    plot_validation: dict[str, Any] = {}
    if selected is None:
        blockers.append("ora_result_not_found")
    else:
        semantics = _semantics(selected)
        source_semantics = str(selected.get("source_result_semantics") or "")
        checks["result_semantics_allowed"] = semantics in {"formal_computed_result", "imported_external_result"}
        if not checks["result_semantics_allowed"]:
            blockers.append(f"ora_report_source_semantics_not_allowed:{semantics or 'unknown'}")
        if semantics == "formal_computed_result" and source_semantics != "formal_computed_result":
            blockers.append("formal_ora_report_requires_formal_source_deg_semantics")
        if semantics == "imported_external_result":
            if not allow_imported_derived_report:
                blockers.append("imported_derived_ora_report_mode_not_allowed")
            if source_semantics != "imported_external_result":
                blockers.append("imported_derived_ora_report_requires_imported_source_deg_semantics")
            warnings.append("imported_derived_ora_report_not_biomedpilot_formal_recomputed_ora")
        checks["task_type_ora_enrichment"] = str(selected.get("task_type") or "") == "ora_enrichment"
        if not checks["task_type_ora_enrichment"]:
            blockers.append("ora_report_requires_ora_enrichment_task_type")
        if selected.get("validation_status") in {"blocked", "failed"}:
            blockers.append("ora_report_source_validation_status_blocked")
        if selected.get("blockers"):
            blockers.append("ora_report_source_result_has_blockers")
        schema_entry = dict(selected)
        schema_entry["report_ready_eligible"] = False
        schema_validation = validate_ora_result_index_entry(schema_entry)
        checks["result_index_v2_complete"] = schema_validation.get("status") == "passed"
        blockers.extend(f"result_index:{item}" for item in schema_validation.get("blockers", []) or [])
        warnings.extend(
            str(item)
            for item in schema_validation.get("warnings", []) or []
            if str(item) not in {"ora_plot_artifacts_not_activated_in_b10_1", "ora_report_artifacts_not_activated_in_b10_1"}
        )
        source_deg = _source_deg_entry(entries, selected)
        checks["source_deg_result_present"] = source_deg is not None and bool(selected.get("source_deg_result_id"))
        if not checks["source_deg_result_present"]:
            blockers.append("ora_report_source_deg_result_missing")
        source_deg_semantics = _semantics(source_deg or {})
        expected = "formal_computed_result" if semantics == "formal_computed_result" else "imported_external_result"
        checks["source_deg_semantics_allowed"] = source_deg_semantics == expected
        if source_deg is not None and not checks["source_deg_semantics_allowed"]:
            blockers.append(f"ora_report_source_deg_semantics_mismatch:{source_deg_semantics}!={expected}")
        checks["parameter_manifest_present"] = bool(selected.get("parameters_manifest"))
        if not checks["parameter_manifest_present"]:
            blockers.append("ora_report_missing_parameter_manifest")
        dependency = selected.get("dependency_snapshot") if isinstance(selected.get("dependency_snapshot"), dict) else {}
        checks["dependency_snapshot_passed"] = dependency.get("status") == "passed"
        if not checks["dependency_snapshot_passed"]:
            blockers.append("ora_report_dependency_snapshot_not_passed")
        table_validation = _validate_ora_table(root, selected)
        checks["ora_result_table_validation_passed"] = table_validation.get("status") == "passed"
        blockers.extend(f"ora_table:{item}" for item in table_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in table_validation.get("warnings", []) or [])
        gene_set_manifest = build_ora_gene_set_resource_gate(root, resource_id=str(selected.get("gene_set_resource_id") or ""))
        checks["gene_set_resource_manifest_passed"] = gene_set_manifest.get("status") == "passed" or gene_set_manifest.get("validation_status") == "passed"
        if not checks["gene_set_resource_manifest_passed"]:
            blockers.extend(f"gene_set:{item}" for item in gene_set_manifest.get("blockers", []) or ["ora_gene_set_resource_manifest_missing"])
        checks["task_run_log_present"] = _task_run_log_path(root, selected).is_file()
        if not checks["task_run_log_present"]:
            blockers.append("ora_report_task_run_log_missing")
        plot_validation = _validate_plot_requirement(selected, allow_table_only_report=allow_table_only_report)
        checks["plot_artifact_or_table_only_mode"] = plot_validation.get("status") == "passed"
        blockers.extend(str(item) for item in plot_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in plot_validation.get("warnings", []) or [])
        checks["no_blockers"] = not selected.get("blockers")
    for check_name, passed in checks.items():
        if not passed and check_name not in {"ora_result_present"}:
            blockers.append(check_name)
    status = "blocked"
    if not blockers and selected is not None:
        status = "eligible_for_ora_report_ready" if _semantics(selected) == "formal_computed_result" else "eligible_for_imported_derived_ora_report_package"
    return {
        "schema_version": ORA_REPORT_READY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": status,
        "selected_result_id": str((selected or {}).get("result_id") or result_id or ""),
        "source_deg_result_id": str((selected or {}).get("source_deg_result_id") or ""),
        "source_deg_result_semantics": _semantics(source_deg or {}),
        "result_index_path": str(root / RESULT_INDEX),
        "dependency_versions": _dependency_versions((selected or {}).get("dependency_snapshot") if isinstance((selected or {}).get("dependency_snapshot"), dict) else {}),
        "allow_table_only_report": allow_table_only_report,
        "allow_imported_derived_report": allow_imported_derived_report,
        "table_only_report_mode_statement": _table_only_statement() if allow_table_only_report else "",
        "guard_copy": ORA_REPORT_GUARD_COPY,
        "checks": checks,
        "table_validation": table_validation,
        "plot_validation": plot_validation,
        "gene_set_resource_manifest": gene_set_manifest,
        "package_layout": ["ora_report.md", "tables/", "plots/", "manifests/", "logs/", "README_limitations.md"],
        "limitations_required": _limitations(_semantics(selected or {}), allow_table_only_report=allow_table_only_report),
        "provenance_required": _provenance(selected or {}, source_deg or {}, root),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys([*warnings, *[str(item) for item in (selected or {}).get("warnings", []) or []]])),
    }


def create_ora_report_ready_package(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
    allow_imported_derived_report: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = evaluate_ora_report_ready_gate(
        root,
        result_id=result_id,
        allow_table_only_report=allow_table_only_report,
        allow_imported_derived_report=allow_imported_derived_report,
    )
    if gate.get("status") == "blocked":
        return {
            "schema_version": ORA_REPORT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "user_visible_package_path": "",
            "gate": gate,
            "blockers": gate.get("blockers", []),
            "warnings": gate.get("warnings", []),
        }
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = next(entry for entry in entries if str(entry.get("result_id") or "") == str(gate.get("selected_result_id") or ""))
    source_deg = _source_deg_entry(entries, selected) or {}
    package_dir = _next_package_dir(root, str(selected.get("result_id") or "ora"))
    tables_dir = package_dir / "tables"
    plots_dir = package_dir / "plots"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, plots_dir, manifests_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    table_path = _ora_table_path(root, selected)
    if table_path.is_file():
        shutil.copy2(table_path, tables_dir / "ora_result_table.tsv")
    task_log = _task_run_log_path(root, selected)
    if task_log.is_file():
        shutil.copy2(task_log, logs_dir / "task_run_log.json")
    _write_plot_artifact_files(plots_dir, selected.get("plot_artifacts", []) or [])
    _write_json(manifests_dir / "ora_result_index_snapshot.json", selected)
    _write_json(manifests_dir / "source_deg_result_snapshot.json", source_deg)
    _write_json(manifests_dir / "ora_parameters_manifest.json", selected.get("parameters_manifest", {}))
    _write_json(manifests_dir / "gene_set_resource_manifest.json", gate.get("gene_set_resource_manifest", {}))
    _write_json(manifests_dir / "dependency_snapshot.json", selected.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "plot_artifacts.json", selected.get("plot_artifacts", []) or [])
    _write_json(manifests_dir / "gate_snapshot.json", gate)
    _write_json(manifests_dir / "provenance.json", gate.get("provenance_required", {}))
    _write_json(manifests_dir / "warnings.json", {"warnings": gate.get("warnings", []), "result_warnings": selected.get("warnings", []) or []})
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(_semantics(selected), allow_table_only_report=allow_table_only_report), encoding="utf-8")
    (package_dir / "ora_report.md").write_text(_ora_report_markdown(selected, source_deg, gate), encoding="utf-8")
    inventory = _package_inventory(package_dir)
    _write_json(manifests_dir / "package_inventory.json", inventory)
    inventory = _package_inventory(package_dir)
    _write_json(manifests_dir / "package_inventory.json", inventory)
    status = "ora_report_ready_package_created" if _semantics(selected) == "formal_computed_result" else "imported_derived_ora_report_package_created"
    manifest = {
        "schema_version": ORA_REPORT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": status,
        "package_path": str(package_dir),
        "user_visible_package_path": str(package_dir),
        "overwrite_policy": "create_new_timestamped_package_directory",
        "package_inventory": inventory,
        "section_scope": "formal_ora_only" if _semantics(selected) == "formal_computed_result" else "imported_derived_ora_only",
        "included_result_ids": [str(selected.get("result_id") or "")],
        "included_source_deg_result_ids": [str(selected.get("source_deg_result_id") or "")],
        "excluded_result_semantics": ["testing_level", "exploratory", "preflight_only"],
        "gsea_enabled": False,
        "survival_enabled": False,
        "clinical_conclusion_enabled": False,
        "allow_table_only_report": allow_table_only_report,
        "guard_copy": ORA_REPORT_GUARD_COPY,
        "gate": gate,
    }
    _write_json(package_dir / "ora_report_package_manifest.json", manifest)
    artifact_type = "ora_report_ready_package" if _semantics(selected) == "formal_computed_result" else "imported_derived_ora_report_package"
    selected["report_artifacts"] = [
        *[item for item in selected.get("report_artifacts", []) or [] if isinstance(item, dict) and item.get("artifact_type") != artifact_type],
        {
            "artifact_type": artifact_type,
            "path": str((package_dir / "ora_report_package_manifest.json").relative_to(root)),
            "schema": ORA_REPORT_PACKAGE_SCHEMA_VERSION,
            "section_scope": manifest["section_scope"],
        },
    ]
    if _semantics(selected) == "formal_computed_result":
        selected["report_ready_eligible"] = True
    else:
        selected["report_ready_eligible"] = False
        selected["warnings"] = list(dict.fromkeys([*(selected.get("warnings", []) or []), "imported_derived_ora_report_not_biomedpilot_formal_recomputed_ora"]))
    selected["updated_at"] = _now()
    save_registry(root, entries)
    return manifest


def _validate_ora_table(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = _ora_table_path(root, entry)
    blockers: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {"status": "blocked", "path": str(path), "row_count": 0, "blockers": ["ora_result_table_missing"], "warnings": warnings}
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        rows = list(csv.DictReader([first, *handle.readlines()], delimiter=delimiter))
    columns = set(rows[0].keys()) if rows else set()
    for column in REQUIRED_ORA_TABLE_COLUMNS:
        if column not in columns:
            blockers.append(f"missing_column:{column}")
    for index, row in enumerate(rows, start=1):
        validation = validate_ora_result_table_row(row)
        blockers.extend(f"row_{index}:{item}" for item in validation.get("blockers", []) or [])
        if not str(row.get("term_id") or "").strip():
            blockers.append(f"row_{index}:missing_term_id")
        if not str(row.get("term_name") or "").strip():
            blockers.append(f"row_{index}:missing_term_name")
    if not rows:
        blockers.append("ora_result_table_has_no_rows")
    return {"status": "blocked" if blockers else "passed", "path": str(path), "row_count": len(rows), "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def _validate_plot_requirement(entry: dict[str, Any], *, allow_table_only_report: bool) -> dict[str, Any]:
    artifacts = [item for item in entry.get("plot_artifacts", []) or [] if isinstance(item, dict)]
    passed_plots: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    for artifact in artifacts:
        validation = validate_plot_artifact(artifact)
        if (
            validation.get("status") == "passed"
            and artifact.get("plot_artifact_scope") == "ora_plot_spec"
            and artifact.get("source_task_type") == "ora_enrichment"
            and artifact.get("source_result_id") == entry.get("result_id")
            and normalize_result_semantics(artifact.get("source_result_semantics"), default="") == _semantics(entry)
            and normalize_result_semantics(artifact.get("plot_semantics"), default="") == _semantics(entry)
            and not artifact.get("blockers")
        ):
            passed_plots.append(str(artifact.get("plot_id") or "ora_plot"))
        warnings.extend(str(item) for item in validation.get("warnings", []) or [])
    if passed_plots:
        return {"status": "passed", "plot_ids": passed_plots, "blockers": [], "warnings": list(dict.fromkeys(warnings))}
    if allow_table_only_report:
        warnings.append("ora_table_only_report_mode_no_plot_artifact")
        return {"status": "passed", "plot_ids": [], "blockers": [], "warnings": list(dict.fromkeys(warnings))}
    blockers.append("ora_report_ready_requires_ora_plot_artifact_or_table_only_mode")
    return {"status": "blocked", "plot_ids": [], "blockers": blockers, "warnings": list(dict.fromkeys(warnings))}


def _select_ora_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [
        entry
        for entry in entries
        if str(entry.get("task_type") or "") == "ora_enrichment"
        and _semantics(entry) in {"formal_computed_result", "imported_external_result"}
    ]
    return candidates[-1] if candidates else None


def _source_deg_entry(entries: list[dict[str, Any]], entry: dict[str, Any]) -> dict[str, Any] | None:
    source_id = str(entry.get("source_deg_result_id") or "")
    if not source_id:
        return None
    return next((item for item in entries if str(item.get("result_id") or "") == source_id and str(item.get("task_type") or "").lower() == "deg"), None)


def _ora_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "ora_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _task_run_log_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("log_artifacts") if isinstance(entry.get("log_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and (item.get("artifact_type") == "controlled_ora_task_run_log" or "task_run" in str(item.get("artifact_type") or ""))), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _ora_report_markdown(entry: dict[str, Any], source_deg: dict[str, Any], gate: dict[str, Any]) -> str:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    rows = _read_rows(Path(str((gate.get("table_validation") or {}).get("path") or "")))
    significant = [row for row in rows if _float(row.get("adjusted_p_value"), default=1.0) <= float(parameters.get("fdr_threshold") or 0.05)]
    top = sorted(rows, key=lambda row: (_float(row.get("adjusted_p_value"), default=1.0), _float(row.get("p_value"), default=1.0)))[:10]
    lines = [
        "# ORA / Pathway Over-Representation Analysis",
        "",
        "This report-ready package is limited to the audited ORA section.",
        "It is not a full integrated research report.",
        "",
        "## Guard Copy",
        "",
        ORA_REPORT_GUARD_COPY,
        "",
        "## Source",
        "",
        f"- ORA result id: {entry.get('result_id', '')}",
        f"- task_run_id: {entry.get('task_run_id', '')}",
        f"- source DEG result id: {entry.get('source_deg_result_id', '')}",
        f"- source DEG result semantics: {entry.get('source_result_semantics', '')}",
        f"- source DEG registry semantics: {_semantics(source_deg)}",
        f"- ORA result semantics: {_semantics(entry)}",
        "",
        "## Method",
        "",
        f"- gene set resource: {entry.get('gene_set_resource_id', '')}",
        f"- method: {parameters.get('test_method', '')}",
        f"- selected gene rule: {parameters.get('selected_gene_rule', '')}",
        f"- background universe rule: {parameters.get('background_universe_rule', '')}",
        f"- thresholds: p={parameters.get('p_value_threshold', '')}, FDR={parameters.get('fdr_threshold', '')}",
        "",
        "## Result Summary",
        "",
        f"- term count: {len(rows)}",
        f"- significant term count: {len(significant)}",
        "",
        "## Top Enriched Terms",
        "",
    ]
    if top:
        for row in top:
            lines.append(f"- {row.get('term_id', '')}: {row.get('term_name', '')}; FDR={row.get('adjusted_p_value', '')}; overlap={row.get('overlap_count', '')}/{row.get('gene_set_size', '')}")
    else:
        lines.append("- None")
    if gate.get("allow_table_only_report"):
        lines.extend(["", "## Table-Only ORA Report Mode", "", f"- {_table_only_statement()}"])
    deps = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    packages = deps.get("packages") if isinstance(deps.get("packages"), dict) else {}
    lines.extend(["", "## Dependency Versions", ""])
    for name in ("numpy", "pandas", "scipy", "statsmodels"):
        status = packages.get(name) if isinstance(packages.get(name), dict) else {}
        lines.append(f"- {name}: {status.get('version', '')}")
    warning_items = list(dict.fromkeys([*(entry.get("warnings", []) or []), *(gate.get("warnings", []) or [])]))
    lines.extend(["", "## Warnings", "", *([f"- {item}" for item in warning_items] if warning_items else ["- None"])])
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in _limitations(_semantics(entry), allow_table_only_report=bool(gate.get("allow_table_only_report")))]])
    lines.extend(["", "## Provenance", ""])
    for key, value in (gate.get("provenance_required", {}) or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def _limitations(semantics: str, *, allow_table_only_report: bool) -> list[str]:
    items = [
        "ORA is a statistical over-representation analysis result only.",
        "ORA does not prove pathway activation or inhibition.",
        "GSEA is disabled and not included.",
        "Survival, KM, Cox, log-rank, HR, and clinical association are disabled and not included.",
        "This package does not provide clinical interpretation, diagnosis, or treatment recommendation.",
        "Warnings, limitations, dependencies, parameters, gene set provenance, and task-run logs must stay attached.",
        "Testing, exploratory, preflight, and raw expression outputs are excluded.",
    ]
    if semantics == "imported_external_result":
        items.append("Imported-derived ORA remains imported-derived and is not labeled as BioMedPilot formal recomputed ORA.")
    if allow_table_only_report:
        items.append(_table_only_statement())
    return items


def _table_only_statement() -> str:
    return "No-plot ORA report: this package intentionally contains only the ORA table and manifests. This does not mean plot generation failed and must not imply that ORA barplot, ORA dotplot, GSEA plot, volcano, or heatmap figures were generated."


def _limitations_markdown(semantics: str, *, allow_table_only_report: bool) -> str:
    return "# ORA Report Limitations\n\n" + "\n".join(f"- {item}" for item in _limitations(semantics, allow_table_only_report=allow_table_only_report)) + "\n"


def _provenance(entry: dict[str, Any], source_deg: dict[str, Any], root: Path) -> dict[str, Any]:
    return {
        "ora_result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "ora_input_id": str(entry.get("ora_input_id") or entry.get("input_package_id") or ""),
        "source_deg_result_id": str(entry.get("source_deg_result_id") or ""),
        "source_deg_result_semantics": _semantics(source_deg),
        "source_result_semantics": str(entry.get("source_result_semantics") or ""),
        "gene_set_resource_id": str(entry.get("gene_set_resource_id") or ""),
        "parameters_manifest_present": bool(entry.get("parameters_manifest")),
        "dependency_snapshot_present": bool(entry.get("dependency_snapshot")),
        "result_index_path": str(root / RESULT_INDEX),
        "result_table_path": str(_ora_table_path(root, entry)) if entry else "",
        "task_run_log": str(_task_run_log_path(root, entry)) if entry else "",
        "plot_artifact_count": len(entry.get("plot_artifacts", []) or []) if entry else 0,
        "report_artifact_count": len(entry.get("report_artifacts", []) or []) if entry else 0,
    }


def _write_plot_artifact_files(target_dir: Path, artifacts: object) -> None:
    if not isinstance(artifacts, list | tuple):
        return
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        name = "ora_plot_artifact.json" if index == 0 else f"ora_plot_artifact_{index + 1}.json"
        _write_json(target_dir / name, artifact)


def _package_inventory(package_dir: Path) -> dict[str, Any]:
    files = sorted(str(path.relative_to(package_dir)) for path in package_dir.rglob("*") if path.is_file())
    return {
        "package_root": str(package_dir),
        "required_directories": {name: (package_dir / name).is_dir() for name in ("tables", "plots", "manifests", "logs")},
        "required_files": {
            "ora_report.md": (package_dir / "ora_report.md").is_file(),
            "README_limitations.md": (package_dir / "README_limitations.md").is_file(),
            "tables/ora_result_table.tsv": (package_dir / "tables" / "ora_result_table.tsv").is_file(),
            "manifests/ora_result_index_snapshot.json": (package_dir / "manifests" / "ora_result_index_snapshot.json").is_file(),
            "manifests/source_deg_result_snapshot.json": (package_dir / "manifests" / "source_deg_result_snapshot.json").is_file(),
            "manifests/ora_parameters_manifest.json": (package_dir / "manifests" / "ora_parameters_manifest.json").is_file(),
            "manifests/gene_set_resource_manifest.json": (package_dir / "manifests" / "gene_set_resource_manifest.json").is_file(),
            "manifests/dependency_snapshot.json": (package_dir / "manifests" / "dependency_snapshot.json").is_file(),
            "manifests/gate_snapshot.json": (package_dir / "manifests" / "gate_snapshot.json").is_file(),
            "manifests/package_inventory.json": (package_dir / "manifests" / "package_inventory.json").is_file(),
            "logs/task_run_log.json": (package_dir / "logs" / "task_run_log.json").is_file(),
        },
        "files": files,
    }


def _next_package_dir(root: Path, result_id: str) -> Path:
    base = root / "report_package" / "ora" / _safe_name(result_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = base / stamp
    suffix = 1
    while candidate.exists():
        suffix += 1
        candidate = base / f"{stamp}_{suffix}"
    return candidate


def _dependency_versions(snapshot: dict[str, Any]) -> dict[str, str]:
    packages = snapshot.get("packages") if isinstance(snapshot.get("packages"), dict) else {}
    return {name: str(status.get("version") or "") for name, status in packages.items() if isinstance(status, dict)}


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return list(csv.DictReader([first, *handle.readlines()], delimiter=delimiter))


def _float(value: object, *, default: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _semantics(entry: dict[str, Any]) -> str:
    return normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "ora"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
