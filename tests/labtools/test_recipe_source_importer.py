from __future__ import annotations

import pytest

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeError
from app.labtools.recipes.recipe_source_importer import RecipeSourceImporter
from app.labtools.recipes.recipe_source_models import NETWORK_DISABLED_MESSAGE, RecipeSourceRequest


def test_source_importer_search_returns_no_results_without_network() -> None:
    importer = RecipeSourceImporter()

    results = importer.search_sources(RecipeSourceRequest(query_text="PBS"))

    assert results == ()
    assert importer.disabled_network_message() == NETWORK_DISABLED_MESSAGE


def test_source_importer_rejects_network_enabled_request() -> None:
    importer = RecipeSourceImporter()

    with pytest.raises(RecipeError, match="未启用外部网络检索"):
        importer.search_sources(RecipeSourceRequest(query_text="PBS", network_enabled=True))


def test_manual_source_to_recipe_draft_flow_stays_unconfirmed() -> None:
    importer = RecipeSourceImporter()
    card = importer.create_manual_source_card(
        source_url="https://example.org/pbs",
        source_title="Manual PBS source",
        snippet="PBS manual source summary",
    )
    extraction = importer.create_extraction_draft(
        source_card=card,
        recipe_name="PBS manual draft",
        extracted_components=(RecipeComponent("NaCl", 8.0, "g", "salt"),),
        extracted_notes=("manual excerpt",),
        preparation_notes=("manual only",),
        warnings=("需要人工核对",),
    )

    draft = importer.to_user_recipe_draft(extraction, default_volume=1000, default_volume_unit="mL")

    assert draft.name == "PBS manual draft"
    assert draft.user_confirmed is False
    assert draft.source_title == "Manual PBS source"
    assert draft.to_dict()["source_url"] == "https://example.org/pbs"


def test_importer_blocks_high_risk_manual_source_content() -> None:
    importer = RecipeSourceImporter()

    with pytest.raises(RecipeError, match="危险化学品"):
        importer.create_manual_source_card(
            source_url="https://example.org/high-risk",
            source_title="High risk source",
            snippet="包含剧毒详细制备内容",
        )
