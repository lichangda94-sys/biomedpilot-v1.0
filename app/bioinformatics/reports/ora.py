from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry


def evaluate_ora_report_ready_gate(project_root: str | Path, *, result_id: str | None = None, allow_table_only_report: bool = False, **_kwargs: Any) -> dict[str, Any]:
    entry = _select_entry(project_root, "ora_enrichment", result_id)
    if entry is None:
        return _gate("blocked", result_id or "", ["ora_result_not_found"])
    if str(entry.get("result_semantics") or "") != "formal_computed_result":
        return _gate("blocked", str(entry.get("result_id") or ""), ["ora_report_ready_requires_formal_computed_result"])
    return _gate("eligible_for_ora_report_ready", str(entry.get("result_id") or ""), [])


def create_ora_report_ready_package(project_root: str | Path, *, result_id: str | None = None, **_kwargs: Any) -> dict[str, Any]:
    gate = evaluate_ora_report_ready_gate(project_root, result_id=result_id)
    if gate["status"] != "eligible_for_ora_report_ready":
        return {"schema_version": "biomedpilot.ora_report_ready_package.v1", "status": "blocked", "blockers": gate["blockers"]}
    return {"schema_version": "biomedpilot.ora_report_ready_package.v1", "status": "ora_report_ready_package_created", "section_scope": "ora_only", "included_result_ids": [gate["selected_result_id"]], "clinical_conclusion_enabled": False}


def _select_entry(project_root: str | Path, task_type: str, result_id: str | None) -> dict[str, Any] | None:
    entries = [entry for entry in load_registry(Path(project_root)).get("results", []) if isinstance(entry, dict)]
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    return next((entry for entry in entries if str(entry.get("task_type") or "") == task_type), None)


def _gate(status: str, result_id: str, blockers: list[str]) -> dict[str, Any]:
    return {"schema_version": "biomedpilot.ora_report_ready_gate.v1", "status": status, "selected_result_id": result_id, "blockers": blockers, "warnings": []}
