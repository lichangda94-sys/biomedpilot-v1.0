from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from app.shared.ui_components.common import DataTableColumn, WorkflowStep, make_data_table, make_disabled_action_button, make_warning_list
from app.shared.ui_components.primitives import make_action_button, make_empty_state, make_info_banner, make_section_title, make_status_chip, make_workbench_card
from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING


@dataclass(frozen=True)
class ReportSection:
    key: str
    title: str
    content: str = ""
    status_key: str = "draft"
    semantic_state: str = "draft"


@dataclass(frozen=True)
class ExportGateCheck:
    key: str
    label: str
    passed: bool = False
    reason: str = ""
    semantic_state: str = "blocked"


@dataclass(frozen=True)
class ExportFormatAction:
    key: str
    label: str
    disabled_reason: str
    semantic_state: str = "export_disabled"


@dataclass(frozen=True)
class EngineStatusItem:
    key: str
    label: str
    status_key: str = "not_configured"
    semantic_state: str = "adapter_needed"
    version: str = ""
    path: str = ""
    detail: str = ""


@dataclass(frozen=True)
class SettingsResourceItem:
    key: str
    label: str
    group: str = ""
    status_key: str = "not_configured"
    version: str = ""
    path: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ProjectRecentItem:
    key: str
    name: str
    module: str = ""
    last_opened: str = ""
    path: str = ""
    status_key: str = "draft"


@dataclass(frozen=True)
class WizardStepSpec:
    key: str
    label: str
    description: str = ""
    status_key: str = "planned"
    semantic_state: str = "planned"
    enabled: bool = True
    disabled_reason: str = ""


@dataclass(frozen=True)
class AuditLogEntry:
    timestamp: str
    source: str
    level: str
    message: str
    semantic_state: str = "draft"


def make_report_viewer_shell(
    *,
    title: str,
    sections: Sequence[ReportSection],
    active_key: str = "",
    status_key: str = "draft",
    semantic_state: str = "draft",
    object_name: str = "reportViewerShell",
    on_section_requested: Callable[[str], None] | None = None,
):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QStandardItem, QStandardItemModel
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListView, QScrollArea, QStackedWidget, QVBoxLayout

    shell = make_workbench_card(object_name=object_name, semantic_state=semantic_state)
    shell.setProperty("uiPrimitive", "report_viewer_shell")
    shell.setProperty("semanticState", semantic_state)
    shell.setProperty("activeKey", active_key)
    shell.setProperty("readOnly", True)
    shell.setProperty("draftOnly", True)
    shell.setProperty("formalReport", False)
    shell.setProperty("reportGenerationAllowed", False)
    shell.setProperty("exportAllowed", False)
    shell.setProperty("fileWriteAllowed", False)

    layout = QVBoxLayout(shell)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title, "Draft/report-disabled viewer shell."))
    layout.addWidget(make_status_chip(status_key=status_key, semantic_state=semantic_state))

    body = QFrame()
    body.setObjectName("reportViewerBody")
    body.setProperty("uiPrimitive", "report_viewer_body")
    body_layout = QHBoxLayout(body)
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.setSpacing(SPACING["md"])

    list_view = QListView()
    list_view.setObjectName("reportViewerSectionList")
    list_view.setProperty("uiPrimitive", "report_viewer_section_list")
    list_view.setProperty("readOnly", True)
    list_view.setMinimumWidth(180)
    list_view.setMaximumWidth(260)
    section_model = QStandardItemModel(list_view)

    stack = QStackedWidget()
    stack.setObjectName("reportViewerStack")
    stack.setProperty("uiPrimitive", "report_viewer_stack")
    stack.setProperty("readOnly", True)

    active_index = 0
    for index, section in enumerate(sections):
        item = QStandardItem(section.title)
        item.setEditable(False)
        item.setData(section.key, Qt.UserRole)
        item.setData(section.status_key, Qt.UserRole + 1)
        item.setData(section.semantic_state, Qt.UserRole + 2)
        section_model.appendRow(item)
        if section.key == active_key:
            active_index = index

        page = QFrame()
        page.setObjectName("reportViewerSection")
        page.setProperty("sectionKey", section.key)
        page.setProperty("semanticState", section.semantic_state)
        page.setProperty("formalResult", False)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        page_layout.setSpacing(SPACING["sm"])
        page_layout.addWidget(make_section_title(section.title))
        page_layout.addWidget(make_status_chip(status_key=section.status_key, semantic_state=section.semantic_state))
        content = QLabel(section.content or "No draft content is available for this section.")
        content.setObjectName("reportViewerSectionContent")
        content.setWordWrap(True)
        content.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
        page_layout.addWidget(content)
        page_layout.addStretch(1)
        stack.addWidget(page)

    if not sections:
        stack.addWidget(make_empty_state("No draft report", "No report sections are available.", semantic_state="report_disabled"))

    list_view.setModel(section_model)
    if section_model.rowCount() > 0:
        list_view.setCurrentIndex(section_model.index(active_index, 0))
        stack.setCurrentIndex(active_index)

    def _section_changed(current, _previous) -> None:
        if not current.isValid():
            return
        stack.setCurrentIndex(current.row())
        if on_section_requested is not None:
            on_section_requested(str(current.data(Qt.UserRole)))

    list_view.selectionModel().currentChanged.connect(_section_changed)

    scroll = QScrollArea()
    scroll.setObjectName("reportViewerScrollArea")
    scroll.setProperty("uiPrimitive", "report_viewer_scroll_area")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setWidget(stack)

    body_layout.addWidget(list_view, 0)
    body_layout.addWidget(scroll, 1)
    layout.addWidget(body, 1)
    shell._biomedpilot_section_model = section_model
    return shell


