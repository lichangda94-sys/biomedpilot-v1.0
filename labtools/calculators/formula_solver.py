from __future__ import annotations

from labtools.calculators.calculator_models import CalculationError, CalculationResult
from labtools.calculators.result_formatting import format_measurement
from labtools.calculators.unit_conversion import (
    canonical_unit,
    concentration_to_relative_base,
    g_per_l_to_mass_concentration,
    g_to_mass,
    l_to_volume,
    mass_concentration_to_g_per_l,
    mass_to_g,
    m_to_molarity,
    molarity_to_m,
    parse_number,
    relative_base_to_concentration,
    unit_kind,
    validate_molecular_weight,
    volume_to_l,
)


def solve_concentration_bridge(
    *,
    mass_concentration: object | None,
    mass_unit: str,
    molar_concentration: object | None,
    molar_unit: str,
    molecular_weight: object | None,
    unknown_field: str | None = None,
) -> CalculationResult:
    unknown = _resolve_unknown(
        {
            "mass_concentration": mass_concentration,
            "molar_concentration": molar_concentration,
            "molecular_weight": molecular_weight,
        },
        unknown_field=unknown_field,
        field_labels={
            "mass_concentration": "质量浓度",
            "molar_concentration": "摩尔浓度",
            "molecular_weight": "分子量",
        },
    )
    mass_unit = canonical_unit(mass_unit)
    molar_unit = canonical_unit(molar_unit)
    if unit_kind(mass_unit) != "mass_concentration":
        raise CalculationError("质量浓度字段必须使用质量浓度单位。")
    if unit_kind(molar_unit) != "molarity":
        raise CalculationError("摩尔浓度字段必须使用摩尔浓度单位。")

    mass_value = _known_number(mass_concentration, "质量浓度", allow_zero=False) if unknown != "mass_concentration" else None
    molar_value = _known_number(molar_concentration, "摩尔浓度", allow_zero=False) if unknown != "molar_concentration" else None
    molecular_weight_value = (
        validate_molecular_weight(molecular_weight) if unknown != "molecular_weight" else None
    )

    if unknown == "mass_concentration":
        assert molar_value is not None and molecular_weight_value is not None
        solved = g_per_l_to_mass_concentration(molarity_to_m(molar_value, molar_unit) * molecular_weight_value, mass_unit)
        display = format_measurement(solved, mass_unit)
        return CalculationResult(
            title="浓度换算动态求解",
            input_summary=(
                f"已知摩尔浓度：{format_measurement(molar_value, molar_unit).text}",
                f"已知分子量：{molecular_weight_value:.2f} g/mol",
                f"求解字段：质量浓度（{mass_unit}）",
            ),
            formula=("质量浓度 = 摩尔浓度 x 分子量",),
            result_lines=(f"质量浓度：{display.text}",),
            result_value=solved,
            result_unit=mass_unit,
            warnings=display.warnings,
            record_inputs={
                "molar_concentration": molar_value,
                "molar_unit": molar_unit,
                "molecular_weight_g_per_mol": molecular_weight_value,
                "solve_for": unknown,
                "target_unit": mass_unit,
            },
            record_outputs={"mass_concentration": solved, "mass_unit": mass_unit},
        )

    if unknown == "molar_concentration":
        assert mass_value is not None and molecular_weight_value is not None
        solved = m_to_molarity(mass_concentration_to_g_per_l(mass_value, mass_unit) / molecular_weight_value, molar_unit)
        display = format_measurement(solved, molar_unit)
        return CalculationResult(
            title="浓度换算动态求解",
            input_summary=(
                f"已知质量浓度：{format_measurement(mass_value, mass_unit).text}",
                f"已知分子量：{molecular_weight_value:.2f} g/mol",
                f"求解字段：摩尔浓度（{molar_unit}）",
            ),
            formula=("摩尔浓度 = 质量浓度 / 分子量",),
            result_lines=(f"摩尔浓度：{display.text}",),
            result_value=solved,
            result_unit=molar_unit,
            warnings=display.warnings,
            record_inputs={
                "mass_concentration": mass_value,
                "mass_unit": mass_unit,
                "molecular_weight_g_per_mol": molecular_weight_value,
                "solve_for": unknown,
                "target_unit": molar_unit,
            },
            record_outputs={"molar_concentration": solved, "molar_unit": molar_unit},
        )

    assert mass_value is not None and molar_value is not None
    solved_mw = mass_concentration_to_g_per_l(mass_value, mass_unit) / molarity_to_m(molar_value, molar_unit)
    return CalculationResult(
        title="浓度换算动态求解",
        input_summary=(
            f"已知质量浓度：{format_measurement(mass_value, mass_unit).text}",
            f"已知摩尔浓度：{format_measurement(molar_value, molar_unit).text}",
            "求解字段：分子量（g/mol）",
        ),
        formula=("分子量 = 质量浓度 / 摩尔浓度",),
        result_lines=(f"分子量：{solved_mw:,.2f} g/mol",),
        result_value=solved_mw,
        result_unit="g/mol",
        record_inputs={
            "mass_concentration": mass_value,
            "mass_unit": mass_unit,
            "molar_concentration": molar_value,
            "molar_unit": molar_unit,
            "solve_for": unknown,
            "target_unit": "g/mol",
        },
        record_outputs={"molecular_weight_g_per_mol": solved_mw},
    )


