from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.image_analysis import IMAGE_REVIEW_NOTICE, TASK_TYPES, ImageAnalysisError
    from app.labtools.image_analysis.analysis_task import ImageAnalysisTask, create_analysis_task
    from app.labtools.image_analysis.image_io import create_image_record
    from app.labtools.image_analysis.image_models import LabImageRecord
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    def _format_bytes(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"


    class LabToolsImageAnalysisWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsImageAnalysisWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._image_records: list[LabImageRecord] = []
            self._tasks: list[ImageAnalysisTask] = []
            self._build_ui()

        def image_records(self) -> tuple[LabImageRecord, ...]:
            return tuple(self._image_records)

        def analysis_tasks(self) -> tuple[ImageAnalysisTask, ...]:
            return tuple(self._tasks)

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])

            title = QLabel("图像定量")
            title.setObjectName("labToolsSectionTitle")
            notice = QLabel(IMAGE_REVIEW_NOTICE)
            notice.setObjectName("imageNotice")
            notice.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(notice)
            root.addWidget(self._build_import_card())
            root.addWidget(self._build_task_card_grid())

            self._task_summary = QTextEdit()
            self._task_summary.setObjectName("imageResultPanel")
            self._task_summary.setReadOnly(True)
            self._task_summary.setText(self._empty_summary())
            root.addWidget(self._task_summary, 1)

        def _build_import_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("图片选择 / 路径输入")
            heading.setObjectName("imageCardTitle")
            row = QHBoxLayout()
            self._path_field = QLineEdit()
            self._path_field.setObjectName("imagePathField")
            self._path_field.setPlaceholderText("选择或填写本地图片路径")
            self._path_field.setMinimumHeight(CONTROL_HEIGHT["field"])
            browse = QPushButton("选择图片")
            browse.setObjectName("secondaryButton")
            browse.clicked.connect(self._handle_browse)
            create = QPushButton("生成图片记录")
            create.setObjectName("primaryButton")
            create.clicked.connect(self._handle_create_image_record)
            row.addWidget(self._path_field, 1)
            row.addWidget(browse)
            row.addWidget(create)
            self._image_summary = QTextEdit()
            self._image_summary.setObjectName("imageResultPanel")
            self._image_summary.setReadOnly(True)
            self._image_summary.setMinimumHeight(96)
            self._image_summary.setText("尚未生成图片记录。本阶段仅引用本地路径，不复制、不上传、不联网。")
            layout.addWidget(heading)
            layout.addLayout(row)
            layout.addWidget(self._image_summary)
            return frame

        def _build_task_card_grid(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("分析任务")
            heading.setObjectName("imageCardTitle")
            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            for index, (task_type, label) in enumerate(TASK_TYPES.items()):
                grid.addWidget(self._task_card(task_type, label), index // 2, index % 2)
            layout.addWidget(heading)
            layout.addLayout(grid)
            return frame

        def _task_card(self, task_type: str, label: str) -> QFrame:
            frame = QFrame()
            frame.setObjectName("imageTaskCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
            title = QLabel(label)
            title.setObjectName("imageTaskTitle")
            status = QLabel("框架已建立，算法开发中")
            status.setObjectName("imageTaskStatus")
            status.setWordWrap(True)
            button = QPushButton("创建任务草稿")
            button.setObjectName("secondaryButton")
            button.clicked.connect(lambda _checked=False, value=task_type: self._handle_create_task(value))
            layout.addWidget(title)
            layout.addWidget(status)
            layout.addStretch(1)
            layout.addWidget(button)
            return frame

        def _handle_browse(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "选择本地图片",
                "",
                "Image Files (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.gif)",
            )
            if path:
                self._path_field.setText(path)

        def _handle_create_image_record(self) -> None:
            try:
                record = create_image_record(self._path_field.text())
            except ImageAnalysisError as exc:
                self._image_summary.setText(f"图片记录需要调整\n{exc}")
                return
            self._image_records.append(record)
            warnings = "\n".join(f"- {warning}" for warning in record.warnings) or "- 无"
            self._image_summary.setText(
                "\n".join(
                    [
                        "已生成图片记录",
                        f"文件名：{record.filename}",
                        f"格式：{record.file_extension}",
                        f"大小：{_format_bytes(record.file_size_bytes)}",
                        f"校验状态：{record.validation_status}",
                        "提示",
                        warnings,
                        "",
                        "本阶段仅引用本地路径，不复制、不上传、不联网。",
                    ]
                )
            )

        def _handle_create_task(self, task_type: str) -> None:
            try:
                task = create_analysis_task(task_type, tuple(self._image_records[-1:]))
            except ImageAnalysisError as exc:
                self._task_summary.setText(f"任务草稿需要调整\n{exc}")
                return
            self._tasks.append(task)
            self._render_task_summary(task)

        def _render_task_summary(self, task: ImageAnalysisTask) -> None:
            image_line = "无图片记录" if not task.image_records else f"{len(task.image_records)} 个图片记录"
            lines = [
                "任务草稿",
                f"任务类型：{task.task_label}",
                f"状态：{task.status}",
                f"图片：{image_line}",
                "",
                "参数",
                "算法状态：开发中，未启用自动定量。",
                "人工复核：必需",
                "",
                "ROI",
                "ROI 待配置；本阶段不会自动识别区域。",
                "",
                "结果",
                "结果状态：algorithm_not_available",
                "未生成面积、细胞数、荧光强度或灰度数值。",
                "",
                "复核提示",
                task.review_notice,
            ]
            self._task_summary.setText("\n".join(lines))

        def _empty_summary(self) -> str:
            return "\n".join(
                [
                    "尚未创建图像分析任务草稿。",
                    "参数、ROI、结果和审计记录会在创建草稿后显示占位结构。",
                    IMAGE_REVIEW_NOTICE,
                ]
            )

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsImageAnalysisWorkspace {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QLabel#labToolsSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#imageNotice {{
                color: {COLORS["muted"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QLabel#imageCardTitle, QLabel#imageTaskTitle {{
                color: {COLORS["bio"]};
                font-weight: 700;
            }}
            QLabel#imageTaskStatus {{
                color: {COLORS["muted"]};
            }}
            QFrame#labToolsCard, QFrame#imageTaskCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QTextEdit#imageResultPanel, QLineEdit#imagePathField {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px;
            }}
            QPushButton#primaryButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton#secondaryButton {{
                color: {COLORS["bio"]};
                background: {COLORS["bio_soft"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            """

else:  # pragma: no cover

    class LabToolsImageAnalysisWidget:  # type: ignore[no-redef]
        pass
