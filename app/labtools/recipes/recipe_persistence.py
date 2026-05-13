from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.labtools.recipes.recipe_models import RECIPE_REVIEW_NOTICE, Recipe, RecipeComponent, RecipeError
from app.labtools.recipes.recipe_validation import validate_recipe


LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION = "labtools_recipe_draft_store.v1"
RECIPE_DRAFT_EXPORT_TYPE = "labtools_user_recipe_draft_store"
SOFTWARE_CHANNEL = "Developer Preview / testing"
RECIPE_DRAFT_REVIEW_STATUS = "manual_review_required"
RECIPE_DRAFT_PERSISTENCE_NOTE = (
    "本地 JSON 仅保存用户确认的 recipe draft；仅在用户明确选择路径后写盘，"
    "不自动保存、不联网、不调用 AI、不替代实验 SOP。"
)
RECIPE_DRAFT_SAFETY_NOTE = (
    "本地配方草稿仅用于常规科研实验记录和复用。使用前需人工核对实验室 SOP、"
    "试剂说明书、SDS 和安全规范；不构成临床、诊断或安全操作建议。"
)
BLOCKED_SCOPE_TERMS = (
    "氰化",
    "cyanide",
    "叠氮",
    "azide",
    "剧毒",
    "toxin",
    "毒素",
    "放射性",
    "radioactive",
    "爆炸",
    "explosive",
    "动物实验",
    "animal protocol",
    "人体实验",
    "human subject",
    "病毒包装",
    "viral packaging",
    "高风险合成",
    "合成路线",
)


@dataclass(frozen=True)
class RecipeSafetyReview:
    status: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    review_notice: str = RECIPE_DRAFT_SAFETY_NOTE

    @property
    def allowed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
        }


@dataclass(frozen=True)
class RecipeStorePersistenceResult:
    success: bool
    path: str
    schema_version: str
    recipe_count: int
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    review_notice: str = RECIPE_DRAFT_SAFETY_NOTE

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "schema_version": self.schema_version,
            "recipe_count": self.recipe_count,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
        }


