from __future__ import annotations

from app.labtools.recipes.recipe_models import RECIPE_REVIEW_NOTICE, RecipeDraft
from app.labtools.recipes.recipe_source_models import RecipeExtractionDraft, SOURCE_REVIEW_NOTICE
from app.labtools.recipes.recipe_source_validation import validate_extraction_draft
from app.labtools.recipes.recipe_validation import validate_recipe_draft


def extraction_draft_to_recipe_draft(
    draft: RecipeExtractionDraft,
    *,
    default_volume: float,
    default_volume_unit: str,
    stock_concentration: str = "1×",
    category: str = "用户来源摘录",
    description: str | None = None,
) -> RecipeDraft:
    validate_extraction_draft(draft)
    summary = description or f"由用户手动摘录来源生成的配方草稿：{draft.source_card.title}"
    preparation_notes = (
        *draft.preparation_notes,
        *draft.extracted_notes,
        "来源摘录已转为用户配方草稿；确认前请逐项核对组分、单位和适用范围。",
    )
    safety_notes = (
        *draft.safety_notes,
        SOURCE_REVIEW_NOTICE,
        RECIPE_REVIEW_NOTICE,
    )
    warnings = "; ".join(draft.warnings)
    if warnings:
        safety_notes = (*safety_notes, f"摘录提示：{warnings}")
    recipe_draft = RecipeDraft(
        name=draft.recipe_name.strip(),
        category=category,
        description=summary,
        stock_concentration=stock_concentration.strip() or "1×",
        default_volume=default_volume,
        default_volume_unit=default_volume_unit,
        components=draft.extracted_components,
        preparation_notes=preparation_notes,
        safety_notes=safety_notes,
        source_label=f"手动来源摘录：{draft.source_card.source_label}",
        version="user-source-draft",
        source_url=draft.source_card.source_url,
        source_title=draft.source_card.title,
        accessed_at=draft.source_card.accessed_at,
        user_confirmed=False,
        edited_by_user=draft.edited_by_user,
    )
    validate_recipe_draft(recipe_draft)
    return recipe_draft
