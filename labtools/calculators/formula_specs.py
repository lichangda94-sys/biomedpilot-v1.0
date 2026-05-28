from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from labtools.calculators.calculator_models import CalculationError
from labtools.calculators.unit_conversion import (
    supported_amount_units,
    supported_concentration_units,
    supported_mass_units,
    supported_molecular_weight_units,
    supported_quick_calculator_units,
    supported_volume_units,
)


FORMULA_RESULT_SECTIONS = (
    "input_summary",
    "equation",
    "substitution",
    "primary_result",
    "warnings",
    "review_notice",
)

QUICK_TASK_RESULT_SECTIONS = (
    "input_summary",
    "primary_result",
    "secondary_results",
    "warnings",
    "copy_or_save",
    "review_notice",
)


@dataclass(frozen=True)
class FormulaFieldSpec:
    field_id: str
    label: str
    field_type: str
    default_unit: str = ""
    unit_group: str = ""
    placeholder: str = ""
    helper_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FormulaSolveTargetSpec:
    target_id: str
    label: str
    result_label: str
    helper_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FormulaExampleSpec:
    title: str
    solve_for: str
    inputs: dict[str, Any]
    expected_result_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FormulaSpec:
    spec_id: str
    title: str
    short_title: str
    group: str
    equation: str
    solver_name: str
    description: str
    fields: tuple[FormulaFieldSpec, ...]
    solve_targets: tuple[FormulaSolveTargetSpec, ...]
    default_solve_target: str
    result_sections: tuple[str, ...] = FORMULA_RESULT_SECTIONS
    display_mode: str = "advanced_formula"
    examples: tuple[FormulaExampleSpec, ...] = ()
    review_notice: str = "结果用于实验辅助计算，使用前需结合 SOP 和人工复核。"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fields"] = [field.to_dict() for field in self.fields]
        payload["solve_targets"] = [target.to_dict() for target in self.solve_targets]
        payload["examples"] = [example.to_dict() for example in self.examples]
        return payload


