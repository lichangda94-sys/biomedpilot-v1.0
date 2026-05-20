from __future__ import annotations

import math

from labtools.calculators.calculator_models import CalculationError


MASS_UNITS: dict[str, float] = {
    "g": 1.0,
    "mg": 1e-3,
    "µg": 1e-6,
    "ng": 1e-9,
}

VOLUME_UNITS: dict[str, float] = {
    "L": 1.0,
    "mL": 1e-3,
    "µL": 1e-6,
    "nL": 1e-9,
}

MOLARITY_UNITS: dict[str, float] = {
    "M": 1.0,
    "mM": 1e-3,
    "µM": 1e-6,
    "nM": 1e-9,
    "pM": 1e-12,
}

MASS_CONCENTRATION_UNITS: dict[str, float] = {
    "g/L": 1.0,
    "mg/L": 1e-3,
    "mg/mL": 1.0,
    "µg/µL": 1.0,
    "µg/mL": 1e-3,
    "ng/mL": 1e-6,
    "ng/µL": 1e-3,
}

RELATIVE_CONCENTRATION_UNITS: dict[str, float] = {
    "%": 0.01,
    "X": 1.0,
    "fold": 1.0,
}

AMOUNT_UNITS: dict[str, float] = {
    "mol": 1.0,
    "mmol": 1e-3,
    "µmol": 1e-6,
    "nmol": 1e-9,
    "pmol": 1e-12,
}

CELL_DENSITY_UNITS: dict[str, float] = {
    "cells/mL": 1.0,
    "cells/µL": 1000.0,
}

QUICK_CALCULATOR_FIELD_TYPES = (
    "concentration",
    "volume",
    "mass",
    "amount",
    "molecular_weight",
)

UNIT_ALIASES = {
    "ug": "µg",
    "μg": "µg",
    "uL": "µL",
    "ul": "µL",
    "μL": "µL",
    "uM": "µM",
    "um": "µM",
    "μM": "µM",
    "pmol": "pmol",
    "pm": "pM",
    "ug/mL": "µg/mL",
    "μg/mL": "µg/mL",
    "ug/uL": "µg/µL",
    "ug/μL": "µg/µL",
    "µg/uL": "µg/µL",
    "μg/uL": "µg/µL",
    "μg/μL": "µg/µL",
    "ng/uL": "ng/µL",
    "ng/μL": "ng/µL",
    "nL": "nL",
    "ul": "µL",
    "umol": "µmol",
    "μmol": "µmol",
    "cells/uL": "cells/µL",
    "cells/μL": "cells/µL",
    "cell/mL": "cells/mL",
    "cells/ml": "cells/mL",
    "x": "X",
    "×": "X",
}


def canonical_unit(unit: str) -> str:
    text = str(unit or "").strip()
    if not text:
        raise CalculationError("请选择单位。")
    canonical = UNIT_ALIASES.get(text, text)
    if (
        canonical in MASS_UNITS
        or canonical in VOLUME_UNITS
        or canonical in MOLARITY_UNITS
        or canonical in MASS_CONCENTRATION_UNITS
        or canonical in RELATIVE_CONCENTRATION_UNITS
        or canonical in AMOUNT_UNITS
        or canonical in CELL_DENSITY_UNITS
    ):
        return canonical
    raise CalculationError(f"暂不支持单位：{text}。")


def parse_number(value: object, field_name: str, *, allow_zero: bool = True) -> float:
    if value is None or str(value).strip() == "":
        raise CalculationError(f"请填写{field_name}。")
    try:
        number = float(str(value).strip())
    except ValueError as exc:
        raise CalculationError(f"{field_name}必须是有效数字。") from exc
    if not math.isfinite(number):
        raise CalculationError(f"{field_name}必须是有效数字。")
    if number < 0:
        raise CalculationError(f"{field_name}不能为负数。")
    if not allow_zero and number == 0:
        raise CalculationError(f"{field_name}必须大于 0。")
    return number


def format_number(value: float) -> str:
    if value == 0:
        return "0"
    absolute = abs(value)
    if 1e-3 <= absolute < 1e6:
        text = f"{value:.6f}".rstrip("0").rstrip(".")
        return text or "0"
    return f"{value:.6g}"


