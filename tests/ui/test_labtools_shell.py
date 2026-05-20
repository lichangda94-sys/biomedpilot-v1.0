from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton

    from app.shell.main_window import MainWindow
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
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
    title = labtools_window.findChild(QLabel, "labtoolsShellTitle")
    assert title is not None
    assert title.text() == "LabTools / 实验工具"


def test_labtools_primary_ia_has_only_three_entries(labtools_window) -> None:
    entry_titles = [label.text() for label in labtools_window.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    entry_buttons = labtools_window.findChildren(QPushButton, "labtoolsEntryButton")

    assert entry_titles == ["通用计算器", "试剂制备", "实验模块"]
    assert len(entry_buttons) == 3
    assert all(not button.isEnabled() for button in entry_buttons)
    assert "图像分析" not in entry_titles
    assert "库存" not in entry_titles


def test_general_calculator_excludes_experiment_specific_workflows(labtools_window) -> None:
    cards = labtools_window.findChildren(QFrame, "labtoolsPrimaryEntryCard")
    general_card = next(
        card
        for card in cards
        if card.findChild(QLabel, "labtoolsPrimaryEntryTitle").text() == "通用计算器"
    )
    details = "\n".join(label.text() for label in general_card.findChildren(QLabel, "labtoolsEntryDetail"))

    assert "跨实验场景" in details
    assert "Western Blot" in details
    assert "PCR/qPCR" in details
    assert "ELISA" in details
    assert "MTT/CCK-8/AlamarBlue" in details
    assert "不包含" in details


def test_labtools_experiment_modules_cover_five_categories(labtools_window) -> None:
    module_titles = [label.text() for label in labtools_window.findChildren(QLabel, "labtoolsExperimentModuleTitle")]
    module_details = "\n".join(label.text() for label in labtools_window.findChildren(QLabel, "labtoolsExperimentModuleDetail"))

    assert module_titles == [
        "细胞实验",
        "蛋白实验",
        "核酸实验",
        "免疫与吸光度实验",
        "免疫组化",
    ]
    assert "MTT / CCK-8 / AlamarBlue 归属此类" in module_details
    assert "Western Blot 完整流程" in module_details
    assert "PCR" in module_details
    assert "qPCR" in module_details
    assert "ELISA" in module_details


def test_labtools_statuses_and_boundaries_are_explicit(labtools_window) -> None:
    chips = labtools_window.findChildren(QLabel, "uiStatusChip")
    status_keys = {chip.property("statusKey") for chip in chips}
    labels = "\n".join(label.text() for label in labtools_window.findChildren(QLabel))

    assert {"planned", "testing", "shell_only"} <= status_keys
    assert "不实现完整库存系统" in labels
    assert "不做云端协作" in labels
    assert "不做局域网共享" in labels
    assert "不重写真实实验计算逻辑" in labels


def test_image_analysis_engine_points_to_settings_not_primary_labtools_entry(labtools_window) -> None:
    primary_titles = [label.text() for label in labtools_window.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    boundary_labels = "\n".join(label.text() for label in labtools_window.findChildren(QLabel, "labtoolsBoundaryDetail"))

    assert all("图像分析" not in title for title in primary_titles)
    assert "Settings / 外部能力" in boundary_labels
    assert "不作为 LabTools 一级入口" in boundary_labels
