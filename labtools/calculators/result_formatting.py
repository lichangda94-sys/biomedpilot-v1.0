from __future__ import annotations

from dataclasses import dataclass

from labtools.calculators.unit_conversion import (
    g_to_mass,
    l_to_volume,
    mass_to_g,
    unit_kind,
    volume_to_l,
)


TINY_VALUE_WARNING = "结果在当前单位下很小，已使用更多有效数字或科学计数法显示，避免显示为 0.00。"
LOW_MASS_WARNING = "称量质量低于常规实验室天平可靠称量范围，不建议直接称量。建议先配制较高浓度 stock，再进行稀释。"
LOW_VOLUME_WARNING = "计算得到的移液体积低于常规手动移液可靠范围。不建议直接移取，建议提高终体积、降低 stock 浓度或先做中间稀释液。"

_MASS_DESCENDING_UNITS = ("g", "mg", "µg", "ng")
_MASS_ASCENDING_UNITS = tuple(reversed(_MASS_DESCENDING_UNITS))
_VOLUME_DESCENDING_UNITS = ("L", "mL", "µL", "nL")
_VOLUME_ASCENDING_UNITS = tuple(reversed(_VOLUME_DESCENDING_UNITS))


@dataclass(frozen=True)
class FormattedMeasurement:
    text: str
    warnings: tuple[str, ...] = ()


def format_display_number(value: float) -> str:
    absolute = abs(value)
    if value == 0:
        return "0"
    if absolute >= 1e6:
        return f"{value:,.0f}"
    if absolute >= 0.01:
        return _trimmed_decimal(value, 2, use_grouping=True)
    return f"{value:.3e}"


def format_measurement(value: float, unit: str) -> FormattedMeasurement:
    kind = unit_kind(unit)
    warnings: list[str] = []
    text = f"{format_display_number(value)} {unit}"

    if 0 < abs(value) < 0.01:
        warnings.append(TINY_VALUE_WARNING)
        alternate = _alternate_small_unit(value, unit, kind)
        if alternate:
            alt_value, alt_unit = alternate
            text = f"{_trimmed_decimal(value, 5)} {unit}（约 {_trimmed_decimal(alt_value, 2)} {alt_unit}）"
        else:
            text = f"{value:.3e} {unit}"
    elif 0 < abs(value) < 1:
        text = f"{_trimmed_decimal(value, 4)} {unit}"

    if kind == "mass":
        warnings.extend(_mass_operation_warnings(value, unit))
    if kind == "volume":
        warnings.extend(_volume_operation_warnings(value, unit))
    return FormattedMeasurement(text=text, warnings=tuple(dict.fromkeys(warnings)))


def _alternate_small_unit(value: float, unit: str, kind: str) -> tuple[float, str] | None:
    if kind == "mass":
        value_g = mass_to_g(value, unit)
        for candidate in _MASS_ASCENDING_UNITS:
            converted = g_to_mass(value_g, candidate)
            if abs(converted) >= 0.01 and candidate != unit:
                return converted, candidate
        return None
    if kind == "volume":
        value_l = volume_to_l(value, unit)
        for candidate in _VOLUME_ASCENDING_UNITS:
            converted = l_to_volume(value_l, candidate)
            if abs(converted) >= 0.01 and candidate != unit:
                return converted, candidate
    return None


def _mass_operation_warnings(value: float, unit: str) -> list[str]:
    value_g = mass_to_g(value, unit)
    value_mg = g_to_mass(value_g, "mg")
    value_ug = g_to_mass(value_g, "µg")
    warnings: list[str] = []
    if 0.1 <= value_mg < 1:
        warnings.append("称量量偏低，请确认天平精度和容器损耗。")
    if 0.01 <= value_mg < 0.1:
        warnings.append(LOW_MASS_WARNING)
    if 0 < value_ug < 1:
        warnings.append(LOW_MASS_WARNING)
    return warnings


def _volume_operation_warnings(value: float, unit: str) -> list[str]:
    value_l = volume_to_l(value, unit)
    value_ul = l_to_volume(value_l, "µL")
    warnings: list[str] = []
    if 1 <= value_ul < 2:
        warnings.append("移液体积偏低，实际操作误差可能偏大。")
    if 0.5 <= value_ul < 1:
        warnings.append(LOW_VOLUME_WARNING)
    if 0 < value_ul < 0.5:
        warnings.append(LOW_VOLUME_WARNING)
    return warnings


def _trimmed_decimal(value: float, decimals: int, *, use_grouping: bool = False) -> str:
    pattern = f",.{decimals}f" if use_grouping else f".{decimals}f"
    text = format(value, pattern)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"
