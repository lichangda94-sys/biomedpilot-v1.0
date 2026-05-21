from __future__ import annotations

import pytest

from labtools.calculators.formula_solver import (
    calculate_serial_dilution,
    convert_mass_concentration_unit,
    solve_concentration_bridge,
    solve_dilution_equation,
    solve_percent_solution,
    solve_solution_preparation_formula,
    solve_stock_working_solution,
)
from labtools.calculators.result_formatting import LOW_MASS_WARNING, LOW_VOLUME_WARNING, TINY_VALUE_WARNING
from labtools.calculators.calculator_models import CalculationError


def test_solve_concentration_bridge_can_solve_molecular_weight() -> None:
    result = solve_concentration_bridge(
        mass_concentration=1,
        mass_unit="mg/mL",
        molar_concentration=1,
        molar_unit="mM",
        molecular_weight=None,
    )

    assert result.result_value == pytest.approx(1000)
    assert result.result_unit == "g/mol"
    assert "分子量：1,000.00 g/mol" in result.as_text()


def test_solve_concentration_bridge_can_solve_mass_and_molar_concentration() -> None:
    mass_result = solve_concentration_bridge(
        mass_concentration=None,
        mass_unit="mg/mL",
        molar_concentration=1,
        molar_unit="mM",
        molecular_weight=1000,
    )
    assert mass_result.result_value == pytest.approx(1)
    assert mass_result.result_unit == "mg/mL"
    assert mass_result.record_inputs["solve_for"] == "mass_concentration"

    molar_result = solve_concentration_bridge(
        mass_concentration=1,
        mass_unit="mg/mL",
        molar_concentration=None,
        molar_unit="mM",
        molecular_weight=1000,
    )
    assert molar_result.result_value == pytest.approx(1)
    assert molar_result.result_unit == "mM"
    assert molar_result.record_inputs["solve_for"] == "molar_concentration"


def test_solve_concentration_bridge_rejects_filled_explicit_unknown() -> None:
    with pytest.raises(CalculationError, match="应清空该字段"):
        solve_concentration_bridge(
            mass_concentration=1,
            mass_unit="mg/mL",
            molar_concentration=1,
            molar_unit="mM",
            molecular_weight=1000,
            unknown_field="molecular_weight",
        )


def test_solve_dilution_equation_can_solve_stock_volume() -> None:
    result = solve_dilution_equation(
        stock_concentration=15,
        stock_unit="mM",
        stock_volume=None,
        stock_volume_unit="mL",
        target_concentration=1,
        target_unit="mM",
        final_volume=30,
        final_volume_unit="mL",
    )

    assert result.result_value == pytest.approx(2)
    assert result.result_unit == "mL"
    assert "15 mM × 2 mL = 1 mM × 30 mL" in result.as_text()


def test_mass_concentration_unit_conversion_does_not_require_mw_or_volume() -> None:
    result = convert_mass_concentration_unit(value=1, from_unit="mg/mL", to_unit="µg/mL")

    assert result.result_value == pytest.approx(1000)
    assert result.result_unit == "µg/mL"
    assert "不需要 MW、体积或质量输入" in result.as_text()


def test_stock_working_solution_outputs_stock_and_diluent_volume() -> None:
    result = solve_stock_working_solution(stock_strength=10, target_strength=1, final_volume=100, final_volume_unit="mL")

    assert result.record_outputs["stock_volume"] == pytest.approx(10)
    assert result.record_outputs["diluent_volume"] == pytest.approx(90)
    assert "加入 stock：10 mL" in result.as_text()

    with pytest.raises(CalculationError, match="不能从低倍数配高倍数"):
        solve_stock_working_solution(stock_strength=1, target_strength=10, final_volume=100, final_volume_unit="mL")


def test_percent_solution_supports_wv_vv_and_ww_semantics() -> None:
    wv = solve_percent_solution(
        percent=1,
        percent_type="w/v",
        solute_amount=None,
        solute_unit="g",
        total_amount=100,
        total_unit="mL",
        unknown_field="solute_amount",
    )
    assert wv.result_value == pytest.approx(1)
    assert "称取 1 g，定容至 100 mL" in wv.as_text()

    vv = solve_percent_solution(
        percent=70,
        percent_type="v/v",
        solute_amount=None,
        solute_unit="mL",
        total_amount=100,
        total_unit="mL",
        unknown_field="solute_amount",
    )
    assert vv.result_value == pytest.approx(70)

    ww = solve_percent_solution(
        percent=5,
        percent_type="w/w",
        solute_amount=None,
        solute_unit="g",
        total_amount=100,
        total_unit="g",
        unknown_field="solute_amount",
    )
    assert ww.result_value == pytest.approx(5)