def unit_kind(unit: str) -> str:
    canonical = canonical_unit(unit)
    if canonical in MASS_UNITS:
        return "mass"
    if canonical in VOLUME_UNITS:
        return "volume"
    if canonical in MOLARITY_UNITS:
        return "molarity"
    if canonical in MASS_CONCENTRATION_UNITS:
        return "mass_concentration"
    if canonical in RELATIVE_CONCENTRATION_UNITS:
        return "relative_concentration"
    if canonical in AMOUNT_UNITS:
        return "amount"
    if canonical in CELL_DENSITY_UNITS:
        return "cell_density"
    raise CalculationError(f"暂不支持单位：{unit}。")


def validate_molecular_weight(value: object) -> float:
    return parse_number(value, "分子量（g/mol）", allow_zero=False)


def mass_to_g(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_UNITS:
        raise CalculationError(f"{canonical} 不是质量单位。")
    return value * MASS_UNITS[canonical]


def g_to_mass(value_g: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_UNITS:
        raise CalculationError(f"{canonical} 不是质量单位。")
    return value_g / MASS_UNITS[canonical]


def volume_to_l(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in VOLUME_UNITS:
        raise CalculationError(f"{canonical} 不是体积单位。")
    return value * VOLUME_UNITS[canonical]


def l_to_volume(value_l: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in VOLUME_UNITS:
        raise CalculationError(f"{canonical} 不是体积单位。")
    return value_l / VOLUME_UNITS[canonical]


def molarity_to_m(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MOLARITY_UNITS:
        raise CalculationError(f"{canonical} 不是物质的量浓度单位。")
    return value * MOLARITY_UNITS[canonical]


def m_to_molarity(value_m: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MOLARITY_UNITS:
        raise CalculationError(f"{canonical} 不是物质的量浓度单位。")
    return value_m / MOLARITY_UNITS[canonical]


def mass_concentration_to_g_per_l(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_CONCENTRATION_UNITS:
        raise CalculationError(f"{canonical} 不是质量浓度单位。")
    return value * MASS_CONCENTRATION_UNITS[canonical]


def g_per_l_to_mass_concentration(value_g_per_l: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in MASS_CONCENTRATION_UNITS:
        raise CalculationError(f"{canonical} 不是质量浓度单位。")
    return value_g_per_l / MASS_CONCENTRATION_UNITS[canonical]


def concentration_to_relative_base(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in RELATIVE_CONCENTRATION_UNITS:
        raise CalculationError(f"{canonical} 不是比例浓度单位。")
    return value * RELATIVE_CONCENTRATION_UNITS[canonical]


def relative_base_to_concentration(value_base: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in RELATIVE_CONCENTRATION_UNITS:
        raise CalculationError(f"{canonical} 不是比例浓度单位。")
    return value_base / RELATIVE_CONCENTRATION_UNITS[canonical]


def amount_to_mol(value: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in AMOUNT_UNITS:
        raise CalculationError(f"{canonical} 不是物质的量单位。")
    return value * AMOUNT_UNITS[canonical]


def mol_to_amount(value_mol: float, unit: str) -> float:
    canonical = canonical_unit(unit)
    if canonical not in AMOUNT_UNITS:
        raise CalculationError(f"{canonical} 不是物质的量单位。")
    return value_mol / AMOUNT_UNITS[canonical]


def supported_concentration_units(*, include_molar: bool = True) -> tuple[str, ...]:
    units = tuple(MASS_CONCENTRATION_UNITS) + tuple(RELATIVE_CONCENTRATION_UNITS)
    if include_molar:
        return units + tuple(MOLARITY_UNITS)
    return units


def supported_mass_units() -> tuple[str, ...]:
    return tuple(MASS_UNITS)


def supported_volume_units() -> tuple[str, ...]:
    return tuple(VOLUME_UNITS)


def supported_cell_density_units() -> tuple[str, ...]:
    return tuple(CELL_DENSITY_UNITS)


def supported_amount_units() -> tuple[str, ...]:
    return tuple(AMOUNT_UNITS)


def supported_molecular_weight_units() -> tuple[str, ...]:
    return ("g/mol",)


def supported_quick_calculator_units(field_type: str, *, use_molar_calculation: bool = False) -> tuple[str, ...]:
    """Return UI-safe unit choices for L3 quick calculator fields."""

    field = str(field_type or "").strip()
    if field == "concentration":
        return supported_concentration_units(include_molar=use_molar_calculation)
    if field == "volume":
        return supported_volume_units()
    if field == "mass":
        return supported_mass_units()
    if field == "amount":
        return supported_amount_units()
    if field == "molecular_weight":
        return supported_molecular_weight_units() if use_molar_calculation else ()
    raise CalculationError(f"暂不支持快速计算字段类型：{field_type}。")