@dataclass(frozen=True)
class QuickCalculatorTaskSpec:
    task_id: str
    title: str
    category: str
    calculator_name: str
    description: str
    primary_result_label: str
    input_field_ids: tuple[str, ...]
    result_sections: tuple[str, ...] = QUICK_TASK_RESULT_SECTIONS
    promoted: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FORMULA_SPECS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        spec_id="concentration_bridge",
        title="浓度桥接：质量浓度 / 摩尔浓度 / 分子量",
        short_title="浓度桥接",
        group="concentration",
        equation="质量浓度 = 摩尔浓度 x 分子量",
        solver_name="solve_concentration_bridge",
        description="用于在质量浓度、摩尔浓度和分子量之间做单未知项反推。",
        fields=(
            FormulaFieldSpec("mass_concentration", "质量浓度", "concentration", "mg/mL", "mass_concentration", "例如 1"),
            FormulaFieldSpec("molar_concentration", "摩尔浓度", "concentration", "mM", "molarity", "例如 10"),
            FormulaFieldSpec("molecular_weight", "分子量", "molecular_weight", "g/mol", "molecular_weight", "例如 180.16"),
        ),
        solve_targets=(
            FormulaSolveTargetSpec("mass_concentration", "求质量浓度", "质量浓度"),
            FormulaSolveTargetSpec("molar_concentration", "求摩尔浓度", "摩尔浓度"),
            FormulaSolveTargetSpec("molecular_weight", "求分子量", "分子量"),
        ),
        default_solve_target="molar_concentration",
        examples=(
            FormulaExampleSpec(
                title="由质量浓度和 MW 求摩尔浓度",
                solve_for="molar_concentration",
                inputs={"mass_concentration": 1, "mass_unit": "mg/mL", "molecular_weight": 180.16, "molar_unit": "mM"},
                expected_result_hint="约 5.55 mM",
            ),
        ),
    ),
    FormulaSpec(
        spec_id="dilution_c1v1",
        title="稀释方程：C1 x V1 = C2 x V2",
        short_title="稀释方程",
        group="dilution",
        equation="C1 x V1 = C2 x V2",
        solver_name="solve_dilution_equation",
        description="用于从原液浓度、原液体积、目标浓度和终体积中反推一个未知项。",
        fields=(
            FormulaFieldSpec("stock_concentration", "原液浓度 C1", "concentration", "mM", "concentration", "例如 100"),
            FormulaFieldSpec("stock_volume", "原液体积 V1", "volume", "µL", "volume", "例如 100"),
            FormulaFieldSpec("target_concentration", "目标浓度 C2", "concentration", "mM", "concentration", "例如 10"),
            FormulaFieldSpec("final_volume", "终体积 V2", "volume", "mL", "volume", "例如 1"),
            FormulaFieldSpec("molecular_weight", "分子量 MW", "molecular_weight", "g/mol", "molecular_weight", "不同浓度维度换算时填写"),
        ),
        solve_targets=(
            FormulaSolveTargetSpec("stock_concentration", "求原液浓度 C1", "原液浓度"),
            FormulaSolveTargetSpec("stock_volume", "求原液体积 V1", "原液体积"),
            FormulaSolveTargetSpec("target_concentration", "求目标浓度 C2", "目标浓度"),
            FormulaSolveTargetSpec("final_volume", "求终体积 V2", "终体积"),
        ),
        default_solve_target="stock_volume",
        examples=(
            FormulaExampleSpec(
                title="100 mM stock 配 10 mM、1 mL working solution",
                solve_for="stock_volume",
                inputs={
                    "stock_concentration": 100,
                    "stock_unit": "mM",
                    "target_concentration": 10,
                    "target_unit": "mM",
                    "final_volume": 1,
                    "final_volume_unit": "mL",
                },
                expected_result_hint="原液 100 µL，补足溶剂 900 µL",
            ),
        ),
    ),
    FormulaSpec(
        spec_id="stock_working_solution",
        title="Stock 配 Working Solution",
        short_title="Stock 到 Working",
        group="dilution",
        equation="stock volume = target concentration x final volume / stock concentration",
        solver_name="solve_stock_working_solution",
        description="用于最常见的从高浓度 stock 配制低浓度 working solution。",
        fields=(
            FormulaFieldSpec("stock_concentration", "Stock 浓度", "concentration", "mM", "concentration", "例如 100"),
            FormulaFieldSpec("target_concentration", "目标浓度", "concentration", "mM", "concentration", "例如 10"),
            FormulaFieldSpec("final_volume", "终体积", "volume", "mL", "volume", "例如 1"),
        ),
        solve_targets=(FormulaSolveTargetSpec("stock_volume", "求 stock 体积", "stock 体积"),),
        default_solve_target="stock_volume",
    ),
    FormulaSpec(
        spec_id="solution_preparation",
        title="溶液配制：质量 / 浓度 / 体积 / MW",
        short_title="溶液配制",
        group="solution_preparation",
        equation="mass = concentration x volume x molecular weight",
        solver_name="solve_solution_preparation_formula",
        description="用于称量配制、反推浓度、反推体积，或在摩尔模式下反推 MW。",
        fields=(
            FormulaFieldSpec("mass", "称量质量", "mass", "mg", "mass", "例如 58.44"),
            FormulaFieldSpec("concentration", "目标浓度", "concentration", "mM", "concentration", "例如 100"),
            FormulaFieldSpec("volume", "终体积", "volume", "mL", "volume", "例如 10"),
            FormulaFieldSpec("molecular_weight", "分子量 MW", "molecular_weight", "g/mol", "molecular_weight", "摩尔模式填写"),
        ),
        solve_targets=(
            FormulaSolveTargetSpec("mass", "求称量质量", "称量质量"),
            FormulaSolveTargetSpec("concentration", "求目标浓度", "目标浓度"),
            FormulaSolveTargetSpec("volume", "求终体积", "终体积"),
            FormulaSolveTargetSpec("molecular_weight", "求分子量", "分子量"),
        ),
        default_solve_target="mass",
    ),
    FormulaSpec(
        spec_id="percent_solution",
        title="百分比溶液：w/v、v/v、w/w",
        short_title="百分比溶液",
        group="solution_preparation",
        equation="percent = solute amount / total amount x 100%",
        solver_name="solve_percent_solution",
        description="用于按 w/v、v/v 或 w/w 语义计算百分比溶液。",
        fields=(
            FormulaFieldSpec("percent", "百分比", "concentration", "%", "relative_concentration", "例如 1"),
            FormulaFieldSpec("solute_amount", "溶质用量", "amount", "g", "mass_or_volume", "例如 1"),
            FormulaFieldSpec("total_amount", "终量", "amount", "mL", "mass_or_volume", "例如 100"),
            FormulaFieldSpec("percent_type", "百分比类型", "option", "", "", "w/v、v/v 或 w/w"),
        ),
        solve_targets=(
            FormulaSolveTargetSpec("percent", "求百分比", "百分比"),
            FormulaSolveTargetSpec("solute_amount", "求溶质用量", "溶质用量"),
            FormulaSolveTargetSpec("total_amount", "求终量", "终量"),
        ),
        default_solve_target="solute_amount",
    ),
    FormulaSpec(
        spec_id="serial_dilution",
        title="梯度稀释 / Serial Dilution",
        short_title="梯度稀释",
        group="dilution",
        equation="each level = previous concentration / dilution factor",
        solver_name="calculate_serial_dilution",
        description="用于生成多级梯度稀释的每一级浓度、转移体积和补足体积。",
        fields=(
            FormulaFieldSpec("start_concentration", "起始浓度", "concentration", "mM", "concentration", "例如 100"),
            FormulaFieldSpec("dilution_factor", "每级稀释倍数", "number", "", "", "例如 10"),
            FormulaFieldSpec("levels", "级数", "integer", "", "", "例如 6"),
            FormulaFieldSpec("final_volume_per_level", "每级终体积", "volume", "µL", "volume", "例如 100"),
        ),
        solve_targets=(FormulaSolveTargetSpec("dilution_series", "生成梯度表", "梯度稀释表"),),
        default_solve_target="dilution_series",
        result_sections=("input_summary", "series_table", "low_transfer_warnings", "review_notice"),
    ),
)


