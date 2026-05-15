from __future__ import annotations

import json

import pytest

from app.labtools.reagent_templates import (
    LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION,
    CommercialReagentInfo,
    PreparationRequest,
    ReagentComponent,
    ReagentTemplate,
    ReagentTemplateError,
    ReagentTemplateStore,
    calculate_preparation,
)


def _component(
    name: str,
    amount: float,
    unit: str,
    *,
    component_type: str = "liquid",
    scale_with_volume: bool = True,
    scale_with_strength: bool = False,
    contributes_to_final_volume: bool = False,
    auto_fill: bool = False,
    referenced_template_id: str = "",
) -> ReagentComponent:
    return ReagentComponent(
        name=name,
        component_type=component_type,
        base_amount=amount,
        unit=unit,
        scale_with_volume=scale_with_volume,
        scale_with_strength=scale_with_strength,
        contributes_to_final_volume=contributes_to_final_volume,
        auto_fill_to_final_volume=auto_fill,
        referenced_template_id=referenced_template_id,
    )


def _template_a(*, child_id: str = "") -> ReagentTemplate:
    components = [
        _component("B", 10, "mL", contributes_to_final_volume=True),
        _component("D 固定添加剂", 2, "mg", scale_with_volume=False, component_type="powder"),
        ReagentComponent(
            name="商品化 E",
            component_type="commercial_reagent",
            base_amount=8,
            unit="mL",
            contributes_to_final_volume=True,
            commercial_info=CommercialReagentInfo(concentration="10X", lot_number="L001", supplier="Vendor", storage_condition="4C"),
        ),
        _component("水", 0, "mL", component_type="solvent", auto_fill=True),
    ]
    if child_id:
        components.insert(
            1,
            _component("试剂 C", 8, "mL", component_type="self_prepared_template", contributes_to_final_volume=True, referenced_template_id=child_id),
        )
    return ReagentTemplate.create(name="试剂 A", default_volume=100, components=tuple(components), notes="用户模板")


