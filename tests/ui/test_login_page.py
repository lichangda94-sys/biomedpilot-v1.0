from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

    from app.shell.login import BioMedPilotLoginWidget, LocalSession
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    BioMedPilotLoginWidget = None  # type: ignore[assignment]
    LocalSession = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_welcome_widget_instantiates(qt_app) -> None:
    widget = BioMedPilotLoginWidget()
    assert widget.objectName() == "welcomePage"


def test_welcome_page_uses_existing_icons_without_replacing_resources(qt_app) -> None:
    widget = BioMedPilotLoginWidget()

    brand_icon = widget.findChild(QLabel, "loginBrandIcon")
    enter_button = widget.findChild(QPushButton, "primaryButton")

    assert brand_icon is not None
    assert brand_icon.pixmap() is not None and not brand_icon.pixmap().isNull()
    assert enter_button is not None and not enter_button.icon().isNull()
    assert enter_button.isDefault()
    assert enter_button.accessibleName() == "Enter local workspace"
    assert enter_button.property("usabilityRole") == "primary_entry_action"


def test_welcome_page_removes_visible_credential_flow(qt_app) -> None:
    widget = BioMedPilotLoginWidget()

    labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    username_input = widget.findChild(QLineEdit, "usernameInput")
    password_input = widget.findChild(QLineEdit, "passwordInput")

    assert "萤火虫 / Firefly" in labels
    assert "BioMedPilot / 医研智析" in labels
    assert "账号" not in labels
    assert "VIP" not in labels
    assert username_input is not None and username_input.isHidden()
    assert password_input is not None and password_input.isHidden()


def test_welcome_enter_workspace_creates_local_session_without_password(qt_app) -> None:
    widget = BioMedPilotLoginWidget()
    widget.set_credentials("", "ignored")

    session = widget.enter_workspace()

    assert isinstance(session, LocalSession)
    assert session.username == "local_workspace_user"
    assert session.role == "local_test_user"
    assert session.tier == "Developer Preview"
    assert session.license_status == "local_testing"
    assert session.login_time
    assert not hasattr(session, "password")
    assert widget.error_message() == ""


def test_successful_welcome_entry_triggers_callback(qt_app) -> None:
    sessions: list[LocalSession] = []
    widget = BioMedPilotLoginWidget(on_login=sessions.append)

    session = widget.enter_workspace()

    assert sessions == [session]


def test_main_window_starts_at_welcome_and_enters_dashboard(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()

    assert window.current_workspace_key() == "welcome"
    session = window._welcome_page.enter_workspace()

    assert window.current_workspace_key() == "dashboard"
    assert window.current_session() == session


def test_settings_page_displays_icon_asset_details(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_settings()

    labels = "\n".join(label.text() for label in window.findChildren(QLabel))

    assert "图标资源状态" in labels
    assert "已生成" in labels
    assert "待生成" in labels
    assert "UI-04 数据来源图标组" in labels
