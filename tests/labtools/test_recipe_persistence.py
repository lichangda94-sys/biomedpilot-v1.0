from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.labtools.recipes.recipe_models import RecipeComponent, RecipeDraft, RecipeError
from app.labtools.recipes.recipe_persistence import (
    LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION,
    build_user_recipe_store_payload,
    evaluate_recipe_safety,
    load_user_recipe_store,
    save_user_recipe_store,
)
from app.labtools.recipes.user_recipe_store import UserRecipeStore


def _draft(name: str = "用户 PBS 草稿") -> RecipeDraft:
    return RecipeDraft(
        name=name,
        category="用户自定义",
        description="常规缓冲液草稿，仅用于本地持久化测试",
        stock_concentration="1×",
        default_volume=100,
        default_volume_unit="mL",
        components=(RecipeComponent("NaCl", 0.8, "g", "主要盐"),),
        preparation_notes=("用户草稿；按实验室 SOP 复核。",),
        safety_notes=("按 SDS 和安全规范复核。",),
        edited_by_user=True,
    )


def test_user_recipe_store_payload_has_schema_and_manual_review_semantics() -> None:
    store = UserRecipeStore()
    recipe = store.confirm_draft(_draft())

    payload = build_user_recipe_store_payload(store.list_recipes())

    assert payload["schema_version"] == LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION
    assert payload["export_type"] == "labtools_user_recipe_draft_store"
    assert payload["software_channel"] == "Developer Preview / testing"
    assert payload["review_status"] == "manual_review_required"
    assert payload["recipe_count"] == 1
    assert payload["recipes"][0]["recipe_id"] == recipe.recipe_id
    assert "不自动保存、不联网、不调用 AI" in payload["persistence_note"]
    assert "人工核对" in payload["safety_note"]
    assert payload["safety_reviews"][0]["status"] == "manual_review_required"


def test_save_and_load_user_recipe_store_round_trip(tmp_path) -> None:
    store = UserRecipeStore()
    recipe = store.confirm_draft(_draft())
    target = tmp_path / "my drafts.json"

    save_result = save_user_recipe_store(store.list_recipes(), target)
    load_result = load_user_recipe_store(save_result.path)

    saved_path = Path(save_result.path)
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert save_result.success is True
    assert saved_path.name == "my_drafts.json"
    assert payload["schema_version"] == LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION
    assert load_result.success is True
    assert load_result.recipe_count == 1
    assert load_result.recipes[0].name == recipe.name
    assert "人工核对" in load_result.review_notice


def test_save_user_recipe_store_does_not_overwrite_existing_file(tmp_path) -> None:
    store = UserRecipeStore()
    store.confirm_draft(_draft())
    target = tmp_path / "drafts.json"

    first = save_user_recipe_store(store.list_recipes(), target)
    first_text = Path(first.path).read_text(encoding="utf-8")
    second = save_user_recipe_store(store.list_recipes(), target)

    assert first.path != second.path
    assert Path(first.path).read_text(encoding="utf-8") == first_text
    assert Path(second.path).name == "drafts_001.json"


def test_load_user_recipe_store_rejects_bad_schema(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": "old", "recipes": []}), encoding="utf-8")

    with pytest.raises(RecipeError, match="schema 不匹配"):
        load_user_recipe_store(path)


def test_save_user_recipe_store_rejects_missing_parent(tmp_path) -> None:
    store = UserRecipeStore()
    store.confirm_draft(_draft())

    with pytest.raises(RecipeError, match="保存路径所在文件夹不存在"):
        save_user_recipe_store(store.list_recipes(), tmp_path / "missing" / "drafts.json")


def test_load_user_recipe_store_rejects_missing_path() -> None:
    with pytest.raises(RecipeError, match="请选择用户配方草稿 JSON 文件"):
        load_user_recipe_store("")


def test_safety_review_blocks_high_risk_recipe_scope() -> None:
    store = UserRecipeStore()
    dangerous = _draft("氰化物高风险合成路线")

    with pytest.raises(RecipeError, match="高风险化学品"):
        store.confirm_draft(dangerous)


def test_safe_recipe_review_keeps_auxiliary_draft_semantics() -> None:
    store = UserRecipeStore()
    recipe = store.confirm_draft(_draft())

    review = evaluate_recipe_safety(recipe)

    assert review.allowed is True
    assert review.status == "manual_review_required"
    assert "SOP" in review.review_notice


def test_user_recipe_import_summary_reports_id_conflicts_without_overwrite() -> None:
    store = UserRecipeStore()
    recipe = store.confirm_draft(_draft())

    result = store.import_recipes_with_summary((recipe,))

    recipes = store.list_recipes()
    assert result.imported_count == 1
    assert result.conflict_count == 1
    assert "未覆盖现有用户配方" in result.warnings[0]
    assert len(recipes) == 2
    assert recipes[0].recipe_id == recipe.recipe_id
    assert result.imported_recipes[0].recipe_id != recipe.recipe_id
    assert result.imported_recipes[0].version == recipe.version
