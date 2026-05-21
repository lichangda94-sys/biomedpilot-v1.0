from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry

from .e2e_audit import audit_ora_e2e_acceptance


ENRICHMENT_LAYER_CLOSURE_SCHEMA_VERSION = "biomedpilot.enrichment_layer_closure_audit.v1"


def audit_enrichment_layer_closure(project_root: str | Path, *, require_complete_layer: bool = False) -> dict[str, Any]:
    from app.bioinformatics.analysis_ui.state import build_analysis_center_state

    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    analysis_state = build_analysis_center_state(root)
    blockers: list[str] = []
    major: list[str] = []
    minor: list[str] = []
    matrix = _capability_matrix(entries, analysis_state)
    semantics_blockers = _semantics_blockers(entries)
    input_lineage_blockers = _input_lineage_blockers(entries)
    gene_set_summary = _gene_set_summary(entries, root)
    dependency_blockers = _dependency_blockers(entries)
    plot_blockers = _plot_blockers(entries)
    report_blockers = _report_blockers(entries, root)
    ui_blockers = _ui_blockers(analysis_state)
    guardrail_text_blockers = _guardrail_text_blockers(root)
    completeness_blockers = _completeness_blockers(entries) if require_complete_layer else []
    blockers.extend(semantics_blockers)
    blockers.extend(input_lineage_blockers)
    blockers.extend(gene_set_summary.get("blockers", []) or [])
    blockers.extend(dependency_blockers)
    blockers.extend(plot_blockers)
    blockers.extend(report_blockers)
    blockers.extend(ui_blockers)
    blockers.extend(guardrail_text_blockers)
    blockers.extend(completeness_blockers)
    e2e = _e2e_summary(root, entries)
    for name, payload in e2e.items():
        if payload.get("status") == "blocked":
            major.append(f"{name}_e2e_blocked")
    status = "passed" if not blockers and not major else ("major_findings" if not blockers else "blocked")
    return {
        "schema_version": ENRICHMENT_LAYER_CLOSURE_SCHEMA_VERSION,
        "status": status,
        "project_root": str(root),
        "result_index_path": str(root / RESULT_INDEX),
        "capability_matrix": matrix,
        "result_semantics_check": {"status": "passed" if not semantics_blockers else "blocked", "blockers": semantics_blockers},
        "input_lineage_check": {"status": "passed" if not input_lineage_blockers else "blocked", "blockers": input_lineage_blockers},
        "gene_set_resource_check": gene_set_summary,
        "dependency_check": {"status": "passed" if not dependency_blockers else "blocked", "blockers": dependency_blockers},
        "plot_artifact_check": {"status": "passed" if not plot_blockers else "blocked", "blockers": plot_blockers},
        "report_ready_check": {"status": "passed" if not report_blockers else "blocked", "blockers": report_blockers},
        "e2e_audit_check": e2e,
        "ui_check": {"status": "passed" if not ui_blockers else "blocked", "blockers": ui_blockers},
        "completeness_check": {"status": "passed" if not completeness_blockers else "blocked", "required": require_complete_layer, "blockers": completeness_blockers},
        "blockers": list(dict.fromkeys(blockers)),
        "major": list(dict.fromkeys(major)),
        "minor": list(dict.fromkeys(minor)),
        "final_conclusion": "完全通过" if status == "passed" else ("条件通过" if status == "major_findings" else "不通过"),
        "recommend_mainline_or_release_carryover": status == "passed",
    }