def solve_dilution_equation(
    *,
    stock_concentration: object | None,
    stock_unit: str,
    stock_volume: object | None,
    stock_volume_unit: str,
    target_concentration: object | None,
    target_unit: str,
    final_volume: object | None,
    final_volume_unit: str,
    molecular_weight: object | None = None,
    unknown_field: str | None = None,
) -> CalculationResult:
    unknown = _resolve_unknown(
        {
            "stock_concentration": stock_concentration,
            "stock_volume": stock_volume,
            "target_concentration": target_concentration,
            "final_volume": final_volume,
        },
        unknown_field=unknown_field,
        field_labels={
            "stock_concentration": "原液浓度",
            "stock_volume": "原液体积",
            "target_concentration": "目标浓度",
            "final_volume": "终体积",
        },
    )
    stock_unit = canonical_unit(stock_unit)
    target_unit = canonical_unit(target_unit)
    stock_volume_unit = canonical_unit(stock_volume_unit)
    final_volume_unit = canonical_unit(final_volume_unit)
    if unit_kind(stock_volume_unit) != "volume" or unit_kind(final_volume_unit) != "volume":
        raise CalculationError("体积字段必须使用体积单位。")

    stock_base_kind = _solver_concentration_kind(stock_unit, target_unit, molecular_weight)
    stock_base = (
        _concentration_to_base(stock_concentration, stock_unit, stock_base_kind, molecular_weight, "原液浓度")
        if unknown != "stock_concentration"
        else None
    )
    target_base = (
        _concentration_to_base(target_concentration, target_unit, stock_base_kind, molecular_weight, "目标浓度")
        if unknown != "target_concentration"
        else None
    )
    stock_volume_l = volume_to_l(_known_number(stock_volume, "原液体积", allow_zero=False), stock_volume_unit) if unknown != "stock_volume" else None
    final_volume_l = volume_to_l(_known_number(final_volume, "终体积", allow_zero=False), final_volume_unit) if unknown != "final_volume" else None

    if unknown == "stock_concentration":
        assert stock_volume_l is not None and target_base is not None and final_volume_l is not None
        solved_base = target_base * final_volume_l / stock_volume_l
        stock_base = solved_base
    elif unknown == "stock_volume":
        assert stock_base is not None and target_base is not None and final_volume_l is not None
        stock_volume_l = target_base * final_volume_l / stock_base
    elif unknown == "target_concentration":
        assert stock_base is not None and stock_volume_l is not None and final_volume_l is not None
        target_base = stock_base * stock_volume_l / final_volume_l
    else:
        assert stock_base is not None and stock_volume_l is not None and target_base is not None
        final_volume_l = stock_base * stock_volume_l / target_base

    assert stock_base is not None and target_base is not None and stock_volume_l is not None and final_volume_l is not None
    if stock_base <= 0 or target_base <= 0:
        raise CalculationError("浓度必须大于 0。")
    if final_volume_l <= 0 or stock_volume_l <= 0:
        raise CalculationError("体积必须大于 0。")
    if target_base > stock_base:
        raise CalculationError("目标浓度高于原液浓度，不能通过稀释获得。")
    if stock_volume_l > final_volume_l:
        raise CalculationError("所需原液体积大于终体积，请检查输入。")

    stock_display_value = _concentration_from_base(stock_base, stock_unit, stock_base_kind, molecular_weight)
    target_display_value = _concentration_from_base(target_base, target_unit, stock_base_kind, molecular_weight)
    stock_volume_display = l_to_volume(stock_volume_l, stock_volume_unit)
    final_volume_display = l_to_volume(final_volume_l, final_volume_unit)
    solvent_volume_display = l_to_volume(final_volume_l - stock_volume_l, final_volume_unit)

    solved_value, solved_unit = _dilution_solved_value_and_unit(
        unknown,
        stock_display_value=stock_display_value,
        stock_unit=stock_unit,
        stock_volume_display=stock_volume_display,
        stock_volume_unit=stock_volume_unit,
        target_display_value=target_display_value,
        target_unit=target_unit,
        final_volume_display=final_volume_display,
        final_volume_unit=final_volume_unit,
    )
    solved_display = format_measurement(solved_value, solved_unit) if solved_unit != "g/mol" else None
    volume_display = format_measurement(stock_volume_display, stock_volume_unit)
    solvent_display = format_measurement(solvent_volume_display, final_volume_unit)
    warnings = list(volume_display.warnings) + list(solvent_display.warnings)
    if solved_display is not None:
        warnings.extend(solved_display.warnings)

    equation = (
        f"{format_measurement(stock_display_value, stock_unit).text} × {format_measurement(stock_volume_display, stock_volume_unit).text}"
        f" = {format_measurement(target_display_value, target_unit).text} × {format_measurement(final_volume_display, final_volume_unit).text}"
    )
    result_lines = (
        f"等式：{equation}",
        f"所需原液体积：{volume_display.text}",
        f"所需溶剂体积：{solvent_display.text}",
    )
    if unknown == "stock_concentration":
        result_lines = (f"原液浓度：{format_measurement(stock_display_value, stock_unit).text}",) + result_lines
    if unknown == "target_concentration":
        result_lines = (f"目标浓度：{format_measurement(target_display_value, target_unit).text}",) + result_lines
    if unknown == "final_volume":
        result_lines = (f"终体积：{format_measurement(final_volume_display, final_volume_unit).text}",) + result_lines

    return CalculationResult(
        title="C1V1 = C2V2 动态求解",
        input_summary=(
            f"原液浓度字段单位：{stock_unit}",
            f"原液体积字段单位：{stock_volume_unit}",
            f"目标浓度字段单位：{target_unit}",
            f"终体积字段单位：{final_volume_unit}",
            f"求解字段：{unknown}",
        ),
        formula=("C1V1 = C2V2", "只允许保留一个未知项。"),
        result_lines=result_lines,
        result_value=solved_value,
        result_unit=solved_unit,
        warnings=tuple(dict.fromkeys(warnings)),
        record_inputs={
            "stock_concentration": stock_concentration,
            "stock_unit": stock_unit,
            "stock_volume": stock_volume,
            "stock_volume_unit": stock_volume_unit,
            "target_concentration": target_concentration,
            "target_unit": target_unit,
            "final_volume": final_volume,
            "final_volume_unit": final_volume_unit,
            "molecular_weight_g_per_mol": molecular_weight,
            "solve_for": unknown,
        },
        record_outputs={
            "stock_concentration": stock_display_value,
            "stock_unit": stock_unit,
            "stock_volume": stock_volume_display,
            "stock_volume_unit": stock_volume_unit,
            "target_concentration": target_display_value,
            "target_unit": target_unit,
            "final_volume": final_volume_display,
            "final_volume_unit": final_volume_unit,
            "solvent_volume": solvent_volume_display,
            "solvent_volume_unit": final_volume_unit,
        },
    )


