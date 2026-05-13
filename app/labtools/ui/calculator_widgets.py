from __future__ import annotations

try:
    from PySide6.QtWidgets import (
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

    from app.labtools.calculators.calculator_models import CalculationError, CalculationResult
    from app.labtools.calculators.concentration_calculator import (
        calculate_mass_for_molar_solution,
        calculate_molar_concentration,
        convert_concentration,
    )
    from app.labtools.calculators.dilution_calculator import calculate_dilution
    from app.labtools.calculators.unit_conversion import (
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

        def show_result(self, result: CalculationResult) -> None:
            self.setText(result.as_text())

        def show_error(self, message: str) -> None:
            self.setText(f"输入需要调整\n{message}")


    class ConcentrationCalculatorWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsConcentrationCalculator")
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

        def _card(self, title: str) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            frame.setToolTip(title)
            return frame

        def _show(self, result: CalculationResult) -> None:
            self._result.show_result(result)

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
                result = calculate_mass_for_molar_solution(
                    self._target_molarity.text(),
                    self._target_molarity_unit.currentText(),
                    self._target_volume.text(),
                    self._target_volume_unit.currentText(),
                    self._target_mw.text(),
                    output_unit=self._mass_output_unit.currentText(),
                )
            except CalculationError as exc:
                self._show_error(exc)
                return
            self._show(result)


    class DilutionCalculatorWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsDilutionCalculator")
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
            self._output_volume_unit = _combo(supported_volume_units(), "µL")
            self._molecular_weight = _line_edit("单位类型不同时填写")
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
            grid.addWidget(QLabel("结果体积单位"), 3, 0)
            grid.addWidget(self._output_volume_unit, 3, 1)
            grid.addWidget(QLabel("分子量 g/mol"), 4, 0)
            grid.addWidget(self._molecular_weight, 4, 1, 1, 2)
            grid.addWidget(button, 5, 0, 1, 3)
            root.addWidget(card)

            self._result = ResultPanel()
            root.addWidget(self._result)
            root.addStretch(1)

        def _handle_calculate(self) -> None:
            try:
                result = calculate_dilution(
                    self._stock_value.text(),
                    self._stock_unit.currentText(),
                    self._target_value.text(),
                    self._target_unit.currentText(),
                    self._volume_value.text(),
                    self._volume_unit.currentText(),
                    molecular_weight=self._molecular_weight.text(),
                    output_volume_unit=self._output_volume_unit.currentText(),
                )
            except CalculationError as exc:
                self._result.show_error(str(exc))
                return
            self._result.show_result(result)


    class LabToolsCalculatorWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsCalculatorWorkspace")
            self.setStyleSheet(self._stylesheet())
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            tabs = QTabWidget()
            tabs.setObjectName("labToolsCalculatorTabs")
            tabs.addTab(ConcentrationCalculatorWidget(), "浓度换算")
            tabs.addTab(DilutionCalculatorWidget(), "稀释计算")
            root.addWidget(tabs)

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
            QLabel#labToolsCardTitle {{
                color: {COLORS["bio"]};
                font-weight: 700;
            }}
            QPushButton#primaryButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                min-height: {CONTROL_HEIGHT["primary"] - 12}px;
                font-weight: 700;
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
