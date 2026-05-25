from __future__ import annotations

import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QFrame = QtWidgets.QFrame
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QScrollArea = QtWidgets.QScrollArea

from app.shared.ui_components import (
    AppSidebarItem,
    diagnostic_disclosure_title,
    make_action_button,
    make_app_sidebar,
    make_button,
    make_card,
    make_empty_state,
    make_icon_label,
    make_info_banner,
    make_page_header,
    make_page_shell,
    make_section_title,
    make_status_chip,
    make_workbench_card,
)
from app.shared.semantic_keys import AnalysisStatusKey
from app.ui_style_tokens import get_status_token


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_status_chip_sets_semantic_properties(qt_app) -> None:
    chip = make_status_chip(status_key="preflight_only")
    token = get_status_token("preflight_only")
    assert isinstance(chip, QLabel)
    assert chip.objectName() == "uiStatusChip"
    assert chip.property("uiPrimitive") == "status_chip"
    assert chip.property("statusKey") == "preflight_only"
    assert chip.property("semanticKey") == AnalysisStatusKey.PREFLIGHT_ONLY.value
    assert chip.property("iconHint") == token.icon_hint
    assert chip.property("semanticState") == "preflight_only"
    assert chip.property("preflight_only") is True
    assert token.background in chip.styleSheet()


def test_button_sets_role_and_size_without_business_page_dependency(qt_app) -> None:
    button = make_button(
        "Run preflight",
        role="primary_action",
        size="small",
        action_key="run_preflight",
        formal_action_enabled=False,
    )
    assert isinstance(button, QPushButton)
    assert button.objectName() == "primaryActionButton"
    assert button.property("uiPrimitive") == "button"
    assert button.property("buttonRole") == "primary_action"
    assert button.property("buttonSize") == "small"
    assert button.property("actionKey") == "run_preflight"
    assert button.property("formalActionEnabled") is False
    assert button.property("fileWriteAllowed") is False
    assert button.property("reportGenerationAllowed") is False
    assert button.property("exportAllowed") is False


def test_action_button_exposes_disabled_reason_without_enabling_business_action(qt_app) -> None:
    button = make_action_button(
        "导出 DOCX",
        role="disabled_action",
        semantic_state="export_disabled",
        action_key="export_docx",
        disabled_reason="Export is disabled until report gate passes.",
        enabled=False,
    )
    assert button.objectName() == "disabledActionButton"
    assert button.isEnabled() is False
    assert button.property("semanticState") == "export_disabled"
    assert button.property("export_disabled") is True
    assert button.property("disabledReason") == "Export is disabled until report gate passes."
    assert button.property("exportAllowed") is False


def test_card_and_empty_state_primitives(qt_app) -> None:
    card = make_card(object_name="settingsResourceCard")
    assert card.objectName() == "settingsResourceCard"
    assert card.property("uiPrimitive") == "card"
    assert card.property("semanticState") == "available"

    workbench_card = make_workbench_card()
    assert workbench_card.objectName() == "uiWorkbenchCard"
    assert workbench_card.property("uiPrimitive") == "workbench_card"

    empty = make_empty_state("No project", "Create or open a project first.", action_text="Open")
    assert empty.objectName() == "uiEmptyState"
    assert empty.property("uiPrimitive") == "empty_state"
    assert empty.property("semanticState") == "disabled"
    assert empty.findChild(QLabel, "uiEmptyStateTitle").text() == "No project"
    assert empty.findChild(QPushButton).property("buttonRole") == "secondary"


def test_page_header_shell_section_icon_and_banner_contracts(qt_app) -> None:
    chip = make_status_chip("Testing", status_key="testing")
    action = make_action_button("Open", role="secondary", action_key="open_project")
    header = make_page_header(
        title="Settings / 设置中心",
        subtitle="Local workbench preferences.",
        module_key="module.settings",
        page_key="settings.page.general",
        status_widgets=[chip],
        action_widgets=[action],
    )
    assert header.property("uiPrimitive") == "page_header"
    assert header.property("moduleKey") == "module.settings"
    assert header.findChild(QLabel, "uiPageHeaderTitle").text() == "Settings / 设置中心"
    assert header.findChild(QPushButton).property("actionKey") == "open_project"

    section = make_section_title("External engines", "Detect-only status.")
    assert section.property("uiPrimitive") == "section_title"
    assert section.findChild(QLabel, "uiSectionTitleText").text() == "External engines"

    icon_label = make_icon_label("Bioinformatics", icon_key="module.bioinformatics", semantic_key="module.bioinformatics")
    assert icon_label.property("uiPrimitive") == "icon_label"
    assert icon_label.property("semanticKey") == "module.bioinformatics"

    banner = make_info_banner(
        "Formal export remains disabled.",
        title="Export gate",
        severity="blocked",
        semantic_state="export_disabled",
    )
    assert banner.property("uiPrimitive") == "info_banner"
    assert banner.property("severity") == "blocked"
    assert banner.property("export_disabled") is True

    shell = make_page_shell(
        module_key="module.settings",
        page_key="settings.page.general",
        content_widgets=[header, section, banner],
        scrollable=True,
    )
    assert isinstance(shell, QFrame)
    assert shell.property("uiPrimitive") == "page_shell"
    assert shell.property("layoutPolishNoOverlap") is True
    assert shell.findChild(QScrollArea, "uiPageShellScrollArea") is not None


def test_app_sidebar_contract_keeps_navigation_non_business(qt_app) -> None:
    clicked = []
    sidebar = make_app_sidebar(
        items=[
            AppSidebarItem("dashboard", "Dashboard", "nav.dashboard"),
            AppSidebarItem("settings", "Settings", "nav.settings", icon_key="module.settings"),
            AppSidebarItem("about", "About", "nav.about", usability_role="auxiliary_navigation"),
        ],
        callbacks={"dashboard": lambda: clicked.append("dashboard")},
        active_key="settings",
    )
    buttons = sidebar.findChildren(QPushButton)
    assert sidebar.property("uiPrimitive") == "app_sidebar"
    assert [button.property("pageKey") for button in buttons] == ["dashboard", "settings", "about"]
    assert buttons[1].property("current") is True
    assert all(button.property("formalActionEnabled") is False for button in buttons)
    assert all(button.property("fileWriteAllowed") is False for button in buttons)


def test_diagnostic_disclosure_title_marks_developer_scope() -> None:
    assert diagnostic_disclosure_title("Project logs") == "Project logs / Developer diagnostics"
