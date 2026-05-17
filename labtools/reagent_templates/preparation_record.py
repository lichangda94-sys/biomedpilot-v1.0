from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from labtools.reagent_templates.models import (
    LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION,
    REAGENT_TEMPLATE_REVIEW_NOTICE,
    PHRecord,
    PreparationComponentResult,
    PreparationRequest,
    PreparationResult,
    PreparationStageGroup,
    PreparationTreeNode,
    ReagentTemplate,
    utc_now,
)


class PreparationRecordError(ValueError):
    pass


@dataclass(frozen=True)
class PreparationRecord:
    record_id: str
    created_at: str
    updated_at: str
    template_id: str
    template_name: str
    template_snapshot: dict[str, Any]
    request_snapshot: dict[str, Any]
    primary_components: tuple[dict[str, Any], ...]
    expanded_subtemplates: tuple[dict[str, Any], ...]
    ph_records: tuple[dict[str, Any], ...]
    staged_steps: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    review_notice: str = REAGENT_TEMPLATE_REVIEW_NOTICE
    schema_version: str = LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION

    @classmethod
    def from_result(
        cls,
        result: PreparationResult,
        template: ReagentTemplate,
        request: PreparationRequest,
        *,
        record_id: str | None = None,
        created_at: str | None = None,
    ) -> "PreparationRecord":
        now = utc_now()
        return cls(
            record_id=record_id or f"reagent_preparation_{uuid4().hex}",
            created_at=created_at or now,
            updated_at=now,
            template_id=result.template_id,
            template_name=result.template_name,
            template_snapshot=template.to_dict(),
            request_snapshot=_request_snapshot(request),
            primary_components=tuple(_component_to_dict(component) for component in result.direct_components),
            expanded_subtemplates=tuple(_tree_node_to_dict(child) for child in result.tree.children),
            ph_records=tuple(_ph_record_entries(result.tree)),
            staged_steps=tuple(_stage_group_to_dict(group) for group in result.direct_stage_groups),
            warnings=result.warnings,
            errors=(),
            review_notice=result.review_notice,
        )

    @property
    def summary_status(self) -> str:
        if self.errors:
            return "Error"
        if self.warnings:
            return "Warning"
        return "OK"

    def with_updated_timestamp(self) -> "PreparationRecord":
        return PreparationRecord(
            record_id=self.record_id,
            created_at=self.created_at,
            updated_at=utc_now(),
            template_id=self.template_id,
            template_name=self.template_name,
            template_snapshot=dict(self.template_snapshot),
            request_snapshot=dict(self.request_snapshot),
            primary_components=tuple(dict(item) for item in self.primary_components),
            expanded_subtemplates=tuple(dict(item) for item in self.expanded_subtemplates),
            ph_records=tuple(dict(item) for item in self.ph_records),
            staged_steps=tuple(dict(item) for item in self.staged_steps),
            warnings=tuple(self.warnings),
            errors=tuple(self.errors),
            review_notice=self.review_notice,
            schema_version=self.schema_version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "template_snapshot": self.template_snapshot,
            "request_snapshot": self.request_snapshot,
            "primary_components": list(self.primary_components),
            "expanded_subtemplates": list(self.expanded_subtemplates),
            "ph_records": list(self.ph_records),
            "staged_steps": list(self.staged_steps),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "review_notice": self.review_notice,
            "summary_status": self.summary_status,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "PreparationRecord":
        if not isinstance(payload, dict):
            raise PreparationRecordError("配置试剂记录 payload 必须是 JSON object。")
        if payload.get("schema_version") != LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION:
            raise PreparationRecordError("配置试剂记录 schema 不匹配。")
        return cls(
            record_id=str(payload.get("record_id") or ""),
            created_at=str(payload.get("created_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
            template_id=str(payload.get("template_id") or ""),
            template_name=str(payload.get("template_name") or ""),
            template_snapshot=_dict_or_empty(payload.get("template_snapshot")),
            request_snapshot=_dict_or_empty(payload.get("request_snapshot")),
            primary_components=tuple(_dict_or_empty(item) for item in _list_or_empty(payload.get("primary_components"))),
            expanded_subtemplates=tuple(_dict_or_empty(item) for item in _list_or_empty(payload.get("expanded_subtemplates"))),
            ph_records=tuple(_dict_or_empty(item) for item in _list_or_empty(payload.get("ph_records"))),
            staged_steps=tuple(_dict_or_empty(item) for item in _list_or_empty(payload.get("staged_steps"))),
            warnings=tuple(str(item) for item in _list_or_empty(payload.get("warnings"))),
            errors=tuple(str(item) for item in _list_or_empty(payload.get("errors"))),
            review_notice=str(payload.get("review_notice") or REAGENT_TEMPLATE_REVIEW_NOTICE),
            schema_version=str(payload.get("schema_version") or LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION),
        )


def _request_snapshot(request: PreparationRequest) -> dict[str, Any]:
    return {
        "template_id": request.template_id,
        "target_volume": request.target_volume,
        "target_volume_unit": request.target_volume_unit,
        "target_strength": request.target_strength,
        "overage_percent": request.overage_percent,
        "loss_mode": request.loss_mode,
        "loss_percent": request.loss_percent,
        "loss_fixed_amount": request.loss_fixed_amount,
        "loss_fixed_unit": request.loss_fixed_unit,
        "expand_subtemplates": request.expand_subtemplates,
        "operator_name": request.operator_name,
        "notes": request.notes,
    }


def _component_to_dict(component: PreparationComponentResult) -> dict[str, Any]:
    return {
        "name": component.name,
        "component_type": component.component_type,
        "amount": component.amount,
        "unit": component.unit,
        "display_amount": component.display_amount,
        "addition_order": component.addition_order,
        "stage_label": component.stage_label,
        "is_commercial": component.is_commercial,
        "is_subtemplate": component.is_subtemplate,
        "referenced_template_id": component.referenced_template_id,
        "is_auto_fill": component.is_auto_fill,
        "initial_addition_display": component.initial_addition_display,
        "initial_addition_detail": component.initial_addition_detail,
        "notes": component.notes,
        "warnings": list(component.warnings),
    }


def _stage_group_to_dict(group: PreparationStageGroup) -> dict[str, Any]:
    return {
        "addition_order": group.addition_order,
        "stage_label": group.stage_label,
        "components": [_component_to_dict(component) for component in group.components],
    }


def _tree_node_to_dict(node: PreparationTreeNode) -> dict[str, Any]:
    return {
        "template_id": node.template_id,
        "template_name": node.template_name,
        "target_volume": node.target_volume,
        "target_volume_unit": node.target_volume_unit,
        "suggested_volume": node.suggested_volume,
        "suggested_volume_unit": node.suggested_volume_unit,
        "components": [_component_to_dict(component) for component in node.components],
        "stage_groups": [_stage_group_to_dict(group) for group in node.stage_groups],
        "ph_record": _ph_record_to_dict(node.ph_record),
        "children": [_tree_node_to_dict(child) for child in node.children],
    }


def _ph_record_entries(node: PreparationTreeNode) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if node.ph_record is not None and _ph_has_content(node.ph_record):
        entries.append(
            {
                "template_id": node.template_id,
                "template_name": node.template_name,
                "ph_record": _ph_record_to_dict(node.ph_record),
            }
        )
    for child in node.children:
        entries.extend(_ph_record_entries(child))
    return entries


def _ph_has_content(ph_record: PHRecord) -> bool:
    return bool(ph_record.target_ph.strip() or ph_record.measured_ph.strip() or ph_record.adjustment_note.strip())


def _ph_record_to_dict(ph_record: PHRecord | None) -> dict[str, Any] | None:
    if ph_record is None:
        return None
    return ph_record.to_dict()


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []
