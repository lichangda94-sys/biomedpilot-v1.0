from __future__ import annotations

from urllib.parse import urlparse

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeError
from app.labtools.recipes.recipe_source_models import RecipeExtractionDraft, RecipeSourceCard, RecipeSourceRequest
from app.labtools.recipes.recipe_validation import validate_recipe_component


HIGH_RISK_TERMS = (
    "受管制物质",
    "爆炸物",
    "爆炸性",
    "剧毒",
    "氰化物",
    "氰化钠",
    "叠氮化钠",
    "汞盐",
    "放射性",
)


def _clean(value: object) -> str:
    return str(value or "").strip()


def contains_high_risk_detail(*values: object) -> bool:
    text = "\n".join(_clean(value) for value in values)
    return any(term in text for term in HIGH_RISK_TERMS)


def validate_source_url(source_url: str) -> None:
    url = _clean(source_url)
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RecipeError("来源 URL 仅允许填写 http 或 https 地址；本阶段不会访问该地址。")


def validate_source_request(request: RecipeSourceRequest) -> None:
    if not _clean(request.query_text):
        raise RecipeError("请填写检索需求或配方名称。")
    if request.network_enabled:
        raise RecipeError("当前版本未启用外部网络检索。")


def validate_source_card(card: RecipeSourceCard) -> None:
    if not _clean(card.title):
        raise RecipeError("请填写来源标题。")
    validate_source_url(card.source_url)
    if not _clean(card.snippet):
        raise RecipeError("请填写来源摘要或摘录。")
    if contains_high_risk_detail(card.title, card.snippet):
        raise RecipeError("当前阶段不保存危险化学品、毒性物质或受管制物质的详细制备内容。")


def validate_extracted_components(components: tuple[RecipeComponent, ...]) -> None:
    if not components:
        raise RecipeError("摘录草稿至少需要 1 个组分。")
    for component in components:
        validate_recipe_component(component)


def validate_extraction_draft(draft: RecipeExtractionDraft) -> None:
    validate_source_card(draft.source_card)
    if not _clean(draft.recipe_name):
        raise RecipeError("请填写摘录草稿的配方名称。")
    validate_extracted_components(draft.extracted_components)
    if contains_high_risk_detail(
        draft.recipe_name,
        *draft.extracted_notes,
        *draft.preparation_notes,
        *draft.safety_notes,
        *(component.name for component in draft.extracted_components),
    ):
        raise RecipeError("当前阶段不保存危险化学品、毒性物质或受管制物质的详细制备内容。")
