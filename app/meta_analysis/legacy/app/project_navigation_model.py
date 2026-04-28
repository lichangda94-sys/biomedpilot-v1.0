from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ProjectType = Literal["bioinformatics", "meta_analysis"]


@dataclass(frozen=True)
class NavigationItem:
    key: str
    title: str
    description: str
    future_component: str
    primary_action: str
    status_label: str = "Planned"


BIOINFORMATICS_NAVIGATION_ITEMS: tuple[NavigationItem, ...] = (
    NavigationItem("home", "首页", "查看项目概况、近期结果和当前分析准备状态。", "BioinformaticsHomeViewModel", "查看首页", "就绪"),
    NavigationItem("data-search", "数据检索", "从 GEO、TCGA、GTEx 或本地索引检索可用数据。", "BioinformaticsDataSearchViewModel", "开始检索", "Requires setup"),
    NavigationItem("data-assets", "数据资产", "管理已导入的数据集、表达矩阵、样本表和注释文件。", "BioinformaticsDataAssetViewModel", "识别数据资产", "Needs data"),
    NavigationItem("sample-groups", "样本分组", "设置病例、对照、肿瘤、正常组织等比较组。", "BioinformaticsSampleGroupViewModel", "自动识别分组", "Needs data"),
    NavigationItem("deg", "差异分析", "准备差异表达分析参数并预览结果结构。", "BioinformaticsDegViewModel", "开始差异分析", "Needs data"),
    NavigationItem("enrichment", "富集分析", "基于差异基因进行 GO、KEGG 和通路富集分析。", "BioinformaticsEnrichmentViewModel", "运行富集分析", "Coming soon"),
    NavigationItem("correlation", "相关性分析", "探索基因表达、临床表型和免疫特征之间的相关性。", "BioinformaticsCorrelationViewModel", "运行相关性分析", "Coming soon"),
    NavigationItem("survival", "生存分析", "基于表达分组和临床随访数据进行生存曲线分析。", "BioinformaticsSurvivalViewModel", "运行生存分析", "Requires setup"),
    NavigationItem("visualization", "可视化", "生成火山图、热图、箱线图和通路图等科研图表。", "BioinformaticsVisualizationViewModel", "重新生成图表", "Needs data"),
    NavigationItem("reporting", "报告导出", "汇总数据来源、方法参数、图表和结果解释。", "BioinformaticsReportingViewModel", "生成报告", "Coming soon"),
    NavigationItem("tasks", "任务中心", "查看分析任务的排队、运行、完成和需要处理状态。", "BioinformaticsTaskCenterViewModel", "查看任务详情", "就绪"),
)

META_ANALYSIS_NAVIGATION_ITEMS: tuple[NavigationItem, ...] = (
    NavigationItem("home", "项目总览", "Meta 分析项目 Dashboard 和当前研究状态。", "MetaAnalysisDashboardViewModel", "查看总览", "Demo"),
    NavigationItem("pico-search", "PICO / 检索", "研究问题、检索策略和数据库检索入口。", "MetaAnalysisPicoSearchViewModel", "编辑 PICO / 检索", "Planned"),
    NavigationItem("import", "文献导入", "RIS / NBIB / CSV 文献导入入口。", "MetaAnalysisImportViewModel", "导入文献", "Planned"),
    NavigationItem("screening", "文献筛选", "标题摘要、全文筛选和排除理由管理。", "MetaAnalysisScreeningViewModel", "开始筛选", "Planned"),
    NavigationItem("extraction", "数据提取", "结构化研究数据提取和行模板编辑。", "MetaAnalysisExtractionViewModel", "提取数据", "Planned"),
    NavigationItem("profile-readiness", "Profile Readiness", "Read-only profile readiness and row CSV testing area.", "MetaAnalysisProfileReadinessViewModel", "Review readiness", "Ready / Read-only"),
    NavigationItem("analysis", "统计分析", "Meta 统计合成和异质性分析入口。", "MetaAnalysisStatisticsViewModel", "运行分析", "Limited / Not implemented"),
    NavigationItem("reporting", "报告导出", "Forest Plot、GRADE 和报告导出入口。", "MetaAnalysisReportingViewModel", "导出报告", "Readiness only"),
    NavigationItem("tasks", "任务中心", "任务状态、输出文件和运行历史。", "MetaAnalysisTaskCenterViewModel", "查看任务", "Demo"),
)


class ProjectNavigationModel:
    def __init__(self, project_type: ProjectType) -> None:
        if project_type not in ("bioinformatics", "meta_analysis"):
            raise ValueError(f"Unsupported project type: {project_type}")
        self.project_type = project_type
        self._items = (
            BIOINFORMATICS_NAVIGATION_ITEMS
            if project_type == "bioinformatics"
            else META_ANALYSIS_NAVIGATION_ITEMS
        )
        self._current_key = self._items[0].key

    @property
    def items(self) -> tuple[NavigationItem, ...]:
        return self._items

    @property
    def current_item(self) -> NavigationItem:
        return self.item_for_key(self._current_key)

    def titles(self) -> list[str]:
        return [item.title for item in self._items]

    def select(self, key: str) -> NavigationItem:
        item = self.item_for_key(key)
        self._current_key = item.key
        return item

    def item_for_key(self, key: str) -> NavigationItem:
        for item in self._items:
            if item.key == key:
                return item
        raise ValueError(f"Navigation item does not exist: {key}")
