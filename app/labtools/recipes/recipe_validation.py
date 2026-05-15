from __future__ import annotations

from app.labtools.calculators.unit_conversion import canonical_unit, parse_number, unit_kind
from app.labtools.recipes.recipe_models import Recipe, RecipeComponent, RecipeDraft, RecipeError


LINEAR_UNIT_KINDS = {"mass", "volume"}


def is_linearly_scalable_unit(unit: str) -> bool:
    try:
        return unit_kind(unit) in LINEAR_UNIT_KINDS
    except Exception:
        return False


def validate_recipe_component(component: RecipeComponent) -> None:
    if not component.name.strip():
        raise RecipeError("请填写组分名称。")
    parse_number(component.amount, f"{component.name} 用量", allow_zero=False)
    if not component.unit.strip():
        raise RecipeError(f"请选择 {component.name} 的单位。")
    try:
        canonical_unit(component.unit)
    except Exception as exc:
        if component.unit not in {"%", "%w/v", "x", "×"}:
            raise RecipeError(f"{component.name} 的单位暂不支持：{component.unit}。") from exc


def validate_recipe(recipe: Recipe) -> None:
    if not recipe.name.strip():
        raise RecipeError("请填写配方名称。")
    if not recipe.components:
        raise RecipeError("至少需要 1 个配方组分。")
    parse_number(recipe.default_volume, "默认体积", allow_zero=False)
    try:
        if unit_kind(recipe.default_volume_unit) != "volume":
            raise RecipeError("默认体积单位必须是体积单位。")
    except RecipeError:
        raise
    except Exception as exc:
        raise RecipeError("默认体积单位必须是体积单位。") from exc
    for component in recipe.components:
        validate_recipe_component(component)


def validate_recipe_draft(draft: RecipeDraft) -> None:
    validate_recipe(
        Recipe(
            recipe_id="draft",
            name=draft.name,
            category=draft.category,
            description=draft.description,
            stock_concentration=draft.stock_concentration,
            default_volume=draft.default_volume,
            default_volume_unit=draft.default_volume_unit,
            components=draft.components,
            preparation_notes=draft.preparation_notes,
            safety_notes=draft.safety_notes,
            source_label="用户草稿",
            version="draft",
            is_user_defined=True,
        )
    )
