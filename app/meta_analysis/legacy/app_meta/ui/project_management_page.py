from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app_meta.core.project_io import PROJECT_FOLDERS, folder_status, recent_log_lines
from app_meta.core.project_state import MetaProjectState
from app_meta.ui.components import SectionCard
from app_meta.ui.theme import Theme


class ProjectManagementPage(QWidget):
    def __init__(self, project_state: MetaProjectState, on_action: Callable[[str], None]) -> None:
        super().__init__()
        self._project_state = project_state
        self._on_action = on_action

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addLayout(self._header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: 0; background: transparent; }")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(16)
        top.addWidget(self._project_info_card(), 1)
        top.addWidget(self._folder_status_card(), 1)
        layout.addLayout(top)
        layout.addWidget(self._save_status_card())
        layout.addWidget(self._diagnostics_section())
        layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        title = QLabel("项目管理")
        title.setObjectName("pageTitle")
        subtitle = QLabel("管理本地 Meta Analysis 项目元数据、目录结构与保存状态")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _project_info_card(self) -> SectionCard:
        card = SectionCard("Project information")
        rows = (
            ("Project ID", self._project_state.project_id),
            ("Project name", self._project_state.project_name),
            ("Review type", self._project_state.review_type),
            ("Status", self._project_state.project_status),
            ("Created at", self._project_state.created_at),
            ("Updated at", self._project_state.updated_at),
            ("Progress", f"{self._project_state.progress_percent}%"),
            ("Current outcome", self._project_state.current_outcome),
            ("Effect size", self._project_state.current_effect_size),
            ("App version", self._project_state.app_version),
        )
        for label, value in rows:
            card.layout.addLayout(_key_value_row(label, value))
        return card

    def _folder_status_card(self) -> SectionCard:
        card = SectionCard("Local folder path")
        path = QLabel(str(self._project_state.project_dir))
        path.setWordWrap(True)
        path.setStyleSheet(
            f"background: {Theme.primary_soft}; color: {Theme.primary}; border-radius: 10px; padding: 10px;"
        )
        card.layout.addWidget(path)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        statuses = folder_status(self._project_state.project_dir)
        for index, folder in enumerate(PROJECT_FOLDERS):
            label = QLabel(f"{'Ready' if statuses[folder] else 'Missing'} · {folder}")
            color = Theme.success if statuses[folder] else Theme.warning
            bg = Theme.success_soft if statuses[folder] else Theme.warning_soft
            label.setStyleSheet(f"color: {color}; background: {bg}; border-radius: 9px; padding: 6px 8px;")
            grid.addWidget(label, index // 2, index % 2)
        card.layout.addLayout(grid)
        return card

    def _save_status_card(self) -> SectionCard:
        card = SectionCard("Save status")
        card.layout.addLayout(_key_value_row("Recent save time", self._project_state.updated_at))
        card.layout.addLayout(_key_value_row("Project file", "project.json"))
        actions = QHBoxLayout()
        for index, label in enumerate(("Save Project", "Open Project Folder", "Export Project")):
            button = QPushButton(label)
            if index == 0:
                button.setObjectName("primaryButton")
            button.clicked.connect(lambda checked=False, name=label: self._on_action(name))
            actions.addWidget(button)
        actions.addStretch(1)
        card.layout.addLayout(actions)
        return card

    def _diagnostics_section(self) -> QGroupBox:
        box = QGroupBox("Developer diagnostics")
        box.setCheckable(True)
        box.setChecked(False)
        box.setStyleSheet(
            f"QGroupBox {{ background: {Theme.card}; border: 1px solid {Theme.border_soft}; "
            f"border-radius: {Theme.radius}px; padding: 14px; font-weight: 700; }}"
        )
        layout = QVBoxLayout(box)
        diagnostic_labels: list[QLabel] = []
        lines = recent_log_lines(self._project_state.project_dir)
        if not lines:
            lines = ("No project log entries yet.",)
        for line in lines:
            label = QLabel(line)
            label.setObjectName("smallMuted")
            label.setWordWrap(True)
            layout.addWidget(label)
            diagnostic_labels.append(label)
        for label in diagnostic_labels:
            label.setVisible(False)
        box.toggled.connect(lambda visible: _set_labels_visible(diagnostic_labels, visible))
        return box


def _key_value_row(label: str, value: str) -> QHBoxLayout:
    row = QHBoxLayout()
    name = QLabel(label)
    name.setObjectName("smallMuted")
    value_label = QLabel(value)
    value_label.setAlignment(Qt.AlignRight)
    value_label.setWordWrap(True)
    value_label.setStyleSheet("font-weight: 700;")
    row.addWidget(name)
    row.addWidget(value_label, 1)
    return row


def _set_labels_visible(labels: list[QLabel], visible: bool) -> None:
    for label in labels:
        label.setVisible(visible)
