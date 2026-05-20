from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QListWidget, QPushButton, QStackedWidget, QToolButton

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

    assert settings_window.current_workspace_key() == "settings"
    assert nav is not None
    assert [nav.item(index).text() for index in range(nav.count())] == [
        "通用偏好",
        "外部能力",
        "分析资源",
        "模型与引擎",
        "开发者诊断",
    ]
    assert stack is not None
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
    assert all(button.isEnabled() and button.text() == "检测状态" for button in detect_buttons)
    assert install_buttons
    assert all(not button.isEnabled() for button in install_buttons)
    assert cloud_buttons
    assert all(not button.isEnabled() for button in cloud_buttons)


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

    toggle.click()

    assert not panel.isHidden()
    labels = "\n".join(label.text() for label in panel.findChildren(QLabel))
    assert "不会安装、下载、更新或连接云端" in labels
