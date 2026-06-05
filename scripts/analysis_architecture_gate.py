from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GATE_REPORT_SCHEMA_RELATIVE_PATH = Path("analysis") / "schemas" / "output" / "architecture_gate_report.schema.json"
EVIDENCE_TEMPLATE_PACKAGE_SCHEMA_RELATIVE_PATH = Path("analysis") / "schemas" / "output" / "evidence_template_package.schema.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BioMedPilot analysis architecture readiness gate.")
    parser.add_argument("--json-output", default="", help="Optional JSON output path.")
    parser.add_argument("--markdown-output", default="", help="Optional Markdown report output path.")
    parser.add_argument("--evidence-template-output", default="", help="Optional JSON output path for external evidence templates.")
    parser.add_argument("--require-full-ready", action="store_true", help="Fail unless the full analysis activation gate is eligible.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    payload = build_gate_report(root=root, require_full_ready=bool(args.require_full_ready))
    text = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=bool(args.pretty))
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown_output:
        markdown_output = Path(args.markdown_output).expanduser().resolve()
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(render_markdown_report(payload), encoding="utf-8")
    if args.evidence_template_output:
        template_output = Path(args.evidence_template_output).expanduser().resolve()
        template_output.parent.mkdir(parents=True, exist_ok=True)
        template_output.write_text(json.dumps(build_evidence_template_package(payload, root=root), ensure_ascii=False, indent=2), encoding="utf-8")
    print(text)
    return 0 if payload["status"] == "passed" else 1


