from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.labtools.image_analysis import ImageAnalysisTaskStore
from app.labtools.western_blot import (
    WB_ROI_TYPES,
    WBMeasurement,
    WBROICollection,
    WBRectangleROI,
    calculate_wb_normalization,
    create_wb_roi_run_request_workspace,
    export_wb_normalized_results,
    export_wb_roi_csv,
    export_wb_roi_json,
    read_wb_measurement_csv,
    unsupported_image_format_message,
)


WB_REVIEW_NOTICE = "自动预处理和灰度测量结果仅用于辅助分析，请人工复核 ROI、背景区域和归一化关系。"
ENGINE_NOT_READY_NOTICE = "图像分析引擎未准备好。请在外部引擎设置中完成 ImageJ/ImageJ-Fiji 配置。当前页面仍可用于导入图片、绘制 ROI、保存任务和准备分析参数。"


class WBROIImagePreview(QWidget):
    roiCreated = Signal(float, float, float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("wbRoiImagePreview")
        self.setMinimumHeight(260)
        self._pixmap: QPixmap | None = None
        self._rois: tuple[WBRectangleROI, ...] = ()
        self._drag_start: tuple[float, float] | None = None
        self._drag_current: tuple[float, float] | None = None

    def set_image_path(self, path: str) -> bool:
        pixmap = QPixmap(path)
        self._pixmap = None if pixmap.isNull() else pixmap
        self.update()
        return self._pixmap is not None

    def set_rois(self, rois: tuple[WBRectangleROI, ...]) -> None:
        self._rois = rois
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#F8FAFC"))
        rect = self._image_rect()
        if self._pixmap and rect:
            painter.drawPixmap(rect, self._pixmap, QRectF(0, 0, self._pixmap.width(), self._pixmap.height()))
        else:
            painter.setPen(QPen(QColor("#64748B")))
            painter.drawText(self.rect(), Qt.AlignCenter, "导入 WB 图片后在此拖拽绘制固定矩形 ROI")
        painter.setPen(QPen(QColor("#2563EB"), 2))
        for roi in self._rois:
            draw_rect = self._image_to_display_rect(roi.x, roi.y, roi.width, roi.height)
            if draw_rect:
                painter.drawRect(draw_rect)
                painter.drawText(int(draw_rect.x()), max(12, int(draw_rect.y()) - 4), roi.label or WB_ROI_TYPES[roi.roi_type])
        if self._drag_start and self._drag_current:
            x0, y0 = self._drag_start
            x1, y1 = self._drag_current
            painter.setPen(QPen(QColor("#0F766E"), 2, Qt.DashLine))
            painter.drawRect(QRectF(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)))

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._drag_start = (event.position().x(), event.position().y())
        self._drag_current = self._drag_start

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._drag_start:
            self._drag_current = (event.position().x(), event.position().y())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if not self._drag_start:
            return
        x0, y0 = self._drag_start
        x1, y1 = event.position().x(), event.position().y()
        self._drag_start = None
        self._drag_current = None
        if abs(x1 - x0) > 4 and abs(y1 - y0) > 4:
            self.roiCreated.emit(*self._display_to_image_rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)))
        self.update()

    def _image_rect(self) -> QRectF | None:
        if not self._pixmap:
            return None
        scale = min(self.width() / self._pixmap.width(), self.height() / self._pixmap.height())
        width = self._pixmap.width() * scale
        height = self._pixmap.height() * scale
        return QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)

    def _display_to_image_rect(self, x: float, y: float, width: float, height: float) -> tuple[float, float, float, float]:
        rect = self._image_rect()
        if not self._pixmap or rect is None:
            return (x, y, width, height)
        scale = rect.width() / self._pixmap.width()
        return (max(0, (x - rect.x()) / scale), max(0, (y - rect.y()) / scale), max(1, width / scale), max(1, height / scale))

    def _image_to_display_rect(self, x: float, y: float, width: float, height: float) -> QRectF | None:
        rect = self._image_rect()
        if not self._pixmap or rect is None:
            return None
        scale = rect.width() / self._pixmap.width()
        return QRectF(rect.x() + x * scale, rect.y() + y * scale, width * scale, height * scale)


