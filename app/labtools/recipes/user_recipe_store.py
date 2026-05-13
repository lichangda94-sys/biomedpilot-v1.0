from __future__ import annotations

from uuid import uuid4

from app.labtools.recipes.recipe_models import Recipe, RecipeDraft
from app.labtools.recipes.recipe_validation import validate_recipe_draft


class UserRecipeStore:
    def __init__(self) -> None:
        self._confirmed: dict[str, Recipe] = {}

    def confirm_draft(self, draft: RecipeDraft) -> Recipe:
        validate_recipe_draft(draft)
        recipe = Recipe(
            recipe_id=f"user_recipe_{uuid4().hex[:12]}",
            name=draft.name.strip(),
            category=draft.category.strip() or "用户自定义",
            description=draft.description.strip() or "用户自定义配方",
            stock_concentration=draft.stock_concentration.strip() or "1×",
            default_volume=draft.default_volume,
            default_volume_unit=draft.default_volume_unit,
            components=draft.components,
            preparation_notes=draft.preparation_notes,
            safety_notes=draft.safety_notes,
            source_label=draft.source_label.strip() or "用户自定义草稿确认",
            version=draft.version.strip() or "user-confirmed-draft",
            is_user_defined=True,
            source_url=draft.source_url.strip(),
            source_title=draft.source_title.strip(),
            accessed_at=draft.accessed_at.strip(),
            user_confirmed=True,
            edited_by_user=draft.edited_by_user,
        )
        self._confirmed[recipe.recipe_id] = recipe
        return recipe

    def list_recipes(self) -> tuple[Recipe, ...]:
        return tuple(self._confirmed.values())

    def export_dict(self) -> dict[str, object]:
        return {"user_recipes": [recipe.to_dict() for recipe in self.list_recipes()]}
