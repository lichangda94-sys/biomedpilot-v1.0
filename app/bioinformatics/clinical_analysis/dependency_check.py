from __future__ import annotations

import importlib.util
from importlib import metadata
from typing import Any


def check_survival_backend_dependencies() -> dict[str, Any]:
    lifelines = _package_status("lifelines")
    return {
        "schema_version": "biomedpilot.survival_dependency_snapshot.v1",
        "python_lifelines": lifelines,
        "r_survival": {"status": "optional_not_configured", "packages": {"survival": "not_checked", "survminer": "not_checked"}},
        "status": "preflight_only" if not lifelines["available"] else "backend_available_but_not_enabled",
        "blockers": [] if lifelines["available"] else ["lifelines_missing_formal_survival_disabled"],
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
