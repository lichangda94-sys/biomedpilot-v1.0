from __future__ import annotations

import importlib.util
from importlib import metadata
from typing import Any


REQUIRED_PACKAGES = ("numpy", "pandas", "scipy", "statsmodels")
OPTIONAL_BACKENDS = ("R", "limma", "DESeq2", "edgeR")
FORMAL_DEG_REQUIRED_PACKAGES = REQUIRED_PACKAGES


def check_deg_backend_dependencies() -> dict[str, Any]:
    packages = {name: _package_status(name) for name in REQUIRED_PACKAGES}
    missing = [name for name, status in packages.items() if not status["available"]]
    blockers = [f"missing_python_package:{name}" for name in missing]
    return {
        "schema_version": "biomedpilot.deg_dependency_snapshot.v2",
        "engine_candidate": "python_scipy_statsmodels",
        "dependency_policy": "formal_deg_requires_numpy_pandas_scipy_statsmodels",
        "required_for": "formal_deg_activation",
        "packages": packages,
        "r_backend": {"status": "optional_not_configured", "packages": {name: "not_checked" for name in OPTIONAL_BACKENDS}},
        "status": "blocked" if missing else "passed",
        "missing_packages": missing,
        "blockers": blockers,
        "warnings": ["r_backend_is_design_placeholder_not_called"],
        "missing_reason": "；".join(blockers) if blockers else "",
        "packaging_impact": _packaging_impact(missing),
        "install_action": "none_detect_first_only",
    }


def _package_status(name: str) -> dict[str, Any]:
    available = importlib.util.find_spec(name) is not None
    version = ""
    missing_reason = ""
    if available:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = "unknown"
    else:
        missing_reason = f"{name}_not_importable_in_current_runtime"
    return {
        "available": available,
        "installed": available,
        "version": version,
        "missing_reason": missing_reason,
        "required_for_formal_deg": name in FORMAL_DEG_REQUIRED_PACKAGES,
        "packaging_impact": "required_in_packaged_app_for_formal_deg" if name in FORMAL_DEG_REQUIRED_PACKAGES else "optional",
    }


def _packaging_impact(missing: list[str]) -> str:
    if missing:
        return "packaged_app_formal_deg_blocked_until_required_python_packages_are_bundled_or_present"
    return "packaged_app_formal_deg_dependency_detection_passed"
