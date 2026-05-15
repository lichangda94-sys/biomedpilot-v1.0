from __future__ import annotations

import re

from app.labtools.calculators.calculator_models import CalculationError, CalculationResult
from app.labtools.calculators.unit_conversion import canonical_unit, format_number, l_to_volume, parse_number, unit_kind, volume_to_l
from app.labtools.recipes.recipe_models import RECIPE_REVIEW_NOTICE, Recipe, RecipeScalingResult, ScaledComponent
from app.labtools.recipes.recipe_validation import is_linearly_scalable_unit


def scale_recipe(recipe: Recipe, target_volume: object, target_volume_unit: str) -> RecipeScalingResult:
    target_value = parse_number(target_volume, "目标体积", allow_zero=False)
    target_unit = canonical_unit(target_volume_unit)
    if unit_kind(target_unit) != "volume":
        raise CalculationError("目标体积单位必须是体积单位。")
    original_l = volume_to_l(recipe.default_volume, recipe.default_volume_unit)
    target_l = volume_to_l(target_value, target_unit)
    factor = target_l / original_l

    scaled_components: list[ScaledComponent] = []
    warnings: list[str] = []
    for component in recipe.components:
        if is_linearly_scalable_unit(component.unit):
            scaled_components.append(
                ScaledComponent(
                    name=component.name,
                    original_amount=component.amount,
                    original_unit=component.unit,
                    scaled_amount=component.amount * factor,
                    scaled_unit=canonical_unit(component.unit),
                    role=component.role,
                    notes=component.notes,
                )
            )
            continue
        warning = f"{component.name} 的单位 {component.unit} 不能线性缩放，请按 SOP 人工确认。"
        warnings.append(warning)
        scaled_components.append(
            ScaledComponent(
                name=component.name,
                original_amount=component.amount,
                original_unit=component.unit,
                scaled_amount=None,
                scaled_unit=component.unit,
                role=component.role,
                notes=warning,
            )
        )

    return RecipeScalingResult(
        recipe_name=recipe.name,
        original_volume=recipe.default_volume,
        original_volume_unit=recipe.default_volume_unit,
        target_volume=target_value,
        target_volume_unit=target_unit,
        scale_factor=factor,
        components=tuple(scaled_components),
        formula=("缩放倍数 = 目标体积 / 原始配方体积", "组分新用量 = 原始组分用量 x 缩放倍数"),
        warnings=tuple(warnings),
    )


def calculate_stock_dilution(
    stock_concentration: str,
    target_concentration: str,
    target_volume: object,
    volume_unit: str,
    *,
    output_volume_unit: str | None = None,
) -> CalculationResult:
    stock_x = _parse_x_concentration(stock_concentration, "stock 浓度")
    target_x = _parse_x_concentration(target_concentration, "目标浓度")
    volume_value = parse_number(target_volume, "目标体积", allow_zero=False)
    source_volume_unit = canonical_unit(volume_unit)
    output_unit = canonical_unit(output_volume_unit or source_volume_unit)
    if unit_kind(source_volume_unit) != "volume" or unit_kind(output_unit) != "volume":
        raise CalculationError("体积单位必须是 L、mL 或 µL。")
    if target_x > stock_x:
        raise CalculationError("目标工作浓度高于 stock 浓度，不能通过稀释获得。")

    target_l = volume_to_l(volume_value, source_volume_unit)
    stock_l = target_x * target_l / stock_x
    solvent_l = target_l - stock_l
    stock_volume = l_to_volume(stock_l, output_unit)
    solvent_volume = l_to_volume(solvent_l, output_unit)
    return CalculationResult(
        title="stock-to-working 稀释计算",
        input_summary=(
            f"stock 浓度：{format_number(stock_x)}×",
            f"目标浓度：{format_number(target_x)}×",
            f"目标体积：{format_number(volume_value)} {source_volume_unit}",
        ),
        formula=("C1V1 = C2V2", "V1 = C2 x V2 / C1", "补足体积 = 目标体积 - stock 体积"),
        result_lines=(
            f"所需 stock 体积：{format_number(stock_volume)} {output_unit}",
            f"所需补足体积：{format_number(solvent_volume)} {output_unit}",
        ),
        review_tip=RECIPE_REVIEW_NOTICE,
        result_value=stock_volume,
        result_unit=output_unit,
        record_inputs={
            "stock_concentration": stock_x,
            "target_concentration": target_x,
            "target_volume": volume_value,
            "target_volume_unit": source_volume_unit,
        },
        record_outputs={
            "stock_volume": stock_volume,
            "solvent_volume": solvent_volume,
            "volume_unit": output_unit,
        },
    )


def _parse_x_concentration(value: str, field_name: str) -> float:
    text = str(value or "").strip()
    if not text:
        raise CalculationError(f"请填写{field_name}。")
    normalized = text.replace("X", "x").replace("×", "x")
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*x\s*", normalized)
    if not match:
        raise CalculationError(f"{field_name}需使用 10×、5×、1× 这类格式。")
    return parse_number(match.group(1), field_name, allow_zero=False)
