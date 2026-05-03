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


def test_login_widget_instantiates(qt_app) -> None:
    widget = BioMedPilotLoginWidget()
    assert widget.objectName() == "loginPage"


def test_login_page_uses_ui01_icons(qt_app) -> None:
    widget = BioMedPilotLoginWidget()

    brand_icon = widget.findChild(QLabel, "loginBrandIcon")
    username_input = widget.findChild(QLineEdit, "usernameInput")
    password_input = widget.findChild(QLineEdit, "passwordInput")
    login_button = widget.findChild(QPushButton, "primaryButton")
    meta_icons = widget.findChildren(QLabel, "loginMetaIcon")

    assert brand_icon is not None
    assert brand_icon.pixmap() is not None and not brand_icon.pixmap().isNull()
    assert username_input is not None and username_input.actions()
    assert password_input is not None and password_input.actions()
    assert login_button is not None and not login_button.icon().isNull()
    assert len(meta_icons) >= 5


def test_login_page_matches_reference_layout_sections(qt_app) -> None:
    widget = BioMedPilotLoginWidget()

    assert widget.findChild(QLabel, "loginTopTitle") is not None
    assert widget.findChild(QLabel, "loginTopVersion") is not None
    assert widget.findChild(QLabel, "loginBrandIcon") is not None
    assert widget.findChild(QLabel, "brandChineseName").text() == "医研智析"
    assert widget.findChild(QLineEdit, "usernameInput").placeholderText() == "用户名"
    assert widget.findChild(QLineEdit, "passwordInput").placeholderText() == "密码"

    dock_tiles = widget.findChildren(QLabel, "loginDockLabel")
    assert dock_tiles == []
    assert widget.findChild(QLabel, "loginDockIcon") is None


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("", ""),
        ("doctor", ""),
        ("", "local-password"),
    ],
)
def test_login_requires_username_and_password(qt_app, username: str, password: str) -> None:
    widget = BioMedPilotLoginWidget()
    widget.set_credentials(username, password)

    assert widget.attempt_login() is None
    assert widget.session() is None
    assert widget.error_message() == "请输入用户名和密码。"


def test_non_empty_credentials_create_local_session(qt_app) -> None:
    widget = BioMedPilotLoginWidget()
    widget.set_credentials("researcher", "local-password")

    session = widget.attempt_login()

    assert isinstance(session, LocalSession)
    assert session.username == "researcher"
    assert session.role == "local_test_user"
    assert session.tier == "Developer Preview"
    assert session.license_status == "local_testing"
    assert session.login_time
    assert not hasattr(session, "password")
    assert widget.error_message() == ""


def test_successful_login_triggers_callback(qt_app) -> None:
    sessions: list[LocalSession] = []
    widget = BioMedPilotLoginWidget(on_login=sessions.append)
    widget.set_credentials("researcher", "local-password")

    session = widget.attempt_login()

    assert sessions == [session]


def test_main_window_starts_at_login_and_enters_dashboard(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()

    assert window.current_workspace_key() == "login"
    window._login_page.set_credentials("researcher", "local-password")
    session = window._login_page.attempt_login()

    assert window.current_workspace_key() == "dashboard"
    assert window.current_session() == session


def test_settings_page_displays_icon_asset_details(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()
    window._login_page.set_credentials("researcher", "local-password")
    window._login_page.attempt_login()
    window.show_settings()

    labels = "\n".join(label.text() for label in window.findChildren(QLabel))

    assert "图标资源状态" in labels
    assert "已生成" in labels
    assert "待生成" in labels
    assert "UI-04 数据来源图标组" in labels