def make_export_gate_panel(
    *,
    title: str,
    checks: Sequence[ExportGateCheck],
    formats: Sequence[ExportFormatAction],
    artifact_exists: bool = False,
    object_name: str = "exportGatePanel",
):
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

    panel = make_workbench_card(object_name=object_name, semantic_state="export_disabled")
    panel.setProperty("uiPrimitive", "export_gate_panel")
    panel.setProperty("artifactExists", artifact_exists)
    panel.setProperty("exportAllowed", False)
    panel.setProperty("reportGenerationAllowed", False)
    panel.setProperty("fileWriteAllowed", False)
    panel.setProperty("formalExport", False)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title, "Export remains disabled until a later authorized stage."))
    layout.addWidget(make_status_chip(status_key="export_disabled", semantic_state="export_disabled"))

    if not checks:
        layout.addWidget(make_info_banner("No export readiness checks are registered.", severity="draft", semantic_state="draft"))
    for check in checks:
        row = QHBoxLayout()
        row.setSpacing(SPACING["sm"])
        label = QLabel(check.label)
        label.setObjectName("exportGateCheckLabel")
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px;")
        row.addWidget(label, 1)
        row.addWidget(make_status_chip(status_key="available" if check.passed else "blocked", semantic_state=check.semantic_state), 0)
        layout.addLayout(row)
        if check.reason:
            reason = QLabel(check.reason)
            reason.setObjectName("exportGateCheckReason")
            reason.setWordWrap(True)
            reason.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
            layout.addWidget(reason)

    for export_format in formats:
        layout.addWidget(
            make_disabled_action_button(
                export_format.label,
                action_key=export_format.key,
                semantic_state=export_format.semantic_state,
                disabled_reason=export_format.disabled_reason,
            )
        )
    layout.addStretch(1)
    return panel


