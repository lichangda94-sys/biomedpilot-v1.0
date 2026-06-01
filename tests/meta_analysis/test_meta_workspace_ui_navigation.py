from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QFrame, QPushButton

    from app.meta_analysis.project_workspace import META_PROJECT_DIRECTORIES, create_meta_analysis_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget, meta_target_ia_pages, meta_workspace_layout_state
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


def test_meta_workspace_layout_state_uses_uishell_target_ia() -> None:
    state = meta_workspace_layout_state()

    assert state.title == "Meta 分析模块"
    assert state.default_page_key == "target_ia"
    assert [item.page_key for item in state.navigation_items] == ["target_ia"]
    assert "旧页面仅作为后端能力来源" in state.testing_notice


def test_meta_workspace_mounts_target_ia_runtime_pages(qt_app, tmp_path: Path) -> None:
    summary = create_meta_analysis_project("Mounted Target IA", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    assert widget.meta_workspace_layout_state()["current_step_workspace"] == "metaCurrentStepWorkspace"
    assert widget.page_keys() == ("target_ia",)
    assert widget.target_ia_page_keys() == tuple(page.key for page in meta_target_ia_pages())
    frames = {frame.objectName() for frame in widget.findChildren(QFrame)}
    assert {
        "metaTargetIAShell",
        "metaProjectHomeRuntimePanel",
        "metaQuestionTypeDraftPanel",
        "metaSearchStrategyRuntimePanel",
        "metaReferenceDedupRuntimePanel",
        "metaScreeningRuntimePanel",
        "metaFulltextExtractionPanel",
        "metaRiskOfBiasRuntimePanel",
        "metaResultReviewRuntimePanel",
        "metaReportExportGateRuntimePanel",
    } <= frames


def test_meta_workspace_creates_meta_project_from_form(qt_app, tmp_path: Path) -> None:
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_new_project_form(project_name="高血压 Meta", research_topic="降压治疗", save_location=tmp_path)

    summary = widget.create_meta_project_from_form()

    assert summary is not None
    assert widget.current_project_dir() == summary.project_root
    for directory in META_PROJECT_DIRECTORIES:
        assert (summary.project_root / directory).is_dir()


def test_meta_workspace_target_ia_navigation_and_button_contracts(qt_app, tmp_path: Path) -> None:
    summary = create_meta_analysis_project("Button Contracts", tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(summary.project_root)

    for page_key in widget.target_ia_page_keys():
        widget.show_target_ia_page(page_key)
        assert widget.current_target_page_key() == page_key

    gaps: list[str] = []
    for button in widget.findChildren(QPushButton):
        if button.property("buttonBehavior") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-buttonBehavior")
        if not button.isEnabled() and button.property("disabledReason") is None:
            gaps.append(f"{button.objectName()}:{button.text()}:missing-disabledReason")
        assert button.property("formalActionEnabled") is False
    assert gaps == []
