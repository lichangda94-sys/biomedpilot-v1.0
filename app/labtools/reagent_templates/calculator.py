from __future__ import annotations

import math
import re

from app.labtools.calculators.calculator_models import CalculationError
from app.labtools.calculators.unit_conversion import canonical_unit, format_number, l_to_volume, unit_kind, volume_to_l
from app.labtools.reagent_templates.models import (
    COMPONENT_TYPES,
    SUPPORTED_TEMPLATE_UNITS,
    PreparationComponentResult,
    PreparationRequest,
    PreparationResult,
    PreparationTreeNode,
    ReagentComponent,
    ReagentTemplate,
    ReagentTemplateError,
)


def validate_template(template: ReagentTemplate, templates: tuple[ReagentTemplate, ...] = ()) -> None:
    if not template.template_id.strip():
        raise ReagentTemplateError("模板缺少 template_id。")
    if not template.name.strip():
        raise ReagentTemplateError("请填写模板名称。")
    if template.default_volume <= 0:
        raise ReagentTemplateError("默认配制体积必须大于 0。")
    _canonical_template_unit(template.default_volume_unit)
    _parse_strength(template.default_strength, "默认倍数或浓度")
    auto_fill_count = sum(1 for component in template.components if component.auto_fill_to_final_volume)
    if auto_fill_count > 1:
        raise ReagentTemplateError("每个模板最多只能有一个自动补足至最终体积的组分。")
    for component in template.components:
        _validate_component(component)
    if templates:
        detect_template_cycles(templates)


def detect_template_cycles(templates: tuple[ReagentTemplate, ...]) -> None:
    template_map = {template.template_id: template for template in templates}
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(template_id: str) -> None:
        if template_id in visiting:
            cycle = visiting[visiting.index(template_id) :] + [template_id]
            names = [template_map[item].name for item in cycle if item in template_map]
            raise ReagentTemplateError("检测到模板循环引用：" + " -> ".join(names or cycle))
        if template_id in visited or template_id not in template_map:
            return
        visiting.append(template_id)
        for component in template_map[template_id].components:
            if component.referenced_template_id:
                visit(component.referenced_template_id)
        visiting.pop()
        visited.add(template_id)

    for template in templates:
        visit(template.template_id)


def calculate_preparation(request: PreparationRequest, templates: tuple[ReagentTemplate, ...]) -> PreparationResult:
    template_map = {template.template_id: template for template in templates}
    if request.template_id not in template_map:
        raise ReagentTemplateError("请选择有效试剂模板。")
    if request.target_volume <= 0:
        raise ReagentTemplateError("本次目标体积必须大于 0。")
    if request.overage_percent < 0:
        raise ReagentTemplateError("损耗系数不能为负数。")
    for template in templates:
        validate_template(template)
    detect_template_cycles(templates)

    root = _calculate_node(
        template_map[request.template_id],
        template_map,
        target_volume=request.target_volume,
        target_volume_unit=request.target_volume_unit,
        target_strength=request.target_strength,
        overage_percent=request.overage_percent,
        expand_subtemplates=request.expand_subtemplates,
        stack=(),
    )
    warnings = tuple(_collect_warnings(root))
    steps = _build_steps(root)
    return PreparationResult(
        title=f"{root.template_name} 本次配制清单",
        template_id=root.template_id,
        template_name=root.template_name,
        target_volume=request.target_volume,
        target_volume_unit=_canonical_template_unit(request.target_volume_unit),
        suggested_volume=root.suggested_volume,
        suggested_volume_unit=root.suggested_volume_unit,
        target_strength=request.target_strength,
        overage_percent=request.overage_percent,
        direct_components=root.components,
        tree=root,
        warnings=warnings,
        steps=steps,
    )


