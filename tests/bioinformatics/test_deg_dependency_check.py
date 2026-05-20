from __future__ import annotations

from app.bioinformatics.deg_engine import check_deg_backend_dependencies


def test_deg_dependency_check_reports_packages_without_installing() -> None:
    snapshot = check_deg_backend_dependencies()

    assert snapshot["engine_candidate"] == "python_scipy_statsmodels"
    assert "scipy" in snapshot["packages"]
    assert "statsmodels" in snapshot["packages"]
    assert snapshot["r_backend"]["status"] == "optional_not_configured"