def build_gate_report(*, root: Path, require_full_ready: bool) -> dict[str, Any]:
    from app.analysis_runtime.architecture_status import (
        build_analysis_architecture_status,
        build_analysis_remediation_queue,
        build_standard_worker_migration_matrix,
    )

    architecture_status = build_analysis_architecture_status()
    full_gate = architecture_status.get("full_analysis_activation_gate") if isinstance(architecture_status, dict) else {}
    migration_matrix = build_standard_worker_migration_matrix()
    remediation_queue = build_analysis_remediation_queue(architecture_status)
    blockers = _gate_blockers(
        architecture_status=architecture_status,
        full_gate=full_gate if isinstance(full_gate, dict) else {},
        migration_matrix=migration_matrix,
        remediation_queue=remediation_queue,
        require_full_ready=require_full_ready,
    )
    p1_issues = [str(item) for item in architecture_status.get("p1_issues", []) if item]
    full_gate_status = str(full_gate.get("status") or "unknown") if isinstance(full_gate, dict) else "unknown"
    environment_validation = architecture_status.get("environment_validation") if isinstance(architecture_status.get("environment_validation"), dict) else {}
    resource_validation = architecture_status.get("resource_validation") if isinstance(architecture_status.get("resource_validation"), dict) else {}
    migration_rows = [dict(row) for row in migration_matrix.get("rows", []) if isinstance(row, dict)]
    requirement_rows = [dict(row) for row in architecture_status.get("requirement_rows", []) if isinstance(row, dict)]
    remediation_items = [dict(item) for item in remediation_queue.get("items", []) if isinstance(item, dict)]
    priority_issues = _priority_issue_lists(
        p0_issues=[str(item) for item in architecture_status.get("p0_issues", []) if item],
        p1_issues=p1_issues,
        requirement_rows=requirement_rows,
        environment_validation=environment_validation,
        resource_validation=resource_validation,
        migration_matrix=migration_matrix,
    )
    payload = {
        "schema_version": "biomedpilot.analysis.architecture_gate_report.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "worktree": str(root),
        "status": "blocked" if blockers else "passed",
        "require_full_ready": require_full_ready,
        "architecture_status": architecture_status.get("status"),
        "requirement_summary": _requirement_summary(requirement_rows),
        "requirement_rows": requirement_rows,
        "priority_issue_lists": priority_issues,
        "top_architecture_risks": _top_architecture_risks(priority_issues),
        "p0_issues": [str(item) for item in architecture_status.get("p0_issues", []) if item],
        "p1_issues": p1_issues,
        "full_analysis_activation_gate": full_gate,
        "environment_readiness": {
            "schema_version": environment_validation.get("schema_version"),
            "status": environment_validation.get("status"),
            "full_mode_ready": environment_validation.get("full_mode_ready"),
            "environment_count": environment_validation.get("environment_count"),
            "blocked_environment_ids": environment_validation.get("blocked_environment_ids", []),
            "evidence_registry_status": environment_validation.get("evidence_registry_status"),
            "evidence_registry_entry_count": environment_validation.get("evidence_registry_entry_count"),
            "environment_lock_evidence_templates": environment_validation.get("environment_lock_evidence_templates", []),
            "readiness_blockers": environment_validation.get("readiness_blockers", []),
            "expected_environment_ids": environment_validation.get("expected_environment_ids", []),
            "missing_environment_ids": environment_validation.get("missing_environment_ids", []),
            "missing_environment_count": environment_validation.get("missing_environment_count", 0),
            "blockers": environment_validation.get("blockers", []),
            "warnings": environment_validation.get("warnings", []),
        },
        "resource_readiness": {
            "schema_version": resource_validation.get("schema_version"),
            "status": resource_validation.get("status"),
            "full_mode_ready": resource_validation.get("full_mode_ready"),
            "resource_count": resource_validation.get("resource_count"),
            "locked_resource_ids": resource_validation.get("locked_resource_ids", []),
            "blocked_resource_ids": resource_validation.get("blocked_resource_ids", []),
            "resource_lock_evidence_templates": resource_validation.get("resource_lock_evidence_templates", []),
            "evidence_registry_status": resource_validation.get("evidence_registry_status"),
            "evidence_registry_entry_count": resource_validation.get("evidence_registry_entry_count"),
            "expected_resource_ids": resource_validation.get("expected_resource_ids", []),
            "missing_resource_ids": resource_validation.get("missing_resource_ids", []),
            "missing_resource_count": resource_validation.get("missing_resource_count", 0),
            "blockers": resource_validation.get("blockers", []),
            "warnings": resource_validation.get("warnings", []),
        },
        "standard_worker_migration_matrix": {
            "schema_version": migration_matrix.get("schema_version"),
            "status": migration_matrix.get("status"),
            "module_count": migration_matrix.get("module_count"),
            "formal_pending_count": migration_matrix.get("formal_pending_count"),
            "full_blocked_count": migration_matrix.get("full_blocked_count"),
            "evidence_registry_status": migration_matrix.get("evidence_registry_status"),
            "evidence_entry_count": migration_matrix.get("evidence_entry_count"),
            "evidence_registry_blockers": migration_matrix.get("evidence_registry_blockers", []),
            "expected_evidence_module_ids": migration_matrix.get("expected_evidence_module_ids", []),
            "passed_evidence_module_ids": migration_matrix.get("passed_evidence_module_ids", []),
            "blocked_evidence_module_ids": migration_matrix.get("blocked_evidence_module_ids", []),
            "missing_evidence_module_ids": migration_matrix.get("missing_evidence_module_ids", []),
        },
        "standard_worker_migration_rows": migration_rows,
        "remediation_queue": {
            "schema_version": remediation_queue.get("schema_version"),
            "status": remediation_queue.get("status"),
            "item_ids": [str(item.get("item_id")) for item in remediation_queue.get("items", []) if isinstance(item, dict)],
            "items": remediation_items,
            "item_count": remediation_queue.get("item_count"),
            "automation_policy": remediation_queue.get("automation_policy"),
            "execution_policy": remediation_queue.get("execution_policy"),
            "install_policy": remediation_queue.get("install_policy"),
            "full_mode_policy": remediation_queue.get("full_mode_policy"),
            "schema_validation_status": remediation_queue.get("schema_validation_status"),
            "schema_blockers": remediation_queue.get("schema_blockers", []),
        },
        "remediation_summary": _remediation_summary(remediation_items),
        "blockers": blockers,
        "warnings": _gate_warnings(full_gate_status=full_gate_status, p1_issues=p1_issues, require_full_ready=require_full_ready),
        "execution_policy": "read_only_no_worker_execution_no_runtime_install_no_resource_download",
        "exit_policy": (
            "exit_nonzero_until_full_analysis_activation_gate_is_eligible"
            if require_full_ready
            else "exit_zero_when_p0_empty_and_contract_payloads_are_valid_even_if_full_gate_is_blocked"
        ),
    }
    schema_blockers = _gate_report_schema_blockers(payload, root=root)
    payload["schema_validation_status"] = "blocked" if schema_blockers else "passed"
    payload["schema_blockers"] = schema_blockers
    if schema_blockers:
        payload["status"] = "blocked"
        payload["blockers"] = [*blockers, "analysis_architecture_gate_report_schema_invalid"]
    return payload