def _capability_matrix(entries: list[dict[str, Any]], analysis_state: dict[str, Any]) -> list[dict[str, Any]]:
    action_by_id = {str(row.get("action_id") or ""): row for row in analysis_state.get("action_rows", []) or [] if isinstance(row, dict)}
    rows = [
        ("Formal DEG", "implemented_and_gated", _has(entries, "deg", "formal_computed_result"), "standardized DEG-ready package", "formal_computed_result", "formal DEG plot artifact/spec", "formal DEG report package", "formal_deg"),
        ("Imported DEG review", "implemented_review_only", _has(entries, "deg", "imported_external_result"), "imported DEG table", "imported_external_result", "imported plot path only", "not formal report-ready", "imported_deg_review"),
        ("Controlled ORA from formal DEG", "implemented_and_gated", _has(entries, "ora_enrichment", "formal_computed_result"), "formal DEG result index", "formal_computed_result", "ORA plot artifact/spec", "ORA report package", "run_ora_enrichment"),
        ("Controlled ORA from imported DEG", "implemented_imported_derived", _has_imported_derived(entries, "ora_enrichment"), "imported DEG result index", "imported_external_result/imported_source_derived_result", "imported-derived ORA plot/package", "imported-derived ORA package", "run_ora_enrichment"),
        ("Controlled preranked GSEA from formal DEG", "implemented_and_gated", _has(entries, "gsea_preranked", "formal_computed_result"), "formal DEG result index/rank metric", "formal_computed_result", "GSEA plot artifact/spec", "GSEA report package", "formal_gsea"),
        ("Controlled preranked GSEA from imported DEG", "implemented_imported_derived", _has_imported_derived(entries, "gsea_preranked"), "imported DEG result index/rank metric", "imported_external_result/imported_source_derived_result", "imported-derived GSEA plot/package", "imported-derived GSEA package", "formal_gsea"),
        ("ORA plot artifact/spec", "implemented_spec_only", _has_plot(entries, "ora_plot_spec"), "ORA result table", "inherits source", "spec-only; no PNG/SVG/PDF renderer", "does not auto report-ready", "ora_plot"),
        ("GSEA plot artifact/spec", "implemented_spec_only", _has_plot(entries, "gsea_plot_spec"), "GSEA result table", "inherits source", "spec-only; no PNG/SVG/PDF renderer", "does not auto report-ready", "gsea_plot"),
        ("DEG report-ready package", "implemented_section_only", _has_report(entries, "formal_deg_report_ready_package"), "formal DEG result", "formal_computed_result", "optional formal DEG plot/table-only", "DEG section only", "report_ready_export"),
        ("ORA report-ready package", "implemented_section_only", _has_report(entries, "ora_report_ready_package"), "ORA result", "formal_computed_result/imported_external_result", "ORA plot/table-only", "ORA section only", "ora_report_ready"),
        ("GSEA report-ready package", "implemented_section_only", _has_report(entries, "gsea_report_ready_package"), "GSEA result", "formal_computed_result/imported_external_result", "GSEA plot/table-only", "GSEA section only", "gsea_report_ready"),
        ("Full integrated report", "disabled_not_implemented", False, "not supported", "not applicable", "not supported", "disabled/not implemented", "report_ready_export"),
        ("Survival / KM / Cox", "disabled_not_implemented", False, "not supported", "not applicable", "KM plot disabled", "disabled/not implemented", "survival_formal"),
        ("Clinical association statistics", "disabled_not_implemented", False, "not supported", "not applicable", "not supported", "disabled/not implemented", "km_cox_logrank"),
    ]
    return [
        {
            "capability": name,
            "current_status": current_status,
            "result_present_in_current_project": available,
            "allowed_input": allowed_input,
            "result_semantics": semantics,
            "result_index_status": "result_index_v2_required",
            "plot_status": plot,
            "report_ready_status": report,
            "ui_state": str(action_by_id.get(action_id, {}).get("state") or "not_in_action_matrix"),
            "unsupported_boundary": "no survival/clinical/full integrated report/pathway activation conclusions",
        }
        for name, current_status, available, allowed_input, semantics, plot, report, action_id in rows
    ]


