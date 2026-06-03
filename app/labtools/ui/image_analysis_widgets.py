from __future__ import annotations

try:
    import html
    from pathlib import Path

    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.image_analysis import (
        IMAGE_REVIEW_NOTICE,
        TASK_TYPES,
        ImageAnalysisError,
        ImageAnalysisTaskStore,
        ImageAnalysisTaskWorkspace,
        MacroTemplate,
        default_macro_for_analysis,
        export_fluorescence_analysis_package,
        export_wound_healing_analysis_package,
    )
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
    from app.labtools.ui.imagej_bridge_widgets import LabToolsImageJFijiStatusPanel
    from app.shared.local_engines import ImageJFijiBridge
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception as exc:  # pragma: no cover
    IMAGE_ANALYSIS_WIDGETS_IMPORT_ERROR = f"{exc.__class__.__name__}: {exc}"
    QWidget = None  # type: ignore[assignment]
else:
    IMAGE_ANALYSIS_WIDGETS_IMPORT_ERROR = ""


if QWidget is not None:

    def _format_bytes(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"


    def _image_workbench_chip(text: str, status: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("imageWorkbenchStatusChip")
        label.setProperty("statusKey", status)
        colors = {
            "available": (COLORS["success_soft"], COLORS["success_border"], COLORS["success"]),
            "testing": (COLORS["bio_soft"], COLORS["border"], COLORS["bio"]),
            "blocked": (COLORS["warning_soft"], COLORS["warning_border"], COLORS["warning"]),
        }.get(status, (COLORS["surface_muted"], COLORS["border"], COLORS["muted"]))
        label.setStyleSheet(
            f"QLabel#imageWorkbenchStatusChip {{ background: {colors[0]}; border: 1px solid {colors[1]}; "
            f"color: {colors[2]}; border-radius: {RADIUS['sm']}px; padding: 5px 9px; font-weight: 700; }}"
        )
        return label


    class LabToolsImageAnalysisWidget(QWidget):
        def __init__(self, *, imagej_bridge: ImageJFijiBridge | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsImageAnalysisWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._imagej_bridge = imagej_bridge
            self._image_records: list[LabImageRecord] = []
            self._tasks: list[ImageAnalysisTask] = []
            self._latest_export_kind = ""
            self._latest_export_result = None
            self._latest_analysis_text = ""
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
            root.addWidget(
                LabToolsImageJFijiStatusPanel(
                    workflow_name="LabTools 图像分析 workflow",
                    bridge=self._imagej_bridge,
                    can_continue_without_engine=True,
                )
            )
            root.addWidget(self._build_import_card())
            root.addWidget(self._build_task_card_grid())
            root.addWidget(self._build_wound_healing_card())
            root.addWidget(self._build_fluorescence_card())

            self._task_summary = QTextEdit()
            self._task_summary.setObjectName("imageResultPanel")
            self._task_summary.setReadOnly(True)
            self._task_summary.setText(self._empty_summary())
            export_row = QHBoxLayout()
            self._export_button = QPushButton("导出当前 ROI 结果")
            self._export_button.setObjectName("secondaryButton")
            self._export_button.setEnabled(False)
            self._export_button.clicked.connect(self._handle_export_current_result)
            export_note = QLabel("仅在用户选择目录后写入 JSON manifest、CSV summary、Markdown 片段和 ROI overlay PNG。")
            export_note.setObjectName("imageTaskStatus")
            export_note.setWordWrap(True)
            export_row.addWidget(export_note, 1)
            export_row.addWidget(self._export_button)
            root.addLayout(export_row)
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
                status_text = "MVP 可用：manual ROI grayscale 指标；需人工复核"
            elif task_type == "wound_healing":
                status_text = "MVP 可用：manual ROI + user threshold 面积估算；semi-quantitative"
            else:
                status_text = "占位：algorithm_not_available，未生成定量结果"
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
            support = QLabel("仅支持单张本地图片和手动矩形 ROI 的 grayscale 指标；不会自动识别细胞、划痕或条带，结果必须人工复核。")
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
            support = QLabel("仅支持单张本地图片、手动矩形 ROI 和用户阈值；结果为基于阈值的划痕区域估算，不能自动解释迁移效果。")
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
            self._latest_export_kind = "fluorescence_intensity"
            self._latest_export_result = result
            self._export_button.setEnabled(True)
            audit_line = f"审计记录：{len(audit_records)} 条；算法参数已随结果结构记录。"
            self._latest_analysis_text = f"{self._render_fluorescence_result(result)}\n\n{audit_line}"
            self._task_summary.setText(self._latest_analysis_text)

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
            self._latest_export_kind = "wound_healing"
            self._latest_export_result = result
            self._export_button.setEnabled(True)
            audit_line = f"审计记录：{len(audit_records)} 条；算法参数已随结果结构记录。"
            self._latest_analysis_text = f"{self._render_wound_result(result)}\n\n{audit_line}"
            self._task_summary.setText(self._latest_analysis_text)

        def has_exportable_result(self) -> bool:
            return self._latest_export_result is not None and self._latest_export_kind in {
                "fluorescence_intensity",
                "wound_healing",
            }

        def set_export_result_for_testing(self, export_kind: str, result) -> None:
            self._latest_export_kind = export_kind
            self._latest_export_result = result
            self._latest_analysis_text = "测试分析结果已设置；仅用于 UI 导出行为测试。"
            self._export_button.setEnabled(self.has_exportable_result())

        def _handle_export_current_result(self) -> None:
            if not self.has_exportable_result():
                self._task_summary.setText("请先运行荧光 ROI 或划痕 ROI 分析，再导出结果。")
                return
            directory = self._select_export_directory()
            if not directory:
                self._task_summary.setText(self._export_cancelled_text())
                return
            try:
                package = self._perform_export_to_directory(directory)
            except Exception as exc:
                self._task_summary.setText(self._export_failed_text(str(exc)))
                return
            self._task_summary.setText(self._render_export_package_summary(package))

        def _select_export_directory(self) -> str:
            return QFileDialog.getExistingDirectory(self, "选择 ROI 结果导出目录")

        def _perform_export_to_directory(self, directory: str):
            if self._latest_export_kind == "fluorescence_intensity":
                return export_fluorescence_analysis_package(self._latest_export_result, directory)
            if self._latest_export_kind == "wound_healing":
                return export_wound_healing_analysis_package(self._latest_export_result, directory)
            raise ImageAnalysisError("当前结果类型暂不支持导出。")

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
                    "导出说明：以上内容默认为内存预览；只有点击“导出当前 ROI 结果”并选择目录后才会写入本地文件。",
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
                    "导出说明：以上内容默认为内存预览；只有点击“导出当前 ROI 结果”并选择目录后才会写入本地文件。",
                ]
            )

        def _render_export_package_summary(self, package) -> str:
            warnings = "\n".join(f"- {warning}" for warning in package.warnings) or "- 无"
            return "\n".join(
                [
                    "导出成功",
                    "ROI 结果导出完成",
                    "软件状态：Developer Preview / testing",
                    f"分析类型：{package.analysis_type}",
                    f"导出目录：{package.output_dir}",
                    "",
                    "写入文件",
                    f"- JSON manifest：{package.manifest_path}",
                    f"- CSV summary：{package.csv_path}",
                    f"- Markdown 片段：{package.markdown_path}",
                    f"- ROI overlay PNG：{package.overlay_path}",
                    "",
                    "人工复核提示",
                    package.review_notice,
                    "",
                    "warning",
                    warnings,
                    "",
                    "语义边界：导出文件为 manual ROI auxiliary analysis / manual-review / semi-quantitative 辅助结果，不构成自动算法结论、临床建议或实验 SOP。",
                ]
            )

        def _export_cancelled_text(self) -> str:
            previous = self._latest_analysis_text or "当前分析结果仍保留在内存预览中。"
            return "\n\n".join(["已取消导出，当前分析结果仍保留；未写入任何文件。", previous])

        def _export_failed_text(self, message: str) -> str:
            previous = self._latest_analysis_text or "当前分析结果仍保留在内存预览中。"
            clean_message = (message or "未知导出错误").splitlines()[0]
            return "\n\n".join(["导出需要调整", clean_message, "当前分析结果保留如下", previous])

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

    class ImageAnalysisWorkbenchWidget(QWidget):
        def __init__(
            self,
            *,
            experiment_module: str,
            analysis_type: str,
            title: str,
            primary_actions: tuple[str, ...],
            parameter_defaults: dict[str, str | bool],
            task_store: ImageAnalysisTaskStore | None = None,
        ) -> None:
            super().__init__()
            self.setObjectName("imageAnalysisWorkbench")
            self.setProperty("uiPrimitive", "labtools_c2_gated_workbench")
            self.setProperty("connectionStatus", "connected")
            self.setProperty("formalActionEnabled", False)
            self.setProperty("experimentModule", experiment_module)
            self.setProperty("analysisType", analysis_type)
            self.setStyleSheet(self._stylesheet())
            self._experiment_module = experiment_module
            self._analysis_type = analysis_type
            self._title = title
            self._primary_actions = primary_actions
            self._parameter_defaults = parameter_defaults
            self._task_store = task_store or ImageAnalysisTaskStore()
            self._image_paths: list[str] = []
            self._latest_workspace: ImageAnalysisTaskWorkspace | None = None
            self._macro_template = default_macro_for_analysis(experiment_module, analysis_type)
            self._parameter_widgets: dict[str, QLineEdit | QCheckBox | QComboBox] = {}
            self._build_ui()

        def latest_workspace(self) -> ImageAnalysisTaskWorkspace | None:
            return self._latest_workspace

        def set_image_paths_for_testing(self, paths: tuple[str, ...]) -> None:
            self._image_paths = [str(path) for path in paths]
            self._refresh_image_table()
            self._refresh_preview()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, SPACING["md"], 0, 0)
            root.setSpacing(SPACING["md"])

            header = QFrame()
            header.setObjectName("imageWorkbenchHeader")
            header_layout = QVBoxLayout(header)
            header_layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
            title = QLabel(self._title)
            title.setObjectName("labToolsSectionTitle")
            subtitle = QLabel("实验图像分析工作台：导入图片、检查预览、设置实验参数、生成 run request；不直接执行外部图像引擎，不产出正式定量结论。")
            subtitle.setObjectName("imageTaskStatus")
            subtitle.setWordWrap(True)
            chip_row = QHBoxLayout()
            chip_row.addWidget(_image_workbench_chip("testing / 可测试", "testing"))
            chip_row.addWidget(_image_workbench_chip("run request", "available"))
            chip_row.addWidget(_image_workbench_chip("engine gated", "blocked"))
            chip_row.addStretch(1)
            header_layout.addWidget(title)
            header_layout.addWidget(subtitle)
            header_layout.addLayout(chip_row)
            engine_notice = QLabel(
                "图像分析引擎未准备好。请在外部引擎设置中完成 ImageJ 配置；需要插件型 macro 时再配置 Fiji 增强路径。当前页面仍可用于导入图片、保存任务和准备分析参数。"
            )
            engine_notice.setObjectName("imageWorkbenchEngineStatus")
            engine_notice.setWordWrap(True)
            review = QLabel("自动图像识别和测量结果仅用于辅助分析，请人工复核 ROI、阈值和输出结果。")
            review.setObjectName("imageNotice")
            review.setWordWrap(True)
            root.addWidget(header)
            root.addWidget(engine_notice)
            root.addWidget(review)

            workbench_row = QHBoxLayout()
            workbench_row.addWidget(self._build_image_list_panel(), 2)
            workbench_row.addWidget(self._build_preview_panel(), 3)
            workbench_row.addWidget(self._build_parameter_panel(), 2)
            root.addLayout(workbench_row, 3)

            self._result_panel = QTextEdit()
            self._result_panel.setObjectName("imageWorkbenchResultPanel")
            self._result_panel.setReadOnly(True)
            self._result_panel.setMinimumHeight(150)
            self._result_panel.setText(self._empty_result_text())
            root.addWidget(self._result_panel, 2)
            root.addWidget(self._build_diagnostics_panel())

        def _build_image_list_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("图片列表 / 样本列表")
            heading.setObjectName("imageCardTitle")
            self._image_table = QTableWidget(0, 4)
            self._image_table.setObjectName("imageWorkbenchImageTable")
            self._image_table.setHorizontalHeaderLabels(("文件名", "分组", "时间点", "导入状态"))
            self._image_table.setMinimumHeight(180)
            button_row = QHBoxLayout()
            add_files = QPushButton("导入图片")
            add_files.setObjectName("imageWorkbenchImportFilesButton")
            add_files.setProperty("buttonBehavior", "opens_local_image_file_picker")
            add_files.clicked.connect(self._handle_import_files)
            add_folder = QPushButton("导入文件夹")
            add_folder.setObjectName("imageWorkbenchImportFolderButton")
            add_folder.setProperty("buttonBehavior", "imports_supported_images_from_local_folder")
            add_folder.clicked.connect(self._handle_import_folder)
            remove = QPushButton("移除图片")
            remove.setObjectName("imageWorkbenchRemoveImageButton")
            remove.setProperty("buttonBehavior", "removes_selected_image_reference")
            remove.clicked.connect(self._handle_remove_selected_image)
            for button in (add_files, add_folder, remove):
                button_row.addWidget(button)
            layout.addWidget(heading)
            layout.addWidget(self._image_table)
            layout.addLayout(button_row)
            return frame

        def _build_preview_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("图片预览与标注区")
            heading.setObjectName("imageCardTitle")
            self._preview = QTextEdit()
            self._preview.setObjectName("imageWorkbenchPreviewPanel")
            self._preview.setReadOnly(True)
            self._preview.setMinimumHeight(240)
            self._preview.setText("尚未选择图片。第一版显示文件路径和 ROI / lane / mask / cell count overlay 占位，不提供通用图片编辑器。")
            layout.addWidget(heading)
            layout.addWidget(self._preview, 1)
            return frame

        def _build_parameter_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("实验参数与操作")
            heading.setObjectName("imageCardTitle")
            layout.addWidget(heading)
            form = QGridLayout()
            for index, (name, default) in enumerate(self._parameter_defaults.items()):
                form.addWidget(QLabel(name), index, 0)
                if isinstance(default, bool):
                    widget = QCheckBox("是")
                    widget.setChecked(default)
                elif name == "输出格式":
                    widget = QComboBox()
                    widget.addItems(("CSV", "TXT"))
                    widget.setCurrentText(str(default))
                else:
                    widget = QLineEdit(str(default))
                widget.setObjectName(f"imageWorkbenchParameter_{index}")
                self._parameter_widgets[name] = widget
                form.addWidget(widget, index, 1)
            layout.addLayout(form)
            for action in self._primary_actions:
                button = QPushButton(action)
                button.setObjectName("imageWorkbenchPrimaryActionButton" if action != "导出结果，占位" else "imageWorkbenchExportPlaceholderButton")
                if action == "导出结果，占位":
                    reason = "当前页面只生成 run request；尚未产生真实图像分析结果，不能导出正式结果。"
                    button.setEnabled(False)
                    button.setProperty("buttonBehavior", "disabled_missing_real_image_analysis_result")
                    button.setProperty("disabledReason", reason)
                    button.setToolTip(reason)
                else:
                    button.setProperty("buttonBehavior", "creates_image_analysis_run_request_without_running_engine")
                    button.setProperty("formalActionEnabled", False)
                    button.clicked.connect(lambda _checked=False, action_text=action: self._handle_generate_run_request(action_text))
                layout.addWidget(button)
            return frame

        def _build_diagnostics_panel(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("高级诊断区（默认折叠）")
            heading.setObjectName("imageCardTitle")
            self._diagnostics = QTextEdit()
            self._diagnostics.setObjectName("imageWorkbenchDiagnosticsPanel")
            self._diagnostics.setReadOnly(True)
            self._diagnostics.setMinimumHeight(100)
            self._diagnostics.setText(self._diagnostic_text(self._macro_template))
            layout.addWidget(heading)
            layout.addWidget(self._diagnostics)
            return frame

        def _handle_import_files(self) -> None:
            paths, _selected_filter = QFileDialog.getOpenFileNames(
                self,
                "导入实验图像",
                "",
                "Image Files (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.gif)",
            )
            if paths:
                self._image_paths.extend(paths)
                self._refresh_image_table()
                self._refresh_preview()

        def _handle_import_folder(self) -> None:
            directory = QFileDialog.getExistingDirectory(self, "导入实验图像文件夹")
            if not directory:
                return
            supported = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}
            paths = [str(path) for path in sorted(Path(directory).iterdir()) if path.suffix.lower() in supported and path.is_file()]
            self._image_paths.extend(paths)
            self._refresh_image_table()
            self._refresh_preview()

        def _handle_remove_selected_image(self) -> None:
            row = self._image_table.currentRow()
            if 0 <= row < len(self._image_paths):
                self._image_paths.pop(row)
                self._refresh_image_table()
                self._refresh_preview()

        def _refresh_image_table(self) -> None:
            self._image_table.setRowCount(len(self._image_paths))
            for row, path_text in enumerate(self._image_paths):
                path = Path(path_text)
                values = (path.name, self._parameter_value("分组"), self._parameter_value("时间点"), "已引用")
                for column, value in enumerate(values):
                    self._image_table.setItem(row, column, QTableWidgetItem(str(value)))

        def _refresh_preview(self) -> None:
            if not self._image_paths:
                self._preview.setText("尚未选择图片。第一版显示文件路径和 ROI / lane / mask / cell count overlay 占位，不提供通用图片编辑器。")
                return
            current = Path(self._image_paths[0])
            image_uri = current.resolve().as_uri() if current.exists() else ""
            escaped_name = html.escape(current.name)
            escaped_path = html.escape(str(current))
            image_html = (
                f'<img src="{image_uri}" style="max-width:100%; max-height:260px; border:1px solid #D8E1EC; border-radius:8px;" />'
                if image_uri
                else "<p><b>图片文件不存在，无法显示缩略图。</b></p>"
            )
            self._preview.setHtml(
                "\n".join(
                    [
                        f"<p><b>当前图片：</b>{escaped_name}</p>",
                        f"<p><b>原始路径：</b>{escaped_path}</p>",
                        image_html,
                        "<p><b>标注状态：</b>已进入预览；ROI / lane / mask / cell count overlay 将由下方“生成分析任务”写入 RunRequest，真实测量仍需外部引擎或人工复核。</p>",
                    ]
                )
            )

        def _collect_parameters(self, action_text: str) -> dict[str, str | bool]:
            parameters: dict[str, str | bool] = {"requested_action": action_text}
            for name, widget in self._parameter_widgets.items():
                if isinstance(widget, QCheckBox):
                    parameters[name] = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    parameters[name] = widget.currentText()
                else:
                    parameters[name] = widget.text().strip()
            return parameters

        def _parameter_value(self, name: str) -> str:
            widget = self._parameter_widgets.get(name)
            if isinstance(widget, QLineEdit):
                return widget.text().strip()
            return ""

        def _handle_generate_run_request(self, action_text: str) -> None:
            if not self._image_paths:
                self._result_panel.setText("请先导入图片或文件夹，再生成分析任务。")
                return
            try:
                workspace = self._task_store.create_workspace(
                    task_name=self._title,
                    experiment_module=self._experiment_module,
                    analysis_type=self._analysis_type,
                    image_paths=tuple(self._image_paths),
                    import_mode="reference_original_path",
                    parameters=self._collect_parameters(action_text),
                )
                workspace = self._task_store.create_run_request(workspace)
            except ImageAnalysisError as exc:
                self._result_panel.setText(str(exc))
                return
            self._latest_workspace = workspace
            self._result_panel.setText(self._workspace_result_text(workspace))
            self._diagnostics.setText(self._diagnostic_text(workspace.macro_template, workspace))

        def _workspace_result_text(self, workspace: ImageAnalysisTaskWorkspace) -> str:
            return "\n".join(
                [
                    "RunRequest 已生成",
                    f"任务状态：{workspace.task.status}",
                    f"任务目录：{workspace.task_dir}",
                    f"输出目录：{workspace.output_dir}",
                    f"RunRequest：{workspace.run_request_path}",
                    "",
                    "预期结果文件",
                    "- outputs/results.csv",
                    "- outputs/summary.txt",
                    "- logs/run_log.txt",
                    "- review/manual_review.json",
                    "",
                    "尚未生成真实图像分析结果。请在外部引擎配置完成并实现对应 Macro 后运行分析。",
                    "",
                    "人工复核提示",
                    "自动图像识别和测量结果仅用于辅助分析，请人工复核 ROI、阈值和输出结果。",
                ]
            )

        def _empty_result_text(self) -> str:
            return "\n".join(
                [
                    "尚未生成 RunRequest。",
                    "结果区将显示任务状态、输出目录、预期结果文件、日志路径和人工复核提示。",
                    "尚未生成真实图像分析结果。请在外部引擎配置完成并实现对应 Macro 后运行分析。",
                ]
            )

        def _placeholder_export_text(self) -> str:
            return "导出结果，占位：本阶段未生成真实图像分析结果，因此不会写出正式结果文件。"

        def _diagnostic_text(self, macro: MacroTemplate, workspace: ImageAnalysisTaskWorkspace | None = None) -> str:
            lines = [
                f"Macro ID：{macro.macro_id}",
                f"Macro 路径：{macro.macro_file_path}",
                "外部引擎 key：imagej",
                f"最低引擎要求：{macro.minimum_engine_requirement}",
            ]
            if workspace is not None:
                lines.extend(
                    [
                        f"RunRequest 路径：{workspace.run_request_path}",
                        f"输出目录：{workspace.output_dir}",
                        "最近一次错误信息：无；外部引擎未就绪时仍只保存请求，不执行。",
                    ]
                )
            return "\n".join(lines)

        def _stylesheet(self) -> str:
            return f"""
            QWidget#imageAnalysisWorkbench {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QFrame#imageWorkbenchHeader {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QLabel#labToolsSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#imageNotice, QLabel#imageWorkbenchEngineStatus {{
                color: {COLORS["text"]};
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
            QFrame#labToolsCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QTextEdit#imageWorkbenchPreviewPanel, QTextEdit#imageWorkbenchResultPanel, QTextEdit#imageWorkbenchDiagnosticsPanel, QTableWidget#imageWorkbenchImageTable, QLineEdit, QComboBox {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px;
            }}
            QPushButton#imageWorkbenchPrimaryActionButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton#imageWorkbenchImportFilesButton, QPushButton#imageWorkbenchImportFolderButton, QPushButton#imageWorkbenchRemoveImageButton, QPushButton#imageWorkbenchExportPlaceholderButton {{
                color: {COLORS["bio"]};
                background: {COLORS["bio_soft"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            """

    def wb_grayscale_workbench_widget() -> ImageAnalysisWorkbenchWidget:
        return ImageAnalysisWorkbenchWidget(
            experiment_module="western_blot",
            analysis_type="wb_grayscale",
            title="Western Blot 结果与灰度分析",
            primary_actions=("识别 Lane", "识别 Band", "测量灰度值", "生成分析任务", "导出结果，占位"),
            parameter_defaults={
                "lane 数量": "10",
                "是否反转图像": False,
                "是否转换 8-bit": True,
                "背景扣除方式": "rolling ball，占位",
                "目标蛋白名称": "",
                "内参蛋白名称": "",
                "是否计算目标/内参比值": True,
                "输出格式": "CSV",
            },
        )

    def scratch_area_workbench_widget() -> ImageAnalysisWorkbenchWidget:
        return ImageAnalysisWorkbenchWidget(
            experiment_module="cell_experiment",
            analysis_type="scratch_area",
            title="划痕实验图像分析",
            primary_actions=("识别划痕区域", "计算划痕面积", "生成分析任务", "导出结果，占位"),
            parameter_defaults={
                "时间点": "0 h",
                "分组": "",
                "是否转换 8-bit": True,
                "阈值模式": "用户阈值，占位",
                "最小划痕区域面积": "占位",
                "是否计算愈合率": True,
                "输出格式": "CSV",
            },
        )

    def transwell_workbench_widget() -> ImageAnalysisWorkbenchWidget:
        return ImageAnalysisWorkbenchWidget(
            experiment_module="cell_experiment",
            analysis_type="transwell_count",
            title="Transwell 图像分析",
            primary_actions=("识别细胞区域", "统计细胞数", "生成分析任务", "导出结果，占位"),
            parameter_defaults={
                "分组": "",
                "是否转换 8-bit": True,
                "是否反转图像": False,
                "阈值模式": "用户阈值，占位",
                "最小颗粒面积": "占位",
                "最大颗粒面积": "占位",
                "输出指标": "细胞数",
                "输出格式": "CSV",
            },
        )

    def fluorescence_workbench_widget() -> ImageAnalysisWorkbenchWidget:
        return ImageAnalysisWorkbenchWidget(
            experiment_module="cell_experiment",
            analysis_type="fluorescence_intensity",
            title="荧光图像分析",
            primary_actions=("设置 ROI", "测量荧光强度", "生成分析任务", "导出结果，占位"),
            parameter_defaults={
                "通道": "Green",
                "是否背景扣除": True,
                "背景扣除半径": "占位",
                "ROI 模式": "全图",
                "输出指标": "mean intensity",
                "输出格式": "CSV",
            },
        )

