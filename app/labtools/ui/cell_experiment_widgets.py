from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
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


def _cell_profile_button_behavior(object_name: str) -> str:
    return {
        "cellProfileNewButton": "clears_cell_profile_form",
        "cellProfileSaveButton": "upserts_cell_profile_store",
        "cellProfileCopyButton": "copies_selected_cell_profile_store",
        "cellProfileExportButton": "exports_selected_cell_profile_txt",
    }.get(object_name, "cell_profile_action")


def _cell_record_button_behavior(object_name: str) -> str:
    if object_name.startswith("cellRecordSaveButton_"):
        return "saves_cell_experiment_record"
    if object_name.startswith("cellRecordFromLastButton_"):
        return "creates_draft_from_last_cell_record"
    if object_name.startswith("cellRecordCopyButton_"):
        return "copies_current_cell_record_draft"
    if object_name.startswith("cellRecordExportButton_"):
        return "exports_cell_experiment_record_txt"
    return "cell_experiment_record_action"


CELL_RECORD_FIELD_LABELS: dict[str, str] = {
    "thaw_date": "复苏日期 / thaw_date",
    "cryovial_id": "冻存管 ID / cryovial_id",
    "cryovial_code": "冻存管编号 / cryovial_code",
    "freezing_batch_id": "冻存批次 ID / freezing_batch_id",
    "freezing_passage": "冻存时 passage / freezing_passage",
    "freezing_date": "冻存日期 / freezing_date",
    "freezing_location": "冻存位置 / freezing_location",
    "passage_after_thaw": "复苏后 passage / passage_after_thaw",
    "water_bath_temperature": "水浴温度 / water_bath_temperature",
    "thawing_time": "复苏时间 / thawing_time",
    "recovery_medium": "复苏培养基 / recovery_medium",
    "remove_dmso": "是否去除 DMSO / remove_dmso",
    "seeding_vessel": "接种容器 / seeding_vessel",
    "attachment_or_growth_status": "贴壁/生长状态 / attachment_or_growth_status",
    "contamination_observation": "污染观察 / contamination_observation",
    "passage_date": "传代日期 / passage_date",
    "passage_before": "传代前 passage / passage_before",
    "passage_after": "传代后 passage / passage_after",
    "confluence_before_passage": "传代前汇合度 / confluence_before_passage",
    "cell_status": "细胞状态 / cell_status",
    "culture_vessel": "培养容器 / culture_vessel",
    "dissociation_reagent": "消化/解离试剂 / dissociation_reagent",
    "split_ratio": "传代比例 / split_ratio",
    "new_vessel": "新培养容器 / new_vessel",
    "final_culture_volume": "最终培养体积 / final_culture_volume",
    "update_profile_passage": "同步更新档案 passage / update_profile_passage",
    "seeding_date": "接种日期 / seeding_date",
    "current_cell_concentration": "当前细胞浓度 / current_cell_concentration",
    "cell_concentration_unit": "浓度单位 / cell_concentration_unit",
    "target_cells_per_well": "每孔目标细胞数 / target_cells_per_well",
    "volume_per_well": "每孔体积 / volume_per_well",
    "well_count": "孔数 / well_count",
    "extra_percent": "额外配制比例 / extra_percent",
    "group_name": "分组名称 / group_name",
    "replicate_count": "重复数 / replicate_count",
    "plate_layout_notes": "孔板布局备注 / plate_layout_notes",
    "freezing_date": "冻存日期 / freezing_date",
    "passage": "当前 passage / passage",
    "confluence_before_freezing": "冻存前汇合度 / confluence_before_freezing",
    "cell_concentration": "细胞浓度 / cell_concentration",
    "viability_percent": "活率 % / viability_percent",
    "cryovial_count": "冻存管数量 / cryovial_count",
    "cells_per_vial": "每管细胞数 / cells_per_vial",
    "volume_per_vial": "每管体积 / volume_per_vial",
    "freezing_medium_formula": "冻存液配方 / freezing_medium_formula",
    "dmso_percent": "DMSO % / dmso_percent",
    "serum_percent": "血清 % / serum_percent",
    "cooling_method": "降温方式 / cooling_method",
    "liquid_nitrogen_tank": "液氮罐 / liquid_nitrogen_tank",
    "rack": "架 / rack",
    "box": "盒 / box",
    "start_box_position": "起始盒位 / start_box_position",
    "treatment_date": "处理日期 / treatment_date",
    "treatment_type": "处理类型 / treatment_type",
    "treatment_name": "处理名称 / treatment_name",
    "working_concentration": "工作浓度 / working_concentration",
    "solvent_or_vehicle": "溶剂/载体 / solvent_or_vehicle",
    "treatment_duration": "处理时长 / treatment_duration",
    "dose": "剂量 / dose",
    "time_point": "时间点 / time_point",
    "observation_result": "观察结果 / observation_result",
    "transfection_date": "转染日期 / transfection_date",
    "transfection_type": "转染类型 / transfection_type",
    "transfection_method": "转染方法 / transfection_method",
    "transfection_reagent_name": "转染试剂 / transfection_reagent_name",
    "dna_or_rna_name": "DNA/RNA 名称 / dna_or_rna_name",
    "dna_or_rna_amount_per_well": "每孔核酸量 / dna_or_rna_amount_per_well",
    "reagent_volume": "试剂体积 / reagent_volume",
    "detection_time_point": "检测时间点 / detection_time_point",
    "transfection_efficiency_method": "转染效率检测方法 / transfection_efficiency_method",
    "toxicity_observation": "毒性观察 / toxicity_observation",
    "operation_date": "操作日期 / operation_date",
    "operation_type": "操作类型 / operation_type",
    "operation_purpose": "操作目的 / operation_purpose",
    "key_reagents": "关键试剂 / key_reagents",
    "operation_steps": "操作步骤 / operation_steps",
    "duration": "持续时间 / duration",
    "temperature_or_culture_condition": "温度/培养条件 / temperature_or_culture_condition",
    "group_design": "分组设计 / group_design",
}


