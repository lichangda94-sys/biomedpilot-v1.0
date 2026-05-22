from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.project_workspace import PROJECT_MANIFEST_FILENAME
from app.shared.semantic_keys import AnalysisStatusKey, FeatureStatusKey, ReportStatusKey, ResultSemanticKey

from .action_rules import build_action_rows


RESULT_INDEX_PATH = Path("results") / "summaries" / "result_index.json"
REPORT_MANIFEST_PATH = Path("reports") / "project_report_manifest.json"


def build_analysis_center_state(project_root: str | Path | None) -> dict[str, Any]:
    """Build a read-only Bioinformatics gate preview state.

    The UIShell C2b carry-over intentionally avoids executor imports and avoids
    calling helpers that materialize result indexes or reports.
    """

    root = Path(project_root).expanduser().resolve() if project_root else None
    has_project = bool(root and (root / PROJECT_MANIFEST_FILENAME).exists())
    result_entries = _read_result_entries(root) if root else []
    page_rows = _page_rows(has_project=has_project, result_entries=result_entries)
    action_rows = build_action_rows(has_project=has_project, result_entries=result_entries)
    result_gate = _result_gate(result_entries)
    report_gate = _report_gate(root, result_entries)
    return {
        "schema_version": "biomedpilot.bioinformatics_gate_shell_state.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_root": str(root) if root else "",
        "has_project": has_project,
        "source_policy": "read_only_gate_preview_no_executor_no_artifact_write",
        "page_rows": page_rows,
        "action_rows": action_rows,
        "result_gate": result_gate,
        "report_gate": report_gate,
        "export_gate": _export_gate(report_gate),
        "dependency_rows": _dependency_rows(),
        "top_blockers": _top_blockers(has_project, action_rows),
        "top_warnings": _top_warnings(result_entries),
    }


