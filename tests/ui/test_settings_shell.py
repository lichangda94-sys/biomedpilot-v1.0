from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QStackedWidget, QTabBar, QToolButton

    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import ModuleKey, PageKey
    from app.shared.storage import default_storage_root
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
    nav = settings_window.findChild(QTabBar, "settingsSecondaryNav")
    stack = settings_window.findChild(QStackedWidget, "settingsContentStack")
    page = settings_window.findChild(QScrollArea, "settingsPage")

    assert settings_window.current_workspace_key() == "settings"
    assert page is not None
    assert page.widgetResizable()
    assert page.property("usabilityRole") == "scrollable_shell_page"
    assert page.accessibleName() == "Settings shell page"
    assert nav is not None
    assert nav.property("uiPrimitive") == "secondary_nav_tabs"
    assert [nav.tabData(index) for index in range(nav.count())] == [
        "general",
        "external_capabilities",
        "analysis_resources",
        "model_engine",
        "developer_diagnostics",
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

    nav.setCurrentIndex(1)
    assert stack.currentWidget().objectName() == "settingsExternalCapabilitiesPage"


def test_settings_external_capabilities_are_detect_first(settings_window) -> None:
    nav = settings_window.findChild(QTabBar, "settingsSecondaryNav")
    stack = settings_window.findChild(QStackedWidget, "settingsContentStack")
    nav.setCurrentIndex(1)
    current_page = stack.currentWidget()

    cards = current_page.findChildren(QFrame, "settingsCapabilityCard")
    detect_buttons = current_page.findChildren(QPushButton, "settingsDetectButton")
    install_buttons = current_page.findChildren(QPushButton, "settingsInstallButton")
    cloud_buttons = current_page.findChildren(QPushButton, "settingsCloudConfigButton")
    labels = "\n".join(label.text() for label in current_page.findChildren(QLabel))

    assert len(cards) >= 4
    assert "Python 环境" in labels
    assert "R 环境" in labels
    assert "ImageJ/Fiji" in labels
    assert "外部图像分析引擎" in labels
    assert detect_buttons
    assert all(button.isEnabled() for button in detect_buttons)
    assert all(button.property("moduleKey") == ModuleKey.SETTINGS.value for button in detect_buttons)
    assert all(button.property("semanticKey") == PageKey.SETTINGS_EXTERNAL_CAPABILITIES.value for button in detect_buttons)
    detect_buttons[0].click()
    assert detect_buttons[0].property("lastDetectionStatus")
    assert detect_buttons[0].toolTip() == detect_buttons[0].property("lastDetectionStatus")
    assert install_buttons
    assert all(button.isEnabled() for button in install_buttons)
    assert all(button.property("userTriggeredInstallAllowed") is True for button in install_buttons)
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


def test_settings_analysis_resources_exposes_r_enrichment_package_gate(settings_window) -> None:
    nav = settings_window.findChild(QTabBar, "settingsSecondaryNav")
    stack = settings_window.findChild(QStackedWidget, "settingsContentStack")
    nav.setCurrentIndex(2)
    current_page = stack.currentWidget()

    labels = "\n".join(label.text() for label in current_page.findChildren(QLabel))
    detect_button = current_page.findChild(QPushButton, "detectREnrichmentBackendButton")
    result_text = current_page.findChild(QPlainTextEdit, "rEnrichmentBackendDetectionText")
    gate = current_page.findChild(QFrame, "settingsREnrichmentBackendGate")

    assert gate is not None
    assert gate.property("detectOnly") is True
    assert gate.property("installAllowed") is False
    assert gate.property("downloadAllowed") is False
    assert "ReactomePA" in labels
    assert "msigdbr" in labels
    assert detect_button is not None
    assert detect_button.isEnabled()
    assert detect_button.property("semanticKey") == PageKey.SETTINGS_ANALYSIS_RESOURCES.value
    assert detect_button.property("detectOnly") is True
    assert detect_button.property("installAllowed") is False
    assert detect_button.property("downloadAllowed") is False
    assert detect_button.property("engineExecutionAllowed") is False
    assert result_text is not None
    assert "尚未在本页运行检测" in result_text.toPlainText()

    detect_button.click()

    result = result_text.toPlainText()
    assert "ReactomePA:" in result
    assert "msigdbr:" in result
    assert "install_action=none_detect_first_only" in result
    assert "packaging_policy=external_runtime_not_bundled" in result
    assert "ora_reactome=" in result


def test_settings_developer_diagnostics_are_collapsed_by_default(settings_window) -> None:
    nav = settings_window.findChild(QTabBar, "settingsSecondaryNav")
    nav.setCurrentIndex(4)

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
    assert "不会自动安装、下载、更新或连接云端" in labels


def test_settings_general_preferences_and_quick_actions_are_clickable(settings_window) -> None:
    general_button = settings_window.findChild(QPushButton, "settingsGeneralAction_language")
    quick_button = settings_window.findChild(QPushButton, "settingsQuickActionButton_updates")
    detail_panel = settings_window.findChild(QPlainTextEdit, "settingsGeneralDetailPanel")
    copy_button = settings_window.findChild(QPushButton, "settingsCopySystemInfoButton")
    overview_log = settings_window.findChild(QPushButton, "settingsOverviewLogButton")
    overview_config = settings_window.findChildren(QPushButton, "settingsCapabilityConfigureButton")[0]

    assert general_button is not None
    assert general_button.isEnabled()
    assert general_button.property("buttonBehavior") == "opens_settings_general_language_panel"
    general_button.click()
    assert general_button.property("lastActionStatus")
    assert detail_panel is not None
    assert "Settings > 通用偏好 > 界面与语言" in detail_panel.toPlainText()

    assert copy_button is not None and copy_button.isEnabled()
    copy_button.click()
    assert copy_button.property("lastActionStatus")
    assert overview_log is not None and overview_log.isEnabled()
    overview_log.click()
    assert overview_log.property("lastActionStatus")
    assert overview_config.isEnabled()
    overview_config.click()
    assert overview_config.property("lastActionStatus")

    assert quick_button is not None
    assert quick_button.isEnabled()
    assert quick_button.property("buttonBehavior") == "runs_settings_quick_action_updates"
    quick_button.click()
    assert quick_button.property("lastActionStatus")
    manifest = default_storage_root() / "settings" / "settings_runtime_manifest.json"
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["last_action"]["action_type"] == "quick_action"
    assert any(action["action_type"] == "general_preference" for action in payload["actions"])
