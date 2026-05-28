from __future__ import annotations

import importlib
import importlib.util
from importlib import metadata
from typing import Any


REQUIRED_ORA_PACKAGES = ("scipy", "statsmodels")


def check_ora_backend_dependencies() -> dict[str, Any]:
    packages = {name: _package_status(name) for name in REQUIRED_ORA_PACKAGES}
    missing = [name for name, status in packages.items() if not status["available"]]
    blockers = [f"missing_python_package:{name}" for name in missing]
    return {
        "schema_version": "biomedpilot.ora_dependency_snapshot.v1",
        "engine_candidate": "python_scipy_statsmodels_ora_mvp",
        "dependency_policy": "controlled_ora_requires_scipy_statsmodels",
        "required_for": "controlled_ora_execution",
        "packages": packages,
        "status": "blocked" if missing else "passed",
        "missing_packages": missing,
        "blockers": blockers,
        "warnings": [],
        "missing_reason": "; ".join(blockers) if blockers else "",
        "packaging_impact": "packaged_app_controlled_ora_blocked_until_scipy_statsmodels_available" if missing else "packaged_app_controlled_ora_dependency_detection_passed",
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
        except Exception as exc:  # pragma: no cover - broken native packages depend on local runtime.
            import_error = f"{exc.__class__.__name__}: {exc}"
    version = ""
    if available:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = str(getattr(module, "__version__", "") or "unknown")
    return {
        "available": available,
        "installed": available,
        "spec_found": found,
        "importable": available,
        "version": version,
        "missing_reason": "" if available else import_error or f"{name}_not_importable_in_current_runtime",
        "required_for_controlled_ora": True,
        "packaging_impact": "required_in_packaged_app_for_controlled_ora",
    }
