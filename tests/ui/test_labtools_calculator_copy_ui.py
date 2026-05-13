from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    return QApplication.instance() or QApplication([])


class _FakeClipboard:
    def __init__(self) -> None:
        self.text = ""

    def setText(self, value: str) -> None:
        self.text = value


def _mock_clipboard(monkeypatch):
    from app.labtools.ui import calculator_widgets

    clipboard = _FakeClipboard()
    monkeypatch.setattr(calculator_widgets.QApplication, "clipboard", staticmethod(lambda: clipboard))
    return clipboard


def test_dilution_copy_button_enables_after_success_and_writes_clipboard(qapp, monkeypatch) -> None:
    from app.labtools.ui.calculator_widgets import DilutionCalculatorWidget

    clipboard = _mock_clipboard(monkeypatch)
    widget = DilutionCalculatorWidget()
    assert widget._copy_button.isEnabled() is False
    widget._stock_value.setText("10")
    widget._stock_unit.setCurrentText("mM")
    widget._target_value.setText("1")
    widget._target_unit.setCurrentText("mM")
    widget._volume_value.setText("1000")
    widget._volume_unit.setCurrentText("µL")

    widget._handle_calculate()

    assert widget._copy_button.isEnabled() is True
    assert "C1V1" in widget._result.copyable_text()
    widget._copy_button.click()
    assert "stock volume" in clipboard.text
    assert "solvent volume" in clipboard.text
    assert "人工核对" in clipboard.text
    assert "已复制计算结果，请使用前人工核对" in widget._result.toPlainText()


def test_dilution_invalid_input_disables_copy_and_does_not_leave_success_text(qapp) -> None:
    from app.labtools.ui.calculator_widgets import DilutionCalculatorWidget

    widget = DilutionCalculatorWidget()
    widget._stock_value.setText("10")
    widget._target_value.setText("1")
    widget._target_unit.setCurrentText("mM")
    widget._volume_value.setText("1000")
    widget._volume_unit.setCurrentText("µL")
    widget._handle_calculate()
    assert widget._copy_button.isEnabled() is True

    widget._stock_value.setText("1")
    widget._target_value.setText("10")
    widget._handle_calculate()

    assert widget._copy_button.isEnabled() is False
    assert widget._result.copyable_text() == ""
    text = widget._result.toPlainText()
    assert "输入需要调整" in text
    assert "stock volume" not in text


def test_mass_molarity_copy_button_uses_formatter(qapp, monkeypatch) -> None:
    from app.labtools.ui.calculator_widgets import ConcentrationCalculatorWidget

    clipboard = _mock_clipboard(monkeypatch)
    widget = ConcentrationCalculatorWidget()
    assert widget._copy_button.isEnabled() is False
    widget._target_mw.setText("100")
    widget._target_molarity.setText("1")
    widget._target_molarity_unit.setCurrentText("mM")
    widget._target_volume.setText("10")
    widget._target_volume_unit.setCurrentText("mL")
    widget._mass_output_unit.setCurrentText("mg")

    widget._handle_mass()

    assert widget._copy_button.isEnabled() is True
    widget._copy_button.click()
    assert "MW 100 g/mol" in clipboard.text
    assert "required mass" in clipboard.text
    assert "1 mg" in clipboard.text
    assert "实验辅助计算草稿，不替代实验 SOP" in clipboard.text


def test_cell_seeding_copy_button_uses_formatter(qapp, monkeypatch) -> None:
    from app.labtools.ui.calculator_widgets import CellSeedingCalculatorWidget

    clipboard = _mock_clipboard(monkeypatch)
    widget = CellSeedingCalculatorWidget()
    assert widget._copy_button.isEnabled() is False
    widget._cell_density.setText("1000000")
    widget._density_unit.setCurrentText("cells/mL")
    widget._target_cells.setText("10000")
    widget._wells.setText("24")
    widget._volume_per_well.setText("500")
    widget._volume_unit.setCurrentText("µL")
    widget._overage_percent.setText("10")

    widget._handle_calculate()

    assert widget._copy_button.isEnabled() is True
    widget._copy_button.click()
    assert "total cells" in clipboard.text
    assert "suspension volume" in clipboard.text
    assert "medium volume" in clipboard.text
    assert "人工核对" in clipboard.text


def test_calculator_copy_text_excludes_formal_or_clinical_claims(qapp) -> None:
    from app.labtools.ui.calculator_widgets import CellSeedingCalculatorWidget, DilutionCalculatorWidget

    widgets = [DilutionCalculatorWidget(), CellSeedingCalculatorWidget()]
    widgets[0]._stock_value.setText("10")
    widgets[0]._target_value.setText("1")
    widgets[0]._target_unit.setCurrentText("mM")
    widgets[0]._volume_value.setText("1000")
    widgets[0]._volume_unit.setCurrentText("µL")
    widgets[0]._handle_calculate()
    widgets[1]._cell_density.setText("1000000")
    widgets[1]._target_cells.setText("10000")
    widgets[1]._wells.setText("1")
    widgets[1]._volume_per_well.setText("500")
    widgets[1]._handle_calculate()

    combined = "\n".join(widget._result.copyable_text() for widget in widgets)
    assert "实验辅助计算草稿" in combined
    for forbidden in ("正式 SOP", "临床诊断", "production", "raw dataclass", "traceback"):
        assert forbidden not in combined.lower()
