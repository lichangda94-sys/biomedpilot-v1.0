from __future__ import annotations

from app.labtools.recipes.built_in_recipes import built_in_recipes
from app.labtools.recipes.recipe_models import Recipe


class RecipeLibrary:
    def __init__(self, recipes: tuple[Recipe, ...] | None = None) -> None:
        self._recipes = tuple(recipes or ())
        self._by_id = {recipe.recipe_id: recipe for recipe in self._recipes}

    def list_recipes(self, *, include_user_defined: bool = True) -> tuple[Recipe, ...]:
        if include_user_defined:
            return self._recipes
        return tuple(recipe for recipe in self._recipes if not recipe.is_user_defined)

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        return self._by_id.get(recipe_id)

    def with_user_recipes(self, recipes: tuple[Recipe, ...]) -> "RecipeLibrary":
        return RecipeLibrary(self._recipes + tuple(recipes))


def default_recipe_library() -> RecipeLibrary:
    return RecipeLibrary(built_in_recipes())
