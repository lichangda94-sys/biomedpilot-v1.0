from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION = "labtools_reagent_template_store.v1"
REAGENT_TEMPLATE_REVIEW_NOTICE = (
    "本结果基于用户录入模板自动换算，仅用于实验准备辅助。"
    "请根据实验室 SOP、试剂说明书和安全规范人工复核。"
)

COMPONENT_TYPES = (
    "liquid",
    "powder",
    "commercial_reagent",
    "solvent",
    "ph_adjustment",
    "self_prepared_template",
)

SUPPORTED_TEMPLATE_UNITS = ("L", "mL", "µL", "g", "mg", "µg", "M", "mM", "µM", "%", "X")


class ReagentTemplateError(ValueError):
    """User-facing error for reagent template validation and calculation."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_template_id() -> str:
    return f"reagent_template_{uuid4().hex[:12]}"


@dataclass(frozen=True)
class CommercialReagentInfo:
    concentration: str = ""
    lot_number: str = ""
    supplier: str = ""
    storage_condition: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "concentration": self.concentration,
            "lot_number": self.lot_number,
            "supplier": self.supplier,
            "storage_condition": self.storage_condition,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "CommercialReagentInfo":
        if not isinstance(payload, dict):
            return cls()
        return cls(
            concentration=str(payload.get("concentration") or ""),
            lot_number=str(payload.get("lot_number") or ""),
            supplier=str(payload.get("supplier") or ""),
            storage_condition=str(payload.get("storage_condition") or ""),
            notes=str(payload.get("notes") or ""),
        )


@dataclass(frozen=True)
class ReagentComponent:
    name: str
    component_type: str
    base_amount: float
    unit: str
    scale_with_volume: bool = True
    scale_with_strength: bool = False
    contributes_to_final_volume: bool = False
    auto_fill_to_final_volume: bool = False
    notes: str = ""
    referenced_template_id: str = ""
    commercial_info: CommercialReagentInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "component_type": self.component_type,
            "base_amount": self.base_amount,
            "unit": self.unit,
            "scale_with_volume": self.scale_with_volume,
            "scale_with_strength": self.scale_with_strength,
            "contributes_to_final_volume": self.contributes_to_final_volume,
            "auto_fill_to_final_volume": self.auto_fill_to_final_volume,
            "notes": self.notes,
            "referenced_template_id": self.referenced_template_id,
            "commercial_info": self.commercial_info.to_dict() if self.commercial_info is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "ReagentComponent":
        if not isinstance(payload, dict):
            raise ReagentTemplateError("组分记录必须是 JSON object。")
        commercial_payload = payload.get("commercial_info")
        return cls(
            name=str(payload.get("name") or ""),
            component_type=str(payload.get("component_type") or ""),
            base_amount=float(payload.get("base_amount") or 0),
            unit=str(payload.get("unit") or ""),
            scale_with_volume=bool(payload.get("scale_with_volume", True)),
            scale_with_strength=bool(payload.get("scale_with_strength", False)),
            contributes_to_final_volume=bool(payload.get("contributes_to_final_volume", False)),
            auto_fill_to_final_volume=bool(payload.get("auto_fill_to_final_volume", False)),
            notes=str(payload.get("notes") or ""),
            referenced_template_id=str(payload.get("referenced_template_id") or ""),
            commercial_info=CommercialReagentInfo.from_dict(commercial_payload) if isinstance(commercial_payload, dict) else None,
        )


@dataclass(frozen=True)
class ReagentTemplate:
    template_id: str
    name: str
    default_volume: float
    default_volume_unit: str
    default_strength: str = "1X"
    notes: str = ""
    components: tuple[ReagentComponent, ...] = ()
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        default_volume: float,
        default_volume_unit: str = "mL",
        default_strength: str = "1X",
        notes: str = "",
        components: tuple[ReagentComponent, ...] = (),
    ) -> "ReagentTemplate":
        now = utc_now()
        return cls(
            template_id=new_template_id(),
            name=name,
            default_volume=default_volume,
            default_volume_unit=default_volume_unit,
            default_strength=default_strength,
            notes=notes,
            components=components,
            created_at=now,
            updated_at=now,
        )

    def renamed_copy(self) -> "ReagentTemplate":
        now = utc_now()
        return replace(
            self,
            template_id=new_template_id(),
            name=f"{self.name} 副本",
            created_at=now,
            updated_at=now,
        )

    def with_updated_timestamp(self) -> "ReagentTemplate":
        return replace(self, updated_at=utc_now())

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "default_volume": self.default_volume,
            "default_volume_unit": self.default_volume_unit,
            "default_strength": self.default_strength,
            "notes": self.notes,
            "components": [component.to_dict() for component in self.components],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "ReagentTemplate":
        if not isinstance(payload, dict):
            raise ReagentTemplateError("模板记录必须是 JSON object。")
        components = payload.get("components")
        if not isinstance(components, list):
            raise ReagentTemplateError("模板缺少 components 列表。")
        return cls(
            template_id=str(payload.get("template_id") or new_template_id()),
            name=str(payload.get("name") or ""),
            default_volume=float(payload.get("default_volume") or 0),
            default_volume_unit=str(payload.get("default_volume_unit") or "mL"),
            default_strength=str(payload.get("default_strength") or "1X"),
            notes=str(payload.get("notes") or ""),
            components=tuple(ReagentComponent.from_dict(component) for component in components),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
        )


@dataclass(frozen=True)
class PreparationRequest:
    template_id: str
    target_volume: float
    target_volume_unit: str = "mL"
    target_strength: str = "1X"
    overage_percent: float = 0
    expand_subtemplates: bool = False


@dataclass(frozen=True)
class PreparationComponentResult:
    name: str
    component_type: str
    amount: float | None
    unit: str
    display_amount: str
    is_commercial: bool = False
    is_subtemplate: bool = False
    referenced_template_id: str = ""
    is_auto_fill: bool = False
    notes: str = ""
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreparationTreeNode:
    template_id: str
    template_name: str
    target_volume: float
    target_volume_unit: str
    suggested_volume: float
    suggested_volume_unit: str
    components: tuple[PreparationComponentResult, ...]
    children: tuple["PreparationTreeNode", ...] = ()


@dataclass(frozen=True)
class PreparationResult:
    title: str
    template_id: str
    template_name: str
    target_volume: float
    target_volume_unit: str
    suggested_volume: float
    suggested_volume_unit: str
    target_strength: str
    overage_percent: float
    direct_components: tuple[PreparationComponentResult, ...]
    tree: PreparationTreeNode
    warnings: tuple[str, ...]
    steps: tuple[str, ...]
    ph_record_fields: tuple[str, ...] = ("目标 pH", "实测 pH", "pH 调节备注")
    review_notice: str = REAGENT_TEMPLATE_REVIEW_NOTICE

    def as_text(self) -> str:
        lines = [
            self.title,
            f"目标试剂名称：{self.template_name}",
            f"目标最终体积：{_fmt(self.target_volume)} {self.target_volume_unit}",
            f"建议配制体积：{_fmt(self.suggested_volume)} {self.suggested_volume_unit}",
            f"目标倍数/浓度：{self.target_strength}",
            "",
            "一级配制清单",
        ]
        lines.extend(_component_line(component) for component in self.direct_components)
        if self.tree.children:
            lines.extend(["", "完整展开清单"])
            lines.extend(_tree_lines(self.tree))
        if self.warnings:
            lines.extend(["", "警告信息", *self.warnings])
        lines.extend(["", "pH 记录字段", *self.ph_record_fields, "", "配制步骤", *self.steps, "", "人工复核提示", self.review_notice])
        return "\n".join(lines)


def _fmt(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _component_line(component: PreparationComponentResult) -> str:
    tags: list[str] = []
    if component.is_commercial:
        tags.append("商品化试剂")
    if component.is_subtemplate:
        tags.append("自配子试剂")
    if component.is_auto_fill:
        tags.append("溶剂补足")
    tag_text = f"（{' / '.join(tags)}）" if tags else ""
    note_text = f"；{component.notes}" if component.notes else ""
    return f"- {component.name}{tag_text}: {component.display_amount}{note_text}"


def _tree_lines(node: PreparationTreeNode, depth: int = 0) -> list[str]:
    indent = "  " * depth
    lines = [f"{indent}- {node.template_name}: {_fmt(node.suggested_volume)} {node.suggested_volume_unit}"]
    for component in node.components:
        lines.append(f"{indent}  {_component_line(component)}")
    for child in node.children:
        lines.extend(_tree_lines(child, depth + 1))
    return lines
