from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    return {
        "schema_version": "biomedpilot.analysis.architecture_gate_report.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "worktree": str(root),
        "status": "blocked" if blockers else "passed",
        "require_full_ready": require_full_ready,
        "architecture_status": architecture_status.get("status"),
        "p0_issues": [str(item) for item in architecture_status.get("p0_issues", []) if item],
        "p1_issues": p1_issues,
        "full_analysis_activation_gate": full_gate,
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


if __name__ == "__main__":
    raise SystemExit(main())
