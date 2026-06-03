from __future__ import annotations

import os
import json

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame

    from app.bioinformatics.workflow_pages import BioinformaticsDataSourceWidget
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
    BioinformaticsDataSourceWidget = None  # type: ignore[assignment]
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


@pytest.fixture
def data_source_widget(qt_app):
    widget = BioinformaticsDataSourceWidget()
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
    assert pages[2].semantic_key == AnalysisStatusKey.PREFLIGHT_ONLY.value
    assert pages[5].semantic_key == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert pages[6].semantic_key == ReportStatusKey.TESTING_SUMMARY.value


def test_bioinformatics_workspace_renders_high_fidelity_mockup_sourced_shell(bio_workspace) -> None:
    title = bio_workspace.findChild(QLabel, "bioinformaticsIATitle")
    subtitle = bio_workspace.findChild(QLabel, "bioinformaticsIASubtitle")
    stepper = bio_workspace.findChild(QFrame, "bioinformaticsWorkflowStepper")
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")

    assert title is not None
    assert title.text() == "生信分析 / Bioinformatics"
    assert subtitle is not None
    assert "一站式分析与可视化" in subtitle.text()
    assert stepper is not None
    assert stepper.property("uiPrimitive") == "workflow_stepper"
    assert stepper.property("moduleKey") == ModuleKey.BIOINFORMATICS.value
    assert stepper.property("formalActionEnabled") is False
    assert len(nav_items) == 9
    assert tuple(item.property("pageKey") for item in nav_items) == bio_workspace.target_ia_page_keys()
    assert all(item.isEnabled() for item in nav_items)
    assert all(item.property("formalActionEnabled") is False for item in nav_items)
    assert all(str(item.property("buttonBehavior")).startswith("navigates_to_bio_target_ia_page_") for item in nav_items)


def test_bioinformatics_project_home_disabled_quick_access_buttons_explain_reason(bio_workspace) -> None:
    buttons = bio_workspace.findChildren(QPushButton, "quickAccessButton")

    assert {button.property("quickAccessKey") for button in buttons} == {"最近使用", "使用指南", "常见问题", "意见反馈"}
    assert all(not button.isEnabled() for button in buttons)
    assert all(button.property("disabledReason") for button in buttons)


