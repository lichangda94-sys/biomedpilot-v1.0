from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


LABTOOLS_SIBLING_ROOT = Path(__file__).resolve().parents[2] / "LabTools"
REVIEW_NOTICE = "实验计算结果需由用户复核后使用。"


@dataclass(frozen=True)
class LabToolsRuntimeStatus:
    available: bool
    message: str


@dataclass(frozen=True)
class LabToolsUiResult:
    title: str
    primary_result: str
    detail_text: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    copy_text: str

    @property
    def valid(self) -> bool:
        return not self.errors


def runtime_status() -> LabToolsRuntimeStatus:
    try:
        _ensure_labtools_importable()
        import labtools  # noqa: F401

        return LabToolsRuntimeStatus(True, "LabTools backend specs available")
    except Exception as exc:  # pragma: no cover - defensive optional dependency fallback.
        return LabToolsRuntimeStatus(False, f"LabTools backend unavailable: {exc}")


def list_quick_tasks() -> tuple[Any, ...]:
    _ensure_labtools_importable()
    from labtools.calculators import list_quick_calculator_tasks

    return tuple(list_quick_calculator_tasks())


def get_quick_task(task_id: str) -> Any:
    _ensure_labtools_importable()
    from labtools.calculators import get_quick_calculator_task

    return get_quick_calculator_task(task_id)


def list_formula_specs() -> tuple[Any, ...]:
    _ensure_labtools_importable()
    from labtools.calculators import list_formula_specs

    return tuple(list_formula_specs())


def get_formula_spec(spec_id: str) -> Any:
    _ensure_labtools_importable()
    from labtools.calculators import get_formula_spec

    return get_formula_spec(spec_id)


def supported_units_for_formula_field(field: Any) -> tuple[str, ...]:
    _ensure_labtools_importable()
    from labtools.calculators import supported_units_for_formula_field

    return tuple(supported_units_for_formula_field(field))


def quick_field_label(field_id: str) -> str:
    return _QUICK_FIELD_LABELS.get(field_id, field_id.replace("_", " "))


def quick_field_default(field_id: str) -> str:
    return _QUICK_FIELD_DEFAULTS.get(field_id, "")


def quick_field_units(field_id: str) -> tuple[str, ...]:
    return _QUICK_FIELD_UNITS.get(field_id, ())