def _gate_blockers(
    *,
    architecture_status: dict[str, Any],
    full_gate: dict[str, Any],
    migration_matrix: dict[str, Any],
    remediation_queue: dict[str, Any],
    require_full_ready: bool,
) -> list[str]:
    blockers: list[str] = []
    if architecture_status.get("p0_issues"):
        blockers.append("analysis_architecture_p0_issues_present")
    if full_gate.get("schema_validation_status") != "passed":
        blockers.append("full_analysis_activation_gate_schema_not_passed")
    if migration_matrix.get("evidence_registry_status") != "passed":
        blockers.append("standard_worker_migration_evidence_registry_not_passed")
    if remediation_queue.get("schema_validation_status") != "passed":
        blockers.append("analysis_remediation_queue_schema_not_passed")
    if require_full_ready and full_gate.get("status") != "eligible":
        blockers.append("full_analysis_activation_gate_not_ready")
    return blockers


def _gate_warnings(*, full_gate_status: str, p1_issues: list[str], require_full_ready: bool) -> list[str]:
    warnings: list[str] = []
    if p1_issues:
        warnings.append("analysis_architecture_has_p1_gaps")
    if full_gate_status == "blocked" and not require_full_ready:
        warnings.append("full_analysis_activation_gate_blocked_but_allowed_by_default_gate")
    return warnings


def _requirement_summary(requirement_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"pass": 0, "warn": 0, "fail": 0, "other": 0}
    for row in requirement_rows:
        status = str(row.get("status") or "other")
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    return {
        "requirement_count": len(requirement_rows),
        "pass_count": counts["pass"],
        "warn_count": counts["warn"],
        "fail_count": counts["fail"],
        "other_count": counts["other"],
        "status_order": ["fail", "warn", "pass"],
    }


