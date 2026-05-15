from __future__ import annotations

from app.labtools.recipes.recipe_models import RecipeComponent
from app.labtools.recipes.recipe_source_draft import extraction_draft_to_recipe_draft
from app.labtools.recipes.recipe_source_models import RecipeExtractionDraft, RecipeSourceCard
from app.labtools.recipes.user_recipe_store import UserRecipeStore


def _source_card() -> RecipeSourceCard:
    return RecipeSourceCard(
        title="Manual TBS source",
        source_url="https://example.org/tbs",
        source_label="用户手动来源",
        snippet="TBS manual summary",
        accessed_at="2026-05-13T00:00:00+00:00",
        trust_note="需要人工复核",
        network_status="手动录入；未访问网络",
    )


def test_extraction_draft_converts_to_unconfirmed_user_recipe_draft() -> None:
    extraction = RecipeExtractionDraft(
        source_card=_source_card(),
        recipe_name="TBS manual draft",
        extracted_components=(RecipeComponent("Tris", 2.42, "g", "buffer"),),
        extracted_notes=("手动摘录",),
        safety_notes=("按 SDS 复核",),
        preparation_notes=("未自动采集网页内容",),
    )

    recipe_draft = extraction_draft_to_recipe_draft(extraction, default_volume=1000, default_volume_unit="mL")

    assert recipe_draft.name == "TBS manual draft"
    assert recipe_draft.user_confirmed is False
    assert recipe_draft.edited_by_user is True
    assert recipe_draft.source_url == "https://example.org/tbs"
    assert "手动来源摘录" in recipe_draft.source_label


def test_source_recipe_draft_requires_store_confirm_before_saved() -> None:
    extraction = RecipeExtractionDraft(
        source_card=_source_card(),
        recipe_name="TBS manual draft",
        extracted_components=(RecipeComponent("Tris", 2.42, "g", "buffer"),),
        extracted_notes=(),
        safety_notes=(),
        preparation_notes=(),
    )
    recipe_draft = extraction_draft_to_recipe_draft(extraction, default_volume=1000, default_volume_unit="mL")
    store = UserRecipeStore()

    assert store.list_recipes() == ()

    recipe = store.confirm_draft(recipe_draft)

    assert recipe.user_confirmed is True
    assert recipe.source_title == "Manual TBS source"
    assert store.list_recipes() == (recipe,)
