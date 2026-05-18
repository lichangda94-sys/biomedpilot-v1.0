from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabToolsTool:
    tool_id: str
    chinese_name: str
    english_name: str
    category: str
    status: str
    entry_page: str
    is_available: bool
    requires_imagej_fiji: bool
    is_planned_only: bool
    description: str
    boundary_statement: str
    future_capabilities: tuple[str, ...] = ()
    unavailable_capabilities: tuple[str, ...] = ()
    button_text: str = "打开"
    object_name: str = "labToolsToolEntry"


LABTOOLS_TOOLS: tuple[LabToolsTool, ...] = (
    LabToolsTool(
        tool_id="general_reagent_calculator",
        chinese_name="通用试剂制备",
        english_name="General Reagent Preparation",
        category="本地计算",
        status="available / 已接入",
        entry_page="general_calculators",
        is_available=True,
        requires_imagej_fiji=False,
        is_planned_only=False,
        description="用于常用试剂快速计算、模板管理和本次制备清单生成。",
        boundary_statement="只做用户录入模板的本地换算和通用步骤整理，不提供内置配方库，不生成实验方案建议，不替代实验 SOP。",
        button_text="进入通用试剂制备",
        object_name="labToolsGeneralCalculatorEntry",
    ),
    LabToolsTool(
        tool_id="western_blot",
        chinese_name="Western Blot 工具",
        english_name="Western Blot Tools",
        category="蛋白实验",
        status="available / 可用",
        entry_page="western_blot",
        is_available=True,
        requires_imagej_fiji=False,
        is_planned_only=False,
        description="Western Blot 流程工作台可用，覆盖样品准备、BCA、上样计算、配胶与 Lane 布局及关键流程记录。",
        boundary_statement="结果与灰度分析仅保留占位；不启用 WB 图像分析、条带识别、灰度定量、自动 ROI 或结果解释。",
        future_capabilities=(
            "WB 流程记录模板持续细化",
            "条带定量 workflow 的人工复核式整理占位",
            "与外部引擎配置状态按需解耦使用",
        ),
        unavailable_capabilities=(
            "不启用 WB/gel 真实分析",
            "不做条带自动识别或自动 ROI",
            "不替代人工判断、试剂盒说明书或实验室 SOP",
        ),
        button_text="进入 Western Blot",
        object_name="labToolsWesternBlotEntry",
    ),
    LabToolsTool(
        tool_id="pcr_qpcr",
        chinese_name="PCR/qPCR 工具",
        english_name="PCR/qPCR Tools",
        category="核酸实验",
        status="planned / 未启用",
        entry_page="pcr_qpcr",
        is_available=False,
        requires_imagej_fiji=False,
        is_planned_only=True,
        description="PCR mix、qPCR 结果整理 workflow 占位。",
        boundary_statement="当前不生成 PCR/qPCR 实验方案、plate layout、Ct/Delta Ct/Delta Delta Ct 结论或统计解释。",
        future_capabilities=(
            "PCR mix 和 qPCR 配液入口",
            "plate layout 和 Ct 数据整理 workflow",
            "结果整理前的 Tool Logic Card",
        ),
        unavailable_capabilities=(
            "不自动解释 Ct 或 Delta Delta Ct 结果",
            "不生成实验方案建议",
            "不替代人工判断和实验室 SOP",
        ),
        button_text="进入 PCR/qPCR",
        object_name="labToolsPcrQpcrEntry",
    ),
    LabToolsTool(
        tool_id="elisa_absorbance",
        chinese_name="ELISA/吸光度工具",
        english_name="ELISA/Absorbance Tools",
        category="吸光度与标准曲线",
        status="planned / 未启用",
        entry_page="elisa_absorbance",
        is_available=False,
        requires_imagej_fiji=False,
        is_planned_only=True,
        description="标准曲线、OD 数据整理 workflow 占位。",
        boundary_statement="当前不拟合标准曲线、不反推样本浓度、不输出 ELISA 或吸光度实验结论。",
        future_capabilities=(
            "标准曲线和 OD 数据整理入口",
            "BCA、Bradford、NanoDrop、ELISA 的结果整理 workflow",
            "实验特异逻辑开发前的 Tool Logic Card",
        ),
        unavailable_capabilities=(
            "不启用标准曲线真实拟合",
            "不自动反推样本浓度",
            "不替代试剂盒说明书和人工复核",
        ),
        button_text="进入 ELISA/吸光度工具",
        object_name="labToolsElisaAbsorbanceEntry",
    ),
    LabToolsTool(
        tool_id="cell_experiments",
        chinese_name="细胞实验工具",
        english_name="Cell Experiment Tools",
        category="细胞实验",
        status="planned / 未启用",
        entry_page="cell_experiments",
        is_available=False,
        requires_imagej_fiji=False,
        is_planned_only=True,
        description="细胞接种、处理分组、实验记录 workflow 占位。",
        boundary_statement="当前不做自动细胞计数、活率识别、wound healing 生产级分析或 pathology workflow。",
        future_capabilities=(
            "细胞接种和处理分组入口",
            "实验记录 workflow 和人工复核式结果整理",
            "后续图像工具接入前的边界声明",
        ),
        unavailable_capabilities=(
            "不启用自动细胞计数",
            "不启用 pathology workflow",
            "不替代人工判断、显微镜判读或实验室 SOP",
        ),
        button_text="进入细胞实验工具",
        object_name="labToolsCellExperimentEntry",
    ),
)


def labtools_tool_registry() -> tuple[LabToolsTool, ...]:
    return LABTOOLS_TOOLS


def get_labtools_tool(tool_id: str) -> LabToolsTool:
    for tool in LABTOOLS_TOOLS:
        if tool.tool_id == tool_id:
            return tool
    raise KeyError(f"Unknown LabTools tool_id: {tool_id}")


def labtools_tool_by_entry_page(entry_page: str) -> LabToolsTool:
    for tool in LABTOOLS_TOOLS:
        if tool.entry_page == entry_page:
            return tool
    raise KeyError(f"Unknown LabTools entry_page: {entry_page}")
