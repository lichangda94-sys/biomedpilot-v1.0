from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget

    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
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


def _primary_button(window, page_key: str):
    return next(
        button
        for button in window.findChildren(QPushButton, "labtoolsEntryButton")
        if button.property("pageKey") == page_key
    )


def _secondary_button(window, page_key: str):
    return next(
        button
        for button in window._labtools_page.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if button.property("pageKey") == page_key
    )


def test_labtools_home_uses_approved_three_entry_ia(labtools_window) -> None:
    page = labtools_window._labtools_page
    labels = "\n".join(label.text() for label in page.findChildren(QLabel))
    primary_titles = [label.text() for label in page.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    primary_buttons = page.findChildren(QPushButton, "labtoolsEntryButton")

    assert page.current_page_key() == "home"
    assert primary_titles == ["通用计算器", "试剂制备", "实验模块"]
    assert [button.property("semanticKey") for button in primary_buttons] == [
        PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
        PageKey.LABTOOLS_REAGENT_PREPARATION.value,
        PageKey.LABTOOLS_EXPERIMENT_MODULES.value,
    ]
    assert all(button.property("moduleKey") == ModuleKey.LABTOOLS.value for button in primary_buttons)
    assert "图像分析" not in primary_titles
    assert "ImageJ" not in primary_titles
    assert "快速入口" in labels
    assert "实验计算结果需由用户复核后用于台面操作" in labels


def test_experiment_modules_route_to_expected_second_level_list(labtools_window) -> None:
    page = labtools_window._labtools_page

    _primary_button(labtools_window, "experiment_modules").click()

    secondary_titles = page.current_page_widget().findChildren(QLabel, "labtoolsSecondaryEntryTitle")
    assert page.current_page_key() == "experiment_modules"
    assert [label.property("pageKey") for label in secondary_titles] == [
        "cell_experiments",
        "protein_experiments",
        "nucleic_acid_experiments",
        "immuno_absorbance",
        "ihc",
    ]


@pytest.mark.parametrize(
    ("page_key", "semantic_key", "expected_text"),
    [
        ("immuno_absorbance", "labtools.page.immuno_absorbance", "ELISA/BCA formal"),
        ("ihc", "labtools.page.ihc", "IHC record model"),
    ],
)
def test_labtools_unconnected_secondary_routes_are_explicitly_disabled(
    labtools_window, page_key: str, semantic_key: str, expected_text: str
) -> None:
    page = labtools_window._labtools_page
    _primary_button(labtools_window, "experiment_modules").click()

    _secondary_button(labtools_window, page_key).click()

    current_page = page.current_page_widget()
    labels = "\n".join(label.text() for label in current_page.findChildren(QLabel))
    disabled = current_page.findChild(QPushButton, "labToolsC1DisabledActionButton")
    assert page.current_page_key() == page_key
    assert page.property("semanticKey") == semantic_key
    assert expected_text in labels
    assert disabled is not None
    assert not disabled.isEnabled()
    assert expected_text in disabled.property("disabledReason")


def test_labtools_nucleic_acid_secondary_route_calls_qpcr_adapter(labtools_window) -> None:
    page = labtools_window._labtools_page
    _primary_button(labtools_window, "experiment_modules").click()

    _secondary_button(labtools_window, "nucleic_acid_experiments").click()

    current_page = page.current_page_widget()
    tabs = current_page.findChild(QTabWidget, "nucleicAcidExperimentTabs")
    assert page.current_page_key() == "nucleic_acid_experiments"
    assert page.property("semanticKey") == "labtools.page.nucleic_acid_experiments"
    assert current_page.property("connectionStatus") == "connected"
    assert tabs is not None
    assert current_page.findChild(QPushButton, "qpcrMixCalculateButton") is not None
    assert current_page.findChild(QPushButton, "nucleicPrimerRegistryGateDisabledButton").property("disabledReason")


def test_labtools_c2_primary_routes_call_backend_widgets(labtools_window) -> None:
    page = labtools_window._labtools_page

    _primary_button(labtools_window, "general_calculators").click()

    calculator_page = page.current_page_widget()
    calculator_tabs = calculator_page.findChild(QTabWidget, "labToolsCalculatorTabs")
    assert page.current_page_key() == "general_calculators"
    assert page.property("semanticKey") == PageKey.LABTOOLS_GENERAL_CALCULATORS.value
    assert calculator_page.property("connectionStatus") == "connected"
    assert calculator_tabs is not None
    assert calculator_tabs.count() >= 2

    page.show_home()
    _primary_button(labtools_window, "reagent_preparation").click()

    reagent_page = page.current_page_widget()
    assert page.current_page_key() == "reagent_preparation"
    assert page.property("semanticKey") == PageKey.LABTOOLS_REAGENT_PREPARATION.value
    assert reagent_page.property("connectionStatus") == "connected"
    assert reagent_page.objectName() == "labToolsReagentPreparationFlow"


def test_labtools_c2_secondary_routes_call_backend_widgets(labtools_window) -> None:
    page = labtools_window._labtools_page
    _primary_button(labtools_window, "experiment_modules").click()

    _secondary_button(labtools_window, "cell_experiments").click()

    cell_page = page.current_page_widget()
    cell_tabs = cell_page.findChild(QTabWidget, "cellExperimentTopTabs")
    assert page.current_page_key() == "cell_experiments"
    assert page.property("semanticKey") == PageKey.LABTOOLS_CELL_EXPERIMENTS.value
    assert cell_page.property("connectionStatus") == "connected"
    assert cell_tabs is not None
    assert cell_tabs.count() >= 2

    page.show_experiment_modules()
    _secondary_button(labtools_window, "protein_experiments").click()

    protein_page = page.current_page_widget()
    western_tabs = protein_page.findChild(QTabWidget, "westernBlotTabs")
    assert page.current_page_key() == "protein_experiments"
    assert page.property("semanticKey") == PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value
    assert protein_page.property("connectionStatus") == "connected"
    assert western_tabs is not None
    assert western_tabs.count() >= 5


def test_labtools_image_processing_is_not_a_module_entry(labtools_window) -> None:
    page = labtools_window._labtools_page
    primary_titles = [label.text() for label in page.findChildren(QLabel, "labtoolsPrimaryEntryTitle")]
    assert "图像分析" not in primary_titles

    _primary_button(labtools_window, "experiment_modules").click()
    labels = "\n".join(label.text() for label in page.current_page_widget().findChildren(QLabel))
    buttons = page.current_page_widget().findChildren(QPushButton, "labtoolsSecondaryEntryButton")

    assert page.current_page_key() == "experiment_modules"
    assert "图像处理" not in labels
    assert "ImageJ/Fiji" not in labels
    assert "image_processing_boundary" not in [button.property("pageKey") for button in buttons]


def test_labtools_home_button_returns_from_second_level_page(labtools_window) -> None:
    page = labtools_window._labtools_page
    _primary_button(labtools_window, "experiment_modules").click()
    _secondary_button(labtools_window, "cell_experiments").click()
    assert page.current_page_key() == "cell_experiments"

    labtools_window.findChild(QPushButton, "labToolsHomeButton").click()

    assert page.current_page_key() == "home"


def test_labtools_visible_buttons_have_click_contracts(labtools_window) -> None:
    page = labtools_window._labtools_page
    gaps: list[str] = []

    for page_key in page.page_keys():
        if page_key == "home":
            page.show_home()
        else:
            page._show_page(page_key)
        for button in page.current_page_widget().findChildren(QPushButton):
            behavior = button.property("buttonBehavior")
            reason = button.property("disabledReason")
            if behavior is None:
                gaps.append(f"{page_key}:{button.objectName()}:{button.text()}:missing-buttonBehavior")
            if not button.isEnabled() and reason is None:
                gaps.append(f"{page_key}:{button.objectName()}:{button.text()}:missing-disabledReason")

    assert gaps == []
