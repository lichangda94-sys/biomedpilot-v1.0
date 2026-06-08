from __future__ import annotations

from pathlib import Path
from typing import Any

from app.analysis_runtime.package_catalog import build_standard_analysis_package_catalog
from app.bioinformatics.results.models import normalize_result_semantics


FORMAL_DEG_STANDARD_PACKAGE_SOURCE_POLICY = "result_index_registered_standard_result_package_artifacts_only"


def formal_deg_standard_package_source(root: str | Path, entry: dict[str, Any]) -> dict[str, Any]:
    """Resolve the package-local DEG table for a formal DEG result.

    Formal DEG review, plotting, and report-ready gates must not infer analysis
    inputs from module-private result folders. They consume only the standard
    result package registered in the result index.
    """

    project_root = Path(root).expanduser().resolve()
    result_id = str(entry.get("result_id") or "")
    catalog = build_standard_analysis_package_catalog(project_root)
    package = next(
        (
            row
            for row in catalog.get("rows", []) or []
            if isinstance(row, dict) and str(row.get("result_id") or "") == result_id
        ),
        {},
    )
    if not package:
        return _blocked("formal_deg_standard_result_package_missing", entry=entry)
    if str(package.get("validation_status") or "") != "passed":
        return _blocked("formal_deg_standard_result_package_invalid", entry=entry, package=package)
    if str(package.get("module_id") or "") != "deg":
        return _blocked("formal_deg_standard_result_package_module_mismatch", entry=entry, package=package)
    if normalize_result_semantics(package.get("result_semantics"), default="") != "formal_computed_result":
        return _blocked("formal_deg_standard_result_package_semantics_invalid", entry=entry, package=package)
    artifact_manifest = package.get("artifact_manifest") if isinstance(package.get("artifact_manifest"), dict) else {}
    table = next(
        (
            item
            for item in artifact_manifest.get("tables", []) or []
            if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"
        ),
        {},
    )
    if not table:
        return _blocked("formal_deg_standard_package_deg_table_missing", entry=entry, package=package)
    if not bool(table.get("exists")):
        return _blocked("formal_deg_standard_package_deg_table_file_missing", entry=entry, package=package)
    if table.get("within_standard_package") is not True:
        return _blocked("formal_deg_standard_package_deg_table_outside_package", entry=entry, package=package)
    return {
        "status": "passed",
        "result_id": result_id,
        "source_policy": FORMAL_DEG_STANDARD_PACKAGE_SOURCE_POLICY,
        "table_path": str(table.get("path") or ""),
        "table_path_relative": str(table.get("path_relative") or ""),
        "table_package_relative_path": str(table.get("package_relative_path") or ""),
        "table_artifact": _table_artifact(table, package),
        "package_path": str(package.get("package_path") or ""),
        "package_path_relative": str(package.get("package_path_relative") or ""),
        "package_validation_status": str(package.get("validation_status") or ""),
        "worker_boundary_type": str(package.get("worker_boundary_type") or ""),
        "worker_migration_status": str(package.get("worker_migration_status") or ""),
        "package": package,
        "blocker": "",
        "blockers": [],
        "warnings": [],
    }


def formal_deg_blocked_standard_package_provenance(entry: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "standard_result_package": str(source.get("package_path_relative") or ""),
        "standard_package_validation_status": str(source.get("package_validation_status") or "missing"),
        "standard_package_source_policy": FORMAL_DEG_STANDARD_PACKAGE_SOURCE_POLICY,
        "result_index_path": "results/summaries/result_index.json",
    }


def _blocked(blocker: str, *, entry: dict[str, Any], package: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "status": "blocked",
        "result_id": str(entry.get("result_id") or ""),
        "source_policy": FORMAL_DEG_STANDARD_PACKAGE_SOURCE_POLICY,
        "table_path": "",
        "table_path_relative": "",
        "table_package_relative_path": "",
        "table_artifact": {},
        "package_path": str((package or {}).get("package_path") or ""),
        "package_path_relative": str((package or {}).get("package_path_relative") or ""),
        "package_validation_status": str((package or {}).get("validation_status") or "missing"),
        "worker_boundary_type": str((package or {}).get("worker_boundary_type") or ""),
        "worker_migration_status": str((package or {}).get("worker_migration_status") or ""),
        "package": package or {},
        "blocker": blocker,
        "blockers": [blocker],
        "warnings": [],
    }
    return payload


def _table_artifact(table: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": "deg_result_table",
        "path": str(table.get("path_relative") or ""),
        "package_relative_path": str(table.get("package_relative_path") or ""),
        "standard_result_package": str(package.get("package_path_relative") or package.get("package_path") or ""),
        "source_policy": FORMAL_DEG_STANDARD_PACKAGE_SOURCE_POLICY,
        "within_standard_package": True,
    }
