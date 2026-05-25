from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
from app.shared.ui_components.primitives import make_button, make_card, make_empty_state, make_status_chip


@dataclass(frozen=True)
class WorkbenchNavItem:
    key: str
    label: str
    status_key: str = "planned"
    semantic_key: str = ""
    enabled: bool = True
    current: bool = False
    tooltip: str = ""


@dataclass(frozen=True)
class WorkbenchActionSpec:
    key: str
    label: str
    role: str = "secondary"
    enabled: bool = False
    disabled_state: str = "disabled_boundary"
    tooltip: str = ""


def make_workbench_shell(
    *,
    title: str,
    subtitle: str = "",
    object_name: str = "workbenchShell",
    module_key: str = "",
    page_key: str = "",
    status_widgets: Sequence[object] = (),
    secondary_nav: object | None = None,
    main_content: object | None = None,
    right_panel: object | None = None,
    action_bar: object | None = None,
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

    shell = QFrame()
    shell.setObjectName(object_name)
    shell.setProperty("uiPrimitive", "workbench_shell")
    shell.setProperty("moduleKey", module_key)
    shell.setProperty("pageKey", page_key)
    shell.setProperty("layoutPolishNoOverlap", True)
    shell.setFrameShape(QFrame.NoFrame)
    shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    shell.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            background: {COLORS["background"]};
            border: 0;
        }}
        """
    )

    root = QVBoxLayout(shell)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(SPACING["lg"])

    header = QFrame()
    header.setObjectName("workbenchHeader")
    header.setProperty("uiPrimitive", "workbench_header")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(SPACING["md"])

    title_block = QWidget()
    title_block.setObjectName("workbenchTitleBlock")
    title_layout = QVBoxLayout(title_block)
    title_layout.setContentsMargins(0, 0, 0, 0)
    title_layout.setSpacing(SPACING["xs"])

    title_label = QLabel(title)
    title_label.setObjectName("workbenchPageTitle")
    title_label.setProperty("uiPrimitive", "workbench_title")
    title_label.setStyleSheet(
        f"color: {COLORS['text']}; font-size: {FONT_SIZE['hero']}px; font-weight: 800;"
    )
    title_label.setWordWrap(True)
    title_layout.addWidget(title_label)

    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("workbenchPageSubtitle")
        subtitle_label.setProperty("uiPrimitive", "workbench_subtitle")
        subtitle_label.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;"
        )
        subtitle_label.setWordWrap(True)
        title_layout.addWidget(subtitle_label)

    header_layout.addWidget(title_block, 1)

    for widget in status_widgets:
        header_layout.addWidget(widget, 0, Qt.AlignTop)

    root.addWidget(header)

    body = QFrame()
    body.setObjectName("workbenchBody")
    body.setProperty("uiPrimitive", "workbench_body")
    body_layout = QHBoxLayout(body)
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.setSpacing(SPACING["lg"])

    if secondary_nav is not None:
        body_layout.addWidget(secondary_nav, 0)
    body_layout.addWidget(main_content or make_workbench_content_area(), 1)
    if right_panel is not None:
        body_layout.addWidget(right_panel, 0)

    root.addWidget(body, 1)

    if action_bar is not None:
        root.addWidget(action_bar)

    return shell


def make_workbench_secondary_nav(
    items: Sequence[WorkbenchNavItem],
    *,
    object_name: str = "workbenchSecondaryNav",
    title: str = "Workflow",
):
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

    nav = QFrame()
    nav.setObjectName(object_name)
    nav.setProperty("uiPrimitive", "workbench_secondary_nav")
    nav.setMinimumWidth(188)
    nav.setMaximumWidth(244)
    nav.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["panel"]}px;
        }}
        QPushButton#workbenchSecondaryNavItem {{
            text-align: left;
            border-radius: {RADIUS["sm"]}px;
            padding: 8px 10px;
            color: {COLORS["text"]};
            background: transparent;
            border: 1px solid transparent;
        }}
        QPushButton#workbenchSecondaryNavItem[currentStep="true"] {{
            background: {COLORS["bio_soft"]};
            border: 1px solid #D6E2EA;
            color: {COLORS["bio"]};
            font-weight: 750;
        }}
        QPushButton#workbenchSecondaryNavItem:disabled {{
            color: #94A3B8;
        }}
        """
    )
    layout = QVBoxLayout(nav)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])

    title_label = QLabel(title)
    title_label.setObjectName("workbenchSecondaryNavTitle")
    title_label.setStyleSheet(
        f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px; font-weight: 800;"
    )
    layout.addWidget(title_label)

    for item in items:
        button = make_button(item.label, role="ghost", size="small")
        button.setObjectName("workbenchSecondaryNavItem")
        button.setEnabled(item.enabled)
        button.setProperty("uiPrimitive", "workbench_secondary_nav_item")
        button.setProperty("pageKey", item.key)
        button.setProperty("statusKey", item.status_key)
        button.setProperty("semanticKey", item.semantic_key)
        button.setProperty("currentStep", item.current)
        button.setProperty("formalActionEnabled", False)
        button.setProperty("fileWriteAllowed", False)
        if item.tooltip:
            button.setToolTip(item.tooltip)
        button.style().unpolish(button)
        button.style().polish(button)
        layout.addWidget(button)

    layout.addStretch(1)
    return nav


