from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame

    from app.bioinformatics.workspace import (
        BioinformaticsWorkspaceWidget,
        bioinformatics_auxiliary_pages,
        bioinformatics_legacy_routes,
        bioinformatics_main_flow_pages,
        bioinformatics_target_ia_pages,
    )
    from app.shared.semantic_keys import AnalysisStatusKey, ModuleKey, PageKey, ReportStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QFrame = None  # type: ignore[assignment]
    BioinformaticsWorkspaceWidget = None  # type: ignore[assignment]
    bioinformatics_target_ia_pages = None  # type: ignore[assignment]
    bioinformatics_main_flow_pages = None  # type: ignore[assignment]
    bioinformatics_auxiliary_pages = None  # type: ignore[assignment]
    bioinformatics_legacy_routes = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def bio_workspace(qt_app):
    widget = BioinformaticsWorkspaceWidget()
    yield widget
    widget.close()
    widget.deleteLater()
    qt_app.processEvents()


def test_bioinformatics_target_ia_pages_are_consolidated() -> None:
    pages = bioinformatics_target_ia_pages()

    assert [page.key for page in pages] == [
        "project_home",
        "data_source",
        "data_check_preparation",
        "group_design",
        "analysis_tasks",
        "result_report",
        "report_export",
        "settings_resources",
        "project_logs_technical_details",
    ]
    assert [page.key for page in bioinformatics_main_flow_pages()] == [
        "project_home",
        "data_source",
        "data_check_preparation",
        "group_design",
        "analysis_tasks",
        "result_report",
        "report_export",
    ]
    assert [page.key for page in bioinformatics_auxiliary_pages()] == [
        "settings_resources",
        "project_logs_technical_details",
    ]
    assert [page.flow_index for page in bioinformatics_main_flow_pages()] == list(range(1, 8))
    assert [page.flow_index for page in bioinformatics_auxiliary_pages()] == [1, 2]
    assert pages[2].semantic_key == AnalysisStatusKey.PREFLIGHT_ONLY.value
    assert pages[5].semantic_key == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert pages[6].semantic_key == ReportStatusKey.TESTING_SUMMARY.value


def test_bioinformatics_workspace_renders_target_ia_shell(bio_workspace) -> None:
    title = bio_workspace.findChild(QLabel, "bioinformaticsIATitle")
    subtitle = bio_workspace.findChild(QLabel, "bioinformaticsIASubtitle")
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")

    assert title is not None
    assert title.text() == "生信分析 / Bioinformatics"
    assert subtitle is not None
    assert "一站式分析与可视化" in subtitle.text()
    assert len(nav_items) == 9
    assert tuple(item.property("pageKey") for item in nav_items) == bio_workspace.target_ia_page_keys()
    assert tuple(item.property("pageKey") for item in nav_items if item.property("pageGroup") == "main_flow") == (
        bio_workspace.main_flow_page_keys()
    )
    assert tuple(item.property("pageKey") for item in nav_items if item.property("pageGroup") == "auxiliary") == (
        bio_workspace.auxiliary_page_keys()
    )
    assert all(not item.isEnabled() for item in nav_items)


