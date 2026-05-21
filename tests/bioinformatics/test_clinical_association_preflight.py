from __future__ import annotations

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, check_survival_backend_dependencies


def test_clinical_association_preflight_detects_variable_types() -> None:
    preflight = build_clinical_association_preflight(
        [
            {"age": "50", "sex": "F", "OS_time": "10", "OS_event": "1"},
            {"age": "60", "sex": "M", "OS_time": "20", "OS_event": "0"},
        ]
    )

    assert preflight["variable_mapping"]["age"]["variable_type"] == "continuous_variable"
    assert preflight["variable_mapping"]["sex"]["variable_type"] == "categorical_variable"
    assert preflight["variable_mapping"]["OS_time"]["variable_type"] == "time_to_event_variable"
    assert preflight["status"] == "design_preflight_only"


def test_survival_dependency_missing_is_blocker_not_traceback() -> None:
    snapshot = check_survival_backend_dependencies()

    assert "python_lifelines" in snapshot
    assert snapshot["warnings"] == ["survival_backend_detect_first_no_auto_install"]
    assert snapshot["install_action"] == "none_detect_first_only"
