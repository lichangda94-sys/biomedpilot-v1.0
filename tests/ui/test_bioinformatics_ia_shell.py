from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget, bioinformatics_target_ia_pages
    from app.shared.semantic_keys import AnalysisStatusKey, ReportStatusKey, ResultSemanticKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    BioinformaticsWorkspaceWidget = None  # type: ignore[assignment]
    bioinformatics_target_ia_pages = None  # type: ignore[assignment]
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
        "results",
        "report_export",
        "settings_resources",
    ]
    assert pages[2].semantic_key == AnalysisStatusKey.PREFLIGHT_ONLY.value
    assert pages[5].semantic_key == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert pages[6].semantic_key == ReportStatusKey.TESTING_SUMMARY.value


def test_bioinformatics_workspace_renders_target_ia_shell(bio_workspace) -> None:
    title = bio_workspace.findChild(QLabel, "bioinformaticsIATitle")
    boundary = bio_workspace.findChild(QLabel, "bioinformaticsIABoundary")
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")

    assert title is not None
    assert title.text() == "Bioinformatics / 生信分析目标 IA shell"
    assert boundary is not None
    assert "resolver-first / preflight-first / result-schema-first" in boundary.text()
    assert "不启用正式分析执行器" in boundary.text()
    assert len(nav_items) == 8
    assert tuple(item.property("pageKey") for item in nav_items) == bio_workspace.target_ia_page_keys()
    assert all(not item.isEnabled() for item in nav_items)


def test_bioinformatics_nav_items_carry_status_and_semantic_keys(bio_workspace) -> None:
    nav_items = bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem")
    by_page = {item.property("pageKey"): item for item in nav_items}

    assert by_page["data_check_preparation"].property("statusKey") == "preflight_only"
    assert by_page["data_check_preparation"].property("semanticKey") == AnalysisStatusKey.PREFLIGHT_ONLY.value
    assert by_page["analysis_tasks"].property("statusKey") == "blocked"
    assert by_page["analysis_tasks"].property("semanticKey") == AnalysisStatusKey.BLOCKED.value
    assert by_page["results"].property("semanticKey") == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert by_page["report_export"].property("statusKey") == "draft"
    assert by_page["report_export"].property("semanticKey") == ReportStatusKey.TESTING_SUMMARY.value


def test_bioinformatics_shell_copy_keeps_preflight_and_result_boundaries(bio_workspace) -> None:
    labels = "\n".join(label.text() for label in bio_workspace.findChildren(QLabel))
    tooltips = "\n".join(button.toolTip() for button in bio_workspace.findChildren(QPushButton, "bioinformaticsIANavItem"))

    assert "preflight/gated" in labels
    assert "imported_external_result != formal_computed_result" in labels
    assert "report draft / testing summary only" in labels
    assert "TCGA+GTEx 不自动合并" in tooltips
    assert "不得把预检包装成正式 DEG/GSEA/生存分析执行" in tooltips
    assert "不生成假结果或假图" in tooltips
    assert "不声明 report-ready 正式报告" in tooltips
