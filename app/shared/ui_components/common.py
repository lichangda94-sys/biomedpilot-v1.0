from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from app.shared.ui_components.primitives import (
    make_action_button,
    make_empty_state,
    make_icon_label,
    make_info_banner,
    make_section_title,
    make_status_chip,
    make_workbench_card,
)
from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING


@dataclass(frozen=True)
class ComponentAction:
    key: str
    label: str
    role: str = "secondary"
    enabled: bool = True
    semantic_state: str = "available"
    disabled_reason: str = ""
    callback: Callable[[], None] | None = None


@dataclass(frozen=True)
class WorkflowStep:
    key: str
    label: str
    status_key: str = "planned"
    semantic_state: str = "planned"
    enabled: bool = True
    current: bool = False
    description: str = ""
    disabled_reason: str = ""


@dataclass(frozen=True)
class NavTab:
    key: str
    label: str
    enabled: bool = True
    semantic_state: str = "available"
    tooltip: str = ""


@dataclass(frozen=True)
class DataTableColumn:
    key: str
    label: str
    min_width: int = 128


@dataclass(frozen=True)
class KeyValueItem:
    key: str
    label: str
    value: str
    status_key: str = ""
    semantic_state: str = "available"


@dataclass(frozen=True)
class HistoryItem:
    key: str
    title: str
    timestamp: str = ""
    source: str = ""
    status_key: str = "draft"
    semantic_state: str = "draft"
    description: str = ""


@dataclass(frozen=True)
class WarningItem:
    key: str
    title: str
    reason: str
    severity: str = "warning"
    semantic_state: str = "blocked"
    source: str = ""


def make_module_entry_card(
    *,
    title: str,
    description: str,
    module_key: str = "",
    page_key: str = "",
    icon_key: str = "",
    status_label: str = "",
    status_key: str = "testing",
    action: ComponentAction | None = None,
    object_name: str = "moduleEntryCard",
):
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

    card = make_workbench_card(object_name=object_name)
    card.setProperty("uiPrimitive", "module_entry_card")
    card.setProperty("moduleKey", module_key)
    card.setProperty("pageKey", page_key)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])

    header = QHBoxLayout()
    header.setSpacing(SPACING["md"])
    if icon_key:
        header.addWidget(make_icon_label(title, icon_key=icon_key, semantic_key=module_key or page_key), 1)
    else:
        title_label = QLabel(title)
        title_label.setObjectName("moduleEntryCardTitle")
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['card_title']}px; font-weight: 800;")
        header.addWidget(title_label, 1)
    header.addWidget(make_status_chip(status_label or None, status_key=status_key), 0)
    layout.addLayout(header)

    body = QLabel(description)
    body.setObjectName("moduleEntryCardDescription")
    body.setWordWrap(True)
    body.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
    layout.addWidget(body)

    if action is not None:
        button = _button_from_action(action)
        layout.addWidget(button)
    return card


def make_workflow_stepper(
    steps: Sequence[WorkflowStep],
    *,
    title: str = "Workflow",
    object_name: str = "workflowStepper",
    on_step_requested: Callable[[str], None] | None = None,
):
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("uiPrimitive", "workflow_stepper")
    frame.setProperty("orientation", "vertical")
    frame.setStyleSheet(_panel_stylesheet(object_name))
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])
    layout.addWidget(make_section_title(title))

    for index, step in enumerate(steps, start=1):
        row = QFrame()
        row.setObjectName("workflowStepperRow")
        row.setProperty("uiPrimitive", "workflow_stepper_row")
        row.setProperty("stepKey", step.key)
        row.setProperty("currentStep", step.current)
        row.setProperty("semanticState", step.semantic_state)
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(SPACING["sm"], SPACING["sm"], SPACING["sm"], SPACING["sm"])
        row_layout.setSpacing(SPACING["xs"])

        label = f"{index}. {step.label}"
        button = make_action_button(
            label,
            role="ghost",
            semantic_state=step.semantic_state,
            action_key=step.key,
            enabled=step.enabled,
            disabled_reason=step.disabled_reason,
        )
        button.setObjectName("workflowStepperButton")
        button.setProperty("formalActionEnabled", False)
        button.setProperty("fileWriteAllowed", False)
        if on_step_requested is not None and step.enabled:
            button.clicked.connect(lambda checked=False, key=step.key: on_step_requested(key))
        row_layout.addWidget(button)
        row_layout.addWidget(make_status_chip(status_key=step.status_key, semantic_state=step.semantic_state))
        if step.description:
            description = QLabel(step.description)
            description.setObjectName("workflowStepperDescription")
            description.setWordWrap(True)
            description.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
            row_layout.addWidget(description)
        layout.addWidget(row)
    layout.addStretch(1)
    return frame