else:  # pragma: no cover
    try:
        from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget as FallbackQWidget
    except Exception:
        FallbackQWidget = object  # type: ignore[assignment]
        QLabel = QVBoxLayout = None  # type: ignore[assignment]

    def _fallback_image_workbench(title: str) -> FallbackQWidget:
        widget = FallbackQWidget()
        if QVBoxLayout is None or QLabel is None:
            return widget
        widget.setObjectName("imageAnalysisWorkbenchFallback")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 20, 24, 20)
        heading = QLabel(title)
        heading.setObjectName("imageAnalysisFallbackTitle")
        detail = QLabel(
            "图像分析工作台依赖导入失败，当前页以安全占位显示，避免 LabTools 或主程序启动闪退。\n"
            f"导入错误：{IMAGE_ANALYSIS_WIDGETS_IMPORT_ERROR or 'unknown'}"
        )
        detail.setObjectName("imageAnalysisFallbackDetail")
        detail.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addStretch(1)
        return widget

    class LabToolsImageAnalysisWidget(FallbackQWidget):  # type: ignore[no-redef, misc]
        def __init__(self, *args, **kwargs) -> None:
            super().__init__()
            if QVBoxLayout is None or QLabel is None:
                return
            layout = QVBoxLayout(self)
            layout.addWidget(_fallback_image_workbench("图像定量"))

    class ImageAnalysisWorkbenchWidget(FallbackQWidget):  # type: ignore[no-redef, misc]
        pass

    def wb_grayscale_workbench_widget() -> FallbackQWidget:
        return _fallback_image_workbench("Western Blot 结果与灰度分析")

    def scratch_area_workbench_widget() -> FallbackQWidget:
        return _fallback_image_workbench("划痕实验图像分析")

    def transwell_workbench_widget() -> FallbackQWidget:
        return _fallback_image_workbench("Transwell 图像分析")

    def fluorescence_workbench_widget() -> FallbackQWidget:
        return _fallback_image_workbench("荧光图像分析")