def make_plot_placeholder(
    *,
    title: str,
    plot_type: str,
    message: str = "Plot output is not available in this UI stage.",
    status_key: str = "planned",
    semantic_state: str = "planned",
    object_name: str = "plotPlaceholder",
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    placeholder = make_workbench_card(object_name=object_name, semantic_state=semantic_state)
    placeholder.setProperty("uiPrimitive", "plot_placeholder")
    placeholder.setProperty("plotType", plot_type)
    placeholder.setProperty("semanticState", semantic_state)
    placeholder.setProperty("formalPlot", False)
    placeholder.setProperty("fakePlotData", False)
    placeholder.setProperty("plottingDependencyRequired", False)
    placeholder.setMinimumHeight(180)

    layout = QVBoxLayout(placeholder)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title))
    layout.addWidget(make_status_chip(status_key=status_key, semantic_state=semantic_state))
    body = QLabel(message)
    body.setObjectName("plotPlaceholderMessage")
    body.setAlignment(Qt.AlignCenter)
    body.setWordWrap(True)
    body.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['body']}px;")
    layout.addWidget(body, 1)
    return placeholder


def make_external_engine_status_panel(
    *,
    title: str,
    engines: Sequence[EngineStatusItem],
    object_name: str = "externalEngineStatusPanel",
    on_detect_requested: Callable[[], None] | None = None,
):
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

    panel = make_workbench_card(object_name=object_name)
    panel.setProperty("uiPrimitive", "external_engine_status_panel")
    panel.setProperty("detectOnly", True)
    panel.setProperty("installAllowed", False)
    panel.setProperty("engineExecutionAllowed", False)
    panel.setProperty("cloudConfigAllowed", False)
    panel.setProperty("downloadAllowed", False)
    panel.setProperty("uploadAllowed", False)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title, "Detection/status display only."))

    for engine in engines:
        row = QFrame()
        row.setObjectName("externalEngineStatusRow")
        row.setProperty("engineKey", engine.key)
        row.setProperty("semanticState", engine.semantic_state)
        row.setStyleSheet(_panel_stylesheet("externalEngineStatusRow"))
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        row_layout.setSpacing(SPACING["xs"])
        header = QHBoxLayout()
        name = QLabel(engine.label)
        name.setObjectName("externalEngineStatusLabel")
        name.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px; font-weight: 750;")
        header.addWidget(name, 1)
        header.addWidget(make_status_chip(status_key=engine.status_key, semantic_state=engine.semantic_state), 0)
        row_layout.addLayout(header)
        detail = " / ".join(value for value in (engine.version, engine.path, engine.detail) if value)
        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName("externalEngineStatusDetail")
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: {FONT_SIZE['caption']}px;")
            row_layout.addWidget(detail_label)
        layout.addWidget(row)

    if on_detect_requested is not None:
        button = make_action_button("检测状态", role="secondary", action_key="detect_external_engines", formal_action_enabled=False, file_write_allowed=False)
        button.setProperty("detectOnly", True)
        button.clicked.connect(on_detect_requested)
        layout.addWidget(button)
    layout.addStretch(1)
    return panel


def make_settings_resource_table(
    resources: Sequence[SettingsResourceItem],
    *,
    object_name: str = "settingsResourceTable",
):
    table = make_data_table(
        columns=[
            DataTableColumn("label", "Resource", 180),
            DataTableColumn("group", "Group", 140),
            DataTableColumn("status", "Status", 140),
            DataTableColumn("version", "Version", 120),
            DataTableColumn("path", "Path", 260),
            DataTableColumn("notes", "Notes", 220),
        ],
        rows=[
            {
                "label": item.label,
                "group": item.group,
                "status": item.status_key,
                "version": item.version,
                "path": item.path,
                "notes": item.notes,
            }
            for item in resources
        ],
        object_name=object_name,
        empty_title="No resources",
        empty_body="No local resources are registered for detection.",
    )
    table.setProperty("uiPrimitive", "settings_resource_table")
    table.setProperty("resourceDetectionOnly", True)
    table.setProperty("installAllowed", False)
    table.setProperty("downloadAllowed", False)
    table.setProperty("cloudConfigAllowed", False)
    table.setProperty("engineExecutionAllowed", False)
    return table