def make_secondary_nav_tabs(
    tabs: Sequence[NavTab],
    *,
    active_key: str = "",
    object_name: str = "secondaryNavTabs",
    on_tab_changed: Callable[[str], None] | None = None,
):
    from PySide6.QtWidgets import QTabBar

    tab_bar = QTabBar()
    tab_bar.setObjectName(object_name)
    tab_bar.setProperty("uiPrimitive", "secondary_nav_tabs")
    tab_bar.setProperty("activeKey", active_key)
    tab_bar.setExpanding(False)
    tab_bar.setDrawBase(False)
    active_index = 0
    for index, tab in enumerate(tabs):
        tab_bar.addTab(tab.label)
        tab_bar.setTabData(index, tab.key)
        tab_bar.setTabEnabled(index, tab.enabled)
        tab_bar.setTabToolTip(index, tab.tooltip or tab.label)
        if tab.key == active_key:
            active_index = index
    if tabs:
        tab_bar.setCurrentIndex(active_index)

    if on_tab_changed is not None:
        tab_bar.currentChanged.connect(lambda index: on_tab_changed(str(tab_bar.tabData(index))))
    tab_bar.setStyleSheet(
        f"""
        QTabBar::tab {{
            color: {COLORS["text"]};
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
            padding: 7px 12px;
            margin-right: {SPACING["xs"]}px;
            font-size: {FONT_SIZE["body"]}px;
        }}
        QTabBar::tab:selected {{
            color: {COLORS["bio"]};
            background: {COLORS["bio_soft"]};
            border: 1px solid #D6E2EA;
            font-weight: 750;
        }}
        QTabBar::tab:disabled {{
            color: {COLORS["muted"]};
            background: {COLORS["surface_muted"]};
        }}
        """
    )
    return tab_bar


def make_data_table(
    *,
    columns: Sequence[DataTableColumn],
    rows: Sequence[Mapping[str, object] | Sequence[object]],
    object_name: str = "dataTable",
    empty_title: str = "No rows",
    empty_body: str = "No data is available for this table.",
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

    table = QTableView()
    table.setObjectName(object_name)
    table.setProperty("uiPrimitive", "data_table")
    table.setProperty("readOnly", True)
    table.setProperty("horizontalOverflow", True)
    table.setProperty("emptyTitle", empty_title)
    table.setProperty("emptyBody", empty_body)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    table.horizontalHeader().setMinimumSectionSize(96)

    source_model = _DataTableModel(columns, rows)
    proxy_model = _DataTableFilterProxyModel()
    proxy_model.setSourceModel(source_model)
    proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
    proxy_model.setFilterKeyColumn(-1)
    table.setModel(proxy_model)
    for index, column in enumerate(columns):
        table.setColumnWidth(index, column.min_width)
    table._biomedpilot_source_model = source_model
    table._biomedpilot_proxy_model = proxy_model
    return table


def make_form_field_row(
    *,
    label: str,
    field_widget,
    help_text: str = "",
    validation_text: str = "",
    semantic_state: str = "available",
    required: bool = False,
    disabled_reason: str = "",
    object_name: str = "formFieldRow",
):
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

    row = QFrame()
    row.setObjectName(object_name)
    row.setProperty("uiPrimitive", "form_field_row")
    row.setProperty("semanticState", semantic_state)
    row.setProperty("required", required)
    row.setProperty("disabledReason", disabled_reason)
    layout = QVBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING["xs"])

    title = QLabel(f"{label}{' *' if required else ''}")
    title.setObjectName("formFieldRowLabel")
    title.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['secondary']}px; font-weight: 750;")
    layout.addWidget(title)
    layout.addWidget(field_widget)

    if help_text:
        help_label = QLabel(help_text)
        help_label.setObjectName("formFieldRowHelp")
        help_label.setWordWrap(True)
        help_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
        layout.addWidget(help_label)
    if validation_text:
        validation = QLabel(validation_text)
        validation.setObjectName("formFieldRowValidation")
        validation.setWordWrap(True)
        validation.setStyleSheet(f"color: {COLORS['danger']}; font-size: {FONT_SIZE['caption']}px;")
        layout.addWidget(validation)
    return row