class WesternBlotROIAnalysisWidget(QWidget):
    def __init__(self, *, task_store: ImageAnalysisTaskStore | None = None) -> None:
        super().__init__()
        self.setObjectName("westernBlotRoiAnalysisPage")
        self._task_store = task_store or ImageAnalysisTaskStore()
        self._roi_collection = WBROICollection()
        self._selected_roi_id = ""
        self._image_path = ""
        self._image_id = "wb_image_001"
        self._latest_workspace = None
        self._latest_measurements: tuple[WBMeasurement, ...] = ()
        self._build_ui()

    def set_image_path_for_testing(self, path: str) -> None:
        self._image_path_input.setText(path)
        self._import_image()

    def add_roi_for_testing(self, roi: WBRectangleROI) -> None:
        self._roi_collection.add_roi(roi)
        self._selected_roi_id = roi.roi_id
        self._refresh_roi_table()

    def latest_workspace(self):
        return self._latest_workspace

    def rois(self) -> tuple[WBRectangleROI, ...]:
        return tuple(self._roi_collection.rois)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Western Blot 结果与灰度分析"))
        root.addWidget(_label(WB_REVIEW_NOTICE, "wbRoiReviewNotice"))
        root.addWidget(_label(ENGINE_NOT_READY_NOTICE, "wbRoiEngineNotice"))
        root.addWidget(self._import_card())
        root.addWidget(self._preprocess_card())
        root.addWidget(self._roi_card())
        root.addWidget(self._measurement_card())
        root.addWidget(self._normalization_card())

    def _import_card(self) -> QFrame:
        frame = _card("wbImageImportSection")
        layout = QGridLayout(frame)
        self._image_path_input = QLineEdit()
        self._image_path_input.setObjectName("wbImagePathInput")
        import_button = QPushButton("导入图片")
        import_button.setObjectName("wbImageImportButton")
        import_button.clicked.connect(self._import_image)
        self._image_info = QLabel("尚未导入图片。支持 TIFF / TIF / PNG / JPG / JPEG；专有格式需先导出为通用图片。")
        self._image_info.setObjectName("wbImageImportInfo")
        layout.addWidget(QLabel("第一步：导入图片"), 0, 0, 1, 2)
        layout.addWidget(self._image_path_input, 1, 0)
        layout.addWidget(import_button, 1, 1)
        layout.addWidget(self._image_info, 2, 0, 1, 2)
        return frame

    def _preprocess_card(self) -> QFrame:
        frame = _card("wbPreprocessSection")
        layout = QHBoxLayout(frame)
        layout.addWidget(QLabel("第二步：预处理设置"))
        self._convert_8bit = QCheckBox("转 8-bit")
        self._convert_8bit.setObjectName("wbConvert8BitCheckbox")
        self._convert_8bit.setChecked(True)
        self._invert_mode = QComboBox()
        self._invert_mode.setObjectName("wbInvertModeCombo")
        self._invert_mode.addItems(("自动判断", "不反转", "反转"))
        self._subtract_background = QCheckBox("背景扣除")
        self._subtract_background.setObjectName("wbSubtractBackgroundCheckbox")
        self._rolling_ball_radius = QSpinBox()
        self._rolling_ball_radius.setObjectName("wbRollingBallRadiusInput")
        self._rolling_ball_radius.setRange(1, 500)
        self._rolling_ball_radius.setValue(50)
        self._analysis_area = QComboBox()
        self._analysis_area.setObjectName("wbAnalysisAreaCombo")
        self._analysis_area.addItems(("整张膜", "指定区域"))
        self._output_format = QComboBox()
        self._output_format.setObjectName("wbOutputFormatCombo")
        self._output_format.addItems(("TIF", "PNG"))
        preprocess = QPushButton("预处理图片")
        preprocess.setObjectName("wbPreprocessButton")
        preprocess.clicked.connect(lambda: self._status.setText(ENGINE_NOT_READY_NOTICE))
        for widget in (self._convert_8bit, self._invert_mode, self._subtract_background, self._rolling_ball_radius, self._analysis_area, self._output_format, preprocess):
            layout.addWidget(widget)
        return frame

    def _roi_card(self) -> QFrame:
        frame = _card("wbRoiEditorSection")
        layout = QGridLayout(frame)
        layout.addWidget(QLabel("第三步：ROI 设置"), 0, 0, 1, 2)
        self._preview = WBROIImagePreview()
        self._preview.roiCreated.connect(self._add_roi_from_preview)
        layout.addWidget(self._preview, 1, 0)
        panel = QGridLayout()
        self._roi_type = QComboBox()
        self._roi_type.setObjectName("wbRoiTypeCombo")
        for key, label in WB_ROI_TYPES.items():
            self._roi_type.addItem(label, key)
        self._roi_label = QLineEdit()
        self._lane_index = QSpinBox()
        self._lane_index.setRange(1, 999)
        self._sample_name = QLineEdit()
        self._roi_x = QSpinBox()
        self._roi_y = QSpinBox()
        self._roi_w = QSpinBox()
        self._roi_h = QSpinBox()
        for spin in (self._roi_x, self._roi_y, self._roi_w, self._roi_h):
            spin.setRange(0, 100000)
        self._background_link = QLineEdit()
        fields = (("ROI 类型", self._roi_type), ("ROI 标签", self._roi_label), ("Lane 编号", self._lane_index), ("样品名", self._sample_name), ("X", self._roi_x), ("Y", self._roi_y), ("宽度", self._roi_w), ("高度", self._roi_h), ("关联背景 ROI", self._background_link))
        for row, (label, widget) in enumerate(fields):
            panel.addWidget(QLabel(label), row, 0)
            panel.addWidget(widget, row, 1)
        layout.addLayout(panel, 1, 1)
        buttons = (("创建 ROI", "wbCreateRoiButton", self._create_roi_from_fields), ("设置为固定 ROI 尺寸", "wbSetFixedRoiSizeButton", self._set_fixed_size), ("复制到下一 Lane", "wbCopyRoiNextLaneButton", self._copy_next_lane), ("复制到全部 Lane", "wbCopyRoiAllLanesButton", self._copy_all_lanes), ("统一 ROI 大小", "wbUnifyRoiSizeButton", self._unify_roi_size), ("删除选中 ROI", "wbDeleteSelectedRoiButton", self._delete_selected_roi), ("清空 ROI", "wbClearRoiButton", self._clear_rois), ("保存 ROI", "wbSaveRoiButton", self._save_rois), ("导出 ROI 坐标", "wbExportRoiButton", self._save_rois), ("测量 ROI", "wbMeasureRoiButton", self._generate_run_request))
        row = QHBoxLayout()
        for label, object_name, callback in buttons:
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row, 2, 0, 1, 2)
        self._fixed_size_label = QLabel("当前固定 ROI 尺寸：未设置")
        self._fixed_size_label.setObjectName("wbFixedRoiSizeLabel")
        layout.addWidget(self._fixed_size_label, 3, 0, 1, 2)
        self._roi_table = QTableWidget(0, 8)
        self._roi_table.setObjectName("wbRoiTable")
        self._roi_table.setHorizontalHeaderLabels(("类型", "标签", "Lane", "Sample", "X", "Y", "W", "ROI ID"))
        layout.addWidget(self._roi_table, 4, 0, 1, 2)
        return frame

    def _measurement_card(self) -> QFrame:
        frame = _card("wbMeasurementResultSection")
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel("第四步：灰度结果"))
        layout.addWidget(QLabel("尚未生成灰度测量结果。请先绘制 ROI 并运行测量。"))
        row = QHBoxLayout()
        self._measurement_path = QLineEdit()
        self._measurement_path.setObjectName("wbMeasurementCsvPathInput")
        load = QPushButton("读取测量结果 CSV")
        load.setObjectName("wbLoadMeasurementCsvButton")
        load.clicked.connect(self._load_measurement_csv)
        row.addWidget(self._measurement_path)
        row.addWidget(load)
        layout.addLayout(row)
        self._measurement_table = QTableWidget(0, 8)
        self._measurement_table.setObjectName("wbMeasurementTable")
        self._measurement_table.setHorizontalHeaderLabels(("Lane", "Sample", "ROI type", "Label", "Area", "Mean", "IntDen", "RawIntDen"))
        layout.addWidget(self._measurement_table)
        return frame

    def _normalization_card(self) -> QFrame:
        frame = _card("wbNormalizationSection")
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel("第五步：归一化计算"))
        row = QHBoxLayout()
        for label, object_name, callback in (("计算目标 / 内参比值", "wbCalculateTargetControlButton", self._calculate_normalization), ("计算目标 / 总蛋白比值", "wbCalculateTargetTotalButton", self._calculate_normalization), ("导出 WB 分析结果", "wbExportNormalizedResultsButton", self._export_normalized)):
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row)
        self._normalization_table = QTableWidget(0, 8)
        self._normalization_table.setObjectName("wbNormalizationTable")
        self._normalization_table.setHorizontalHeaderLabels(("Lane", "Sample", "target density", "control density", "total protein density", "normalized ratio", "relative expression", "error"))
        self._status = QLabel("")
        self._status.setObjectName("wbRoiStatusLabel")
        layout.addWidget(self._normalization_table)
        layout.addWidget(self._status)
        return frame

    def _import_image(self) -> None:
        path = self._image_path_input.text().strip()
        if not path:
            return
        unsupported = unsupported_image_format_message(path)
        if unsupported:
            self._image_info.setText(unsupported)
            return
        self._image_path = path
        self._preview.set_image_path(path)
        self._image_info.setText(f"图片文件名：{Path(path).name}；文件格式：{Path(path).suffix.lower()}；是否可读取：已记录；原始路径：{path}")

    def _add_roi_from_preview(self, x: float, y: float, width: float, height: float) -> None:
        self._roi_x.setValue(round(x))
        self._roi_y.setValue(round(y))
        self._roi_w.setValue(round(width))
        self._roi_h.setValue(round(height))
        self._create_roi_from_fields()

    def _create_roi_from_fields(self) -> None:
        path = self._image_path or self._image_path_input.text().strip()
        if not path:
            self._status.setText("请先导入图片。")
            return
        roi = WBRectangleROI(self._image_id, path, str(self._roi_type.currentData()), self._roi_x.value(), self._roi_y.value(), max(1, self._roi_w.value()), max(1, self._roi_h.value()), label=self._roi_label.text(), lane_index=self._lane_index.value(), sample_name=self._sample_name.text(), linked_background_roi_id=self._background_link.text())
        self._roi_collection.add_roi(roi)
        self._selected_roi_id = roi.roi_id
        self._refresh_roi_table()

    def _set_fixed_size(self) -> None:
        if self._selected_roi_id:
            size = self._roi_collection.set_fixed_size_from_roi(self._selected_roi_id)
            self._fixed_size_label.setText(f"当前固定 ROI 尺寸：{size.width:g} x {size.height:g}")

    def _copy_next_lane(self) -> None:
        if self._selected_roi_id:
            self._selected_roi_id = self._roi_collection.copy_to_next_lane(self._selected_roi_id).roi_id
            self._refresh_roi_table()

    def _copy_all_lanes(self) -> None:
        if self._selected_roi_id:
            self._roi_collection.copy_to_all_lanes(self._selected_roi_id, max(2, self._lane_index.value()))
            self._refresh_roi_table()

    def _unify_roi_size(self) -> None:
        self._roi_collection.unify_size()
        self._refresh_roi_table()

    def _delete_selected_roi(self) -> None:
        self._roi_collection.delete_roi(self._selected_roi_id)
        self._selected_roi_id = ""
        self._refresh_roi_table()

    def _clear_rois(self) -> None:
        self._roi_collection.clear()
        self._selected_roi_id = ""
        self._refresh_roi_table()

    def _save_rois(self) -> None:
        base = self._task_store.root / "manual_wb_rois"
        csv_path = export_wb_roi_csv(tuple(self._roi_collection.rois), base / "wb_rois.csv")
        export_wb_roi_json(tuple(self._roi_collection.rois), base / "wb_rois.json")
        self._status.setText(f"已导出 ROI 坐标：{csv_path}")

    def _generate_run_request(self) -> None:
        if not self._image_path:
            self._import_image()
        self._latest_workspace = create_wb_roi_run_request_workspace(image_path=self._image_path, rois=tuple(self._roi_collection.rois), parameters={"invert_mode": self._invert_mode.currentText()}, task_store=self._task_store)
        self._status.setText(f"RunRequest 已生成：{self._latest_workspace.run_request_path}。{ENGINE_NOT_READY_NOTICE}")

    def _load_measurement_csv(self) -> None:
        self._latest_measurements = read_wb_measurement_csv(self._measurement_path.text())
        self._measurement_table.setRowCount(len(self._latest_measurements))
        for row, measurement in enumerate(self._latest_measurements):
            for column, value in enumerate((measurement.lane_index, measurement.sample_name, measurement.roi_type, measurement.label, measurement.area, measurement.mean_gray_value, measurement.integrated_density, measurement.raw_integrated_density)):
                self._measurement_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _calculate_normalization(self) -> None:
        results = calculate_wb_normalization(self._latest_measurements)
        self._normalization_table.setRowCount(len(results))
        for row, result in enumerate(results):
            for column, value in enumerate((result.lane_index, result.sample_name, result.target_density, result.control_density, result.total_protein_density, result.target_control_ratio, result.target_total_protein_ratio, result.error)):
                self._normalization_table.setItem(row, column, QTableWidgetItem("" if value is None else str(value)))

    def _export_normalized(self) -> None:
        path = self._task_store.root / "manual_wb_rois" / "wb_normalized_results.csv"
        export_wb_normalized_results(calculate_wb_normalization(self._latest_measurements), path)
        self._status.setText(f"已导出 WB 分析结果：{path}")

    def _refresh_roi_table(self) -> None:
        self._roi_table.setRowCount(len(self._roi_collection.rois))
        for row, roi in enumerate(self._roi_collection.rois):
            for column, value in enumerate((WB_ROI_TYPES[roi.roi_type], roi.label, roi.lane_index, roi.sample_name, round(roi.x), round(roi.y), round(roi.width), roi.roi_id)):
                self._roi_table.setItem(row, column, QTableWidgetItem(str(value)))
        self._preview.set_rois(tuple(self._roi_collection.rois))


def _card(object_name: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName(object_name)
    return frame


def _label(text: str, object_name: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName(object_name)
    label.setWordWrap(True)
    return label
