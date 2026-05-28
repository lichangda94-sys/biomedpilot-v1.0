from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment_backend import build_enrichment_backend_gate
from app.bioinformatics.enrichment_plot_report import build_enrichment_plot_gate, evaluate_enrichment_section_report_ready_gate
from app.bioinformatics.enrichment_result_review import build_enrichment_result_review
from app.bioinformatics.enrichment_resources import build_enrichment_resource_registry
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import load_registry


ENRICHMENT_E2E_AUDIT_SCHEMA_VERSION = "biomedpilot.enrichment_e2e_acceptance_audit.v1"


def audit_enrichment_layer_acceptance(project_root: str | Path, *, result_id: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_formal_enrichment(entries, result_id)
    selected_id = str((selected or {}).get("result_id") or result_id or "")
    review = build_enrichment_result_review(root, result_id=selected_id or None)
    plot_type = "gsea_preranked_plot" if (selected or {}).get("task_type") == "gsea_preranked" else "ora_dotplot"
    plot_gate = build_enrichment_plot_gate(root, result_id=selected_id or None, plot_type=plot_type)
    report_gate = evaluate_enrichment_section_report_ready_gate(root, result_id=selected_id or None, allow_table_only_report=True)
    backend_gate = build_enrichment_backend_gate(root, analysis_type="ora")
    resource_registry = build_enrichment_resource_registry(root)
    checks = {
        "resource_registry_available": resource_registry.get("schema_version") == "biomedpilot.enrichment_resource_registry.v1",
        "backend_gate_detect_first": backend_gate.get("install_action") == "none_detect_first_only",
        "formal_enrichment_result_selected": selected is not None,
        "review_excludes_non_formal": _review_excludes_non_formal(review),
        "plot_gate_blocks_or_passes_with_clear_reason": plot_gate.get("status") in {"passed", "blocked"} and bool(plot_gate.get("blockers") or plot_gate.get("status") == "passed"),
        "section_report_gate_is_section_only": report_gate.get("section_scope") == "formal_enrichment_only" and report_gate.get("full_integrated_report_enabled") is False,
        "non_formal_outputs_not_promoted": _non_formal_outputs_not_promoted(entries),
        "no_clinical_interpretation": report_gate.get("clinical_interpretation_enabled") is False and "clinical" in str(report_gate.get("guard_copy") or "").lower(),
    }
    blockers: list[str] = [name for name, passed in checks.items() if not passed]
    warnings: list[str] = []
    if backend_gate.get("status") == "blocked":
        warnings.extend(str(item) for item in backend_gate.get("blockers", []) or [])
    return {
        "schema_version": ENRICHMENT_E2E_AUDIT_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "project_root": str(root),
        "selected_result_id": selected_id,
        "capability_matrix": {
            "resource_registry": resource_registry.get("schema_version", ""),
            "backend_gate_status": backend_gate.get("status", ""),
            "review_status": review.get("status", ""),
            "plot_gate_status": plot_gate.get("status", ""),
            "section_report_gate_status": report_gate.get("status", ""),
            "reactomepa_msigdbr_policy": "blocked_until_external_detector_and_resource_gates_pass",
        },
        "checks": checks,
        "review": review,
        "plot_gate": plot_gate,
        "section_report_gate": report_gate,
        "unsupported_scope": [
            "reactomepa_pathway_execution_until_package_available",
            "msigdbr_catalog_execution_until_package_available",
            "full_integrated_report_auto_upgrade",
            "clinical_interpretation",
            "survival_activation",
        ],
        "blockers": blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _select_formal_enrichment(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id and _is_formal_enrichment(entry)), None)
    candidates = [entry for entry in entries if _is_formal_enrichment(entry)]
    return candidates[-1] if candidates else None


def _is_formal_enrichment(entry: dict[str, Any]) -> bool:
    return normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result" and str(entry.get("task_type") or "") in {"ora", "gsea_preranked"}


def _review_excludes_non_formal(review: dict[str, Any]) -> bool:
    for item in review.get("excluded_results", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("result_semantics") or "") in {"imported_external_result", "testing_level", "exploratory", "preflight_only"}:
            if item.get("reason") != "not_formal_computed_enrichment_result":
                return False
    return True


def _non_formal_outputs_not_promoted(entries: list[dict[str, Any]]) -> bool:
    for entry in entries:
        semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
        if semantics in {"imported_external_result", "testing_level", "exploratory", "preflight_only"}:
            if entry.get("report_ready_eligible"):
                return False
            if any(isinstance(item, dict) and item.get("artifact_type") == "enrichment_section_report_package" for item in entry.get("report_artifacts", []) or []):
                return False
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
