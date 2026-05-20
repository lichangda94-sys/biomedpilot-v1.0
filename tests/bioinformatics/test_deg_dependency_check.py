from __future__ import annotations

from app.bioinformatics.deg_engine import check_deg_backend_dependencies


def test_deg_dependency_check_reports_packages_without_installing() -> None:
    snapshot = check_deg_backend_dependencies()

    assert snapshot["engine_candidate"] == "python_scipy_statsmodels"
    assert snapshot["dependency_policy"] == "formal_deg_requires_numpy_pandas_scipy_statsmodels"
    assert snapshot["required_for"] == "formal_deg_activation"
    assert "scipy" in snapshot["packages"]
    assert "statsmodels" in snapshot["packages"]
    assert "missing_reason" in snapshot["packages"]["scipy"]
    assert "packaging_impact" in snapshot["packages"]["statsmodels"]
    assert snapshot["install_action"] == "none_detect_first_only"
    assert snapshot["r_backend"]["status"] == "optional_not_configured"
