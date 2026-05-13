from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RECIPE_REVIEW_NOTICE = "配方仅供科研实验参考，请结合实验室 SOP、试剂说明书和安全规范人工复核。"


class RecipeError(ValueError):
    """User-facing recipe validation error."""


@dataclass(frozen=True)
class RecipeComponent:
    name: str
    amount: float
    unit: str
    role: str
    optional: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "amount": self.amount,
            "unit": self.unit,
            "role": self.role,
            "optional": self.optional,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    name: str
    category: str
    description: str
    stock_concentration: str
    default_volume: float
    default_volume_unit: str
    components: tuple[RecipeComponent, ...]
    preparation_notes: tuple[str, ...]
    safety_notes: tuple[str, ...]
    source_label: str
    version: str
    is_user_defined: bool = False
    review_notice: str = RECIPE_REVIEW_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "stock_concentration": self.stock_concentration,
            "default_volume": self.default_volume,
            "default_volume_unit": self.default_volume_unit,
            "components": [component.to_dict() for component in self.components],
            "preparation_notes": list(self.preparation_notes),
            "safety_notes": list(self.safety_notes),
            "source_label": self.source_label,
            "version": self.version,
            "is_user_defined": self.is_user_defined,
            "review_notice": self.review_notice,
        }


@dataclass(frozen=True)
class RecipeDraft:
    name: str
    category: str
    description: str
    stock_concentration: str
    default_volume: float
    default_volume_unit: str
    components: tuple[RecipeComponent, ...]
    preparation_notes: tuple[str, ...] = ()
    safety_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScaledComponent:
    name: str
    original_amount: float
    original_unit: str
    scaled_amount: float | None
    scaled_unit: str
    role: str
    notes: str = ""

    def line(self, formatter) -> str:
        if self.scaled_amount is None:
            return f"{self.name}：{self.original_amount:g} {self.original_unit}（{self.notes}）"
        return f"{self.name}：{formatter(self.scaled_amount)} {self.scaled_unit}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "original_amount": self.original_amount,
            "original_unit": self.original_unit,
            "scaled_amount": self.scaled_amount,
            "scaled_unit": self.scaled_unit,
            "role": self.role,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class RecipeScalingResult:
    recipe_name: str
    original_volume: float
    original_volume_unit: str
    target_volume: float
    target_volume_unit: str
    scale_factor: float
    components: tuple[ScaledComponent, ...]
    formula: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    review_notice: str = RECIPE_REVIEW_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "original_volume": self.original_volume,
            "original_volume_unit": self.original_volume_unit,
            "target_volume": self.target_volume,
            "target_volume_unit": self.target_volume_unit,
            "scale_factor": self.scale_factor,
            "components": [component.to_dict() for component in self.components],
            "formula": list(self.formula),
            "warnings": list(self.warnings),
            "review_notice": self.review_notice,
        }

    def as_text(self, formatter) -> str:
        lines = [
            f"配方：{self.recipe_name}",
            f"原始配方体积：{formatter(self.original_volume)} {self.original_volume_unit}",
            f"目标体积：{formatter(self.target_volume)} {self.target_volume_unit}",
            f"缩放倍数：{formatter(self.scale_factor)}",
            "",
            "组分新用量",
        ]
        lines.extend(component.line(formatter) for component in self.components)
        lines.extend(["", "公式说明", *self.formula])
        if self.warnings:
            lines.extend(["", "提示", *self.warnings])
        lines.extend(["", "复核提示", self.review_notice])
        return "\n".join(lines)
