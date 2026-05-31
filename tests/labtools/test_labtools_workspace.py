from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget

    from app.labtools.workspace import LabToolsWorkspaceWidget
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


EXPECTED_PAGE_KEYS = (
    "home",
    "general_calculators",
    "reagent_preparation",
    "experiment_modules",
    "cell_experiments",
    "protein_experiments",
    "nucleic_acid_experiments",
    "immuno_absorbance",
    "ihc",
)


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_labtools_workspace_opens_on_three_entry_home(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()

    primary_titles = [label.text() for label in widget.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    primary_buttons = widget.findChildren(QPushButton, "labtoolsEntryButton")
    labels = "\n".join(label.text() for label in widget.findChildren(QLabel))

    assert widget.page_keys() == EXPECTED_PAGE_KEYS
    assert widget.current_page_key() == "home"
    assert primary_titles == ["通用计算器", "试剂制备", "实验模块"]
    assert [button.property("pageKey") for button in primary_buttons] == [
        "general_calculators",
        "reagent_preparation",
        "experiment_modules",
    ]
    assert "图像分析" not in primary_titles
    assert "ImageJ" not in primary_titles
    assert "实验计算结果需由用户复核后用于台面操作" in labels


def test_experiment_modules_expose_second_level_entries(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()
    button = next(
        item
        for item in widget.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("pageKey") == "experiment_modules"
    )

    button.click()

    titles = widget.current_page_widget().findChildren(QLabel, "labtoolsSecondaryEntryTitle")
    buttons = widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
    assert widget.current_page_key() == "experiment_modules"
    assert [label.property("pageKey") for label in titles] == [
        "cell_experiments",
        "protein_experiments",
        "nucleic_acid_experiments",
        "immuno_absorbance",
        "ihc",
    ]
    assert [button.property("pageKey") for button in buttons] == [
        "cell_experiments",
        "protein_experiments",
        "nucleic_acid_experiments",
        "immuno_absorbance",
        "ihc",
    ]
    assert "image_processing_boundary" not in [button.property("pageKey") for button in buttons]


def test_labtools_c2_primary_routes_connect_to_workbench_widgets(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()

    widget.show_general_calculator()

    calculator_page = widget.current_page_widget()
    calculator_tabs = calculator_page.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert widget.current_page_key() == "general_calculators"
    assert widget.property("semanticKey") == "labtools.page.general_calculators"
    assert calculator_page.property("connectionStatus") == "connected"
    assert calculator_tabs is not None
    assert calculator_tabs.count() >= 2

    widget.show_reagent_preparation()

    reagent_page = widget.current_page_widget()
    assert widget.current_page_key() == "reagent_preparation"
    assert widget.property("semanticKey") == "labtools.page.reagent_preparation"
    assert reagent_page.property("connectionStatus") == "connected"
    assert reagent_page.objectName() == "labToolsReagentPreparationFlow"


def test_labtools_c2_secondary_routes_connect_cell_and_protein_workbenches(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()
    widget.show_experiment_modules()

    cell_button = next(
        item
        for item in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "cell_experiments"
    )
    protein_button = next(
        item
        for item in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "protein_experiments"
    )

    cell_button.click()

    cell_page = widget.current_page_widget()
    cell_tabs = cell_page.findChild(QTabWidget, "cellExperimentTopTabs")
    assert widget.current_page_key() == "cell_experiments"
    assert widget.property("semanticKey") == "labtools.page.cell_experiments"
    assert cell_page.property("connectionStatus") == "connected"
    assert cell_tabs is not None
    assert cell_tabs.count() >= 2

    widget.show_experiment_modules()
    protein_button = next(
        item
        for item in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "protein_experiments"
    )
    protein_button.click()

    protein_page = widget.current_page_widget()
    western_tabs = protein_page.findChild(QTabWidget, "westernBlotTabs")
    assert widget.current_page_key() == "protein_experiments"
    assert widget.property("semanticKey") == "labtools.page.protein_experiments"
    assert protein_page.property("connectionStatus") == "connected"
    assert western_tabs is not None
    assert western_tabs.count() >= 5


@pytest.mark.parametrize(
    "page_key",
    ["nucleic_acid_experiments", "immuno_absorbance", "ihc"],
)
def test_labtools_unconnected_secondary_placeholders_keep_disabled_reason(qt_app, page_key: str) -> None:
    widget = LabToolsWorkspaceWidget()
    widget.show_experiment_modules()
    button = next(
        item
        for item in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == page_key
    )

    button.click()

    current_page = widget.current_page_widget()
    disabled = current_page.findChild(QPushButton, "labToolsC1DisabledActionButton")
    assert widget.current_page_key() == page_key
    assert disabled is not None
    assert not disabled.isEnabled()
    assert disabled.property("disabledReason")


def test_labtools_experiment_modules_do_not_expose_image_processing_entry(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()
    widget.show_experiment_modules()

    current_page = widget.current_page_widget()
    labels = "\n".join(label.text() for label in current_page.findChildren(QLabel))
    buttons = current_page.findChildren(QPushButton, "labtoolsSecondaryEntryButton")

    assert "图像处理" not in labels
    assert "ImageJ/Fiji" not in labels
    assert "image_processing_boundary" not in [button.property("pageKey") for button in buttons]