def make_workbench_content_area(
    content_widgets: Iterable[object] = (),
    *,
    object_name: str = "workbenchContentArea",
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

    scroll = QScrollArea()
    scroll.setObjectName(object_name)
    scroll.setProperty("uiPrimitive", "workbench_content_area")
    scroll.setProperty("layoutPolishNoOverlap", True)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    content = QWidget()
    content.setObjectName(f"{object_name}Viewport")
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["lg"])
    for widget in content_widgets:
        layout.addWidget(widget)
    layout.addStretch(1)
    scroll.setWidget(content)
    return scroll


def make_workbench_right_panel(
    *,
    title: str,
    content_widgets: Iterable[object] = (),
    object_name: str = "workbenchRightPanel",
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    panel = make_card(object_name=object_name)
    panel.setProperty("uiPrimitive", "workbench_right_panel")
    panel.setMinimumWidth(280)
    panel.setMaximumWidth(360)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])

    title_label = QLabel(title)
    title_label.setObjectName("workbenchRightPanelTitle")
    title_label.setStyleSheet(
        f"color: {COLORS['text']}; font-size: {FONT_SIZE['card_title']}px; font-weight: 800;"
    )
    title_label.setWordWrap(True)
    layout.addWidget(title_label)

    for widget in content_widgets:
        layout.addWidget(widget)
    layout.addStretch(1)
    return panel


