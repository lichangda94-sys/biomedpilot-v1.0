from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QScrollArea

    from app.shell.dashboard import build_dashboard_model
    from app.shell.login import LocalSession
    from app.shell.module_selection import ModuleSelectionWidget
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    QScrollArea = None  # type: ignore[assignment]
    build_dashboard_model = None  # type: ignore[assignment]
    LocalSession = None  # type: ignore[assignment]
    ModuleSelectionWidget = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def local_session() -> LocalSession:
    return LocalSession(
        username="researcher",
        role="local_test_user",
        tier="Developer Preview",
        license_status="local_testing",
        login_time="2026-04-30T10:00:00+08:00",
    )


def _widget(session: LocalSession | None = None, **callbacks) -> ModuleSelectionWidget:
    return ModuleSelectionWidget(
        dashboard=build_dashboard_model(),
        session=session,
        **callbacks,
    )


def test_module_selection_widget_instantiates(qt_app) -> None:
    widget = _widget()
    assert widget.objectName() == "moduleSelectionPage"
    assert widget.session_display()["username"] == "未登录本地测试用户"
    assert widget.findChild(QScrollArea, "moduleSelectionScrollArea") is not None


def test_module_selection_displays_session(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    display = widget.session_display()

    assert display["username"] == "researcher"
    assert display["tier"] == "Developer Preview"
    assert display["license_status"] == "local_testing"


def test_module_selection_displays_icon_asset_summary(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    support_text = "\n".join(label.text() for label in widget.findChildren(QLabel, "supportLine"))

    assert "图标资源：已生成" in support_text
    assert "待生成" in support_text


def test_bioinformatics_button_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_bioinformatics=lambda: events.append("bio"))

    button = widget.findChild(QPushButton, "bioModuleButton")
    assert button.text() == "进入生信分析模块"
    assert not button.icon().isNull()
    button.click()

    assert events == ["bio"]


def test_bioinformatics_card_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_bioinformatics=lambda: events.append("bio"))

    card = widget.findChildren(QFrame, "moduleCard")[0]
    QTest.mouseClick(card, Qt.LeftButton)

    assert events == ["bio"]


def test_module_icons_are_visible(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    icons = widget.findChildren(QLabel, "moduleIcon")
    visible_icons = [icon for icon in icons if not icon.isHidden() and icon.pixmap() is not None and not icon.pixmap().isNull()]

    assert len(icons) == 2
    assert len(visible_icons) == 2


def test_ui02_page_icons_are_visible(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    icons = widget.findChildren(QLabel, "ui02Icon")
    visible_icons = [icon for icon in icons if not icon.isHidden() and icon.pixmap() is not None and not icon.pixmap().isNull()]

    assert len(visible_icons) >= 8


def test_meta_button_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_meta_analysis=lambda: events.append("meta"))

    button = widget.findChild(QPushButton, "metaModuleButton")
    assert button.text() == "进入 Meta 分析模块"
    assert not button.icon().isNull()
    button.click()

    assert events == ["meta"]


def test_meta_module_card_mentions_current_workflow(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    descriptions = [label.text() for label in widget.findChildren(QLabel, "moduleDescription")]

    assert any("中文 18 步工作流" in text for text in descriptions)
    assert any("文献获取" in text for text in descriptions)
    assert any("testing-level / 待开发" in text for text in descriptions)


def test_logout_button_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_logout=lambda: events.append("logout"))

    button = widget.findChild(QPushButton, "logoutButton")
    button.click()

    assert events == ["logout"]


def test_main_window_logout_returns_to_login_and_clears_session(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()
    assert window.minimumWidth() <= 860
    assert window.minimumHeight() <= 560
    window._login_page.set_credentials("researcher", "local-password")
    window._login_page.attempt_login()

    assert window.current_workspace_key() == "dashboard"
    assert window.current_session() is not None

    logout_button = window._dashboard_page.findChild(QPushButton, "logoutButton")
    logout_button.click()

    assert window.current_workspace_key() == "login"
    assert window.current_session() is None
    assert window._login_page.session() is None


def test_main_window_module_buttons_enter_existing_workspaces(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()
    window._login_page.set_credentials("researcher", "local-password")
    window._login_page.attempt_login()

    bio_button = window._dashboard_page.findChild(QPushButton, "bioModuleButton")
    bio_button.click()
    assert window.current_workspace_key() == "bioinformatics"

    window.show_dashboard()
    meta_button = window._dashboard_page.findChild(QPushButton, "metaModuleButton")
    meta_button.click()
    assert window.current_workspace_key() == "meta_analysis"
    assert window._meta_analysis_page.page_keys()[:4] == (
        "workflow_home",
        "pico_workspace",
        "search_strategy",
        "literature_import",
    )


def test_main_window_open_meta_project_binds_workspace_project_dir(qt_app, tmp_path) -> None:
    from app.shared.project_center.service import ProjectRecord
    from app.shell.main_window import MainWindow

    record = ProjectRecord(
        project_id="meta-test",
        project_name="Meta UI Test",
        project_type="meta_analysis",
        created_at="2026-05-10T00:00:00+08:00",
        updated_at="2026-05-10T00:00:00+08:00",
        project_dir=str(tmp_path / "meta_project"),
        current_stage="created",
        status="active",
    )
    window = MainWindow()
    window._login_page.set_credentials("researcher", "local-password")
    window._login_page.attempt_login()
    window.open_project_record(record)

    assert window.current_workspace_key() == "meta_analysis"
    assert window._meta_analysis_page.current_project_dir() == (tmp_path / "meta_project").resolve()