def make_project_recent_table(
    projects: Sequence[ProjectRecentItem],
    *,
    object_name: str = "projectRecentTable",
):
    table = make_data_table(
        columns=[
            DataTableColumn("name", "Project", 200),
            DataTableColumn("module", "Module", 140),
            DataTableColumn("last_opened", "Last opened", 160),
            DataTableColumn("path", "Path", 280),
            DataTableColumn("status", "State", 140),
        ],
        rows=[
            {
                "name": item.name,
                "module": item.module,
                "last_opened": item.last_opened,
                "path": item.path,
                "status": item.status_key,
            }
            for item in projects
        ],
        object_name=object_name,
        empty_title="No recent projects",
        empty_body="Recent project records will appear here when provided by the project service.",
    )
    table.setProperty("uiPrimitive", "project_recent_table")
    table.setProperty("readOnly", True)
    table.setProperty("createsProject", False)
    table.setProperty("opensProject", False)
    table.setProperty("fakeRecords", False)
    return table


def make_wizard_flow_shell(
    *,
    title: str,
    steps: Sequence[WizardStepSpec],
    current_key: str = "",
    content_widgets: Mapping[str, object] | None = None,
    object_name: str = "wizardFlowShell",
    on_back_requested: Callable[[str], None] | None = None,
    on_next_requested: Callable[[str], None] | None = None,
):
    from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout

    shell = make_workbench_card(object_name=object_name)
    shell.setProperty("uiPrimitive", "wizard_flow_shell")
    shell.setProperty("currentKey", current_key)
    shell.setProperty("executorAllowed", False)
    shell.setProperty("formalAnalysisAllowed", False)
    shell.setProperty("reportGenerationAllowed", False)
    shell.setProperty("exportAllowed", False)

    layout = QVBoxLayout(shell)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title))

    body = QHBoxLayout()
    body.setSpacing(SPACING["lg"])
    current_index = 0
    workflow_steps: list[WorkflowStep] = []
    for index, step in enumerate(steps):
        is_current = step.key == current_key or (not current_key and index == 0)
        if is_current:
            current_index = index
        workflow_steps.append(
            WorkflowStep(
                step.key,
                step.label,
                status_key=step.status_key,
                semantic_state=step.semantic_state,
                enabled=step.enabled,
                current=is_current,
                description=step.description,
                disabled_reason=step.disabled_reason,
            )
        )
    stepper = make_warning_aware_stepper(workflow_steps)
    body.addWidget(stepper, 0)

    stack = QStackedWidget()
    stack.setObjectName("wizardFlowStack")
    stack.setProperty("uiPrimitive", "wizard_flow_stack")
    widgets = content_widgets or {}
    for step in steps:
        stack.addWidget(widgets.get(step.key) or make_empty_state(step.label, step.description or "No wizard content is attached.", semantic_state=step.semantic_state))
    if not steps:
        stack.addWidget(make_empty_state("No wizard steps", "Wizard steps are not configured.", semantic_state="planned"))
    stack.setCurrentIndex(current_index)
    body.addWidget(stack, 1)
    layout.addLayout(body, 1)

    action_row = QHBoxLayout()
    action_row.addStretch(1)
    active_step_key = steps[current_index].key if steps else ""
    back = make_action_button(
        "Back",
        role="secondary",
        action_key="wizard_back",
        semantic_state="testing",
        enabled=on_back_requested is not None,
        disabled_reason="" if on_back_requested is not None else "Back navigation callback is not connected.",
    )
    next_button = make_action_button(
        "Next",
        role="secondary",
        action_key="wizard_next",
        semantic_state="testing",
        enabled=on_next_requested is not None,
        disabled_reason="" if on_next_requested is not None else "Next navigation callback is not connected.",
    )
    if on_back_requested is not None:
        back.clicked.connect(lambda checked=False, key=active_step_key: on_back_requested(key))
    if on_next_requested is not None:
        next_button.clicked.connect(lambda checked=False, key=active_step_key: on_next_requested(key))
    action_row.addWidget(back)
    action_row.addWidget(next_button)
    layout.addLayout(action_row)
    return shell