def make_workbench_action_bar(
    actions: Sequence[WorkbenchActionSpec],
    *,
    object_name: str = "workbenchActionBar",
):
    from PySide6.QtWidgets import QFrame, QHBoxLayout

    bar = QFrame()
    bar.setObjectName(object_name)
    bar.setProperty("uiPrimitive", "workbench_action_bar")
    bar.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["panel"]}px;
        }}
        """
    )
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
    layout.setSpacing(SPACING["sm"])
    layout.addStretch(1)
    for action in actions:
        button = make_button(action.label, role=action.role)
        button.setObjectName("workbenchActionButton")
        button.setProperty("uiPrimitive", "workbench_action_button")
        button.setProperty("actionKey", action.key)
        button.setProperty("disabledState", action.disabled_state)
        button.setProperty("formalActionEnabled", False)
        button.setProperty("fileWriteAllowed", False)
        button.setEnabled(action.enabled)
        if action.tooltip:
            button.setToolTip(action.tooltip)
        layout.addWidget(button)
    return bar


def make_workbench_status_row(
    items: Sequence[tuple[str, str]],
    *,
    object_name: str = "workbenchStatusRow",
):
    from PySide6.QtWidgets import QFrame, QHBoxLayout

    row = QFrame()
    row.setObjectName(object_name)
    row.setProperty("uiPrimitive", "workbench_status_row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["sm"])
    for label, status_key in items:
        layout.addWidget(make_status_chip(label, status_key=status_key))
    layout.addStretch(1)
    return row


def make_workbench_section(
    *,
    title: str,
    body: str = "",
    object_name: str = "workbenchSection",
    content_widgets: Iterable[object] = (),
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    section = make_card(object_name=object_name)
    section.setProperty("uiPrimitive", "workbench_section")
    layout = QVBoxLayout(section)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])

    title_label = QLabel(title)
    title_label.setObjectName("workbenchSectionTitle")
    title_label.setWordWrap(True)
    title_label.setStyleSheet(
        f"color: {COLORS['text']}; font-size: {FONT_SIZE['card_title']}px; font-weight: 800;"
    )
    layout.addWidget(title_label)

    if body:
        body_label = QLabel(body)
        body_label.setObjectName("workbenchSectionBody")
        body_label.setWordWrap(True)
        body_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
        layout.addWidget(body_label)

    for widget in content_widgets:
        layout.addWidget(widget)
    return section


def make_workbench_notice(
    text: str,
    *,
    severity: str = "info",
    object_name: str = "workbenchNotice",
):
    from PySide6.QtWidgets import QLabel

    palette = {
        "warning": (COLORS["warning_soft"], COLORS["warning_border"], "#92400E"),
        "blocker": (COLORS["danger_soft"], COLORS["danger_border"], COLORS["danger"]),
        "success": (COLORS["success_soft"], COLORS["success_border"], "#0E6F66"),
        "info": (COLORS["bio_soft"], "#D6E2EA", COLORS["bio"]),
    }
    background, border, text_color = palette.get(severity, palette["info"])
    notice = QLabel(text)
    notice.setObjectName(object_name)
    notice.setProperty("uiPrimitive", "workbench_notice")
    notice.setProperty("severity", severity)
    notice.setWordWrap(True)
    notice.setStyleSheet(
        f"""
        QLabel#{object_name} {{
            color: {text_color};
            background: {background};
            border: 1px solid {border};
            border-radius: {RADIUS["sm"]}px;
            padding: 10px 12px;
            font-size: {FONT_SIZE["body"]}px;
        }}
        """
    )
    return notice


def make_workbench_disabled_action(
    text: str,
    *,
    action_key: str = "",
    disabled_state: str = "disabled_boundary",
    tooltip: str = "",
):
    button = make_button(text, role="secondary")
    button.setObjectName("workbenchDisabledAction")
    button.setEnabled(False)
    button.setProperty("uiPrimitive", "workbench_disabled_action")
    button.setProperty("actionKey", action_key)
    button.setProperty("disabledState", disabled_state)
    button.setProperty("formalActionEnabled", False)
    button.setProperty("fileWriteAllowed", False)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def make_workbench_table(
    *,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    object_name: str = "workbenchTable",
):
    from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

    table = QTableWidget(len(rows), len(headers))
    table.setObjectName(object_name)
    table.setProperty("uiPrimitive", "workbench_table")
    table.setProperty("readOnly", True)
    table.setHorizontalHeaderLabels(list(headers))
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
    return table


def make_workbench_empty_state(
    title: str,
    body: str,
    *,
    empty_state_key: str | None = None,
    semantic_key: str | None = None,
):
    empty = make_empty_state(title, body, empty_state_key=empty_state_key, semantic_key=semantic_key)
    empty.setObjectName("workbenchEmptyState")
    empty.setProperty("uiPrimitive", "workbench_empty_state")
    return empty


__all__ = [
    "WorkbenchActionSpec",
    "WorkbenchNavItem",
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
