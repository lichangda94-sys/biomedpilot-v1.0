from __future__ import annotations

from app.shared import testing_mode


def test_testing_mode_summary_lists_testable_and_unavailable_features() -> None:
    summary = testing_mode.testing_mode_summary()
    assert summary["goal"]
    assert summary["testable_features"]
    assert summary["unavailable_features"]
    assert summary["feedback_location"]


def test_generate_feedback_template(tmp_path) -> None:
    path = testing_mode.generate_feedback_template(tmp_path)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "BioMedPilot Test Feedback" in content
    assert "Project Creation" in content