def _priority_issue_lists(
    *,
    p0_issues: list[str],
    p1_issues: list[str],
    requirement_rows: list[dict[str, Any]],
    environment_validation: dict[str, Any],
    resource_validation: dict[str, Any],
    migration_matrix: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    p0 = [
        _issue("P0", issue, "architecture_p0_guard", "P0 issue is present in architecture status.")
        for issue in p0_issues
    ]
    p1: list[dict[str, Any]] = []
    if "full_analysis_environment_locks_not_restored" in p1_issues:
        p1.append(
            _issue(
                "P1",
                "full_analysis_environment_locks_not_restored",
                "environment_readiness",
                "Full analysis environments remain scaffold-only or lack restored lock evidence.",
                evidence={
                    "blocked_environment_ids": environment_validation.get("blocked_environment_ids", []),
                    "readiness_blockers": environment_validation.get("readiness_blockers", []),
                },
            )
        )
    if "full_analysis_resource_locks_not_complete" in p1_issues:
        p1.append(
            _issue(
                "P1",
                "full_analysis_resource_locks_not_complete",
                "resource_readiness",
                "Full analysis resources/tools remain blocked until version/hash/license/cache evidence is complete.",
                evidence={
                    "blocked_resource_ids": resource_validation.get("blocked_resource_ids", []),
                    "warnings": resource_validation.get("warnings", []),
                },
            )
        )
    if "formal_algorithms_not_universally_migrated_to_isolated_standard_worker" in p1_issues:
        p1.append(
            _issue(
                "P1",
                "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
                "standard_worker_migration_matrix",
                "Formal algorithms still have pending isolated standard-worker migration rows.",
                evidence={
                    "formal_pending_count": migration_matrix.get("formal_pending_count"),
                    "full_blocked_count": migration_matrix.get("full_blocked_count"),
                    "evidence_entry_count": migration_matrix.get("evidence_entry_count"),
                },
            )
        )
    p2_requirement_ids = {"RARCH-03", "RARCH-08", "RARCH-09", "RARCH-16", "RARCH-17"}
    p3_requirement_ids = {"RARCH-04", "RARCH-12", "RARCH-13", "RARCH-14", "RARCH-15", "RARCH-18"}
    p2 = [_issue_from_requirement("P2", row) for row in requirement_rows if row.get("requirement_id") in p2_requirement_ids and row.get("status") == "warn"]
    p3 = [_issue_from_requirement("P3", row) for row in requirement_rows if row.get("requirement_id") in p3_requirement_ids and row.get("status") == "warn"]
    return {"P0": p0, "P1": p1, "P2": p2, "P3": p3}


def _issue_from_requirement(priority: str, row: dict[str, Any]) -> dict[str, Any]:
    return _issue(
        priority,
        str(row.get("requirement_id") or "unknown_requirement"),
        str(row.get("evidence") or ""),
        str(row.get("label") or ""),
        evidence={
            "status": row.get("status"),
            "warnings": row.get("warnings", []),
            "blockers": row.get("blockers", []),
        },
    )


def _issue(priority: str, issue_id: str, source: str, summary: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "priority": priority,
        "issue_id": issue_id,
        "source": source,
        "summary": summary,
        "evidence": evidence or {},
    }


def _top_architecture_risks(priority_issues: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for priority in ("P0", "P1", "P2", "P3"):
        for issue in priority_issues.get(priority, []):
            risks.append(
                {
                    "priority": priority,
                    "risk_id": str(issue.get("issue_id") or ""),
                    "source": str(issue.get("source") or ""),
                    "summary": str(issue.get("summary") or ""),
                    "evidence": issue.get("evidence", {}),
                }
            )
            if len(risks) >= 5:
                return risks
    return risks


def _remediation_summary(remediation_items: list[dict[str, Any]]) -> dict[str, Any]:
    involved_files: list[str] = []
    minimal_path: list[str] = []
    manual_decisions: list[dict[str, Any]] = []
    for item in remediation_items:
        item_id = str(item.get("item_id") or "")
        title = str(item.get("title") or item_id)
        minimal_path.append(item_id)
        for path in item.get("recommended_files", []):
            if isinstance(path, str) and path not in involved_files:
                involved_files.append(path)
        manual_decisions.append(
            {
                "item_id": item_id,
                "title": title,
                "decision_required": str(item.get("boundary") or ""),
                "required_evidence": [str(value) for value in item.get("required_evidence", []) if value],
                "scope": _remediation_scope_summary(item),
            }
        )
    return {
        "item_count": len(remediation_items),
        "minimal_remediation_path": minimal_path,
        "involved_files": involved_files,
        "manual_decision_points": manual_decisions,
    }


def _gate_report_schema_blockers(payload: dict[str, Any], *, root: Path) -> list[str]:
    schema_path = root / GATE_REPORT_SCHEMA_RELATIVE_PATH
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError:
        return [f"analysis_architecture_gate_report_schema_missing:{GATE_REPORT_SCHEMA_RELATIVE_PATH}"]
    except json.JSONDecodeError:
        return [f"analysis_architecture_gate_report_schema_invalid_json:{GATE_REPORT_SCHEMA_RELATIVE_PATH}"]

    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"analysis_architecture_gate_report_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_architecture_gate_report_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _matches_json_type(value, expected_type):
            blockers.append(f"analysis_architecture_gate_report_type_invalid:{field}")
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"analysis_architecture_gate_report_min_length_invalid:{field}")
    return blockers


def _matches_json_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def render_markdown_report(payload: dict[str, Any]) -> str:
    requirement_summary = payload.get("requirement_summary") if isinstance(payload.get("requirement_summary"), dict) else {}
    full_gate = payload.get("full_analysis_activation_gate") if isinstance(payload.get("full_analysis_activation_gate"), dict) else {}
    migration_matrix = payload.get("standard_worker_migration_matrix") if isinstance(payload.get("standard_worker_migration_matrix"), dict) else {}
    remediation_summary = payload.get("remediation_summary") if isinstance(payload.get("remediation_summary"), dict) else {}
    remediation_queue = payload.get("remediation_queue") if isinstance(payload.get("remediation_queue"), dict) else {}
    remediation_items = [item for item in remediation_queue.get("items", []) if isinstance(item, dict)]

    lines: list[str] = [
        "# BioMedPilot R Analysis Architecture Gate Report",
        "",
        f"Generated: `{_markdown_text(payload.get('created_at'))}`",
        "",
        f"Worktree: `{_markdown_text(payload.get('worktree'))}`",
        "",
        "## 1. 当前是否符合目标模式",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Gate status | `{_markdown_text(payload.get('status'))}` |",
        f"| Architecture status | `{_markdown_text(payload.get('architecture_status'))}` |",
        f"| Schema validation | `{_markdown_text(payload.get('schema_validation_status'))}` |",
        f"| Full analysis activation gate | `{_markdown_text(full_gate.get('status'))}` |",
        f"| Require full ready | `{_markdown_text(payload.get('require_full_ready'))}` |",
        "",
        "Current interpretation: the architecture gate proves the current source has no P0 blocker and the report contract is schema-valid. It does not prove full analysis readiness while the full activation gate remains blocked.",
        "",
        "## 2. PASS / WARN / FAIL 总表",
        "",
        "| Requirements | PASS | WARN | FAIL | Other |",
        "| --- | ---: | ---: | ---: | ---: |",
        (
            f"| {_markdown_text(requirement_summary.get('requirement_count'))} | "
            f"{_markdown_text(requirement_summary.get('pass_count'))} | "
            f"{_markdown_text(requirement_summary.get('warn_count'))} | "
            f"{_markdown_text(requirement_summary.get('fail_count'))} | "
            f"{_markdown_text(requirement_summary.get('other_count'))} |"
        ),
        "",
        "## 3. 最大的 5 个架构风险",
        "",
    ]
    risks = [risk for risk in payload.get("top_architecture_risks", []) if isinstance(risk, dict)]
    lines.extend(_markdown_table(["Priority", "Risk ID", "Source", "Summary"], risks, ["priority", "risk_id", "source", "summary"]))
    lines.extend(
        [
            "",
            "### Standard Worker Migration Evidence Coverage",
            "",
        ]
    )
    lines.extend(_migration_evidence_coverage_table(migration_matrix))
    lines.extend(
        [
            "",
            "## 4. P0/P1/P2/P3 问题清单",
            "",
        ]
    )
    priority_lists = payload.get("priority_issue_lists") if isinstance(payload.get("priority_issue_lists"), dict) else {}
    for priority in ("P0", "P1", "P2", "P3"):
        issues = [issue for issue in priority_lists.get(priority, []) if isinstance(issue, dict)]
        lines.extend([f"### {priority}", ""])
        lines.extend(_markdown_table(["Issue ID", "Source", "Summary"], issues, ["issue_id", "source", "summary"]))
        lines.append("")
    lines.extend(
        [
            "## 5. 涉及的文件路径",
            "",
        ]
    )
    for path in remediation_summary.get("involved_files", []):
        lines.append(f"- `{_markdown_text(path)}`")
    if not remediation_summary.get("involved_files"):
        lines.append("- None reported.")
    lines.extend(
        [
            "",
            "## 6. 最小可行整改路径",
            "",
        ]
    )
    for index, item_id in enumerate(remediation_summary.get("minimal_remediation_path", []), start=1):
        lines.append(f"{index}. `{_markdown_text(item_id)}`")
    if not remediation_summary.get("minimal_remediation_path"):
        lines.append("No remediation item is currently required by the gate.")
    lines.extend(
        [
            "",
            "## 7. 建议优先修改的文件",
            "",
        ]
    )
    lines.extend(_priority_file_lines(remediation_items))
    lines.extend(
        [
            "",
            "## 8. 已完成的修改",
            "",
        ]
    )
    lines.extend(_completed_change_lines(payload))
    lines.extend(
        [
            "",
            "## 9. 尚需人工决定的问题",
            "",
        ]
    )
    decisions = [item for item in remediation_summary.get("manual_decision_points", []) if isinstance(item, dict)]
    lines.extend(_markdown_table(["Item", "Decision Required", "Required Evidence", "Scope"], decisions, ["item_id", "decision_required", "required_evidence", "scope"]))
    lines.append("")
    return "\n".join(lines)


def build_evidence_template_package(payload: dict[str, Any], *, root: Path) -> dict[str, Any]:
    environment_readiness = payload.get("environment_readiness") if isinstance(payload.get("environment_readiness"), dict) else {}
    resource_readiness = payload.get("resource_readiness") if isinstance(payload.get("resource_readiness"), dict) else {}
    remediation_summary = payload.get("remediation_summary") if isinstance(payload.get("remediation_summary"), dict) else {}
    migration_rows = [row for row in payload.get("standard_worker_migration_rows", []) if isinstance(row, dict)]
    migration_templates = [
        row.get("migration_evidence_template")
        for row in migration_rows
        if isinstance(row.get("migration_evidence_template"), dict)
    ]
    migration_blockers = {
        str(row.get("module_id") or ""): row.get("migration_blockers", [])
        for row in migration_rows
        if row.get("module_id")
    }
    environment_templates = [
        item
        for item in environment_readiness.get("environment_lock_evidence_templates", [])
        if isinstance(item, dict)
    ]
    resource_templates = [
        item
        for item in resource_readiness.get("resource_lock_evidence_templates", [])
        if isinstance(item, dict)
    ]
    migration_matrix = payload.get("standard_worker_migration_matrix") if isinstance(payload.get("standard_worker_migration_matrix"), dict) else {}
    template_package = {
        "schema_version": "biomedpilot.analysis.evidence_template_package.v1",
        "created_at": payload.get("created_at"),
        "worktree": payload.get("worktree"),
        "architecture_status": payload.get("architecture_status"),
        "full_analysis_activation_gate_status": (
            payload.get("full_analysis_activation_gate", {}).get("status")
            if isinstance(payload.get("full_analysis_activation_gate"), dict)
            else "unknown"
        ),
        "execution_policy": payload.get("execution_policy"),
        "install_policy": "no_runtime_package_install_or_resource_download",
        "template_policy": {
            "templates_are_not_readiness_evidence": True,
            "external_evidence_must_be_registered": True,
            "runtime_install_forbidden": True,
            "runtime_download_forbidden": True,
            "mock_lite_and_legacy_sidecar_evidence_forbidden": True,
        },
        "registry_paths": {
            "environment_lock_evidence_registry": "analysis/registry/environment_lock_evidence.json",
            "resource_lock_evidence_registry": "analysis/registry/resource_lock_evidence.json",
            "standard_worker_migration_evidence_registry": "analysis/registry/standard_worker_migration_evidence.json",
        },
        "expected_evidence_scope": {
            "scope_policy": "authoritative_registry_scope",
            "expected_environment_ids": environment_readiness.get("expected_environment_ids", []),
            "missing_environment_ids": environment_readiness.get("missing_environment_ids", []),
            "expected_resource_ids": resource_readiness.get("expected_resource_ids", []),
            "missing_resource_ids": resource_readiness.get("missing_resource_ids", []),
            "expected_module_ids": migration_matrix.get("expected_evidence_module_ids", []),
            "passed_module_ids": migration_matrix.get("passed_evidence_module_ids", []),
            "blocked_module_ids": migration_matrix.get("blocked_evidence_module_ids", []),
            "missing_module_ids": migration_matrix.get("missing_evidence_module_ids", []),
        },
        "environment_lock_evidence_templates": environment_templates,
        "resource_lock_evidence_templates": resource_templates,
        "standard_worker_migration_evidence_templates": migration_templates,
        "blockers": {
            "environment_readiness": environment_readiness.get("readiness_blockers", []),
            "resource_readiness": resource_readiness.get("blocked_resource_ids", []),
            "standard_worker_migration": migration_blockers,
            "full_analysis_activation_gate": (
                payload.get("full_analysis_activation_gate", {}).get("blockers", [])
                if isinstance(payload.get("full_analysis_activation_gate"), dict)
                else []
            ),
        },
        "remediation_scope": {
            "manual_decision_points": [
                {
                    "item_id": item.get("item_id"),
                    "scope": item.get("scope", ""),
                    "decision_required": item.get("decision_required", ""),
                }
                for item in remediation_summary.get("manual_decision_points", [])
                if isinstance(item, dict)
            ],
            "minimal_remediation_path": remediation_summary.get("minimal_remediation_path", []),
        },
        "template_counts": {
            "environment_lock_evidence_templates": len(environment_templates),
            "resource_lock_evidence_templates": len(resource_templates),
            "standard_worker_migration_evidence_templates": len(migration_templates),
        },
    }
    schema_blockers = _evidence_template_package_schema_blockers(template_package, root=root)
    template_package["schema_validation_status"] = "blocked" if schema_blockers else "passed"
    template_package["schema_blockers"] = schema_blockers
    return template_package


def _evidence_template_package_schema_blockers(payload: dict[str, Any], *, root: Path) -> list[str]:
    schema_path = root / EVIDENCE_TEMPLATE_PACKAGE_SCHEMA_RELATIVE_PATH
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError:
        return [f"analysis_evidence_template_package_schema_missing:{EVIDENCE_TEMPLATE_PACKAGE_SCHEMA_RELATIVE_PATH}"]
    except json.JSONDecodeError:
        return [f"analysis_evidence_template_package_schema_invalid_json:{EVIDENCE_TEMPLATE_PACKAGE_SCHEMA_RELATIVE_PATH}"]

    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"analysis_evidence_template_package_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_evidence_template_package_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _matches_json_type(value, expected_type):
            blockers.append(f"analysis_evidence_template_package_type_invalid:{field}")
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"analysis_evidence_template_package_min_length_invalid:{field}")
    blockers.extend(_environment_template_package_item_blockers(payload.get("environment_lock_evidence_templates")))
    blockers.extend(_resource_template_package_item_blockers(payload.get("resource_lock_evidence_templates")))
    blockers.extend(_evidence_template_scope_blockers(payload))
    return blockers


