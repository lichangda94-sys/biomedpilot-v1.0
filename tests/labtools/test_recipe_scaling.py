from __future__ import annotations

import pytest

from app.labtools.calculators.calculator_models import CalculationError
from app.labtools.recipes.recipe_library import default_recipe_library
from app.labtools.recipes.recipe_models import Recipe, RecipeComponent
from app.labtools.recipes.recipe_scaling import calculate_stock_dilution, scale_recipe


def test_scale_recipe_linearly_scales_mass_and_volume_units() -> None:
    recipe = default_recipe_library().get_recipe("pbs_1x_reference")
    assert recipe is not None

    result = scale_recipe(recipe, 500, "mL")

    assert result.scale_factor == pytest.approx(0.5)
    nacl = next(component for component in result.components if component.name == "NaCl")
    water = next(component for component in result.components if component.name == "纯化水补足至")
    assert nacl.scaled_amount == pytest.approx(4.0)
    assert water.scaled_amount == pytest.approx(500.0)
    assert "请结合实验室 SOP" in result.as_text(lambda value: f"{value:g}")


def test_scale_recipe_warns_for_non_linear_units() -> None:
    recipe = Recipe(
        recipe_id="non_linear",
        name="非线性单位测试",
        category="测试",
        description="测试",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("目标比例", 1, "%w/v", "浓度"),),
        preparation_notes=(),
        safety_notes=(),
        source_label="测试",
        version="v1",
    )

    result = scale_recipe(recipe, 200, "mL")

    assert result.components[0].scaled_amount is None
    assert "不能线性缩放" in result.warnings[0]


def test_stock_to_working_dilution_uses_c1v1_formula() -> None:
    result = calculate_stock_dilution("10×", "1×", 100, "mL", output_volume_unit="mL")

    assert result.result_value == pytest.approx(10)
    assert result.record_outputs["solvent_volume"] == pytest.approx(90)
    assert "C1V1 = C2V2" in result.as_text()


def test_stock_to_working_rejects_invalid_inputs() -> None:
    with pytest.raises(CalculationError, match="不能通过稀释获得"):
        calculate_stock_dilution("1×", "5×", 100, "mL")
    with pytest.raises(CalculationError, match="目标体积必须大于 0"):
        calculate_stock_dilution("10×", "1×", 0, "mL")
    with pytest.raises(CalculationError, match="需使用"):
        calculate_stock_dilution("ten", "1×", 100, "mL")
