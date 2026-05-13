from __future__ import annotations

import pytest

from app.labtools.recipes.recipe_models import RECIPE_REVIEW_NOTICE, Recipe, RecipeComponent, RecipeDraft, RecipeError
from app.labtools.recipes.recipe_validation import validate_recipe, validate_recipe_draft


def test_recipe_exports_json_compatible_dict() -> None:
    recipe = Recipe(
        recipe_id="test_recipe",
        name="测试配方",
        category="测试",
        description="本地测试配方",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("NaCl", 1.0, "g", "主要盐"),),
        preparation_notes=("按 SOP 复核。",),
        safety_notes=("按安全规范复核。",),
        source_label="本地测试",
        version="v1",
    )

    payload = recipe.to_dict()

    assert payload["recipe_id"] == "test_recipe"
    assert payload["components"][0]["name"] == "NaCl"
    assert payload["review_notice"] == RECIPE_REVIEW_NOTICE


def test_recipe_validation_requires_name_components_and_volume() -> None:
    recipe = Recipe(
        recipe_id="bad",
        name="",
        category="测试",
        description="",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("NaCl", 1.0, "g", "主要盐"),),
        preparation_notes=(),
        safety_notes=(),
        source_label="本地测试",
        version="v1",
    )

    with pytest.raises(RecipeError, match="请填写配方名称"):
        validate_recipe(recipe)


def test_recipe_draft_validation_rejects_bad_component_unit() -> None:
    draft = RecipeDraft(
        name="用户配方",
        category="用户",
        description="用户输入",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("未知组分", 1, "ppm", "用户输入"),),
    )

    with pytest.raises(RecipeError, match="单位暂不支持"):
        validate_recipe_draft(draft)