QUICK_CALCULATOR_TASKS: tuple[QuickCalculatorTaskSpec, ...] = (
    QuickCalculatorTaskSpec(
        task_id="quick_dilution",
        title="稀释配液",
        category="general",
        calculator_name="calculate_dilution_v1",
        description="已知 stock 浓度、目标浓度和终体积，快速计算 stock 与溶剂体积。",
        primary_result_label="stock 体积",
        input_field_ids=("stock_concentration", "target_concentration", "final_volume"),
    ),
    QuickCalculatorTaskSpec(
        task_id="quick_mass_molarity",
        title="摩尔浓度称量",
        category="general",
        calculator_name="calculate_mass_molarity_v1",
        description="已知 MW、目标摩尔浓度和终体积，快速计算称量质量。",
        primary_result_label="称量质量",
        input_field_ids=("molecular_weight", "target_concentration", "final_volume", "output_mass_unit"),
    ),
    QuickCalculatorTaskSpec(
        task_id="quick_solution_preparation",
        title="溶液配制",
        category="general",
        calculator_name="solve_solution_preparation_formula",
        description="按质量浓度或摩尔浓度计算配制结果，并保留公式和 warning。",
        primary_result_label="配制结果",
        input_field_ids=("mass", "concentration", "volume", "molecular_weight"),
    ),
    QuickCalculatorTaskSpec(
        task_id="quick_qpcr_mix",
        title="qPCR Mix",
        category="pcr_qpcr",
        calculator_name="calculate_qpcr_mix_v1",
        description="按反应数、单反应体积和组分体积快速计算 master mix。",
        primary_result_label="含 overage 总用量",
        input_field_ids=("reactions", "reaction_volume_ul", "master_mix_value", "forward_primer_ul", "reverse_primer_ul", "template_ul"),
    ),
    QuickCalculatorTaskSpec(
        task_id="quick_cell_seeding",
        title="细胞铺板",
        category="cell_culture",
        calculator_name="calculate_cell_seeding_v1",
        description="按当前细胞浓度、目标每孔细胞数和孔数快速计算悬液与培养基体积。",
        primary_result_label="细胞悬液体积",
        input_field_ids=("current_cell_concentration", "target_cells_per_well", "well_count", "volume_per_well"),
    ),
    QuickCalculatorTaskSpec(
        task_id="quick_wb_loading",
        title="WB 上样",
        category="western_blot",
        calculator_name="calculate_western_blot_loading_v1",
        description="按蛋白浓度、目标蛋白量、终体积和 loading buffer 倍数快速计算上样体系。",
        primary_result_label="样品体积",
        input_field_ids=("protein_concentration", "target_protein_mass_ug", "final_loading_volume", "loading_buffer_x"),
    ),
)


