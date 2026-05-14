from __future__ import annotations

import re

try:
    from PySide6.QtCore import Qt
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
        QScrollArea,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.western_blot import (
        DEFAULT_OVERAGE_PERCENT,
        GEL_REVIEW_NOTICE,
        GEL_TEMPLATE_CONTEXT_NOTICE,
        SUPPORTED_GEL_COMPONENT_UNITS,
        GelComponent,
        GelSection,
        SdsPageGelCalculationInput,
        SdsPageGelCalculationResult,
        SdsPageGelTemplate,
        SdsPageGelTemplateError,
        SdsPageGelTemplateStore,
        calculate_sds_page_gel_batch,
        load_sds_page_gel_template_json,
        save_sds_page_gel_calculation_xlsx,
        save_sds_page_gel_template_json,
    )
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
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsWesternBlotWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._template_store = SdsPageGelTemplateStore()
            self._current_template: SdsPageGelTemplate | None = None
            self._current_result: SdsPageGelCalculationResult | None = None
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
                    "提供 BCA、Bradford、NanoDrop 等蛋白浓度测定入口；底层逻辑后续与吸光度/标准曲线能力复用。",
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
            if planned_entries:
                open_tool = QPushButton("打开 SDS-PAGE 配胶工具")
                open_tool.setObjectName("openSdsPageGelToolButton")
                open_tool.clicked.connect(lambda: self._tabs.setCurrentIndex(1))
                planned_label = QLabel("planned 子入口\n" + "\n".join(f"- {entry}: {SECTION_STATUS}" for entry in planned_entries))
                planned_label.setObjectName("labToolsWesternBlotPlannedEntries")
                planned_label.setWordWrap(True)
                layout.addWidget(planned_label)
                layout.addWidget(open_tool, alignment=Qt.AlignLeft)
            layout.addStretch(1)
            return frame

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
