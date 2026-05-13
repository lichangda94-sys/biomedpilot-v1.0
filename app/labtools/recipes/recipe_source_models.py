from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.labtools.recipes.recipe_models import RecipeComponent


SOURCE_REVIEW_NOTICE = "外部来源内容仅供参考，请结合实验室 SOP、试剂说明书和安全规范人工复核。"
NETWORK_DISABLED_MESSAGE = "当前版本未启用外部网络检索。"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class RecipeSourceRequest:
    query_text: str
    intended_recipe_name: str = ""
    user_goal: str = ""
    network_enabled: bool = False
    created_at: str = field(default_factory=utc_timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_text": self.query_text,
            "intended_recipe_name": self.intended_recipe_name,
            "user_goal": self.user_goal,
            "network_enabled": self.network_enabled,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RecipeSourceCard:
    title: str
    source_url: str
    source_label: str
    snippet: str
    accessed_at: str
    trust_note: str
    network_status: str
    source_id: str = field(default_factory=lambda: f"source_{uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "source_url": self.source_url,
            "source_label": self.source_label,
            "snippet": self.snippet,
            "accessed_at": self.accessed_at,
            "trust_note": self.trust_note,
            "network_status": self.network_status,
        }


@dataclass(frozen=True)
class RecipeExtractionDraft:
    source_card: RecipeSourceCard
    recipe_name: str
    extracted_components: tuple[RecipeComponent, ...]
    extracted_notes: tuple[str, ...]
    safety_notes: tuple[str, ...]
    preparation_notes: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    user_confirmed: bool = False
    edited_by_user: bool = True
    draft_id: str = field(default_factory=lambda: f"source_draft_{uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "source_card": self.source_card.to_dict(),
            "recipe_name": self.recipe_name,
            "extracted_components": [component.to_dict() for component in self.extracted_components],
            "extracted_notes": list(self.extracted_notes),
            "safety_notes": list(self.safety_notes),
            "preparation_notes": list(self.preparation_notes),
            "warnings": list(self.warnings),
            "user_confirmed": self.user_confirmed,
            "edited_by_user": self.edited_by_user,
        }
