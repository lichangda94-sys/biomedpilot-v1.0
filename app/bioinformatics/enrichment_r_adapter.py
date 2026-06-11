from __future__ import annotations

from pathlib import Path
from typing import Any

from app.analysis_runtime.resources import full_mode_environment_blockers, full_mode_resource_blockers


CONTROLLED_ENRICHMENT_R_RUN_SCHEMA_VERSION = "biomedpilot.controlled_enrichment_r_run.v1"


def run_controlled_ora_r_fixture(
    project_root: str | Path,
    *,
    detection_path: str | Path | None = None,
    runner: object | None = None,
) -> dict[str, Any]:
    return _blocked_until_standard_worker_full_migration(
        project_root,
        analysis_type="ora",
        detection_path=detection_path,
    )


def run_controlled_gsea_preranked_r_fixture(
    project_root: str | Path,
    *,
    detection_path: str | Path | None = None,
    runner: object | None = None,
) -> dict[str, Any]:
    return _blocked_until_standard_worker_full_migration(
        project_root,
        analysis_type="gsea_preranked",
        detection_path=detection_path,
    )


def _blocked_until_standard_worker_full_migration(
    project_root: str | Path,
    *,
    analysis_type: str,
    detection_path: str | Path | None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    blockers = [
        "controlled_enrichment_legacy_formal_execution_disabled",
        "enrichment_full_standard_worker_migration_required",
        *full_mode_environment_blockers("enrichment"),
        *full_mode_resource_blockers("enrichment"),
    ]
    return {
        "schema_version": CONTROLLED_ENRICHMENT_R_RUN_SCHEMA_VERSION,
        "status": "blocked",
        "analysis_type": analysis_type,
        "result_semantics": "blocked",
        "project_root": str(root),
        "detection_path": str(detection_path or ""),
        "standard_worker_required": True,
        "required_worker_boundary": "standard_r_worker",
        "required_task_system_invocation": "task_center_registered",
        "required_mode": "full",
        "legacy_execution_policy": "disabled_until_full_standard_worker_migration_evidence_passes",
        "runtime_install_policy": "forbidden",
        "resource_download_policy": "forbidden",
        "plot_artifacts": [],
        "report_artifacts": [],
        "report_ready_eligible": False,
        "warnings": [],
        "blockers": list(dict.fromkeys(blockers)),
    }
