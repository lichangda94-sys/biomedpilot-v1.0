from __future__ import annotations

import re

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.western_blot import (
        BCA_COLUMNS,
        BCA_REVIEW_NOTICE,
        BCA_ROWS,
        BCA_WELL_TYPES,
        DEFAULT_OVERAGE_PERCENT,
        DEFAULT_LOADING_OVERAGE_PERCENT,
        GEL_REVIEW_NOTICE,
        GEL_TEMPLATE_CONTEXT_NOTICE,
        PROTEIN_LOADING_REVIEW_NOTICE,
        REDUCING_AGENT_NOTICE,
        SUPPORTED_GEL_COMPONENT_UNITS,
        SUPPORTED_PROTEIN_CONCENTRATION_UNITS,
        BcaAnalysisResult,
        BcaAssayError,
        BcaPlateMatrix,
        BcaWellAnnotation,
        GelComponent,
        GelSection,
        ProteinLoadingError,
        ProteinLoadingResult,
        ProteinLoadingSampleInput,
        ProteinLoadingSettings,
        SdsPageGelCalculationInput,
        SdsPageGelCalculationResult,
        SdsPageGelTemplate,
        SdsPageGelTemplateError,
        SdsPageGelTemplateStore,
        WB_RECORD_STEP_FIELDS,
        WB_REVIEW_NOTICE,
        WB_WORKFLOW_STEPS,
        WBWorkflowRecord,
        WBWorkflowRecordError,
        WBWorkflowRecordStore,
        annotate_well,
        analyze_bca_assay,
        annotate_well_range,
        calculate_protein_loading,
        calculate_sds_page_gel_batch,
        load_sds_page_gel_template_json,
        parse_bca_od_matrix,
        save_sds_page_gel_calculation_xlsx,
        save_sds_page_gel_template_json,
    )
    from app.labtools.western_blot.widgets import WesternBlotLoadingCalculatorWidget
    from app.shared.local_engines import ImageJFijiBridge
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:
    SECTION_STATUS = "待确认使用逻辑 / 规划中 / 暂未开放"

    def _line_edit(placeholder: str, text: str = "") -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setText(text)
        field.setMinimumHeight(CONTROL_HEIGHT["field"])
        return field


    def _combo(values: tuple[str, ...], current: str | None = None) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        if current in values:
            combo.setCurrentText(current)
        combo.setMinimumHeight(CONTROL_HEIGHT["field"])
        return combo


    class LabToolsWesternBlotWidget(QWidget):
        def __init__(self, *, imagej_bridge: ImageJFijiBridge | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsWesternBlotWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._imagej_bridge = imagej_bridge
            self._template_store = SdsPageGelTemplateStore()
            self._workflow_record_store = WBWorkflowRecordStore()
            self._current_template: SdsPageGelTemplate | None = None
            self._current_result: SdsPageGelCalculationResult | None = None
            self._current_loading_result: ProteinLoadingResult | None = None
            self._current_bca_result: BcaAnalysisResult | None = None
            self._bca_annotations: dict[str, BcaWellAnnotation] = {}
            self._bca_selected_wells: set[str] = set()
            self._record_forms: dict[str, dict[str, object]] = {}
            self._loading_widget = WesternBlotLoadingCalculatorWidget()
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setObjectName("labToolsWesternBlotScroll")
            content = QWidget()
            content.setObjectName("labToolsWesternBlotContent")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["lg"])

            title = QLabel("Western Blot")
            title.setObjectName("labToolsWesternBlotTitle")
            description = QLabel("用于蛋白样品准备、蛋白浓度测定入口、Western Blot 上样体系、SDS-PAGE 配胶、电泳/转膜参数和抗体孵育流程记录。")
            description.setObjectName("labToolsWesternBlotDescription")
            description.setWordWrap(True)
            notice = QLabel(f"{GEL_TEMPLATE_CONTEXT_NOTICE}。{WB_REVIEW_NOTICE}")
            notice.setObjectName("labToolsWesternBlotBoundary")
            notice.setWordWrap(True)
            l4_status = QLabel(
                "Western Blot 流程工作台：available / 可用\n"
                "结果与灰度分析：placeholder / 未启用\n"
                "当前不启用 WB 图像分析、条带识别、灰度定量、自动 ROI 或结果解释。"
            )
            l4_status.setObjectName("labToolsWesternBlotL4Status")
            l4_status.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(description)
            layout.addWidget(notice)
            layout.addWidget(l4_status)

            self._tabs = QTabWidget()
            self._tabs.setObjectName("westernBlotTabs")
            self._tabs.addTab(self._build_sections_tab(), "流程工作台")
            self._tabs.addTab(self._build_workflow_record_tab("sample_preparation"), "蛋白样品准备")
            self._tabs.addTab(self._build_bca_assay_tab(), "BCA 蛋白浓度测定")
            self._tabs.addTab(self._build_protein_loading_tab(), "蛋白上样计算")
            self._tabs.addTab(self._build_sds_page_tool_tab(), "配胶与 Lane 布局")
            for step_id, step_label in WB_WORKFLOW_STEPS:
                if step_id in {"sample_preparation", "bca_assay", "protein_loading", "gel_lane_layout", "result_analysis"}:
                    continue
                self._tabs.addTab(self._build_workflow_record_tab(step_id), step_label)
            self._tabs.addTab(self._build_result_placeholder_tab(), "结果与灰度分析")
            layout.addWidget(self._tabs, 1)

            scroll.setWidget(content)
            root.addWidget(scroll)

        def _build_sections_tab(self) -> QWidget:
            tab = QWidget()
            layout = QGridLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])
            descriptions = {
                "sample_preparation": "记录样品来源、裂解、分组、保存条件和实验室 SOP 文字。",
                "bca_assay": "保留 96 孔板 OD 矩阵粘贴、Blank/Standard/Sample/Unused 标注和标准曲线草稿计算。",
                "protein_loading": "按目标蛋白量、样品浓度和横向 lane layout 分阶段生成上样计算结果。",
                "gel_lane_layout": "维护 Lane / Stacking gel / Resolving gel 三层结构，可导入上样结果中的 lane。",
                "electrophoresis": "记录电泳 buffer、电压、时间和异常情况。",
                "transfer": "记录膜、transfer buffer、转膜方式、电压/电流/时间和异常情况。",
                "blocking": "记录 blocking buffer、体积、时间、温度和备注。",
                "primary_antibody": "记录一抗名称、厂家、货号、lot、稀释比例和孵育条件。",
                "primary_wash": "记录一抗后洗膜 buffer、Tween、时间、次数和体积。",
                "secondary_antibody": "记录二抗名称、识别对象、标记类型、厂家、货号和孵育条件。",
                "secondary_wash": "记录二抗后洗膜 buffer、Tween、时间、次数和体积。",
                "imaging": "记录显影方式、试剂、设备、曝光时间、通道和图像文件路径。",
                "result_analysis": "仅保留结果与灰度分析占位；后续单独讨论，不启用自动条带识别、自动 ROI、灰度定量。",
            }
            for index, (step_id, step_label) in enumerate(WB_WORKFLOW_STEPS):
                card = self._section_card(step_id, step_label, descriptions[step_id])
                layout.addWidget(card, index // 2, index % 2)
            return tab

        def _build_protein_loading_tab(self) -> QWidget:
            return self._loading_widget

        def _build_bca_assay_tab(self) -> QWidget:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])

            intro = QLabel("BCA 蛋白浓度测定")
            intro.setObjectName("labToolsWesternBlotSectionTitle")
            boundary = QLabel(BCA_REVIEW_NOTICE)
            boundary.setObjectName("labToolsWesternBlotDescription")
            boundary.setWordWrap(True)
            layout.addWidget(intro)
            layout.addWidget(boundary)

            plate_card = self._card()
            plate_layout = QGridLayout(plate_card)
            plate_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._bca_plate_table = QTableWidget(8, 12)
            self._bca_plate_table.setObjectName("bcaPlateTable")
            self._bca_plate_table.setHorizontalHeaderLabels([str(column) for column in BCA_COLUMNS])
            self._bca_plate_table.setVerticalHeaderLabels(list(BCA_ROWS))
            self._bca_plate_table.setMinimumHeight(240)
            self._bca_plate_table.cellClicked.connect(self._handle_bca_well_clicked)
            self._bca_matrix_paste = QTextEdit()
            self._bca_matrix_paste.setObjectName("bcaOdMatrixPasteArea")
            self._bca_matrix_paste.setPlaceholderText("粘贴 8×12 OD 矩阵，支持 Excel/tab 格式、A-H 行名和 1-12 列号。")
            self._bca_matrix_paste.setMinimumHeight(110)
            parse_button = QPushButton("解析 OD 矩阵")
            parse_button.setObjectName("bcaParseOdMatrixButton")
            parse_button.clicked.connect(self._handle_bca_parse_matrix)
            plate_layout.addWidget(QLabel("96 孔板 OD 数据"), 0, 0)
            plate_layout.addWidget(self._bca_plate_table, 1, 0)
            plate_layout.addWidget(QLabel("粘贴 OD 矩阵"), 0, 1)
            plate_layout.addWidget(self._bca_matrix_paste, 1, 1)
            plate_layout.addWidget(parse_button, 2, 1, alignment=Qt.AlignLeft)
            layout.addWidget(plate_card)

            annotation_card = self._card()
            annotation_layout = QGridLayout(annotation_card)
            annotation_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._bca_annotation_type = _combo(BCA_WELL_TYPES, "Standard")
            self._bca_annotation_type.setObjectName("bcaWellTypeCombo")
            self._bca_range_start = _line_edit("起始孔位", "A1")
            self._bca_range_start.setObjectName("bcaBatchStartWellField")
            self._bca_range_end = _line_edit("结束孔位", "A1")
            self._bca_range_end.setObjectName("bcaBatchEndWellField")
            self._bca_annotation_name = _line_edit("标准品/样本名称")
            self._bca_annotation_name.setObjectName("bcaAnnotationNameField")
            self._bca_standard_concentration = _line_edit("标准浓度")
            self._bca_standard_concentration.setObjectName("bcaStandardConcentrationField")
            self._bca_concentration_unit = _combo(("µg/mL", "mg/mL"), "µg/mL")
            self._bca_concentration_unit.setObjectName("bcaConcentrationUnitCombo")
            self._bca_dilution_factor = _line_edit("稀释倍数", "1")
            self._bca_dilution_factor.setObjectName("bcaDilutionFactorField")
            self._bca_annotation_note = _line_edit("备注")
            self._bca_annotation_note.setObjectName("bcaAnnotationNoteField")
            self._bca_blank_subtraction = QCheckBox("启用 blank 扣除")
            self._bca_blank_subtraction.setObjectName("bcaBlankSubtractionCheckbox")
            apply_button = QPushButton("批量标注选区")
            apply_button.setObjectName("bcaApplyBatchAnnotationButton")
            apply_button.clicked.connect(self._handle_bca_apply_annotation)
            self._bca_selected_well_label = QLabel("当前孔位：未选择")
            self._bca_selected_well_label.setObjectName("bcaSelectedWellLabel")
            apply_selected_button = QPushButton("标注当前孔位")
            apply_selected_button.setObjectName("bcaApplySelectedAnnotationButton")
            apply_selected_button.clicked.connect(lambda: self._handle_bca_apply_selected_annotation())
            blank_button = QPushButton("Blank")
            blank_button.setObjectName("bcaSetBlankButton")
            blank_button.clicked.connect(lambda: self._handle_bca_apply_selected_annotation("Blank"))
            standard_button = QPushButton("Standard")
            standard_button.setObjectName("bcaSetStandardButton")
            standard_button.clicked.connect(lambda: self._handle_bca_apply_selected_annotation("Standard"))
            sample_button = QPushButton("Sample")
            sample_button.setObjectName("bcaSetSampleButton")
            sample_button.clicked.connect(lambda: self._handle_bca_apply_selected_annotation("Sample"))
            unused_button = QPushButton("Unused")
            unused_button.setObjectName("bcaSetUnusedButton")
            unused_button.clicked.connect(lambda: self._handle_bca_apply_selected_annotation("Unused"))
            fields = (
                ("孔类型", self._bca_annotation_type),
                ("起始孔位", self._bca_range_start),
                ("结束孔位", self._bca_range_end),
                ("名称", self._bca_annotation_name),
                ("标准浓度", self._bca_standard_concentration),
                ("浓度单位", self._bca_concentration_unit),
                ("稀释倍数", self._bca_dilution_factor),
                ("备注", self._bca_annotation_note),
            )
            for index, (label, widget) in enumerate(fields):
                annotation_layout.addWidget(QLabel(label), index // 4 * 2, index % 4)
                annotation_layout.addWidget(widget, index // 4 * 2 + 1, index % 4)
            annotation_layout.addWidget(self._bca_blank_subtraction, 4, 0, 1, 2)
            annotation_layout.addWidget(apply_button, 4, 2, alignment=Qt.AlignLeft)
            annotation_layout.addWidget(self._bca_selected_well_label, 5, 0, 1, 2)
            annotation_layout.addWidget(apply_selected_button, 5, 2, alignment=Qt.AlignLeft)
            quick_row = QHBoxLayout()
            for button in (blank_button, standard_button, sample_button, unused_button):
                quick_row.addWidget(button)
            quick_row.addStretch(1)
            annotation_layout.addLayout(quick_row, 6, 0, 1, 4)
            layout.addWidget(annotation_card)

            action = self._card()
            action_layout = QHBoxLayout(action)
            action_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._bca_calculate_button = QPushButton("计算 BCA 结果")
            self._bca_calculate_button.setObjectName("bcaCalculateButton")
            self._bca_calculate_button.clicked.connect(self._handle_bca_calculate)
            self._bca_copy_button = QPushButton("复制结果")
            self._bca_copy_button.setObjectName("bcaCopyResultButton")
            self._bca_copy_button.setEnabled(False)
            self._bca_copy_button.clicked.connect(self._copy_bca_result)
            action_layout.addWidget(self._bca_calculate_button)
            action_layout.addWidget(self._bca_copy_button)
            action_layout.addStretch(1)
            layout.addWidget(action)

            result_grid = QGridLayout()
            self._bca_raw_result = QTextEdit()
            self._bca_raw_result.setObjectName("bcaRawDataPanel")
            self._bca_standard_result = QTextEdit()
            self._bca_standard_result.setObjectName("bcaStandardCurvePanel")
            self._bca_sample_result = QTextEdit()
            self._bca_sample_result.setObjectName("bcaSampleResultsPanel")
            for panel in (self._bca_raw_result, self._bca_standard_result, self._bca_sample_result):
                panel.setReadOnly(True)
                panel.setMinimumHeight(150)
                panel.setText("尚未计算。")
            result_grid.addWidget(QLabel("Plate Raw Data"), 0, 0)
            result_grid.addWidget(QLabel("Standard Curve"), 0, 1)
            result_grid.addWidget(QLabel("Sample Results"), 0, 2)
            result_grid.addWidget(self._bca_raw_result, 1, 0)
            result_grid.addWidget(self._bca_standard_result, 1, 1)
            result_grid.addWidget(self._bca_sample_result, 1, 2)
            layout.addLayout(result_grid, 1)
            return tab

        def _build_sds_page_tool_tab(self) -> QWidget:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])

            intro = QLabel("配胶与 Lane 布局")
            intro.setObjectName("labToolsWesternBlotSectionTitle")
            boundary = QLabel(
                "基于用户录入的试剂盒/实验室模板进行批量换算；包含 Lane / Stacking gel / Resolving gel 三层结构，不内置通用配方、不进行自动配方推荐、不自动推导胶浓度、不生成配置步骤。"
            )
            boundary.setObjectName("labToolsWesternBlotDescription")
            boundary.setWordWrap(True)
            layout.addWidget(intro)
            layout.addWidget(boundary)
            layout.addWidget(self._build_template_card())
            layout.addWidget(self._build_lane_layout_card())
            layout.addWidget(self._build_section_input_card("分离胶", "resolving"))
            layout.addWidget(self._build_section_input_card("浓缩胶", "stacking"))
            layout.addWidget(self._build_action_card())
            self._sds_page_result = QTextEdit()
            self._sds_page_result.setObjectName("sdsPageGelResultPanel")
            self._sds_page_result.setReadOnly(True)
            self._sds_page_result.setMinimumHeight(180)
            self._sds_page_result.setText("尚未计算。填写用户模板后可计算批量用量；未计算前 XLSX 导出不可用。")
            layout.addWidget(self._sds_page_result, 1)
            return tab

        def _build_template_card(self) -> QFrame:
            frame = self._card()
            layout = QGridLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._template_name = _line_edit("模板名称")
            self._template_name.setObjectName("sdsPageTemplateNameField")
            self._template_version = _line_edit("模板版本", "v1")
            self._gel_concentration = _line_edit("胶浓度，例如用户录入 10%")
            self._gel_concentration.setObjectName("sdsPageGelConcentrationField")
            self._gel_thickness = _combo(("0.75 mm", "1.0 mm", "1.5 mm"), "1.0 mm")
            self._gel_thickness.setObjectName("sdsPageGelThicknessCombo")
            self._well_count = _combo(("10 wells", "12 wells", "15 wells"), "10 wells")
            self._well_count.setObjectName("sdsPageWellCountCombo")
            self._gel_format_note = _line_edit("胶板规格或备注")
            self._kit_source = _line_edit("试剂盒说明书或实验室模板来源")
            self._gel_count = _line_edit("胶数量", "1")
            self._gel_count.setObjectName("sdsPageGelCountField")
            self._overage_percent = _line_edit("余量百分比", str(int(DEFAULT_OVERAGE_PERCENT)))
            self._overage_percent.setObjectName("sdsPageOveragePercentField")

            fields = (
                ("模板名称", self._template_name),
                ("模板版本", self._template_version),
                ("胶浓度", self._gel_concentration),
                ("胶厚度", self._gel_thickness),
                ("孔数", self._well_count),
                ("胶板规格 / 备注", self._gel_format_note),
                ("模板来源", self._kit_source),
                ("胶数量", self._gel_count),
                ("余量百分比", self._overage_percent),
            )
            for index, (label, widget) in enumerate(fields):
                layout.addWidget(QLabel(label), index // 3 * 2, index % 3)
                layout.addWidget(widget, index // 3 * 2 + 1, index % 3)
            self._well_count.currentTextChanged.connect(lambda _text: self._refresh_lane_layout(blank=True))
            return frame

        def _build_lane_layout_card(self) -> QFrame:
            frame = self._card()
            frame.setObjectName("sdsPageLaneLayoutCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            heading = QLabel("Lane / 上样孔布局")
            heading.setObjectName("labToolsWesternBlotSectionTitle")
            layers = QLabel("三层结构：Lane / 上样孔布局；Stacking gel；Resolving gel")
            layers.setObjectName("labToolsWesternBlotDescription")
            layers.setWordWrap(True)
            self._lane_layout_table = QTableWidget(0, 3)
            self._lane_layout_table.setObjectName("gelLaneLayoutTable")
            self._lane_layout_table.setHorizontalHeaderLabels(("Lane 编号", "样品名", "总上样体积"))
            self._lane_layout_table.setMinimumHeight(150)
            button_row = QHBoxLayout()
            blank_button = QPushButton("生成空白 Lane 布局")
            blank_button.setObjectName("refreshBlankLaneLayoutButton")
            blank_button.clicked.connect(lambda: self._refresh_lane_layout(blank=True))
            import_button = QPushButton("从上样计算导入 Lane")
            import_button.setObjectName("importLoadingLaneLayoutButton")
            import_button.clicked.connect(self._import_loading_lane_layout)
            button_row.addWidget(blank_button)
            button_row.addWidget(import_button)
            button_row.addStretch(1)
            layout.addWidget(heading)
            layout.addWidget(layers)
            layout.addWidget(self._lane_layout_table)
            layout.addLayout(button_row)
            self._refresh_lane_layout(blank=True)
            return frame

        def _build_section_input_card(self, title: str, prefix: str) -> QFrame:
            frame = self._card()
            frame.setObjectName(f"sdsPage{prefix.title()}SectionCard")
            layout = QGridLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel(title)
            heading.setObjectName("labToolsWesternBlotSectionTitle")
            use_box = QCheckBox("使用该 section")
            use_box.setObjectName(f"sdsPage{prefix.title()}UseCheckbox")
            use_box.setChecked(True)
            component_name = _line_edit("组分名称")
            component_name.setObjectName(f"sdsPage{prefix.title()}ComponentNameField")
            amount = _line_edit("每块胶用量")
            amount.setObjectName(f"sdsPage{prefix.title()}AmountField")
            unit = _combo(SUPPORTED_GEL_COMPONENT_UNITS, "mL")
            unit.setObjectName(f"sdsPage{prefix.title()}UnitCombo")
            note = _line_edit("备注/提示：位置、过期、最后加入等")
            note.setObjectName(f"sdsPage{prefix.title()}ComponentNoteField")
            setattr(self, f"_{prefix}_use", use_box)
            setattr(self, f"_{prefix}_component_name", component_name)
            setattr(self, f"_{prefix}_amount", amount)
            setattr(self, f"_{prefix}_unit", unit)
            setattr(self, f"_{prefix}_note", note)

            layout.addWidget(heading, 0, 0, 1, 4)
            layout.addWidget(use_box, 1, 0, 1, 4)
            layout.addWidget(QLabel("组分名称"), 2, 0)
            layout.addWidget(QLabel("每块胶用量"), 2, 1)
            layout.addWidget(QLabel("单位"), 2, 2)
            layout.addWidget(QLabel("备注/提示"), 2, 3)
            layout.addWidget(component_name, 3, 0)
            layout.addWidget(amount, 3, 1)
            layout.addWidget(unit, 3, 2)
            layout.addWidget(note, 3, 3)
            return frame

        def _build_action_card(self) -> QFrame:
            frame = self._card()
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            row = QHBoxLayout()
            self._calculate_button = QPushButton("计算批量用量")
            self._calculate_button.setObjectName("primaryButton")
            self._calculate_button.clicked.connect(self._handle_calculate)
            self._save_template_button = QPushButton("导出模板 JSON")
            self._save_template_button.setObjectName("sdsPageTemplateJsonExportButton")
            self._save_template_button.setEnabled(False)
            self._save_template_button.clicked.connect(self._handle_save_template_json)
            self._load_template_button = QPushButton("导入模板 JSON")
            self._load_template_button.setObjectName("sdsPageTemplateJsonImportButton")
            self._load_template_button.clicked.connect(self._handle_load_template_json)
            self._import_conflict_policy = _combo(("跳过", "作为副本导入"), "跳过")
            self._import_conflict_policy.setObjectName("sdsPageImportConflictPolicyCombo")
            self._xlsx_export_button = QPushButton("导出本次计算 XLSX")
            self._xlsx_export_button.setObjectName("sdsPageXlsxExportButton")
            self._xlsx_export_button.setEnabled(False)
            self._xlsx_export_button.clicked.connect(self._handle_export_xlsx)
            for widget in (
                self._calculate_button,
                self._save_template_button,
                self._load_template_button,
                self._import_conflict_policy,
                self._xlsx_export_button,
            ):
                row.addWidget(widget)
            row.addStretch(1)
            layout.addLayout(row)
            return frame

        def _section_card(self, step_id: str, title: str, description: str) -> QFrame:
            frame = self._card()
            frame.setObjectName("labToolsWesternBlotSectionCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            status = QLabel(SECTION_STATUS)
            status.setObjectName("labToolsWesternBlotSectionStatus")
            section_title = QLabel(title)
            section_title.setObjectName("labToolsWesternBlotSectionTitle")
            section_description = QLabel(description)
            section_description.setObjectName("labToolsWesternBlotSectionDescription")
            section_description.setWordWrap(True)
            layout.addWidget(status)
            layout.addWidget(section_title)
            layout.addWidget(section_description)
            if step_id == "result_analysis":
                planned_label = QLabel("placeholder / 未启用：不启用自动条带识别、自动 ROI、灰度定量或结果解释。")
                planned_label.setObjectName("labToolsWesternBlotPlannedEntries")
                planned_label.setWordWrap(True)
                layout.addWidget(planned_label)
            button = QPushButton(f"进入 {title}")
            button.setObjectName(f"wbWorkflowStepButton_{step_id}")
            button.clicked.connect(lambda _checked=False, label=title: self._tabs.setCurrentIndex(self._tab_index_by_label(label)))
            layout.addWidget(button, alignment=Qt.AlignLeft)
            if step_id == "bca_assay":
                button.setObjectName("openBcaAssayToolButton")
            elif step_id == "protein_loading":
                button.setObjectName("openProteinLoadingToolButton")
            elif step_id == "gel_lane_layout":
                button.setObjectName("openSdsPageGelToolButton")
            layout.addStretch(1)
            return frame

        def _tab_index_by_label(self, label: str) -> int:
            for index in range(self._tabs.count()):
                if self._tabs.tabText(index) == label:
                    return index
            return 0

        def _build_workflow_record_tab(self, step_id: str) -> QWidget:
            label = dict(WB_WORKFLOW_STEPS)[step_id]
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])

            intro = QLabel(label)
            intro.setObjectName("labToolsWesternBlotSectionTitle")
            notice = QLabel(f"{WB_REVIEW_NOTICE} 本页保存结构化字段、SOP 文本和自由文本实验记录。")
            notice.setObjectName("labToolsWesternBlotDescription")
            notice.setWordWrap(True)
            layout.addWidget(intro)
            layout.addWidget(notice)

            form_card = self._card()
            form_layout = QGridLayout(form_card)
            form_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            field_widgets: dict[str, QLineEdit] = {}
            fields = WB_RECORD_STEP_FIELDS.get(step_id, ("实验日期", "操作者", "项目", "备注"))
            for index, field_name in enumerate(fields):
                widget = _line_edit(field_name)
                widget.setObjectName(f"wbRecordField_{step_id}_{index}")
                field_widgets[field_name] = widget
                form_layout.addWidget(QLabel(field_name), index // 3 * 2, index % 3)
                form_layout.addWidget(widget, index // 3 * 2 + 1, index % 3)
            layout.addWidget(form_card)

            text_card = self._card()
            text_layout = QGridLayout(text_card)
            text_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            sop_text = QTextEdit()
            sop_text.setObjectName(f"wbRecordSopText_{step_id}")
            sop_text.setPlaceholderText("粘贴或记录实验室 SOP / 试剂盒说明书摘要。")
            free_text = QTextEdit()
            free_text.setObjectName(f"wbRecordFreeText_{step_id}")
            free_text.setPlaceholderText("记录本次实验实际观察、偏差、异常和人工复核点。")
            for panel in (sop_text, free_text):
                panel.setMinimumHeight(120)
            text_layout.addWidget(QLabel("SOP 文本 / 模板"), 0, 0)
            text_layout.addWidget(QLabel("自由文本实验记录"), 0, 1)
            text_layout.addWidget(sop_text, 1, 0)
            text_layout.addWidget(free_text, 1, 1)
            layout.addWidget(text_card)

            action_card = self._card()
            action_layout = QHBoxLayout(action_card)
            action_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            save_button = QPushButton("保存当前记录")
            save_button.setObjectName(f"wbRecordSaveButton_{step_id}")
            save_button.clicked.connect(lambda _checked=False, sid=step_id: self._save_workflow_record(sid))
            save_template_button = QPushButton("保存 SOP 模板")
            save_template_button.setObjectName(f"wbRecordSaveSopTemplateButton_{step_id}")
            save_template_button.clicked.connect(lambda _checked=False, sid=step_id: self._save_workflow_record(sid))
            load_button = QPushButton("载入上次记录")
            load_button.setObjectName(f"wbRecordLoadLastButton_{step_id}")
            load_button.clicked.connect(lambda _checked=False, sid=step_id: self._load_latest_workflow_record(sid))
            export_button = QPushButton("导出文本")
            export_button.setObjectName(f"wbRecordExportTextButton_{step_id}")
            export_button.clicked.connect(lambda _checked=False, sid=step_id: self._export_workflow_record_text(sid))
            status = QLabel("尚未保存。")
            status.setObjectName(f"wbRecordStatus_{step_id}")
            status.setWordWrap(True)
            for widget in (save_button, save_template_button, load_button, export_button):
                action_layout.addWidget(widget)
            action_layout.addStretch(1)
            layout.addWidget(action_card)
            layout.addWidget(status)
            layout.addStretch(1)

            self._record_forms[step_id] = {
                "label": label,
                "fields": field_widgets,
                "sop": sop_text,
                "free": free_text,
                "status": status,
            }
            return tab

        def _build_result_placeholder_tab(self) -> QWidget:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])
            title = QLabel("结果与灰度分析")
            title.setObjectName("labToolsWesternBlotSectionTitle")
            body = QLabel(
                "本页仅保留占位，用于后续单独讨论 WB/gel grayscale、条带 ROI、背景扣除和结果导出。当前不启用自动条带识别、自动 ROI、灰度定量或结果解释。"
            )
            body.setObjectName("labToolsWesternBlotBoundary")
            body.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(body)
            layout.addStretch(1)
            return tab

        def _add_loading_sample_row(self) -> None:
            row = self._loading_sample_table.rowCount()
            self._loading_sample_table.insertRow(row)
            self._loading_sample_table.setItem(row, 0, QTableWidgetItem(f"Sample {row + 1}"))
            self._loading_sample_table.setItem(row, 1, QTableWidgetItem(""))
            self._loading_sample_table.setCellWidget(row, 2, _combo(SUPPORTED_PROTEIN_CONCENTRATION_UNITS, "µg/µL"))

        def _handle_loading_calculate(self) -> None:
            try:
                result = calculate_protein_loading(self._loading_samples_from_table(), self._loading_settings_from_form())
            except (ProteinLoadingError, ValueError) as exc:
                self._current_loading_result = None
                self._loading_copy_button.setEnabled(False)
                self._loading_result.setText(str(exc))
                return
            self._current_loading_result = result
            self._loading_copy_button.setEnabled(True)
            self._loading_result.setText(result.copy_text())

        def _loading_samples_from_table(self) -> tuple[ProteinLoadingSampleInput, ...]:
            samples: list[ProteinLoadingSampleInput] = []
            for row in range(self._loading_sample_table.rowCount()):
                name_item = self._loading_sample_table.item(row, 0)
                concentration_item = self._loading_sample_table.item(row, 1)
                concentration_text = concentration_item.text().strip() if concentration_item is not None else ""
                if not concentration_text:
                    continue
                unit_widget = self._loading_sample_table.cellWidget(row, 2)
                unit = unit_widget.currentText() if isinstance(unit_widget, QComboBox) else "µg/µL"
                samples.append(
                    ProteinLoadingSampleInput(
                        sample_name=name_item.text().strip() if name_item is not None else "",
                        protein_concentration=float(concentration_text),
                        concentration_unit=unit,
                    )
                )
            return tuple(samples)

        def _loading_settings_from_form(self) -> ProteinLoadingSettings:
            return ProteinLoadingSettings(
                target_protein_ug=float(self._loading_target_protein.text()),
                final_loading_volume_ul=float(self._loading_final_volume.text()),
                loading_buffer_multiple=float(self._loading_buffer_multiple.text()),
                loading_buffer_target_concentration=float(self._loading_buffer_target.text()),
                overage_percent=float(self._loading_overage.text()),
            )

        def _copy_loading_result(self) -> None:
            if self._current_loading_result is not None:
                QApplication.clipboard().setText(self._current_loading_result.copy_text())

        def _handle_bca_well_clicked(self, row: int, column: int) -> None:
            well = f"{BCA_ROWS[row]}{BCA_COLUMNS[column]}"
            if well in self._bca_selected_wells:
                self._bca_selected_wells.remove(well)
            else:
                self._bca_selected_wells.add(well)
            self._refresh_bca_selected_label()

        def _refresh_bca_selected_label(self) -> None:
            wells = ", ".join(sorted(self._bca_selected_wells, key=self._well_sort_key))
            self._bca_selected_well_label.setText(f"当前孔位：{wells or '未选择'}")

        def _well_sort_key(self, well: str) -> tuple[int, int]:
            row = BCA_ROWS.index(well[0]) if well and well[0] in BCA_ROWS else 999
            try:
                column = int(well[1:])
            except ValueError:
                column = 999
            return row, column

        def _handle_bca_apply_selected_annotation(self, well_type: str | None = None) -> None:
            selected_wells = set(self._bca_selected_wells)
            if not selected_wells:
                current = self._bca_plate_table.currentIndex()
                if current.isValid():
                    selected_wells.add(f"{BCA_ROWS[current.row()]}{BCA_COLUMNS[current.column()]}")
            if not selected_wells:
                self._bca_raw_result.setText("请先点击 96 孔板中的孔位。")
                return
            try:
                standard_text = self._bca_standard_concentration.text().strip()
                standard_concentration = float(standard_text) if standard_text else None
                target_type = well_type or self._bca_annotation_type.currentText()
                for well in selected_wells:
                    self._bca_annotations = annotate_well(
                        self._bca_annotations,
                        well,
                        target_type,
                        name=self._bca_annotation_name.text().strip(),
                        standard_concentration=standard_concentration,
                        concentration_unit=self._bca_concentration_unit.currentText(),
                        dilution_factor=float(self._bca_dilution_factor.text()),
                        note=self._bca_annotation_note.text().strip(),
                    )
            except (BcaAssayError, ValueError) as exc:
                self._bca_raw_result.setText(str(exc))
                return
            self._bca_annotation_type.setCurrentText(well_type or self._bca_annotation_type.currentText())
            wells = ", ".join(sorted(selected_wells, key=self._well_sort_key))
            self._bca_raw_result.setText(f"已标注孔位：{wells}")

        def _handle_bca_parse_matrix(self) -> None:
            try:
                plate = parse_bca_od_matrix(self._bca_matrix_paste.toPlainText())
            except BcaAssayError as exc:
                self._bca_raw_result.setText(str(exc))
                return
            for row_index, row_name in enumerate(BCA_ROWS):
                for col_index, col_number in enumerate(BCA_COLUMNS):
                    value = plate.value(f"{row_name}{col_number}")
                    self._bca_plate_table.setItem(row_index, col_index, QTableWidgetItem("" if value is None else f"{value:g}"))
            self._bca_raw_result.setText("OD 矩阵已解析。\n" + "\n".join(plate.warnings))

        def _handle_bca_apply_annotation(self) -> None:
            try:
                standard_text = self._bca_standard_concentration.text().strip()
                standard_concentration = float(standard_text) if standard_text else None
                self._bca_annotations = annotate_well_range(
                    self._bca_annotations,
                    self._bca_range_start.text(),
                    self._bca_range_end.text(),
                    self._bca_annotation_type.currentText(),
                    name=self._bca_annotation_name.text().strip(),
                    standard_concentration=standard_concentration,
                    concentration_unit=self._bca_concentration_unit.currentText(),
                    dilution_factor=float(self._bca_dilution_factor.text()),
                    note=self._bca_annotation_note.text().strip(),
                )
            except (BcaAssayError, ValueError) as exc:
                self._bca_raw_result.setText(str(exc))
                return
            self._bca_raw_result.setText(f"已批量标注选区：{self._bca_range_start.text()} - {self._bca_range_end.text()}")

        def _handle_bca_calculate(self) -> None:
            try:
                plate = self._bca_plate_from_table()
                result = analyze_bca_assay(plate, self._bca_annotations, blank_subtraction_enabled=self._bca_blank_subtraction.isChecked())
            except (BcaAssayError, ValueError) as exc:
                self._current_bca_result = None
                self._bca_copy_button.setEnabled(False)
                self._bca_raw_result.setText(str(exc))
                return
            self._current_bca_result = result
            self._bca_copy_button.setEnabled(True)
            self._bca_raw_result.setText(self._bca_raw_text(result))
            self._bca_standard_result.setText(self._bca_standard_text(result))
            self._bca_sample_result.setText(self._bca_sample_text(result))

        def _bca_plate_from_table(self) -> BcaPlateMatrix:
            values: dict[str, float | None] = {}
            warnings: list[str] = []
            for row_index, row_name in enumerate(BCA_ROWS):
                for col_index, col_number in enumerate(BCA_COLUMNS):
                    well = f"{row_name}{col_number}"
                    item = self._bca_plate_table.item(row_index, col_index)
                    text = item.text().strip() if item is not None else ""
                    if not text:
                        values[well] = None
                        continue
                    try:
                        values[well] = float(text)
                    except ValueError:
                        values[well] = None
                        warnings.append(f"{well}: 缺失值或非数值，需人工核对")
            return BcaPlateMatrix(values=values, warnings=tuple(warnings))

        def _copy_bca_result(self) -> None:
            if self._current_bca_result is not None:
                QApplication.clipboard().setText(self._current_bca_result.copy_text())

        def _bca_raw_text(self, result: BcaAnalysisResult) -> str:
            lines = ["Plate Raw Data", f"Blank 扣除：{'启用' if result.blank_subtraction_enabled else '未启用'}"]
            for row in result.raw_data:
                if row.well_type != "Unused" or row.raw_od is not None:
                    lines.append(
                        f"{row.well}\t{row.well_type}\t{row.name}\t原始 OD {row.raw_od}\tblank 扣除后 {row.blank_corrected_od}\t参与计算 {row.include_in_calculation}\t{'; '.join(row.warnings)}"
                    )
            lines.append("\n警告：")
            lines.extend(result.warnings)
            return "\n".join(lines)

        def _bca_standard_text(self, result: BcaAnalysisResult) -> str:
            lines = ["Standard Curve"]
            fit = result.fit
            lines.append(f"slope: {fit.slope}; intercept: {fit.intercept}; R²: {fit.r_squared}")
            for row in result.standard_curve:
                lines.append(
                    f"{row.standard_name}\t{row.standard_concentration:g} {row.concentration_unit}\t{', '.join(row.wells)}\tmean {row.mean_od}\tSD {row.sd}\tCV% {row.cv_percent}\t用于拟合 {row.used_for_fit}\t{'; '.join(row.warnings)}"
                )
            return "\n".join(lines)

        def _bca_sample_text(self, result: BcaAnalysisResult) -> str:
            lines = ["Sample Results"]
            for row in result.sample_results:
                lines.append(
                    f"{row.sample_name}\t{', '.join(row.wells)}\t稀释倍数 {row.dilution_factor:g}\tmean {row.mean_od}\tSD {row.sd}\tCV% {row.cv_percent}\t测定孔浓度 {row.measured_concentration}\t稀释修正后原始样本浓度 {row.original_sample_concentration} {row.unit}\t超出标准曲线范围 {row.out_of_standard_range}\t{'; '.join(row.warnings)}\t备注 {row.note}"
                )
            lines.append(result.review_notice)
            return "\n".join(lines)

        def _refresh_lane_layout(self, *, blank: bool) -> None:
            if not hasattr(self, "_lane_layout_table") or not hasattr(self, "_well_count"):
                return
            lane_count = int(self._well_count.currentText().split()[0])
            self._lane_layout_table.setRowCount(lane_count)
            for row in range(lane_count):
                lane_label = f"Lane {row + 1}"
                if blank or self._lane_layout_table.item(row, 0) is None:
                    self._lane_layout_table.setItem(row, 0, QTableWidgetItem(lane_label))
                    self._lane_layout_table.setItem(row, 1, QTableWidgetItem(""))
                    self._lane_layout_table.setItem(row, 2, QTableWidgetItem(""))

        def _import_loading_lane_layout(self) -> None:
            result = getattr(self._loading_widget, "_current_result", None)
            if result is None:
                self._refresh_lane_layout(blank=True)
                return
            lanes = result.lanes
            self._lane_layout_table.setRowCount(len(lanes))
            for row, lane in enumerate(lanes):
                sample_name = lane.sample_name or lane.lane_label
                if lane.result_row is not None:
                    total_volume = f"{lane.result_row.final_volume_ul:g} µL"
                elif lane.marker_volume_ul:
                    total_volume = f"{lane.marker_volume_ul:g} µL"
                else:
                    total_volume = ""
                self._lane_layout_table.setItem(row, 0, QTableWidgetItem(lane.lane_label))
                self._lane_layout_table.setItem(row, 1, QTableWidgetItem(sample_name))
                self._lane_layout_table.setItem(row, 2, QTableWidgetItem(total_volume))

        def _lane_layout_summary(self) -> list[str]:
            if not hasattr(self, "_lane_layout_table"):
                return ["尚未生成 Lane 布局。"]
            lines = ["Lane 编号\t样品名\t总上样体积"]
            for row in range(self._lane_layout_table.rowCount()):
                values = []
                for column in range(3):
                    item = self._lane_layout_table.item(row, column)
                    values.append(item.text().strip() if item is not None else "")
                lines.append("\t".join(values))
            return lines

        def _save_workflow_record(self, step_id: str) -> None:
            form = self._record_forms[step_id]
            fields = {name: widget.text().strip() for name, widget in form["fields"].items() if isinstance(widget, QLineEdit)}
            sop_text = form["sop"].toPlainText().strip() if isinstance(form["sop"], QTextEdit) else ""
            free_text = form["free"].toPlainText().strip() if isinstance(form["free"], QTextEdit) else ""
            try:
                saved = self._workflow_record_store.save_record(
                    WBWorkflowRecord(
                        step_id=step_id,
                        step_label=str(form["label"]),
                        fields=fields,
                        sop_text=sop_text,
                        free_text=free_text,
                    )
                )
            except WBWorkflowRecordError as exc:
                self._record_status(step_id).setText(str(exc))
                return
            self._record_status(step_id).setText(f"已保存：{saved.record_id}")

        def _load_latest_workflow_record(self, step_id: str) -> None:
            try:
                record = self._workflow_record_store.latest_for_step(step_id)
            except WBWorkflowRecordError as exc:
                self._record_status(step_id).setText(str(exc))
                return
            if record is None:
                self._record_status(step_id).setText("没有可载入的历史记录。")
                return
            form = self._record_forms[step_id]
            for name, widget in form["fields"].items():
                if isinstance(widget, QLineEdit):
                    widget.setText(record.fields.get(name, ""))
            if isinstance(form["sop"], QTextEdit):
                form["sop"].setText(record.sop_text)
            if isinstance(form["free"], QTextEdit):
                form["free"].setText(record.free_text)
            self._record_status(step_id).setText(f"已载入：{record.record_id}")

        def _export_workflow_record_text(self, step_id: str) -> None:
            form = self._record_forms[step_id]
            fields = {name: widget.text().strip() for name, widget in form["fields"].items() if isinstance(widget, QLineEdit)}
            record = WBWorkflowRecord(
                step_id=step_id,
                step_label=str(form["label"]),
                fields=fields,
                sop_text=form["sop"].toPlainText().strip() if isinstance(form["sop"], QTextEdit) else "",
                free_text=form["free"].toPlainText().strip() if isinstance(form["free"], QTextEdit) else "",
            )
            export_path = self._workflow_record_store.resolved_path().with_name(f"{step_id}_workflow_record.txt")
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(record.as_text() + "\n", encoding="utf-8")
            self._record_status(step_id).setText(f"已导出文本：{export_path}")

        def _record_status(self, step_id: str) -> QLabel:
            status = self._record_forms[step_id]["status"]
            if isinstance(status, QLabel):
                return status
            raise RuntimeError("Western Blot record status widget is missing")

        def _handle_calculate(self) -> None:
            try:
                template = self._template_from_form()
                result = calculate_sds_page_gel_batch(
                    SdsPageGelCalculationInput(
                        template=template,
                        gel_count=self._positive_int(self._gel_count.text()),
                        overage_percent=self._non_negative_float(self._overage_percent.text()),
                    )
                )
            except SdsPageGelTemplateError as exc:
                self._show_error(str(exc))
                return
            self._current_template = template
            self._current_result = result
            self._save_template_button.setEnabled(True)
            self._xlsx_export_button.setEnabled(True)
            self._sds_page_result.setText(self._result_text(result))

        def _handle_save_template_json(self) -> None:
            if self._current_template is None:
                self._show_error("请先计算并确认模板。")
                return
            path = self._select_template_save_path()
            if not path:
                return
            try:
                saved = save_sds_page_gel_template_json(self._current_template, path)
            except SdsPageGelTemplateError as exc:
                self._show_error(str(exc))
                return
            self._sds_page_result.append(f"\n模板 JSON 已导出：{saved}")

        def _handle_load_template_json(self) -> None:
            path = self._select_template_load_path()
            if not path:
                return
            try:
                template = load_sds_page_gel_template_json(path)
                conflict_policy = "copy" if self._import_conflict_policy.currentText() == "作为副本导入" else "skip"
                result = self._template_store.import_template(template, conflict_policy=conflict_policy)
            except SdsPageGelTemplateError as exc:
                self._show_error(str(exc))
                return
            if result.template is None:
                self._sds_page_result.setText(result.message)
                return
            self._apply_template(result.template)
            self._current_template = result.template
            self._save_template_button.setEnabled(True)
            self._sds_page_result.setText(f"导入前预览完成：{result.template.template_name}\n{result.message}\n使用前仍需人工核对。")

        def _handle_export_xlsx(self) -> None:
            if self._current_result is None:
                self._show_error("请先计算本次批量用量。")
                return
            path = self._select_xlsx_export_path()
            if not path:
                return
            try:
                exported = save_sds_page_gel_calculation_xlsx(self._current_result, path)
            except SdsPageGelTemplateError:
                self._show_error("导出失败，请检查目标文件夹是否可写")
                return
            self._sds_page_result.append(f"\nXLSX 已导出：{exported}")

        def _template_from_form(self) -> SdsPageGelTemplate:
            return SdsPageGelTemplate(
                template_id=self._template_id(),
                template_name=self._template_name.text().strip(),
                template_version=self._template_version.text().strip() or "v1",
                gel_concentration=self._gel_concentration.text().strip(),
                gel_thickness=self._gel_thickness.currentText(),
                well_count=self._well_count.currentText(),
                gel_format_or_note=self._gel_format_note.text().strip(),
                kit_or_sop_source=self._kit_source.text().strip(),
                resolving_gel_section=self._section_from_form("分离胶", "resolving"),
                stacking_gel_section=self._section_from_form("浓缩胶", "stacking"),
            )

        def _section_from_form(self, title: str, prefix: str) -> GelSection:
            is_used = getattr(self, f"_{prefix}_use").isChecked()
            amount_text = getattr(self, f"_{prefix}_amount").text().strip()
            if not is_used and not amount_text:
                return GelSection(title, (), is_used=False)
            amount = self._float_or_zero(amount_text)
            component = GelComponent(
                component_name=getattr(self, f"_{prefix}_component_name").text().strip(),
                amount_per_gel=amount,
                unit=getattr(self, f"_{prefix}_unit").currentText(),
                note=getattr(self, f"_{prefix}_note").text().strip(),
            )
            return GelSection(title, (component,), is_used=is_used)

        def _apply_template(self, template: SdsPageGelTemplate) -> None:
            self._template_name.setText(template.template_name)
            self._template_version.setText(template.template_version)
            self._gel_concentration.setText(template.gel_concentration)
            self._gel_thickness.setCurrentText(template.gel_thickness)
            self._well_count.setCurrentText(template.well_count)
            self._gel_format_note.setText(template.gel_format_or_note)
            self._kit_source.setText(template.kit_or_sop_source)
            self._apply_section("resolving", template.resolving_gel_section)
            self._apply_section("stacking", template.stacking_gel_section)

        def _apply_section(self, prefix: str, section: GelSection) -> None:
            getattr(self, f"_{prefix}_use").setChecked(section.is_used)
            component = section.components[0] if section.components else GelComponent("", 0, "mL")
            getattr(self, f"_{prefix}_component_name").setText(component.component_name)
            getattr(self, f"_{prefix}_amount").setText(str(component.amount_per_gel))
            getattr(self, f"_{prefix}_unit").setCurrentText(component.unit)
            getattr(self, f"_{prefix}_note").setText(component.note)

        def _result_text(self, result: SdsPageGelCalculationResult) -> str:
            lines = [
                "配胶摘要",
                GEL_TEMPLATE_CONTEXT_NOTICE,
                WB_REVIEW_NOTICE,
                f"模板名称：{result.template.template_name}",
                f"胶数量：{result.gel_count}",
                f"余量百分比：{result.overage_percent}%",
                "",
                "Lane 布局摘要",
                *self._lane_layout_summary(),
                "",
                "总量含余量：",
            ]
            for heading, section in (("Resolving gel 组分表", result.resolving_gel), ("Stacking gel 组分表", result.stacking_gel)):
                lines.append(heading)
                if not section.rows:
                    lines.append("- 0 / 不使用")
                for row in section.rows:
                    lines.append(f"- {row.component_name}: {row.total_amount:g} {row.unit}（每块胶 {row.amount_per_gel:g} {row.unit}; 备注：{row.note}）")
            return "\n".join(lines)

        def _show_error(self, message: str) -> None:
            self._current_result = None
            self._xlsx_export_button.setEnabled(False)
            self._sds_page_result.setText(message)

        def _select_template_save_path(self) -> str:
            path, _ = QFileDialog.getSaveFileName(self, "导出 SDS-PAGE 配胶模板 JSON", "", "JSON (*.json)")
            return path

        def _select_template_load_path(self) -> str:
            path, _ = QFileDialog.getOpenFileName(self, "导入 SDS-PAGE 配胶模板 JSON", "", "JSON (*.json)")
            return path

        def _select_xlsx_export_path(self) -> str:
            path, _ = QFileDialog.getSaveFileName(self, "导出本次 SDS-PAGE 计算 XLSX", "", "XLSX (*.xlsx)")
            return path

        def _template_id(self) -> str:
            name = re.sub(r"[^A-Za-z0-9]+", "_", self._template_name.text().strip().lower()).strip("_")
            return f"sds_page_{name or 'template'}"

        def _positive_int(self, value: str) -> int:
            try:
                number = int(value)
            except ValueError as exc:
                raise SdsPageGelTemplateError("胶数量需要为正整数") from exc
            if number <= 0:
                raise SdsPageGelTemplateError("胶数量需要为正整数")
            return number

        def _non_negative_float(self, value: str) -> float:
            try:
                number = float(value)
            except ValueError as exc:
                raise SdsPageGelTemplateError("余量百分比不能小于 0") from exc
            if number < 0:
                raise SdsPageGelTemplateError("余量百分比不能小于 0")
            return number

        def _float_or_zero(self, value: str) -> float:
            if value == "":
                return 0.0
            try:
                return float(value)
            except ValueError as exc:
                raise SdsPageGelTemplateError("组分用量不能小于 0") from exc

        def _card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsWesternBlotCard")
            return frame

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsWesternBlotWorkspace, QWidget#labToolsWesternBlotContent {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QScrollArea#labToolsWesternBlotScroll {{
                border: 0;
                background: {COLORS["background"]};
            }}
            QLabel#labToolsWesternBlotTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 780;
            }}
            QLabel#labToolsWesternBlotDescription, QLabel#labToolsWesternBlotSectionDescription, QLabel#labToolsWesternBlotPlannedEntries {{
                color: {COLORS["muted"]};
            }}
            QLabel#labToolsWesternBlotBoundary {{
                color: {COLORS["text"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QFrame#labToolsWesternBlotCard, QFrame#labToolsWesternBlotSectionCard, QFrame#sdsPageLaneLayoutCard, QFrame#sdsPageResolvingSectionCard, QFrame#sdsPageStackingSectionCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
                min-height: 150px;
            }}
            QLabel#labToolsWesternBlotSectionStatus {{
                color: #0E6F66;
                background: #E7F7F5;
                border: 1px solid #BCE7E2;
                border-radius: {RADIUS["sm"]}px;
                padding: 4px 8px;
                font-weight: 700;
            }}
            QLabel#labToolsWesternBlotSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QTextEdit#sdsPageGelResultPanel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            """

else:  # pragma: no cover

    class LabToolsWesternBlotWidget:  # type: ignore[no-redef]
        pass
