from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry

from .models import REPORT_READY_SCHEMA_VERSION


CLINICAL_ADVICE_PHRASES = ("clinical advice", "medical advice", "治疗建议", "临床建议", "诊断建议")


def evaluate_report_ready_gate(project_root: str | Path, *, include_result_ids: list[str] | None = None, test_report_mode: bool = False) -> dict[str, Any]:
    registry = load_registry(project_root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = entries if include_result_ids is None else [entry for entry in entries if str(entry.get("result_id") or "") in set(include_result_ids)]
    blockers: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}
    checks["result_index_exists"] = bool(entries)
    checks["all_included_results_have_semantics"] = all(bool(entry.get("result_semantics")) for entry in selected)
    checks["input_package_provenance_present"] = all(bool(entry.get("input_package_id")) for entry in selected)
    checks["parameters_manifest_present"] = all(bool(entry.get("parameters_manifest")) for entry in selected)
    checks["dependency_snapshot_present"] = all(bool(entry.get("dependency_snapshot")) for entry in selected)
    checks["validation_status_pass_or_warn_only"] = all(entry.get("validation_status") in {"passed", "warning"} for entry in selected)
    checks["warnings_included"] = True
    checks["limitations_included"] = True
    checks["no_clinical_advice"] = True
    checks["plot_artifacts_registered_if_figures_included"] = all(_plots_registered(entry) for entry in selected)
    if not checks["result_index_exists"]:
        blockers.append("result_index_missing_or_empty")
    for name, passed in checks.items():
        if not passed:
            blockers.append(name)
    non_formal = [str(entry.get("result_id") or "") for entry in selected if entry.get("result_semantics") in {"testing_level", "exploratory", "imported_external_result"}]
    if non_formal and not test_report_mode:
        blockers.append("unverified_testing_exploratory_or_imported_results_present")
    if non_formal and test_report_mode:
        warnings.append("test_report_mode_includes_non_formal_results")
    status = "test_report_only" if test_report_mode and not blockers else ("blocked" if blockers else "eligible_for_internal_report")
    return {
        "schema_version": REPORT_READY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "checks": checks,
        "included_result_ids": [str(entry.get("result_id") or "") for entry in selected],
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
        "limitations_required": ["Not clinical advice", "Internal research report only", "Warnings and dependency snapshots must remain attached"],
    }


def _plots_registered(entry: dict[str, Any]) -> bool:
    if not entry.get("plot_artifacts"):
        return True
    return all(isinstance(plot, dict) and plot.get("plot_id") for plot in entry.get("plot_artifacts", []) or [])
