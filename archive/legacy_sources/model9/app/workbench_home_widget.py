from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui_style_tokens import COLORS, SPACING


class WorkbenchHomeWidget(QWidget):
    def __init__(
        self,
        *,
        on_open_bioinformatics: Callable[[], None],
        on_open_meta_analysis: Callable[[], None],
        on_create_project: Callable[[], None] | None = None,
        on_load_demo_project: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_open_bioinformatics = on_open_bioinformatics
        self._on_open_meta_analysis = on_open_meta_analysis
        self._on_create_project = on_create_project
        self._on_load_demo_project = on_load_demo_project
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["md"])
        root.setSpacing(SPACING["md"])
        root.addWidget(self._build_navigation())

        main = QVBoxLayout()
        main.setSpacing(SPACING["md"])
        root.addLayout(main, 1)

        hero = QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        title = QLabel("BioMedPilot / 医研智析")
        title.setObjectName("heroTitle")
        subtitle = QLabel("Internal testing build for Meta Analysis and Bioinformatics workflows.")
        subtitle.setObjectName("mutedLabel")
        subtitle.setWordWrap(True)
        self._capability_notice = QLabel(
            "Capability notice: internal testing build, not a formal release. "
            "Statistics runners, AI/PDF extraction, and PDF/Word export are not implemented here."
        )
        self._capability_notice.setObjectName("mutedLabel")
        self._capability_notice.setWordWrap(True)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addWidget(self._capability_notice)
        main.addWidget(hero)

        entries = QHBoxLayout()
        entries.setSpacing(SPACING["md"])
        entries.addWidget(
            self._entry_card(
                title="生信分析 Bioinformatics",
                description="GEO / TCGA / GTEx · 差异分析 · 富集分析 · 生存分析 · 可视化",
                buttons=("进入模块", "最近项目", "新建分析"),
                preview_titles=("Volcano Plot 占位", "Heatmap Top 50 占位"),
                accent=COLORS["bio"],
                soft=COLORS["bio_soft"],
                on_open=self._on_open_bioinformatics,
                object_name="bioinformaticsEntryCard",
            )
        )
        entries.addWidget(
            self._entry_card(
                title="Meta 分析 Meta Analysis",
                description="PICO / 检索 / 筛选 / 提取 / Forest Plot / Reporting",
                buttons=("进入模块", "最近项目", "新建项目"),
                preview_titles=("Forest Plot 占位", "PRISMA 流程占位"),
                accent=COLORS["meta"],
                soft=COLORS["meta_soft"],
                on_open=self._on_open_meta_analysis,
                object_name="metaAnalysisEntryCard",
            )
        )
        main.addLayout(entries, 2)

        project_actions = QFrame()
        project_actions.setObjectName("card")
        project_layout = QVBoxLayout(project_actions)
        project_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        project_title = QLabel("Project actions")
        project_title.setStyleSheet("font-weight: 700; background: transparent;")
        self._current_project_label = QLabel("Current project: No project opened")
        self._current_project_label.setObjectName("mutedLabel")
        self._current_project_label.setWordWrap(True)
        project_note = QLabel(
            "Create Project and Load Demo Project are active for internal testing. "
            "Open Project is available through the current project API; file-picker UI is planned."
        )
        project_note.setObjectName("mutedLabel")
        project_note.setWordWrap(True)
        action_row = QHBoxLayout()
        self._create_project_button = QPushButton("Create Project")
        self._create_project_button.setObjectName("createProjectButton")
        self._create_project_button.clicked.connect(self._trigger_create_project)
        self._open_project_button = QPushButton("Open Project")
        self._open_project_button.setObjectName("openProjectButton")
        self._open_project_button.setEnabled(False)
        self._load_demo_project_button = QPushButton("Load Demo Project")
        self._load_demo_project_button.setObjectName("loadDemoProjectButton")
        self._load_demo_project_button.clicked.connect(self._trigger_load_demo_project)
        action_row.addWidget(self._create_project_button)
        action_row.addWidget(self._open_project_button)
        action_row.addWidget(self._load_demo_project_button)
        action_row.addStretch(1)
        demo_note = QLabel(
            "Demo profiles: Treatment Effect Demo, Diagnostic Accuracy Demo, "
            "Biomarker Prevalence Demo."
        )
        demo_note.setObjectName("mutedLabel")
        demo_note.setWordWrap(True)
        project_layout.addWidget(project_title)
        project_layout.addWidget(self._current_project_label)
        project_layout.addWidget(project_note)
        project_layout.addLayout(action_row)
        project_layout.addWidget(demo_note)
        main.addWidget(project_actions)

        info = QGridLayout()
        info.setSpacing(SPACING["md"])
        for index, (title_text, lines) in enumerate(
            [
                ("最近项目", ["TCGA-LUAD mock", "Meta cardiovascular review mock"]),
                ("统一任务中心", ["2 active mock tasks", "Ready"]),
                ("共享资源", ["Reference gene sets", "Report templates"]),
                ("快速开始", ["Choose a module", "Create or open a project"]),
            ]
        ):
            info.addWidget(self._info_card(title_text, lines), index // 2, index % 2)
        main.addLayout(info)

        status = QLabel("Current status: Internal testing build · No statistics are run from this home screen.")
        status.setObjectName("statusLabel")
        main.addWidget(status)

    def _build_navigation(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sidePanel")
        frame.setFixedWidth(176)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["sm"], SPACING["md"], SPACING["sm"], SPACING["md"])
        title = QLabel("BioMedPilot")
        title.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title)
        for index, text in enumerate(["工作台", "项目中心", "数据中心", "任务中心", "报告中心", "团队协作", "设置"]):
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.setEnabled(index == 0)
            layout.addWidget(button)
        layout.addStretch(1)
        return frame

    def _entry_card(
        self,
        *,
        title: str,
        description: str,
        buttons: tuple[str, str, str],
        preview_titles: tuple[str, str],
        accent: str,
        soft: str,
        on_open: Callable[[], None],
        object_name: str,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("entryCard")
        frame.setProperty("entryName", object_name)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])
        title_widget = QLabel(title)
        title_widget.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {accent}; background: transparent;")
        description_widget = QLabel(description)
        description_widget.setObjectName("mutedLabel")
        description_widget.setWordWrap(True)
        layout.addWidget(title_widget)
        layout.addWidget(description_widget)

        button_row = QHBoxLayout()
        for index, text in enumerate(buttons):
            button = QPushButton(text)
            if index == 0:
                button.setObjectName("primaryButton" if accent == COLORS["bio"] else "metaButton")
                button.clicked.connect(on_open)
            else:
                button.setEnabled(False)
            button_row.addWidget(button)
        layout.addLayout(button_row)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(SPACING["sm"])
        for preview_title in preview_titles:
            preview = QLabel(preview_title)
            preview.setAlignment(Qt.AlignCenter)
            preview.setMinimumHeight(120)
            preview.setStyleSheet(f"background: {soft}; border: 1px dashed {accent}; border-radius: 12px; color: {accent};")
            preview_row.addWidget(preview)
        layout.addLayout(preview_row, 1)
        return frame

    def _info_card(self, title: str, lines: list[str]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        title_widget = QLabel(title)
        title_widget.setStyleSheet("font-weight: 700; background: transparent;")
        layout.addWidget(title_widget)
        for line in lines:
            label = QLabel(line)
            label.setObjectName("mutedLabel")
            layout.addWidget(label)
        return frame

    def entry_titles(self) -> list[str]:
        return ["Bioinformatics", "Meta Analysis"]

    def set_current_project_summary(self, summary: str) -> None:
        self._current_project_label.setText(f"Current project: {summary}")

    def current_project_text(self) -> str:
        return self._current_project_label.text()

    def capability_notice_text(self) -> str:
        return self._capability_notice.text()

    def project_action_labels(self) -> list[str]:
        return [
            self._create_project_button.text(),
            self._open_project_button.text(),
            self._load_demo_project_button.text(),
        ]

    def _trigger_create_project(self) -> None:
        if self._on_create_project is not None:
            self._on_create_project()

    def _trigger_load_demo_project(self) -> None:
        if self._on_load_demo_project is not None:
            self._on_load_demo_project()
