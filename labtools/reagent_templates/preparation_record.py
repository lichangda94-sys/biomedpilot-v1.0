from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    generated_steps: tuple[str, ...] = ()
    exported_file_path: str = ""
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
            generated_steps=result.steps,
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
            generated_steps=tuple(self.generated_steps),
            warnings=tuple(self.warnings),
            errors=tuple(self.errors),
            exported_file_path=self.exported_file_path,
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
            "generated_steps": list(self.generated_steps),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "exported_file_path": self.exported_file_path,
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
            generated_steps=tuple(str(item) for item in _list_or_empty(payload.get("generated_steps"))),
            warnings=tuple(str(item) for item in _list_or_empty(payload.get("warnings"))),
            errors=tuple(str(item) for item in _list_or_empty(payload.get("errors"))),
            exported_file_path=str(payload.get("exported_file_path") or ""),
            review_notice=str(payload.get("review_notice") or REAGENT_TEMPLATE_REVIEW_NOTICE),
            schema_version=str(payload.get("schema_version") or LABTOOLS_PREPARATION_RECORD_SCHEMA_VERSION),
        )

    def as_text(self) -> str:
        request = self.request_snapshot
        target_volume = request.get("target_volume", "")
        target_unit = request.get("target_volume_unit", "")
        loss_text = _loss_text(request)
        lines = [
            "本次制备摘要",
            f"试剂名称：{self.template_name}",
            f"使用模板：{self.template_name}",
            f"模板基准体积：{self.template_snapshot.get('default_volume', '')} {self.template_snapshot.get('default_volume_unit', '')}",
            f"目标体积：{target_volume} {target_unit}".strip(),
            f"损耗设置：{loss_text}",
            f"建议实际制备体积：{_suggested_volume_from_components(self, target_volume, target_unit)}",
            f"子模板展开：{'是' if request.get('expand_subtemplates') else '否'}",
            f"生成时间：{self.created_at}",
            f"历史记录 ID：{self.record_id}",
            "",
            "组分换算清单",
        ]
        lines.extend(_record_component_lines(self.primary_components))
        if self.expanded_subtemplates:
            lines.extend(["", "完整展开清单"])
            for child in self.expanded_subtemplates:
                lines.extend(_tree_dict_lines(child))
        if self.ph_records:
            lines.extend(["", "pH / 调节记录"])
            for entry in self.ph_records:
                ph_record = entry.get("ph_record") or {}
                lines.append(f"- {entry.get('template_name', '')}: {_ph_record_dict_line(ph_record)}")
        if self.warnings:
            lines.extend(["", "警告信息", *self.warnings])
        lines.extend(["", "制备步骤"])
        lines.extend(f"{index}. {step}" for index, step in enumerate(self.generated_steps, start=1))
        lines.extend(["", "人工核对提示", self.review_notice])
        return "\n".join(lines)

    def export_text(self, directory: str | Path, *, filename: str | None = None) -> Path:
        target_dir = Path(directory).expanduser().resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = filename or f"{_safe_filename(self.template_name)}_{self.created_at[:10]}_preparation.txt"
        path = target_dir / _safe_filename(safe_name)
        path.write_text(self.as_text() + "\n", encoding="utf-8")
        return path


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


def _loss_text(request: dict[str, Any]) -> str:
    mode = request.get("loss_mode") or "none"
    if mode == "percent":
        return f"{request.get('loss_percent', 0)}%"
    if mode == "fixed_amount":
        return f"+{request.get('loss_fixed_amount', 0)} {request.get('loss_fixed_unit', '')}".strip()
    overage = request.get("overage_percent", 0)
    return "0%" if not overage else f"{overage}%"


def _suggested_volume_from_components(record: PreparationRecord, target_volume: object, target_unit: object) -> str:
    request = record.request_snapshot
    target = float(target_volume or 0)
    if request.get("loss_mode") == "percent":
        suggested = target * (1 + float(request.get("loss_percent") or request.get("overage_percent") or 0) / 100)
        return f"{suggested:g} {target_unit}"
    if request.get("loss_mode") == "fixed_amount":
        return f"{target:g} {target_unit} + {request.get('loss_fixed_amount', 0)} {request.get('loss_fixed_unit', '')}".strip()
    overage = float(request.get("overage_percent") or 0)
    return f"{target * (1 + overage / 100):g} {target_unit}"


def _record_component_lines(components: tuple[dict[str, Any], ...]) -> list[str]:
    lines: list[str] = []
    for component in sorted(components, key=lambda item: (int(item.get("addition_order") or 0), str(item.get("name") or ""))):
        stage = component.get("stage_label") or f"Stage {component.get('addition_order') or 0}"
        amount = component.get("display_amount") or f"{component.get('amount', '')} {component.get('unit', '')}".strip()
        volume_text = "是" if component.get("is_auto_fill") or component.get("component_type") in {"liquid", "commercial_reagent", "solvent"} else "否"
        notes = component.get("notes") or ""
        lines.append(
            f"{stage} - {component.get('name', '')}：{amount}；类型：{component.get('component_type', '')}；计入终体积：{volume_text}；备注：{notes}"
        )
    return lines


def _tree_dict_lines(node: dict[str, Any], depth: int = 0) -> list[str]:
    indent = "  " * depth
    lines = [f"{indent}- {node.get('template_name', '')}: {node.get('suggested_volume', '')} {node.get('suggested_volume_unit', '')}"]
    components = node.get("components") if isinstance(node.get("components"), list) else []
    lines.extend(f"{indent}  {line}" for line in _record_component_lines(tuple(_dict_or_empty(item) for item in components)))
    children = node.get("children") if isinstance(node.get("children"), list) else []
    for child in children:
        lines.extend(_tree_dict_lines(_dict_or_empty(child), depth + 1))
    return lines


def _ph_record_dict_line(ph_record: dict[str, Any]) -> str:
    parts = []
    if ph_record.get("target_ph"):
        parts.append(f"目标 pH: {ph_record['target_ph']}")
    if ph_record.get("measured_ph"):
        parts.append(f"实测 pH: {ph_record['measured_ph']}")
    if ph_record.get("adjustment_note"):
        parts.append(f"调节说明: {ph_record['adjustment_note']}")
    return "；".join(parts) if parts else "pH 记录待填写"


def _safe_filename(value: str) -> str:
    text = "".join("_" if char in '<>:"/\\|?*' or ord(char) < 32 else char for char in str(value or "reagent"))
    text = text.strip(" ._")
    return text or "reagent_preparation.txt"


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []
