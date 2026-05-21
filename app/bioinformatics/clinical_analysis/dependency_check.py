from __future__ import annotations

import importlib.util
from importlib import metadata
from typing import Any


def check_survival_backend_dependencies() -> dict[str, Any]:
    lifelines = _package_status("lifelines")
    passed = lifelines["available"] is True
    return {
        "schema_version": "biomedpilot.survival_dependency_snapshot.v1",
        "python_lifelines": lifelines,
        "r_survival": {"status": "optional_not_configured", "packages": {"survival": "not_checked", "survminer": "not_checked"}},
        "status": "passed" if passed else "preflight_only",
        "blockers": [] if passed else ["lifelines_missing_formal_survival_disabled"],
        "warnings": ["survival_backend_detect_first_no_auto_install"],
        "install_action": "none_detect_first_only",
        "packaging_impact": "lifelines_required_for_b13_controlled_km_logrank_runtime",
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
