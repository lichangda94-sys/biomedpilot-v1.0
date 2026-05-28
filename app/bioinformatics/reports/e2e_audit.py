from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.bioinformatics.analysis_ui.state import build_analysis_center_state
from app.bioinformatics.deg_engine.confirmation import load_deg_parameter_confirmation
from app.bioinformatics.deg_engine.result_review import build_formal_deg_result_review
from app.bioinformatics.plots.formal_deg import build_formal_deg_plot_gate
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .formal_deg import evaluate_formal_deg_report_ready_gate


FORMAL_DEG_E2E_AUDIT_SCHEMA_VERSION = "biomedpilot.formal_deg_e2e_acceptance_audit.v1"


def audit_formal_deg_e2e_acceptance(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    package_manifest_path: str | Path | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    result = _select_result(entries, result_id)
    selected_result_id = str((result or {}).get("result_id") or result_id or "")
    confirmation = load_deg_parameter_confirmation(root)
    review = build_formal_deg_result_review(root, result_id=selected_result_id or None, sort_by="input_order", significance_filter="all")
    plot_gate = build_formal_deg_plot_gate(root, result_id=selected_result_id or None)
    report_gate = evaluate_formal_deg_report_ready_gate(root, result_id=selected_result_id or None, allow_table_only_report=allow_table_only_report)
    analysis_state = build_analysis_center_state(root)
    package_manifest = _load_package_manifest(root, selected_result_id, package_manifest_path)
    checks = _checks(root, result, confirmation, review, plot_gate, report_gate, analysis_state, package_manifest, allow_table_only_report)
    blockers = [check_id for check_id, passed in checks.items() if not passed]
    warnings = _warnings(result, confirmation, review, plot_gate, report_gate, package_manifest)
    return {
        "schema_version": FORMAL_DEG_E2E_AUDIT_SCHEMA_VERSION,
        "status": "passed" if not blockers else "blocked",
        "project_root": str(root),
        "result_id": selected_result_id,
        "result_index_path": str(root / RESULT_INDEX),
        "package_manifest_path": str(package_manifest.get("_manifest_path") or ""),
        "allow_table_only_report": allow_table_only_report,
        "checklist": checks,
        "blockers": blockers,
        "warnings": warnings,
        "step_status": _step_status(analysis_state, review, plot_gate, report_gate, package_manifest),
        "traceability": _traceability(root, result, confirmation, review, package_manifest),
        "failure_diagnostics": {
            "formal_deg_action": _action(analysis_state, "formal_deg"),
            "plot_gate_blockers": plot_gate.get("blockers", []),
            "report_gate_blockers": report_gate.get("blockers", []),
            "review_blockers": review.get("blockers", []),
        },
    }


def _checks(
    root: Path,
    result: dict[str, Any] | None,
    confirmation: dict[str, Any],
    review: dict[str, Any],
    plot_gate: dict[str, Any],
    report_gate: dict[str, Any],
    analysis_state: dict[str, Any],
    package_manifest: dict[str, Any],
    allow_table_only_report: bool,
) -> dict[str, bool]:
    package_path = Path(str(package_manifest.get("package_path") or ""))
    formal_action = _action(analysis_state, "formal_deg")
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    return {
        "user_can_understand_step_statuses": _has_status_text(analysis_state, review, plot_gate, report_gate),
        "formal_deg_button_state_clear": bool(formal_action.get("state")) and (bool(formal_action.get("disabled_reason")) if not formal_action.get("enabled") else True),
        "confirmation_traces_to_result": bool(result and output_plan.get("result_id") == result.get("result_id")),
        "confirmation_traces_to_report_package": bool(package_manifest.get("included_result_ids") and output_plan.get("result_id") in package_manifest.get("included_result_ids", [])),
        "review_matches_result_table": _review_matches_result_table(root, result, review),
        "review_matches_report_package_table": _review_matches_package_table(root, result, review, package_manifest),
        "plot_artifact_registered_and_packaged": _plot_registered_and_packaged(package_path, result, allow_table_only_report),
        "table_only_mode_not_misleading": _table_only_text_ok(package_path, package_manifest, allow_table_only_report),
        "export_path_visible_stable_no_overwrite": bool(package_manifest.get("user_visible_package_path")) and package_manifest.get("overwrite_policy") == "create_new_timestamped_package_directory" and package_path.is_dir(),
        "failure_scenarios_have_clear_errors": bool(report_gate.get("blockers") or report_gate.get("status") == "eligible_for_formal_deg_report_ready"),
        "dependency_confirmation_plot_table_blockers_work": _gate_has_required_blocker_surface(report_gate),
        "package_independently_reviewable": _package_independently_reviewable(package_path),
        "report_ready_eligible_only_after_gate_pass": bool(result and result.get("report_ready_eligible") is True and report_gate.get("status") == "eligible_for_formal_deg_report_ready"),
        "non_formal_outputs_not_upgraded": _non_formal_outputs_not_upgraded(root),
        "statistical_only_boundaries_present": _statistical_boundaries_present(package_path),
    }


def _step_status(
    analysis_state: dict[str, Any],
    review: dict[str, Any],
    plot_gate: dict[str, Any],
    report_gate: dict[str, Any],
    package_manifest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "formal_deg_action": _action(analysis_state, "formal_deg"),
        "review_status": review.get("status", "blocked"),
        "plot_gate_status": plot_gate.get("status", "blocked"),
        "report_ready_gate_status": report_gate.get("status", "blocked"),
        "package_status": package_manifest.get("status", "missing"),
    }


def _traceability(
    root: Path,
    result: dict[str, Any] | None,
    confirmation: dict[str, Any],
    review: dict[str, Any],
    package_manifest: dict[str, Any],
) -> dict[str, Any]:
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    return {
        "confirmation_path": str(root / "manifests" / "formal_deg_parameter_confirmation.json"),
        "confirmation_created_at": str(confirmation.get("created_at") or ""),
        "confirmation_result_id": str(output_plan.get("result_id") or ""),
        "result_id": str((result or {}).get("result_id") or ""),
        "task_run_id": str((result or {}).get("task_run_id") or ""),
        "review_selected_result_id": str(review.get("selected_result_id") or ""),
        "report_package_path": str(package_manifest.get("package_path") or ""),
        "report_included_result_ids": list(package_manifest.get("included_result_ids", []) or []),
    }


def _select_result(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [
        entry
        for entry in entries
        if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result"
        and str(entry.get("task_type") or "").lower() == "deg"
    ]
    return candidates[-1] if candidates else None


def _load_package_manifest(root: Path, result_id: str, manifest_path: str | Path | None) -> dict[str, Any]:
    if manifest_path:
        path = Path(manifest_path).expanduser()
        path = path if path.is_absolute() else root / path
        return _read_json_with_path(path)
    base = root / "report_package" / "formal_deg" / _safe_name(result_id)
    manifests = sorted(base.glob("*/formal_deg_report_package_manifest.json"))
    return _read_json_with_path(manifests[-1]) if manifests else {}


def _review_matches_result_table(root: Path, result: dict[str, Any] | None, review: dict[str, Any]) -> bool:
    rows = _read_table_rows(_result_table_path(root, result))
    return review.get("status") == "passed" and len(review.get("rows", []) or []) == len(rows)


def _review_matches_package_table(root: Path, result: dict[str, Any] | None, review: dict[str, Any], package_manifest: dict[str, Any]) -> bool:
    package_root = Path(str(package_manifest.get("package_path") or ""))
    if not package_root.is_dir():
        return False
    result_table = _result_table_path(root, result)
    packaged_table = package_root / "tables" / result_table.name
    return packaged_table.is_file() and len(_read_table_rows(packaged_table)) == len(review.get("rows", []) or [])


def _plot_registered_and_packaged(package_path: Path, result: dict[str, Any] | None, allow_table_only_report: bool) -> bool:
    if allow_table_only_report:
        return True
    plots = [item for item in (result or {}).get("plot_artifacts", []) or [] if isinstance(item, dict) and item.get("plot_artifact_scope") == "formal_deg_plot"]
    if not plots:
        return False
    return all((package_path / "plots" / f"{_safe_name(str(plot.get('plot_id') or 'plot'))}.plot_artifact.json").is_file() for plot in plots)


def _table_only_text_ok(package_path: Path, package_manifest: dict[str, Any], allow_table_only_report: bool) -> bool:
    if not allow_table_only_report:
        return True
    text = _read_text(package_path / "formal_deg_report.md")
    return (
        package_manifest.get("allow_table_only_report") is True
        and "Table-Only Report Mode" in text
        and "does not mean plot generation failed" in text
        and "must not imply that volcano or heatmap figures were generated" in text
    )


def _package_independently_reviewable(package_path: Path) -> bool:
    required = (
        "formal_deg_report.md",
        "README_limitations.md",
        "manifests/result_index_snapshot.json",
        "manifests/formal_deg_parameter_confirmation.json",
        "manifests/dependency_snapshot.json",
        "manifests/plot_artifacts.json",
        "manifests/gate_snapshot.json",
        "manifests/package_inventory.json",
        "manifests/provenance.json",
        "manifests/warnings.json",
    )
    return package_path.is_dir() and all((package_path / item).is_file() for item in required) and (package_path / "tables").is_dir() and (package_path / "logs").is_dir()


def _gate_has_required_blocker_surface(report_gate: dict[str, Any]) -> bool:
    blocker_items = list(report_gate.get("blockers", []) or [])
    warning_items = list(report_gate.get("warnings", []) or [])
    text = " ".join(str(item) for item in [*blocker_items, *warning_items])
    return report_gate.get("status") == "eligible_for_formal_deg_report_ready" or any(
        token in text
        for token in (
            "formal_deg_parameter_confirmation_expired",
            "formal_deg_dependency_snapshot_not_passed",
            "formal_deg_report_ready_requires_formal_plot_artifact_or_table_only_mode",
            "deg_table:",
        )
    )


def _non_formal_outputs_not_upgraded(root: Path) -> bool:
    entries = [entry for entry in load_registry(root).get("results", []) if isinstance(entry, dict)]
    for entry in entries:
        semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
        if semantics in {"imported_external_result", "testing_level", "exploratory", "preflight_only"}:
            if entry.get("report_ready_eligible") or any(isinstance(item, dict) and item.get("artifact_type") == "formal_deg_report_ready_package" for item in entry.get("report_artifacts", []) or []):
                return False
    return True


def _statistical_boundaries_present(package_path: Path) -> bool:
    text = "\n".join([_read_text(package_path / "formal_deg_report.md"), _read_text(package_path / "README_limitations.md")])
    return all(
        phrase in text
        for phrase in (
            "statistical results only",
            "not a clinical conclusion",
            "treatment recommendation",
            "GSEA is disabled",
            "Survival",
        )
    )


def _has_status_text(analysis_state: dict[str, Any], review: dict[str, Any], plot_gate: dict[str, Any], report_gate: dict[str, Any]) -> bool:
    return bool(analysis_state.get("action_rows") and review.get("status") and plot_gate.get("status") and report_gate.get("status"))


def _warnings(
    result: dict[str, Any] | None,
    confirmation: dict[str, Any],
    review: dict[str, Any],
    plot_gate: dict[str, Any],
    report_gate: dict[str, Any],
    package_manifest: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not result:
        warnings.append("formal_deg_result_missing")
    if not confirmation:
        warnings.append("formal_deg_confirmation_missing")
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


def _result_table_path(root: Path, result: dict[str, Any] | None) -> Path:
    artifacts = (result or {}).get("output_artifacts") if isinstance((result or {}).get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _read_table_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return list(csv.DictReader([first, *handle.readlines()], delimiter=delimiter))


def _read_json_with_path(path: Path) -> dict[str, Any]:
    payload = {}
    if path.is_file():
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            parsed = {}
        payload = parsed if isinstance(parsed, dict) else {}
    payload["_manifest_path"] = str(path) if path else ""
    return payload


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "formal_deg"
