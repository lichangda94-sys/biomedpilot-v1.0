from __future__ import annotations

from typing import Any


def legacy_sidecar_execution_gate(module_id: str, *, allow_legacy_sidecar_execution: bool = False) -> dict[str, Any]:
    """Gate direct legacy service-adapter sidecar execution.

    Legacy sidecars remain useful for compatibility audits, but normal runtime
    execution must move through task-center registered standard workers. The
    explicit override is reserved for focused tests and migration evidence work
    that needs to inspect the old package contract without presenting it as
    formal standard-worker execution.
    """

    module = str(module_id or "").strip()
    if allow_legacy_sidecar_execution:
        return {
            "schema_version": "biomedpilot.analysis.legacy_sidecar_execution_gate.v1",
            "status": "passed",
            "module_id": module,
            "policy": "developer_test_override_legacy_sidecar_execution_allowed_for_contract_audit_only",
            "warnings": ["legacy_sidecar_execution_developer_override_not_user_execution_readiness"],
            "blockers": [],
        }

    matrix = _standard_worker_migration_matrix()
    row = next(
        (
            item
            for item in matrix.get("rows", [])
            if isinstance(item, dict) and str(item.get("module_id") or "") == module
        ),
        {},
    )
    return {
        "schema_version": "biomedpilot.analysis.legacy_sidecar_execution_gate.v1",
        "status": "blocked",
        "module_id": module,
        "policy": "legacy_service_adapter_sidecar_execution_disabled_until_task_center_standard_worker_migration",
        "required_worker_boundary": "standard_r_worker",
        "required_task_system_invocation": "task_center_registered",
        "current_formal_worker_status": str(row.get("formal_worker_status") or "missing"),
        "current_full_status": str(row.get("full_status") or "missing"),
        "migration_next_action": str(row.get("migration_next_action") or "inspect_standard_worker_migration_matrix"),
        "migration_blockers": [str(item) for item in row.get("migration_blockers", [])] if isinstance(row.get("migration_blockers"), list) else [],
        "warnings": [],
        "blockers": [
            "legacy_service_adapter_sidecar_execution_disabled",
            f"standard_worker_migration_required:{module or 'missing'}",
        ],
    }


def _standard_worker_migration_matrix() -> dict[str, Any]:
    from app.analysis_runtime.architecture_status import build_standard_worker_migration_matrix

    return build_standard_worker_migration_matrix()
