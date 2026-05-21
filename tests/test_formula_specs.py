from __future__ import annotations

import json

import pytest

from labtools.calculators import (
    FORMULA_RESULT_SECTIONS,
    QUICK_TASK_RESULT_SECTIONS,
    get_formula_spec,
    get_quick_calculator_task,
    list_formula_specs,
    list_quick_calculator_tasks,
    supported_units_for_formula_field,
)
from labtools.calculators.calculator_models import CalculationError


def test_formula_specs_have_unique_ids_and_valid_default_targets() -> None:
    specs = list_formula_specs()
    ids = [spec.spec_id for spec in specs]

    assert len(ids) == len(set(ids))
    assert {"concentration_bridge", "dilution_c1v1", "solution_preparation", "serial_dilution"}.issubset(ids)
    for spec in specs:
        target_ids = {target.target_id for target in spec.solve_targets}
        assert spec.default_solve_target in target_ids
        assert spec.result_sections
        assert set(spec.result_sections).issubset(set(FORMULA_RESULT_SECTIONS) | {"series_table", "low_transfer_warnings"})


def test_dilution_formula_spec_exposes_explicit_solve_targets_for_ui() -> None:
    spec = get_formula_spec("dilution_c1v1")

    assert spec.equation == "C1 x V1 = C2 x V2"
    assert spec.solver_name == "solve_dilution_equation"
    assert [target.target_id for target in spec.solve_targets] == [
        "stock_concentration",
        "stock_volume",
        "target_concentration",
        "final_volume",
    ]
    assert spec.default_solve_target == "stock_volume"


def test_formula_field_unit_groups_resolve_to_ui_safe_units() -> None:
    spec = get_formula_spec("concentration_bridge")
    fields = {field.field_id: field for field in spec.fields}

    assert supported_units_for_formula_field(fields["mass_concentration"]) == (
        "g/L",
        "mg/L",
        "mg/mL",
        "µg/µL",
        "µg/mL",
        "ng/mL",
        "ng/µL",
    )
    assert supported_units_for_formula_field(fields["molar_concentration"]) == ("M", "mM", "µM", "nM", "pM")
    assert supported_units_for_formula_field(fields["molecular_weight"]) == ("g/mol",)


def test_quick_calculator_tasks_are_task_first_and_filterable() -> None:
    tasks = list_quick_calculator_tasks()
    ids = [task.task_id for task in tasks]

    assert len(ids) == len(set(ids))
    assert get_quick_calculator_task("quick_dilution").calculator_name == "calculate_dilution_v1"
    assert [task.task_id for task in list_quick_calculator_tasks(category="western_blot")] == ["quick_wb_loading"]
    assert all(set(task.result_sections).issubset(set(QUICK_TASK_RESULT_SECTIONS)) for task in tasks)


def test_specs_are_json_serializable_for_frontend_contract() -> None:
    payload = {
        "formulas": [spec.to_dict() for spec in list_formula_specs()],
        "quick_tasks": [task.to_dict() for task in list_quick_calculator_tasks()],
    }

    encoded = json.dumps(payload, ensure_ascii=False)

    assert "稀释方程" in encoded
    assert "qPCR Mix" in encoded


def test_unknown_formula_or_quick_task_reports_user_facing_error() -> None:
    with pytest.raises(CalculationError, match="未知公式配置"):
        get_formula_spec("missing")
    with pytest.raises(CalculationError, match="未知快速计算任务"):
        get_quick_calculator_task("missing")