def make_key_value_panel(
    *,
    title: str = "",
    items: Sequence[KeyValueItem],
    object_name: str = "keyValuePanel",
):
    from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

    panel = make_workbench_card(object_name=object_name)
    panel.setProperty("uiPrimitive", "key_value_panel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    if title:
        layout.addWidget(make_section_title(title))
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(SPACING["md"])
    grid.setVerticalSpacing(SPACING["sm"])
    for row_index, item in enumerate(items):
        key = QLabel(item.label)
        key.setObjectName("keyValuePanelKey")
        key.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['secondary']}px;")
        value = QLabel(item.value)
        value.setObjectName("keyValuePanelValue")
        value.setWordWrap(True)
        value.setProperty("itemKey", item.key)
        value.setProperty("semanticState", item.semantic_state)
        value.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px; font-weight: 650;")
        grid.addWidget(key, row_index, 0)
        grid.addWidget(value, row_index, 1)
        if item.status_key:
            grid.addWidget(make_status_chip(status_key=item.status_key, semantic_state=item.semantic_state), row_index, 2)
    layout.addLayout(grid)
    return panel


def make_history_list(
    *,
    items: Sequence[HistoryItem],
    object_name: str = "historyList",
):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QStandardItem, QStandardItemModel
    from PySide6.QtWidgets import QListView

    view = QListView()
    view.setObjectName(object_name)
    view.setProperty("uiPrimitive", "history_list")
    view.setProperty("readOnly", True)
    model = QStandardItemModel(view)
    for item in items:
        display = item.title
        if item.timestamp:
            display = f"{display}  ·  {item.timestamp}"
        standard_item = QStandardItem(display)
        standard_item.setEditable(False)
        standard_item.setData(item.key, Qt.UserRole)
        standard_item.setData(item.status_key, Qt.UserRole + 1)
        standard_item.setData(item.semantic_state, Qt.UserRole + 2)
        standard_item.setToolTip(item.description or item.source or item.title)
        model.appendRow(standard_item)
    view.setModel(model)
    view._biomedpilot_model = model
    return view


def make_result_panel(
    *,
    title: str,
    semantic_state: str = "draft",
    status_key: str = "draft",
    content_widgets: Sequence[object] = (),
    actions: Sequence[ComponentAction] = (),
    object_name: str = "resultPanel",
):
    from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

    panel = make_workbench_card(object_name=object_name, semantic_state=semantic_state)
    panel.setProperty("uiPrimitive", "result_panel")
    panel.setProperty("semanticState", semantic_state)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title))
    layout.addWidget(make_status_chip(status_key=status_key, semantic_state=semantic_state))
    for widget in content_widgets:
        layout.addWidget(widget)
    if actions:
        action_row = QHBoxLayout()
        action_row.addStretch(1)
        for action in actions:
            action_row.addWidget(_button_from_action(action))
        layout.addLayout(action_row)
    return panel


def make_warning_list(
    warnings: Sequence[WarningItem],
    *,
    title: str = "Warnings",
    object_name: str = "warningList",
):
    from PySide6.QtWidgets import QFrame, QVBoxLayout

    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setProperty("uiPrimitive", "warning_list")
    frame.setStyleSheet(_panel_stylesheet(object_name))
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])
    layout.addWidget(make_section_title(title))
    if not warnings:
        layout.addWidget(make_empty_state("No warnings", "There are no warnings to review.", semantic_state="available"))
    for warning in warnings:
        row_title = warning.title if not warning.source else f"{warning.source}: {warning.title}"
        layout.addWidget(
            make_info_banner(
                warning.reason,
                title=row_title,
                severity="blocked" if warning.semantic_state == "blocked" else warning.severity,
                semantic_state=warning.semantic_state,
            )
        )
    return frame


def make_gate_notice(
    *,
    title: str,
    body: str,
    blockers: Sequence[str] = (),
    disabled_actions: Sequence[ComponentAction] = (),
    status_key: str = "blocked",
    semantic_state: str = "blocked",
    object_name: str = "gateNotice",
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    panel = make_workbench_card(object_name=object_name, semantic_state=semantic_state)
    panel.setProperty("uiPrimitive", "gate_notice")
    panel.setProperty("semanticState", semantic_state)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title, body))
    layout.addWidget(make_status_chip(status_key=status_key, semantic_state=semantic_state))
    for blocker in blockers:
        label = QLabel(f"- {blocker}")
        label.setObjectName("gateNoticeBlocker")
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
        layout.addWidget(label)
    for action in disabled_actions:
        layout.addWidget(
            make_disabled_action_button(
                action.label,
                action_key=action.key,
                semantic_state=action.semantic_state,
                disabled_reason=action.disabled_reason or "This action is disabled by the current gate.",
            )
        )
    return panel


