from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame

    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget, meta_active_types_v1, meta_target_ia_pages
    from app.shared.semantic_keys import FeatureStatusKey, ModuleKey, PageKey, ReportStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    MetaAnalysisWorkspaceWidget = None  # type: ignore[assignment]
    meta_active_types_v1 = None  # type: ignore[assignment]
    meta_target_ia_pages = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def meta_workspace(qt_app):
    widget = MetaAnalysisWorkspaceWidget()
    yield widget
    widget.close()
    widget.deleteLater()
    qt_app.processEvents()


def test_meta_target_ia_pages_are_shell_structure_only() -> None:
    pages = meta_target_ia_pages()

    assert [page.key for page in pages] == [
        "project_home",
        "question_meta_type",
        "search_strategy",
        "import_dedup",
        "screening",
        "fulltext_extraction",
        "quality_assessment",
        "analysis_tasks",
        "result_report",
        "report_export",
        "meta_settings",
    ]
    assert {"testing", "planned", "shell_only"} <= {page.status_key for page in pages}
    assert [page.flow_index for page in pages if page.page_group == "main_flow"] == list(range(1, 11))
    assert [page.key for page in pages if page.page_group == "auxiliary"] == ["meta_settings"]
    assert any("不启用 Network Meta" in page.boundary for page in pages)
    assert any("不声明生产级系统综述能力" in page.boundary for page in pages)


def test_meta_active_types_include_exactly_ten_v1_types() -> None:
    active_types = meta_active_types_v1()

    assert [item.type_id for item in active_types] == [
        "binary_outcome_meta",
        "continuous_outcome_meta",
        "survival_outcome_meta",
        "prevalence_incidence_meta",
        "diagnostic_accuracy_meta",
        "exposure_disease_risk_meta",
        "biomarker_expression_difference_meta",
        "correlation_meta",
        "prognostic_factor_meta",
        "dose_response_meta",
    ]
    assert all(item.status_key == "testing" for item in active_types)
    assert "NETWORK_META_ANALYSIS" not in {item.type_id for item in active_types}
    assert "network_meta_analysis" not in {item.type_id for item in active_types}


def test_meta_workspace_renders_target_ia_shell(meta_workspace) -> None:
    title = meta_workspace.findChild(QLabel, "metaTargetIATitle")
    boundary = meta_workspace.findChild(QLabel, "metaTargetIABoundary")
    nav_items = meta_workspace.findChildren(QPushButton, "metaTargetIANavItem")

    assert title is not None
    assert title.text() == "Meta Analysis / Meta 分析目标 IA shell"
    assert boundary is not None
    assert "定义研究问题" in boundary.text()
    assert "全文管理" in boundary.text()
    assert len(nav_items) == 11
    assert tuple(item.property("pageKey") for item in nav_items) == meta_workspace.target_ia_page_keys()
    assert all(item.isEnabled() for item in nav_items)
    assert all(item.property("interactionMode") == "select_only" for item in nav_items)
    assert all(item.property("formalActionEnabled") is False for item in nav_items)
    assert all(item.property("moduleKey") == ModuleKey.META_ANALYSIS.value for item in nav_items)
    assert all(item.minimumHeight() >= 74 for item in nav_items)
    assert all("\n" in item.text() for item in nav_items)
    assert {item.property("semanticKey") for item in nav_items} >= {
        PageKey.META_PROJECT_HOME.value,
        PageKey.META_RESULT_REPORT.value,
        PageKey.META_REPORT_EXPORT.value,
    }
    assert {item.property("statusSemanticKey") for item in nav_items} >= {
        FeatureStatusKey.SHELL_ONLY.value,
        FeatureStatusKey.TESTING.value,
        FeatureStatusKey.PLANNED.value,
    }


def test_meta_workspace_groups_ten_active_meta_types(meta_workspace) -> None:
    cards = meta_workspace.findChildren(QFrame, "metaActiveTypeCard")
    select_buttons = meta_workspace.findChildren(QPushButton, "metaActiveTypeSelectButton")
    group_titles = [label.text() for label in meta_workspace.findChildren(QLabel, "metaTypeGroupTitle")]
    type_ids = [card.property("typeId") for card in cards]

    assert len(cards) == 10
    assert len(select_buttons) == 10
    assert type_ids == list(meta_workspace.active_meta_type_ids())
    assert group_titles == [
        "结局型 Meta",
        "流行病学 Meta",
        "诊断与关联 Meta",
        "关联与预后 Meta",
        "Testing schema",
    ]
    assert all(card.property("statusKey") == "testing" for card in cards)
    assert all(card.minimumHeight() >= 128 for card in cards)
    assert all(card.property("moduleKey") == ModuleKey.META_ANALYSIS.value for card in cards)
    assert all(card.property("semanticKey") == FeatureStatusKey.TESTING.value for card in cards)
    assert all(button.property("interactionMode") == "schema_shell" for button in select_buttons)
    assert all(button.property("formalActionEnabled") is False for button in select_buttons)
    assert all(button.property("moduleKey") == ModuleKey.META_ANALYSIS.value for button in select_buttons)
    assert all(button.property("semanticKey") == FeatureStatusKey.TESTING.value for button in select_buttons)


