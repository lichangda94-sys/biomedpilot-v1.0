from __future__ import annotations

import pytest

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeError
from app.labtools.recipes.recipe_source_models import RecipeSourceCard, RecipeSourceRequest
from app.labtools.recipes.recipe_source_validation import (
    validate_extracted_components,
    validate_source_card,
    validate_source_request,
    validate_source_url,
)


def test_source_request_rejects_enabled_network() -> None:
    request = RecipeSourceRequest(query_text="PBS", network_enabled=True)

    with pytest.raises(RecipeError, match="未启用外部网络检索"):
        validate_source_request(request)


def test_source_url_validation_does_not_allow_local_or_script_urls() -> None:
    with pytest.raises(RecipeError, match="http 或 https"):
        validate_source_url("file:///tmp/source.html")

    with pytest.raises(RecipeError, match="http 或 https"):
        validate_source_url("javascript:alert(1)")


def test_source_card_rejects_high_risk_preparation_content() -> None:
    card = RecipeSourceCard(
        title="unsafe note",
        source_url="https://example.org/unsafe",
        source_label="手动来源",
        snippet="包含受管制物质详细制备内容",
        accessed_at="2026-05-13T00:00:00+00:00",
        trust_note="人工复核",
        network_status="手动录入；未访问网络",
    )

    with pytest.raises(RecipeError, match="危险化学品"):
        validate_source_card(card)


def test_extracted_components_reuse_recipe_component_validation() -> None:
    with pytest.raises(RecipeError, match="请填写组分名称"):
        validate_extracted_components((RecipeComponent("", 1.0, "g", "salt"),))
