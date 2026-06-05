from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GATE_REPORT_SCHEMA_RELATIVE_PATH = Path("analysis") / "schemas" / "output" / "architecture_gate_report.schema.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BioMedPilot analysis architecture readiness gate.")
    parser.add_argument("--json-output", default="", help="Optional JSON output path.")
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
            "readiness_blockers": environment_validation.get("readiness_blockers", []),
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
            "evidence_registry_status": resource_validation.get("evidence_registry_status"),
            "evidence_registry_entry_count": resource_validation.get("evidence_registry_entry_count"),
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
        },
        "standard_worker_migration_rows": migration_rows,
        "remediation_queue": {
            "schema_version": remediation_queue.get("schema_version"),
            "status": remediation_queue.get("status"),
            "item_ids": [str(item.get("item_id")) for item in remediation_queue.get("items", []) if isinstance(item, dict)],
            "schema_validation_status": remediation_queue.get("schema_validation_status"),
            "schema_blockers": remediation_queue.get("schema_blockers", []),
        },
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


if __name__ == "__main__":
    raise SystemExit(main())
