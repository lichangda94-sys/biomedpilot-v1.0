from __future__ import annotations

from collections.abc import Callable

try:
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
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


    class LabToolsCalculatorWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsCalculatorWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._latest_record: CalculationRecord | None = None
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["lg"])
            root.setSpacing(SPACING["md"])
            self._record_summary = QLabel("最近一次计算：暂无")
            self._record_summary.setObjectName("labToolsRecordSummary")
            self._record_summary.setWordWrap(True)
            title = QLabel("实验计算器中心")
            title.setObjectName("labToolsCalculatorTitle")
            subtitle = QLabel("本地辅助计算：稀释、摩尔浓度换算、细胞接种。结果仅供实验前核对，不替代实验 SOP。")
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
            tabs.addTab(ConcentrationCalculatorWidget(on_record=self._set_latest_record), "浓度换算")
            tabs.addTab(DilutionCalculatorWidget(on_record=self._set_latest_record), "稀释计算")
            tabs.addTab(SolutionPreparationCalculatorWidget(on_record=self._set_latest_record), "溶液配制")
            tabs.addTab(CellSeedingCalculatorWidget(on_record=self._set_latest_record), "细胞接种")
            tabs.addTab(QpcrMixCalculatorWidget(on_record=self._set_latest_record), "qPCR 配液")
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
