from __future__ import annotations

from pathlib import Path
from typing import Any

from app.analysis_runtime.package_catalog import build_standard_analysis_package_catalog
from app.bioinformatics.results.models import normalize_result_semantics


IMMUNE_STANDARD_PACKAGE_SOURCE_POLICY = "result_index_registered_standard_result_package_artifacts_only"
IMMUNE_REQUIRED_TABLE_TYPES = (
    "immune_score_matrix",
    "immune_signature_coverage",
    "immune_sample_score_summary",
)


def immune_scoring_standard_package_source(
    project_root: str | Path,
    *,
    result_id: str | None = None,
) -> dict[str, Any]:
    """Resolve immune/TME scoring artifacts from the standard result package."""

    root = Path(project_root).expanduser().resolve()
    catalog = build_standard_analysis_package_catalog(root)
    rows = [
        row
        for row in catalog.get("rows", []) or []
        if isinstance(row, dict)
        and str(row.get("module_id") or "") == "immune_infiltration"
        and (
            not result_id
            or str(row.get("result_id") or "") == str(result_id)
            or str(row.get("task_run_id") or "") == str(result_id)
        )
    ]
    if not rows:
        return _blocked("immune_standard_result_package_missing", result_id=result_id or "")
    package = rows[-1]
    if str(package.get("validation_status") or "") != "passed":
        return _blocked("immune_standard_result_package_invalid", result_id=result_id or str(package.get("result_id") or ""), package=package)
    if normalize_result_semantics(package.get("result_semantics"), default="") != "testing_level":
        return _blocked("immune_standard_result_package_semantics_invalid", result_id=str(package.get("result_id") or ""), package=package)
    artifact_manifest = package.get("artifact_manifest") if isinstance(package.get("artifact_manifest"), dict) else {}
    table_rows = [item for item in artifact_manifest.get("tables", []) or [] if isinstance(item, dict)]
    tables = {str(item.get("artifact_type") or ""): _artifact_source(item, package) for item in table_rows}
    missing = [artifact_type for artifact_type in IMMUNE_REQUIRED_TABLE_TYPES if artifact_type not in tables]
    not_package_local = [
        artifact_type
        for artifact_type, artifact in tables.items()
        if artifact_type in IMMUNE_REQUIRED_TABLE_TYPES and artifact.get("within_standard_package") is not True
    ]
    not_existing = [
        artifact_type
        for artifact_type, artifact in tables.items()
        if artifact_type in IMMUNE_REQUIRED_TABLE_TYPES and artifact.get("exists") is not True
    ]
    blockers = [
        *[f"immune_standard_package_table_missing:{item}" for item in missing],
        *[f"immune_standard_package_table_outside_package:{item}" for item in not_package_local],
        *[f"immune_standard_package_table_file_missing:{item}" for item in not_existing],
    ]
    if blockers:
        return _blocked(blockers[0], result_id=str(package.get("result_id") or ""), package=package, blockers=blockers, tables=tables)
    return {
        "status": "passed",
        "result_id": str(package.get("result_id") or ""),
        "source_policy": IMMUNE_STANDARD_PACKAGE_SOURCE_POLICY,
        "standard_result_package": str(package.get("package_path_relative") or package.get("package_path") or ""),
        "standard_package_validation_status": str(package.get("validation_status") or ""),
        "worker_boundary_type": str(package.get("worker_boundary_type") or ""),
        "worker_migration_status": str(package.get("worker_migration_status") or ""),
        "tables": tables,
        "reports": [
            _artifact_source(item, package)
            for item in artifact_manifest.get("reports", []) or []
            if isinstance(item, dict)
        ],
        "logs": [
            _artifact_source(item, package)
            for item in artifact_manifest.get("logs", []) or []
            if isinstance(item, dict)
        ],
        "package": package,
        "blockers": [],
        "warnings": list(package.get("warnings", []) or []),
    }


def _blocked(
    blocker: str,
    *,
    result_id: str,
    package: dict[str, Any] | None = None,
    blockers: list[str] | None = None,
    tables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "blocked",
        "result_id": result_id,
        "source_policy": IMMUNE_STANDARD_PACKAGE_SOURCE_POLICY,
        "standard_result_package": str((package or {}).get("package_path_relative") or ""),
        "standard_package_validation_status": str((package or {}).get("validation_status") or "missing"),
        "worker_boundary_type": str((package or {}).get("worker_boundary_type") or ""),
        "worker_migration_status": str((package or {}).get("worker_migration_status") or ""),
        "tables": tables or {},
        "reports": [],
        "logs": [],
        "package": package or {},
        "blocker": blocker,
        "blockers": blockers or [blocker],
        "warnings": [],
    }


def _artifact_source(artifact: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": str(artifact.get("artifact_type") or ""),
        "path": str(artifact.get("path") or ""),
        "path_relative": str(artifact.get("path_relative") or ""),
        "package_relative_path": str(artifact.get("package_relative_path") or ""),
        "standard_result_package": str(package.get("package_path_relative") or package.get("package_path") or ""),
        "exists": bool(artifact.get("exists")),
        "within_standard_package": artifact.get("within_standard_package") is True,
        "source_policy": IMMUNE_STANDARD_PACKAGE_SOURCE_POLICY,
    }
