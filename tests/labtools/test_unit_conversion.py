from __future__ import annotations

import pytest

from app.labtools.calculators.calculator_models import CalculationError
from app.labtools.calculators.unit_conversion import (
    amount_to_mol,
    canonical_unit,
    concentration_to_relative_base,
    mass_concentration_to_g_per_l,
    mass_to_g,
    mol_to_amount,
    molarity_to_m,
    parse_number,
    relative_base_to_concentration,
    supported_quick_calculator_units,
    volume_to_l,
)


def test_supported_unit_aliases_are_canonicalized() -> None:
    assert canonical_unit("ug") == "µg"
    assert canonical_unit("uL") == "µL"
    assert canonical_unit("uM") == "µM"
    assert canonical_unit("ng/uL") == "ng/µL"
    assert canonical_unit("ug/mL") == "µg/mL"
    assert canonical_unit("ug/uL") == "µg/µL"
    assert canonical_unit("cells/uL") == "cells/µL"
    assert canonical_unit("x") == "X"
    assert canonical_unit("umol") == "µmol"


def test_mass_volume_and_concentration_convert_to_base_units() -> None:
    assert mass_to_g(2, "mg") == pytest.approx(0.002)
    assert volume_to_l(500, "µL") == pytest.approx(0.0005)
    assert volume_to_l(500, "nL") == pytest.approx(5e-7)
    assert molarity_to_m(250, "µM") == pytest.approx(0.00025)
    assert mass_concentration_to_g_per_l(1, "mg/mL") == pytest.approx(1.0)
    assert mass_concentration_to_g_per_l(1, "g/L") == pytest.approx(1.0)
    assert mass_concentration_to_g_per_l(1, "µg/µL") == pytest.approx(1.0)
    assert mass_concentration_to_g_per_l(1, "ng/mL") == pytest.approx(1e-6)
    assert mass_concentration_to_g_per_l(1, "ng/µL") == pytest.approx(0.001)
    assert concentration_to_relative_base(10, "%") == pytest.approx(0.1)
    assert relative_base_to_concentration(2, "fold") == pytest.approx(2)
    assert amount_to_mol(1, "µmol") == pytest.approx(1e-6)
    assert mol_to_amount(1e-9, "nmol") == pytest.approx(1)


def test_parse_number_reports_friendly_errors() -> None:
    with pytest.raises(CalculationError, match="请填写质量"):
        parse_number("", "质量")
    with pytest.raises(CalculationError, match="不能为负数"):
        parse_number("-1", "体积")
    with pytest.raises(CalculationError, match="必须大于 0"):
        parse_number("0", "目标体积", allow_zero=False)


def test_unknown_unit_reports_friendly_error() -> None:
    with pytest.raises(CalculationError, match="暂不支持单位"):
        canonical_unit("ppm")


def test_quick_calculator_unit_schema_respects_molar_mode() -> None:
    concentration_units = supported_quick_calculator_units("concentration", use_molar_calculation=False)
    assert "mg/mL" in concentration_units
    assert "fold" in concentration_units
    assert "mM" not in concentration_units

    molar_units = supported_quick_calculator_units("concentration", use_molar_calculation=True)
    assert "mM" in molar_units
    assert "pM" in molar_units

    assert supported_quick_calculator_units("molecular_weight", use_molar_calculation=False) == ()
    assert supported_quick_calculator_units("molecular_weight", use_molar_calculation=True) == ("g/mol",)
    assert supported_quick_calculator_units("volume") == ("L", "mL", "µL", "nL")
    assert supported_quick_calculator_units("mass") == ("g", "mg", "µg", "ng")
    assert supported_quick_calculator_units("amount") == ("mol", "mmol", "µmol", "nmol", "pmol")


def test_quick_calculator_unit_schema_rejects_unknown_field_type() -> None:
    with pytest.raises(CalculationError, match="字段类型"):
        supported_quick_calculator_units("temperature")
