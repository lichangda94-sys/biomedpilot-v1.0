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


REQUIRED_PACKAGES = ("numpy", "pandas", "scipy", "statsmodels")
OPTIONAL_BACKENDS = ("R", "limma", "DESeq2", "edgeR")
CONTROLLED_DEG_CAPABILITIES = ("package.python.scipy.available", "package.python.statsmodels.available")
R_DEG_CAPABILITIES = ("package.r.limma.available", "package.r.deseq2.available", "package.r.edger.available")


def check_deg_backend_dependencies(
    *,
    external_registry: ExternalEngineRegistry | None = None,
    storage_root: str | Path | None = None,
) -> dict[str, Any]:
    registry = external_registry or load_external_engine_registry(storage_root)
    packages = {name: _package_status(name) for name in REQUIRED_PACKAGES}
    missing = [name for name, status in packages.items() if not status["available"]]
    controlled_deg_handoff = dependency_snapshot_handoff(
        registry,
        engine_family=PYTHON_STATISTICAL_ENGINE_FAMILY,
        required_capabilities=CONTROLLED_DEG_CAPABILITIES,
    )
    r_handoff = dependency_snapshot_handoff(
        registry,
        engine_family=R_BIOCONDUCTOR_ENGINE_FAMILY,
        required_capabilities=R_DEG_CAPABILITIES,
    )
    registry_checked = registry.query_engine_family(PYTHON_STATISTICAL_ENGINE_FAMILY) is not None
    external_blockers = _missing_capability_blockers(controlled_deg_handoff) if registry_checked else []
    return {
        "schema_version": "biomedpilot.deg_dependency_snapshot.v1",
        "engine_candidate": "python_scipy_statsmodels",
        "packages": packages,
        "external_dependency_registry": {
            "status": "checked" if registry_checked else "not_checked",
            "controlled_deg_handoff": controlled_deg_handoff,
        },
        "r_backend": {
            "status": "detected" if registry.query_engine_family(R_BIOCONDUCTOR_ENGINE_FAMILY) is not None else "optional_not_configured",
            "packages": {name: "not_checked" for name in OPTIONAL_BACKENDS},
            "capability_handoff": r_handoff,
        },
        "status": "blocked" if missing or external_blockers else "passed",
        "blockers": [*[f"missing_python_package:{name}" for name in missing], *external_blockers],
        "warnings": ["r_backend_is_design_placeholder_not_called"],
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