def test_bioinformatics_nav_items_carry_status_and_semantic_keys(bio_workspace) -> None:
    by_page = {item.property("pageKey"): item for item in bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")}

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


def test_bioinformatics_ia_nav_items_live_click_target_pages(bio_workspace) -> None:
    by_page = {item.property("pageKey"): item for item in bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")}

    for page_key in bio_workspace.target_ia_page_keys():
        bio_workspace.show_project_home()
        by_page[page_key].click()

        assert bio_workspace.current_target_page_key() == page_key
        assert by_page[page_key].property("currentStep") is True


def test_bioinformatics_legacy_routes_are_mapped_to_target_pages() -> None:
    by_route = {route.route_key: route for route in bioinformatics_legacy_routes()}

    assert by_route["recognition"].target_page_key == "data_check_preparation"
    assert by_route["recognition"].legacy_status == "folded_into_target"
    assert by_route["readiness"].target_page_key == "data_check_preparation"
    assert by_route["readiness"].visibility == "developer_diagnostic"
    assert by_route["group_design"].target_page_key == "group_design"
    assert by_route["group_design"].legacy_status == "target_page"
    assert by_route["group_design"].visibility == "primary"
    assert by_route["workflow_status"].target_page_key == "project_logs_technical_details"
    assert by_route["analysis_tasks"].legacy_status == "gated_target"
    assert by_route["results_browser"].target_page_key == "result_report"
    assert by_route["report_viewer"].target_page_key == "report_export"


def test_bioinformatics_navigation_sets_current_target_metadata(bio_workspace) -> None:
    bio_workspace.show_recognition()
    assert bio_workspace.current_page_object_name() == "bioinformaticsRecognitionPage"
    assert bio_workspace.current_route_key() == "recognition"
    assert bio_workspace.current_target_page_key() == "data_check_preparation"
    assert bio_workspace.current_route_status() == "folded_into_target"

    bio_workspace.show_results_browser()
    assert bio_workspace.current_page_object_name() == "bioinformaticsResultsBrowserPage"
    assert bio_workspace.current_route_key() == "results_browser"
    assert bio_workspace.current_target_page_key() == "result_report"
    assert bio_workspace.current_route_status() == "testing_summary"

    by_page = {item.property("pageKey"): item for item in bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")}
    assert by_page["result_report"].isChecked()
    assert by_page["result_report"].property("currentStep") is True
    assert by_page["project_home"].property("currentStep") is False

    bio_workspace.show_group_design()
    assert bio_workspace.current_page_object_name() == "bioinformaticsGroupComparisonDesignPage"
    assert bio_workspace.current_route_key() == "group_design"
    assert bio_workspace.current_target_page_key() == "group_design"
    assert bio_workspace.current_route_status() == "target_page"
    assert by_page["group_design"].isChecked()
    assert by_page["group_design"].property("currentStep") is True


def test_data_source_page_uses_high_fidelity_mockup_sourced_gated_shell(data_source_widget) -> None:
    source_cards = data_source_widget.findChildren(QFrame, "bioinformaticsDataSourceMainCard")
    source_buttons = data_source_widget.findChildren(QPushButton, "bioinformaticsDataSourceSelectPreviewButton")
    research_card = data_source_widget.findChild(QFrame, "bioinformaticsDataSourceResearchCard")

    assert len(source_cards) == 4
    assert tuple(card.property("sourceKey") for card in source_cards) == ("geo", "tcga", "gtex", "local_file")
    assert {button.property("sourceKey") for button in source_buttons} == {"geo", "tcga", "gtex", "local_file"}
    assert all(button.property("formalActionEnabled") is False for button in source_buttons)
    assert all(button.property("buttonBehavior") == "creates_data_source_request_draft_when_project_open" for button in source_buttons)
    assert research_card is not None
    assert research_card.property("formalActionEnabled") is False


def test_data_source_buttons_explain_disabled_reason_without_project(data_source_widget) -> None:
    geo_button = next(
        button for button in data_source_widget.findChildren(QPushButton, "bioinformaticsDataSourceSelectPreviewButton")
        if button.property("sourceKey") == "geo"
    )

    geo_button.click()

    assert "请先创建或打开生信分析项目" in data_source_widget.status_message()
    assert data_source_widget.latest_data_source_request_path() is None


def test_data_source_button_generates_request_artifact_when_project_open(data_source_widget, tmp_path) -> None:
    data_source_widget.refresh_project(tmp_path)
    tcga_button = next(
        button for button in data_source_widget.findChildren(QPushButton, "bioinformaticsDataSourceSelectPreviewButton")
        if button.property("sourceKey") == "tcga"
    )

    tcga_button.click()

    request_path = data_source_widget.latest_data_source_request_path()
    assert request_path is not None
    assert request_path.exists()
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert request_payload["source_type"] == "tcga"
    assert request_payload["status"] == "draft"
    assert "expression_matrix" in request_payload["expected_assets"]
    assert any("TCGA+GTEx" in warning for warning in request_payload["warnings"])
    index_path = tmp_path / "manifests" / "data_source_requests.json"
    assert index_path.exists()


def test_data_source_tcga_and_gtex_adapter_controls_are_isolated(data_source_widget, tmp_path) -> None:
    data_source_widget.refresh_project(tmp_path)
    buttons = {
        button.property("sourceKey"): button
        for button in data_source_widget.findChildren(QPushButton, "bioinformaticsDataSourceSelectPreviewButton")
    }

    buttons["tcga"].click()
    tcga_controls = data_source_widget.findChild(QFrame, "bioinformaticsTcgaAdapterControls")
    gtex_controls = data_source_widget.findChild(QFrame, "bioinformaticsGtexAdapterControls")
    assert tcga_controls is not None
    assert gtex_controls is not None
    assert not tcga_controls.isHidden()
    assert gtex_controls.isHidden()

    buttons["gtex"].click()
    assert tcga_controls.isHidden()
    assert not gtex_controls.isHidden()
