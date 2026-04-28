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
    FeatureAvailability("bioinformatics", "bio-data-import", "数据检索 / 导入", FeatureAvailabilityStatus.TESTING, "GEO 检索/导入能力来自 legacy GEO 工具，当前先暴露状态入口。", "将 legacy GEO GUI 操作嵌入统一工作台。", "app/bioinformatics/legacy/geo_tool"),
    FeatureAvailability("bioinformatics", "bio-download", "数据下载", FeatureAvailabilityStatus.TESTING, "legacy GEO 下载流程已保留。", "增加受控下载按钮和结果目录登记。", "app/bioinformatics/legacy/geo_pipeline"),
    FeatureAvailability("bioinformatics", "bio-asset-detection", "数据资产识别", FeatureAvailabilityStatus.TESTING, "geo_processing 资产识别能力已保留。", "接入统一 Data Center。", "app/bioinformatics/legacy/geo_processing"),
    FeatureAvailability("bioinformatics", "bio-cleaning", "数据清洗", FeatureAvailabilityStatus.TESTING, "legacy GEO/本地数据处理能力已保留。", "增加输入检查和标准化结果预览。", "app/bioinformatics/legacy/geo_processing"),
    FeatureAvailability("bioinformatics", "bio-sample-groups", "样本分组", FeatureAvailabilityStatus.PLACEHOLDER, "工作台占位，真实项目数据接入后开放。", "接入样本注释和分组编辑。"),
    FeatureAvailability("bioinformatics", "bio-deg", "差异表达分析", FeatureAvailabilityStatus.PLACEHOLDER, "当前测试版暂未开放正式统计执行。", "完成参数检查和 runner adapter。"),
    FeatureAvailability("bioinformatics", "bio-enrichment", "富集分析", FeatureAvailabilityStatus.UNAVAILABLE, "暂未开放。", "等待差异分析结果接入。"),
    FeatureAvailability("bioinformatics", "bio-correlation", "相关性分析", FeatureAvailabilityStatus.UNAVAILABLE, "暂未开放。", "定义输入数据契约。"),
    FeatureAvailability("bioinformatics", "bio-survival", "生存分析", FeatureAvailabilityStatus.UNAVAILABLE, "暂未开放。", "定义临床数据契约。"),
    FeatureAvailability("bioinformatics", "bio-reporting", "报告导出", FeatureAvailabilityStatus.PLACEHOLDER, "统一报告入口占位。", "接入 Report Center。"),
    FeatureAvailability("meta_analysis", "meta-pico", "研究问题 / PICO", FeatureAvailabilityStatus.TESTING, "legacy PICO/search 能力已保留。", "接入统一项目记录。", "app/meta_analysis/legacy/pico"),
    FeatureAvailability("meta_analysis", "meta-literature-import", "文献导入", FeatureAvailabilityStatus.TESTING, "支持 NBIB / RIS / CSV 文件导入，并登记任务与数据资产。", "继续接入 Prepare for Screening 和 Duplicate Review。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-dedup-prep", "去重准备", FeatureAvailabilityStatus.TESTING, "去重准备能力来自 legacy literature 服务。", "接入导入后的文献集合。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-duplicate-review", "Duplicate Review", FeatureAvailabilityStatus.TESTING, "Duplicate Review 能力已保留。", "接入人工确认 UI。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-screening", "Screening", FeatureAvailabilityStatus.TESTING, "Screening service 已保留。", "接入标题摘要筛选队列。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-extraction", "Extraction", FeatureAvailabilityStatus.TESTING, "Extraction service 已保留。", "接入提取表单和保存。", "app/meta_analysis/legacy/extraction"),
    FeatureAvailability("meta_analysis", "meta-analysis", "Analysis", FeatureAvailabilityStatus.PLACEHOLDER, "当前测试版暂未开放完整 Meta 统计执行。", "接入分析计划和统计 runner。", "app/meta_analysis/legacy/analysis"),
    FeatureAvailability("meta_analysis", "meta-reporting", "Reporting", FeatureAvailabilityStatus.TESTING, "Reporting service 已保留。", "接入报告导出按钮和历史记录。", "app/meta_analysis/legacy/reporting"),
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
