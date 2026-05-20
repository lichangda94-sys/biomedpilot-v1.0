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

    assert "跨实验场景" in details
    assert "Western Blot" in details
    assert "PCR/qPCR" in details
    assert "ELISA" in details
    assert "MTT/CCK-8/AlamarBlue" in details
    assert "不包含" in details


def test_labtools_experiment_modules_cover_five_categories(labtools_window) -> None:
    module_titles = labtools_window.findChildren(QLabel, "labtoolsExperimentModuleTitle")
    module_keys = [label.property("semanticKey") for label in module_titles]
    module_details = "\n".join(label.text() for label in labtools_window.findChildren(QLabel, "labtoolsExperimentModuleDetail"))

    assert module_keys == [
        PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
        PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
        PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value,
        PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
        PageKey.LABTOOLS_IHC.value,
    ]
    assert all(label.property("moduleKey") == ModuleKey.LABTOOLS.value for label in module_titles)
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
