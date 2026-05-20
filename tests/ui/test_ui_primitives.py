from __future__ import annotations

import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton

from app.shared.ui_components import (
    diagnostic_disclosure_title,
    make_button,
    make_card,
    make_empty_state,
    make_status_chip,
)
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
    assert chip.property("iconHint") == token.icon_hint
    assert token.background in chip.styleSheet()


def test_button_sets_role_and_size_without_business_page_dependency(qt_app) -> None:
    button = make_button("Run preflight", role="primary_action", size="small")
    assert isinstance(button, QPushButton)
    assert button.objectName() == "primaryActionButton"
    assert button.property("uiPrimitive") == "button"
    assert button.property("buttonRole") == "primary_action"
    assert button.property("buttonSize") == "small"


def test_card_and_empty_state_primitives(qt_app) -> None:
    card = make_card(object_name="settingsResourceCard")
    assert card.objectName() == "settingsResourceCard"
    assert card.property("uiPrimitive") == "card"

    empty = make_empty_state("No project", "Create or open a project first.", action_text="Open")
    assert empty.objectName() == "uiEmptyState"
    assert empty.property("uiPrimitive") == "empty_state"
    assert empty.findChild(QLabel, "uiEmptyStateTitle").text() == "No project"
    assert empty.findChild(QPushButton).property("buttonRole") == "secondary"


def test_diagnostic_disclosure_title_marks_developer_scope() -> None:
    assert diagnostic_disclosure_title("Project logs") == "Project logs / Developer diagnostics"
