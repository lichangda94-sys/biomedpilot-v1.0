from __future__ import annotations

import importlib

from app.bioinformatics.deg_engine import check_deg_backend_dependencies
from app.bioinformatics.deg_engine.dependency_check import _package_status


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


def test_package_status_blocks_when_spec_exists_but_import_fails(monkeypatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str, package: str | None = None):
        if name == "numpy":
            raise ImportError("incompatible architecture")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    status = _package_status("numpy")

    assert status["spec_found"] is True
    assert status["available"] is False
    assert status["importable"] is False
    assert "incompatible architecture" in status["missing_reason"]