@dataclass(frozen=True)
class RecipeStoreLoadResult:
    success: bool
    path: str
    schema_version: str
    recipes: tuple[Recipe, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    review_notice: str = RECIPE_DRAFT_SAFETY_NOTE

    @property
    def recipe_count(self) -> int:
        return len(self.recipes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "schema_version": self.schema_version,
            "recipe_count": self.recipe_count,
            "recipes": [recipe.to_dict() for recipe in self.recipes],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
        }


def evaluate_recipe_safety(recipe: Recipe) -> RecipeSafetyReview:
    validate_recipe(recipe)
    haystack = _recipe_text(recipe).lower()
    matches = tuple(term for term in BLOCKED_SCOPE_TERMS if term.lower() in haystack)
    if matches:
        return RecipeSafetyReview(
            status="blocked_high_risk_scope",
            errors=(
                "配方草稿包含高风险化学品、毒物、高风险合成、动物/人体实验或病毒相关关键词；"
                "LabTools 不保存此类操作草稿。",
            ),
            warnings=matches,
        )
    return RecipeSafetyReview(
        status=RECIPE_DRAFT_REVIEW_STATUS,
        warnings=("本地草稿保存前已完成基础范围检查；仍需人工核对 SOP、SDS 和试剂说明书。",),
    )


def build_user_recipe_store_payload(recipes: tuple[Recipe, ...]) -> dict[str, Any]:
    reviews = [evaluate_recipe_safety(recipe).to_dict() for recipe in recipes]
    return {
        "schema_version": LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION,
        "export_type": RECIPE_DRAFT_EXPORT_TYPE,
        "created_at": _utc_now(),
        "software_channel": SOFTWARE_CHANNEL,
        "review_status": RECIPE_DRAFT_REVIEW_STATUS,
        "recipe_count": len(recipes),
        "recipes": [recipe.to_dict() for recipe in recipes],
        "safety_reviews": reviews,
        "safety_note": RECIPE_DRAFT_SAFETY_NOTE,
        "persistence_note": RECIPE_DRAFT_PERSISTENCE_NOTE,
    }


def save_user_recipe_store(recipes: tuple[Recipe, ...], output_path: str | Path | None) -> RecipeStorePersistenceResult:
    path = _resolve_output_file(output_path)
    payload = build_user_recipe_store_payload(recipes)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError as exc:
        raise RecipeError("保存目标文件已存在，已停止以避免覆盖。") from exc
    except OSError as exc:
        raise RecipeError("无法写入用户配方草稿文件，请检查路径权限。") from exc
    return RecipeStorePersistenceResult(
        success=True,
        path=str(path),
        schema_version=LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION,
        recipe_count=len(recipes),
        warnings=("仅保存用户确认配方；未保存内置参考配方、网络内容或自动建议。",),
    )


def load_user_recipe_store(input_path: str | Path | None) -> RecipeStoreLoadResult:
    path = _input_file(input_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RecipeError("用户配方草稿文件不是有效 JSON。") from exc
    except OSError as exc:
        raise RecipeError("无法读取用户配方草稿文件。") from exc
    if payload.get("schema_version") != LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION:
        raise RecipeError("用户配方草稿文件 schema 不匹配。")
    raw_recipes = payload.get("recipes")
    if not isinstance(raw_recipes, list):
        raise RecipeError("用户配方草稿文件缺少 recipes 列表。")
    recipes = tuple(_recipe_from_dict(item) for item in raw_recipes)
    for recipe in recipes:
        review = evaluate_recipe_safety(recipe)
        if not review.allowed:
            raise RecipeError(review.errors[0])
    return RecipeStoreLoadResult(
        success=True,
        path=str(path),
        schema_version=LABTOOLS_RECIPE_DRAFT_STORE_SCHEMA_VERSION,
        recipes=recipes,
        warnings=("载入结果仍为本地草稿；使用前需人工核对 SOP、SDS 和试剂说明书。",),
    )


def clone_imported_user_recipe(recipe: Recipe) -> Recipe:
    return replace(
        recipe,
        recipe_id=f"user_recipe_imported_{uuid4().hex[:12]}",
        is_user_defined=True,
        user_confirmed=True,
        review_notice=RECIPE_REVIEW_NOTICE,
    )


def _recipe_from_dict(payload: Any) -> Recipe:
    if not isinstance(payload, dict):
        raise RecipeError("recipes 列表包含无效配方记录。")
    components = payload.get("components")
    if not isinstance(components, list):
        raise RecipeError("配方记录缺少 components 列表。")
    recipe = Recipe(
        recipe_id=str(payload.get("recipe_id") or f"user_recipe_imported_{uuid4().hex[:12]}"),
        name=str(payload.get("name") or ""),
        category=str(payload.get("category") or "用户自定义"),
        description=str(payload.get("description") or "用户配方草稿"),
        stock_concentration=str(payload.get("stock_concentration") or "1×"),
        default_volume=float(payload.get("default_volume") or 0),
        default_volume_unit=str(payload.get("default_volume_unit") or "mL"),
        components=tuple(_component_from_dict(component) for component in components),
        preparation_notes=tuple(str(note) for note in payload.get("preparation_notes") or ()),
        safety_notes=tuple(str(note) for note in payload.get("safety_notes") or ()),
        source_label=str(payload.get("source_label") or "本地 JSON 载入"),
        version=str(payload.get("version") or "local-draft"),
        is_user_defined=True,
        review_notice=str(payload.get("review_notice") or RECIPE_REVIEW_NOTICE),
        source_url=str(payload.get("source_url") or ""),
        source_title=str(payload.get("source_title") or ""),
        accessed_at=str(payload.get("accessed_at") or ""),
        user_confirmed=bool(payload.get("user_confirmed", True)),
        edited_by_user=bool(payload.get("edited_by_user", True)),
    )
    validate_recipe(recipe)
    return recipe


def _component_from_dict(payload: Any) -> RecipeComponent:
    if not isinstance(payload, dict):
        raise RecipeError("配方组分记录无效。")
    return RecipeComponent(
        name=str(payload.get("name") or ""),
        amount=float(payload.get("amount") or 0),
        unit=str(payload.get("unit") or ""),
        role=str(payload.get("role") or "用户配方组分"),
        optional=bool(payload.get("optional", False)),
        notes=str(payload.get("notes") or ""),
    )


def _recipe_text(recipe: Recipe) -> str:
    fields: list[str] = [
        recipe.name,
        recipe.category,
        recipe.description,
        recipe.source_label,
        recipe.source_title,
    ]
    for component in recipe.components:
        fields.extend([component.name, component.role, component.notes])
    fields.extend(recipe.preparation_notes)
    fields.extend(recipe.safety_notes)
    return "\n".join(fields)


def _resolve_output_file(output_path: str | Path | None) -> Path:
    if output_path is None or str(output_path).strip() == "":
        raise RecipeError("请选择用户配方草稿保存路径。")
    requested = Path(output_path).expanduser()
    if requested.exists() and requested.is_dir():
        requested = requested / "labtools_user_recipe_drafts.json"
    if requested.suffix.lower() != ".json":
        requested = requested.with_suffix(".json")
    parent = requested.parent
    if not parent.exists() or not parent.is_dir():
        raise RecipeError("保存路径所在文件夹不存在。")
    return _non_overwriting_path(requested)


def _input_file(input_path: str | Path | None) -> Path:
    if input_path is None or str(input_path).strip() == "":
        raise RecipeError("请选择用户配方草稿 JSON 文件。")
    path = Path(input_path).expanduser()
    if not path.exists() or not path.is_file():
        raise RecipeError("用户配方草稿 JSON 文件不存在。")
    return path


def _non_overwriting_path(path: Path) -> Path:
    safe_name = _sanitize_filename(path.stem)
    candidate = path.with_name(f"{safe_name}{path.suffix}")
    for index in range(1000):
        numbered = candidate if index == 0 else candidate.with_name(f"{safe_name}_{index:03d}{path.suffix}")
        if not numbered.exists():
            return numbered
    raise RecipeError("保存目录中同名文件过多，请选择新的保存路径。")


def _sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return sanitized[:96] or "labtools_user_recipe_drafts"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
