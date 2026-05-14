from __future__ import annotations

from app.shell.dashboard import build_dashboard_model


def test_dashboard_model_loads() -> None:
    dashboard = build_dashboard_model()
    assert dashboard.product_name == "BioMedPilot / 医研智析"
    assert "Bioinformatics Analysis" in dashboard.product_subtitle
    assert dashboard.bioinformatics_features
    assert dashboard.meta_analysis_features
    assert dashboard.labtools_features


def test_unified_entry_console_smoke() -> None:
    from app.main import main

    assert callable(main)


def test_unified_entry_ignores_launchservices_psn_argument() -> None:
    from app.main import parse_args

    args = parse_args(["-psn_0_12345", "--smoke-test"])

    assert args.smoke_test is True
