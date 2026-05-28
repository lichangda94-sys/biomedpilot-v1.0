from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.bioinformatics.plots.ora import build_ora_plot_gate
from app.bioinformatics.reports.ora import evaluate_ora_report_ready_gate
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .review import build_ora_result_review


ORA_E2E_ACCEPTANCE_AUDIT_SCHEMA_VERSION = "biomedpilot.ora_e2e_acceptance_audit.v1"


def audit_ora_e2e_acceptance(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    package_manifest_path: str | Path | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    from app.bioinformatics.analysis_ui.state import build_analysis_center_state

    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    result = _select_ora_result(entries, result_id)
    selected_result_id = str((result or {}).get("result_id") or result_id or "")
    source_deg = _source_deg_entry(entries, result or {})
    review = build_ora_result_review(root, result_id=selected_result_id or None, sort_by="input_order", significance_filter="all")
    plot_gate = build_ora_plot_gate(root, result_id=selected_result_id or None)
    report_gate = evaluate_ora_report_ready_gate(root, result_id=selected_result_id or None, allow_table_only_report=allow_table_only_report)
    analysis_state = build_analysis_center_state(root)
    package_manifest = _load_package_manifest(root, selected_result_id, package_manifest_path)
    checks = _checks(root, result, source_deg, review, plot_gate, report_gate, analysis_state, package_manifest, allow_table_only_report)
    blockers = [check_id for check_id, passed in checks.items() if not passed]
    warnings = _warnings(result, review, plot_gate, report_gate, package_manifest)
    return {
        "schema_version": ORA_E2E_ACCEPTANCE_AUDIT_SCHEMA_VERSION,
        "status": "passed" if not blockers else "blocked",
        "project_root": str(root),
        "ora_result_id": selected_result_id,
        "source_deg_result_id": str((result or {}).get("source_deg_result_id") or ""),
        "gene_set_resource_id": str((result or {}).get("gene_set_resource_id") or ""),
        "result_index_path": str(root / RESULT_INDEX),
        "package_manifest_path": str(package_manifest.get("_manifest_path") or ""),
        "allow_table_only_report": allow_table_only_report,
        "checklist": checks,
        "blockers": blockers,
        "warnings": warnings,
        "step_status": {
            "ora_readiness_action": _action(analysis_state, "ora_readiness_review"),
            "ora_run_action": _action(analysis_state, "run_ora_enrichment"),
            "ora_plot_action": _action(analysis_state, "ora_plot"),
            "ora_report_action": _action(analysis_state, "ora_report_ready"),
            "ora_review_status": review.get("status", "blocked"),
            "ora_plot_gate_status": plot_gate.get("status", "blocked"),
            "ora_report_ready_gate_status": report_gate.get("status", "blocked"),
            "package_status": package_manifest.get("status", "missing"),
        },
        "traceability": {
            "source_deg_result_id": str((result or {}).get("source_deg_result_id") or ""),
            "source_deg_result_semantics": normalize_result_semantics((source_deg or {}).get("canonical_result_semantics") or (source_deg or {}).get("result_semantics"), default=""),
            "ora_result_id": selected_result_id,
            "gene_set_resource_id": str((result or {}).get("gene_set_resource_id") or ""),
            "ora_parameter_manifest_id": str(((result or {}).get("parameters_manifest") or {}).get("ora_parameter_id") if isinstance((result or {}).get("parameters_manifest"), dict) else ""),
            "dependency_snapshot_present": bool((result or {}).get("dependency_snapshot")),
            "task_run_log": _task_run_log_path(root, result or {}),
            "package_included_ids": package_manifest.get("included_result_ids", []) or [],
        },
        "failure_diagnostics": {
            "plot_gate_blockers": plot_gate.get("blockers", []),
            "report_gate_blockers": report_gate.get("blockers", []),
            "review_blockers": review.get("blockers", []),
        },
    }


def _checks(
    root: Path,
    result: dict[str, Any] | None,
    source_deg: dict[str, Any] | None,
    review: dict[str, Any],
    plot_gate: dict[str, Any],
    report_gate: dict[str, Any],
    analysis_state: dict[str, Any],
    package_manifest: dict[str, Any],
    allow_table_only_report: bool,
) -> dict[str, bool]:
    package_path = Path(str(package_manifest.get("package_path") or ""))
    return {
        "user_can_understand_step_statuses": bool(analysis_state.get("action_rows") and review.get("status") and plot_gate.get("status") and report_gate.get("status")),
        "ora_report_button_state_clear": bool(_action(analysis_state, "ora_report_ready").get("state")),
        "source_deg_traces_to_ora_result": bool(result and source_deg and result.get("source_deg_result_id") == source_deg.get("result_id")),
        "ora_review_matches_result_table": _review_matches_result_table(root, result, review),
        "packaged_ora_table_matches_result_table": _package_table_matches_result(root, result, package_manifest),
        "plot_artifact_registered_and_packaged": _plot_registered_and_packaged(package_path, result, allow_table_only_report),
        "gate_snapshot_records_blockers_warnings_provenance": _gate_snapshot_ok(package_path),
        "table_only_mode_not_misleading": _table_only_text_ok(package_path, package_manifest, allow_table_only_report),
        "export_path_visible_stable_no_overwrite": bool(package_manifest.get("user_visible_package_path")) and package_manifest.get("overwrite_policy") == "create_new_timestamped_package_directory" and package_path.is_dir(),
        "dependency_missing_invalid_table_missing_plot_blockers_visible": _gate_has_required_blocker_surface(report_gate),
        "imported_derived_source_not_mislabeled": _imported_source_not_mislabeled(result, package_manifest),
        "testing_exploratory_preflight_blocked": _non_reportable_outputs_not_upgraded(root),
        "package_independently_reviewable": _package_independently_reviewable(package_path),
        "statistical_boundaries_present": _statistical_boundaries_present(package_path),
    }


def _select_ora_result(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [
        entry
        for entry in entries
        if str(entry.get("task_type") or "") == "ora_enrichment"
        and normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") in {"formal_computed_result", "imported_external_result"}
    ]
    return candidates[-1] if candidates else None


def _source_deg_entry(entries: list[dict[str, Any]], entry: dict[str, Any]) -> dict[str, Any] | None:
    source_id = str(entry.get("source_deg_result_id") or "")
    return next((item for item in entries if str(item.get("result_id") or "") == source_id), None)


def _load_package_manifest(root: Path, result_id: str, manifest_path: str | Path | None) -> dict[str, Any]:
    if manifest_path:
        path = Path(manifest_path).expanduser()
        path = path if path.is_absolute() else root / path
        return _read_json_with_path(path)
    base = root / "report_package" / "ora" / _safe_name(result_id)
    manifests = sorted(base.glob("*/ora_report_package_manifest.json"))
    return _read_json_with_path(manifests[-1]) if manifests else {}


def _review_matches_result_table(root: Path, result: dict[str, Any] | None, review: dict[str, Any]) -> bool:
    rows = _read_table_rows(_ora_table_path(root, result))
    return review.get("status") == "passed" and len(review.get("rows", []) or []) == len(rows)


def _package_table_matches_result(root: Path, result: dict[str, Any] | None, package_manifest: dict[str, Any]) -> bool:
    package_root = Path(str(package_manifest.get("package_path") or ""))
    if not package_root.is_dir():
        return False
    result_rows = _read_table_rows(_ora_table_path(root, result))
    package_rows = _read_table_rows(package_root / "tables" / "ora_result_table.tsv")
    return bool(result_rows) and len(result_rows) == len(package_rows)


def _plot_registered_and_packaged(package_path: Path, result: dict[str, Any] | None, allow_table_only_report: bool) -> bool:
    if allow_table_only_report:
        return True
    plots = [item for item in (result or {}).get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_artifact_scope") == "ora_plot_spec"]
    return bool(plots) and (package_path / "plots" / "ora_plot_artifact.json").is_file()


def _gate_snapshot_ok(package_path: Path) -> bool:
    gate = _read_json(package_path / "manifests" / "gate_snapshot.json")
    return isinstance(gate.get("blockers"), list) and isinstance(gate.get("warnings"), list) and isinstance(gate.get("provenance_required"), dict)


def _table_only_text_ok(package_path: Path, package_manifest: dict[str, Any], allow_table_only_report: bool) -> bool:
    if not allow_table_only_report:
        return True
    text = _read_text(package_path / "ora_report.md") + "\n" + _read_text(package_path / "README_limitations.md")
    return (
        package_manifest.get("allow_table_only_report") is True
        and "No-plot ORA report" in text
        and "does not mean plot generation failed" in text
        and "must not imply that ORA barplot, ORA dotplot, GSEA plot, volcano, or heatmap figures were generated" in text
    )


def _gate_has_required_blocker_surface(report_gate: dict[str, Any]) -> bool:
    if report_gate.get("status") in {"eligible_for_ora_report_ready", "eligible_for_imported_derived_ora_report_package"}:
        return True
    text = " ".join(str(item) for item in report_gate.get("blockers", []) or [])
    return any(token in text for token in ("dependency_snapshot", "ora_table:", "gene_set:", "plot_artifact_or_table_only_mode", "task_run_log"))


def _imported_source_not_mislabeled(result: dict[str, Any] | None, package_manifest: dict[str, Any]) -> bool:
    if normalize_result_semantics((result or {}).get("canonical_result_semantics") or (result or {}).get("result_semantics"), default="") != "imported_external_result":
        return True
    return package_manifest.get("section_scope") == "imported_derived_ora_only" and package_manifest.get("status") == "imported_derived_ora_report_package_created"


def _non_reportable_outputs_not_upgraded(root: Path) -> bool:
    entries = [entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict)]
    for entry in entries:
        semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
        if semantics in {"testing_level", "exploratory", "preflight_only"} and (entry.get("report_ready_eligible") or entry.get("report_artifacts")):
            return False
        if semantics == "imported_external_result" and any(isinstance(item, dict) and item.get("artifact_type") == "ora_report_ready_package" for item in entry.get("report_artifacts", []) or []):
            return False
    return True


def _package_independently_reviewable(package_path: Path) -> bool:
    required = (
        "ora_report.md",
        "README_limitations.md",
        "tables/ora_result_table.tsv",
        "manifests/ora_result_index_snapshot.json",
        "manifests/source_deg_result_snapshot.json",
        "manifests/ora_parameters_manifest.json",
        "manifests/gene_set_resource_manifest.json",
        "manifests/dependency_snapshot.json",
        "manifests/gate_snapshot.json",
        "manifests/package_inventory.json",
        "logs/task_run_log.json",
    )
    return package_path.is_dir() and all((package_path / item).is_file() for item in required)


def _statistical_boundaries_present(package_path: Path) -> bool:
    text = _read_text(package_path / "ora_report.md") + "\n" + _read_text(package_path / "README_limitations.md")
    return all(phrase in text for phrase in ("does not prove pathway activation", "It is not GSEA", "It is not survival analysis", "not clinical interpretation", "treatment recommendation"))


def _warnings(
    result: dict[str, Any] | None,
    review: dict[str, Any],
    plot_gate: dict[str, Any],
    report_gate: dict[str, Any],
    package_manifest: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not result:
        warnings.append("ora_result_missing")
    warnings.extend(str(item) for item in review.get("warnings", []) or [])
    warnings.extend(str(item) for item in plot_gate.get("warnings", []) or [])
    warnings.extend(str(item) for item in report_gate.get("warnings", []) or [])
    package_gate = package_manifest.get("gate") if isinstance(package_manifest.get("gate"), dict) else {}
    warnings.extend(str(item) for item in package_gate.get("warnings", []) or [])
    return list(dict.fromkeys(warnings))


def _action(analysis_state: dict[str, Any], action_id: str) -> dict[str, Any]:
    for row in analysis_state.get("action_rows", []) or []:
        if isinstance(row, dict) and row.get("action_id") == action_id:
            return row
    return {}


def _ora_table_path(root: Path, result: dict[str, Any] | None) -> Path:
    artifacts = (result or {}).get("output_artifacts") if isinstance((result or {}).get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "ora_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _task_run_log_path(root: Path, result: dict[str, Any]) -> str:
    artifacts = result.get("log_artifacts") if isinstance(result.get("log_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict)), {})
    path = Path(str(artifact.get("path") or ""))
    resolved = path if path.is_absolute() else root / path
    return str(resolved)


def _read_table_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return list(csv.DictReader([first, *handle.readlines()], delimiter=delimiter))


def _read_json_with_path(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    payload["_manifest_path"] = str(path) if path else ""
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "ora"