def _evidence_template_scope_blockers(payload: dict[str, Any]) -> list[str]:
    scope = payload.get("expected_evidence_scope")
    if not isinstance(scope, dict):
        return ["analysis_evidence_template_package_expected_scope_missing"]
    blockers: list[str] = []
    for field in (
        "expected_environment_ids",
        "missing_environment_ids",
        "expected_resource_ids",
        "missing_resource_ids",
        "expected_module_ids",
        "passed_module_ids",
        "blocked_module_ids",
        "missing_module_ids",
    ):
        value = scope.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            blockers.append(f"analysis_evidence_template_package_expected_scope_invalid:{field}")
    if scope.get("scope_policy") != "authoritative_registry_scope":
        blockers.append("analysis_evidence_template_package_expected_scope_policy_invalid")
    return blockers


def _environment_template_package_item_blockers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    blockers: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            blockers.append(f"analysis_evidence_template_package_environment_template_invalid:{index}")
            continue
        template_id = str(item.get("environment_id") or index)
        content = item.get("renv_lock_content")
        if not isinstance(content, dict):
            blockers.append(f"analysis_evidence_template_package_environment_template_renv_lock_content_missing:{template_id}")
        elif content.get("packages_non_empty") is not True:
            blockers.append(f"analysis_evidence_template_package_environment_template_packages_non_empty_missing:{template_id}")
        if isinstance(content, dict) and not str(content.get("policy_status") or ""):
            blockers.append(f"analysis_evidence_template_package_environment_template_policy_status_missing:{template_id}")
        docker_image = item.get("docker_image")
        if not isinstance(docker_image, dict):
            blockers.append(f"analysis_evidence_template_package_environment_template_docker_image_missing:{template_id}")
        else:
            if not str(docker_image.get("image_ref") or ""):
                blockers.append(f"analysis_evidence_template_package_environment_template_docker_image_ref_missing:{template_id}")
            if not isinstance(docker_image.get("digest"), dict):
                blockers.append(f"analysis_evidence_template_package_environment_template_docker_image_digest_missing:{template_id}")
            if not str(docker_image.get("architecture") or ""):
                blockers.append(f"analysis_evidence_template_package_environment_template_docker_image_architecture_missing:{template_id}")
            if docker_image.get("build_status") != "built":
                blockers.append(f"analysis_evidence_template_package_environment_template_docker_image_status_missing:{template_id}")
            if not str(docker_image.get("build_log") or ""):
                blockers.append(f"analysis_evidence_template_package_environment_template_docker_image_build_log_missing:{template_id}")
    return blockers


