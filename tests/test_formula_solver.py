from __future__ import annotations

import pytest

from labtools.calculators.formula_solver import (
    solve_concentration_bridge,
    solve_dilution_equation,
    solve_solution_preparation_formula,
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
