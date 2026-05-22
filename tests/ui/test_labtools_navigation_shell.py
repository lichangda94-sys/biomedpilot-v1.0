from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea

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


def _content(window):
    return window.findChild(QScrollArea, "labtoolsShellPage").widget()


def _click_primary(window, semantic_key: str) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == semantic_key
    )
    button.click()


def _click_secondary(window, page_key: str) -> None:
    button = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == page_key
    )
    button.click()


def test_primary_entries_route_to_safe_secondary_shells(labtools_window) -> None:
    _click_primary(labtools_window, PageKey.LABTOOLS_GENERAL_CALCULATORS.value)
    content = _content(labtools_window)
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))
    mode_buttons = content.findChildren(QPushButton, "labtoolsGeneralModeButton")

    assert content.property("pageKey") == "general_calculators"
    assert content.property("semanticKey") == PageKey.LABTOOLS_GENERAL_CALCULATORS.value
    assert [button.property("modeKey") for button in mode_buttons] == ["quick_calculator", "formula_solver"]
    assert "Western Blot" not in labels
    assert "BCA" not in labels
    assert "ELISA" not in labels
    assert "细胞实验记录" not in labels

    labtools_window.findChild(QPushButton, "labtoolsBackButton").click()
    assert _content(labtools_window).property("semanticKey") == PageKey.LABTOOLS_HOME.value


def test_reagent_shell_keeps_save_and_export_adapter_needed(labtools_window) -> None:
    _click_primary(labtools_window, PageKey.LABTOOLS_REAGENT_PREPARATION.value)
    content = _content(labtools_window)
    save_template = content.findChild(QPushButton, "labtoolsReagentSaveTemplateButton")
    save_record = content.findChild(QPushButton, "labtoolsReagentSaveRecordButton")
    export = content.findChild(QPushButton, "labtoolsReagentExportButton")
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))

    assert content.property("pageKey") == "reagent_preparation"
    assert content.findChild(QLabel, "labtoolsReagentResultPrimary") is not None
    assert save_template is not None and not save_template.isEnabled()
    assert save_record is not None and not save_record.isEnabled()
    assert export is not None and not export.isEnabled()
    assert save_record.property("disabledState") == "disabled_missing_storage_adapter"
    assert export.property("disabledState") == "disabled_missing_file_picker"
    assert "不默认写入 ~/.labtools" in labels
    assert "库存扣减" not in labels
    assert "云模板库" not in labels
    assert "多用户同步" not in labels


def test_experiment_modules_render_boundaries_without_enabling_actions(labtools_window) -> None:
    _click_primary(labtools_window, PageKey.LABTOOLS_EXPERIMENT_MODULES.value)
    content = _content(labtools_window)
    secondary_pages = [label.property("pageKey") for label in content.findChildren(QLabel, "labtoolsSecondaryEntryTitle")]

    assert secondary_pages == [
        "wb_loading",
        "sds_page",
        "bca_od_mvp",
        "cell_experiment_workspace",
        "elisa_boundary",
        "image_processing_boundary",
    ]

    _click_secondary(labtools_window, "elisa_boundary")
    content = _content(labtools_window)
    chips = content.findChildren(QLabel, "uiStatusChip")
    buttons = content.findChildren(QPushButton, "labtoolsDisabledActionButton")
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))

    assert content.property("pageKey") == "elisa_boundary"
    assert any(chip.property("statusKey") == "blocked" for chip in chips)
    assert all(not button.isEnabled() for button in buttons)
    assert "ELISA 后端缺失" in labels
    assert "4PL" in labels


def test_cell_and_image_processing_boundaries_preserve_shell_only_semantics(labtools_window) -> None:
    _click_primary(labtools_window, PageKey.LABTOOLS_EXPERIMENT_MODULES.value)
    _click_secondary(labtools_window, "cell_experiment_workspace")
    content = _content(labtools_window)
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))
    buttons = content.findChildren(QPushButton, "labtoolsDisabledActionButton")

    assert content.property("pageKey") == "cell_experiment_workspace"
    assert "record store" in labels or "store 尚未接入" in labels
    assert "ELISA 不属于此页面" in labels
    assert all(not button.isEnabled() for button in buttons)

    labtools_window.findChild(QPushButton, "labtoolsBackButton").click()
    _click_primary(labtools_window, PageKey.LABTOOLS_EXPERIMENT_MODULES.value)
    _click_secondary(labtools_window, "image_processing_boundary")
    content = _content(labtools_window)
    settings_link = content.findChild(QPushButton, "labtoolsSettingsLinkButton")
    labels = "\n".join(label.text() for label in content.findChildren(QLabel))

    assert content.property("pageKey") == "image_processing_boundary"
    assert "ImageJ/Fiji 仅显示为 Settings-linked 外部能力配置入口" in labels
    assert settings_link is not None
    assert settings_link.isEnabled()
    assert settings_link.property("moduleKey") == ModuleKey.LABTOOLS.value
