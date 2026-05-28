from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QScrollArea, QTableView

    from app.shell.dashboard import build_dashboard_model
    from app.shell.login import LocalSession
    from app.shell.module_selection import ModuleSelectionWidget
    from app.shared.semantic_keys import BrandKey, ModuleKey, NavKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    QScrollArea = None  # type: ignore[assignment]
    build_dashboard_model = None  # type: ignore[assignment]
    LocalSession = None  # type: ignore[assignment]
    ModuleSelectionWidget = None  # type: ignore[assignment]
    BrandKey = None  # type: ignore[assignment]
    ModuleKey = None  # type: ignore[assignment]
    NavKey = None  # type: ignore[assignment]
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


def _dispose_window(window) -> None:
    window.close()
    window.deleteLater()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()


def test_module_selection_widget_instantiates(qt_app) -> None:
    widget = _widget()
    assert widget.objectName() == "moduleSelectionPage"
    assert widget.session_display()["username"] == "未登录本地测试用户"
    assert widget.findChild(QScrollArea, "moduleSelectionScrollArea") is not None


def test_module_selection_displays_global_shell_brand(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    title = widget.findChild(QLabel, "dashboardTitle")
    subtitle = widget.findChild(QLabel, "dashboardSubtitle")
    labels = "\n".join(label.text() for label in widget.findChildren(QLabel))

    assert title is not None
    assert title.property("semanticKey") == BrandKey.PRIMARY.value
    assert subtitle is not None
    assert subtitle.property("semanticKey") == BrandKey.SECONDARY.value
    assert "订阅 / VIP" not in labels


def test_module_selection_displays_recent_projects_table_without_status_footer(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    recent = widget.findChild(QFrame, "dashboardRecentProjectsCard")
    table = widget.findChild(QTableView, "dashboardRecentProjectsTable")

    assert recent is not None
    assert recent.property("uiPrimitive") == "dashboard_recent_projects"
    assert recent.property("projectCenter") is False
    assert table is not None
    assert table.property("uiPrimitive") == "project_recent_table"
    assert table.property("dashboardOnly") is True
    assert table.property("horizontalOverflow") is True
    assert "最近项目 / Recent Projects" in labels
    assert "本地环境可用" not in labels
    assert "外部引擎可选配置" not in labels
    assert "分析资源可管理" not in labels
    assert "测试反馈入口" not in labels


def test_three_module_cards_are_visible(qt_app, local_session: LocalSession) -> None:
    widget = _widget(local_session)

    module_titles = widget.findChildren(QLabel, "moduleTitle")
    module_cards = widget.findChildren(QFrame, "moduleCard")
    icons = widget.findChildren(QLabel, "moduleIcon")
    visible_icons = [icon for icon in icons if not icon.isHidden() and icon.pixmap() is not None and not icon.pixmap().isNull()]

    assert [card.property("moduleKey") for card in module_cards] == [
        ModuleKey.BIOINFORMATICS.value,
        ModuleKey.META_ANALYSIS.value,
        ModuleKey.LABTOOLS.value,
    ]
    assert all(card.property("usabilityRole") == "module_entry_card" for card in module_cards)
    assert all(card.property("uiPrimitive") == "module_entry_card" for card in module_cards)
    assert all(card.accessibleName() for card in module_cards)
    assert [label.property("semanticKey") for label in module_titles] == [card.property("moduleKey") for card in module_cards]
    assert len(icons) == 3
    assert len(visible_icons) == 3


def test_bioinformatics_button_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_bioinformatics=lambda: events.append("bio"))

    button = widget.findChild(QPushButton, "bioModuleButton")
    assert button.property("moduleKey") == ModuleKey.BIOINFORMATICS.value
    assert button.property("navKey") == NavKey.BIOINFORMATICS.value
    assert button.property("semanticKey") == ModuleKey.BIOINFORMATICS.value
    assert button.property("usabilityRole") == "module_entry_action"
    assert button.accessibleName()
    assert not button.icon().isNull()
    button.click()

    assert events == ["bio"]


def test_bioinformatics_card_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_bioinformatics=lambda: events.append("bio"))

    card = widget.findChildren(QFrame, "moduleCard")[0]
    QTest.mouseClick(card, Qt.LeftButton)

    assert events == ["bio"]


def test_meta_button_triggers_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_meta_analysis=lambda: events.append("meta"))

    button = widget.findChild(QPushButton, "metaModuleButton")
    assert button.property("moduleKey") == ModuleKey.META_ANALYSIS.value
    assert button.property("navKey") == NavKey.META_ANALYSIS.value
    assert not button.icon().isNull()
    button.click()

    assert events == ["meta"]


def test_labtools_button_triggers_low_fidelity_shell_callback(qt_app, local_session: LocalSession) -> None:
    events: list[str] = []
    widget = _widget(local_session, on_open_labtools=lambda: events.append("labtools"))

    button = widget.findChild(QPushButton, "labtoolsModuleButton")
    assert button.property("moduleKey") == ModuleKey.LABTOOLS.value
    assert button.property("navKey") == NavKey.LABTOOLS.value
    assert not button.icon().isNull()
    button.click()

    assert events == ["labtools"]


def test_main_window_module_buttons_enter_expected_workspaces(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()

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

        window.show_dashboard()
        labtools_button = window._dashboard_page.findChild(QPushButton, "labToolsModuleButton")
        labtools_button.click()
        assert window.current_workspace_key() == "labtools"
        assert window._labtools_page.page_keys() == (
            "home",
            "general_calculators",
            "imagej_fiji",
            "reagent_records",
            "cell_experiments",
            "western_blot",
            "pcr_qpcr",
            "elisa_absorbance",
        )

        window.show_dashboard()
        labtools_button = window._dashboard_page.findChild(QPushButton, "labtoolsModuleButton")
        labtools_button.click()
        assert window.current_workspace_key() == "labtools"
    finally:
        _dispose_window(window)


def test_about_and_test_feedback_shells_are_reachable(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()

        window.show_about()
        assert window.current_workspace_key() == "about"
        about_labels = "\n".join(label.text() for label in window.findChildren(QLabel))
        assert "About / 关于" in about_labels
        assert "萤火虫 / Firefly" in about_labels

        window.show_test_feedback()
        assert window.current_workspace_key() == "test_feedback"
        feedback_button = window.findChild(QPushButton, "generateTestFeedbackButton")
        lan_feedback_button = window.findChild(QPushButton, "generateLanFeedbackButton")
        assert feedback_button is not None
        assert feedback_button.text() == "生成测试反馈模板"
        assert lan_feedback_button is not None
        assert lan_feedback_button.text() == "生成 LAN 真实测试反馈报告"
        assert lan_feedback_button.property("feedbackType") == "labtools_lan_real_world"
        assert lan_feedback_button.property("networkRequestAllowed") is False
    finally:
        _dispose_window(window)


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
    try:
        window._welcome_page.enter_workspace()
        window.open_project_record(record)

        assert window.current_workspace_key() == "meta_analysis"
        assert window._meta_analysis_page.current_project_dir() == (tmp_path / "meta_project").resolve()
    finally:
        _dispose_window(window)
