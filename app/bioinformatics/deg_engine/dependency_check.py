from __future__ import annotations

import importlib.util
from importlib import metadata
from typing import Any


REQUIRED_PACKAGES = ("numpy", "pandas", "scipy", "statsmodels")
OPTIONAL_BACKENDS = ("R", "limma", "DESeq2", "edgeR")


def check_deg_backend_dependencies() -> dict[str, Any]:
    packages = {name: _package_status(name) for name in REQUIRED_PACKAGES}
    missing = [name for name, status in packages.items() if not status["available"]]
    return {
        "schema_version": "biomedpilot.deg_dependency_snapshot.v1",
        "engine_candidate": "python_scipy_statsmodels",
        "packages": packages,
        "r_backend": {"status": "optional_not_configured", "packages": {name: "not_checked" for name in OPTIONAL_BACKENDS}},
        "status": "blocked" if missing else "passed",
        "blockers": [f"missing_python_package:{name}" for name in missing],
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
