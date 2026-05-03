from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

        self._summary_lines: list[QLabel] = []
        for _ in range(7):
            line = QLabel("")
            line.setObjectName("bioProjectSummaryLine")
            line.setWordWrap(True)
            self._summary_lines.append(line)
            layout.addWidget(line)

        return frame

    def _render_summary(self, summary: BioinformaticsProjectSummary | None) -> None:
        self._current_summary = summary
        has_summary = summary is not None
        self._empty_state_label.setVisible(not has_summary)
        values = []
        if summary is not None:
            values = [
                f"项目名称：{summary.project_name or '未知'}",
                f"项目路径：{summary.project_root}",
                f"创建时间：{summary.created_at or '未记录'}",
                f"当前阶段：{summary.current_stage or '未知'}",
                f"Ready 状态：{summary.readiness_status or '尚未生成'}",
                f"警告数量：{summary.warning_count}",
                f"最近分析结果：{summary.recent_analysis_result or '暂无最近分析结果'}",
            ]
        for index, label in enumerate(self._summary_lines):
            label.setText(values[index] if index < len(values) else "")
            label.setVisible(has_summary)

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