def solve_solution_preparation_formula(
    *,
    mass: object | None,
    mass_unit: str,
    concentration: object | None,
    concentration_unit: str,
    volume: object | None,
    volume_unit: str,
    molecular_weight: object | None = None,
    unknown_field: str | None = None,
) -> CalculationResult:
    concentration_unit = canonical_unit(concentration_unit)
    concentration_kind = unit_kind(concentration_unit)
    if concentration_kind not in {"mass_concentration", "molarity"}:
        raise CalculationError("浓度字段必须使用质量浓度或摩尔浓度单位。")

    fields = {
        "mass": mass,
        "concentration": concentration,
        "volume": volume,
    }
    if concentration_kind == "molarity":
        fields["molecular_weight"] = molecular_weight
    unknown = _resolve_unknown(
        fields,
        unknown_field=unknown_field,
        field_labels={
            "mass": "质量",
            "concentration": "浓度",
            "volume": "体积",
            "molecular_weight": "分子量",
        },
    )

    mass_unit = canonical_unit(mass_unit)
    volume_unit = canonical_unit(volume_unit)
    if unit_kind(mass_unit) != "mass":
        raise CalculationError("质量字段必须使用质量单位。")
    if unit_kind(volume_unit) != "volume":
        raise CalculationError("体积字段必须使用体积单位。")

    mass_g = mass_to_g(_known_number(mass, "质量", allow_zero=False), mass_unit) if unknown != "mass" else None
    volume_l = volume_to_l(_known_number(volume, "体积", allow_zero=False), volume_unit) if unknown != "volume" else None
    concentration_base = (
        _solution_concentration_to_base(concentration, concentration_unit, "目标浓度")
        if unknown != "concentration"
        else None
    )
    molecular_weight_value = (
        validate_molecular_weight(molecular_weight) if concentration_kind == "molarity" and unknown != "molecular_weight" else None
    )

    if concentration_kind == "mass_concentration":
        if unknown == "mass":
            assert concentration_base is not None and volume_l is not None
            mass_g = concentration_base * volume_l
        elif unknown == "concentration":
            assert mass_g is not None and volume_l is not None
            concentration_base = mass_g / volume_l
        else:
            assert mass_g is not None and concentration_base is not None
            volume_l = mass_g / concentration_base
    else:
        if unknown == "mass":
            assert concentration_base is not None and volume_l is not None and molecular_weight_value is not None
            mass_g = concentration_base * volume_l * molecular_weight_value
        elif unknown == "concentration":
            assert mass_g is not None and volume_l is not None and molecular_weight_value is not None
            concentration_base = mass_g / (volume_l * molecular_weight_value)
        elif unknown == "volume":
            assert mass_g is not None and concentration_base is not None and molecular_weight_value is not None
            volume_l = mass_g / (concentration_base * molecular_weight_value)
        else:
            assert mass_g is not None and concentration_base is not None and volume_l is not None
            molecular_weight_value = mass_g / (concentration_base * volume_l)

    assert mass_g is not None and volume_l is not None and concentration_base is not None
    mass_value = g_to_mass(mass_g, mass_unit)
    volume_value = l_to_volume(volume_l, volume_unit)
    concentration_value = _solution_concentration_from_base(concentration_base, concentration_unit)

    mass_display = format_measurement(mass_value, mass_unit)
    volume_display = format_measurement(volume_value, volume_unit)
    concentration_display = format_measurement(concentration_value, concentration_unit)
    warnings = list(mass_display.warnings) + list(volume_display.warnings) + list(concentration_display.warnings)
    result_lines = (
        f"质量：{mass_display.text}",
        f"浓度：{concentration_display.text}",
        f"体积：{volume_display.text}",
    )
    if concentration_kind == "molarity":
        assert molecular_weight_value is not None
        result_lines += (f"分子量：{molecular_weight_value:,.2f} g/mol",)

    solved_value, solved_unit = _solution_solved_value_and_unit(
        unknown,
        mass_value=mass_value,
        mass_unit=mass_unit,
        concentration_value=concentration_value,
        concentration_unit=concentration_unit,
        volume_value=volume_value,
        volume_unit=volume_unit,
        molecular_weight_value=molecular_weight_value,
    )
    return CalculationResult(
        title="溶液配制动态求解",
        input_summary=(
            f"浓度模式：{'摩尔浓度' if concentration_kind == 'molarity' else '质量浓度'}",
            f"求解字段：{unknown}",
            f"目标浓度单位：{concentration_unit}",
            f"体积单位：{volume_unit}",
            f"质量单位：{mass_unit}",
        ),
        formula=(
            "质量浓度模式：质量 = 浓度 x 体积",
            "摩尔浓度模式：质量 = 摩尔浓度 x 体积 x 分子量",
        ),
        result_lines=result_lines,
        result_value=solved_value,
        result_unit=solved_unit,
        warnings=tuple(dict.fromkeys(warnings)),
        record_inputs={
            "mass": mass,
            "mass_unit": mass_unit,
            "concentration": concentration,
            "concentration_unit": concentration_unit,
            "volume": volume,
            "volume_unit": volume_unit,
            "molecular_weight_g_per_mol": molecular_weight,
            "solve_for": unknown,
        },
        record_outputs={
            "mass": mass_value,
            "mass_unit": mass_unit,
            "concentration": concentration_value,
            "concentration_unit": concentration_unit,
            "volume": volume_value,
            "volume_unit": volume_unit,
            "molecular_weight_g_per_mol": molecular_weight_value,
        },
    )