def _page_rows(*, has_project: bool, result_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result_semantic = _dominant_result_semantic(result_entries)
    return [
        _page("project_home", "Project Home / 项目首页", FeatureStatusKey.DEVELOPER_PREVIEW.value, "not_a_result", "draft", "disabled_empty_result"),
        _page("data_source", "Data Source / 数据来源", FeatureStatusKey.TESTING.value, "not_a_result", "draft", "disabled_empty_result"),
        _page("data_check_preparation", "Data Check & Preparation / 数据检查与准备", AnalysisStatusKey.PREFLIGHT_ONLY.value, AnalysisStatusKey.PREFLIGHT_ONLY.value, "draft", "disabled_empty_result"),
        _page("group_design", "Group & Design / 分组与设计", AnalysisStatusKey.PREFLIGHT_ONLY.value, AnalysisStatusKey.PREFLIGHT_ONLY.value, "draft", "disabled_empty_result"),
        _page("analysis_tasks", "Analysis Tasks / 分析任务", AnalysisStatusKey.BLOCKED.value if not has_project else AnalysisStatusKey.PREFLIGHT_ONLY.value, AnalysisStatusKey.PREFLIGHT_ONLY.value, "draft", "disabled_empty_result"),
        _page("result_report", "Result & Report / 结果与报告", FeatureStatusKey.TESTING.value, result_semantic, ReportStatusKey.DRAFT.value, "disabled_missing_report_ready"),
        _page("report_export", "Report Export / 报告导出", ReportStatusKey.DRAFT.value, result_semantic, ReportStatusKey.DRAFT.value, "disabled_missing_report_ready"),
    ]


def _page(page_key: str, label: str, status_key: str, result_semantic_key: str, report_status_key: str, export_gate: str) -> dict[str, Any]:
    return {
        "page_key": page_key,
        "label": label,
        "status_key": status_key,
        "result_semantic_key": result_semantic_key,
        "report_status_key": report_status_key,
        "export_gate": export_gate,
        "formal_action_enabled": False,
    }


def _read_result_entries(root: Path | None) -> list[dict[str, Any]]:
    if root is None:
        return []
    payload = _read_json(root / RESULT_INDEX_PATH)
    raw: list[Any] = []
    for key in ("entries", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            raw.extend(value)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        entry = dict(item)
        entry_id = str(entry.get("result_id") or entry.get("item_id") or f"entry-{index}")
        if entry_id in seen:
            continue
        seen.add(entry_id)
        semantic = _normalize_result_semantic(entry)
        entry["result_id"] = entry_id
        entry["result_semantic_key"] = semantic
        entry["formal_computed_result"] = semantic == ResultSemanticKey.FORMAL_COMPUTED_RESULT.value
        entries.append(entry)
    return entries


def _normalize_result_semantic(entry: dict[str, Any]) -> str:
    raw = str(entry.get("canonical_result_semantics") or entry.get("result_semantics") or entry.get("semantic_key") or "").strip()
    normalized = raw.replace("-", "_").replace(" ", "_")
    aliases = {
        ResultSemanticKey.FORMAL_COMPUTED_RESULT.value: ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
        ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value: ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value,
        ResultSemanticKey.TESTING_SUMMARY_ONLY.value: ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
        "formal_computed_result": ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
        "formal": ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
        "imported_external_result": ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value,
        "imported": ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value,
        "testing_level": ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
        "testing_summary": ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
        "preflight_only": AnalysisStatusKey.PREFLIGHT_ONLY.value,
    }
    if normalized in aliases:
        return aliases[normalized]
    item_type = str(entry.get("item_type") or entry.get("analysis_type") or "")
    if "imported_deg" in item_type or "imported" in item_type:
        return ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value
    if "task_run" in item_type or "preflight" in item_type:
        return AnalysisStatusKey.PREFLIGHT_ONLY.value
    return ResultSemanticKey.TESTING_SUMMARY_ONLY.value


def _result_gate(entries: list[dict[str, Any]]) -> dict[str, Any]:
    formal_count = sum(1 for entry in entries if entry.get("result_semantic_key") == ResultSemanticKey.FORMAL_COMPUTED_RESULT.value)
    imported_count = sum(1 for entry in entries if entry.get("result_semantic_key") == ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value)
    preflight_count = sum(1 for entry in entries if entry.get("result_semantic_key") == AnalysisStatusKey.PREFLIGHT_ONLY.value)
    testing_count = len(entries) - formal_count - imported_count - preflight_count
    return {
        "status": "empty" if not entries else "available_for_review",
        "entry_count": len(entries),
        "formal_computed_result_count": formal_count,
        "imported_external_result_count": imported_count,
        "preflight_only_count": preflight_count,
        "testing_summary_count": max(testing_count, 0),
        "result_semantic_key": _dominant_result_semantic(entries),
        "fake_result_allowed": False,
        "fake_plot_allowed": False,
    }


def _report_gate(root: Path | None, entries: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = _read_json(root / REPORT_MANIFEST_PATH) if root else {}
    has_manifest = bool(manifest)
    return {
        "status": "draft_available" if has_manifest else "draft_only",
        "report_status_key": ReportStatusKey.DRAFT.value,
        "report_ready_package_allowed": False,
        "report_ready_package_present": False,
        "formal_report_generation_enabled": False,
        "source_result_count": len(entries),
        "manifest_present": has_manifest,
        "gate_reason": "Report preview is draft/testing only; report-ready package generation is disabled in UI-C2b.",
    }


def _export_gate(report_gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "disabled_missing_report_ready",
        "export_gate": "disabled_missing_report_ready",
        "export_enabled": False,
        "report_status_key": report_gate["report_status_key"],
        "report_ready_package_allowed": False,
        "gate_reason": "Export requires report-ready package and file picker; both remain disabled in UI-C2b.",
    }


def _dependency_rows() -> list[dict[str, Any]]:
    return [
        {"dependency_id": "formal_deg", "status": "blocked_until_carryover", "enabled": False},
        {"dependency_id": "formal_ora", "status": "blocked_until_backend", "enabled": False},
        {"dependency_id": "formal_gsea", "status": "hidden_until_ready", "enabled": False},
        {"dependency_id": "km_logrank", "status": "blocked_until_carryover", "enabled": False},
        {"dependency_id": "cox_univariate", "status": "blocked_until_carryover", "enabled": False},
        {"dependency_id": "report_ready_package", "status": "disabled_missing_report_ready", "enabled": False},
        {"dependency_id": "export_package", "status": "disabled_missing_report_ready", "enabled": False},
    ]


def _dominant_result_semantic(entries: list[dict[str, Any]]) -> str:
    if any(entry.get("result_semantic_key") == ResultSemanticKey.FORMAL_COMPUTED_RESULT.value for entry in entries):
        return ResultSemanticKey.FORMAL_COMPUTED_RESULT.value
    if any(entry.get("result_semantic_key") == ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value for entry in entries):
        return ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value
    if any(entry.get("result_semantic_key") == AnalysisStatusKey.PREFLIGHT_ONLY.value for entry in entries):
        return AnalysisStatusKey.PREFLIGHT_ONLY.value
    return ResultSemanticKey.TESTING_SUMMARY_ONLY.value


def _top_blockers(has_project: bool, action_rows: list[dict[str, Any]]) -> list[str]:
    blockers = [] if has_project else ["open_or_create_project_first"]
    blockers.extend(str(row.get("disabled_reason") or "") for row in action_rows if not row.get("enabled") and row.get("disabled_reason"))
    return list(dict.fromkeys(blockers))[:8]


def _top_warnings(entries: list[dict[str, Any]]) -> list[str]:
    warnings = ["No formal executor is enabled in UI-C2b."]
    if any(entry.get("result_semantic_key") == ResultSemanticKey.FORMAL_COMPUTED_RESULT.value for entry in entries):
        warnings.append("Existing formal result entries are displayed read-only; this shell does not generate new formal results.")
    return warnings


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
    except (OSError, json.JSONDecodeError):
        return {}
    return {}