def execute_quick_task(task_id: str, values: dict[str, str], units: dict[str, str]) -> LabToolsUiResult:
    _ensure_labtools_importable()
    from labtools.calculators import (
        CellSeedingInput,
        DilutionInput,
        MassMolarityInput,
        QpcrMixInput,
        WesternBlotLoadingInput,
        calculate_cell_seeding_v1,
        calculate_dilution_v1,
        calculate_mass_molarity_v1,
        calculate_qpcr_mix_v1,
        calculate_western_blot_loading_v1,
        format_cell_seeding_copy_text,
        format_dilution_copy_text,
        format_mass_molarity_copy_text,
        solve_solution_preparation_formula,
    )

    task = get_quick_task(task_id)
    try:
        if task.calculator_name == "calculate_dilution_v1":
            input_data = DilutionInput(
                stock_concentration=_value(values, "stock_concentration"),
                stock_unit=_unit(units, "stock_concentration", "mM"),
                target_concentration=_value(values, "target_concentration"),
                target_unit=_unit(units, "target_concentration", "mM"),
                final_volume=_value(values, "final_volume"),
                final_volume_unit=_unit(units, "final_volume", "mL"),
            )
            result = calculate_dilution_v1(input_data)
            copy_text = format_dilution_copy_text(input_data, result) or result.as_text()
            return _result_from_dataclass(task.title, result, copy_text=copy_text)

        if task.calculator_name == "calculate_mass_molarity_v1":
            input_data = MassMolarityInput(
                molecular_weight=_value(values, "molecular_weight"),
                target_concentration=_value(values, "target_concentration"),
                concentration_unit=_unit(units, "target_concentration", "mM"),
                final_volume=_value(values, "final_volume"),
                volume_unit=_unit(units, "final_volume", "mL"),
                output_mass_unit=_unit(units, "output_mass_unit", "mg"),
            )
            result = calculate_mass_molarity_v1(input_data)
            copy_text = format_mass_molarity_copy_text(input_data, result) or result.as_text()
            return _result_from_dataclass(task.title, result, copy_text=copy_text)

        if task.calculator_name == "calculate_qpcr_mix_v1":
            input_data = QpcrMixInput(
                reactions=_value(values, "reactions"),
                reaction_volume_ul=_value(values, "reaction_volume_ul"),
                master_mix_value=_value(values, "master_mix_value"),
                forward_primer_ul=_value(values, "forward_primer_ul"),
                reverse_primer_ul=_value(values, "reverse_primer_ul"),
                template_ul=_value(values, "template_ul"),
            )
            result = calculate_qpcr_mix_v1(input_data)
            return _result_from_dataclass(task.title, result)

        if task.calculator_name == "calculate_cell_seeding_v1":
            input_data = CellSeedingInput(
                current_cell_concentration=_value(values, "current_cell_concentration"),
                concentration_unit=_unit(units, "current_cell_concentration", "cells/mL"),
                target_cells_per_well=_value(values, "target_cells_per_well"),
                well_count=_value(values, "well_count"),
                volume_per_well=_value(values, "volume_per_well"),
                volume_unit=_unit(units, "volume_per_well", "µL"),
            )
            result = calculate_cell_seeding_v1(input_data)
            copy_text = format_cell_seeding_copy_text(input_data, result) or result.as_text()
            return _result_from_dataclass(f"{task.title}（仅计算辅助）", result, copy_text=copy_text)

        if task.calculator_name == "calculate_western_blot_loading_v1":
            input_data = WesternBlotLoadingInput(
                protein_concentration=_value(values, "protein_concentration"),
                concentration_unit=_unit(units, "protein_concentration", "mg/mL"),
                target_protein_mass_ug=_value(values, "target_protein_mass_ug"),
                final_loading_volume=_value(values, "final_loading_volume"),
                volume_unit=_unit(units, "final_loading_volume", "µL"),
                loading_buffer_x=_value(values, "loading_buffer_x"),
            )
            result = calculate_western_blot_loading_v1(input_data)
            return _result_from_dataclass(task.title, result)

        if task.calculator_name == "solve_solution_preparation_formula":
            result = solve_solution_preparation_formula(
                mass=None,
                mass_unit=_unit(units, "mass", "mg"),
                concentration=_value(values, "concentration"),
                concentration_unit=_unit(units, "concentration", "mM"),
                volume=_value(values, "volume"),
                volume_unit=_unit(units, "volume", "mL"),
                molecular_weight=_value(values, "molecular_weight"),
                unknown_field="mass",
            )
            return _result_from_calculation_result(task.title, result)

        return LabToolsUiResult(
            title=task.title,
            primary_result="暂未接入",
            detail_text=f"该 quick task 的 calculator_name 尚未接入 UI adapter：{task.calculator_name}",
            warnings=(REVIEW_NOTICE,),
            errors=(),
            copy_text="",
        )
    except Exception as exc:
        return _error_result(task.title, exc)


def execute_formula(spec_id: str, solve_target: str, values: dict[str, str], units: dict[str, str]) -> LabToolsUiResult:
    _ensure_labtools_importable()
    from labtools.calculators import (
        calculate_serial_dilution,
        solve_concentration_bridge,
        solve_dilution_equation,
        solve_percent_solution,
        solve_solution_preparation_formula,
        solve_stock_working_solution,
    )

    spec = get_formula_spec(spec_id)
    solvers: dict[str, Callable[..., Any]] = {
        "solve_concentration_bridge": solve_concentration_bridge,
        "solve_dilution_equation": solve_dilution_equation,
        "solve_stock_working_solution": solve_stock_working_solution,
        "solve_solution_preparation_formula": solve_solution_preparation_formula,
        "solve_percent_solution": solve_percent_solution,
        "calculate_serial_dilution": calculate_serial_dilution,
    }
    try:
        solver = solvers[spec.solver_name]
        kwargs = _formula_solver_kwargs(spec.solver_name, solve_target, values, units)
        result = solver(**kwargs)
        return _result_from_calculation_result(spec.short_title, result)
    except Exception as exc:
        return _error_result(spec.short_title, exc)