def _resolve_unknown(
    values: dict[str, object | None],
    *,
    unknown_field: str | None,
    field_labels: dict[str, str],
) -> str:
    if unknown_field is not None:
        if unknown_field not in values:
            raise CalculationError(f"未知求解字段：{unknown_field}。")
        if values[unknown_field] not in (None, ""):
            raise CalculationError("如果显式指定求解字段，应清空该字段的输入值。")
        filled_others = [name for name, value in values.items() if name != unknown_field and value not in (None, "")]
        if len(filled_others) != len(values) - 1:
            raise CalculationError("请填写足够的已知项，并只保留一个未知项。")
        return unknown_field

    empty_fields = [name for name, value in values.items() if value in (None, "")]
    if len(empty_fields) == 1:
        return empty_fields[0]
    if not empty_fields:
        raise CalculationError("请选择一个要求解字段，或清空一个字段。")
    labels = "、".join(field_labels[name] for name in empty_fields)
    raise CalculationError(f"请填写足够的已知项，并只保留一个未知项。当前为空：{labels}。")


def _known_number(value: object | None, field_name: str, *, allow_zero: bool) -> float:
    if value in (None, ""):
        raise CalculationError(f"请填写{field_name}。")
    return parse_number(value, field_name, allow_zero=allow_zero)


