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
    FeatureAvailability("bioinformatics", "bio-local-expression-import", "Local Expression Matrix Import", FeatureAvailabilityStatus.TESTING, "已支持本地 CSV / TSV / TXT / XLSX 表达矩阵结构诊断、导入摘要和标准 asset manifest；尚未进行表达矩阵标准化、样本分组和差异分析。", "接入数据资产确认、样本注释导入和表达矩阵清洗。"),
    FeatureAvailability("bioinformatics", "bio-download", "数据下载", FeatureAvailabilityStatus.TESTING, "读取 GEO 查询计划并生成下载计划；当前不实际下载 NCBI 数据。", "在用户确认后接入 legacy GEO 下载执行。", "app/bioinformatics/legacy/geo_pipeline"),
    FeatureAvailability("bioinformatics", "bio-asset-detection", "数据资产识别", FeatureAvailabilityStatus.TESTING, "读取 GEO 下载计划并扫描本地目标目录，不联网、不下载。", "接入真实下载产物后的表达矩阵、样本注释和平台注释识别。", "app/bioinformatics/legacy/geo_processing"),
    FeatureAvailability("bioinformatics", "bio-cleaning", "数据清洗", FeatureAvailabilityStatus.TESTING, "读取资产识别结果并生成清洗预检计划；当前不执行矩阵标准化。", "接入受控矩阵清洗、标准化结果预览和输出登记。", "app/bioinformatics/legacy/geo_processing"),
    FeatureAvailability("bioinformatics", "bio-sample-groups", "样本分组", FeatureAvailabilityStatus.TESTING, "读取数据清洗计划并生成样本分组预检；当前不自动推断病例/对照分组。", "接入样本注释表预览、分组编辑和保存。"),
    FeatureAvailability("bioinformatics", "bio-deg", "差异表达分析", FeatureAvailabilityStatus.TESTING, "读取样本分组计划并检查表达矩阵、样本注释和病例/对照分组；当前不运行正式差异统计。", "接入参数配置、统计引擎选择和受控 DEG runner。"),
    FeatureAvailability("bioinformatics", "bio-enrichment", "富集分析", FeatureAvailabilityStatus.TESTING, "读取差异表达分析预检并检查 DEG 结果或基因列表；当前不下载数据库、不运行 GO / KEGG / GSEA。", "接入基因列表确认、数据库版本选择和受控富集 runner。"),
    FeatureAvailability("bioinformatics", "bio-correlation", "相关性分析", FeatureAvailabilityStatus.TESTING, "读取数据清洗计划并检查表达矩阵与样本注释；当前不计算相关系数、不生成相关性图。", "接入目标基因/表型选择、相关方法设置和图表输出。"),
    FeatureAvailability("bioinformatics", "bio-survival", "生存分析", FeatureAvailabilityStatus.TESTING, "读取数据清洗计划并检查临床/生存字段；当前不计算 Kaplan-Meier、log-rank 或 Cox 模型。", "接入生存字段映射、分组策略和受控生存分析 runner。"),
    FeatureAvailability("bioinformatics", "bio-reporting", "报告导出", FeatureAvailabilityStatus.TESTING, "支持导出 Bioinformatics 测试摘要，汇总已有预检 JSON；当前不生成正式报告或图表包。", "接入正式报告模板、图表包和 Report Center 历史。"),
    FeatureAvailability("meta_analysis", "meta-pico", "研究问题 / PICO", FeatureAvailabilityStatus.TESTING, "legacy PICO/search 能力已保留。", "接入统一项目记录。", "app/meta_analysis/legacy/pico"),
    FeatureAvailability("meta_analysis", "meta-literature-import", "文献导入", FeatureAvailabilityStatus.TESTING, "支持 NBIB / RIS / CSV 文件导入，并登记任务与数据资产。", "继续接入 Prepare for Screening 和 Duplicate Review。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-dedup-prep", "去重准备", FeatureAvailabilityStatus.TESTING, "读取 Literature Import 输出并生成标准化筛选准备记录。", "继续接入 Duplicate Review。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-duplicate-review", "Duplicate Review", FeatureAvailabilityStatus.TESTING, "已支持疑似重复组查看和最小人工决策；尚未支持完整批量合并 UI、高级 fuzzy matching 和多人审核。", "继续完善批量处理、冲突合并预览和审核记录。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-screening", "Screening", FeatureAvailabilityStatus.TESTING, "读取 Prepare/Duplicate 输出并生成标题摘要筛选队列，支持最小 include/exclude/maybe 决策保存，并新增 testing full-text registry、全文筛选排除报告和基础质量评价输出。", "接入 publication export 和复现包。", "app/meta_analysis/legacy/literature"),
    FeatureAvailability("meta_analysis", "meta-extraction", "Extraction", FeatureAvailabilityStatus.TESTING, "读取 Screening 队列并为 included 文献生成数据提取池；支持 testing 结构化 ExtractionRecord 表单保存、校验和 CSV 导出。", "接入 Analysis-ready dataset 构建。", "app/meta_analysis/legacy/extraction"),
    FeatureAvailability("meta_analysis", "meta-analysis", "Analysis", FeatureAvailabilityStatus.TESTING, "读取 Extraction 输出并执行 Analysis 预检，可构建 analysis-ready dataset，支持基础 testing pooled effect、forest plot PNG 和 result table CSV；当前不是生产级正式 Meta 统计。", "接入正式报告和 PRISMA 摘要。", "app/meta_analysis/legacy/analysis"),
    FeatureAvailability("meta_analysis", "meta-reporting", "Reporting", FeatureAvailabilityStatus.TESTING, "保留 Analysis 预检测试版 Markdown 摘要，支持 testing PRISMA 数字摘要、formal Markdown/HTML/DOCX report 雏形、supplementary exports、figure package、project snapshot 和复现包；PDF 正式报告仍未开放。", "继续完善 publication export、PDF 策略和投稿级模板。", "app/meta_analysis/legacy/reporting"),
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
