from __future__ import annotations

from app.shared import testing_mode


def test_testing_mode_summary_lists_testable_and_unavailable_features() -> None:
    summary = testing_mode.testing_mode_summary()
    assert summary["goal"]
    assert summary["testable_features"]
    assert summary["unavailable_features"]
    assert summary["feedback_location"]
    assert summary["lan_feedback_location"]


def test_generate_feedback_template(tmp_path) -> None:
    path = testing_mode.generate_feedback_template(tmp_path)
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "BioMedPilot Test Feedback" in content
    assert "Project Creation" in content


def test_lan_real_world_feedback_summary_keeps_real_lan_test_as_later_manual_checkpoint() -> None:
    summary = testing_mode.lan_real_world_feedback_summary()

    assert "真实用户" in str(summary["goal"])
    assert "界面完成后" in str(summary["goal"])
    assert any("Auth required" in step for step in summary["recommended_flow"])
    assert any("revoke" in step for step in summary["recommended_flow"])
    assert any("不启用 LAN sync" in check for check in summary["boundary_checks"])
    assert any("不自动扣减库存" in check for check in summary["boundary_checks"])
    assert summary["feedback_location"]


def test_generate_lan_feedback_template(tmp_path) -> None:
    path = testing_mode.generate_lan_feedback_template(tmp_path)

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "BioMedPilot LabTools LAN Real-Use Feedback" in content
    assert "Host Setup" in content
    assert "Client Connection" in content
    assert "Revoke Check" in content
    assert "Compatibility Mode Check" in content
    assert "no LAN writes" in content
    assert "no sync" in content
    assert "attach this Markdown file" in content