def test_bioinformatics_nav_items_carry_status_and_semantic_keys(bio_workspace) -> None:
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")
    by_page = {item.property("pageKey"): item for item in nav_items}

    assert by_page["data_check_preparation"].property("statusKey") == "preflight_only"
    assert by_page["data_check_preparation"].property("semanticKey") == PageKey.BIO_DATA_CHECK_PREPARATION.value
    assert by_page["data_check_preparation"].property("statusSemanticKey") == AnalysisStatusKey.PREFLIGHT_ONLY.value
    assert by_page["analysis_tasks"].property("statusKey") == "blocked"
    assert by_page["analysis_tasks"].property("semanticKey") == PageKey.BIO_ANALYSIS_TASKS.value
    assert by_page["analysis_tasks"].property("statusSemanticKey") == AnalysisStatusKey.BLOCKED.value
    assert by_page["result_report"].property("semanticKey") == PageKey.BIO_RESULT_REPORT.value
    assert by_page["result_report"].property("statusSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert by_page["report_export"].property("statusKey") == "draft"
    assert by_page["report_export"].property("semanticKey") == PageKey.BIO_REPORT_EXPORT.value
    assert by_page["report_export"].property("statusSemanticKey") == ReportStatusKey.TESTING_SUMMARY.value
    assert by_page["result_report"].property("pageGroup") == "main_flow"
    assert by_page["result_report"].property("flowIndex") == 6
    assert by_page["result_report"].property("moduleKey") == ModuleKey.BIOINFORMATICS.value
    assert by_page["settings_resources"].property("pageGroup") == "auxiliary"
    assert by_page["settings_resources"].property("semanticKey") == PageKey.BIO_SETTINGS_RESOURCES.value


def test_bioinformatics_shell_copy_keeps_user_facing_flow_and_quick_access(bio_workspace) -> None:
    labels = "\n".join(label.text() for label in bio_workspace.findChildren(QLabel))
    tooltips = "\n".join(button.toolTip() for button in bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem"))
    quick_buttons = bio_workspace.findChildren(QPushButton, "quickAccessButton")

    assert "生信分析流程概览 / Workflow Overview" in labels
    assert [button.property("quickAccessKey") for button in quick_buttons] == ["最近使用", "使用指南", "常见问题", "意见反馈"]
    assert "Architecture Boundaries" not in labels
    assert "resolver-first" not in labels
    assert "preflight-first" not in labels
    assert "result-schema-first" not in labels
    assert "TCGA+GTEx 不自动合并" not in tooltips


def test_bioinformatics_adopts_shared_result_report_export_shell(bio_workspace) -> None:
    panel = bio_workspace.findChild(QFrame, "resultReportExportAdoptionPanel")

    assert panel is not None
    buttons = panel.findChildren(QPushButton, "exportGatedButton")
    assert panel.property("adoptionModule") == "bioinformatics"
    assert panel.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert panel.property("reportStatusKey") == ReportStatusKey.DRAFT.value
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("reportReadyPackageAllowed") is False
    assert [button.property("exportFormatKey") for button in buttons] == [
        "export.format.markdown",
        "export.format.html",
        "export.format.docx",
    ]
    assert all(not button.isEnabled() for button in buttons)


def test_bioinformatics_legacy_routes_are_mapped_to_target_pages() -> None:
    routes = bioinformatics_legacy_routes()
    by_route = {route.route_key: route for route in routes}

    assert by_route["recognition"].target_page_key == "data_check_preparation"
    assert by_route["recognition"].legacy_status == "folded_into_target"
    assert by_route["readiness"].target_page_key == "data_check_preparation"
    assert by_route["readiness"].visibility == "developer_diagnostic"
    assert by_route["workflow_status"].target_page_key == "project_logs_technical_details"
    assert by_route["workflow_status"].legacy_status == "developer_diagnostic"
    assert by_route["analysis_tasks"].legacy_status == "gated_target"
    assert by_route["results_browser"].target_page_key == "result_report"
    assert by_route["report_viewer"].target_page_key == "report_export"


def test_bioinformatics_workspace_exposes_legacy_route_calibration(bio_workspace) -> None:
    route_items = bio_workspace.findChildren(QPushButton, "bioinformaticsLegacyRouteItem")

    assert route_items == []
    calibration = {item["route_key"]: item for item in bio_workspace.legacy_route_calibration()}
    assert tuple(calibration) == bio_workspace.legacy_route_keys()
    assert calibration["recognition"]["target_page_key"] == "data_check_preparation"
    assert calibration["workflow_status"]["target_page_key"] == "project_logs_technical_details"
    assert calibration["workflow_status"]["visibility"] == "developer_diagnostic"


def test_bioinformatics_result_report_highlights_step_six_without_meta_context(bio_workspace) -> None:
    bio_workspace.show_results_browser()
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")
    by_page = {item.property("pageKey"): item for item in nav_items}
    labels = "\n".join(label.text() for label in bio_workspace.findChildren(QLabel))

    assert by_page["result_report"].isChecked()
    assert by_page["result_report"].property("flowIndex") == 6
    assert by_page["result_report"].property("moduleKey") == ModuleKey.BIOINFORMATICS.value
    assert "PubMed" not in labels
    assert "文献筛选" not in labels
    assert "forest plot" not in labels


def test_bioinformatics_legacy_navigation_sets_current_target_metadata(bio_workspace) -> None:
    bio_workspace.show_recognition()
    assert bio_workspace.current_page_object_name() == "bioinformaticsRecognitionPage"
    assert bio_workspace.current_route_key() == "recognition"
    assert bio_workspace.current_target_page_key() == "data_check_preparation"
    assert bio_workspace.current_route_status() == "folded_into_target"

    bio_workspace.show_workflow_status()
    assert bio_workspace.current_page_object_name() == "bioinformaticsWorkflowStatusPage"
    assert bio_workspace.current_route_key() == "workflow_status"
    assert bio_workspace.current_target_page_key() == "project_logs_technical_details"
    assert bio_workspace.current_route_status() == "developer_diagnostic"
    assert bio_workspace.current_route_visibility() == "developer_diagnostic"
