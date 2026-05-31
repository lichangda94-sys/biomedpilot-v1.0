from __future__ import annotations

from app.labtools.recipes.recipe_models import RecipeComponent
from app.labtools.recipes.recipe_source_models import (
    NETWORK_DISABLED_MESSAGE,
    RecipeExtractionDraft,
    RecipeSourceCard,
    RecipeSourceRequest,
)


def test_source_request_defaults_to_network_disabled() -> None:
    request = RecipeSourceRequest(query_text="PBS protocol")

    payload = request.to_dict()

    assert payload["network_enabled"] is False
    assert payload["query_text"] == "PBS protocol"
    assert payload["created_at"]
    assert NETWORK_DISABLED_MESSAGE == "当前版本未启用外部网络检索。"


def test_source_card_and_extraction_draft_export_json_compatible_dict() -> None:
    card = RecipeSourceCard(
        title="Manual PBS note",
        source_url="https://example.org/pbs",
        source_label="用户手动录入来源",
        snippet="PBS summary",
        accessed_at="2026-05-13T00:00:00+00:00",
        trust_note="需要人工复核",
        network_status="手动录入；未访问网络",
    )
    draft = RecipeExtractionDraft(
        source_card=card,
        recipe_name="PBS manual draft",
        extracted_components=(RecipeComponent("NaCl", 8.0, "g", "buffer salt"),),
        extracted_notes=("manual excerpt",),
        safety_notes=("review SDS",),
        preparation_notes=("manual entry only",),
        warnings=("人工核对",),
    )

    payload = draft.to_dict()

    assert payload["source_card"]["source_url"] == "https://example.org/pbs"
    assert payload["extracted_components"][0]["name"] == "NaCl"
    assert payload["user_confirmed"] is False
    assert payload["edited_by_user"] is True
