from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

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


def test_labtools_c1_secondary_placeholder_has_disabled_reason(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()
    widget.show_experiment_modules()
    button = next(
        item
        for item in widget.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == "protein_experiments"
    )

    button.click()

    current_page = widget.current_page_widget()
    labels = "\n".join(label.text() for label in current_page.findChildren(QLabel))
    disabled = current_page.findChild(QPushButton, "labToolsC1DisabledActionButton")
    assert widget.current_page_key() == "protein_experiments"
    assert widget.property("semanticKey") == "labtools.page.protein_experiments"
    assert "Disabled reason: UI-LABTOOLS-C2 will connect WB loading" in labels
    assert disabled is not None
    assert not disabled.isEnabled()
    assert (
        disabled.property("disabledReason")
        == "UI-LABTOOLS-C2 will connect WB loading, SDS-PAGE, BCA/OD, records, and report gates."
    )


def test_labtools_experiment_modules_do_not_expose_image_processing_entry(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()
    widget.show_experiment_modules()

    current_page = widget.current_page_widget()
    labels = "\n".join(label.text() for label in current_page.findChildren(QLabel))
    buttons = current_page.findChildren(QPushButton, "labtoolsSecondaryEntryButton")

    assert "图像处理" not in labels
    assert "ImageJ/Fiji" not in labels
    assert "image_processing_boundary" not in [button.property("pageKey") for button in buttons]