def test_network_meta_is_planned_boundary_not_active_type(meta_workspace) -> None:
    cards = meta_workspace.findChildren(QFrame, "metaActiveTypeCard")
    planned = meta_workspace.findChild(QLabel, "metaNetworkMetaBoundary")
    planned_button = meta_workspace.findChild(QPushButton, "metaNetworkMetaPlannedButton")

    assert planned is not None
    assert "Network Meta：planned only / not enabled" in planned.text()
    assert planned.property("formalActionEnabled") is False
    assert planned_button is not None
    assert planned_button.property("typeId") == "network_meta_analysis"
    assert planned_button.property("interactionMode") == "planned_disabled"
    assert planned_button.property("formalActionEnabled") is False
    assert not planned_button.isEnabled()
    assert meta_workspace.network_meta_enabled() is False
    assert all("network" not in str(card.property("typeId")).lower() for card in cards)


def test_meta_adopts_shared_result_report_export_shell(meta_workspace) -> None:
    panel = meta_workspace.findChild(QFrame, "resultReportExportAdoptionPanel")

    assert panel is not None
    buttons = panel.findChildren(QPushButton, "exportGatedButton")
    assert panel.property("adoptionModule") == "meta_analysis"
    assert panel.property("resultSemanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert panel.property("reportStatusKey") == ReportStatusKey.DRAFT.value
    assert panel.property("exportGate") == "disabled_empty_result"
    assert panel.property("reportReadyPackageAllowed") is False
    assert all(button.property("formalActionEnabled") is False for button in buttons)
    assert all(not button.isEnabled() for button in buttons)


def test_mainline_page_keys_remain_shell_contract(meta_workspace) -> None:
    assert meta_workspace.page_keys() == ("workflow_home", "project_contract", "dev_branch")


def test_meta_target_page_selection_updates_shell_state_only(meta_workspace) -> None:
    nav_items = meta_workspace.findChildren(QPushButton, "metaTargetIANavItem")
    by_page = {button.property("pageKey"): button for button in nav_items}
    status = meta_workspace.findChild(QLabel, "metaTargetInteractionStatus")

    assert meta_workspace.current_target_page_key() == "project_home"
    assert by_page["project_home"].isChecked()

    by_page["screening"].click()

    assert meta_workspace.current_target_page_key() == "screening"
    assert by_page["screening"].isChecked()
    assert by_page["screening"].property("currentStep") is True
    assert by_page["project_home"].property("currentStep") is False
    assert by_page["screening"].property("pageGroup") == "main_flow"
    assert by_page["screening"].property("flowIndex") == 5
    assert status is not None
    assert "当前页面：Screening / 文献筛选 · testing" in status.text()
    assert meta_workspace.page_keys() == ("workflow_home", "project_contract", "dev_branch")


def test_meta_active_type_selection_remains_schema_shell(meta_workspace) -> None:
    type_buttons = meta_workspace.findChildren(QPushButton, "metaActiveTypeSelectButton")
    by_type = {button.property("typeId"): button for button in type_buttons}
    status = meta_workspace.findChild(QLabel, "metaActiveTypeInteractionStatus")

    assert meta_workspace.selected_active_meta_type_id() == "binary_outcome_meta"
    assert by_type["binary_outcome_meta"].isChecked()

    by_type["diagnostic_accuracy_meta"].click()

    assert meta_workspace.selected_active_meta_type_id() == "diagnostic_accuracy_meta"
    assert by_type["diagnostic_accuracy_meta"].isChecked()
    assert by_type["diagnostic_accuracy_meta"].property("interactionMode") == "schema_shell"
    assert status is not None
    assert "AI suggestion remains review-only" in status.text()


def test_meta_fulltext_extraction_tabs_match_c1_concept(meta_workspace) -> None:
    meta_workspace.show_target_ia_page("fulltext_extraction")
    tabs = meta_workspace.findChildren(QPushButton, "metaFulltextExtractionTab")
    by_tab = {tab.property("tabKey"): tab for tab in tabs}
    management_body = meta_workspace.findChild(QFrame, "metaFulltextManagementBody")
    extraction_body = meta_workspace.findChild(QFrame, "metaExtractionDesignBody")
    confirm = meta_workspace.findChild(QPushButton, "metaConfirmExtractionButton")
    fields = meta_workspace.findChildren(QLabel, "metaExtractionFieldCell")
    labels = "\n".join(label.text() for label in meta_workspace.findChildren(QLabel))

    assert [tab.property("tabKey") for tab in tabs] == ["全文管理", "提取表设计", "提取完成核查", "历史记录"]
    assert "数据提取" not in [tab.property("tabKey") for tab in tabs]
    assert all(tab.minimumHeight() >= 34 for tab in tabs)
    assert management_body is not None
    assert extraction_body is not None
    assert management_body.minimumHeight() >= 260
    assert not management_body.isHidden()
    assert extraction_body.isHidden()
    by_tab["提取表设计"].click()
    assert by_tab["提取表设计"].isChecked()
    assert management_body.isHidden()
    assert not extraction_body.isHidden()
    assert confirm is not None
    assert confirm.property("actionSemantic") == "advance_to_extraction_stage"
    assert not confirm.isEnabled()
    assert any(label.text() == "研究设计" for label in fields)
    assert "当前提取表字段（Binary Outcome Meta 专用）" in labels
