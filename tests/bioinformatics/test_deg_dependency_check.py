from __future__ import annotations

from app.bioinformatics.deg_engine import check_deg_backend_dependencies
from app.shared.local_engines import ExternalEngineRegistry


def test_deg_dependency_check_reports_packages_without_installing() -> None:
    snapshot = check_deg_backend_dependencies()

    assert snapshot["engine_candidate"] == "python_scipy_statsmodels"
    assert "scipy" in snapshot["packages"]
    assert "statsmodels" in snapshot["packages"]
    assert snapshot["r_backend"]["status"] == "optional_not_configured"


def test_deg_dependency_check_consumes_external_capability_registry() -> None:
    registry = ExternalEngineRegistry(
        (
            _snapshot("python_statistical", "package.python.scipy.available", "available"),
            _snapshot("r_bioconductor", "package.r.limma.available", "missing"),
        )
    )

    snapshot = check_deg_backend_dependencies(external_registry=registry)

    assert snapshot["external_dependency_registry"]["status"] == "checked"
    assert snapshot["external_dependency_registry"]["controlled_deg_handoff"]["snapshot_path"].endswith("python_statistical_snapshot.json")
    assert "missing_external_capability:package.python.statsmodels.available:unknown" in snapshot["blockers"]
    assert snapshot["r_backend"]["status"] == "detected"
    assert snapshot["r_backend"]["capability_handoff"]["all_required_available"] is False


def _snapshot(engine_family: str, capability_key: str, capability_status: str) -> dict[str, object]:
    return {
        "schema_version": "biomedpilot_external_engine_dependency_snapshot.v1",
        "engine_family": engine_family,
        "engine_name": engine_family,
        "status": "available" if capability_status == "available" else "partially_available",
        "runtime_path": "/usr/bin/env",
        "version": "1.0.0",
        "architecture": "arm64",
        "checked_at": "2026-05-22T00:00:00+00:00",
        "snapshot_path": f"/tmp/{engine_family}_snapshot.json",
        "packages": [
            {
                "name": capability_key,
                "required_for": ["test_runtime"],
                "status": capability_status,
                "version": "1.0.0" if capability_status == "available" else "",
                "minimum_version": "",
                "blocker": None if capability_status == "available" else {"code": "missing_dependency", "message": "missing", "required_by": ["test_runtime"]},
                "capability_key": capability_key,
            }
        ],
        "blockers": [] if capability_status == "available" else [{"code": "missing_dependency", "message": "missing", "required_by": ["test_runtime"]}],
        "install_guidance": {"safe_to_show": True, "commands": [], "manual_steps": []},
    }
