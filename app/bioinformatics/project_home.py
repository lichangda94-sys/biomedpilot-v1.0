from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.bioinformatics.project_workspace import (
    BioinformaticsProjectSummary,
    create_bioinformatics_project,
    open_bioinformatics_project,
)
from app.app_identity import load_ui03_project_home_icon, load_ui03_project_home_pixmap
from app.ui_style_tokens import SPACING, bioinformatics_project_home_stylesheet

WORKFLOW_STEPS = (
    ("project_created", "创建项目"),
    ("ready_for_data_source_selection", "选择数据来源"),
    ("data_recognition", "数据识别"),
    ("data_standardization", "数据标准化"),
    ("analysis_tasks", "分析任务"),
    ("results_browser", "结果浏览"),
    ("project_report", "项目报告"),
)


class BioinformaticsProjectHomeWidget(QWidget):
    continue_requested = Signal(object)
    back_requested = Signal()

    def __init__(
        self,
        *,
        on_continue: Callable[[BioinformaticsProjectSummary], None] | None = None,
        on_back: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._current_summary: BioinformaticsProjectSummary | None = None
        self.setObjectName("bioinformaticsProjectHomePage")
        self.setStyleSheet(bioinformatics_project_home_stylesheet())
        self._build_ui()
        self._annotate_buttons()
        if on_continue is not None:
            self.continue_requested.connect(on_continue)
        if on_back is not None:
            self.back_requested.connect(on_back)
        self._render_summary(None)

    def current_summary(self) -> BioinformaticsProjectSummary | None:
        return self._current_summary

    def status_message(self) -> str:
        return self._validation_status_label.text()

    def set_new_project_inputs(self, project_name: str, save_location: str | Path) -> None:
        self._project_name_input.setText(project_name)
        self._save_location_input.setText(str(save_location))

    def set_existing_project_path(self, project_root: str | Path) -> None:
        self._existing_project_input.setText(str(project_root))

    def create_project_from_inputs(self) -> BioinformaticsProjectSummary | None:
        project_name = self._project_name_input.text().strip()
        save_location = self._save_location_input.text().strip()
        if not project_name or not save_location:
            self._set_status("请输入项目名称并选择项目保存位置。", error=True)
            return None
        summary = create_bioinformatics_project(project_name, save_location)
        self._set_current_summary(summary)
        self._set_status("项目已设置成功，正在进入数据来源与登记…")
        self.continue_requested.emit(summary)
        return summary

    def open_selected_project(self) -> BioinformaticsProjectSummary | None:
        project_root = self._existing_project_input.text().strip()
        if not project_root:
            self._set_status("请选择项目文件夹。", error=True)
            return None
        validation = open_bioinformatics_project(project_root)
        if not validation.is_valid or validation.summary is None:
            message = validation.errors[0] if validation.errors else "该文件夹不是有效的生信分析项目，或缺少 project_manifest.json。"
            self._set_status(message, error=True)
            self._render_summary(None)
            return None
        self._set_current_summary(validation.summary)
        if validation.warnings:
            self._set_status(f"项目已打开，但存在 {len(validation.warnings)} 条目录警告。", warning=True)
        else:
            self._set_status("项目验证通过，已设置为当前生信项目。正在进入数据来源与登记…")
        self.continue_requested.emit(validation.summary)
        return validation.summary

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("bioProjectHomeScrollArea")
        content = QWidget()
        content.setObjectName("bioProjectHomeContent")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(SPACING["md"])
        root.addWidget(self._build_header())

        top_cards = QHBoxLayout()
        top_cards.setSpacing(SPACING["md"])
        top_cards.addWidget(self._build_create_card())
        top_cards.addWidget(self._build_open_card())
        root.addLayout(top_cards)
        root.addWidget(self._build_summary_card())
        root.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _annotate_buttons(self) -> None:
        for button in self.findChildren(QPushButton):
            if button.property("buttonBehavior") is None:
                button.setProperty("buttonBehavior", "bio_project_home_action_requires_explicit_audit")
            if button.property("formalActionEnabled") is None:
                button.setProperty("formalActionEnabled", False)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bioProjectHeader")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        title_col = QVBoxLayout()
        title_col.addWidget(self._icon_label("project_config", 42), alignment=Qt.AlignLeft)
        title = QLabel("生信分析模块")
        title.setObjectName("bioProjectTitle")
        subtitle = QLabel("Bioinformatics Analyze Module")
        subtitle.setObjectName("bioProjectSubtitle")
        status = QLabel("当前状态：Developer Preview / 本地测试版")
        status.setObjectName("bioProjectPreviewBadge")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        title_col.addWidget(status, alignment=Qt.AlignLeft)
        layout.addLayout(title_col, 1)
        back_button = QPushButton("返回模块选择首页")
        back_button.setObjectName("secondaryButton")
        back_button.setProperty("buttonBehavior", "navigates_back_to_module_selection")
        back_button.setProperty("formalActionEnabled", False)
        back_button.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_button)
        return frame

    def _build_create_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bioProjectCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])
        layout.addLayout(self._title_row("创建新项目", "create_project"))
        layout.addWidget(self._field_label("项目名称", icon_key="project_name"))
        self._project_name_input = QLineEdit()
        self._project_name_input.setObjectName("projectNameInput")
        self._project_name_input.setPlaceholderText("例如：TCGA-LUAD 探索分析")
        name_icon = load_ui03_project_home_icon("project_name")
        if not name_icon.isNull():
            self._project_name_input.addAction(name_icon, QLineEdit.LeadingPosition)
        layout.addWidget(self._project_name_input)
        layout.addWidget(self._field_label("项目保存位置", icon_key="save_location"))
        self._save_location_input = QLineEdit()
        self._save_location_input.setObjectName("saveLocationInput")
        self._save_location_input.setPlaceholderText("请选择保存位置")
        save_icon = load_ui03_project_home_icon("save_location")
        if not save_icon.isNull():
            self._save_location_input.addAction(save_icon, QLineEdit.LeadingPosition)
        layout.addWidget(self._save_location_input)
        choose_button = QPushButton("选择保存位置")
        choose_button.setObjectName("secondaryButton")
        choose_button.setProperty("buttonBehavior", "opens_new_project_save_location_picker")
        choose_button.setProperty("formalActionEnabled", False)
        choose_button.setIcon(load_ui03_project_home_icon("folder_picker"))
        choose_button.setIconSize(QSize(18, 18))
        choose_button.clicked.connect(self._choose_save_location)
        layout.addWidget(choose_button, alignment=Qt.AlignLeft)
        description = QLabel(
            "每个项目会自动保存原始数据、分析结果、报告和日志，便于后续追踪与复用。"
        )
        description.setObjectName("bioProjectMutedLabel")
        description.setWordWrap(True)
        layout.addWidget(description)
        details = QLabel("项目结构和 manifest/config 会由软件自动生成，可在后续技术详情中查看。")
        details.setObjectName("bioProjectMutedLabel")
        details.setWordWrap(True)
        details.setToolTip(
            "项目目录包含 raw_data/、acquisition/、recognized_data/、standardized_data/、analysis/、"
            "results/、reports/、logs/、manifests/、project_manifest.json、project_config.json。"
        )
        layout.addWidget(details)
        create_button = QPushButton("创建项目并继续")
        create_button.setObjectName("primaryButton")
        create_button.setProperty("buttonBehavior", "calls_create_bioinformatics_project_and_writes_project_manifest")
        create_button.setProperty("formalActionEnabled", False)
        create_button.setIcon(load_ui03_project_home_icon("create_project"))
        create_button.setIconSize(QSize(18, 18))
        create_button.clicked.connect(self.create_project_from_inputs)
        layout.addWidget(create_button, alignment=Qt.AlignLeft)
        return frame

    def _build_open_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bioProjectCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])
        layout.addLayout(self._title_row("打开已有项目", "open_existing_project"))
        self._existing_project_input = QLineEdit()
        self._existing_project_input.setObjectName("existingProjectInput")
        self._existing_project_input.setPlaceholderText("请选择项目文件夹")
        folder_icon = load_ui03_project_home_icon("folder_picker")
        if not folder_icon.isNull():
            self._existing_project_input.addAction(folder_icon, QLineEdit.LeadingPosition)
        layout.addWidget(self._existing_project_input)
        choose_button = QPushButton("选择项目文件夹")
        choose_button.setObjectName("secondaryButton")
        choose_button.setProperty("buttonBehavior", "opens_existing_project_folder_picker")
        choose_button.setProperty("formalActionEnabled", False)
        choose_button.setIcon(load_ui03_project_home_icon("folder_picker"))
        choose_button.setIconSize(QSize(18, 18))
        choose_button.clicked.connect(self._choose_existing_project)
        layout.addWidget(choose_button, alignment=Qt.AlignLeft)
        validation_card = QFrame()
        validation_card.setObjectName("projectValidationStatusCard")
        validation_layout = QHBoxLayout(validation_card)
        validation_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        validation_layout.setSpacing(SPACING["md"])
        self._validation_status_icon = self._icon_label("validation_status", 46)
        validation_layout.addWidget(self._validation_status_icon, alignment=Qt.AlignTop)
        self._validation_status_label = QLabel("项目合法性验证状态：尚未选择项目。")
        self._validation_status_label.setObjectName("bioProjectStatusLabel")
        self._validation_status_label.setWordWrap(True)
        validation_layout.addWidget(self._validation_status_label, 1)
        layout.addWidget(validation_card)
        recent = QLabel("最近项目：占位，后续接入 Project Center 的生信项目列表。")
        recent.setObjectName("bioProjectMutedLabel")
        recent.setWordWrap(True)
        layout.addWidget(recent)
        open_button = QPushButton("确认并继续")
        open_button.setObjectName("primaryButton")
        open_button.setProperty("buttonBehavior", "calls_open_bioinformatics_project_and_validates_manifest")
        open_button.setProperty("formalActionEnabled", False)
        open_button.setIcon(load_ui03_project_home_icon("open_existing_project"))
        open_button.setIconSize(QSize(18, 18))
        open_button.clicked.connect(self.open_selected_project)
        layout.addWidget(open_button, alignment=Qt.AlignLeft)
        return frame

    def _build_summary_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("bioProjectSummaryCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        layout.addLayout(self._title_row("当前项目摘要", "current_project_summary"))

        self._empty_state_label = QLabel("尚未打开项目，请创建新项目或选择已有项目文件夹。")
        self._empty_state_label.setObjectName("bioProjectEmptyState")
        self._empty_state_label.setWordWrap(True)
        layout.addLayout(self._icon_text_row(self._empty_state_label, "project_warning"))

        self._summary_content = QWidget()
        self._summary_content.setObjectName("bioProjectSummaryContent")
        content_layout = QVBoxLayout(self._summary_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(SPACING["sm"])

        two_col = QHBoxLayout()
        two_col.setSpacing(SPACING["md"])
        left = QVBoxLayout()
        left.setSpacing(SPACING["sm"])
        self._project_name_line = QLabel("")
        self._project_path_line = QLabel("")
        self._created_at_line = QLabel("")
        self._current_status_line = QLabel("")
        for line in (self._project_name_line, self._project_path_line, self._created_at_line, self._current_status_line):
            line.setObjectName("bioProjectSummaryLine")
            line.setWordWrap(True)
            left.addWidget(line)
        self._step_labels: list[QLabel] = []
        steps_row = QHBoxLayout()
        steps_row.setSpacing(6)
        for _, step_label in WORKFLOW_STEPS:
            label = QLabel(step_label)
            label.setObjectName("bioProjectStepLabel")
            label.setAlignment(Qt.AlignCenter)
            self._step_labels.append(label)
            steps_row.addWidget(label)
        left.addLayout(steps_row)
        two_col.addLayout(left, 2)

        right = QVBoxLayout()
        right.setSpacing(SPACING["sm"])
        self._health_card = QFrame()
        self._health_card.setObjectName("bioProjectHealthCard")
        health_layout = QVBoxLayout(self._health_card)
        health_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        health_layout.setSpacing(2)
        self._health_title = QLabel("")
        self._health_title.setObjectName("bioProjectHealthTitle")
        self._health_detail = QLabel("")
        self._health_detail.setObjectName("bioProjectHealthDetail")
        self._health_detail.setWordWrap(True)
        health_layout.addWidget(self._health_title)
        health_layout.addWidget(self._health_detail)
        right.addWidget(self._health_card)
        self._continue_button = QPushButton("继续：选择数据来源")
        self._continue_button.setObjectName("primaryButton")
        self._continue_button.setProperty("buttonBehavior", "navigates_to_data_source_when_project_summary_exists")
        self._continue_button.setProperty("formalActionEnabled", False)
        self._continue_button.clicked.connect(self._continue_to_data_source)
        right.addWidget(self._continue_button)
        secondary_actions = QHBoxLayout()
        self._open_folder_button = QPushButton("打开项目文件夹")
        self._open_folder_button.setObjectName("secondaryButton")
        self._open_folder_button.setProperty("buttonBehavior", "opens_current_project_folder_when_project_summary_exists")
        self._open_folder_button.setProperty("formalActionEnabled", False)
        self._open_folder_button.clicked.connect(self._open_project_folder)
        self._structure_button = QPushButton("查看项目结构")
        self._structure_button.setObjectName("secondaryButton")
        self._structure_button.setProperty("buttonBehavior", "renders_expected_project_directory_structure_summary")
        self._structure_button.setProperty("formalActionEnabled", False)
        self._structure_button.clicked.connect(self._show_project_structure)
        secondary_actions.addWidget(self._open_folder_button)
        secondary_actions.addWidget(self._structure_button)
        right.addLayout(secondary_actions)
        right.addStretch(1)
        two_col.addLayout(right, 1)
        content_layout.addLayout(two_col)

        status_grid = QGridLayout()
        status_grid.setHorizontalSpacing(SPACING["sm"])
        status_grid.setVerticalSpacing(SPACING["sm"])
        self._status_blocks: dict[str, tuple[QLabel, QLabel]] = {}
        for index, key in enumerate(("data_source", "sample_recognition", "analysis_results", "project_report")):
            block = QFrame()
            block.setObjectName("bioProjectMiniStatusBlock")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
            block_layout.setSpacing(2)
            title = QLabel("")
            title.setObjectName("bioProjectMiniStatusTitle")
            value = QLabel("")
            value.setObjectName("bioProjectMiniStatusValue")
            block_layout.addWidget(title)
            block_layout.addWidget(value)
            self._status_blocks[key] = (title, value)
            status_grid.addWidget(block, 0, index)
        content_layout.addLayout(status_grid)

        self._technical_toggle = QPushButton("技术详情")
        self._technical_toggle.setObjectName("secondaryButton")
        self._technical_toggle.setProperty("buttonBehavior", "toggles_project_manifest_technical_details")
        self._technical_toggle.setProperty("formalActionEnabled", False)
        self._technical_toggle.setCheckable(True)
        self._technical_toggle.toggled.connect(self._toggle_technical_details)
        content_layout.addWidget(self._technical_toggle, alignment=Qt.AlignLeft)
        self._technical_details = QPlainTextEdit()
        self._technical_details.setObjectName("bioProjectTechnicalDetails")
        self._technical_details.setReadOnly(True)
        self._technical_details.setMaximumHeight(120)
        self._technical_details.setVisible(False)
        content_layout.addWidget(self._technical_details)
        layout.addWidget(self._summary_content)

        return frame

    def _render_summary(self, summary: BioinformaticsProjectSummary | None) -> None:
        self._current_summary = summary
        has_summary = summary is not None
        self._empty_state_label.setVisible(not has_summary)
        self._summary_content.setVisible(has_summary)
        if summary is None:
            return
        self._project_name_line.setText(f"项目名称：{summary.project_name or '未知'}")
        compact_path = _compact_user_path(summary.project_root)
        self._project_path_line.setText(f"保存位置：{compact_path}")
        self._project_path_line.setToolTip(str(summary.project_root))
        self._created_at_line.setText(f"创建时间：{_format_user_time(summary.created_at)}")
        self._current_status_line.setText(f"当前状态：{_project_status_text(summary)}")
        current_step = _current_step_key(summary)
        for step_key, label in zip((item[0] for item in WORKFLOW_STEPS), self._step_labels):
            state = _step_state(step_key, current_step)
            label.setProperty("state", state)
            label.setText(f"{_step_state_prefix(state)}{label.text().lstrip('✓').replace('当前：', '').replace('未开始：', '').strip()}")
            label.style().unpolish(label)
            label.style().polish(label)
        warnings = _project_warning_summaries(summary)
        if summary.warning_count > 0:
            self._health_card.setProperty("status", "warning")
            self._health_title.setText(f"存在 {summary.warning_count} 条项目警告")
            self._health_detail.setText("；".join(warnings[:3]) if warnings else "查看技术详情")
        else:
            self._health_card.setProperty("status", "ok")
            self._health_title.setText("项目结构正常")
            self._health_detail.setText("暂无警告")
        self._health_card.style().unpolish(self._health_card)
        self._health_card.style().polish(self._health_card)
        for key, (title, value) in self._status_blocks.items():
            title_text, value_text = _mini_status(summary, key)
            title.setText(title_text)
            value.setText(value_text)
        self._technical_details.setPlainText(_technical_details_text(summary))
        self._technical_details.setVisible(self._technical_toggle.isChecked())

    def _set_current_summary(self, summary: BioinformaticsProjectSummary) -> None:
        self._render_summary(summary)

    def _continue_to_data_source(self) -> None:
        if self._current_summary is None:
            self._set_status("请先创建或打开一个生信分析项目。", error=True)
            return
        self.continue_requested.emit(self._current_summary)

    def _show_project_folder_path(self) -> None:
        if self._current_summary is None:
            self._set_status("请先创建或打开一个生信分析项目。", error=True)
            return
        self._set_status(f"当前项目文件夹：{self._current_summary.project_root}")

    def _open_project_folder(self) -> None:
        if self._current_summary is None:
            self._set_status("请先创建或打开一个生信分析项目。", error=True)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._current_summary.project_root)))

    def _show_project_structure(self) -> None:
        if self._current_summary is None:
            self._set_status("请先创建或打开一个生信分析项目。", error=True)
            return
        directories = [
            "raw_data",
            "acquisition",
            "recognized_data",
            "standardized_data",
            "analysis",
            "results",
            "reports",
            "logs",
            "manifests",
        ]
        self._set_status("项目结构：" + " / ".join(directories))

    def _toggle_technical_details(self, checked: bool) -> None:
        self._technical_details.setVisible(checked)

    def _choose_save_location(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择保存位置")
        if directory:
            self._save_location_input.setText(directory)

    def _choose_existing_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择项目文件夹")
        if directory:
            self._existing_project_input.setText(directory)

    def _set_status(self, text: str, *, error: bool = False, warning: bool = False) -> None:
        self._validation_status_label.setText(text)
        if error:
            self._validation_status_label.setProperty("status", "error")
        elif warning:
            self._validation_status_label.setProperty("status", "warning")
        else:
            self._validation_status_label.setProperty("status", "ok")
        self._validation_status_label.style().unpolish(self._validation_status_label)
        self._validation_status_label.style().polish(self._validation_status_label)

    def _field_label(self, text: str, *, icon_key: str | None = None) -> QLabel:
        label = QLabel(text)
        label.setObjectName("bioProjectFieldLabel")
        if icon_key:
            label.setToolTip(text)
        return label

    def _icon_label(self, icon_key: str, size: int = 24) -> QLabel:
        label = QLabel()
        label.setObjectName("bioProjectIcon")
        label.setFixedSize(size + 4, size + 4)
        label.setAlignment(Qt.AlignCenter)
        pixmap = load_ui03_project_home_pixmap(icon_key, size)
        label.setPixmap(pixmap)
        label.setVisible(not pixmap.isNull())
        return label

    def _title_row(self, title: str, icon_key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING["sm"])
        row.addWidget(self._icon_label(icon_key, 36))
        label = QLabel(title)
        label.setObjectName("bioProjectCardTitle")
        row.addWidget(label)
        row.addStretch(1)
        return row

    def _icon_text_row(self, label: QLabel, icon_key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING["sm"])
        row.addWidget(self._icon_label(icon_key, 22), alignment=Qt.AlignTop)
        row.addWidget(label, 1)
        return row


def _project_status_text(summary: BioinformaticsProjectSummary) -> str:
    stage = {
        "project_created": "项目已创建",
    }.get(summary.current_stage, "项目已打开")
    readiness = {
        "ready_for_data_source_selection": "等待选择数据来源",
        "尚未生成": "等待准备数据",
    }.get(summary.readiness_status, _readable_status(summary.readiness_status))
    return f"{stage}，{readiness}"


def _current_step_key(summary: BioinformaticsProjectSummary) -> str:
    if summary.readiness_status == "ready_for_data_source_selection":
        return "ready_for_data_source_selection"
    if _acquisition_record_count(summary.project_root) > 0:
        return "data_recognition"
    return "project_created"


def _step_state(step_key: str, current_step: str) -> str:
    order = [item[0] for item in WORKFLOW_STEPS]
    if order.index(step_key) < order.index(current_step):
        return "done"
    if step_key == current_step:
        return "current"
    return "todo"


def _step_state_prefix(state: str) -> str:
    if state == "done":
        return "✓ "
    if state == "current":
        return "当前："
    return "未开始："


def _mini_status(summary: BioinformaticsProjectSummary, key: str) -> tuple[str, str]:
    if key == "data_source":
        return "数据来源", "已选择" if _acquisition_record_count(summary.project_root) else "未选择"
    if key == "sample_recognition":
        report = _read_json_or_none(summary.project_root / "logs" / "recognition" / "recognition_report.json")
        return "样本识别", "已识别" if isinstance(report, dict) and report.get("files") else "未开始"
    if key == "analysis_results":
        index = _read_json_or_none(summary.project_root / "results" / "summaries" / "result_index.json")
        entries = []
        if isinstance(index, dict):
            raw = index.get("results") or index.get("entries") or []
            entries = [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
        return "分析结果", f"已有 {len(entries)} 项" if entries else "暂无"
    if key == "project_report":
        report = summary.project_root / "reports" / "project_analysis_report.md"
        has_report = report.exists() or any((summary.project_root / "reports").glob("*.md"))
        return "项目报告", "已生成" if has_report else "未生成"
    return "", ""


def _technical_details_text(summary: BioinformaticsProjectSummary) -> str:
    return "\n".join(
        [
            f"project_stage: {summary.current_stage}",
            f"readiness: {summary.readiness_status}",
            f"manifest path: {summary.manifest_path}",
            f"config path: {summary.config_path}",
            f"project root: {summary.project_root}",
        ]
    )


def _project_warning_summaries(summary: BioinformaticsProjectSummary) -> list[str]:
    manifest = _read_json_or_none(summary.manifest_path)
    readiness = manifest.get("readiness") if isinstance(manifest, dict) else {}
    warnings = readiness.get("warnings") if isinstance(readiness, dict) else []
    return [str(item) for item in warnings[:3]] if isinstance(warnings, list) else []


def _acquisition_record_count(project_root: Path) -> int:
    records = project_root / "acquisition" / "records"
    if not records.exists():
        return 0
    return sum(1 for path in records.glob("*.json") if path.name != "latest_acquisition_record.json")


def _read_json_or_none(path: Path) -> dict[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None


def _format_user_time(value: str) -> str:
    if not value or value == "未记录":
        return "未记录"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _compact_user_path(path: Path) -> str:
    home = Path.home()
    try:
        relative = path.resolve().relative_to(home)
        return " / ".join(relative.parts)
    except ValueError:
        parts = path.resolve().parts
        return " / ".join(parts[-3:]) if len(parts) >= 3 else str(path)


def _readable_status(value: str) -> str:
    return {
        "no_recent_analysis": "暂无分析结果",
        "not_selected": "未选择",
        "project_created": "项目已创建",
    }.get(value, value or "未记录")
