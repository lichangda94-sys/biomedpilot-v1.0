from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget, meta_workspace_layout_state
    from app.shared.project_center.service import ProjectRecord
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_mainline_meta_layout_is_uishell_target_ia_contract() -> None:
    state = meta_workspace_layout_state()

    assert state.default_page_key == "target_ia"
    assert [item.page_key for item in state.navigation_items] == ["target_ia"]
    assert "UIShell" in state.description
    assert "旧页面仅作为后端能力来源" in state.testing_notice


def test_mainline_meta_workspace_binds_project_record_to_target_ia(qt_app, tmp_path) -> None:
    project = create_meta_analysis_project("Meta UI", tmp_path)
    record = ProjectRecord(
        project_id="meta-ui",
        project_name="Meta UI",
        project_type="meta_analysis",
        created_at="2026-05-11T00:00:00+08:00",
        updated_at="2026-05-11T00:00:00+08:00",
        project_dir=str(project.project_root),
        current_stage="created",
        status="active",
    )
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_record(record)

    assert widget.current_project_dir() == project.project_root
    assert widget.page_keys() == ("target_ia",)
    assert widget.target_ia_page_keys()[:4] == (
        "project_home",
        "question_meta_type",
        "search_strategy",
        "import_dedup",
    )
    assert widget.meta_workspace_layout_state()["contract_version"]
