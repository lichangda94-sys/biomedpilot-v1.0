from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QScrollArea

    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QScrollArea = None  # type: ignore[assignment]
    MainWindow = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def labtools_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def test_labtools_entry_is_reachable_from_global_shell(labtools_window) -> None:
    assert labtools_window.current_workspace_key() == "labtools"
    page = labtools_window.findChild(QScrollArea, "labtoolsShellPage")
    title = labtools_window.findChild(QLabel, "labtoolsShellTitle")
    assert page is not None
    assert page.widgetResizable()
    assert page.property("usabilityRole") == "scrollable_shell_page"
    assert page.accessibleName() == "LabTools shell page"
    assert title is not None
    assert title.property("moduleKey") == ModuleKey.LABTOOLS.value
    assert title.property("semanticKey") == ModuleKey.LABTOOLS.value


def test_labtools_primary_ia_has_only_three_entries(labtools_window) -> None:
    entry_title_labels = labtools_window.findChildren(QLabel, "labtoolsPrimaryEntryTitle")
    entry_pages = [label.property("semanticKey") for label in entry_title_labels]
    entry_buttons = labtools_window.findChildren(QPushButton, "labtoolsEntryButton")

    assert entry_pages == [
        PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
        PageKey.LABTOOLS_REAGENT_PREPARATION.value,
        PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
    ]
    assert len(entry_buttons) == 3
    assert all(button.property("moduleKey") == ModuleKey.LABTOOLS.value for button in entry_buttons)
    assert [button.property("semanticKey") for button in entry_buttons] == entry_pages
    assert all(not button.isEnabled() for button in entry_buttons)


def test_general_calculator_excludes_experiment_specific_workflows(labtools_window) -> None:
    cards = labtools_window.findChildren(QFrame, "labtoolsPrimaryEntryCard")
    general_card = next(
        card
        for card in cards
        if card.property("semanticKey") == PageKey.LABTOOLS_GENERAL_CALCULATORS.value
    )
    details = "\n".join(label.text() for label in general_card.findChildren(QLabel, "labtoolsEntryDetail"))

    assert "稀释计算" in details
    assert "加样计算" in details
    assert "单位换算" in details
    assert "Western Blot" not in details
    assert "PCR/qPCR" not in details
    assert "ELISA" not in details
    assert "MTT/CCK-8/AlamarBlue" not in details


def test_labtools_home_does_not_render_experiment_categories_as_large_cards(labtools_window) -> None:
    module_titles = labtools_window.findChildren(QLabel, "labtoolsExperimentModuleTitle")
    labels = "\n".join(label.text() for label in labtools_window.findChildren(QLabel))

    assert module_titles == []
    assert "细胞实验、蛋白实验、核酸实验、免疫与吸光度实验、免疫组化。" in labels
    assert "说明与边界" not in labels


def test_labtools_statuses_and_quick_access_are_explicit(labtools_window) -> None:
    content = labtools_window.findChild(QFrame, "labtoolsShellContent") or labtools_window.findChild(QScrollArea, "labtoolsShellPage").widget()
    chips = content.findChildren(QLabel, "uiStatusChip")
    status_keys = {chip.property("statusKey") for chip in chips}
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))
    quick_buttons = content.findChildren(QPushButton, "quickAccessButton")

    assert {"planned", "testing", "shell_only", "developer_preview"} <= status_keys
    assert [button.property("quickAccessKey") for button in quick_buttons] == ["使用指南", "常见问题", "意见反馈", "最近使用"]
    assert "不实现完整库存系统" not in labels
    assert "不做云端协作" not in labels
    assert "不做局域网共享" not in labels
    assert "不重写真实实验计算逻辑" not in labels


def test_image_analysis_engine_points_to_settings_not_primary_labtools_entry(labtools_window) -> None:
    content = labtools_window.findChild(QScrollArea, "labtoolsShellPage").widget()
    primary_titles = [label.text() for label in content.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))

    assert all("图像分析" not in title for title in primary_titles)
    assert "图像分析" not in labels
    assert content.findChildren(QLabel, "labtoolsBoundaryDetail") == []