def _ensure_labtools_importable() -> None:
    if LABTOOLS_SIBLING_ROOT.exists():
        root = str(LABTOOLS_SIBLING_ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)


def _formula_solver_kwargs(solver_name: str, solve_target: str, values: dict[str, str], units: dict[str, str]) -> dict[str, Any]:
    field_values = {field_id: (None if field_id == solve_target else _value(values, field_id)) for field_id in values}
    if solver_name == "solve_concentration_bridge":
        return {
            "mass_concentration": field_values.get("mass_concentration"),
            "mass_unit": _unit(units, "mass_concentration", "mg/mL"),
            "molar_concentration": field_values.get("molar_concentration"),
            "molar_unit": _unit(units, "molar_concentration", "mM"),
            "molecular_weight": field_values.get("molecular_weight"),
            "unknown_field": solve_target,
        }
    if solver_name == "solve_dilution_equation":
        return {
            "stock_concentration": field_values.get("stock_concentration"),
            "stock_unit": _unit(units, "stock_concentration", "mM"),
            "stock_volume": field_values.get("stock_volume"),
            "stock_volume_unit": _unit(units, "stock_volume", "µL"),
            "target_concentration": field_values.get("target_concentration"),
            "target_unit": _unit(units, "target_concentration", "mM"),
            "final_volume": field_values.get("final_volume"),
            "final_volume_unit": _unit(units, "final_volume", "mL"),
            "molecular_weight": field_values.get("molecular_weight"),
            "unknown_field": solve_target,
        }
    if solver_name == "solve_stock_working_solution":
        return {
            "stock_strength": field_values.get("stock_concentration"),
            "target_strength": field_values.get("target_concentration") or 1,
            "final_volume": field_values.get("final_volume"),
            "final_volume_unit": _unit(units, "final_volume", "mL"),
            "output_volume_unit": _unit(units, "final_volume", "µL"),
        }
    if solver_name == "solve_solution_preparation_formula":
        return {
            "mass": field_values.get("mass"),
            "mass_unit": _unit(units, "mass", "mg"),
            "concentration": field_values.get("concentration"),
            "concentration_unit": _unit(units, "concentration", "mM"),
            "volume": field_values.get("volume"),
            "volume_unit": _unit(units, "volume", "mL"),
            "molecular_weight": field_values.get("molecular_weight"),
            "unknown_field": solve_target,
        }
    if solver_name == "solve_percent_solution":
        return {
            "percent": field_values.get("percent"),
            "percent_type": field_values.get("percent_type") or "w/v",
            "solute_amount": field_values.get("solute_amount"),
            "solute_unit": _unit(units, "solute_amount", "g"),
            "total_amount": field_values.get("total_amount"),
            "total_unit": _unit(units, "total_amount", "mL"),
            "unknown_field": solve_target,
        }
    if solver_name == "calculate_serial_dilution":
        return {
            "initial_concentration": field_values.get("start_concentration"),
            "concentration_unit": _unit(units, "start_concentration", "mM"),
            "dilution_factor": field_values.get("dilution_factor"),
            "levels": field_values.get("levels"),
            "final_volume": field_values.get("final_volume_per_level"),
            "final_volume_unit": _unit(units, "final_volume_per_level", "µL"),
        }
    raise KeyError(f"Unsupported solver: {solver_name}")


def _result_from_dataclass(title: str, result: Any, *, copy_text: str | None = None) -> LabToolsUiResult:
    errors = tuple(getattr(result, "errors", ()) or ())
    warnings = tuple(dict.fromkeys((*tuple(getattr(result, "warnings", ()) or ()), REVIEW_NOTICE)))
    detail_text = result.as_text() if hasattr(result, "as_text") else str(result)
    return LabToolsUiResult(
        title=title,
        primary_result=getattr(result, "summary", "") or title,
        detail_text=detail_text,
        warnings=warnings,
        errors=errors,
        copy_text=copy_text if copy_text is not None else detail_text,
    )


