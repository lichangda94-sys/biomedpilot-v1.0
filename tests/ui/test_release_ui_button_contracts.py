from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.bioinformatics.pages.enrichment_page import EnrichmentPage
    from app.bioinformatics.pages.survival_page import SurvivalPage
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workflow_pages import (
        BioinformaticsAcquisitionStatusWidget,
        BioinformaticsAnalysisTaskCenterWidget,
        BioinformaticsChineseDatasetSearchWidget,
        BioinformaticsDataSourceWidget,
        BioinformaticsGroupComparisonDesignWidget,
        BioinformaticsReadinessDashboardWidget,
        BioinformaticsRecognitionWidget,
        BioinformaticsReportViewerWidget,
        BioinformaticsResultsBrowserWidget,
        BioinformaticsSettingsAndLocalAIWidget,
        BioinformaticsStandardizedAssetsWidget,
        BioinformaticsWorkflowStatusWidget,
    )
    from app.labtools.workspace import LabToolsWorkspaceWidget
    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
    from app.shared.data_center.service import DataCenter
    from app.shared.project_center.service import ProjectCenter
    from app.shared.task_center.service import TaskCenter
    from app.shell.centers_page import build_centers_page
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _assert_buttons_have_release_contract(widget, *, scope: str) -> None:
    gaps: list[str] = []
    for button in widget.findChildren(QPushButton):
        if button.property("buttonBehavior") is None:
            gaps.append(f"{scope}:{button.objectName()}:{button.text()}:missing-buttonBehavior")
        if not button.isEnabled() and button.property("disabledReason") is None:
            gaps.append(f"{scope}:{button.objectName()}:{button.text()}:missing-disabledReason")
    assert gaps == []


def test_release_ui_button_contracts_cover_labtools_bio_meta_and_centers(qt_app, tmp_path: Path) -> None:
    labtools = LabToolsWorkspaceWidget()
    for page_key in labtools.page_keys():
        if page_key == "home":
            labtools.show_home()
        else:
            labtools._show_page(page_key)
        _assert_buttons_have_release_contract(labtools.current_page_widget(), scope=f"labtools:{page_key}")

    bio_project = create_bioinformatics_project("Release Contract Bio", tmp_path / "bio")
    bio_pages = [
        BioinformaticsDataSourceWidget(),
        BioinformaticsChineseDatasetSearchWidget(),
        BioinformaticsAcquisitionStatusWidget(),
        BioinformaticsRecognitionWidget(),
        BioinformaticsReadinessDashboardWidget(),
        BioinformaticsStandardizedAssetsWidget(),
        BioinformaticsGroupComparisonDesignWidget(),
        BioinformaticsWorkflowStatusWidget(),
        BioinformaticsAnalysisTaskCenterWidget(),
        BioinformaticsResultsBrowserWidget(),
        BioinformaticsReportViewerWidget(),
        BioinformaticsSettingsAndLocalAIWidget(),
        EnrichmentPage(),
        SurvivalPage(),
    ]
    for page in bio_pages:
        if hasattr(page, "refresh_project"):
            page.refresh_project(bio_project)
        _assert_buttons_have_release_contract(page, scope=f"bio:{page.objectName()}")

    meta_project = create_meta_analysis_project("Release Contract Meta", tmp_path / "meta")
    meta = MetaAnalysisWorkspaceWidget()
    meta.set_project_dir(meta_project.project_root)
    for page_key in meta.page_keys():
        meta.show_step(page_key)
        _assert_buttons_have_release_contract(meta._page_stack.currentWidget().widget(), scope=f"meta:{page_key}")

    centers = build_centers_page(
        project_center=ProjectCenter(tmp_path / "centers" / "projects.json"),
        data_center=DataCenter(tmp_path / "centers" / "data_assets.json"),
        task_center=TaskCenter(tmp_path / "centers" / "tasks.json"),
    )
    _assert_buttons_have_release_contract(centers, scope="shell:centers")
