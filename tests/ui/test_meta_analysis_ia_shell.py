from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame

    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget, meta_active_types_v1, meta_target_ia_pages
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
    assert "AI suggestion 仅为人工可审核建议" in boundary.text()
    assert "当前不启用 Network Meta" in boundary.text()
    assert "不声明生产级系统综述能力" in boundary.text()
    assert len(nav_items) == 11
    assert tuple(item.property("pageKey") for item in nav_items) == meta_workspace.target_ia_page_keys()
    assert all(not item.isEnabled() for item in nav_items)


def test_meta_workspace_groups_ten_active_meta_types(meta_workspace) -> None:
    cards = meta_workspace.findChildren(QFrame, "metaActiveTypeCard")
    group_titles = [label.text() for label in meta_workspace.findChildren(QLabel, "metaTypeGroupTitle")]
    type_ids = [card.property("typeId") for card in cards]

    assert len(cards) == 10
    assert type_ids == list(meta_workspace.active_meta_type_ids())
    assert group_titles == [
        "结局型 Meta",
        "流行病学 Meta",
        "诊断与关联 Meta",
        "关联与预后 Meta",
        "Testing schema",
    ]
    assert all(card.property("statusKey") == "testing" for card in cards)


def test_network_meta_is_planned_boundary_not_active_type(meta_workspace) -> None:
    cards = meta_workspace.findChildren(QFrame, "metaActiveTypeCard")
    planned = meta_workspace.findChild(QLabel, "metaNetworkMetaBoundary")

    assert planned is not None
    assert "Network Meta：planned only / not enabled" in planned.text()
    assert all("network" not in str(card.property("typeId")).lower() for card in cards)


def test_mainline_page_keys_remain_shell_contract(meta_workspace) -> None:
    assert meta_workspace.page_keys() == ("workflow_home", "project_contract", "dev_branch")