def test_serial_dilution_outputs_each_level_and_low_transfer_warning() -> None:
    result = calculate_serial_dilution(
        initial_concentration=100,
        concentration_unit="µM",
        dilution_factor=10,
        levels=3,
        final_volume=1,
        final_volume_unit="mL",
    )

    steps = result.record_outputs["steps"]
    assert [step["concentration"] for step in steps] == pytest.approx([10, 1, 0.1])
    assert steps[0]["transfer_volume"] == pytest.approx(0.1)
    assert "第 3 级：0.1 µM" in result.as_text()

    tiny = calculate_serial_dilution(
        initial_concentration=100,
        concentration_unit="µM",
        dilution_factor=10000,
        levels=1,
        final_volume=1,
        final_volume_unit="mL",
    )
    assert "移液器下限" in tiny.warnings[0]


def test_solve_dilution_equation_can_solve_each_equation_field() -> None:
    stock_concentration = solve_dilution_equation(
        stock_concentration=None,
        stock_unit="mM",
        stock_volume=2,
        stock_volume_unit="mL",
        target_concentration=1,
        target_unit="mM",
        final_volume=30,
        final_volume_unit="mL",
    )
    assert stock_concentration.result_value == pytest.approx(15)
    assert stock_concentration.result_unit == "mM"

    target_concentration = solve_dilution_equation(
        stock_concentration=15,
        stock_unit="mM",
        stock_volume=2,
        stock_volume_unit="mL",
        target_concentration=None,
        target_unit="mM",
        final_volume=30,
        final_volume_unit="mL",
    )
    assert target_concentration.result_value == pytest.approx(1)
    assert target_concentration.result_unit == "mM"

    final_volume = solve_dilution_equation(
        stock_concentration=15,
        stock_unit="mM",
        stock_volume=2,
        stock_volume_unit="mL",
        target_concentration=1,
        target_unit="mM",
        final_volume=None,
        final_volume_unit="mL",
    )
    assert final_volume.result_value == pytest.approx(30)
    assert final_volume.result_unit == "mL"


def test_solve_dilution_equation_rejects_multiple_unknowns() -> None:
    with pytest.raises(CalculationError, match="只保留一个未知项"):
        solve_dilution_equation(
            stock_concentration=15,
            stock_unit="mM",
            stock_volume=None,
            stock_volume_unit="mL",
            target_concentration=None,
            target_unit="mM",
            final_volume=30,
            final_volume_unit="mL",
        )


def test_solve_solution_preparation_formula_supports_fixed_amount_mode_and_warning_policy() -> None:
    result = solve_solution_preparation_formula(
        mass=None,
        mass_unit="µg",
        concentration=11,
        concentration_unit="nM",
        volume=1,
        volume_unit="mL",
        molecular_weight=256.39,
    )

    assert result.result_value == pytest.approx(0.00282029, rel=1e-6)
    assert result.result_unit == "µg"
    assert any(warning in result.warnings for warning in (LOW_MASS_WARNING, TINY_VALUE_WARNING))
    assert "0.00282 µg" in result.as_text()
    assert "约 2.82 ng" in result.as_text()


def test_solve_solution_preparation_formula_solves_mass_concentration_mode_fields() -> None:
    mass = solve_solution_preparation_formula(
        mass=None,
        mass_unit="mg",
        concentration=10,
        concentration_unit="mg/mL",
        volume=1,
        volume_unit="mL",
    )
    assert mass.result_value == pytest.approx(10)
    assert mass.result_unit == "mg"

    concentration = solve_solution_preparation_formula(
        mass=10,
        mass_unit="mg",
        concentration=None,
        concentration_unit="mg/mL",
        volume=1,
        volume_unit="mL",
    )
    assert concentration.result_value == pytest.approx(10)
    assert concentration.result_unit == "mg/mL"

    volume = solve_solution_preparation_formula(
        mass=10,
        mass_unit="mg",
        concentration=10,
        concentration_unit="mg/mL",
        volume=None,
        volume_unit="mL",
    )
    assert volume.result_value == pytest.approx(1)
    assert volume.result_unit == "mL"


def test_solve_solution_preparation_formula_can_solve_molecular_weight() -> None:
    result = solve_solution_preparation_formula(
        mass=0.00282029,
        mass_unit="µg",
        concentration=11,
        concentration_unit="nM",
        volume=1,
        volume_unit="mL",
        molecular_weight=None,
    )

    assert result.result_value == pytest.approx(256.39, rel=1e-5)
    assert result.result_unit == "g/mol"


def test_solve_solution_preparation_formula_warns_on_low_volume() -> None:
    result = solve_solution_preparation_formula(
        mass=1,
        mass_unit="mg",
        concentration=10,
        concentration_unit="mg/mL",
        volume=None,
        volume_unit="µL",
    )

    assert result.result_value == pytest.approx(100)
    assert result.result_unit == "µL"
    assert LOW_VOLUME_WARNING not in result.warnings

    tiny = solve_dilution_equation(
        stock_concentration=10,
        stock_unit="mg/mL",
        stock_volume=None,
        stock_volume_unit="µL",
        target_concentration=0.01,
        target_unit="mg/mL",
        final_volume=1,
        final_volume_unit="µL",
    )
    assert LOW_VOLUME_WARNING in tiny.warnings