def _cell_record_field_label(field_name: str) -> str:
    return CELL_RECORD_FIELD_LABELS.get(field_name, f"{field_name.replace('_', ' ')} / {field_name}")


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
        self._record_template_widgets: list[RecordTemplateWidget] = []
        self._profile_summary_labels: dict[str, QLabel] = {}
        self.setObjectName("labToolsCellExperimentPage")
        self.setStyleSheet(_stylesheet())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("cellExperimentWorkspaceScroll")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(self._scroll_area)

        content = QWidget()
        content.setObjectName("cellExperimentWorkspaceContent")
        self._scroll_area.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["lg"])

        title = QLabel("细胞实验 / Cell Experiment")
        title.setObjectName("labToolsCellExperimentTitle")
        description = QLabel("细胞信息、实验记录模板与结果处理工具的独立工作区。")
        description.setObjectName("labToolsCellExperimentDescription")
        description.setWordWrap(True)
        status_row = QHBoxLayout()
        status_row.addWidget(_chip("Developer Preview / 本地测试版", "available"))
        status_row.addWidget(_chip("记录保存需适配", "warning"))
        status_row.addWidget(_chip("结果处理仅外部能力配置", "planned"))
        status_row.addStretch(1)

        boundary = QLabel("细胞状态和实验记录需由实验人员复核；当前首屏按 UI-C1c3 Figma 结构恢复，真实记录和图像分析入口在下方后端接线区验证。")
        boundary.setObjectName("labToolsCellExperimentBoundary")
        boundary.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(status_row)
        layout.addWidget(boundary)

        layout.addLayout(self._workspace_nav_row())
        layout.addLayout(self._figma_workspace_row())
        layout.addWidget(self._timeline_panel())

        adapter_title = QLabel("后端接线验证区")
        adapter_title.setObjectName("cellExperimentBackendTitle")
        layout.addWidget(adapter_title)
        self._backend_tabs = QTabWidget()
        self._backend_tabs.setObjectName("cellExperimentTopTabs")
        self._backend_tabs.addTab(self._records_tab(), "细胞实验记录")
        self._backend_tabs.addTab(self._image_analysis_tab(), "细胞图像分析")
        layout.addWidget(self._backend_tabs)

    def _workspace_nav_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(SPACING["sm"])
        for title, subtitle, state in (
            ("细胞信息", "细胞状态与动态信息", "active"),
            ("实验记录", "模板化实验记录入口", "neutral"),
            ("结果处理", "图像与结果处理工具", "neutral"),
        ):
            card = QFrame()
            card.setObjectName("cellExperimentNavCard")
            card.setProperty("state", state)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
            label = QLabel(title)
            label.setObjectName("cellExperimentNavTitle")
            sub = QLabel(subtitle)
            sub.setObjectName("cellExperimentNavSubtitle")
            card_layout.addWidget(label)
            card_layout.addWidget(sub)
            row.addWidget(card, 1)
        return row

    def _figma_workspace_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(SPACING["md"])
        row.addWidget(self._cell_profile_summary_panel(), 3)
        row.addWidget(self._record_templates_summary_panel(), 4)
        row.addWidget(self._result_processing_panel(), 3)
        return row

    def _cell_profile_summary_panel(self) -> QFrame:
        panel = _panel("细胞信息 / Cell Profile")
        layout = panel.layout()
        assert isinstance(layout, QVBoxLayout)
        for label, key in (
            ("细胞名称", "cell_name"),
            ("来源", "source"),
            ("模型", "cell_type"),
            ("当前 passage", "current_passage"),
            ("培养条件", "culture_condition"),
        ):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            value_label = QLabel("")
            value_label.setObjectName(f"cellProfileSummary_{key}")
            row.addWidget(value_label, 1)
            layout.addLayout(row)
            self._profile_summary_labels[key] = value_label
        state_row = QHBoxLayout()
        state_row.addWidget(QLabel("当前状态"))
        for label, state in (("培养中", "available"), ("冻存", "muted"), ("复苏", "muted"), ("传代后", "muted"), ("待处理", "muted")):
            state_row.addWidget(_chip(label, state))
        state_row.addStretch(1)
        layout.addLayout(state_row)

        layout.addWidget(_section_label("动态状态 / Status Overview"))
        for label, value, state in (
            ("冻存批次", "未记录", "warning"),
            ("冻存管", "未记录", "warning"),
            ("污染检查", "未记录", "planned"),
            ("支原体", "未记录", "planned"),
            ("形态观察", "待人工记录", "planned"),
            ("汇合度", "待人工记录", "planned"),
        ):
            layout.addLayout(_row(label, value, state))
        layout.addWidget(_note("未选择或未保存细胞档案时，本区只显示模板字段，不展示虚假细胞信息。"))
        self._refresh_profile_summary_panel()
        return panel

    def _refresh_profile_summary_panel(self) -> None:
        labels = getattr(self, "_profile_summary_labels", {})
        if not labels:
            return
        profiles = list(self._profile_store.load())
        if not profiles:
            values = {
                "cell_name": "未选择细胞档案",
                "source": "模板字段",
                "cell_type": "模板字段",
                "current_passage": "未记录",
                "culture_condition": "保存细胞档案后显示真实培养条件",
            }
        else:
            profile = profiles[0]
            values = {
                "cell_name": profile.cell_name,
                "source": profile.source or "未记录",
                "cell_type": profile.cell_type or "未记录",
                "current_passage": profile.current_passage or "未记录",
                "culture_condition": ", ".join(part for part in (profile.basal_medium, profile.serum_type, profile.culture_temperature, f"{profile.co2_percent}% CO2" if profile.co2_percent else "") if part) or "未记录",
            }
        for key, value in values.items():
            if key in labels:
                labels[key].setText(value)

    def _record_templates_summary_panel(self) -> QFrame:
        panel = _panel("细胞实验记录 / Experiment Record Templates")
        layout = panel.layout()
        assert isinstance(layout, QVBoxLayout)
        grid = QGridLayout()
        grid.setSpacing(SPACING["sm"])
        templates = (
            ("传代", "记录传代比例、消化时间、接种密度", "仅壳层"),
            ("复苏", "记录复苏批次、复苏时间、培养条件", "仅壳层"),
            ("冻存", "记录冻存批次、冻存管、冻存液", "仅壳层"),
            ("接种", "记录接种密度、孔板格式、体积", "计算辅助可用"),
            ("给药 / 处理", "记录处理条件、剂量、时间点", "仅壳层"),
            ("转染", "记录转染试剂、核酸量、时间点", "仅壳层"),
        )
        for index, (title, text, status) in enumerate(templates):
            grid.addWidget(_template_card(title, text, status, index == 3, self._open_records_backend), index // 2, index % 2)
        layout.addLayout(grid)

        from_last = QFrame()
        from_last.setObjectName("cellExperimentFromLastCard")
        from_last_layout = QHBoxLayout(from_last)
        from_last_layout.addWidget(QLabel("从上次记录创建"))
        from_last_layout.addWidget(_chip("需要历史记录存储", "warning"))
        from_last_layout.addStretch(1)
        create = QPushButton("创建记录 - 暂不可用")
        create.setObjectName("cellExperimentCreateFromLastDisabledButton")
        create.setEnabled(False)
        from_last_layout.addWidget(create)
        layout.addWidget(from_last)
        layout.addWidget(_note("当前项目暂无保存的细胞实验记录；记录保存需要后续 CellExperimentRecordStore 适配检查。"))
        return panel

    def _result_processing_panel(self) -> QFrame:
        panel = _panel("细胞结果处理工具 / Result Processing")
        layout = panel.layout()
        assert isinstance(layout, QVBoxLayout)
        for title, text in (
            ("划痕实验", "可设计图像标注与复核流程；不执行自动 ROI。"),
            ("Transwell 实验", "可设计计数复核界面；不执行自动细胞计数。"),
            ("荧光 / 染色图像", "可设计图像预览与人工标注；不执行自动分割。"),
        ):
            layout.addWidget(_result_entry(title, text))
        engine = QFrame()
        engine.setObjectName("cellExperimentEngineCallout")
        engine_layout = QVBoxLayout(engine)
        engine_layout.addWidget(_section_label("ImageJ / Fiji 外部引擎"))
        for label, value in (
            ("检测状态", "未在此页检测"),
            ("配置入口", "设置中心 > 外部能力"),
            ("运行状态", "暂不执行图像分析"),
        ):
            engine_layout.addLayout(_row(label, value))
        settings = QPushButton("前往设置中心 - 需路由")
        settings.setObjectName("cellExperimentSettingsRouteDisabledButton")
        settings.setEnabled(False)
        run = QPushButton("运行图像分析 - 暂未开放")
        run.setObjectName("cellExperimentRunImageAnalysisDisabledButton")
        run.setEnabled(False)
        actions = QHBoxLayout()
        actions.addWidget(settings)
        actions.addWidget(run)
        engine_layout.addLayout(actions)
        layout.addWidget(engine)
        layout.addWidget(_note("ImageJ/Fiji 仅作为外部引擎接入；当前不执行 macro、不提供自动 ROI、自动计数或结果解析。"))
        return panel

    def _timeline_panel(self) -> QFrame:
        panel = _panel("状态时间线 / State Timeline")
        layout = panel.layout()
        assert isinstance(layout, QVBoxLayout)
        layout.addWidget(_note("暂无可读取的细胞实验记录。接入记录模型后，这里将显示传代、复苏、冻存、接种、处理和转染事件。"))
        return panel

    def _open_records_backend(self) -> None:
        tabs = getattr(self, "_backend_tabs", None)
        if tabs is None:
            return
        tabs.setCurrentIndex(0)
        self._scroll_area.ensureWidgetVisible(tabs)

    def _records_tab(self) -> QWidget:
        tabs = QTabWidget()
        tabs.setObjectName("cellExperimentRecordTabs")
        profile_widget = CellProfileWidget(self._profile_store, self._inventory_store, self._record_store)
        profile_widget.profiles_changed.connect(self._refresh_record_profile_selectors)
        tabs.addTab(profile_widget, "细胞档案")
        for record_type, label in CELL_EXPERIMENT_RECORD_TYPES[1:]:
            record_widget = RecordTemplateWidget(record_type, label, self._profile_store, self._record_store, self._inventory_store)
            self._record_template_widgets.append(record_widget)
            tabs.addTab(record_widget, label)
        return tabs

    def _refresh_record_profile_selectors(self) -> None:
        for record_widget in self._record_template_widgets:
            record_widget.refresh_profiles()
        self._refresh_profile_summary_panel()

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
    profiles_changed = Signal()

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
            button.setProperty("buttonBehavior", _cell_profile_button_behavior(name))
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
        create.setProperty("buttonBehavior", "creates_freezing_batch_and_cryovial_inventory")
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
        update.setProperty("buttonBehavior", "updates_cryovial_location_and_status")
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
        self.profiles_changed.emit()

    def _copy_profile(self) -> None:
        if not self._current_profile_id:
            self._status.setText("请先选择细胞档案。")
            return
        copied = self._profile_store.copy_profile(self._current_profile_id)
        self._current_profile_id = copied.cell_profile_id
        self._fill_profile(copied)
        self._refresh_profiles()
        self._status.setText(f"已复制细胞档案：{copied.cell_name}")
        self.profiles_changed.emit()

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
            grid.addWidget(QLabel(_cell_record_field_label(field_name)), index // 2, (index % 2) * 2)
            grid.addWidget(edit, index // 2, (index % 2) * 2 + 1)
        root.addLayout(grid)

        if record_type == "seeding":
            root.addWidget(self._seeding_calculation_panel())

        self._sop = QTextEdit()
        self._sop.setObjectName(f"cellRecordFreeSop_{record_type}")
        self._sop.setPlaceholderText("SOP / 自由文本")
        self._notes = QTextEdit()
        self._notes.setObjectName(f"cellRecordNotes_{record_type}")
        self._notes.setPlaceholderText("备注 / notes")
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
            button.setProperty("buttonBehavior", _cell_record_button_behavior(name))
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
        calculate.setProperty("buttonBehavior", "calculates_cell_seeding_preparation_preview")
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


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("cellExperimentSectionLabel")
    label.setWordWrap(True)
    return label


def _chip(text: str, state: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("cellExperimentStatusChip")
    label.setProperty("state", state)
    return label


def _panel(title: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("cellExperimentFigmaPanel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["sm"])
    layout.addWidget(_section_label(title))
    return frame


def _row(label: str, value: str, state: str | None = None) -> QHBoxLayout:
    row = QHBoxLayout()
    name = QLabel(label)
    name.setObjectName("cellExperimentInfoLabel")
    val = QLabel(value)
    val.setObjectName("cellExperimentInfoValue")
    row.addWidget(name)
    row.addStretch(1)
    if state:
        row.addWidget(_chip(value, state))
    else:
        row.addWidget(val)
    return row


def _template_card(title: str, text: str, status: str, active_helper: bool, callback) -> QFrame:
    frame = QFrame()
    frame.setObjectName("cellExperimentTemplateCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["sm"], SPACING["sm"], SPACING["sm"], SPACING["sm"])
    heading = QLabel(title)
    heading.setObjectName("cellExperimentTemplateTitle")
    desc = QLabel(text)
    desc.setObjectName("cellExperimentTemplateDescription")
    desc.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(desc)
    layout.addWidget(_chip(status, "available" if active_helper else "muted"))
    action = QPushButton("打开接种计算辅助" if active_helper else "新建记录 - 需适配")
    action.setObjectName("cellExperimentSeedingHelperButton" if active_helper else f"cellExperimentDisabledRecordButton_{title}")
    if active_helper:
        action.clicked.connect(callback)
    else:
        action.setEnabled(False)
    layout.addWidget(action)
    return frame


def _result_entry(title: str, text: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("cellExperimentResultEntry")
    layout = QHBoxLayout(frame)
    copy = QVBoxLayout()
    heading = QLabel(title)
    heading.setObjectName("cellExperimentResultTitle")
    desc = QLabel(text)
    desc.setObjectName("cellExperimentResultDescription")
    desc.setWordWrap(True)
    copy.addWidget(heading)
    copy.addWidget(desc)
    layout.addLayout(copy, 1)
    layout.addWidget(_chip("规划中", "planned"))
    return frame


def _stylesheet() -> str:
    return f"""
    QWidget#labToolsCellExperimentPage {{
        background: {COLORS["background"]};
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["body"]}px;
    }}
    QScrollArea#cellExperimentWorkspaceScroll {{
        border: 0;
        background: {COLORS["background"]};
    }}
    QWidget#cellExperimentWorkspaceContent {{
        background: {COLORS["background"]};
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
    QLabel#cellExperimentBackendTitle, QLabel#cellExperimentSectionLabel {{
        color: {COLORS["text"]};
        font-size: {FONT_SIZE["card_title"]}px;
        font-weight: 720;
    }}
    QFrame#cellExperimentNavCard {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    QFrame#cellExperimentNavCard[state="active"] {{
        border: 1px solid {COLORS["labtools"]};
        background: {COLORS["labtools_soft"]};
    }}
    QLabel#cellExperimentNavTitle {{
        color: {COLORS["text"]};
        font-weight: 720;
    }}
    QLabel#cellExperimentNavSubtitle, QLabel#cellExperimentInfoLabel, QLabel#cellExperimentTemplateDescription, QLabel#cellExperimentResultDescription {{
        color: {COLORS["muted"]};
    }}
    QFrame#cellExperimentFigmaPanel, QFrame#cellExperimentTemplateCard, QFrame#cellExperimentResultEntry,
    QFrame#cellExperimentEngineCallout, QFrame#cellExperimentFromLastCard {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    QFrame#cellExperimentTemplateCard, QFrame#cellExperimentResultEntry, QFrame#cellExperimentEngineCallout, QFrame#cellExperimentFromLastCard {{
        padding: 6px;
    }}
    QLabel#cellExperimentInfoValue, QLabel#cellExperimentTemplateTitle, QLabel#cellExperimentResultTitle {{
        color: {COLORS["text"]};
        font-weight: 650;
    }}
    QLabel#cellExperimentStatusChip {{
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["md"]}px;
        padding: 3px 8px;
        color: {COLORS["text"]};
        background: {COLORS["surface_muted"]};
        font-size: {FONT_SIZE["caption"]}px;
    }}
    QLabel#cellExperimentStatusChip[state="available"] {{
        color: {COLORS["success"]};
        background: {COLORS["success_soft"]};
        border-color: {COLORS["success"]};
    }}
    QLabel#cellExperimentStatusChip[state="warning"] {{
        color: {COLORS["warning"]};
        background: {COLORS["warning_soft"]};
        border-color: {COLORS["warning"]};
    }}
    QLabel#cellExperimentStatusChip[state="planned"] {{
        color: {COLORS["labtools"]};
        background: {COLORS["labtools_soft"]};
        border-color: {COLORS["labtools"]};
    }}
    QLabel#cellExperimentStatusChip[state="muted"] {{
        color: {COLORS["muted"]};
    }}
    QFrame#cellProfileFreezingInventorySection, QFrame#seedingCalculationPanel {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: {RADIUS["sm"]}px;
    }}
    """
