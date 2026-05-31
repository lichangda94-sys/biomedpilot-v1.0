from __future__ import annotations

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeDraft, RecipeError
from app.labtools.recipes.recipe_source_draft import extraction_draft_to_recipe_draft
from app.labtools.recipes.recipe_source_models import (
    NETWORK_DISABLED_MESSAGE,
    SOURCE_REVIEW_NOTICE,
    RecipeExtractionDraft,
    RecipeSourceCard,
    RecipeSourceRequest,
    utc_timestamp,
)
from app.labtools.recipes.recipe_source_validation import (
    validate_extraction_draft,
    validate_source_card,
    validate_source_request,
)


class RecipeSourceImporter:
    """Disabled-by-default source workflow; no external network calls are made."""

    def search_sources(self, request: RecipeSourceRequest) -> tuple[RecipeSourceCard, ...]:
        validate_source_request(request)
        return ()

    def disabled_network_message(self) -> str:
        return NETWORK_DISABLED_MESSAGE

    def create_manual_source_card(
        self,
        *,
        source_url: str,
        source_title: str,
        snippet: str,
        source_label: str = "用户手动录入来源",
        accessed_at: str | None = None,
    ) -> RecipeSourceCard:
        card = RecipeSourceCard(
            title=source_title.strip(),
            source_url=source_url.strip(),
            source_label=source_label.strip() or "用户手动录入来源",
            snippet=snippet.strip(),
            accessed_at=accessed_at or utc_timestamp(),
            trust_note=SOURCE_REVIEW_NOTICE,
            network_status="手动录入；未访问网络",
        )
        validate_source_card(card)
        return card

    def create_extraction_draft(
        self,
        *,
        source_card: RecipeSourceCard,
        recipe_name: str,
        extracted_components: tuple[RecipeComponent, ...],
        extracted_notes: tuple[str, ...] = (),
        safety_notes: tuple[str, ...] = (),
        preparation_notes: tuple[str, ...] = (),
        warnings: tuple[str, ...] = (),
        edited_by_user: bool = True,
    ) -> RecipeExtractionDraft:
        draft = RecipeExtractionDraft(
            source_card=source_card,
            recipe_name=recipe_name.strip(),
            extracted_components=extracted_components,
            extracted_notes=extracted_notes,
            safety_notes=safety_notes,
            preparation_notes=preparation_notes,
            warnings=warnings,
            edited_by_user=edited_by_user,
            user_confirmed=False,
        )
        validate_extraction_draft(draft)
        return draft

    def to_user_recipe_draft(
        self,
        extraction_draft: RecipeExtractionDraft,
        *,
        default_volume: float,
        default_volume_unit: str,
        stock_concentration: str = "1×",
    ) -> RecipeDraft:
        if extraction_draft.user_confirmed:
            raise RecipeError("来源摘录需要先转为用户配方草稿，再由用户确认保存。")
        return extraction_draft_to_recipe_draft(
            extraction_draft,
            default_volume=default_volume,
            default_volume_unit=default_volume_unit,
            stock_concentration=stock_concentration,
        )
