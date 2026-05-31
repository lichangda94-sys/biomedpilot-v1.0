from __future__ import annotations

from app.labtools.recipes.recipe_library import default_recipe_library


def test_default_recipe_library_lists_local_builtins() -> None:
    library = default_recipe_library()
    names = [recipe.name for recipe in library.list_recipes(include_user_defined=False)]

    assert "PBS 1× 参考配方" in names
    assert "TAE 50× 参考配方" in names
    assert "Agarose Gel 1% 参考计算" in names
    assert "RIPA Buffer 示例框架" in names
    assert len(names) >= 9


def test_builtins_are_local_reference_recipes_with_review_notice() -> None:
    recipe = default_recipe_library().get_recipe("pbs_1x_reference")

    assert recipe is not None
    assert recipe.source_label == "BioMedPilot 内置科研参考配方"
    assert recipe.is_user_defined is False
    assert "实验室 SOP" in recipe.review_notice
    assert all("http" not in note.lower() for note in recipe.preparation_notes + recipe.safety_notes)
