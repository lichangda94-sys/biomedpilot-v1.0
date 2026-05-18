from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.labtools.cell_experiments import (
    CELL_EXPERIMENT_RECORD_TYPES,
    CRYOVIAL_STATUSES,
    RECORD_TEMPLATE_FIELDS,
    CellExperimentError,
    CellExperimentRecord,
    CellExperimentRecordStore,
    CellProfile,
    CellProfileStore,
    FreezingBatch,
    FreezingInventoryStore,
    calculate_seeding_preparation,
)
from app.labtools.ui.image_analysis_widgets import fluorescence_workbench_widget, scratch_area_workbench_widget, transwell_workbench_widget
from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING


class LabToolsCellExperimentPage(QWidget):
    def __init__(
        self,
        *,
        profile_store: CellProfileStore | None = None,
        record_store: CellExperimentRecordStore | None = None,
        inventory_store: FreezingInventoryStore | None = None,
    ) -> None:
        super().__init__()
        self._profile_store = profile_store or CellProfileStore()
        self._inventory_store = inventory_store or FreezingInventoryStore()
        self._record_store = record_store or CellExperimentRecordStore(profile_store=self._profile_store, inventory_store=self._inventory_store)
        self.setObjectName("labToolsCellExperimentPage")
        self.setStyleSheet(_stylesheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        root.setSpacing(SPACING["lg"])

        title = QLabel("细胞实验工具")
        title.setObjectName("labToolsCellExperimentTitle")
        description = QLabel("记录细胞档案、复苏、传代、接种、冻存、给药、转染和其他处理流程。")
        description.setObjectName("labToolsCellExperimentDescription")
        description.setWordWrap(True)
        boundary = QLabel("第一版提供模板化电子记录、轻量冻存库存、从上次记录创建和 TXT 导出；图像分析区本阶段只生成任务、Macro 模板映射和 RunRequest；不实现完整 ELN/LIMS、真实图像识别、给药计算、转染体系计算或 ImageJ/Fiji 安装检测。")
        boundary.setObjectName("labToolsCellExperimentBoundary")
        boundary.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(description)
        root.addWidget(boundary)

        top_tabs = QTabWidget()
        top_tabs.setObjectName("cellExperimentTopTabs")
        top_tabs.addTab(self._records_tab(), "细胞实验记录")
        top_tabs.addTab(self._image_analysis_tab(), "细胞图像分析")
        root.addWidget(top_tabs, 1)

    def _records_tab(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setObjectName("cellExperimentRecordTabs")
        tabs.addTab(CellProfileWidget(self._profile_store, self._inventory_store, self._record_store), "细胞档案")
        for record_type, label in CELL_EXPERIMENT_RECORD_TYPES[1:]:
            tabs.addTab(RecordTemplateWidget(record_type, label, self._profile_store, self._record_store, self._inventory_store), label)
        return tabs

    def _image_analysis_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["md"])
        description = QLabel("进入划痕实验、Transwell、荧光 / 染色图像等分析页面。")
        description.setObjectName("cellExperimentImageAnalysisDescription")
        description.setWordWrap(True)
        layout.addWidget(description)
        tabs = QTabWidget()
        tabs.setObjectName("cellExperimentImageAnalysisTabs")
        tabs.addTab(scratch_area_workbench_widget(), "划痕实验图像分析")
        tabs.addTab(transwell_workbench_widget(), "Transwell 图像分析")
        tabs.addTab(fluorescence_workbench_widget(), "荧光 / 染色图像分析")
        layout.addWidget(tabs, 1)
        return page


class CellProfileWidget(QWidget):
    def __init__(self, profile_store: CellProfileStore, inventory_store: FreezingInventoryStore, record_store: CellExperimentRecordStore) -> None:
        super().__init__()
        self._profile_store = profile_store
        self._inventory_store = inventory_store
        self._record_store = record_store
        self._current_profile_id = ""
        self._fields: dict[str, QLineEdit] = {}
        self.setObjectName("cellProfileTemplatePage")

        root = QVBoxLayout(self)
        root.setSpacing(SPACING["md"])
        root.addWidget(_note("细胞档案详情包含基础信息、培养条件、质控与状态、冻存库存、关联记录、备注 / SOP。"))

        grid = QGridLayout()
        profile_fields = (
            ("cell_name", "细胞名称"),
            ("alias", "别名"),
            ("cell_type", "细胞类型"),
            ("species", "物种"),
            ("tissue_origin", "组织来源"),
            ("source", "来源"),
            ("batch_or_lot", "批次 / lot"),
            ("current_passage", "当前 passage"),
            ("basal_medium", "培养基"),
            ("serum_type", "血清"),
            ("antibiotics", "抗生素"),
            ("culture_temperature", "培养温度"),
            ("co2_percent", "CO2 %"),
            ("recommended_split_ratio", "推荐传代比例"),
            ("recommended_seeding_density", "推荐接种密度"),
            ("current_status", "当前状态"),
            ("mycoplasma_status", "支原体状态"),
            ("str_status", "STR 状态"),
        )
        for index, (key, label) in enumerate(profile_fields):
            edit = QLineEdit()
            edit.setObjectName(f"cellProfileField_{key}")
            self._fields[key] = edit
            grid.addWidget(QLabel(label), index // 2, (index % 2) * 2)
            grid.addWidget(edit, index // 2, (index % 2) * 2 + 1)
        root.addLayout(grid)

        self._sop = QTextEdit()
        self._sop.setObjectName("cellProfileSopText")
        self._sop.setPlaceholderText("备注 / SOP")
        root.addWidget(self._sop)

        actions = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setObjectName("cellProfileSearchInput")
        self._search.setPlaceholderText("搜索 / 筛选细胞档案")
        self._search.textChanged.connect(self._refresh_profiles)
        actions.addWidget(self._search, 1)
        for name, label, callback in (
            ("cellProfileNewButton", "新建细胞档案", self._new_profile),
            ("cellProfileSaveButton", "保存细胞档案", self._save_profile),
            ("cellProfileCopyButton", "复制细胞档案", self._copy_profile),
            ("cellProfileExportButton", "导出细胞档案 TXT", self._export_profile),
        ):
            button = QPushButton(label)
            button.setObjectName(name)
            button.clicked.connect(callback)
            actions.addWidget(button)
        root.addLayout(actions)

        self._profile_table = QTableWidget(0, 4)
        self._profile_table.setObjectName("cellProfileTable")
        self._profile_table.setHorizontalHeaderLabels(["细胞名称", "当前 passage", "状态", "档案 ID"])
        self._profile_table.cellClicked.connect(self._select_profile_row)
        root.addWidget(self._profile_table)

        root.addWidget(self._inventory_panel())
        self._status = QLabel("")
        self._status.setObjectName("cellProfileStatusLabel")
        root.addWidget(self._status)
        self._refresh_profiles()
        self._refresh_cryovials()

    def _inventory_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("cellProfileFreezingInventorySection")
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel("冻存库存"))
        controls = QHBoxLayout()
        self._batch_code = QLineEdit()
        self._batch_code.setObjectName("freezingBatchCodeInput")
        self._batch_code.setPlaceholderText("批次编号")
        self._vial_count = QSpinBox()
        self._vial_count.setObjectName("freezingCryovialCountInput")
        self._vial_count.setRange(0, 999)
        self._vial_count.setValue(2)
        self._tank = QLineEdit()
        self._tank.setObjectName("cryovialTankInput")
        self._tank.setPlaceholderText("液氮罐")
        self._rack = QLineEdit()
        self._rack.setObjectName("cryovialRackInput")
        self._rack.setPlaceholderText("架")
        self._box = QLineEdit()
        self._box.setObjectName("cryovialBoxInput")
        self._box.setPlaceholderText("盒")
        self._start_position = QLineEdit("1")
        self._start_position.setObjectName("cryovialStartPositionInput")
        self._start_position.setPlaceholderText("起始位置")
        create = QPushButton("新建冻存批次并生成冻存管")
        create.setObjectName("freezingBatchCreateButton")
        create.clicked.connect(self._create_freezing_batch)
        for widget in (self._batch_code, self._vial_count, self._tank, self._rack, self._box, self._start_position, create):
            controls.addWidget(widget)
        layout.addLayout(controls)

        edit_controls = QHBoxLayout()
        self._cryovial_id = QLineEdit()
        self._cryovial_id.setObjectName("cryovialEditIdInput")
        self._cryovial_id.setPlaceholderText("冻存管 ID")
        self._cryovial_position = QLineEdit()
        self._cryovial_position.setObjectName("cryovialPositionEditInput")
        self._cryovial_position.setPlaceholderText("位置")
        self._cryovial_status = QComboBox()
        self._cryovial_status.setObjectName("cryovialStatusEditInput")
        self._cryovial_status.addItems(CRYOVIAL_STATUSES)
        update = QPushButton("编辑冻存管位置和状态")
        update.setObjectName("cryovialUpdateButton")
        update.clicked.connect(self._update_cryovial)
        for widget in (self._cryovial_id, self._cryovial_position, self._cryovial_status, update):
            edit_controls.addWidget(widget)
        layout.addLayout(edit_controls)

        self._cryovial_table = QTableWidget(0, 6)
        self._cryovial_table.setObjectName("cellProfileCryovialTable")
        self._cryovial_table.setHorizontalHeaderLabels(["编号", "Passage", "位置", "状态", "冻存日期", "冻存管 ID"])
        self._cryovial_table.cellClicked.connect(self._select_cryovial_row)
        layout.addWidget(self._cryovial_table)
        return frame

    def _new_profile(self) -> None:
        self._current_profile_id = ""
        for field in self._fields.values():
            field.clear()
        self._sop.clear()
        self._status.setText("已清空，可新建细胞档案。")

    def _save_profile(self) -> None:
        values = {key: widget.text().strip() for key, widget in self._fields.items()}
        if self._current_profile_id:
            values["cell_profile_id"] = self._current_profile_id
        values["cell_name"] = values.get("cell_name") or "未命名细胞"
        values["sop_text"] = self._sop.toPlainText()
        profile = self._profile_store.save_profile(CellProfile.from_dict(values))
        self._current_profile_id = profile.cell_profile_id
        self._refresh_profiles()
        self._refresh_cryovials()
        self._status.setText(f"已保存细胞档案：{profile.cell_name}")

    def _copy_profile(self) -> None:
        if not self._current_profile_id:
            self._status.setText("请先选择细胞档案。")
            return
        copied = self._profile_store.copy_profile(self._current_profile_id)
        self._current_profile_id = copied.cell_profile_id
        self._fill_profile(copied)
        self._refresh_profiles()
        self._status.setText(f"已复制细胞档案：{copied.cell_name}")

    def _export_profile(self) -> None:
        if not self._current_profile_id:
            self._status.setText("请先选择细胞档案。")
            return
        path = self._profile_store.export_profile_text(self._current_profile_id)
        self._status.setText(f"已导出：{path}")

    def _refresh_profiles(self) -> None:
        profiles = self._profile_store.search(self._search.text() if hasattr(self, "_search") else "")
        self._profile_table.setRowCount(len(profiles))
        for row, profile in enumerate(profiles):
            for column, value in enumerate((profile.cell_name, profile.current_passage, profile.current_status, profile.cell_profile_id)):
                self._profile_table.setItem(row, column, QTableWidgetItem(value))

    def _select_profile_row(self, row: int, _column: int) -> None:
        item = self._profile_table.item(row, 3)
        if not item:
            return
        profile = self._profile_store.get(item.text())
        self._current_profile_id = profile.cell_profile_id
        self._fill_profile(profile)
        self._refresh_cryovials()

    def _fill_profile(self, profile: CellProfile) -> None:
        payload = profile.to_dict()
        for key, widget in self._fields.items():
            widget.setText(str(payload.get(key) or ""))
        self._sop.setPlainText(profile.sop_text)

    def _create_freezing_batch(self) -> None:
        if not self._current_profile_id:
            self._status.setText("请先选择或保存细胞档案。")
            return
        profile = self._profile_store.get(self._current_profile_id)
        batch = FreezingBatch(
            cell_profile_id=profile.cell_profile_id,
            cell_name=profile.cell_name,
            batch_code=self._batch_code.text().strip(),
            passage=profile.current_passage,
            cryovial_count=self._vial_count.value(),
        )
        _, cryovials = self._inventory_store.save_batch_with_generated_cryovials(
            batch,
            liquid_nitrogen_tank=self._tank.text().strip(),
            rack=self._rack.text().strip(),
            box=self._box.text().strip(),
            start_box_position=self._start_position.text().strip() or "1",
        )
        self._refresh_cryovials()
        self._status.setText(f"已生成 {len(cryovials)} 个冻存管。")

    def _refresh_cryovials(self) -> None:
        cryovials = self._inventory_store.list_cryovials(cell_profile_id=self._current_profile_id) if self._current_profile_id else ()
        self._cryovial_table.setRowCount(len(cryovials))
        for row, vial in enumerate(cryovials):
            for column, value in enumerate((vial.cryovial_code, vial.passage, vial.location, vial.status, vial.freezing_date, vial.cryovial_id)):
                self._cryovial_table.setItem(row, column, QTableWidgetItem(value))

    def _select_cryovial_row(self, row: int, _column: int) -> None:
        item = self._cryovial_table.item(row, 5)
        if item:
            self._cryovial_id.setText(item.text())

    def _update_cryovial(self) -> None:
        cryovial_id = self._cryovial_id.text().strip()
        if not cryovial_id:
            self._status.setText("请先选择冻存管。")
            return
        self._inventory_store.update_cryovial(cryovial_id, box_position=self._cryovial_position.text().strip(), status=self._cryovial_status.currentText())
        self._refresh_cryovials()
        self._status.setText("已更新冻存管位置和状态。")


class RecordTemplateWidget(QWidget):
    def __init__(self, record_type: str, label: str, profile_store: CellProfileStore, record_store: CellExperimentRecordStore, inventory_store: FreezingInventoryStore) -> None:
        super().__init__()
        self._record_type = record_type
        self._label = label
        self._profile_store = profile_store
        self._record_store = record_store
        self._inventory_store = inventory_store
        self._fields: dict[str, QLineEdit] = {}
        self._latest_record_id = ""
        self.setObjectName(f"cellRecordTemplate_{record_type}")

        root = QVBoxLayout(self)
        root.setSpacing(SPACING["md"])
        root.addWidget(_note(f"{label}：选择细胞档案后自动保存 cell_profile_id 和 cell_profile_snapshot。"))

        selectors = QHBoxLayout()
        self._profile_combo = QComboBox()
        self._profile_combo.setObjectName(f"cellRecordProfileSelector_{record_type}")
        self._profile_combo.currentIndexChanged.connect(self._refresh_thaw_cryovials)
        selectors.addWidget(QLabel("细胞档案"))
        selectors.addWidget(self._profile_combo, 1)
        self._cryovial_combo = QComboBox()
        self._cryovial_combo.setObjectName("thawAvailableCryovialSelector")
        if record_type == "thaw":
            selectors.addWidget(QLabel("可用冻存管"))
            selectors.addWidget(self._cryovial_combo, 1)
        root.addLayout(selectors)

        common = QGridLayout()
        self._experiment_name = QLineEdit()
        self._experiment_name.setObjectName(f"cellRecordExperimentName_{record_type}")
        self._operator = QLineEdit()
        self._operator.setObjectName(f"cellRecordOperator_{record_type}")
        common.addWidget(QLabel("实验名称"), 0, 0)
        common.addWidget(self._experiment_name, 0, 1)
        common.addWidget(QLabel("操作者"), 0, 2)
        common.addWidget(self._operator, 0, 3)
        root.addLayout(common)

        grid = QGridLayout()
        for index, field_name in enumerate(RECORD_TEMPLATE_FIELDS[record_type]):
            edit = QLineEdit()
            edit.setObjectName(f"cellRecordField_{record_type}_{field_name}")
            self._fields[field_name] = edit
            grid.addWidget(QLabel(field_name), index // 2, (index % 2) * 2)
            grid.addWidget(edit, index // 2, (index % 2) * 2 + 1)
        root.addLayout(grid)

        if record_type == "seeding":
            root.addWidget(self._seeding_calculation_panel())

        self._sop = QTextEdit()
        self._sop.setObjectName(f"cellRecordFreeSop_{record_type}")
        self._sop.setPlaceholderText("free_text_sop")
        self._notes = QTextEdit()
        self._notes.setObjectName(f"cellRecordNotes_{record_type}")
        self._notes.setPlaceholderText("notes")
        root.addWidget(self._sop)
        root.addWidget(self._notes)

        actions = QHBoxLayout()
        for name, label_text, callback in (
            (f"cellRecordSaveButton_{record_type}", "保存记录", self._save_record),
            (f"cellRecordFromLastButton_{record_type}", "从上次记录创建", self._from_last),
            (f"cellRecordCopyButton_{record_type}", "复制当前记录", self._copy_current),
            (f"cellRecordExportButton_{record_type}", "导出 TXT", self._export_record),
        ):
            button = QPushButton(label_text)
            button.setObjectName(name)
            button.clicked.connect(callback)
            actions.addWidget(button)
        root.addLayout(actions)
        self._status = QLabel("")
        self._status.setObjectName(f"cellRecordStatus_{record_type}")
        root.addWidget(self._status)
        root.addStretch(1)
        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        self._profile_combo.clear()
        for profile in self._profile_store.load():
            self._profile_combo.addItem(f"{profile.cell_name} ({profile.current_passage})", profile.cell_profile_id)
        self._refresh_thaw_cryovials()

    def _selected_profile(self) -> CellProfile | None:
        profile_id = self._profile_combo.currentData()
        if not profile_id:
            return None
        return self._profile_store.get(str(profile_id))

    def _refresh_thaw_cryovials(self) -> None:
        if self._record_type != "thaw":
            return
        self._cryovial_combo.clear()
        profile = self._selected_profile()
        if not profile:
            return
        for vial in self._inventory_store.list_available_cryovials(profile.cell_profile_id):
            self._cryovial_combo.addItem(f"{vial.cryovial_code} {vial.location}", vial.cryovial_id)

    def _save_record(self) -> None:
        profile = self._selected_profile()
        if not profile:
            self._status.setText("请先选择细胞档案。")
            return
        fields = {name: widget.text().strip() for name, widget in self._fields.items()}
        if self._record_type == "thaw" and self._cryovial_combo.currentData():
            vial_id = str(self._cryovial_combo.currentData())
            fields["cryovial_id"] = vial_id
        record = CellExperimentRecord(
            record_type=self._record_type,
            cell_profile_id=profile.cell_profile_id,
            cell_profile_snapshot=profile.snapshot(),
            experiment_name=self._experiment_name.text().strip() or self._label,
            fields=fields,
            operator=self._operator.text().strip(),
            notes=self._notes.toPlainText(),
            free_text_sop=self._sop.toPlainText(),
        )
        saved = self._record_store.save_record(record)
        self._latest_record_id = saved.record_id
        self._refresh_thaw_cryovials()
        self._status.setText(f"已保存记录：{saved.record_id}")

    def _from_last(self) -> None:
        copied = self._record_store.create_from_last(self._record_type)
        if not copied:
            self._status.setText("暂无上次记录。")
            return
        self._fill_record(copied)
        self._latest_record_id = copied.record_id
        self._status.setText("已从上次记录创建草稿。")

    def _copy_current(self) -> None:
        if not self._latest_record_id:
            self._status.setText("请先保存或从上次记录创建。")
            return
        copied = self._record_store.get(self._latest_record_id).copied_from_last()
        self._fill_record(copied)
        self._latest_record_id = copied.record_id
        self._status.setText("已复制当前记录为草稿。")

    def _export_record(self) -> None:
        if not self._latest_record_id:
            self._status.setText("请先保存记录。")
            return
        path = self._record_store.export_record_text(self._latest_record_id)
        self._status.setText(f"已导出：{path}")

    def _fill_record(self, record: CellExperimentRecord) -> None:
        self._experiment_name.setText(record.experiment_name)
        self._operator.setText(record.operator)
        for name, widget in self._fields.items():
            widget.setText(record.fields.get(name, ""))
        self._sop.setPlainText(record.free_text_sop)
        self._notes.setPlainText(record.notes)

    def _seeding_calculation_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("seedingCalculationPanel")
        layout = QHBoxLayout(frame)
        self._seed_concentration = _double("seedingCalcCurrentConcentration", 1_000_000)
        self._seed_unit = QComboBox()
        self._seed_unit.setObjectName("seedingCalcConcentrationUnit")
        self._seed_unit.addItems(("cells/mL", "cells/µL"))
        self._seed_target = _double("seedingCalcTargetCellsPerWell", 10000)
        self._seed_wells = QSpinBox()
        self._seed_wells.setObjectName("seedingCalcWellCount")
        self._seed_wells.setRange(1, 10000)
        self._seed_wells.setValue(24)
        self._seed_volume = _double("seedingCalcVolumePerWell", 0.5)
        self._seed_extra = _double("seedingCalcExtraPercent", 10)
        calculate = QPushButton("计算接种体积")
        calculate.setObjectName("seedingCalculationButton")
        calculate.clicked.connect(self._calculate_seeding)
        self._seed_result = QLabel("")
        self._seed_result.setObjectName("seedingCalculationResult")
        for widget in (
            QLabel("浓度"),
            self._seed_concentration,
            self._seed_unit,
            QLabel("目标/孔"),
            self._seed_target,
            QLabel("孔数"),
            self._seed_wells,
            QLabel("体积/孔"),
            self._seed_volume,
            QLabel("余量%"),
            self._seed_extra,
            calculate,
            self._seed_result,
        ):
            layout.addWidget(widget)
        return frame

    def _calculate_seeding(self) -> None:
        try:
            result = calculate_seeding_preparation(
                self._seed_concentration.value(),
                self._seed_unit.currentText(),
                self._seed_target.value(),
                self._seed_wells.value(),
                self._seed_volume.value(),
                self._seed_extra.value(),
            )
        except CellExperimentError as exc:
            self._seed_result.setText(str(exc))
            return
        warning = f"；{result.warnings[0]}" if result.warnings else ""
        self._seed_result.setText(
            f"总目标细胞数 {result.total_target_cells:g}；建议总配制体积 {result.suggested_total_volume:g} {result.unit}；"
            f"需要细胞悬液体积 {result.cell_suspension_volume:g} {result.unit}；需要培养基体积 {result.medium_volume:g} {result.unit}{warning}"
        )


def _double(object_name: str, value: float) -> QDoubleSpinBox:
    spin = QDoubleSpinBox()
    spin.setObjectName(object_name)
    spin.setRange(0, 1_000_000_000)
    spin.setDecimals(4)
    spin.setValue(value)
    return spin


def _note(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setObjectName("cellExperimentNote")
    return label


def _stylesheet() -> str:
    return f"""
    QWidget#labToolsCellExperimentPage {{
        background: {COLORS["background"]};
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QLabel#labToolsCellExperimentTitle {{
        color: {COLORS["bio"]};
        font-size: {FONT_SIZE["page_title"]}px;
        font-weight: 760;
    }}
    QLabel#labToolsCellExperimentDescription {{
        color: {COLORS["muted"]};
    }}
    QLabel#labToolsCellExperimentBoundary, QLabel#cellExperimentNote {{
        color: {COLORS["text"]};
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
        padding: 8px 10px;
    }}
    QFrame#cellProfileFreezingInventorySection, QFrame#seedingCalculationPanel {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    """