def _solver_concentration_kind(stock_unit: str, target_unit: str, molecular_weight: object | None) -> str:
    stock_kind = unit_kind(stock_unit)
    target_kind = unit_kind(target_unit)
    valid = {"molarity", "mass_concentration", "relative_concentration"}
    if stock_kind not in valid or target_kind not in valid:
        raise CalculationError("浓度字段必须使用浓度或比例浓度单位。")
    if stock_kind == target_kind:
        return stock_kind
    if {stock_kind, target_kind} == {"molarity", "mass_concentration"}:
        validate_molecular_weight(molecular_weight)
        return "molarity"
    raise CalculationError("比例浓度单位不能与质量浓度或摩尔浓度混用。")


def _concentration_to_base(
    value: object | None,
    unit: str,
    solver_kind: str,
    molecular_weight: object | None,
    field_name: str,
) -> float:
    number = _known_number(value, field_name, allow_zero=False)
    kind = unit_kind(unit)
    if solver_kind == "molarity":
        if kind == "molarity":
            return molarity_to_m(number, unit)
        assert molecular_weight is not None
        return mass_concentration_to_g_per_l(number, unit) / validate_molecular_weight(molecular_weight)
    if solver_kind == "mass_concentration":
        return mass_concentration_to_g_per_l(number, unit)
    return concentration_to_relative_base(number, unit)


def _concentration_from_base(value_base: float, unit: str, solver_kind: str, molecular_weight: object | None) -> float:
    kind = unit_kind(unit)
    if solver_kind == "molarity":
        if kind == "molarity":
            return m_to_molarity(value_base, unit)
        assert molecular_weight is not None
        return g_per_l_to_mass_concentration(value_base * validate_molecular_weight(molecular_weight), unit)
    if solver_kind == "mass_concentration":
        return g_per_l_to_mass_concentration(value_base, unit)
    return relative_base_to_concentration(value_base, unit)


def _solution_concentration_to_base(value: object | None, unit: str, field_name: str) -> float:
    number = _known_number(value, field_name, allow_zero=False)
    if unit_kind(unit) == "molarity":
        return molarity_to_m(number, unit)
    return mass_concentration_to_g_per_l(number, unit)


def _solution_concentration_from_base(value_base: float, unit: str) -> float:
    if unit_kind(unit) == "molarity":
        return m_to_molarity(value_base, unit)
    return g_per_l_to_mass_concentration(value_base, unit)


def _dilution_solved_value_and_unit(
    unknown: str,
    *,
    stock_display_value: float,
    stock_unit: str,
    stock_volume_display: float,
    stock_volume_unit: str,
    target_display_value: float,
    target_unit: str,
    final_volume_display: float,
    final_volume_unit: str,
) -> tuple[float, str]:
    if unknown == "stock_concentration":
        return stock_display_value, stock_unit
    if unknown == "stock_volume":
        return stock_volume_display, stock_volume_unit
    if unknown == "target_concentration":
        return target_display_value, target_unit
    return final_volume_display, final_volume_unit


def _solution_solved_value_and_unit(
    unknown: str,
    *,
    mass_value: float,
    mass_unit: str,
    concentration_value: float,
    concentration_unit: str,
    volume_value: float,
    volume_unit: str,
    molecular_weight_value: float | None,
) -> tuple[float, str]:
    if unknown == "mass":
        return mass_value, mass_unit
    if unknown == "concentration":
        return concentration_value, concentration_unit
    if unknown == "volume":
        return volume_value, volume_unit
    assert molecular_weight_value is not None
    return molecular_weight_value, "g/mol"
