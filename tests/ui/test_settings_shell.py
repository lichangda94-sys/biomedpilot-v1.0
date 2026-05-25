from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QListWidget, QPushButton, QScrollArea, QStackedWidget, QToolButton

    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import ModuleKey, PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    Qt = None  # type: ignore[assignment]
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
def settings_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_settings()
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def test_settings_shell_exposes_secondary_navigation(settings_window) -> None:
    nav = settings_window.findChild(QListWidget, "settingsSecondaryNav")
    stack = settings_window.findChild(QStackedWidget, "settingsContentStack")
    page = settings_window.findChild(QScrollArea, "settingsPage")

    assert settings_window.current_workspace_key() == "settings"
    assert page is not None
    assert page.widgetResizable()
    assert page.property("usabilityRole") == "scrollable_shell_page"
    assert page.accessibleName() == "Settings shell page"
    assert nav is not None
    assert nav.property("uiPrimitive") == "workbench_secondary_nav"
    assert nav.property("layoutPolishNoOverlap") is True
    assert [nav.item(index).data(Qt.UserRole + 1) for index in range(nav.count())] == [
        PageKey.SETTINGS_GENERAL.value,
        PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
        PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
        PageKey.SETTINGS_MODEL_ENGINE.value,
        PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value,
    ]
    assert stack is not None
    assert stack.property("uiPrimitive") == "workbench_content_stack"
    assert stack.property("layoutPolishNoOverlap") is True
    assert [stack.widget(index).property("moduleKey") for index in range(stack.count())] == [ModuleKey.SETTINGS.value] * 5
    assert [stack.widget(index).property("semanticKey") for index in range(stack.count())] == [
        PageKey.SETTINGS_GENERAL.value,
        PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value,
        PageKey.SETTINGS_ANALYSIS_RESOURCES.value,
        PageKey.SETTINGS_MODEL_ENGINE.value,
        PageKey.SETTINGS_DEVELOPER_DIAGNOSTICS.value,
    ]
    assert [stack.widget(index).objectName() for index in range(stack.count())] == [
        "settingsGeneralPage",
        "settingsExternalCapabilitiesPage",
        "settingsAnalysisResourcesPage",
        "settingsModelEnginePage",
        "settingsDeveloperDiagnosticsPage",
    ]

    nav.setCurrentRow(1)
    assert stack.currentWidget().objectName() == "settingsExternalCapabilitiesPage"


def test_settings_external_capabilities_are_detect_first(settings_window) -> None:
    nav = settings_window.findChild(QListWidget, "settingsSecondaryNav")
    nav.setCurrentRow(1)

    cards = settings_window.findChildren(QFrame, "settingsCapabilityCard")
    detect_buttons = settings_window.findChildren(QPushButton, "settingsDetectButton")
    install_buttons = settings_window.findChildren(QPushButton, "settingsInstallButton")
    cloud_buttons = settings_window.findChildren(QPushButton, "settingsCloudConfigButton")
    labels = "\n".join(label.text() for label in settings_window.findChildren(QLabel))

    assert len(cards) >= 4
    assert "Python 环境" in labels
    assert "R 环境" in labels
    assert "ImageJ/Fiji" in labels
    assert "外部图像分析引擎" in labels
    assert detect_buttons
    assert all(button.isEnabled() for button in detect_buttons)
    assert all(button.property("moduleKey") == ModuleKey.SETTINGS.value for button in detect_buttons)
    assert all(button.property("semanticKey") == PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value for button in detect_buttons)
    assert install_buttons
    assert all(not button.isEnabled() for button in install_buttons)
    assert all(button.property("moduleKey") == ModuleKey.SETTINGS.value for button in install_buttons)
    assert cloud_buttons
    assert all(not button.isEnabled() for button in cloud_buttons)
    assert all(button.property("semanticKey") == PageKey.SETTINGS_MODEL_ENGINE.value for button in cloud_buttons)


def test_settings_status_chips_cover_external_resource_states(settings_window) -> None:
    chips = settings_window.findChildren(QLabel, "uiStatusChip")
    status_keys = {chip.property("statusKey") for chip in chips}

    assert {
        "available",
        "not_configured",
        "planned",
        "preflight_only",
        "developer_preview",
        "blocked",
        "shell_only",
    }.issubset(status_keys)


def test_settings_developer_diagnostics_are_collapsed_by_default(settings_window) -> None:
    nav = settings_window.findChild(QListWidget, "settingsSecondaryNav")
    nav.setCurrentRow(4)

    toggle = settings_window.findChild(QToolButton, "developerDiagnosticsToggle")
    panel = settings_window.findChild(QFrame, "developerDiagnosticsPanel")

    assert toggle is not None
    assert toggle.text() == "Settings resources / Developer diagnostics"
    assert panel is not None
    assert panel.isHidden()
    assert panel.property("moduleKey") == ModuleKey.SETTINGS.value
    assert panel.property("statusKey") == "developer_preview"

    toggle.click()

    assert not panel.isHidden()
    labels = "\n".join(label.text() for label in panel.findChildren(QLabel))
    assert "不会安装、下载、更新或连接云端" in labels
