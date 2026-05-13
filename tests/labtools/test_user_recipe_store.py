from __future__ import annotations

import pytest

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeDraft, RecipeError
from app.labtools.recipes.user_recipe_store import UserRecipeStore


def test_user_recipe_store_confirms_draft_in_memory_only() -> None:
    store = UserRecipeStore()
    draft = RecipeDraft(
        name="用户 PBS 变体",
        category="用户自定义",
        description="仅测试内存结构",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("NaCl", 0.8, "g", "主要盐"),),
        preparation_notes=("按 SOP 复核。",),
        safety_notes=("按安全规范复核。",),
    )

    recipe = store.confirm_draft(draft)
    payload = store.export_dict()

    assert recipe.is_user_defined is True
    assert recipe.recipe_id.startswith("user_recipe_")
    assert store.list_recipes() == (recipe,)
    assert payload["user_recipes"][0]["name"] == "用户 PBS 变体"


def test_user_recipe_store_requires_confirmed_valid_draft() -> None:
    store = UserRecipeStore()
    bad_draft = RecipeDraft(
        name="",
        category="用户",
        description="",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("NaCl", 0.8, "g", "主要盐"),),
    )

    with pytest.raises(RecipeError, match="请填写配方名称"):
        store.confirm_draft(bad_draft)