def _template_c() -> ReagentTemplate:
    return ReagentTemplate.create(
        name="试剂 C",
        default_volume=100,
        components=(
            _component("C1", 20, "mL", contributes_to_final_volume=True),
            _component("C powder", 1, "g", component_type="powder"),
            _component("C water", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )


def test_reagent_template_model_serializes_schema_fields() -> None:
    template = _template_a()
    payload = template.to_dict()
    restored = ReagentTemplate.from_dict(payload)

    assert restored.template_id == template.template_id
    assert restored.name == "试剂 A"
    assert restored.default_volume == 100
    assert restored.default_strength == "1X"
    assert restored.components[2].commercial_info is not None
    assert restored.components[2].commercial_info.lot_number == "L001"


def test_reagent_template_store_saves_loads_copies_and_requires_delete_confirmation(tmp_path) -> None:
    store = ReagentTemplateStore(tmp_path / "templates.json")
    template = _template_a()

    saved = store.upsert_template(template)
    loaded = store.load()

    assert loaded[0].template_id == saved.template_id
    assert json.loads((tmp_path / "templates.json").read_text(encoding="utf-8"))["schema_version"] == LABTOOLS_REAGENT_TEMPLATE_STORE_SCHEMA_VERSION

    copied = store.copy_template(saved.template_id)
    assert copied.template_id != saved.template_id
    assert copied.name.endswith("副本")
    with pytest.raises(ReagentTemplateError, match="确认"):
        store.delete_template(saved.template_id)
    remaining = store.delete_template(saved.template_id, confirmed=True)
    assert [template.template_id for template in remaining] == [copied.template_id]


def test_reagent_template_store_rejects_bad_json_and_schema(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ReagentTemplateError, match="有效 JSON"):
        ReagentTemplateStore(path).load()

    path.write_text(json.dumps({"schema_version": "wrong", "templates": []}), encoding="utf-8")
    with pytest.raises(ReagentTemplateError, match="schema"):
        ReagentTemplateStore(path).load()


def test_preparation_scales_volume_fixed_amount_strength_and_overage() -> None:
    template = ReagentTemplate.create(
        name="倍数模板",
        default_volume=100,
        default_strength="1X",
        components=(
            _component("随体积液体", 10, "mL", contributes_to_final_volume=True),
            _component("固定粉末", 5, "mg", component_type="powder", scale_with_volume=False),
            _component("按倍数组分", 4, "mL", scale_with_strength=True, contributes_to_final_volume=True),
            _component("水", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )

    result = calculate_preparation(PreparationRequest(template.template_id, 75, "mL", "0.5X", 10), (template,))

    assert result.target_volume == 75
    assert result.suggested_volume == pytest.approx(82.5)
    amounts = {component.name: component.amount for component in result.direct_components}
    assert amounts["随体积液体"] == pytest.approx(8.25)
    assert amounts["固定粉末"] == pytest.approx(5)
    assert amounts["按倍数组分"] == pytest.approx(1.65)
    assert amounts["水"] == pytest.approx(72.6)
    assert "目标最终体积：75 mL" in result.as_text()
    assert "建议配制体积：82.5 mL" in result.as_text()


def test_auto_fill_rejects_overfilled_volume_and_multiple_fillers(tmp_path) -> None:
    overfilled = ReagentTemplate.create(
        name="超量模板",
        default_volume=100,
        components=(
            _component("液体", 120, "mL", contributes_to_final_volume=True),
            _component("水", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )
    with pytest.raises(ReagentTemplateError, match="超过建议配制体积"):
        calculate_preparation(PreparationRequest(overfilled.template_id, 100), (overfilled,))

    invalid = ReagentTemplate.create(
        name="双补足",
        default_volume=100,
        components=(
            _component("水", 0, "mL", component_type="solvent", auto_fill=True),
            _component("PBS", 0, "mL", component_type="solvent", auto_fill=True),
        ),
    )
    with pytest.raises(ReagentTemplateError, match="最多只能有一个"):
        ReagentTemplateStore(tmp_path / "templates.json").save_all((invalid,))


def test_l3_template_units_are_explicitly_limited_to_first_version_scope() -> None:
    unsupported = ReagentTemplate.create(
        name="暂不支持单位",
        default_volume=100,
        components=(_component("低浓度组分", 1, "nM"),),
    )

    with pytest.raises(ReagentTemplateError, match="暂不支持单位"):
        calculate_preparation(PreparationRequest(unsupported.template_id, 10), (unsupported,))


def test_subtemplate_expands_with_child_target_volume() -> None:
    child = _template_c()
    parent = _template_a(child_id=child.template_id)

    result = calculate_preparation(PreparationRequest(parent.template_id, 100, expand_subtemplates=True), (parent, child))

    child_node = result.tree.children[0]
    assert child_node.template_name == "试剂 C"
    assert child_node.suggested_volume == pytest.approx(8)
    child_amounts = {component.name: component.amount for component in child_node.components}
    assert child_amounts["C1"] == pytest.approx(1.6)
    assert child_amounts["C water"] == pytest.approx(6.4)
    assert "完整展开清单" in result.as_text()
    assert "试剂 C" in result.as_text()


def test_cycle_reference_is_blocked() -> None:
    a = ReagentTemplate.create(name="A", default_volume=100)
    c = ReagentTemplate.create(name="C", default_volume=100)
    a = ReagentTemplate(
        **{**a.to_dict(), "components": (_component("C", 1, "mL", component_type="self_prepared_template", referenced_template_id=c.template_id),)}
    )
    c = ReagentTemplate(
        **{**c.to_dict(), "components": (_component("A", 1, "mL", component_type="self_prepared_template", referenced_template_id=a.template_id),)}
    )

    with pytest.raises(ReagentTemplateError, match="循环引用"):
        calculate_preparation(PreparationRequest(a.template_id, 10), (a, c))


def test_preparation_steps_are_generic_and_include_review_notice() -> None:
    template = _template_a()
    result = calculate_preparation(PreparationRequest(template.template_id, 75), (template,))
    text = result.as_text()

    assert "准备合适容器" in text
    assert "按一级配制清单顺序加入各组分" in text
    assert "记录目标 pH、实测 pH" in text
    assert "补足至建议配制体积" in text
    assert "人工复核提示" in text
    for forbidden in ("自动 pH 预测", "自动推荐最佳配方", "无需人工复核"):
        assert forbidden not in text