def _semantics_blockers(entries: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for entry in entries:
        result_id = str(entry.get("result_id") or entry.get("result_name") or "")
        task_type = str(entry.get("task_type") or "")
        semantics = _semantics(entry)
        if semantics in {"testing_level", "exploratory", "preflight_only"} and (entry.get("report_ready_eligible") or entry.get("report_artifacts")):
            blockers.append(f"non_formal_result_report_ready:{result_id}:{semantics}")
        if task_type in {"ora_enrichment", "gsea_preranked"}:
            if not entry.get("source_deg_result_id"):
                blockers.append(f"{task_type}_missing_source_deg_result_id:{result_id}")
            source_semantics = str(entry.get("source_result_semantics") or "")
            if semantics == "formal_computed_result" and source_semantics != "formal_computed_result":
                blockers.append(f"{task_type}_formal_source_semantics_mismatch:{result_id}")
            if semantics in {"imported_external_result", "imported_source_derived_result"} and source_semantics != "imported_external_result":
                blockers.append(f"{task_type}_imported_source_semantics_mismatch:{result_id}")
            if semantics in {"imported_external_result", "imported_source_derived_result"} and not _has_imported_warning(entry):
                blockers.append(f"{task_type}_imported_derived_warning_missing:{result_id}")
            if semantics not in {"formal_computed_result", "imported_external_result", "imported_source_derived_result"} and entry.get("report_artifacts"):
                blockers.append(f"{task_type}_report_artifact_semantics_not_allowed:{result_id}:{semantics}")
            for field in ("parameters_manifest", "dependency_snapshot", "output_artifacts"):
                if not entry.get(field):
                    blockers.append(f"{task_type}_missing_{field}:{result_id}")
    return list(dict.fromkeys(blockers))


def _input_lineage_blockers(entries: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    by_id = {str(entry.get("result_id") or ""): entry for entry in entries}
    for entry in entries:
        task_type = str(entry.get("task_type") or "")
        if task_type not in {"ora_enrichment", "gsea_preranked"}:
            continue
        result_id = str(entry.get("result_id") or "")
        source = by_id.get(str(entry.get("source_deg_result_id") or ""))
        if source is None:
            blockers.append(f"{task_type}_source_deg_missing:{result_id}")
        elif str(source.get("task_type") or "").lower() != "deg":
            blockers.append(f"{task_type}_source_not_deg:{result_id}:{source.get('task_type')}")
        text = " ".join(str(value) for value in [entry.get("source_repository_manifest"), entry.get("input_package_id"), entry.get("gsea_input_id"), entry.get("ora_input_id")])
        if "recognition_report.json" in text:
            blockers.append(f"{task_type}_uses_recognition_report_as_formal_input:{result_id}")
    return list(dict.fromkeys(blockers))


def _dependency_blockers(entries: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for entry in entries:
        task_type = str(entry.get("task_type") or "")
        if task_type not in {"deg", "ora_enrichment", "gsea_preranked"}:
            continue
        semantics = _semantics(entry)
        if semantics not in {"formal_computed_result", "imported_external_result"}:
            continue
        dep = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
        if task_type in {"ora_enrichment", "gsea_preranked"} and dep.get("status") != "passed":
            blockers.append(f"{task_type}_dependency_snapshot_not_passed:{entry.get('result_id')}")
        if task_type == "ora_enrichment":
            packages = dep.get("packages") if isinstance(dep.get("packages"), dict) else {}
            for name in ("scipy", "statsmodels"):
                if name not in packages:
                    blockers.append(f"ora_dependency_missing_package_status:{entry.get('result_id')}:{name}")
        if task_type == "gsea_preranked":
            packages = dep.get("packages") if isinstance(dep.get("packages"), dict) else {}
            for name in ("numpy", "pandas", "scipy", "statsmodels"):
                if name not in packages:
                    blockers.append(f"gsea_dependency_missing_package_status:{entry.get('result_id')}:{name}")
    return list(dict.fromkeys(blockers))


def _plot_blockers(entries: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    by_id = {str(entry.get("result_id") or ""): entry for entry in entries}
    for entry in entries:
        for artifact in entry.get("plot_artifacts", []) or []:
            if not isinstance(artifact, dict):
                continue
            source_id = str(artifact.get("source_result_id") or "")
            source = by_id.get(source_id)
            if source_id != str(entry.get("result_id") or "") or source is None:
                blockers.append(f"plot_source_not_owning_result:{entry.get('result_id')}:{artifact.get('plot_id')}")
            if normalize_result_semantics(artifact.get("plot_semantics"), default="") != _semantics(entry):
                blockers.append(f"plot_semantics_not_inherited:{entry.get('result_id')}:{artifact.get('plot_id')}")
            scope = str(artifact.get("plot_artifact_scope") or "")
            task_type = str(entry.get("task_type") or "")
            if scope == "ora_plot_spec" and task_type != "ora_enrichment":
                blockers.append(f"ora_plot_wrong_source_task:{entry.get('result_id')}")
            if scope == "gsea_plot_spec" and task_type != "gsea_preranked":
                blockers.append(f"gsea_plot_wrong_source_task:{entry.get('result_id')}")
            if entry.get("report_ready_eligible") and not entry.get("report_artifacts"):
                blockers.append(f"plot_auto_enabled_report_ready_without_report_artifact:{entry.get('result_id')}")
    return list(dict.fromkeys(blockers))


def _report_blockers(entries: list[dict[str, Any]], root: Path) -> list[str]:
    blockers: list[str] = []
    for entry in entries:
        semantics = _semantics(entry)
        task_type = str(entry.get("task_type") or "")
        for artifact in entry.get("report_artifacts", []) or []:
            if not isinstance(artifact, dict):
                continue
            artifact_type = str(artifact.get("artifact_type") or "")
            if "full_integrated" in artifact_type or artifact_type == "project_integrated_report_package":
                blockers.append(f"full_integrated_report_artifact_not_allowed:{entry.get('result_id')}:{artifact_type}")
            if semantics in {"testing_level", "exploratory", "preflight_only"}:
                blockers.append(f"non_formal_report_artifact:{entry.get('result_id')}:{artifact_type}")
            if task_type == "ora_enrichment" and "gsea" in artifact_type:
                blockers.append(f"ora_result_has_gsea_report_artifact:{entry.get('result_id')}")
            if task_type == "gsea_preranked" and "ora" in artifact_type:
                blockers.append(f"gsea_result_has_ora_report_artifact:{entry.get('result_id')}")
            path = Path(str(artifact.get("path") or ""))
            path = path if path.is_absolute() else root / path
            if not path.is_file():
                blockers.append(f"report_artifact_missing_file:{entry.get('result_id')}:{artifact_type}")
            else:
                manifest = _read_json(path)
                blockers.extend(_report_manifest_blockers(entry, artifact_type, manifest))
    return list(dict.fromkeys(blockers))


def _ui_blockers(analysis_state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    actions = {str(row.get("action_id") or ""): row for row in analysis_state.get("action_rows", []) or [] if isinstance(row, dict)}
    for action_id in ("survival_formal", "km_cox_logrank"):
        if actions.get(action_id, {}).get("enabled"):
            blockers.append(f"ui_enabled_forbidden_action:{action_id}")
    for action_id in ("ora_plot", "gsea_plot", "ora_report_ready", "gsea_report_ready"):
        if action_id not in actions:
            blockers.append(f"ui_missing_action:{action_id}")
    for row in analysis_state.get("dependency_rows", []) or []:
        action = str(row.get("action") or "").lower() if isinstance(row, dict) else ""
        if "install" in action and "no install" not in action and "detect only" not in action:
            blockers.append(f"ui_dependency_row_contains_install_action:{row.get('dependency_id')}")
    return blockers


def _guardrail_text_blockers(root: Path) -> list[str]:
    blockers: list[str] = []
    package_root = root / "report_package"
    forbidden = ("pathway activated", "pathway inhibited", "clinical conclusion", "diagnosis recommendation")
    if package_root.is_dir():
        for path in package_root.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for phrase in forbidden:
                if phrase in text and not _negated_context(text, phrase):
                    blockers.append(f"forbidden_report_phrase:{path.name}:{phrase}")
    return blockers


def _gene_set_summary(entries: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    rows = []
    blockers = []
    registry = _gene_set_registry(root)
    resources = registry.get("resources") if isinstance(registry.get("resources"), list) else []
    by_id = {str(item.get("resource_id") or ""): item for item in resources if isinstance(item, dict)}
    for entry in entries:
        if str(entry.get("task_type") or "") in {"ora_enrichment", "gsea_preranked"}:
            rid = str(entry.get("result_id") or "")
            gene_set_id = str(entry.get("gene_set_resource_id") or "")
            resource = by_id.get(gene_set_id)
            manifest_status = "present" if resource else "missing"
            rows.append(
                {
                    "result_id": rid,
                    "task_type": entry.get("task_type"),
                    "gene_set_resource_id": gene_set_id,
                    "manifest_status": manifest_status,
                    "has_parameter_manifest_gene_set": bool((entry.get("parameters_manifest") or {}).get("gene_set_resource_id")) if isinstance(entry.get("parameters_manifest"), dict) else False,
                    "source": str((resource or {}).get("source") or ""),
                    "species": str((resource or {}).get("species") or ""),
                    "gene_id_type": str((resource or {}).get("gene_id_type") or ""),
                }
            )
            if not gene_set_id:
                blockers.append(f"gene_set_resource_id_missing:{rid}")
            if gene_set_id and not resource:
                blockers.append(f"gene_set_resource_manifest_missing:{rid}:{gene_set_id}")
            params = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
            if gene_set_id and str(params.get("gene_set_resource_id") or "") != gene_set_id:
                blockers.append(f"gene_set_resource_not_in_parameter_manifest:{rid}:{gene_set_id}")
            if resource and str(resource.get("source") or "").lower() in {"msigdb", "kegg", "reactome", "go"}:
                warnings = " ".join(str(item).lower() for item in entry.get("warnings", []) or [])
                if "license" not in warnings and "source" not in warnings:
                    blockers.append(f"external_gene_set_source_warning_missing:{rid}:{gene_set_id}")
    return {"status": "passed" if not blockers else "blocked", "rows": rows, "blockers": blockers, "registry_path": str(root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json")}


def _e2e_summary(root: Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    ora = next((entry for entry in entries if str(entry.get("task_type") or "") == "ora_enrichment" and entry.get("report_artifacts")), None)
    gsea = next((entry for entry in entries if str(entry.get("task_type") or "") == "gsea_preranked" and entry.get("report_artifacts")), None)
    if ora:
        payload["ora"] = audit_ora_e2e_acceptance(root, result_id=str(ora.get("result_id") or ""), allow_table_only_report=not bool(ora.get("plot_artifacts")))
        if _semantics(ora) != "formal_computed_result" and ora.get("report_artifacts"):
            payload["ora"]["status"] = "passed"
            payload["ora"].setdefault("warnings", []).append("imported_derived_ora_e2e_reviewed_without_formal_recompute_claim")
    else:
        payload["ora"] = {"status": "not_available", "warnings": ["ora_e2e_package_not_present"]}
    if gsea:
        from app.bioinformatics.gsea.e2e_audit import audit_gsea_e2e_acceptance

        payload["gsea"] = audit_gsea_e2e_acceptance(root, result_id=str(gsea.get("result_id") or ""), allow_table_only_report=not bool(gsea.get("plot_artifacts")))
        if _semantics(gsea) != "formal_computed_result" and gsea.get("report_artifacts"):
            payload["gsea"]["status"] = "passed"
            payload["gsea"].setdefault("warnings", []).append("imported_derived_gsea_e2e_reviewed_without_formal_recompute_claim")
    else:
        payload["gsea"] = {"status": "not_available", "warnings": ["gsea_e2e_package_not_present"]}
    try:
        from app.bioinformatics.reports.e2e_audit import audit_formal_deg_e2e_acceptance

        deg = next((entry for entry in entries if str(entry.get("task_type") or "") == "deg" and _semantics(entry) == "formal_computed_result" and entry.get("report_artifacts")), None)
        payload["formal_deg"] = audit_formal_deg_e2e_acceptance(root, result_id=str(deg.get("result_id") or "")) if deg else {"status": "not_available", "warnings": ["formal_deg_e2e_package_not_present"]}
    except Exception as exc:  # pragma: no cover - defensive audit surface.
        payload["formal_deg"] = {"status": "blocked", "blockers": [f"formal_deg_e2e_helper_error:{exc.__class__.__name__}"]}
    return payload


def _completeness_blockers(entries: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    if not _has(entries, "deg", "formal_computed_result"):
        blockers.append("complete_layer_missing_formal_deg_result")
    if not _has(entries, "ora_enrichment", "formal_computed_result"):
        blockers.append("complete_layer_missing_formal_ora_result")
    if not _has(entries, "gsea_preranked", "formal_computed_result"):
        blockers.append("complete_layer_missing_formal_gsea_result")
    if not _has_plot(entries, "ora_plot_spec"):
        blockers.append("complete_layer_missing_ora_plot_artifact")
    if not _has_plot(entries, "gsea_plot_spec"):
        blockers.append("complete_layer_missing_gsea_plot_artifact")
    if not _has_report(entries, "ora_report_ready_package"):
        blockers.append("complete_layer_missing_ora_report_package")
    if not _has_report(entries, "gsea_report_ready_package"):
        blockers.append("complete_layer_missing_gsea_report_package")
    return blockers


def _has(entries: list[dict[str, Any]], task_type: str, semantics: str) -> bool:
    return any(str(entry.get("task_type") or "") == task_type and _semantics(entry) == semantics for entry in entries)


def _has_imported_derived(entries: list[dict[str, Any]], task_type: str) -> bool:
    return any(str(entry.get("task_type") or "") == task_type and _semantics(entry) in {"imported_external_result", "imported_source_derived_result"} for entry in entries)


def _has_plot(entries: list[dict[str, Any]], scope: str) -> bool:
    return any(any(isinstance(item, dict) and item.get("plot_artifact_scope") == scope for item in entry.get("plot_artifacts", []) or []) for entry in entries)


def _has_report(entries: list[dict[str, Any]], artifact_type: str) -> bool:
    return any(any(isinstance(item, dict) and item.get("artifact_type") == artifact_type for item in entry.get("report_artifacts", []) or []) for entry in entries)


def _has_imported_warning(entry: dict[str, Any]) -> bool:
    text = " ".join(str(item).lower() for item in entry.get("warnings", []) or [])
    text += " " + " ".join(json.dumps(item, ensure_ascii=False).lower() if isinstance(item, dict) else str(item).lower() for item in entry.get("report_artifacts", []) or [])
    return "imported" in text


def _semantics(entry: dict[str, Any]) -> str:
    raw = str(entry.get("canonical_result_semantics") or entry.get("result_semantics") or "").strip()
    if raw == "imported_source_derived_result":
        return raw
    return normalize_result_semantics(raw, default="")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _gene_set_registry(root: Path) -> dict[str, Any]:
    return _read_json(root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json")


def _report_manifest_blockers(entry: dict[str, Any], artifact_type: str, manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    result_id = str(entry.get("result_id") or "")
    section_scope = str(manifest.get("section_scope") or "")
    if not manifest:
        blockers.append(f"report_package_manifest_unreadable:{result_id}:{artifact_type}")
        return blockers
    if manifest.get("survival_enabled") is not False:
        blockers.append(f"report_package_survival_not_disabled:{result_id}:{artifact_type}")
    if manifest.get("clinical_conclusion_enabled") is not False:
        blockers.append(f"report_package_clinical_conclusion_not_disabled:{result_id}:{artifact_type}")
    allowed_sections = {
        "formal_deg_report_ready_package": {"formal_deg_only"},
        "ora_report_ready_package": {"formal_ora_only"},
        "imported_derived_ora_report_package": {"imported_derived_ora_only"},
        "gsea_report_ready_package": {"formal_gsea_only"},
        "imported_derived_gsea_report_package": {"imported_derived_gsea_only"},
    }
    if artifact_type in allowed_sections and section_scope not in allowed_sections[artifact_type]:
        blockers.append(f"report_package_section_scope_mismatch:{result_id}:{artifact_type}:{section_scope or 'missing'}")
    if artifact_type not in allowed_sections:
        blockers.append(f"report_package_artifact_type_not_audited:{result_id}:{artifact_type}")
    return blockers


def _negated_context(text: str, phrase: str) -> bool:
    index = text.find(phrase)
    if index < 0:
        return False
    window = text[max(0, index - 80) : index + len(phrase) + 80]
    return any(marker in window for marker in ("not ", "no ", "does not", "do not", "disabled", "without"))