def make_review_confirmation_panel(
    *,
    title: str,
    summary_items: Sequence[tuple[str, str]] = (),
    blockers: Sequence[str] = (),
    action_label: str = "Confirm review",
    disabled_reason: str = "Review confirmation is disabled until a later authorized stage.",
    object_name: str = "reviewConfirmationPanel",
):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    panel = make_workbench_card(object_name=object_name, semantic_state="blocked" if blockers else "draft")
    panel.setProperty("uiPrimitive", "review_confirmation_panel")
    panel.setProperty("finalDecisionEnabled", False)
    panel.setProperty("formalApprovalAllowed", False)
    panel.setProperty("reportGenerationAllowed", False)
    panel.setProperty("exportAllowed", False)
    panel.setProperty("disabledReason", disabled_reason)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title, "Review state display only."))
    layout.addWidget(make_status_chip(status_key="blocked" if blockers else "draft", semantic_state="blocked" if blockers else "draft"))
    for label, value in summary_items:
        row = QLabel(f"{label}: {value}")
        row.setObjectName("reviewConfirmationSummaryRow")
        row.setWordWrap(True)
        row.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONT_SIZE['body']}px;")
        layout.addWidget(row)
    if blockers:
        layout.addWidget(
            make_warning_list(
                warnings=[_warning_from_blocker(index, blocker) for index, blocker in enumerate(blockers)],
                title="Review blockers",
            )
        )
    layout.addWidget(
        make_disabled_action_button(
            action_label,
            action_key="review_confirmation",
            semantic_state="blocked" if blockers else "draft",
            disabled_reason=disabled_reason,
        )
    )
    layout.addStretch(1)
    return panel


def make_audit_log_panel(
    entries: Sequence[AuditLogEntry],
    *,
    title: str = "Audit log",
    object_name: str = "auditLogPanel",
):
    from PySide6.QtWidgets import QVBoxLayout

    panel = make_workbench_card(object_name=object_name)
    panel.setProperty("uiPrimitive", "audit_log_panel")
    panel.setProperty("readOnly", True)
    panel.setProperty("diagnosticOnly", True)
    panel.setProperty("exportAllowed", False)
    panel.setProperty("fileWriteAllowed", False)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
    layout.setSpacing(SPACING["md"])
    layout.addWidget(make_section_title(title))
    table = make_data_table(
        columns=[
            DataTableColumn("timestamp", "Timestamp", 180),
            DataTableColumn("source", "Source", 140),
            DataTableColumn("level", "Level", 120),
            DataTableColumn("message", "Message", 320),
            DataTableColumn("state", "State", 140),
        ],
        rows=[
            {
                "timestamp": entry.timestamp,
                "source": entry.source,
                "level": entry.level,
                "message": entry.message,
                "state": entry.semantic_state,
            }
            for entry in entries
        ],
        object_name="auditLogTable",
        empty_title="No audit entries",
        empty_body="Audit events will appear here when provided by the runtime.",
    )
    table.setProperty("uiPrimitive", "audit_log_table")
    table.setProperty("readOnly", True)
    layout.addWidget(table)
    return panel


def make_warning_aware_stepper(steps: Sequence[WorkflowStep]):
    from app.shared.ui_components.common import make_workflow_stepper

    stepper = make_workflow_stepper(steps, title="Steps")
    stepper.setProperty("uiPrimitive", "wizard_stepper")
    stepper.setProperty("orientation", "vertical")
    return stepper


def _warning_from_blocker(index: int, blocker: str):
    from app.shared.ui_components.common import WarningItem

    return WarningItem(key=f"review_blocker_{index}", title="Blocked", reason=blocker, semantic_state="blocked")


def _panel_stylesheet(object_name: str) -> str:
    return f"""
    QFrame#{object_name} {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    """


__all__ = [
    "AuditLogEntry",
    "EngineStatusItem",
    "ExportFormatAction",
    "ExportGateCheck",
    "ProjectRecentItem",
    "ReportSection",
    "SettingsResourceItem",
    "WizardStepSpec",
    "make_audit_log_panel",
    "make_export_gate_panel",
    "make_external_engine_status_panel",
    "make_plot_placeholder",
    "make_project_recent_table",
    "make_report_viewer_shell",
    "make_review_confirmation_panel",
    "make_settings_resource_table",
    "make_wizard_flow_shell",
]
