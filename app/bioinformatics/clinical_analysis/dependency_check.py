from __future__ import annotations

import importlib.util
from importlib import metadata
from pathlib import Path
from typing import Any

from app.shared.local_engines import (
    CAPABILITY_STATUS_AVAILABLE,
    PYTHON_STATISTICAL_ENGINE_FAMILY,
    R_BIOCONDUCTOR_ENGINE_FAMILY,
    ExternalEngineRegistry,
    dependency_snapshot_handoff,
    load_external_engine_registry,
)


SURVIVAL_PYTHON_CAPABILITIES = ("package.python.lifelines.available",)
SURVIVAL_R_CAPABILITIES = ("package.r.survival.available", "package.r.survminer.available")


def check_survival_backend_dependencies(
    *,
    external_registry: ExternalEngineRegistry | None = None,
    storage_root: str | Path | None = None,
) -> dict[str, Any]:
    registry = external_registry or load_external_engine_registry(storage_root)
    lifelines = _package_status("lifelines")
    python_handoff = dependency_snapshot_handoff(
        registry,
        engine_family=PYTHON_STATISTICAL_ENGINE_FAMILY,
        required_capabilities=SURVIVAL_PYTHON_CAPABILITIES,
    )
    r_handoff = dependency_snapshot_handoff(
        registry,
        engine_family=R_BIOCONDUCTOR_ENGINE_FAMILY,
        required_capabilities=SURVIVAL_R_CAPABILITIES,
    )
    registry_checked = registry.query_engine_family(PYTHON_STATISTICAL_ENGINE_FAMILY) is not None
    blockers = [] if lifelines["available"] else ["lifelines_missing_formal_survival_disabled"]
    if registry_checked:
        blockers.extend(_missing_capability_blockers(python_handoff))
    return {
        "schema_version": "biomedpilot.survival_dependency_snapshot.v1",
        "python_lifelines": lifelines | {"capability_handoff": python_handoff},
        "external_dependency_registry": {
            "status": "checked" if registry_checked else "not_checked",
            "survival_handoff": python_handoff,
        },
        "r_survival": {
            "status": "detected" if registry.query_engine_family(R_BIOCONDUCTOR_ENGINE_FAMILY) is not None else "optional_not_configured",
            "packages": {"survival": "not_checked", "survminer": "not_checked"},
            "capability_handoff": r_handoff,
        },
        "status": "preflight_only" if blockers else "backend_available_but_not_enabled",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": ["survival_backend_detection_only_no_km_cox_logrank_execution"],
    }


def _package_status(name: str) -> dict[str, Any]:
    available = importlib.util.find_spec(name) is not None
    version = ""
    if available:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = "unknown"
    return {"available": available, "version": version}


def _missing_capability_blockers(handoff: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for row in handoff.get("capabilities", []) or []:
        if isinstance(row, dict) and row.get("status") != CAPABILITY_STATUS_AVAILABLE:
            blockers.append(f"missing_external_capability:{row.get('capability_key')}:{row.get('status')}")
    return blockers
