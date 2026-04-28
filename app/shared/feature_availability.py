from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FeatureAvailabilityStatus(StrEnum):
    OPEN = "open"
    TESTING = "testing"
    PLACEHOLDER = "placeholder"
    UNAVAILABLE = "unavailable"

    def display_label(self) -> str:
        return {
            FeatureAvailabilityStatus.OPEN: "已开放",
            FeatureAvailabilityStatus.TESTING: "测试中",
            FeatureAvailabilityStatus.PLACEHOLDER: "待接入",
            FeatureAvailabilityStatus.UNAVAILABLE: "暂未开放",
        }[self]


@dataclass(frozen=True)
class FeatureAvailability:
    module: str
    feature_id: str
    feature_name: str
    status: FeatureAvailabilityStatus
    description: str
    next_step: str
    legacy_source: str = ""

    def display_label(self) -> str:
        return f"{self.feature_name} · {self.status.display_label()}"


FEATURE_REGISTRY: tuple[FeatureAvailability, ...] = (
    FeatureAvailability("bioinformatics", "bio-study-question", "研究问题", FeatureAvailabilityStatus.PLACEHOLDER, "研究设计入口已预留。", "接入项目向导和研究目标记录。"),
    FeatureAvailability("bioinformatics", "bio-data-import", "数据检索 / 导入", FeatureAvailabilityStatus.TESTING, "支持生成 GEO 查询计划和 GSE accession 导入记录；当前不自动下载 NCBI 数据。", "接入受控在线检索、候选列表和下载步骤。", "app/bioinformatics/legacy/geo_tool"),
    FeatureAvailability("bioinformatics", "bio-download", "数据下载", FeatureAvailabilityStatus.TESTING, "读取 GEO 查询计划并生成下载计划；当前不实际下载 NCBI 数据。", "在用户确认后接入 legacy GEO 下载执行。", "app/bioinformatics/legacy/geo_pipeline"),
    FeatureAvailability("bioinformatics", "bio-asset-detection", "数据资产识别", FeatureAvailabilityStatus.TESTING, "读取 GEO 下载计划并扫描本地目标目录，不联网、不下载。", "接入真实下载产物后的表达矩阵、样本注释和平台注释识别。", "app/bioinformatics/legacy/geo_processing"),
    FeatureAvailability("bioinformatics", "bio-cleaning", "数据清洗", FeatureAvailabilityStatus.TESTING, "读取资产识别结果并生成清洗预检计划；当前不执行矩阵标准化。", "接入受控矩阵清洗、标准化结果预览和输出登记。", "app/bioinformatics/legacy/geo_processing"),
    FeatureAvailability("bioinformatics", "bio-sample-groups", "样本分组", FeatureAvailabilityStatus.PLACEHOLDER, "工作台占位，真实项目数据接入后开放。", "接入样本注释和分组编辑。"),
    FeatureAvailability("bioinformatics", "bio-deg", "差异表达分析", FeatureAvailabilityStatus.PLACEHOLDER, "当前测试版暂未开放正式统计执行。", "完成参数检查和 runner adapter。"),
    FeatureAvailability("bioinformatics", "bio-enrichment", "富集分析", FeatureAvailabilityStatus.UNAVAILABLE, "暂未开放。", "等待差异分析结果接入。"),
    FeatureAvailability("bioinformatics", "bio-correlation", "相关性分析", FeatureAvailabilityStatus.UNAVAILABLE, "暂未开放。", "定义输入数据契约。"),
    FeatureAvailability("bioinformatics", "bio-survival", "生存分析", FeatureAvailabilityStatus.UNAVAILABLE, "暂未开放。", "定义临床数据契约。"),
    FeatureAvailability("bioinformatics", "bio-reporting", "报告导出", FeatureAvailabilityStatus.PLACEHOLDER, "统一报告入口占位。", "接入 Report Center。"),
    FeatureAvailability("meta_analysis", "meta-pico", "研究问题 / PICO", FeatureAvailabilityStatus.TESTING, "legacy PICO/search 能力已保留。", "接入统一项目记录。", "app/meta_analysis/legacy/pico"),
    FeatureAvailability("meta_analysis", "meta-literature-import", "文献导入", FeatureAvailabilityStatus.TESTING, "支持 NBIB / RIS / CSV 文件导入，并登记任务与数据资产。", "继续接入 Prepare for Screening 和 Duplicate Review。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-dedup-prep", "去重准备", FeatureAvailabilityStatus.TESTING, "读取 Literature Import 输出并生成标准化筛选准备记录。", "继续接入 Duplicate Review。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-duplicate-review", "Duplicate Review", FeatureAvailabilityStatus.TESTING, "读取筛选准备记录并生成重复候选组摘要，当前不执行人工合并。", "接入人工确认 UI 和合并决策保存。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-screening", "Screening", FeatureAvailabilityStatus.TESTING, "读取 Prepare/Duplicate 输出并生成标题摘要筛选队列，支持最小 include/exclude/maybe 决策保存。", "扩展为逐条文献判读界面和排除理由字典。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-extraction", "Extraction", FeatureAvailabilityStatus.TESTING, "读取 Screening 队列并为 included 文献生成数据提取池，正式人工提取表单尚未开放。", "接入 PICO 字段、结局数据和来源页码的人工提取表单。", "app/meta_analysis/legacy/extraction"),
    FeatureAvailability("meta_analysis", "meta-analysis", "Analysis", FeatureAvailabilityStatus.TESTING, "读取 Extraction 输出并执行 Analysis 预检；当前不运行正式 Meta 统计。", "接入 outcome 提取表单、分析计划和统计 runner。", "app/meta_analysis/legacy/analysis"),
    FeatureAvailability("meta_analysis", "meta-reporting", "Reporting", FeatureAvailabilityStatus.TESTING, "读取 Analysis 预检输出并导出测试版 Markdown 摘要；正式报告和图表包尚未开放。", "接入森林图、漏斗图、结果表和正式报告模板。", "app/meta_analysis/legacy/reporting"),
    FeatureAvailability("shared", "shared-project-center", "项目中心", FeatureAvailabilityStatus.OPEN, "支持 JSON 持久化项目记录和最近项目读取。", "增加项目搜索和归档。"),
    FeatureAvailability("shared", "shared-testing-mode", "测试模式", FeatureAvailabilityStatus.OPEN, "提供测试说明和反馈模板生成。", "增加反馈包导出。"),
)


def list_features(module: str | None = None) -> list[FeatureAvailability]:
    features = list(FEATURE_REGISTRY)
    if module is not None:
        features = [feature for feature in features if feature.module == module]
    return features


def get_feature(feature_id: str) -> FeatureAvailability | None:
    for feature in FEATURE_REGISTRY:
        if feature.feature_id == feature_id:
            return feature
    return None


def features_by_status(status: FeatureAvailabilityStatus) -> list[FeatureAvailability]:
    return [feature for feature in FEATURE_REGISTRY if feature.status is status]