def list_formula_specs(*, group: str | None = None, display_mode: str | None = None) -> tuple[FormulaSpec, ...]:
    specs = FORMULA_SPECS
    if group is not None:
        specs = tuple(spec for spec in specs if spec.group == group)
    if display_mode is not None:
        specs = tuple(spec for spec in specs if spec.display_mode == display_mode)
    return specs


def get_formula_spec(spec_id: str) -> FormulaSpec:
    for spec in FORMULA_SPECS:
        if spec.spec_id == spec_id:
            return spec
    raise CalculationError(f"未知公式配置：{spec_id}。")


def list_quick_calculator_tasks(*, category: str | None = None, promoted_only: bool = False) -> tuple[QuickCalculatorTaskSpec, ...]:
    tasks = QUICK_CALCULATOR_TASKS
    if category is not None:
        tasks = tuple(task for task in tasks if task.category == category)
    if promoted_only:
        tasks = tuple(task for task in tasks if task.promoted)
    return tasks


def get_quick_calculator_task(task_id: str) -> QuickCalculatorTaskSpec:
    for task in QUICK_CALCULATOR_TASKS:
        if task.task_id == task_id:
            return task
    raise CalculationError(f"未知快速计算任务：{task_id}。")


def supported_units_for_formula_field(field: FormulaFieldSpec, *, use_molar_calculation: bool = True) -> tuple[str, ...]:
    if field.unit_group == "mass_concentration":
        return tuple(unit for unit in supported_concentration_units(include_molar=False) if unit not in {"%", "X", "fold"})
    if field.unit_group == "molarity":
        return tuple(unit for unit in supported_concentration_units(include_molar=True) if unit in {"M", "mM", "µM", "nM", "pM"})
    if field.unit_group == "concentration":
        return supported_quick_calculator_units("concentration", use_molar_calculation=use_molar_calculation)
    if field.unit_group == "relative_concentration":
        return ("%", "X", "fold")
    if field.unit_group == "volume":
        return supported_volume_units()
    if field.unit_group == "mass":
        return supported_mass_units()
    if field.unit_group == "amount":
        return supported_amount_units()
    if field.unit_group == "molecular_weight":
        return supported_molecular_weight_units()
    if field.unit_group == "mass_or_volume":
        return supported_mass_units() + supported_volume_units()
    if not field.unit_group:
        return ()
    raise CalculationError(f"未知公式字段单位组：{field.unit_group}。")
