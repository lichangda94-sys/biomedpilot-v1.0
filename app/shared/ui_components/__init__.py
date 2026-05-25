"""Shared UI component namespace."""

from app.shared.ui_components.primitives import (
    diagnostic_disclosure_title,
    make_button,
    make_card,
    make_empty_state,
    make_status_chip,
)
from app.shared.ui_components.workbench import (
    WorkbenchActionSpec,
    WorkbenchNavItem,
    make_workbench_action_bar,
    make_workbench_content_area,
    make_workbench_disabled_action,
    make_workbench_empty_state,
    make_workbench_notice,
    make_workbench_right_panel,
    make_workbench_secondary_nav,
    make_workbench_section,
    make_workbench_shell,
    make_workbench_status_row,
    make_workbench_table,
)

__all__ = [
    "WorkbenchActionSpec",
    "WorkbenchNavItem",
    "diagnostic_disclosure_title",
    "make_button",
    "make_card",
    "make_empty_state",
    "make_status_chip",
    "make_workbench_action_bar",
    "make_workbench_content_area",
    "make_workbench_disabled_action",
    "make_workbench_empty_state",
    "make_workbench_notice",
    "make_workbench_right_panel",
    "make_workbench_secondary_nav",
    "make_workbench_section",
    "make_workbench_shell",
    "make_workbench_status_row",
    "make_workbench_table",
]