def _calculate_node(
    template: ReagentTemplate,
    template_map: dict[str, ReagentTemplate],
    *,
    target_volume: float,
    target_volume_unit: str,
    target_strength: str,
    overage_percent: float,
    expand_subtemplates: bool,
    stack: tuple[str, ...],
) -> PreparationTreeNode:
    if template.template_id in stack:
        raise ReagentTemplateError("检测到模板循环引用。")
    target_unit = _canonical_template_unit(target_volume_unit)
    target_l = volume_to_l(target_volume, target_unit)
    suggested_l = target_l * (1 + overage_percent / 100)
    suggested_volume = l_to_volume(suggested_l, target_unit)
    default_l = volume_to_l(template.default_volume, template.default_volume_unit)
    volume_factor = suggested_l / default_l
    strength_factor = _parse_strength(target_strength, "本次目标倍数") / _parse_strength(template.default_strength, "模板默认倍数")

    children: list[PreparationTreeNode] = []
    preliminary: list[PreparationComponentResult] = []
    volume_total_l = 0.0
    auto_fill_component: ReagentComponent | None = None

    for component in template.components:
        if component.auto_fill_to_final_volume:
            auto_fill_component = component
            continue
        result = _component_result(component, volume_factor=volume_factor, strength_factor=strength_factor)
        preliminary.append(result)
        if component.contributes_to_final_volume and result.amount is not None:
            volume_total_l += _volume_amount_to_l(result.amount, result.unit, component.name)
        if result.is_subtemplate and component.referenced_template_id not in template_map:
            raise ReagentTemplateError(f"{component.name} 引用的子模板不存在。")
        if result.is_subtemplate and result.amount is not None and expand_subtemplates:
            child_template = template_map.get(component.referenced_template_id)
            if child_template is None:
                raise ReagentTemplateError(f"{component.name} 引用的子模板不存在。")
            if unit_kind(_canonical_template_unit(result.unit)) != "volume":
                raise ReagentTemplateError(f"{component.name} 引用子模板时，本次需求量必须是体积单位。")
            children.append(
                _calculate_node(
                    child_template,
                    template_map,
                    target_volume=result.amount,
                    target_volume_unit=result.unit,
                    target_strength=child_template.default_strength,
                    overage_percent=0,
                    expand_subtemplates=expand_subtemplates,
                    stack=stack + (template.template_id,),
                )
            )

    if auto_fill_component is not None:
        remaining_l = suggested_l - volume_total_l
        if remaining_l < -1e-12:
            raise ReagentTemplateError("参与最终体积的组分总量已经超过建议配制体积，无法自动补足溶剂。")
        remaining_l = max(0.0, remaining_l)
        fill_unit = _canonical_template_unit(auto_fill_component.unit)
        fill_amount = l_to_volume(remaining_l, fill_unit)
        preliminary.append(
            PreparationComponentResult(
                name=auto_fill_component.name,
                component_type=auto_fill_component.component_type,
                amount=fill_amount,
                unit=fill_unit,
                display_amount=f"{format_number(fill_amount)} {fill_unit}",
                is_auto_fill=True,
                notes=auto_fill_component.notes or "自动补足至建议配制体积",
            )
        )

    return PreparationTreeNode(
        template_id=template.template_id,
        template_name=template.name,
        target_volume=target_volume,
        target_volume_unit=target_unit,
        suggested_volume=suggested_volume,
        suggested_volume_unit=target_unit,
        components=tuple(preliminary),
        children=tuple(children),
    )


def _component_result(component: ReagentComponent, *, volume_factor: float, strength_factor: float) -> PreparationComponentResult:
    factor = 1.0
    if component.scale_with_volume:
        factor *= volume_factor
    if component.scale_with_strength:
        factor *= strength_factor
    amount = component.base_amount * factor
    unit = _canonical_template_unit(component.unit)
    warnings: list[str] = []
    if component.contributes_to_final_volume and unit_kind(unit) != "volume":
        warnings.append("该组分标记为参与最终体积，但单位不是体积单位，已排除自动补足计算。")
    if component.component_type == "self_prepared_template" and not component.referenced_template_id:
        raise ReagentTemplateError(f"{component.name} 是自配试剂模板组分，但未引用子模板。")
    return PreparationComponentResult(
        name=component.name,
        component_type=component.component_type,
        amount=amount,
        unit=unit,
        display_amount=f"{format_number(amount)} {unit}",
        is_commercial=component.component_type == "commercial_reagent",
        is_subtemplate=bool(component.referenced_template_id),
        referenced_template_id=component.referenced_template_id,
        notes=component.notes,
        warnings=tuple(warnings),
    )