def _result_from_calculation_result(title: str, result: Any) -> LabToolsUiResult:
    warnings = tuple(dict.fromkeys((*tuple(getattr(result, "warnings", ()) or ()), REVIEW_NOTICE)))
    detail_text = result.as_text() if hasattr(result, "as_text") else str(result)
    primary = "\n".join(getattr(result, "result_lines", ()) or ()) or title
    return LabToolsUiResult(
        title=title,
        primary_result=primary,
        detail_text=detail_text,
        warnings=warnings,
        errors=(),
        copy_text=detail_text,
    )


def _error_result(title: str, exc: Exception) -> LabToolsUiResult:
    return LabToolsUiResult(
        title=title,
        primary_result="输入需要调整",
        detail_text="",
        warnings=(REVIEW_NOTICE,),
        errors=(str(exc),),
        copy_text="",
    )


def _value(values: dict[str, str], field_id: str) -> str | None:
    value = values.get(field_id, "")
    return value if value != "" else None


def _unit(units: dict[str, str], field_id: str, default: str) -> str:
    return units.get(field_id) or default


_QUICK_FIELD_LABELS: dict[str, str] = {
    "stock_concentration": "Stock 浓度",
    "target_concentration": "目标浓度",
    "final_volume": "终体积",
    "molecular_weight": "分子量 MW",
    "output_mass_unit": "输出质量单位",
    "mass": "称量质量（输出）",
    "concentration": "目标浓度",
    "volume": "终体积",
    "reactions": "反应数",
    "reaction_volume_ul": "单反应体积",
    "master_mix_value": "Master mix 体积",
    "forward_primer_ul": "Forward primer",
    "reverse_primer_ul": "Reverse primer",
    "template_ul": "Template / cDNA",
    "current_cell_concentration": "当前细胞浓度",
    "target_cells_per_well": "目标每孔细胞数",
    "well_count": "孔数",
    "volume_per_well": "每孔体积",
    "protein_concentration": "蛋白浓度",
    "target_protein_mass_ug": "目标蛋白量",
    "final_loading_volume": "终上样体积",
    "loading_buffer_x": "Loading buffer 倍数",
}

_QUICK_FIELD_DEFAULTS: dict[str, str] = {
    "stock_concentration": "100",
    "target_concentration": "10",
    "final_volume": "1",
    "molecular_weight": "180.16",
    "output_mass_unit": "",
    "mass": "",
    "concentration": "100",
    "volume": "10",
    "reactions": "24",
    "reaction_volume_ul": "20",
    "master_mix_value": "10",
    "forward_primer_ul": "0.8",
    "reverse_primer_ul": "0.8",
    "template_ul": "2",
    "current_cell_concentration": "1000000",
    "target_cells_per_well": "5000",
    "well_count": "24",
    "volume_per_well": "100",
    "protein_concentration": "2",
    "target_protein_mass_ug": "20",
    "final_loading_volume": "20",
    "loading_buffer_x": "4",
}

_QUICK_FIELD_UNITS: dict[str, tuple[str, ...]] = {
    "stock_concentration": ("mM", "µM", "M", "mg/mL", "µg/µL"),
    "target_concentration": ("mM", "µM", "M", "mg/mL", "µg/µL"),
    "final_volume": ("mL", "µL", "L", "nL"),
    "molecular_weight": ("g/mol",),
    "output_mass_unit": ("mg", "µg", "g", "ng"),
    "mass": ("mg", "µg", "g", "ng"),
    "concentration": ("mM", "µM", "M", "mg/mL"),
    "volume": ("mL", "µL", "L"),
    "reaction_volume_ul": ("µL",),
    "master_mix_value": ("µL",),
    "forward_primer_ul": ("µL",),
    "reverse_primer_ul": ("µL",),
    "template_ul": ("µL",),
    "current_cell_concentration": ("cells/mL", "cells/µL"),
    "volume_per_well": ("µL", "mL"),
    "protein_concentration": ("mg/mL", "µg/µL"),
    "final_loading_volume": ("µL", "mL"),
}
