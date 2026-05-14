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
        analyze_bca_assay,
        annotate_well_range,
        calculate_protein_loading,
        calculate_sds_page_gel_batch,
        load_sds_page_gel_template_json,
        parse_bca_od_matrix,
        save_sds_page_gel_calculation_xlsx,
        save_sds_page_gel_template_json,
    )
    from app.labtools.ui.imagej_bridge_widgets import LabToolsImageJFijiStatusPanel
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
            self._current_template: SdsPageGelTemplate | None = None
            self._current_result: SdsPageGelCalculationResult | None = None
            self._current_loading_result: ProteinLoadingResult | None = None
            self._current_bca_result: BcaAnalysisResult | None = None
            self._bca_annotations: dict[str, BcaWellAnnotation] = {}
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
            description = QLabel("用于蛋白样品准备、蛋白浓度测定入口、上样体系、SDS-PAGE 配胶、电泳/转膜参数、抗体孵育流程和后续灰度分析。")
            description.setObjectName("labToolsWesternBlotDescription")
            description.setWordWrap(True)
            notice = QLabel(f"{GEL_TEMPLATE_CONTEXT_NOTICE}。{GEL_REVIEW_NOTICE}。")
            notice.setObjectName("labToolsWesternBlotBoundary")
            notice.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(description)
            layout.addWidget(notice)

            self._tabs = QTabWidget()
            self._tabs.setObjectName("westernBlotTabs")
            self._tabs.addTab(self._build_sections_tab(), "模块分区")
            self._tabs.addTab(self._build_sds_page_tool_tab(), "SDS-PAGE 配胶模板")
            self._tabs.addTab(self._build_protein_loading_tab(), "蛋白上样体系")
            self._tabs.addTab(self._build_bca_assay_tab(), "BCA 蛋白浓度测定")
            layout.addWidget(self._tabs, 1)

            scroll.setWidget(content)
            root.addWidget(scroll)

        def _build_sections_tab(self) -> QWidget:
            tab = QWidget()
            layout = QGridLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])
            sections = (
                (
                    "蛋白样品准备",
                    "用于记录蛋白提取、裂解液/抑制剂草稿、样本分组和实验室自定义流程。当前为流程模板入口，不自动生成唯一实验方案。",
                    (),
                ),
                (
                    "蛋白浓度测定",
                    "提供 BCA 蛋白浓度测定辅助计算入口；Bradford、NanoDrop 后续仍需单独确认逻辑。",
                    (),
                ),
                (
                    "上样与胶",
                    "用于蛋白上样体系计算、loading buffer、还原剂、SDS-PAGE 配胶模板和批量配制计算。",
                    ("蛋白上样体系计算", "SDS-PAGE 配胶模板与批量配制"),
                ),
                (
                    "电泳 / 转膜 / 抗体孵育流程",
                    "用于记录电泳参数、电转参数、封闭、一抗、二抗和洗膜步骤模板。用户可录入试剂盒说明书或实验室成熟流程。",
                    (),
                ),
                (
                    "结果与灰度分析",
                    "用于后续 WB/gel grayscale、条带 ROI、背景扣除、target/loading control ratio 和结果导出。开发前需单独确认图像分析逻辑。",
                    (),
                ),
            )
            for index, (section_title, section_description, planned_entries) in enumerate(sections):
                card = self._section_card(section_title, section_description, planned_entries)
                layout.addWidget(card, index // 2, index % 2)
            return tab

        def _build_protein_loading_tab(self) -> QWidget:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["md"], 0, 0)
            layout.setSpacing(SPACING["md"])

            intro = QLabel("蛋白上样体系计算")
            intro.setObjectName("labToolsWesternBlotSectionTitle")
            boundary = QLabel(PROTEIN_LOADING_REVIEW_NOTICE)
            boundary.setObjectName("labToolsWesternBlotDescription")
            boundary.setWordWrap(True)
            reducing = QLabel(REDUCING_AGENT_NOTICE)
            reducing.setObjectName("labToolsWesternBlotBoundary")
            reducing.setWordWrap(True)
            layout.addWidget(intro)
            layout.addWidget(boundary)
            layout.addWidget(reducing)

            sample_card = self._card()
            sample_layout = QVBoxLayout(sample_card)
            sample_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._loading_sample_table = QTableWidget(2, 3)
            self._loading_sample_table.setObjectName("proteinLoadingSampleTable")
            self._loading_sample_table.setHorizontalHeaderLabels(("样本名称", "蛋白样品浓度", "浓度单位"))
            for row in range(2):
                self._loading_sample_table.setItem(row, 0, QTableWidgetItem(f"Sample {row + 1}"))
                self._loading_sample_table.setItem(row, 1, QTableWidgetItem(""))
                unit_combo = _combo(SUPPORTED_PROTEIN_CONCENTRATION_UNITS, "µg/µL")
                unit_combo.setObjectName("proteinLoadingConcentrationUnitCombo")
                self._loading_sample_table.setCellWidget(row, 2, unit_combo)
            add_row = QPushButton("添加样本行")
            add_row.setObjectName("proteinLoadingAddSampleRowButton")
            add_row.clicked.connect(self._add_loading_sample_row)
            sample_layout.addWidget(self._loading_sample_table)
            sample_layout.addWidget(add_row, alignment=Qt.AlignLeft)
            layout.addWidget(sample_card)

            settings = self._card()
            settings_layout = QGridLayout(settings)
            settings_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._loading_target_protein = _line_edit("目标每孔蛋白量 µg", "20")
            self._loading_target_protein.setObjectName("proteinLoadingTargetProteinField")
            self._loading_final_volume = _line_edit("最终上样体积 µL", "20")
            self._loading_final_volume.setObjectName("proteinLoadingFinalVolumeField")
            self._loading_buffer_multiple = _line_edit("Loading buffer 倍数，例如 4", "4")
            self._loading_buffer_multiple.setObjectName("proteinLoadingBufferMultipleField")
            self._loading_buffer_target = _line_edit("Loading buffer 目标终浓度", "1")
            self._loading_buffer_target.setObjectName("proteinLoadingBufferTargetField")
            self._loading_overage = _line_edit("余量百分比", str(int(DEFAULT_LOADING_OVERAGE_PERCENT)))
            self._loading_overage.setObjectName("proteinLoadingOverageField")
            for index, (label, widget) in enumerate(
                (
                    ("目标每孔蛋白量 (µg)", self._loading_target_protein),
                    ("最终上样体积 (µL)", self._loading_final_volume),
                    ("Loading buffer 倍数", self._loading_buffer_multiple),
                    ("Loading buffer 目标终浓度", self._loading_buffer_target),
                    ("余量百分比", self._loading_overage),
                )
            ):
                settings_layout.addWidget(QLabel(label), index // 3 * 2, index % 3)
                settings_layout.addWidget(widget, index // 3 * 2 + 1, index % 3)
            layout.addWidget(settings)

            action = self._card()
            action_layout = QHBoxLayout(action)
            action_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._loading_calculate_button = QPushButton("计算上样体系")
            self._loading_calculate_button.setObjectName("proteinLoadingCalculateButton")
            self._loading_calculate_button.clicked.connect(self._handle_loading_calculate)
            self._loading_copy_button = QPushButton("复制结果")
            self._loading_copy_button.setObjectName("proteinLoadingCopyResultButton")
            self._loading_copy_button.setEnabled(False)
            self._loading_copy_button.clicked.connect(self._copy_loading_result)
            action_layout.addWidget(self._loading_calculate_button)
            action_layout.addWidget(self._loading_copy_button)
            action_layout.addStretch(1)
            layout.addWidget(action)

            self._loading_result = QTextEdit()
            self._loading_result.setObjectName("proteinLoadingResultPanel")
            self._loading_result.setReadOnly(True)
            self._loading_result.setMinimumHeight(180)
            self._loading_result.setText("尚未计算。填写样本浓度和全局设置后生成辅助计算草稿。")
            layout.addWidget(self._loading_result, 1)
            return tab

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

            intro = QLabel("SDS-PAGE 配胶模板与批量配制计算器")
            intro.setObjectName("labToolsWesternBlotSectionTitle")
            boundary = QLabel(
                "基于用户录入的试剂盒/实验室模板进行批量换算；不内置通用配方、不进行自动配方推荐、不自动推导胶浓度、不生成配置步骤。"
            )
            boundary.setObjectName("labToolsWesternBlotDescription")
            boundary.setWordWrap(True)
            layout.addWidget(intro)
            layout.addWidget(boundary)
            layout.addWidget(self._build_template_card())
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

        def _section_card(self, title: str, description: str, planned_entries: tuple[str, ...]) -> QFrame:
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
            if planned_entries and title != "上样与胶":
                planned_label = QLabel("planned 子入口\n" + "\n".join(f"- {entry}: {SECTION_STATUS}" for entry in planned_entries))
                planned_label.setObjectName("labToolsWesternBlotPlannedEntries")
                planned_label.setWordWrap(True)
                layout.addWidget(planned_label)
            if title == "蛋白浓度测定":
                status_label = QLabel("已开放子入口\n- BCA 蛋白浓度测定: 已实现 / 辅助计算草稿\n- Bradford / NanoDrop: 待确认使用逻辑 / 规划中 / 暂未开放")
                status_label.setObjectName("labToolsWesternBlotPlannedEntries")
                status_label.setWordWrap(True)
                layout.addWidget(status_label)
                open_bca = QPushButton("打开 BCA 蛋白浓度测定")
                open_bca.setObjectName("openBcaAssayToolButton")
                open_bca.clicked.connect(lambda: self._tabs.setCurrentIndex(3))
                layout.addWidget(open_bca, alignment=Qt.AlignLeft)
            if title == "上样与胶":
                status_label = QLabel("已开放子入口\n- 蛋白上样体系计算: 已实现 / 辅助计算草稿\n- SDS-PAGE 配胶模板与批量配制: 已实现 / 用户模板换算")
                status_label.setObjectName("labToolsWesternBlotPlannedEntries")
                status_label.setWordWrap(True)
                layout.addWidget(status_label)
                open_loading = QPushButton("打开蛋白上样体系计算器")
                open_loading.setObjectName("openProteinLoadingToolButton")
                open_loading.clicked.connect(lambda: self._tabs.setCurrentIndex(2))
                open_tool = QPushButton("打开 SDS-PAGE 配胶工具")
                open_tool.setObjectName("openSdsPageGelToolButton")
                open_tool.clicked.connect(lambda: self._tabs.setCurrentIndex(1))
                layout.addWidget(open_loading, alignment=Qt.AlignLeft)
                layout.addWidget(open_tool, alignment=Qt.AlignLeft)
            if title == "结果与灰度分析":
                layout.addWidget(
                    LabToolsImageJFijiStatusPanel(
                        workflow_name="Western Blot 灰度分析 workflow",
                        bridge=self._imagej_bridge,
                        can_continue_without_engine=False,
                    )
                )
            layout.addStretch(1)
            return frame

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
                GEL_TEMPLATE_CONTEXT_NOTICE,
                GEL_REVIEW_NOTICE,
                f"模板名称：{result.template.template_name}",
                f"胶数量：{result.gel_count}",
                f"余量百分比：{result.overage_percent}%",
                "总量含余量：",
            ]
            for section in (result.resolving_gel, result.stacking_gel):
                lines.append(section.section_name)
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
            QFrame#labToolsWesternBlotCard, QFrame#labToolsWesternBlotSectionCard, QFrame#sdsPageResolvingSectionCard, QFrame#sdsPageStackingSectionCard {{
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
