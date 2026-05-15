from __future__ import annotations

from collections.abc import Callable

try:
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.calculators.calculation_record import CalculationRecord
    from app.labtools.calculators.calculator_models import CalculationError, CalculationResult
    from app.labtools.calculators.concentration_calculator import (
        calculate_molar_concentration,
        convert_concentration,
    )
    from app.labtools.calculators.experiment_calculator_center import (
        CALCULATION_REVIEW_NOTICE,
        CellSeedingInput,
        DilutionInput,
        MassMolarityInput,
        QpcrMixInput,
        calculate_cell_seeding_v1,
        calculate_dilution_v1,
        calculate_mass_molarity_v1,
        calculate_qpcr_mix_v1,
        format_cell_seeding_copy_text,
        format_dilution_copy_text,
        format_mass_molarity_copy_text,
    )
    from app.labtools.calculators.solution_preparation_calculator import calculate_solution_preparation
    from app.labtools.calculators.unit_conversion import (
        supported_cell_density_units,
        supported_concentration_units,
        supported_mass_units,
        supported_volume_units,
    )
    from app.labtools.reagent_templates import (
        CommercialReagentInfo,
        PreparationRequest,
        PHRecord,
        ReagentComponent,
        ReagentTemplate,
        ReagentTemplateError,
        ReagentTemplateStore,
        calculate_preparation,
    )
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    def _line_edit(placeholder: str) -> QLineEdit:
        field = QLineEdit()
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


    class ResultPanel(QTextEdit):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsResultPanel")
            self.setReadOnly(True)
            self.setMinimumHeight(180)
            self.setText("填写参数后点击计算。")
            self._copyable_text = ""
            self._copy_button: QPushButton | None = None

        def show_result(self, result: CalculationResult) -> None:
            self.setText(result.as_text())
            self.set_copyable_text(result.as_text())

        def show_text_result(self, text: str, *, copyable_text: str = "") -> None:
            self.setText(text)
            self.set_copyable_text(copyable_text)

        def show_error(self, message: str) -> None:
            self.setText(f"输入需要调整\n{message}")
            self.set_copyable_text("")

        def set_copy_button(self, button: QPushButton) -> None:
            self._copy_button = button
            self._copy_button.setEnabled(False)
            self._copy_button.clicked.connect(self.copy_to_clipboard)

        def set_copyable_text(self, text: str) -> None:
            self._copyable_text = text.strip()
            if self._copy_button is not None:
                self._copy_button.setEnabled(bool(self._copyable_text))

        def copyable_text(self) -> str:
            return self._copyable_text

        def copy_to_clipboard(self) -> bool:
            if not self._copyable_text:
                return False
            QApplication.clipboard().setText(self._copyable_text)
            base_text = self.toPlainText().split("\n\n已复制计算结果，请使用前人工核对。")[0]
            self.setText(f"{base_text}\n\n已复制计算结果，请使用前人工核对。")
            return True


    def _copy_button_for(panel: ResultPanel) -> QPushButton:
        button = QPushButton("复制结果")
        button.setObjectName("secondaryButton")
        panel.set_copy_button(button)
        return button


    class ConcentrationCalculatorWidget(QWidget):
        def __init__(self, on_record: Callable[[CalculationRecord], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsConcentrationCalculator")
            self._on_record = on_record
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])

            title = QLabel("浓度 / 分子量 / 摩尔浓度换算")
            title.setObjectName("labToolsSectionTitle")
            root.addWidget(title)

            conversion = self._card("浓度单位换算")
            conversion_grid = QGridLayout(conversion)
            conversion_grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._concentration_value = _line_edit("例如 10")
            self._from_unit = _combo(supported_concentration_units(), "mg/mL")
            self._to_unit = _combo(supported_concentration_units(), "µM")
            self._molecular_weight = _line_edit("跨质量浓度和摩尔浓度时必填")
            convert_button = QPushButton("换算浓度")
            convert_button.setObjectName("primaryButton")
            convert_button.clicked.connect(self._handle_convert)
            conversion_grid.addWidget(QLabel("输入浓度"), 0, 0)
            conversion_grid.addWidget(self._concentration_value, 0, 1)
            conversion_grid.addWidget(self._from_unit, 0, 2)
            conversion_grid.addWidget(QLabel("目标单位"), 1, 0)
            conversion_grid.addWidget(self._to_unit, 1, 1)
            conversion_grid.addWidget(QLabel("分子量 g/mol"), 2, 0)
            conversion_grid.addWidget(self._molecular_weight, 2, 1, 1, 2)
            conversion_grid.addWidget(convert_button, 3, 0, 1, 3)
            root.addWidget(conversion)

            molarity = self._card("由称量质量计算摩尔浓度")
            molarity_grid = QGridLayout(molarity)
            molarity_grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._mass_value = _line_edit("例如 5")
            self._mass_unit = _combo(supported_mass_units(), "mg")
            self._volume_value = _line_edit("例如 10")
            self._volume_unit = _combo(supported_volume_units(), "mL")
            self._mass_mw = _line_edit("例如 180.16")
            self._molarity_output_unit = _combo(("M", "mM", "µM", "nM"), "µM")
            molarity_button = QPushButton("计算摩尔浓度")
            molarity_button.setObjectName("primaryButton")
            molarity_button.clicked.connect(self._handle_molarity)
            molarity_grid.addWidget(QLabel("质量"), 0, 0)
            molarity_grid.addWidget(self._mass_value, 0, 1)
            molarity_grid.addWidget(self._mass_unit, 0, 2)
            molarity_grid.addWidget(QLabel("体积"), 1, 0)
            molarity_grid.addWidget(self._volume_value, 1, 1)
            molarity_grid.addWidget(self._volume_unit, 1, 2)
            molarity_grid.addWidget(QLabel("分子量 g/mol"), 2, 0)
            molarity_grid.addWidget(self._mass_mw, 2, 1)
            molarity_grid.addWidget(self._molarity_output_unit, 2, 2)
            molarity_grid.addWidget(molarity_button, 3, 0, 1, 3)
            root.addWidget(molarity)

            mass = self._card("由摩尔浓度计算称量质量")
            mass_grid = QGridLayout(mass)
            mass_grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._target_molarity = _line_edit("例如 100")
            self._target_molarity_unit = _combo(("M", "mM", "µM", "nM"), "µM")
            self._target_volume = _line_edit("例如 1")
            self._target_volume_unit = _combo(supported_volume_units(), "mL")
            self._target_mw = _line_edit("例如 180.16")
            self._mass_output_unit = _combo(supported_mass_units(), "µg")
            mass_button = QPushButton("计算称量质量")
            mass_button.setObjectName("primaryButton")
            mass_button.clicked.connect(self._handle_mass)
            mass_grid.addWidget(QLabel("目标浓度"), 0, 0)
            mass_grid.addWidget(self._target_molarity, 0, 1)
            mass_grid.addWidget(self._target_molarity_unit, 0, 2)
            mass_grid.addWidget(QLabel("目标体积"), 1, 0)
            mass_grid.addWidget(self._target_volume, 1, 1)
            mass_grid.addWidget(self._target_volume_unit, 1, 2)
            mass_grid.addWidget(QLabel("分子量 g/mol"), 2, 0)
            mass_grid.addWidget(self._target_mw, 2, 1)
            mass_grid.addWidget(self._mass_output_unit, 2, 2)
            mass_grid.addWidget(mass_button, 3, 0, 1, 3)
            root.addWidget(mass)

            self._result = ResultPanel()
            root.addWidget(self._result)
            self._copy_button = _copy_button_for(self._result)
            root.addWidget(self._copy_button)

        def _card(self, title: str) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            frame.setToolTip(title)
            return frame

        def _show(self, result: CalculationResult) -> None:
            self._result.show_result(result)
            if self._on_record is not None:
                self._on_record(result.to_record(result.title))

        def _show_error(self, exc: CalculationError) -> None:
            self._result.show_error(str(exc))

        def _handle_convert(self) -> None:
            try:
                result = convert_concentration(
                    self._concentration_value.text(),
                    self._from_unit.currentText(),
                    self._to_unit.currentText(),
                    molecular_weight=self._molecular_weight.text(),
                )
            except CalculationError as exc:
                self._show_error(exc)
                return
            self._show(result)

        def _handle_molarity(self) -> None:
            try:
                result = calculate_molar_concentration(
                    self._mass_value.text(),
                    self._mass_unit.currentText(),
                    self._volume_value.text(),
                    self._volume_unit.currentText(),
                    self._mass_mw.text(),
                    output_unit=self._molarity_output_unit.currentText(),
                )
            except CalculationError as exc:
                self._show_error(exc)
                return
            self._show(result)

        def _handle_mass(self) -> None:
            try:
                input_data = MassMolarityInput(
                    molecular_weight=self._target_mw.text(),
                    target_concentration=self._target_molarity.text(),
                    concentration_unit=self._target_molarity_unit.currentText(),
                    final_volume=self._target_volume.text(),
                    volume_unit=self._target_volume_unit.currentText(),
                    output_mass_unit=self._mass_output_unit.currentText(),
                )
                result = calculate_mass_molarity_v1(input_data)
            except Exception as exc:  # pragma: no cover - defensive UI guard
                self._result.show_error(str(exc))
                return
            self._result.show_text_result(result.as_text(), copyable_text=format_mass_molarity_copy_text(input_data, result))


    class DilutionCalculatorWidget(QWidget):
        def __init__(self, on_record: Callable[[CalculationRecord], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsDilutionCalculator")
            self._on_record = on_record
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            title = QLabel("C1V1 = C2V2 稀释计算")
            title.setObjectName("labToolsSectionTitle")
            root.addWidget(title)

            card = QFrame()
            card.setObjectName("labToolsCard")
            grid = QGridLayout(card)
            grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._stock_value = _line_edit("例如 10")
            self._stock_unit = _combo(supported_concentration_units(), "mM")
            self._target_value = _line_edit("例如 100")
            self._target_unit = _combo(supported_concentration_units(), "µM")
            self._volume_value = _line_edit("例如 1")
            self._volume_unit = _combo(supported_volume_units(), "mL")
            button = QPushButton("计算稀释体积")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_calculate)
            grid.addWidget(QLabel("原液浓度"), 0, 0)
            grid.addWidget(self._stock_value, 0, 1)
            grid.addWidget(self._stock_unit, 0, 2)
            grid.addWidget(QLabel("目标浓度"), 1, 0)
            grid.addWidget(self._target_value, 1, 1)
            grid.addWidget(self._target_unit, 1, 2)
            grid.addWidget(QLabel("目标体积"), 2, 0)
            grid.addWidget(self._volume_value, 2, 1)
            grid.addWidget(self._volume_unit, 2, 2)
            grid.addWidget(button, 3, 0, 1, 3)
            root.addWidget(card)

            self._result = ResultPanel()
            root.addWidget(self._result)
            self._copy_button = _copy_button_for(self._result)
            root.addWidget(self._copy_button)
            root.addStretch(1)

        def _handle_calculate(self) -> None:
            try:
                input_data = DilutionInput(
                    stock_concentration=self._stock_value.text(),
                    stock_unit=self._stock_unit.currentText(),
                    target_concentration=self._target_value.text(),
                    target_unit=self._target_unit.currentText(),
                    final_volume=self._volume_value.text(),
                    final_volume_unit=self._volume_unit.currentText(),
                )
                result = calculate_dilution_v1(input_data)
            except Exception as exc:  # pragma: no cover - defensive UI guard
                self._result.show_error(str(exc))
                return
            self._result.show_text_result(result.as_text(), copyable_text=format_dilution_copy_text(input_data, result))


    class SolutionPreparationCalculatorWidget(QWidget):
        def __init__(self, on_record: Callable[[CalculationRecord], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsSolutionPreparationCalculator")
            self._on_record = on_record
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            title = QLabel("溶液配制计算")
            title.setObjectName("labToolsSectionTitle")
            root.addWidget(title)

            card = QFrame()
            card.setObjectName("labToolsCard")
            grid = QGridLayout(card)
            grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._concentration_value = _line_edit("例如 1")
            self._concentration_unit = _combo(supported_concentration_units(), "mg/mL")
            self._volume_value = _line_edit("例如 10")
            self._volume_unit = _combo(supported_volume_units(), "mL")
            self._molecular_weight = _line_edit("摩尔浓度配制时必填")
            self._mass_unit = _combo(supported_mass_units(), "mg")
            button = QPushButton("计算配制用量")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_calculate)
            grid.addWidget(QLabel("目标浓度"), 0, 0)
            grid.addWidget(self._concentration_value, 0, 1)
            grid.addWidget(self._concentration_unit, 0, 2)
            grid.addWidget(QLabel("目标体积"), 1, 0)
            grid.addWidget(self._volume_value, 1, 1)
            grid.addWidget(self._volume_unit, 1, 2)
            grid.addWidget(QLabel("分子量 g/mol"), 2, 0)
            grid.addWidget(self._molecular_weight, 2, 1)
            grid.addWidget(QLabel("质量单位"), 3, 0)
            grid.addWidget(self._mass_unit, 3, 1)
            grid.addWidget(button, 4, 0, 1, 3)
            root.addWidget(card)

            self._result = ResultPanel()
            root.addWidget(self._result)
            self._copy_button = _copy_button_for(self._result)
            root.addWidget(self._copy_button)
            root.addStretch(1)

        def _handle_calculate(self) -> None:
            try:
                result = calculate_solution_preparation(
                    self._concentration_value.text(),
                    self._concentration_unit.currentText(),
                    self._volume_value.text(),
                    self._volume_unit.currentText(),
                    molecular_weight=self._molecular_weight.text(),
                    output_mass_unit=self._mass_unit.currentText(),
                )
            except CalculationError as exc:
                self._result.show_error(str(exc))
                return
            self._result.show_result(result)
            if self._on_record is not None:
                self._on_record(result.to_record(result.title))


    class CellSeedingCalculatorWidget(QWidget):
        def __init__(self, on_record: Callable[[CalculationRecord], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsCellSeedingCalculator")
            self._on_record = on_record
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            title = QLabel("细胞接种计算")
            title.setObjectName("labToolsSectionTitle")
            root.addWidget(title)

            card = QFrame()
            card.setObjectName("labToolsCard")
            grid = QGridLayout(card)
            grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._cell_density = _line_edit("例如 1000000")
            self._density_unit = _combo(supported_cell_density_units(), "cells/mL")
            self._target_cells = _line_edit("例如 10000")
            self._wells = _line_edit("例如 24")
            self._volume_per_well = _line_edit("例如 500")
            self._volume_per_well.setText("500")
            self._volume_unit = _combo(supported_volume_units(), "µL")
            self._overage_percent = _line_edit("默认 10")
            self._overage_percent.setText("10")
            button = QPushButton("计算接种体积")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_calculate)
            grid.addWidget(QLabel("当前细胞悬液浓度"), 0, 0)
            grid.addWidget(self._cell_density, 0, 1)
            grid.addWidget(self._density_unit, 0, 2)
            grid.addWidget(QLabel("目标每孔细胞数"), 1, 0)
            grid.addWidget(self._target_cells, 1, 1, 1, 2)
            grid.addWidget(QLabel("孔数"), 2, 0)
            grid.addWidget(self._wells, 2, 1, 1, 2)
            grid.addWidget(QLabel("每孔体积"), 3, 0)
            grid.addWidget(self._volume_per_well, 3, 1)
            grid.addWidget(self._volume_unit, 3, 2)
            grid.addWidget(QLabel("overage 比例 %"), 4, 0)
            grid.addWidget(self._overage_percent, 4, 1, 1, 2)
            grid.addWidget(button, 5, 0, 1, 3)
            root.addWidget(card)

            self._result = ResultPanel()
            root.addWidget(self._result)
            self._copy_button = _copy_button_for(self._result)
            root.addWidget(self._copy_button)
            root.addStretch(1)

        def _handle_calculate(self) -> None:
            try:
                input_data = CellSeedingInput(
                    current_cell_concentration=self._cell_density.text(),
                    concentration_unit=self._density_unit.currentText(),
                    target_cells_per_well=self._target_cells.text(),
                    well_count=self._wells.text(),
                    volume_per_well=self._volume_per_well.text(),
                    volume_unit=self._volume_unit.currentText(),
                    overage_percentage=self._overage_percent.text(),
                )
                result = calculate_cell_seeding_v1(input_data)
            except Exception as exc:  # pragma: no cover - defensive UI guard
                self._result.show_error(str(exc))
                return
            self._result.show_text_result(result.as_text(), copyable_text=format_cell_seeding_copy_text(input_data, result))


    class QpcrMixCalculatorWidget(QWidget):
        def __init__(self, on_record: Callable[[CalculationRecord], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsQpcrMixCalculator")
            self._on_record = on_record
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            title = QLabel("qPCR 配液计算")
            title.setObjectName("labToolsSectionTitle")
            root.addWidget(title)

            card = QFrame()
            card.setObjectName("labToolsCard")
            grid = QGridLayout(card)
            grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._reactions = _line_edit("例如 24")
            self._reaction_volume = _line_edit("例如 20")
            self._master_mix_value = _line_edit("例如 10 或 50")
            self._master_mix_mode = _combo(("体积（µL）", "比例（%）"), "体积（µL）")
            self._forward = _line_edit("例如 0.4")
            self._reverse = _line_edit("例如 0.4")
            self._template = _line_edit("例如 2")
            self._loss_percent = _line_edit("默认 10")
            self._loss_percent.setText("10")
            button = QPushButton("计算配液用量")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_calculate)
            grid.addWidget(QLabel("反应数"), 0, 0)
            grid.addWidget(self._reactions, 0, 1, 1, 2)
            grid.addWidget(QLabel("单反应总体积 µL"), 1, 0)
            grid.addWidget(self._reaction_volume, 1, 1, 1, 2)
            grid.addWidget(QLabel("master mix"), 2, 0)
            grid.addWidget(self._master_mix_value, 2, 1)
            grid.addWidget(self._master_mix_mode, 2, 2)
            grid.addWidget(QLabel("forward primer µL"), 3, 0)
            grid.addWidget(self._forward, 3, 1, 1, 2)
            grid.addWidget(QLabel("reverse primer µL"), 4, 0)
            grid.addWidget(self._reverse, 4, 1, 1, 2)
            grid.addWidget(QLabel("template µL"), 5, 0)
            grid.addWidget(self._template, 5, 1, 1, 2)
            grid.addWidget(QLabel("损耗比例 %"), 6, 0)
            grid.addWidget(self._loss_percent, 6, 1, 1, 2)
            grid.addWidget(button, 7, 0, 1, 3)
            root.addWidget(card)

            self._result = ResultPanel()
            root.addWidget(self._result)
            self._copy_button = _copy_button_for(self._result)
            root.addWidget(self._copy_button)
            root.addStretch(1)

        def _handle_calculate(self) -> None:
            try:
                result = calculate_qpcr_mix_v1(
                    QpcrMixInput(
                        reactions=self._reactions.text(),
                        reaction_volume_ul=self._reaction_volume.text(),
                        master_mix_value=self._master_mix_value.text(),
                        forward_primer_ul=self._forward.text(),
                        reverse_primer_ul=self._reverse.text(),
                        template_ul=self._template.text(),
                        master_mix_mode="ratio" if self._master_mix_mode.currentText() == "比例（%）" else "volume",
                        overage_percentage=self._loss_percent.text(),
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive UI guard
                self._result.show_error(str(exc))
                return
            self._result.show_text_result(result.as_text(), copyable_text=result.as_text() if result.valid else "")


    class QuickCalculationWidget(QWidget):
        def __init__(self, on_record: Callable[[CalculationRecord], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsQuickCalculationWorkspace")
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            tabs = QTabWidget()
            tabs.setObjectName("labToolsQuickCalculatorTabs")
            tabs.addTab(ConcentrationCalculatorWidget(on_record=on_record), "浓度换算")
            tabs.addTab(DilutionCalculatorWidget(on_record=on_record), "稀释计算")
            tabs.addTab(SolutionPreparationCalculatorWidget(on_record=on_record), "溶液配制")
            root.addWidget(tabs)


    class ReagentTemplateManagerWidget(QWidget):
        def __init__(self, store: ReagentTemplateStore | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsReagentTemplateManager")
            self._store = store or ReagentTemplateStore()
            self._templates: tuple[ReagentTemplate, ...] = ()
            self._components: list[ReagentComponent] = []
            self._selected_template_id = ""
            self._build_ui()
            self.refresh_templates()
            self._handle_new_template()

        def refresh_templates(self) -> None:
            try:
                self._templates = self._store.load()
                self._status.setText(f"本地模板数：{len(self._templates)}\n路径：{self._store.resolved_path()}\n不联网、不上传、不依赖账号。")
            except ReagentTemplateError as exc:
                self._templates = ()
                self._status.setText(f"读取需要调整\n{exc}")
            self._refresh_template_list()
            self._refresh_reference_combo()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            title = QLabel("我的试剂模板")
            title.setObjectName("labToolsSectionTitle")
            note = QLabel("手动录入本实验室确认过的试剂模板；第一版不做 Excel/CSV/OCR 导入，不提供内置配方库。")
            note.setObjectName("labToolsCalculatorNotice")
            note.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(note)

            row = QHBoxLayout()
            self._template_list = QListWidget()
            self._template_list.setObjectName("reagentTemplateList")
            self._template_list.currentRowChanged.connect(self._handle_template_selected)
            row.addWidget(self._template_list, 1)

            form = QFrame()
            form.setObjectName("labToolsCard")
            form_layout = QGridLayout(form)
            form_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._name = _line_edit("例如 试剂 A")
            self._name.setObjectName("reagentTemplateNameField")
            self._default_volume = _line_edit("例如 100")
            self._default_volume.setObjectName("reagentTemplateDefaultVolumeField")
            self._default_volume_unit = _combo(supported_volume_units(), "mL")
            self._default_volume_unit.setObjectName("reagentTemplateDefaultVolumeUnitCombo")
            self._default_strength = _line_edit("例如 1X、100%、原液")
            self._default_strength.setObjectName("reagentTemplateDefaultStrengthField")
            self._notes = _line_edit("备注")
            self._notes.setObjectName("reagentTemplateNotesField")
            fields = (
                ("模板名称", self._name),
                ("默认体积", self._default_volume),
                ("体积单位", self._default_volume_unit),
                ("默认倍数/浓度", self._default_strength),
                ("备注", self._notes),
            )
            for index, (label, widget) in enumerate(fields):
                form_layout.addWidget(QLabel(label), index, 0)
                form_layout.addWidget(widget, index, 1)
            row.addWidget(form, 2)
            root.addLayout(row)

            component_card = QFrame()
            component_card.setObjectName("labToolsCard")
            component_layout = QGridLayout(component_card)
            component_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._component_name = _line_edit("组分名称")
            self._component_name.setObjectName("reagentComponentNameField")
            self._component_type = _combo(("liquid", "powder", "commercial_reagent", "solvent", "self_prepared_template"), "liquid")
            self._component_type.setObjectName("reagentComponentTypeCombo")
            self._component_amount = _line_edit("基准用量")
            self._component_amount.setObjectName("reagentComponentAmountField")
            self._component_unit = _combo(("L", "mL", "µL", "g", "mg", "µg", "M", "mM", "µM", "%", "X"), "mL")
            self._component_unit.setObjectName("reagentComponentUnitCombo")
            self._scale_volume = QCheckBox("随总量缩放")
            self._scale_volume.setObjectName("reagentComponentScaleVolumeCheck")
            self._scale_volume.setChecked(True)
            self._scale_strength = QCheckBox("按目标倍数缩放")
            self._scale_strength.setObjectName("reagentComponentScaleStrengthCheck")
            self._contributes_volume = QCheckBox("参与最终体积")
            self._contributes_volume.setObjectName("reagentComponentContributesVolumeCheck")
            self._auto_fill = QCheckBox("自动补足至最终体积")
            self._auto_fill.setObjectName("reagentComponentAutoFillCheck")
            self._reference_template = QComboBox()
            self._reference_template.setObjectName("reagentComponentReferenceTemplateCombo")
            self._component_notes = _line_edit("组分备注")
            self._component_notes.setObjectName("reagentComponentNotesField")
            self._commercial_concentration = _line_edit("商品化试剂浓度")
            self._commercial_concentration.setObjectName("reagentCommercialConcentrationField")
            self._commercial_lot = _line_edit("批号")
            self._commercial_lot.setObjectName("reagentCommercialLotField")
            self._commercial_supplier = _line_edit("供应商")
            self._commercial_supplier.setObjectName("reagentCommercialSupplierField")
            self._commercial_storage = _line_edit("保存条件")
            self._commercial_storage.setObjectName("reagentCommercialStorageField")
            self._initial_mode = _combo(("none", "percent_of_final", "fixed_amount", "note_only"), "none")
            self._initial_mode.setObjectName("reagentSolventInitialModeCombo")
            self._initial_percent = _line_edit("例如 80")
            self._initial_percent.setObjectName("reagentSolventInitialPercentField")
            self._initial_amount = _line_edit("固定初始加入量")
            self._initial_amount.setObjectName("reagentSolventInitialAmountField")
            self._initial_unit = _combo(supported_volume_units(), "mL")
            self._initial_unit.setObjectName("reagentSolventInitialUnitCombo")
            self._initial_note = _line_edit("初始加入备注")
            self._initial_note.setObjectName("reagentSolventInitialNoteField")
            component_widgets = (
                ("组分名称", self._component_name),
                ("组分类型", self._component_type),
                ("基准用量", self._component_amount),
                ("单位", self._component_unit),
                ("引用子模板", self._reference_template),
                ("备注", self._component_notes),
                ("商品化浓度", self._commercial_concentration),
                ("商品化批号", self._commercial_lot),
                ("供应商", self._commercial_supplier),
                ("保存条件", self._commercial_storage),
                ("初始加入模式", self._initial_mode),
                ("初始加入比例 %", self._initial_percent),
                ("固定初始加入量", self._initial_amount),
                ("固定初始单位", self._initial_unit),
                ("初始加入备注", self._initial_note),
            )
            for index, (label, widget) in enumerate(component_widgets):
                component_layout.addWidget(QLabel(label), index // 2 * 2, index % 2)
                component_layout.addWidget(widget, index // 2 * 2 + 1, index % 2)
            checks = QHBoxLayout()
            for check in (self._scale_volume, self._scale_strength, self._contributes_volume, self._auto_fill):
                checks.addWidget(check)
            component_layout.addLayout(checks, 16, 0, 1, 2)
            add_component = QPushButton("添加组分")
            add_component.setObjectName("reagentTemplateAddComponentButton")
            add_component.clicked.connect(self._handle_add_component)
            remove_component = QPushButton("移除最后组分")
            remove_component.setObjectName("reagentTemplateRemoveLastComponentButton")
            remove_component.clicked.connect(self._handle_remove_last_component)
            clear_components = QPushButton("清空组分")
            clear_components.setObjectName("reagentTemplateClearComponentsButton")
            clear_components.clicked.connect(self._handle_clear_components)
            component_actions = QHBoxLayout()
            component_actions.addWidget(add_component)
            component_actions.addWidget(remove_component)
            component_actions.addWidget(clear_components)
            component_actions.addStretch(1)
            component_layout.addLayout(component_actions, 17, 0, 1, 2)
            root.addWidget(component_card)

            ph_card = QFrame()
            ph_card.setObjectName("labToolsCard")
            ph_layout = QGridLayout(ph_card)
            ph_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._ph_enabled = QCheckBox("启用 pH / 调节记录")
            self._ph_enabled.setObjectName("reagentPhRecordEnabledCheck")
            self._ph_target = _line_edit("例如 7.4")
            self._ph_target.setObjectName("reagentPhTargetField")
            self._ph_measured = _line_edit("实测 pH，可选")
            self._ph_measured.setObjectName("reagentPhMeasuredField")
            self._ph_note = _line_edit("例如 使用 HCl 或 NaOH 调整，需 pH meter 实测")
            self._ph_note.setObjectName("reagentPhAdjustmentNoteField")
            self._ph_include_steps = QCheckBox("写入配制步骤")
            self._ph_include_steps.setObjectName("reagentPhIncludeStepsCheck")
            self._ph_include_steps.setChecked(True)
            ph_layout.addWidget(self._ph_enabled, 0, 0, 1, 2)
            for index, (label, widget) in enumerate(
                (
                    ("目标 pH", self._ph_target),
                    ("实测 pH", self._ph_measured),
                    ("调节说明", self._ph_note),
                ),
                start=1,
            ):
                ph_layout.addWidget(QLabel(label), index, 0)
                ph_layout.addWidget(widget, index, 1)
            ph_layout.addWidget(self._ph_include_steps, 4, 0, 1, 2)
            root.addWidget(ph_card)

            self._component_summary = QTextEdit()
            self._component_summary.setObjectName("reagentTemplateComponentSummary")
            self._component_summary.setReadOnly(True)
            self._component_summary.setMinimumHeight(120)
            root.addWidget(self._component_summary)

            actions = QHBoxLayout()
            for text, name, handler in (
                ("新建模板", "reagentTemplateNewButton", self._handle_new_template),
                ("保存模板", "reagentTemplateSaveButton", self._handle_save_template),
                ("复制模板", "reagentTemplateCopyButton", self._handle_copy_template),
                ("删除模板", "reagentTemplateDeleteButton", self._handle_delete_template),
                ("重新读取", "reagentTemplateReloadButton", self.refresh_templates),
            ):
                button = QPushButton(text)
                button.setObjectName(name)
                button.clicked.connect(handler)
                actions.addWidget(button)
            actions.addStretch(1)
            root.addLayout(actions)
            self._status = QTextEdit()
            self._status.setObjectName("reagentTemplateStatusPanel")
            self._status.setReadOnly(True)
            self._status.setMinimumHeight(110)
            root.addWidget(self._status)

        def _refresh_template_list(self) -> None:
            self._template_list.clear()
            for template in self._templates:
                self._template_list.addItem(f"{template.name} · {template.default_volume:g} {template.default_volume_unit} · {template.default_strength}")

        def _refresh_reference_combo(self) -> None:
            current = self._reference_template.currentData()
            self._reference_template.clear()
            self._reference_template.addItem("不引用", "")
            for template in self._templates:
                self._reference_template.addItem(template.name, template.template_id)
            if current:
                index = self._reference_template.findData(current)
                if index >= 0:
                    self._reference_template.setCurrentIndex(index)

        def _handle_template_selected(self, row: int) -> None:
            if row < 0 or row >= len(self._templates):
                return
            template = self._templates[row]
            self._selected_template_id = template.template_id
            self._name.setText(template.name)
            self._default_volume.setText(f"{template.default_volume:g}")
            self._default_volume_unit.setCurrentText(template.default_volume_unit)
            self._default_strength.setText(template.default_strength)
            self._notes.setText(template.notes)
            self._components = list(template.components)
            self._set_ph_record(template.ph_record)
            self._refresh_component_summary()

        def _handle_new_template(self) -> None:
            self._selected_template_id = ""
            self._name.clear()
            self._default_volume.setText("100")
            self._default_volume_unit.setCurrentText("mL")
            self._default_strength.setText("1X")
            self._notes.clear()
            self._components = []
            self._set_ph_record(None)
            self._refresh_component_summary()

        def _handle_add_component(self) -> None:
            try:
                amount = float(self._component_amount.text())
                reference_id = str(self._reference_template.currentData() or "")
                component = ReagentComponent(
                    name=self._component_name.text().strip(),
                    component_type=self._component_type.currentText(),
                    base_amount=amount,
                    unit=self._component_unit.currentText(),
                    scale_with_volume=self._scale_volume.isChecked(),
                    scale_with_strength=self._scale_strength.isChecked(),
                    contributes_to_final_volume=self._contributes_volume.isChecked(),
                    auto_fill_to_final_volume=self._auto_fill.isChecked(),
                    notes=self._component_notes.text().strip(),
                    referenced_template_id=reference_id,
                    initial_addition_mode=self._initial_mode.currentText(),
                    initial_addition_percent=float(self._initial_percent.text() or 0),
                    initial_addition_amount=float(self._initial_amount.text() or 0),
                    initial_addition_unit=self._initial_unit.currentText(),
                    initial_addition_note=self._initial_note.text().strip(),
                    commercial_info=CommercialReagentInfo(
                        concentration=self._commercial_concentration.text().strip(),
                        lot_number=self._commercial_lot.text().strip(),
                        supplier=self._commercial_supplier.text().strip(),
                        storage_condition=self._commercial_storage.text().strip(),
                        notes=self._component_notes.text().strip(),
                    )
                    if self._component_type.currentText() == "commercial_reagent"
                    else None,
                )
            except ValueError:
                self._status.setText("组分需要调整\n基准用量必须是有效数字。")
                return
            self._components.append(component)
            self._refresh_component_summary()
            self._component_name.clear()
            self._component_amount.clear()
            self._component_notes.clear()
            self._commercial_concentration.clear()
            self._commercial_lot.clear()
            self._commercial_supplier.clear()
            self._commercial_storage.clear()
            self._initial_mode.setCurrentText("none")
            self._initial_percent.clear()
            self._initial_amount.clear()
            self._initial_note.clear()

        def _handle_remove_last_component(self) -> None:
            if not self._components:
                self._status.setText("当前模板尚未添加组分。")
                return
            removed = self._components.pop()
            self._refresh_component_summary()
            self._status.setText(f"已移除最后组分：{removed.name}。保存模板后写入本地 JSON。")

        def _handle_clear_components(self) -> None:
            self._components = []
            self._refresh_component_summary()
            self._status.setText("已清空当前表单组分。保存模板后写入本地 JSON。")

        def _refresh_component_summary(self) -> None:
            if not self._components:
                self._component_summary.setText("尚未添加组分。")
                return
            lines = []
            for component in self._components:
                flags = []
                if component.scale_with_volume:
                    flags.append("随总量缩放")
                if component.scale_with_strength:
                    flags.append("按倍数缩放")
                if component.contributes_to_final_volume:
                    flags.append("参与体积")
                if component.auto_fill_to_final_volume:
                    flags.append("自动补足")
                if component.initial_addition_mode != "none":
                    flags.append(f"初始加入:{component.initial_addition_mode}")
                if component.referenced_template_id:
                    flags.append("引用子模板")
                lines.append(f"{component.name}: {component.base_amount:g} {component.unit} / {component.component_type} / {', '.join(flags) or '固定记录'}")
            ph_record = self._build_ph_record()
            if ph_record is not None:
                lines.append(f"pH / 调节记录: 目标 pH {ph_record.target_ph or '待填'} / {ph_record.adjustment_note or '无说明'}")
            self._component_summary.setText("\n".join(lines))

        def _set_ph_record(self, ph_record: PHRecord | None) -> None:
            self._ph_enabled.setChecked(ph_record is not None)
            self._ph_target.setText(ph_record.target_ph if ph_record is not None else "")
            self._ph_measured.setText(ph_record.measured_ph if ph_record is not None else "")
            self._ph_note.setText(ph_record.adjustment_note if ph_record is not None else "")
            self._ph_include_steps.setChecked(True if ph_record is None else ph_record.include_in_steps)

        def _build_ph_record(self) -> PHRecord | None:
            if not self._ph_enabled.isChecked():
                return None
            return PHRecord(
                target_ph=self._ph_target.text().strip(),
                measured_ph=self._ph_measured.text().strip(),
                adjustment_note=self._ph_note.text().strip(),
                include_in_steps=self._ph_include_steps.isChecked(),
            )

        def _build_template_from_form(self) -> ReagentTemplate:
            try:
                default_volume = float(self._default_volume.text())
            except ValueError as exc:
                raise ReagentTemplateError("默认配制体积必须是有效数字。") from exc
            if self._selected_template_id:
                existing = next((template for template in self._templates if template.template_id == self._selected_template_id), None)
                created_at = existing.created_at if existing is not None else ""
                return ReagentTemplate(
                    template_id=self._selected_template_id,
                    name=self._name.text().strip(),
                    default_volume=default_volume,
                    default_volume_unit=self._default_volume_unit.currentText(),
                    default_strength=self._default_strength.text().strip() or "1X",
                    notes=self._notes.text().strip(),
                    components=tuple(self._components),
                    ph_record=self._build_ph_record(),
                    created_at=created_at,
                    updated_at=created_at,
                )
            return ReagentTemplate.create(
                name=self._name.text().strip(),
                default_volume=default_volume,
                default_volume_unit=self._default_volume_unit.currentText(),
                default_strength=self._default_strength.text().strip() or "1X",
                notes=self._notes.text().strip(),
                components=tuple(self._components),
                ph_record=self._build_ph_record(),
            )

        def _handle_save_template(self) -> None:
            try:
                template = self._store.upsert_template(self._build_template_from_form())
            except ReagentTemplateError as exc:
                self._status.setText(f"保存需要调整\n{exc}")
                return
            self._selected_template_id = template.template_id
            self.refresh_templates()
            self._status.setText(f"模板已保存\n名称：{template.name}\ntemplate_id：{template.template_id}\n路径：{self._store.resolved_path()}\n本地 JSON 保存，不联网、不上传。")

        def _handle_copy_template(self) -> None:
            if not self._selected_template_id:
                self._status.setText("请先选择要复制的模板。")
                return
            try:
                copied = self._store.copy_template(self._selected_template_id)
            except ReagentTemplateError as exc:
                self._status.setText(f"复制需要调整\n{exc}")
                return
            self.refresh_templates()
            self._status.setText(f"模板已复制\n名称：{copied.name}\ntemplate_id：{copied.template_id}")

        def _handle_delete_template(self, _checked: bool = False, *, confirmed: bool = False) -> None:
            if not self._selected_template_id:
                self._status.setText("请先选择要删除的模板。")
                return
            if not confirmed:
                answer = QMessageBox.question(self, "确认删除模板", "删除模板前请确认。此操作只影响本地 JSON。")
                if answer != QMessageBox.Yes:
                    self._status.setText("已取消删除。")
                    return
            try:
                self._store.delete_template(self._selected_template_id, confirmed=True)
            except ReagentTemplateError as exc:
                self._status.setText(f"删除需要调整\n{exc}")
                return
            self._selected_template_id = ""
            self._components = []
            self.refresh_templates()
            self._status.setText("模板已删除。本地 JSON 已更新。")


    class ReagentPreparationWidget(QWidget):
        def __init__(self, store: ReagentTemplateStore | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsReagentPreparationWorkspace")
            self._store = store or ReagentTemplateStore()
            self._templates: tuple[ReagentTemplate, ...] = ()
            self._build_ui()
            self.refresh_templates()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            title = QLabel("本次配制")
            title.setObjectName("labToolsSectionTitle")
            note = QLabel("选择本地模板后输入本次目标体积、目标倍数和损耗系数，生成本次配制清单。")
            note.setObjectName("labToolsCalculatorNotice")
            note.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(note)

            card = QFrame()
            card.setObjectName("labToolsCard")
            grid = QGridLayout(card)
            grid.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            self._template_combo = QComboBox()
            self._template_combo.setObjectName("preparationTemplateCombo")
            self._target_volume = _line_edit("例如 75")
            self._target_volume.setObjectName("preparationTargetVolumeField")
            self._target_volume_unit = _combo(supported_volume_units(), "mL")
            self._target_volume_unit.setObjectName("preparationTargetVolumeUnitCombo")
            self._target_strength = _line_edit("例如 1X、0.5X、100%")
            self._target_strength.setObjectName("preparationTargetStrengthField")
            self._target_strength.setText("1X")
            self._overage = _line_edit("例如 10")
            self._overage.setObjectName("preparationOverageField")
            self._overage.setText("0")
            self._expand = QCheckBox("展开子模板")
            self._expand.setObjectName("preparationExpandSubtemplatesCheck")
            fields = (
                ("试剂模板", self._template_combo),
                ("目标体积", self._target_volume),
                ("体积单位", self._target_volume_unit),
                ("目标倍数/浓度", self._target_strength),
                ("损耗系数 %", self._overage),
            )
            for index, (label, widget) in enumerate(fields):
                grid.addWidget(QLabel(label), index, 0)
                grid.addWidget(widget, index, 1)
            grid.addWidget(self._expand, len(fields), 0, 1, 2)
            root.addWidget(card)

            actions = QHBoxLayout()
            reload_button = QPushButton("重新读取模板")
            reload_button.setObjectName("preparationReloadTemplatesButton")
            reload_button.clicked.connect(self.refresh_templates)
            calculate_button = QPushButton("生成本次配制清单")
            calculate_button.setObjectName("preparationCalculateButton")
            calculate_button.clicked.connect(self._handle_calculate)
            actions.addWidget(reload_button)
            actions.addWidget(calculate_button)
            actions.addStretch(1)
            root.addLayout(actions)

            self._result = QTextEdit()
            self._result.setObjectName("preparationResultPanel")
            self._result.setReadOnly(True)
            self._result.setMinimumHeight(320)
            self._result.setText("尚未生成配制清单。模板保存为本地 JSON，生成结果不联网、不上传。")
            root.addWidget(self._result, 1)

        def refresh_templates(self) -> None:
            try:
                self._templates = self._store.load()
            except ReagentTemplateError as exc:
                self._templates = ()
                self._result.setText(f"读取模板需要调整\n{exc}")
            current = self._template_combo.currentData()
            self._template_combo.clear()
            for template in self._templates:
                self._template_combo.addItem(template.name, template.template_id)
            if current:
                index = self._template_combo.findData(current)
                if index >= 0:
                    self._template_combo.setCurrentIndex(index)

        def _handle_calculate(self) -> None:
            template_id = str(self._template_combo.currentData() or "")
            if not template_id:
                self._result.setText("请先创建并选择试剂模板。")
                return
            try:
                request = PreparationRequest(
                    template_id=template_id,
                    target_volume=float(self._target_volume.text()),
                    target_volume_unit=self._target_volume_unit.currentText(),
                    target_strength=self._target_strength.text().strip() or "1X",
                    overage_percent=float(self._overage.text() or 0),
                    expand_subtemplates=self._expand.isChecked(),
                )
                result = calculate_preparation(request, self._templates)
            except ValueError:
                self._result.setText("输入需要调整\n目标体积和损耗系数必须是有效数字。")
                return
            except ReagentTemplateError as exc:
                self._result.setText(f"配制需要调整\n{exc}")
                return
            self._result.setText(result.as_text())


    class LabToolsCalculatorWidget(QWidget):
        def __init__(self, reagent_template_store: ReagentTemplateStore | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsCalculatorWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._reagent_template_store = reagent_template_store or ReagentTemplateStore()
            self._latest_record: CalculationRecord | None = None
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            self._record_summary = QLabel("最近一次计算：暂无")
            self._record_summary.setObjectName("labToolsRecordSummary")
            self._record_summary.setWordWrap(True)
            title = QLabel("通用试剂计算器")
            title.setObjectName("labToolsCalculatorTitle")
            subtitle = QLabel(
                "本地通用试剂模板与分层配制计算工作台：保留浓度换算、C1V1 稀释和溶液配制快速计算，"
                "并支持用户自定义试剂模板、本次配制换算、子模板展开与本地 JSON 保存。结果仅供实验前核对，不替代实验 SOP。"
            )
            subtitle.setObjectName("labToolsCalculatorNotice")
            subtitle.setWordWrap(True)
            risk = QLabel(CALCULATION_REVIEW_NOTICE)
            risk.setObjectName("labToolsCalculatorNotice")
            risk.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(subtitle)
            root.addWidget(risk)
            root.addWidget(self._record_summary)
            tabs = QTabWidget()
            tabs.setObjectName("labToolsCalculatorTabs")
            tabs.addTab(QuickCalculationWidget(on_record=self._set_latest_record), "快速计算")
            tabs.addTab(ReagentTemplateManagerWidget(self._reagent_template_store), "我的试剂模板")
            tabs.addTab(ReagentPreparationWidget(self._reagent_template_store), "本次配制")
            root.addWidget(tabs)

        def latest_record(self) -> CalculationRecord | None:
            return self._latest_record

        def _set_latest_record(self, record: CalculationRecord) -> None:
            self._latest_record = record
            self._record_summary.setText("\n".join(record.summary_lines()))

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsCalculatorWorkspace {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QFrame#labToolsCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QLabel#labToolsSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsCalculatorTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsCalculatorNotice {{
                color: {COLORS["muted"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QLabel#labToolsCardTitle {{
                color: {COLORS["bio"]};
                font-weight: 700;
            }}
            QLabel#labToolsRecordSummary {{
                color: {COLORS["muted"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QPushButton#primaryButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                min-height: {CONTROL_HEIGHT["primary"] - 12}px;
                font-weight: 700;
            }}
            QPushButton#secondaryButton {{
                color: {COLORS["bio"]};
                background: {COLORS["bio_soft"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                min-height: {CONTROL_HEIGHT["primary"] - 12}px;
                font-weight: 600;
            }}
            QTextEdit#labToolsResultPanel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 10px;
            }}
            """

else:  # pragma: no cover

    class LabToolsCalculatorWidget:  # type: ignore[no-redef]
        pass