def _resource_template_package_item_blockers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    blockers: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            blockers.append(f"analysis_evidence_template_package_resource_template_invalid:{index}")
            continue
        template_id = str(item.get("resource_id") or index)
        content = item.get("cache_content")
        if not isinstance(content, dict):
            blockers.append(f"analysis_evidence_template_package_resource_template_cache_content_missing:{template_id}")
            continue
        if content.get("non_empty") is not True:
            blockers.append(f"analysis_evidence_template_package_resource_template_non_empty_missing:{template_id}")
    return blockers


def _priority_file_lines(remediation_items: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in remediation_items:
        item_id = _markdown_text(item.get("item_id"))
        files = [str(path) for path in item.get("recommended_files", []) if path]
        if not files:
            continue
        lines.append(f"- `{item_id}`")
        for path in files[:8]:
            lines.append(f"  - `{_markdown_text(path)}`")
        if len(files) > 8:
            lines.append(f"  - ... {len(files) - 8} more files")
    return lines or ["- No priority files reported by remediation queue."]


def _completed_change_lines(payload: dict[str, Any]) -> list[str]:
    lines = [
        "- Architecture gate script exists and emits a schema-versioned JSON payload.",
        "- The gate reports PASS/WARN/FAIL requirement rows, priority issues, top risks, and remediation guidance from one machine-readable source.",
        "- Default gate policy remains read-only and does not execute workers, install R packages, or download resources.",
    ]
    if payload.get("schema_validation_status") == "passed":
        lines.append("- Architecture gate report schema validation is currently `passed`.")
    if not payload.get("p0_issues"):
        lines.append("- Current P0 issue list is empty.")
    full_gate = payload.get("full_analysis_activation_gate") if isinstance(payload.get("full_analysis_activation_gate"), dict) else {}
    if full_gate.get("status") == "blocked":
        lines.append("- Full analysis activation remains explicitly blocked rather than silently enabled.")
    return lines


def _remediation_scope_summary(item: dict[str, Any]) -> str:
    module_scope = item.get("module_scope") if isinstance(item.get("module_scope"), dict) else {}
    if not module_scope:
        return ""
    missing_modules = module_scope.get("missing_module_ids") if isinstance(module_scope.get("missing_module_ids"), list) else []
    passed_modules = module_scope.get("passed_module_ids") if isinstance(module_scope.get("passed_module_ids"), list) else []
    blocked_modules = module_scope.get("blocked_module_ids") if isinstance(module_scope.get("blocked_module_ids"), list) else []
    return (
        f"missing={len(missing_modules)}; "
        f"passed={len(passed_modules)}; "
        f"blocked={len(blocked_modules)}; "
        f"modules={', '.join(str(item) for item in missing_modules)}"
    )


def _migration_evidence_coverage_table(matrix: dict[str, Any]) -> list[str]:
    rows = [
        {
            "metric": "Expected evidence modules",
            "count": len(matrix.get("expected_evidence_module_ids", []) if isinstance(matrix.get("expected_evidence_module_ids"), list) else []),
            "modules": matrix.get("expected_evidence_module_ids", []),
        },
        {
            "metric": "Passed evidence modules",
            "count": len(matrix.get("passed_evidence_module_ids", []) if isinstance(matrix.get("passed_evidence_module_ids"), list) else []),
            "modules": matrix.get("passed_evidence_module_ids", []),
        },
        {
            "metric": "Blocked evidence modules",
            "count": len(matrix.get("blocked_evidence_module_ids", []) if isinstance(matrix.get("blocked_evidence_module_ids"), list) else []),
            "modules": matrix.get("blocked_evidence_module_ids", []),
        },
        {
            "metric": "Missing evidence modules",
            "count": len(matrix.get("missing_evidence_module_ids", []) if isinstance(matrix.get("missing_evidence_module_ids"), list) else []),
            "modules": matrix.get("missing_evidence_module_ids", []),
        },
    ]
    return _markdown_table(["Metric", "Count", "Modules"], rows, ["metric", "count", "modules"])


def _markdown_table(headers: list[str], rows: list[dict[str, Any]], fields: list[str]) -> list[str]:
    if not rows:
        return ["No rows reported."]
    table = [
        "| " + " | ".join(_escape_markdown_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        table.append("| " + " | ".join(_escape_markdown_cell(row.get(field)) for field in fields) + " |")
    return table


def _escape_markdown_cell(value: Any) -> str:
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value) if value is not None else ""
    return text.replace("\n", " ").replace("|", "\\|")


def _markdown_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value) if value is not None else ""


if __name__ == "__main__":
    raise SystemExit(main())
