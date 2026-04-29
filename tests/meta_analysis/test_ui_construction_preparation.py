from __future__ import annotations

from pathlib import Path

from app.meta_analysis.services.ui_construction_readiness_service import build_meta_ui_construction_readiness


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ui_construction_readiness_lists_reusable_page_states() -> None:
    state = build_meta_ui_construction_readiness(REPO_ROOT)

    assert state.status_label == "Developer Preview / testing"
    assert state.ready_for_ui_construction is True
    assert state.reusable_page_state_count >= 9
    step_ids = {item.step_id for item in state.page_items}
    assert {"workflow_dashboard", "literature_import", "extraction", "quality", "analysis", "reporting"} <= step_ids
    assert state.high_risk_page_count >= 4


def test_ui_construction_readiness_keeps_constraints_and_acceptance_checks() -> None:
    state = build_meta_ui_construction_readiness(REPO_ROOT)
    constraints = " ".join(state.global_constraints)
    checks = " ".join(state.acceptance_checks)

    assert "Do not modify Bioinformatics" in constraints
    assert "Developer Preview / testing" in constraints
    assert "Do not implement automatic PDF download" in constraints
    assert "Missing artifacts show empty/warning states" in checks
    assert "Extraction and Quality pages" in checks


def test_ui_construction_preparation_docs_exist() -> None:
    prep = REPO_ROOT / "docs" / "meta_ui_construction_preparation.md"
    report = REPO_ROOT / "docs" / "meta_dev_reports" / "ui_construction_preparation_report.md"

    assert prep.exists()
    assert report.exists()
    prep_text = prep.read_text(encoding="utf-8")
    report_text = report.read_text(encoding="utf-8")
    assert "Construction Sequence" in prep_text
    assert "High-Risk UI Areas" in prep_text
    assert "Recommended Next Step" in report_text
    assert "Developer Preview / testing" in report_text
