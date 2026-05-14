from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from app.app_identity import (
        APP_ICON_ICNS_PATH,
        APP_ICON_PNG_PATH,
        APP_NAME,
        BIOINFORMATICS_MODULE_ICON_PATH,
        LABTOOLS_MODULE_ICON_PATH,
        META_ANALYSIS_MODULE_ICON_PATH,
        UI01_LOGIN_ICON_PATHS,
        UI01_LOGIN_ICON_SHEET_PATH,
        UI02_MODULE_SELECTION_ICON_PATHS,
        UI02_MODULE_SELECTION_ICON_SHEET_PATH,
        UI03_PROJECT_HOME_ICON_PATHS,
        UI03_PROJECT_HOME_ICON_SHEET_PATH,
        apply_app_identity,
        icon_asset_statuses,
        icon_asset_summary,
        load_app_icon,
        load_module_icon,
        load_module_pixmap,
        load_ui01_login_icon,
        load_ui01_login_pixmap,
        load_ui02_module_selection_icon,
        load_ui02_module_selection_pixmap,
        load_ui03_project_home_icon,
        load_ui03_project_home_pixmap,
    )
    from app.shell.main_window import MainWindow
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_app_icon_assets_exist_and_load(qt_app) -> None:
    assert APP_ICON_PNG_PATH.exists()
    assert APP_ICON_ICNS_PATH.exists()

    icon = load_app_icon()

    assert not icon.isNull()


def test_app_identity_applies_to_qapplication(qt_app) -> None:
    icon = apply_app_identity(qt_app)

    assert not icon.isNull()
    assert qt_app.applicationName() == "BioMedPilot"
    assert qt_app.applicationDisplayName() == APP_NAME


def test_main_window_uses_app_icon(qt_app) -> None:
    window = MainWindow()

    assert window.windowTitle() == APP_NAME
    assert not window.windowIcon().isNull()


def test_module_icons_load(qt_app) -> None:
    assert BIOINFORMATICS_MODULE_ICON_PATH.exists()
    assert META_ANALYSIS_MODULE_ICON_PATH.exists()
    assert LABTOOLS_MODULE_ICON_PATH.exists()
    assert not load_module_icon("bioinformatics").isNull()
    assert not load_module_pixmap("bioinformatics").isNull()
    assert not load_module_icon("meta_analysis").isNull()
    assert not load_module_pixmap("meta_analysis").isNull()
    assert not load_module_icon("labtools").isNull()
    assert not load_module_pixmap("labtools").isNull()


def test_ui01_login_icon_assets_load(qt_app) -> None:
    assert UI01_LOGIN_ICON_SHEET_PATH.exists()
    assert set(UI01_LOGIN_ICON_PATHS) == {
        "brand",
        "user",
        "security",
        "login",
        "register",
        "forgot",
        "subscription",
        "vip",
        "license",
        "preview",
    }
    for key, path in UI01_LOGIN_ICON_PATHS.items():
        assert path.exists(), key
        assert not load_ui01_login_icon(key).isNull(), key
        assert not load_ui01_login_pixmap(key).isNull(), key


def test_ui02_module_selection_icon_assets_load(qt_app) -> None:
    assert UI02_MODULE_SELECTION_ICON_SHEET_PATH.exists()
    assert set(UI02_MODULE_SELECTION_ICON_PATHS) == {
        "dashboard",
        "settings",
        "developer_preview",
        "recent_projects",
        "local_environment",
        "current_user",
        "version",
        "logout",
        "workspace",
        "project_entry",
    }
    for key, path in UI02_MODULE_SELECTION_ICON_PATHS.items():
        assert path.exists(), key
        assert not load_ui02_module_selection_icon(key).isNull(), key
        assert not load_ui02_module_selection_pixmap(key).isNull(), key


def test_ui03_project_home_icon_assets_load(qt_app) -> None:
    assert UI03_PROJECT_HOME_ICON_SHEET_PATH.exists()
    assert set(UI03_PROJECT_HOME_ICON_PATHS) == {
        "create_project",
        "open_existing_project",
        "project_name",
        "save_location",
        "folder_picker",
        "validation_status",
        "project_manifest",
        "project_config",
        "current_project_summary",
        "continue_next_step",
        "project_folder_structure",
        "project_warning",
    }
    for key, path in UI03_PROJECT_HOME_ICON_PATHS.items():
        assert path.exists(), key
        assert not load_ui03_project_home_icon(key).isNull(), key
        assert not load_ui03_project_home_pixmap(key).isNull(), key


def test_icon_asset_inventory_reports_generated_and_pending_slots(qt_app) -> None:
    statuses = icon_asset_statuses()
    summary = icon_asset_summary()

    assert summary["total"] == len(statuses)
    assert summary["generated"] >= 35
    assert summary["connected"] >= 33
    assert summary["pending"] >= 1
    assert any(item.label == "UI-04 数据来源图标组" and item.state_label == "待生成" for item in statuses)
    assert any(item.label == "UI-01 Subscription 图标" and item.state_label == "已生成，等待接入" for item in statuses)
    assert any("UI-02 模块选择首页" in item.usages for item in statuses if item.key == "module.bioinformatics")
    assert any("UI-02 模块选择首页" in item.usages for item in statuses if item.key == "module.labtools")
    assert any(item.label == "UI-02 Dashboard 图标" and item.state_label == "已生成并接入" for item in statuses)
    assert any(item.label == "UI-03 创建项目图标" and item.state_label == "已生成并接入" for item in statuses)
