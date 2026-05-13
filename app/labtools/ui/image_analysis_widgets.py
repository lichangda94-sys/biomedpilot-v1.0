from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QComboBox,
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
    from app.labtools.image_analysis.fluorescence import (
        FluorescenceAnalysisParameters,
        FluorescenceROI,
        analyze_fluorescence_roi,
        create_fluorescence_audit_records,
        fluorescence_csv_text,
        fluorescence_json_preview,
        fluorescence_markdown_report_fragment,
        fluorescence_metrics_table_text,
        fluorescence_parameter_summary,
        fluorescence_result_summary,
    )
    from app.labtools.image_analysis.wound_healing import (
        WoundHealingParameters,
        WoundHealingROI,
        analyze_wound_healing_area,
        create_wound_healing_audit_records,
        wound_csv_text,
        wound_json_preview,
        wound_markdown_report_fragment,
        wound_metrics_table_text,
        wound_parameter_summary,
        wound_result_summary,
    )
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
            root.addWidget(self._build_wound_healing_card())
            root.addWidget(self._build_fluorescence_card())

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
            if task_type == "fluorescence_intensity":
                status_text = "MVP 可用：手动 ROI"
            elif task_type == "wound_healing":
                status_text = "MVP 可用：手动 ROI + 阈值"
            else:
                status_text = "框架已建立，算法开发中"
            status = QLabel(status_text)
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

        def _build_fluorescence_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("荧光强度 ROI 分析 MVP")
            heading.setObjectName("imageCardTitle")
            grid = QGridLayout()
            grid.setSpacing(SPACING["sm"])
            self._signal_x = self._roi_field("x", "0")
            self._signal_y = self._roi_field("y", "0")
            self._signal_w = self._roi_field("width", "2")
            self._signal_h = self._roi_field("height", "2")
            self._background_x = self._roi_field("x", "0")
            self._background_y = self._roi_field("y", "0")
            self._background_w = self._roi_field("width", "2")
            self._background_h = self._roi_field("height", "2")
            run = QPushButton("运行荧光分析")
            run.setObjectName("primaryButton")
            run.clicked.connect(self._handle_run_fluorescence)
            grid.addWidget(QLabel("signal ROI"), 0, 0)
            grid.addWidget(self._signal_x, 0, 1)
            grid.addWidget(self._signal_y, 0, 2)
            grid.addWidget(self._signal_w, 0, 3)
            grid.addWidget(self._signal_h, 0, 4)
            grid.addWidget(QLabel("background ROI"), 1, 0)
            grid.addWidget(self._background_x, 1, 1)
            grid.addWidget(self._background_y, 1, 2)
            grid.addWidget(self._background_w, 1, 3)
            grid.addWidget(self._background_h, 1, 4)
            grid.addWidget(run, 2, 0, 1, 5)
            layout.addWidget(heading)
            layout.addLayout(grid)
            support = QLabel("仅支持单张本地图片和手动矩形 ROI；不会自动识别细胞、划痕或条带。")
            support.setObjectName("imageTaskStatus")
            support.setWordWrap(True)
            layout.addWidget(support)
            return frame

        def _build_wound_healing_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("划痕实验面积分析 MVP")
            heading.setObjectName("imageCardTitle")
            grid = QGridLayout()
            grid.setSpacing(SPACING["sm"])
            self._wound_x = self._roi_field("x", "0")
            self._wound_y = self._roi_field("y", "0")
            self._wound_w = self._roi_field("width", "10")
            self._wound_h = self._roi_field("height", "10")
            self._wound_threshold = self._roi_field("threshold 0-255", "128")
            self._wound_mode = QComboBox()
            self._wound_mode.addItem("亮划痕：pixel >= threshold", "bright")
            self._wound_mode.addItem("暗划痕：pixel <= threshold", "dark")
            self._wound_mode.setMinimumHeight(CONTROL_HEIGHT["field"])
            run = QPushButton("运行划痕面积分析")
            run.setObjectName("primaryButton")
            run.clicked.connect(self._handle_run_wound_healing)
            grid.addWidget(QLabel("analysis ROI"), 0, 0)
            grid.addWidget(self._wound_x, 0, 1)
            grid.addWidget(self._wound_y, 0, 2)
            grid.addWidget(self._wound_w, 0, 3)
            grid.addWidget(self._wound_h, 0, 4)
            grid.addWidget(QLabel("阈值"), 1, 0)
            grid.addWidget(self._wound_threshold, 1, 1)
            grid.addWidget(QLabel("模式"), 1, 2)
            grid.addWidget(self._wound_mode, 1, 3, 1, 2)
            grid.addWidget(run, 2, 0, 1, 5)
            layout.addWidget(heading)
            layout.addLayout(grid)
            support = QLabel("仅支持单张本地图片、手动矩形 ROI 和用户阈值；结果为基于阈值的划痕区域估算。")
            support.setObjectName("imageTaskStatus")
            support.setWordWrap(True)
            layout.addWidget(support)
            return frame

        def _roi_field(self, placeholder: str, text: str) -> QLineEdit:
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setText(text)
            field.setMinimumHeight(CONTROL_HEIGHT["field"])
            return field

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

        def _handle_run_fluorescence(self) -> None:
            try:
                signal_roi = FluorescenceROI(
                    label="signal ROI",
                    x=self._parse_roi_int(self._signal_x.text(), "signal x"),
                    y=self._parse_roi_int(self._signal_y.text(), "signal y"),
                    width=self._parse_roi_int(self._signal_w.text(), "signal width"),
                    height=self._parse_roi_int(self._signal_h.text(), "signal height"),
                    roi_type="signal",
                )
                background_roi = FluorescenceROI(
                    label="background ROI",
                    x=self._parse_roi_int(self._background_x.text(), "background x"),
                    y=self._parse_roi_int(self._background_y.text(), "background y"),
                    width=self._parse_roi_int(self._background_w.text(), "background width"),
                    height=self._parse_roi_int(self._background_h.text(), "background height"),
                    roi_type="background",
                )
                image_path = self._path_field.text().strip()
                if self._image_records and self._image_records[-1].source_path == image_path:
                    image_record = self._image_records[-1]
                else:
                    image_record = create_image_record(image_path, image_role="fluorescence_source")
                    self._image_records.append(image_record)
                task = create_analysis_task("fluorescence_intensity", (image_record,))
                parameters = FluorescenceAnalysisParameters(
                    image_path=image_path,
                    signal_roi=signal_roi,
                    background_roi=background_roi,
                )
                result = analyze_fluorescence_roi(parameters, task_id=task.task_id)
                audit_records = create_fluorescence_audit_records(result, source_path=parameters.image_path)
            except ValueError as exc:
                self._task_summary.setText(f"荧光分析需要调整\n{exc}")
                return
            except ImageAnalysisError as exc:
                self._task_summary.setText(f"荧光分析需要调整\n{exc}")
                return
            self._tasks.append(task)
            audit_line = f"审计记录：{len(audit_records)} 条；算法参数已随结果结构记录。"
            self._task_summary.setText(f"{self._render_fluorescence_result(result)}\n\n{audit_line}")

        def _handle_run_wound_healing(self) -> None:
            try:
                roi = WoundHealingROI(
                    label="analysis ROI",
                    x=self._parse_roi_int(self._wound_x.text(), "analysis x"),
                    y=self._parse_roi_int(self._wound_y.text(), "analysis y"),
                    width=self._parse_roi_int(self._wound_w.text(), "analysis width"),
                    height=self._parse_roi_int(self._wound_h.text(), "analysis height"),
                )
                threshold = self._parse_threshold_int(self._wound_threshold.text())
                scratch_mode = str(self._wound_mode.currentData() or "bright")
                image_path = self._path_field.text().strip()
                if self._image_records and self._image_records[-1].source_path == image_path:
                    image_record = self._image_records[-1]
                else:
                    image_record = create_image_record(image_path, image_role="wound_healing_source")
                    self._image_records.append(image_record)
                task = create_analysis_task("wound_healing", (image_record,))
                parameters = WoundHealingParameters(
                    image_path=image_path,
                    roi=roi,
                    threshold=threshold,
                    scratch_mode=scratch_mode,
                )
                result = analyze_wound_healing_area(parameters, task_id=task.task_id)
                audit_records = create_wound_healing_audit_records(result, source_path=parameters.image_path)
            except ValueError as exc:
                self._task_summary.setText(f"划痕面积分析需要调整\n{exc}")
                return
            except ImageAnalysisError as exc:
                self._task_summary.setText(f"划痕面积分析需要调整\n{exc}")
                return
            self._tasks.append(task)
            audit_line = f"审计记录：{len(audit_records)} 条；算法参数已随结果结构记录。"
            self._task_summary.setText(f"{self._render_wound_result(result)}\n\n{audit_line}")

        def _parse_roi_int(self, value: str, field_name: str) -> int:
            if value is None or str(value).strip() == "":
                raise ValueError(f"请填写 {field_name}。")
            try:
                return int(str(value).strip())
            except ValueError as exc:
                raise ValueError(f"{field_name} 必须是整数。") from exc

        def _parse_threshold_int(self, value: str) -> int:
            threshold = self._parse_roi_int(value, "threshold")
            if threshold < 0 or threshold > 255:
                raise ValueError("threshold 必须在 0-255 之间。")
            return threshold

        def _render_wound_result(self, result) -> str:
            warnings = "\n".join(f"- {warning}" for warning in result.warnings) or "- 无"
            csv_preview = "\n".join(wound_csv_text(result).splitlines()[:8])
            markdown_preview = "\n".join(wound_markdown_report_fragment(result).splitlines()[:30])
            return "\n\n".join(
                [
                    wound_result_summary(result),
                    wound_metrics_table_text(result),
                    wound_parameter_summary(result),
                    "\n".join(["warning", warnings]),
                    "\n".join(["复核提示", result.review_notice]),
                    wound_json_preview(result),
                    "\n".join(["CSV 导出预览", csv_preview]),
                    "\n".join(["Markdown 报告片段预览", markdown_preview]),
                    "导出说明：以上内容仅为内存中的字符串或数据结构预览，本阶段不会自动写盘。",
                ]
            )

        def _render_fluorescence_result(self, result) -> str:
            warnings = "\n".join(f"- {warning}" for warning in result.warnings) or "- 无"
            csv_preview = "\n".join(fluorescence_csv_text(result).splitlines()[:8])
            markdown_preview = "\n".join(fluorescence_markdown_report_fragment(result).splitlines()[:28])
            return "\n\n".join(
                [
                    fluorescence_result_summary(result),
                    fluorescence_metrics_table_text(result),
                    fluorescence_parameter_summary(result),
                    "\n".join(["warning", warnings]),
                    "\n".join(["复核提示", result.review_notice]),
                    fluorescence_json_preview(result),
                    "\n".join(["CSV 导出预览", csv_preview]),
                    "\n".join(["Markdown 报告片段预览", markdown_preview]),
                    "导出说明：以上内容仅为内存中的字符串或数据结构预览，本阶段不会自动写盘。",
                ]
            )

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
            QTextEdit#imageResultPanel, QLineEdit#imagePathField, QComboBox {{
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
