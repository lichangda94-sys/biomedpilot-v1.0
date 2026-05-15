from __future__ import annotations

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
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.western_blot.calculator import calculate_wb_loading
    from app.labtools.western_blot.exporter import wb_loading_record_csv, wb_loading_record_markdown
    from app.labtools.western_blot.models import WBLoadingCalculatorError, WBLoadingConfig, WBLoadingRecord, WBLoadingResult, WBSampleInput
    from app.labtools.western_blot.store import WBLoadingRecordStore
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    def _line_edit(text: str = "", placeholder: str = "") -> QLineEdit:
        field = QLineEdit()
        field.setText(text)
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(CONTROL_HEIGHT["field"])
        return field


    def _combo(values: tuple[str, ...], current: str | None = None) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        if current in values:
            combo.setCurrentText(current)
        combo.setMinimumHeight(CONTROL_HEIGHT["field"])
        return combo


    class WesternBlotLoadingCalculatorWidget(QWidget):
        def __init__(self, *, record_store: WBLoadingRecordStore | None = None) -> None:
            super().__init__()
            self.setObjectName("westernBlotLoadingCalculatorWidget")
            self.setStyleSheet(self._stylesheet())
            self._record_store = record_store or WBLoadingRecordStore()
            self._current_result: WBLoadingResult | None = None
            self._current_samples: tuple[WBSampleInput, ...] = ()
            self._current_record: WBLoadingRecord | None = None
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, SPACING["md"], 0, 0)
            root.setSpacing(SPACING["md"])

            title = QLabel("Western Blot 上样计算器")
            title.setObjectName("labToolsWesternBlotSectionTitle")
            status = QLabel("available / 可用")
            status.setObjectName("wbLoadingCalculatorStatus")
            boundary = QLabel(
                "当前 L4 仅支持 Western Blot 上样体系计算；不启用 WB 图像分析、条带识别、灰度定量、自动 ROI 或结果解释。"
                "本工具不判断实验设计合理性，也不进行图像分析或结果解释。"
            )
            boundary.setObjectName("labToolsWesternBlotBoundary")
            boundary.setWordWrap(True)
            reducer_notice = QLabel("请确认所用 loading buffer 是否已包含 DTT、β-ME 或其他还原剂；如已包含，可将还原剂模式设为 none。")
            reducer_notice.setObjectName("wbLoadingReducerNotice")
            reducer_notice.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(status)
            root.addWidget(boundary)
            root.addWidget(reducer_notice)
            root.addWidget(self._build_config_card())
            root.addWidget(self._build_sample_card())
            root.addWidget(self._build_action_card())
            root.addWidget(self._build_result_card(), 1)
            root.addWidget(self._build_record_card())
            self._refresh_history()

        def _build_config_card(self) -> QFrame:
            card = self._card()
            layout = QGridLayout(card)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])

            self._experiment_name = _line_edit("WB loading")
            self._experiment_name.setObjectName("wbLoadingExperimentNameField")
            self._target_protein = _line_edit("20")
            self._target_protein.setObjectName("proteinLoadingTargetProteinField")
            self._final_volume = _line_edit("20")
            self._final_volume.setObjectName("proteinLoadingFinalVolumeField")
            self._loading_factor = _combo(("4X", "5X"), "4X")
            self._loading_factor.setObjectName("wbLoadingBufferFactorCombo")
            self._reducing_mode = _combo(("none", "fixed_volume", "percent_of_final"), "none")
            self._reducing_mode.setObjectName("wbLoadingReducingModeCombo")
            self._reducing_name = _line_edit("", "DTT、β-ME、TCEP 或自定义")
            self._reducing_name.setObjectName("wbLoadingReducingNameField")
            self._reducing_fixed_volume = _line_edit("0")
            self._reducing_fixed_volume.setObjectName("wbLoadingReducingFixedVolumeField")
            self._reducing_percent = _line_edit("0")
            self._reducing_percent.setObjectName("wbLoadingReducingPercentField")
            self._diluent_name = _line_edit("ddH2O")
            self._diluent_name.setObjectName("wbLoadingDiluentNameField")
            self._marker_enabled = QCheckBox("启用 Marker，Lane 1 默认 Marker")
            self._marker_enabled.setObjectName("wbLoadingMarkerEnabledCheck")
            self._marker_enabled.setChecked(True)
            self._marker_name = _line_edit("Protein Marker")
            self._marker_name.setObjectName("wbLoadingMarkerNameField")
            self._marker_volume = _line_edit("5")
            self._marker_volume.setObjectName("wbLoadingMarkerVolumeField")
            self._lane_mode = _combo(("auto", "fixed"), "auto")
            self._lane_mode.setObjectName("wbLoadingLaneModeCombo")
            self._fixed_lane_count = _combo(("10", "12", "15"), "10")
            self._fixed_lane_count.setObjectName("wbLoadingFixedLaneCountCombo")
            self._min_pipette_volume = _line_edit("0.5")
            self._min_pipette_volume.setObjectName("wbLoadingMinPipetteField")

            fields = (
                ("实验名称", self._experiment_name),
                ("目标上样蛋白量 (µg/lane)", self._target_protein),
                ("目标终体积 (µL/lane)", self._final_volume),
                ("Loading buffer 倍数", self._loading_factor),
                ("还原剂模式", self._reducing_mode),
                ("还原剂名称", self._reducing_name),
                ("还原剂固定体积 (µL)", self._reducing_fixed_volume),
                ("还原剂百分比 (%)", self._reducing_percent),
                ("补足液名称", self._diluent_name),
                ("Marker 名称", self._marker_name),
                ("Marker 体积 (µL)", self._marker_volume),
                ("Lane 数模式", self._lane_mode),
                ("固定 Lane 数", self._fixed_lane_count),
                ("低体积 warning 阈值 (µL)", self._min_pipette_volume),
            )
            for index, (label, widget) in enumerate(fields):
                layout.addWidget(QLabel(label), index // 3 * 2, index % 3)
                layout.addWidget(widget, index // 3 * 2 + 1, index % 3)
            layout.addWidget(self._marker_enabled, 10, 0, 1, 3)
            return card

        def _build_sample_card(self) -> QFrame:
            card = self._card()
            layout = QVBoxLayout(card)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._sample_table = QTableWidget(2, 3)
            self._sample_table.setObjectName("proteinLoadingSampleTable")
            self._sample_table.setHorizontalHeaderLabels(("样本名称", "浓度 (µg/µL)", "备注"))
            for row in range(2):
                self._sample_table.setItem(row, 0, QTableWidgetItem(f"S{row + 1}"))
                self._sample_table.setItem(row, 1, QTableWidgetItem(""))
                self._sample_table.setItem(row, 2, QTableWidgetItem(""))
            self._sample_table.setMinimumHeight(130)
            self._add_sample_button = QPushButton("添加样本行")
            self._add_sample_button.setObjectName("proteinLoadingAddSampleRowButton")
            self._add_sample_button.clicked.connect(self._add_sample_row)
            layout.addWidget(QLabel("样本输入（浓度单位固定为 µg/µL；重复孔请自行命名为 S1-R1、S1-R2 等）"))
            layout.addWidget(self._sample_table)
            layout.addWidget(self._add_sample_button, alignment=Qt.AlignLeft)
            return card

        def _build_action_card(self) -> QFrame:
            card = self._card()
            layout = QHBoxLayout(card)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._calculate_button = QPushButton("计算上样体系")
            self._calculate_button.setObjectName("proteinLoadingCalculateButton")
            self._calculate_button.clicked.connect(self._handle_calculate)
            self._copy_button = QPushButton("复制结果")
            self._copy_button.setObjectName("proteinLoadingCopyResultButton")
            self._copy_button.setEnabled(False)
            self._copy_button.clicked.connect(self._copy_result)
            layout.addWidget(self._calculate_button)
            layout.addWidget(self._copy_button)
            layout.addStretch(1)
            return card

        def _build_result_card(self) -> QFrame:
            card = self._card()
            layout = QGridLayout(card)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._result_panel = QTextEdit()
            self._result_panel.setObjectName("proteinLoadingResultPanel")
            self._detail_panel = QTextEdit()
            self._detail_panel.setObjectName("wbLoadingDetailResultPanel")
            self._lane_panel = QTextEdit()
            self._lane_panel.setObjectName("wbLoadingLaneLayoutPanel")
            for panel in (self._result_panel, self._detail_panel, self._lane_panel):
                panel.setReadOnly(True)
                panel.setMinimumHeight(150)
                panel.setText("尚未计算。填写基础参数和样本浓度后生成纵向明细与横向 lane layout。")
            layout.addWidget(QLabel("完整结果"), 0, 0)
            layout.addWidget(QLabel("纵向计算明细"), 0, 1)
            layout.addWidget(QLabel("横向 lane layout"), 0, 2)
            layout.addWidget(self._result_panel, 1, 0)
            layout.addWidget(self._detail_panel, 1, 1)
            layout.addWidget(self._lane_panel, 1, 2)
            return card

        def _build_record_card(self) -> QFrame:
            card = self._card()
            layout = QGridLayout(card)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])

            title = QLabel("本次上样记录保存与导出")
            title.setObjectName("labToolsWesternBlotSectionTitle")
            self._operator_name = _line_edit("", "可选")
            self._operator_name.setObjectName("wbLoadingOperatorNameField")
            self._project_name = _line_edit("", "可选")
            self._project_name.setObjectName("wbLoadingProjectNameField")
            self._record_notes = _line_edit("", "可选备注")
            self._record_notes.setObjectName("wbLoadingRecordNotesField")
            self._save_record_button = QPushButton("保存本次上样记录")
            self._save_record_button.setObjectName("wbLoadingSaveRecordButton")
            self._save_record_button.setEnabled(False)
            self._save_record_button.clicked.connect(self._handle_save_record)
            self._copy_markdown_button = QPushButton("复制结果 Markdown")
            self._copy_markdown_button.setObjectName("wbLoadingCopyMarkdownButton")
            self._copy_markdown_button.setEnabled(False)
            self._copy_markdown_button.clicked.connect(self._copy_markdown)
            self._export_markdown_button = QPushButton("导出 Markdown")
            self._export_markdown_button.setObjectName("wbLoadingExportMarkdownButton")
            self._export_markdown_button.setEnabled(False)
            self._export_markdown_button.clicked.connect(self._export_markdown)
            self._export_csv_button = QPushButton("导出 CSV")
            self._export_csv_button.setObjectName("wbLoadingExportCsvButton")
            self._export_csv_button.setEnabled(False)
            self._export_csv_button.clicked.connect(self._export_csv)
            self._record_status = QLabel("尚未保存。记录保存为本地 JSON，不联网、不上传。")
            self._record_status.setObjectName("wbLoadingRecordStatusLabel")
            self._record_status.setWordWrap(True)

            self._history_table = QTableWidget(0, 6)
            self._history_table.setObjectName("wbLoadingRecordHistoryTable")
            self._history_table.setHorizontalHeaderLabels(("实验名称", "创建时间", "样本数", "Lane 数", "状态", "record_id"))
            self._history_table.setMinimumHeight(120)
            self._view_record_button = QPushButton("查看记录")
            self._view_record_button.setObjectName("wbLoadingViewRecordButton")
            self._view_record_button.clicked.connect(self._view_selected_record)
            self._delete_record_button = QPushButton("删除记录")
            self._delete_record_button.setObjectName("wbLoadingDeleteRecordButton")
            self._delete_record_button.clicked.connect(self._delete_selected_record)
            self._refresh_record_button = QPushButton("刷新历史记录")
            self._refresh_record_button.setObjectName("wbLoadingRefreshRecordHistoryButton")
            self._refresh_record_button.clicked.connect(self._refresh_history)

            layout.addWidget(title, 0, 0, 1, 4)
            layout.addWidget(QLabel("操作者"), 1, 0)
            layout.addWidget(QLabel("项目"), 1, 1)
            layout.addWidget(QLabel("备注"), 1, 2)
            layout.addWidget(self._operator_name, 2, 0)
            layout.addWidget(self._project_name, 2, 1)
            layout.addWidget(self._record_notes, 2, 2, 1, 2)
            for index, button in enumerate((self._save_record_button, self._copy_markdown_button, self._export_markdown_button, self._export_csv_button)):
                layout.addWidget(button, 3, index)
            layout.addWidget(self._record_status, 4, 0, 1, 4)
            layout.addWidget(QLabel("历史上样记录"), 5, 0, 1, 4)
            layout.addWidget(self._history_table, 6, 0, 1, 4)
            history_actions = QHBoxLayout()
            history_actions.addWidget(self._view_record_button)
            history_actions.addWidget(self._delete_record_button)
            history_actions.addWidget(self._refresh_record_button)
            history_actions.addStretch(1)
            layout.addLayout(history_actions, 7, 0, 1, 4)
            return card

        def _add_sample_row(self) -> None:
            row = self._sample_table.rowCount()
            self._sample_table.insertRow(row)
            self._sample_table.setItem(row, 0, QTableWidgetItem(f"S{row + 1}"))
            self._sample_table.setItem(row, 1, QTableWidgetItem(""))
            self._sample_table.setItem(row, 2, QTableWidgetItem(""))

        def _handle_calculate(self) -> None:
            try:
                samples = self._samples_from_table()
                result = calculate_wb_loading(self._config_from_form(), samples)
            except (WBLoadingCalculatorError, ValueError) as exc:
                self._current_result = None
                self._current_samples = ()
                self._current_record = None
                self._copy_button.setEnabled(False)
                self._set_record_actions_enabled(False)
                self._result_panel.setText(str(exc))
                self._detail_panel.setText(str(exc))
                self._lane_panel.setText(str(exc))
                return
            self._current_result = result
            self._current_samples = samples
            self._current_record = None
            self._copy_button.setEnabled(True)
            self._set_record_actions_enabled(True)
            self._result_panel.setText(result.as_text())
            self._detail_panel.setText(self._detail_text(result))
            self._lane_panel.setText(self._lane_text(result))
            self._record_status.setText("计算完成，可保存为本地 JSON 记录或导出 Markdown/CSV。")

        def _config_from_form(self) -> WBLoadingConfig:
            return WBLoadingConfig(
                experiment_name=self._experiment_name.text().strip() or "WB loading",
                target_protein_ug=float(self._target_protein.text()),
                final_volume_ul=float(self._final_volume.text()),
                loading_buffer_factor=float(self._loading_factor.currentText().rstrip("X")),
                reducing_agent_mode=self._reducing_mode.currentText(),  # type: ignore[arg-type]
                reducing_agent_name=self._reducing_name.text().strip(),
                reducing_agent_fixed_volume_ul=float(self._reducing_fixed_volume.text() or 0),
                reducing_agent_percent=float(self._reducing_percent.text() or 0),
                diluent_name=self._diluent_name.text().strip() or "ddH2O",
                marker_enabled=self._marker_enabled.isChecked(),
                marker_name=self._marker_name.text().strip() or "Protein Marker",
                marker_volume_ul=float(self._marker_volume.text() or 0),
                lane_count_mode=self._lane_mode.currentText(),  # type: ignore[arg-type]
                fixed_lane_count=int(self._fixed_lane_count.currentText()),
                min_pipette_volume_ul=float(self._min_pipette_volume.text() or 0),
            )

        def _samples_from_table(self) -> tuple[WBSampleInput, ...]:
            samples: list[WBSampleInput] = []
            for row in range(self._sample_table.rowCount()):
                concentration_item = self._sample_table.item(row, 1)
                concentration_text = concentration_item.text().strip() if concentration_item is not None else ""
                if not concentration_text:
                    continue
                name_item = self._sample_table.item(row, 0)
                note_item = self._sample_table.item(row, 2)
                samples.append(
                    WBSampleInput(
                        sample_name=name_item.text().strip() if name_item is not None else "",
                        concentration_ug_per_ul=float(concentration_text),
                        note=note_item.text().strip() if note_item is not None else "",
                    )
                )
            return tuple(samples)

        def _copy_result(self) -> None:
            if self._current_result is not None:
                QApplication.clipboard().setText(self._current_result.as_text())

        def _handle_save_record(self) -> None:
            try:
                record = self._record_from_current_result()
                saved = self._record_store.save_record(record)
            except Exception as exc:
                self._record_status.setText(str(exc))
                return
            self._current_record = saved
            self._record_status.setText(f"已保存本次上样记录：{saved.record_id}")
            self._refresh_history()

        def _copy_markdown(self) -> None:
            try:
                QApplication.clipboard().setText(wb_loading_record_markdown(self._record_for_export()))
            except Exception as exc:
                self._record_status.setText(str(exc))

        def _export_markdown(self) -> None:
            try:
                record = self._record_for_export()
                path, _ = QFileDialog.getSaveFileName(self, "导出 Western Blot 上样记录 Markdown", f"{_safe_stem(record.experiment_name)}.md", "Markdown (*.md)")
                if not path:
                    return
                saved = self._record_store.export_record_markdown(record, path)
            except Exception as exc:
                self._record_status.setText(str(exc))
                return
            self._record_status.setText(f"Markdown 已导出：{saved}")

        def _export_csv(self) -> None:
            try:
                record = self._record_for_export()
                path, _ = QFileDialog.getSaveFileName(self, "导出 Western Blot 上样记录 CSV", f"{_safe_stem(record.experiment_name)}.csv", "CSV (*.csv)")
                if not path:
                    return
                saved = self._record_store.export_record_csv(record, path)
            except Exception as exc:
                self._record_status.setText(str(exc))
                return
            self._record_status.setText(f"CSV 已导出：{saved}")

        def _record_from_current_result(self) -> WBLoadingRecord:
            if self._current_result is None:
                raise WBLoadingCalculatorError("请先计算上样体系。")
            return WBLoadingRecord.from_result(
                self._current_result,
                self._current_samples,
                operator_name=self._operator_name.text().strip(),
                project_name=self._project_name.text().strip(),
                notes=self._record_notes.text().strip(),
            )

        def _record_for_export(self) -> WBLoadingRecord:
            return self._current_record or self._record_from_current_result()

        def _set_record_actions_enabled(self, enabled: bool) -> None:
            for button in (self._save_record_button, self._copy_markdown_button, self._export_markdown_button, self._export_csv_button):
                button.setEnabled(enabled)

        def _refresh_history(self) -> None:
            try:
                records = self._record_store.list_records()
            except Exception as exc:
                self._history_table.setRowCount(0)
                self._record_status.setText(str(exc))
                return
            self._history_table.setRowCount(0)
            for record in sorted(records, key=lambda item: item.created_at, reverse=True):
                row_index = self._history_table.rowCount()
                self._history_table.insertRow(row_index)
                rows = record.result_snapshot.get("rows", [])
                lanes = record.result_snapshot.get("lanes", [])
                values = (
                    record.experiment_name,
                    record.created_at,
                    str(len(rows) if isinstance(rows, list) else 0),
                    str(len(lanes) if isinstance(lanes, list) else 0),
                    record.summary_status,
                    record.record_id,
                )
                for column, value in enumerate(values):
                    self._history_table.setItem(row_index, column, QTableWidgetItem(value))

        def _selected_record_id(self) -> str | None:
            row = self._history_table.currentRow()
            if row < 0:
                return None
            item = self._history_table.item(row, 5)
            return item.text().strip() if item is not None else None

        def _view_selected_record(self) -> None:
            record_id = self._selected_record_id()
            if not record_id:
                self._record_status.setText("请先选择一条历史记录。")
                return
            try:
                record = self._record_store.get_record(record_id)
            except Exception as exc:
                self._record_status.setText(str(exc))
                return
            self._current_record = record
            self._result_panel.setText(wb_loading_record_markdown(record))
            self._detail_panel.setText(wb_loading_record_csv(record))
            self._lane_panel.setText("\n".join("\t".join(row) for row in record.lane_layout_snapshot))
            self._record_status.setText(f"已载入记录：{record.record_id}")

        def _delete_selected_record(self) -> None:
            record_id = self._selected_record_id()
            if not record_id:
                self._record_status.setText("请先选择一条历史记录。")
                return
            answer = QMessageBox.question(self, "确认删除记录", "删除 Western Blot 上样记录前请确认。此操作只影响本地 JSON。")
            if answer != QMessageBox.Yes:
                return
            try:
                self._record_store.delete_record(record_id, confirmed=True)
            except Exception as exc:
                self._record_status.setText(str(exc))
                return
            self._record_status.setText("记录已删除。本地 JSON 已更新。")
            self._refresh_history()

        def _detail_text(self, result: WBLoadingResult) -> str:
            lines = [
                "纵向计算明细表",
                "样本\t浓度\t目标蛋白\t样本体积\tLoading buffer\t还原剂\t补足液\t终体积\t状态",
            ]
            for row in result.rows:
                lines.append(
                    f"{row.sample_name}\t{row.concentration_ug_per_ul:g} µg/µL\t{row.target_protein_ug:g} µg\t"
                    f"{row.sample_volume_ul:g} µL\t{row.loading_buffer_volume_ul:g} µL\t{row.reducing_agent_volume_ul:g} µL\t"
                    f"{row.diluent_volume_ul:g} µL\t{row.final_volume_ul:g} µL\t{row.status}"
                )
                lines.extend(f"警告：{warning}" for warning in row.warnings)
                lines.extend(f"错误：{error}" for error in row.errors)
            return "\n".join(lines)

        def _lane_text(self, result: WBLoadingResult) -> str:
            return "\n".join("\t".join(row) for row in result.lane_layout_table)

        def _card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("westernBlotLoadingCard")
            return frame

        def _stylesheet(self) -> str:
            return f"""
            QWidget#westernBlotLoadingCalculatorWidget {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QFrame#westernBlotLoadingCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QLabel#labToolsWesternBlotSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QLabel#wbLoadingCalculatorStatus {{
                color: #0E6F66;
                background: #E7F7F5;
                border: 1px solid #BCE7E2;
                border-radius: {RADIUS["sm"]}px;
                padding: 5px 8px;
                font-weight: 700;
            }}
            QLabel#labToolsWesternBlotBoundary, QLabel#wbLoadingReducerNotice {{
                color: {COLORS["text"]};
                background: #FFF4F2;
                border: 1px solid #F3B4AA;
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            """

else:  # pragma: no cover

    class WesternBlotLoadingCalculatorWidget:  # type: ignore[no-redef]
        pass


def _safe_stem(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value.strip())
    return cleaned or "western_blot_loading_record"