def _build_steps(root: PreparationTreeNode) -> tuple[str, ...]:
    has_child = bool(root.children)
    has_auto_fill = any(component.is_auto_fill for component in root.components)
    has_commercial = any(component.is_commercial for component in root.components)
    steps = [
        "准备合适容器并核对模板名称、日期、操作者和目标体积。",
        "先加入部分溶剂或基础液体，保留补足空间。",
    ]
    if has_child:
        steps.append("需要时先按完整展开清单配制自配子试剂，并记录其批次或配制日期。")
    if has_commercial:
        steps.append("核对商品化试剂名称、浓度、批号、供应商和保存条件后再加入。")
    steps.extend(
        [
            "按一级配制清单顺序加入各组分并混匀。",
            "需要时记录目标 pH、实测 pH 和 pH 调节备注；软件不预测酸碱加入量。",
        ]
    )
    if has_auto_fill:
        steps.append("用标记为自动补足的溶剂补足至建议配制体积。")
    steps.extend(
        [
            "混匀后标记名称、日期、操作者、保存条件和人工复核状态。",
            "本步骤为通用准备清单，不替代实验室 SOP、SDS 或试剂说明书。",
        ]
    )
    return tuple(steps)


def _collect_warnings(node: PreparationTreeNode) -> list[str]:
    warnings: list[str] = []
    for component in node.components:
        warnings.extend(component.warnings)
    for child in node.children:
        warnings.extend(_collect_warnings(child))
    return warnings


def _validate_component(component: ReagentComponent) -> None:
    if not component.name.strip():
        raise ReagentTemplateError("组分名称不能为空。")
    if component.component_type not in COMPONENT_TYPES:
        raise ReagentTemplateError(f"暂不支持组分类型：{component.component_type}。")
    if component.base_amount < 0 or not math.isfinite(component.base_amount):
        raise ReagentTemplateError("组分基准用量必须是非负数字。")
    unit = _canonical_template_unit(component.unit)
    if component.auto_fill_to_final_volume and unit_kind(unit) != "volume":
        raise ReagentTemplateError("自动补足组分必须使用体积单位。")
    if component.component_type == "self_prepared_template" and not component.referenced_template_id.strip():
        raise ReagentTemplateError("自配试剂模板组分必须引用子模板。")


def _canonical_template_unit(unit: str) -> str:
    text = str(unit or "").strip()
    alias = {"uL": "µL", "ul": "µL", "μL": "µL", "ug": "µg", "μg": "µg", "uM": "µM", "μM": "µM", "x": "X", "×": "X"}
    canonical = alias.get(text, text)
    if canonical in {"%", "X"}:
        return canonical
    try:
        normalized = canonical_unit(canonical)
    except CalculationError as exc:
        raise ReagentTemplateError(str(exc)) from exc
    if normalized not in SUPPORTED_TEMPLATE_UNITS:
        raise ReagentTemplateError(f"L3 试剂模板暂不支持单位：{text}。")
    return normalized


def _parse_strength(value: str, field_name: str) -> float:
    text = str(value or "").strip()
    if not text or text in {"原液", "stock", "Stock"}:
        return 1.0
    normalized = text.replace("×", "X").replace("x", "X")
    if normalized.endswith("X"):
        number = normalized[:-1].strip()
        return _positive_float(number, field_name)
    if normalized.endswith("%"):
        number = normalized[:-1].strip()
        return _positive_float(number, field_name) / 100
    return _positive_float(normalized, field_name)


def _positive_float(value: str, field_name: str) -> float:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value or ""):
        raise ReagentTemplateError(f"{field_name}必须是 1X、0.5X、100% 或数字。")
    number = float(value)
    if number <= 0:
        raise ReagentTemplateError(f"{field_name}必须大于 0。")
    return number


def _volume_amount_to_l(amount: float, unit: str, component_name: str) -> float:
    if unit_kind(_canonical_template_unit(unit)) != "volume":
        raise ReagentTemplateError(f"{component_name} 参与最终体积但单位不是体积单位。")
    return volume_to_l(amount, unit)