def make_file_picker_button(
    label: str,
    *,
    action_key: str = "choose_local_path",
    semantic_state: str = "available",
    disabled_reason: str = "",
    enabled: bool = True,
    on_requested: Callable[[], None] | None = None,
):
    button = make_action_button(
        label,
        role="file_picker",
        semantic_state=semantic_state,
        action_key=action_key,
        disabled_reason=disabled_reason,
        enabled=enabled,
        formal_action_enabled=False,
        file_write_allowed=False,
    )
    button.setObjectName("filePickerButton")
    button.setProperty("uiPrimitive", "file_picker_button")
    button.setProperty("localOnly", True)
    button.setProperty("formalExport", False)
    if on_requested is not None and enabled:
        button.clicked.connect(on_requested)
    return button


def make_disabled_action_button(
    label: str,
    *,
    action_key: str = "",
    semantic_state: str = "disabled",
    disabled_reason: str,
    object_name: str = "disabledActionButtonFrame",
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    frame = make_workbench_card(object_name=object_name, semantic_state=semantic_state)
    frame.setProperty("uiPrimitive", "disabled_action_button")
    frame.setProperty("actionKey", action_key)
    frame.setProperty("disabledReason", disabled_reason)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["sm"], SPACING["sm"], SPACING["sm"], SPACING["sm"])
    layout.setSpacing(SPACING["xs"])
    button = make_action_button(
        label,
        role="disabled_action",
        semantic_state=semantic_state,
        action_key=action_key,
        disabled_reason=disabled_reason,
        enabled=False,
    )
    button.setObjectName("disabledActionButton")
    layout.addWidget(button)
    reason = QLabel(disabled_reason)
    reason.setObjectName("disabledActionReason")
    reason.setWordWrap(True)
    reason.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
    layout.addWidget(reason)
    return frame


class _DataTableModel:
    pass


try:
    from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
except Exception:  # pragma: no cover
    pass
else:

    class _DataTableModel(QAbstractTableModel):  # type: ignore[no-redef]
        def __init__(self, columns: Sequence[DataTableColumn], rows: Sequence[Mapping[str, object] | Sequence[object]]) -> None:
            super().__init__()
            self._columns = tuple(columns)
            self._rows = tuple(rows)

        def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
            return 0 if parent is not None and parent.isValid() else len(self._rows)

        def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
            return 0 if parent is not None and parent.isValid() else len(self._columns)

        def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
            if not index.isValid() or role not in (Qt.DisplayRole, Qt.ToolTipRole):
                return None
            value = self._value_at(index.row(), index.column())
            return "" if value is None else str(value)

        def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
            if role != Qt.DisplayRole:
                return None
            if orientation == Qt.Horizontal and 0 <= section < len(self._columns):
                return self._columns[section].label
            return section + 1

        def flags(self, index: QModelIndex):
            if not index.isValid():
                return Qt.NoItemFlags
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

        def _value_at(self, row_index: int, column_index: int):
            row = self._rows[row_index]
            column = self._columns[column_index]
            if isinstance(row, Mapping):
                return row.get(column.key, "")
            if column_index < len(row):
                return row[column_index]
            return ""


    class _DataTableFilterProxyModel(QSortFilterProxyModel):
        pass


def _button_from_action(action: ComponentAction):
    button = make_action_button(
        action.label,
        role=action.role,
        semantic_state=action.semantic_state,
        action_key=action.key,
        enabled=action.enabled,
        disabled_reason=action.disabled_reason,
        formal_action_enabled=False,
        file_write_allowed=False,
    )
    if action.callback is not None and action.enabled:
        button.clicked.connect(action.callback)
    return button


def _panel_stylesheet(object_name: str) -> str:
    return f"""
    QFrame#{object_name} {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["panel"]}px;
    }}
    """


__all__ = [
    "ComponentAction",
    "DataTableColumn",
    "HistoryItem",
    "KeyValueItem",
    "NavTab",
    "WarningItem",
    "WorkflowStep",
    "make_data_table",
    "make_disabled_action_button",
    "make_file_picker_button",
    "make_form_field_row",
    "make_gate_notice",
    "make_history_list",
    "make_key_value_panel",
    "make_module_entry_card",
    "make_result_panel",
    "make_secondary_nav_tabs",
    "make_warning_list",
    "make_workflow_stepper",
]
