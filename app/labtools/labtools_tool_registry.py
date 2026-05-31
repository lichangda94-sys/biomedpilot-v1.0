from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabToolsPrimaryEntry:
    tool_id: str
    title: str
    english_title: str
    page_key: str
    semantic_key: str
    status: str
    status_key: str
    description: str
    details: tuple[str, ...]
    button_text: str
    source_commits: tuple[str, ...]
    object_name: str


@dataclass(frozen=True)
class LabToolsSecondaryEntry:
    tool_id: str
    title: str
    english_title: str
    page_key: str
    semantic_key: str
    status: str
    status_key: str
    description: str
    disabled_reason: str
    button_text: str
    source_commits: tuple[str, ...]
    object_name: str


LABTOOLS_PRIMARY_ENTRIES: tuple[LabToolsPrimaryEntry, ...] = (
    LabToolsPrimaryEntry(
        tool_id="general_calculators",
        title="通用计算器",
        english_title="General Calculator",
        page_key="general_calculators",
        semantic_key="labtools.page.general_calculators",
        status="Shell only",
        status_key="shell_only",
        description="常用科学计算与单位换算，满足日常实验计算需求。",
        details=("稀释计算", "加样计算", "分子量 / 摩尔量换算", "单位换算", "更多通用计算入口"),
        button_text="打开计算器",
        source_commits=("3bf79f4", "ca006ee", "4999405"),
        object_name="labToolsGeneralCalculatorEntry",
    ),
    LabToolsPrimaryEntry(
        tool_id="reagent_preparation",
        title="试剂制备",
        english_title="Reagent Preparation",
        page_key="reagent_preparation",
        semantic_key="labtools.page.reagent_preparation",
        status="后续开放",
        status_key="planned",
        description="试剂配制与浓度换算，快速规划实验所需试剂。",
        details=("溶液配制", "稀释系列", "缓冲液配方", "配制复核提示", "更多配制工具"),
        button_text="进入试剂制备",
        source_commits=("3bf79f4", "f18b9a0", "4999405"),
        object_name="labToolsReagentPreparationEntry",
    ),
    LabToolsPrimaryEntry(
        tool_id="experiment_modules",
        title="实验模块",
        english_title="Experiment Modules",
        page_key="experiment_modules",
        semantic_key="labtools.page.experiment_modules",
        status="测试中",
        status_key="testing",
        description="面向不同实验类型的专用入口，提供已接入工具与待接入模块的分组导航。",
        details=("细胞实验", "蛋白实验", "核酸实验", "免疫与吸光度实验", "免疫组化"),
        button_text="选择实验模块",
        source_commits=("3bf79f4", "00f4ec6", "4999405"),
        object_name="labToolsExperimentModulesEntry",
    ),
)


LABTOOLS_SECONDARY_ENTRIES: tuple[LabToolsSecondaryEntry, ...] = (
    LabToolsSecondaryEntry(
        tool_id="cell_experiments",
        title="细胞实验",
        english_title="Cell Experiments",
        page_key="cell_experiments",
        semantic_key="labtools.page.cell_experiments",
        status="C2 待接入",
        status_key="shell_only",
        description="细胞档案、传代复苏冻存、接种给药转染和记录模板入口。",
        disabled_reason="UI-LABTOOLS-C2 will connect cell information, culture records, operation templates, and sample storage.",
        button_text="进入细胞实验",
        source_commits=("00f4ec6", "4cd06fb", "4999405"),
        object_name="labToolsCellExperimentsSecondaryEntry",
    ),
    LabToolsSecondaryEntry(
        tool_id="protein_experiments",
        title="蛋白实验",
        english_title="Protein Experiments",
        page_key="protein_experiments",
        semantic_key="labtools.page.protein_experiments",
        status="adapter needed",
        status_key="shell_only",
        description="WB 上样、SDS-PAGE、BCA/OD 和蛋白实验记录的分组入口。",
        disabled_reason="UI-LABTOOLS-C2 will connect WB loading, SDS-PAGE, BCA/OD, records, and report gates.",
        button_text="进入蛋白实验",
        source_commits=("a33cffe", "00f4ec6", "4999405"),
        object_name="labToolsProteinExperimentsSecondaryEntry",
    ),
    LabToolsSecondaryEntry(
        tool_id="nucleic_acid_experiments",
        title="核酸实验",
        english_title="Nucleic Acid Experiments",
        page_key="nucleic_acid_experiments",
        semantic_key="labtools.page.nucleic_acid_experiments",
        status="testing MVP",
        status_key="testing",
        description="PCR/qPCR、反应体系、程序、引物和 plate layout 的规划入口。",
        disabled_reason="PCR/qPCR adapters, primer registry, and result processing gates are not connected in C1.",
        button_text="进入核酸实验",
        source_commits=("00f4ec6", "4999405"),
        object_name="labToolsNucleicAcidExperimentsSecondaryEntry",
    ),
    LabToolsSecondaryEntry(
        tool_id="immuno_absorbance",
        title="免疫与吸光度实验",
        english_title="Immunoassay & Absorbance",
        page_key="immuno_absorbance",
        semantic_key="labtools.page.immuno_absorbance",
        status="backend missing",
        status_key="blocked",
        description="ELISA、吸光度读数、标准曲线边界和板式记录入口。",
        disabled_reason="ELISA/BCA formal records, curve fitting, and report export are not connected in C1.",
        button_text="进入免疫吸光度",
        source_commits=("00f4ec6", "4999405"),
        object_name="labToolsImmunoAbsorbanceSecondaryEntry",
    ),
    LabToolsSecondaryEntry(
        tool_id="ihc",
        title="免疫组化",
        english_title="Immunohistochemistry",
        page_key="ihc",
        semantic_key="labtools.page.ihc",
        status="blocked",
        status_key="blocked",
        description="IHC 样本、染色步骤、读片记录和图像辅助提示的边界入口。",
        disabled_reason="IHC record model, review workflow, and Settings-linked image assistance are not connected in C1.",
        button_text="进入免疫组化",
        source_commits=("00f4ec6", "4999405"),
        object_name="labToolsIhcSecondaryEntry",
    ),
)


def labtools_primary_entries() -> tuple[LabToolsPrimaryEntry, ...]:
    return LABTOOLS_PRIMARY_ENTRIES


def labtools_secondary_entries() -> tuple[LabToolsSecondaryEntry, ...]:
    return LABTOOLS_SECONDARY_ENTRIES


def get_labtools_primary_entry(tool_id: str) -> LabToolsPrimaryEntry:
    for entry in LABTOOLS_PRIMARY_ENTRIES:
        if entry.tool_id == tool_id:
            return entry
    raise KeyError(f"Unknown LabTools primary tool_id: {tool_id}")


def get_labtools_primary_by_page(page_key: str) -> LabToolsPrimaryEntry:
    for entry in LABTOOLS_PRIMARY_ENTRIES:
        if entry.page_key == page_key:
            return entry
    raise KeyError(f"Unknown LabTools primary page_key: {page_key}")


def get_labtools_secondary_entry(tool_id: str) -> LabToolsSecondaryEntry:
    for entry in LABTOOLS_SECONDARY_ENTRIES:
        if entry.tool_id == tool_id:
            return entry
    raise KeyError(f"Unknown LabTools secondary tool_id: {tool_id}")


def get_labtools_secondary_by_page(page_key: str) -> LabToolsSecondaryEntry:
    for entry in LABTOOLS_SECONDARY_ENTRIES:
        if entry.page_key == page_key:
            return entry
    raise KeyError(f"Unknown LabTools secondary page_key: {page_key}")
