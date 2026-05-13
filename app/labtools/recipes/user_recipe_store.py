from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.labtools.recipes.recipe_models import Recipe, RecipeDraft
from app.labtools.recipes.recipe_persistence import clone_imported_user_recipe, evaluate_recipe_safety
from app.labtools.recipes.recipe_validation import validate_recipe_draft


@dataclass(frozen=True)
class UserRecipeImportResult:
    imported_recipes: tuple[Recipe, ...]
    conflict_count: int
    warnings: tuple[str, ...] = ()

    @property
    def imported_count(self) -> int:
        return len(self.imported_recipes)


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
        review = evaluate_recipe_safety(recipe)
        if not review.allowed:
            from app.labtools.recipes.recipe_models import RecipeError

            raise RecipeError(review.errors[0])
        self._confirmed[recipe.recipe_id] = recipe
        return recipe

    def import_recipes(self, recipes: tuple[Recipe, ...]) -> tuple[Recipe, ...]:
        return self.import_recipes_with_summary(recipes).imported_recipes

    def import_recipes_with_summary(self, recipes: tuple[Recipe, ...]) -> UserRecipeImportResult:
        imported: list[Recipe] = []
        conflict_count = 0
        for recipe in recipes:
            review = evaluate_recipe_safety(recipe)
            if not review.allowed:
                from app.labtools.recipes.recipe_models import RecipeError

                raise RecipeError(review.errors[0])
            candidate = recipe
            if candidate.recipe_id in self._confirmed:
                conflict_count += 1
                candidate = clone_imported_user_recipe(candidate)
            self._confirmed[candidate.recipe_id] = candidate
            imported.append(candidate)
        warnings = ()
        if conflict_count:
            warnings = (
                f"检测到 {conflict_count} 个 recipe_id 冲突；已作为 imported copy 保存，未覆盖现有用户配方。",
            )
        return UserRecipeImportResult(imported_recipes=tuple(imported), conflict_count=conflict_count, warnings=warnings)

    def list_recipes(self) -> tuple[Recipe, ...]:
        return tuple(self._confirmed.values())

    def export_dict(self) -> dict[str, object]:
        return {"user_recipes": [recipe.to_dict() for recipe in self.list_recipes()]}
