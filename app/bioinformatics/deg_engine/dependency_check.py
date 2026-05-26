from __future__ import annotations

import importlib.util
import importlib
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
FORMAL_DEG_REQUIRED_PACKAGES = REQUIRED_PACKAGES
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
    blockers = [*[f"missing_python_package:{name}" for name in missing], *external_blockers]
    return {
        "schema_version": "biomedpilot.deg_dependency_snapshot.v2",
        "engine_candidate": "python_scipy_statsmodels",
        "dependency_policy": "formal_deg_requires_numpy_pandas_scipy_statsmodels",
        "required_for": "formal_deg_activation",
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
        "status": "blocked" if blockers else "passed",
        "missing_packages": missing,
        "blockers": blockers,
        "warnings": ["r_backend_is_design_placeholder_not_called"],
        "missing_reason": "；".join(blockers) if blockers else "",
        "packaging_impact": _packaging_impact(missing),
        "install_action": "none_detect_first_only",
    }


def _package_status(name: str) -> dict[str, Any]:
    found = importlib.util.find_spec(name) is not None
    import_error = ""
    available = False
    module: Any | None = None
    if found:
        try:
            module = importlib.import_module(name)
            available = True
        except Exception as exc:  # pragma: no cover - depends on broken native package installs.
            import_error = f"{exc.__class__.__name__}: {exc}"
    version = ""
    missing_reason = ""
    if available:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = str(getattr(module, "__version__", "") or "unknown")
    else:
        missing_reason = import_error or f"{name}_not_importable_in_current_runtime"
    return {
        "available": available,
        "installed": available,
        "spec_found": found,
        "importable": available,
        "version": version,
        "missing_reason": missing_reason,
        "required_for_formal_deg": name in FORMAL_DEG_REQUIRED_PACKAGES,
        "packaging_impact": "required_in_packaged_app_for_formal_deg" if name in FORMAL_DEG_REQUIRED_PACKAGES else "optional",
    }


def _packaging_impact(missing: list[str]) -> str:
    if missing:
        return "packaged_app_formal_deg_blocked_until_required_python_packages_are_bundled_or_present"
    return "packaged_app_formal_deg_dependency_detection_passed"


def _missing_capability_blockers(handoff: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for row in handoff.get("capabilities", []) or []:
        if isinstance(row, dict) and row.get("status") != CAPABILITY_STATUS_AVAILABLE:
            blockers.append(f"missing_external_capability:{row.get('capability_key')}:{row.get('status')}")
    return blockers
