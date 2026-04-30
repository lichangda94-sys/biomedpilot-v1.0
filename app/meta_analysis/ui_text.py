from __future__ import annotations

from dataclasses import dataclass


INTERNAL_BETA_STATUS_ZH = "内部测试版 / Developer Preview / testing"
DEVELOPER_PREVIEW_ZH = "内部测试"
DEVELOPER_INFO_TITLE_ZH = "开发者信息"
USER_MISSING_ARTIFACT_WARNING_ZH = "当前步骤缺少必要输出，请按下一步建议补齐。"
WORKFLOW_DASHBOARD_TITLE_ZH = "Meta 分析流程总控"
WORKFLOW_DASHBOARD_DESCRIPTION_ZH = "用中文汇总当前 Meta 项目进度、需要复核的问题和下一步建议。"
WORKFLOW_EMPTY_STATE_ZH = "选择或创建 Meta 项目后，这里会显示每一步的状态、问题数量和下一步建议。"


WORKFLOW_STATUS_ZH: dict[str, str] = {
    "Not started": "未开始",
    "In progress": "进行中",
    "Needs review": "需要复核",
    "Ready": "已就绪",
    "Completed": "已完成",
    "Developer Preview": DEVELOPER_PREVIEW_ZH,
}


@dataclass(frozen=True)
class WorkflowStepText:
    title_zh: str
    subtitle_en: str
    input_summary_zh: str
    output_summary_zh: str
    next_step_zh: str
    entrypoint_zh: str


WORKFLOW_STEP_TEXT: dict[str, WorkflowStepText] = {
    "project_setup": WorkflowStepText(
        "项目设置",
        "Project Setup",
        "项目名称、项目目录和基础项目文件。",
        "项目配置和基础 manifest 文件。",
        "完善研究问题 / PICO-PICOS。",
        "进入项目设置",
    ),
    "protocol": WorkflowStepText(
        "研究问题 / PICO-PICOS",
        "Protocol / Research Question",
        "研究题目、PICO/PICOS、分析类型和计划检索数据库。",
        "研究方案、检索词草稿和检索策略预览。",
        "确认研究问题后进入文献导入。",
        "进入研究问题页面",
    ),
    "literature_import": WorkflowStepText(
        "文献导入",
        "Literature Import",
        "本地 RIS、NBIB 或 CSV 文献导出文件。",
        "导入后的文献记录和导入批次摘要。",
        "查看导入诊断，确认字段质量。",
        "进入文献导入",
    ),
    "import_diagnostics": WorkflowStepText(
        "导入诊断",
        "Import Diagnostics",
        "文献导入生成的诊断摘要和 warning 文件。",
        "缺失字段、解析失败和 warning 数量。",
        "修正严重问题后进入去重审核。",
        "查看导入诊断",
    ),
    "duplicate_review": WorkflowStepText(
        "去重审核",
        "Duplicate Review",
        "导入文献或筛选准备记录。",
        "重复候选组、合并预览和去重决策。",
        "确认重复文献后设置纳入与排除标准。",
        "进入去重审核",
    ),
    "criteria_builder": WorkflowStepText(
        "纳入与排除标准",
        "Criteria Builder",
        "研究问题和 PICO/PICOS 信息。",
        "纳入标准、排除标准和标准摘要。",
        "使用标准开展标题摘要筛选。",
        "进入标准设置",
    ),
    "title_abstract_screening": WorkflowStepText(
        "标题摘要筛选",
        "Title / Abstract Screening",
        "去重后的文献和纳入/排除标准。",
        "标题摘要筛选决策、进度和排除原因。",
        "对 include / maybe 文献进行全文筛选。",
        "进入标题摘要筛选",
    ),
    "fulltext_attachment": WorkflowStepText(
        "全文 / 附件管理",
        "Full-text / Attachment",
        "标题摘要筛选后的候选文献和本地 PDF 路径。",
        "全文状态、附件登记、缺失全文报告和最终纳入清单。",
        "确认全文资格后进入数据提取。",
        "进入全文与附件管理",
    ),
    "extraction": WorkflowStepText(
        "数据提取",
        "Data Extraction",
        "最终纳入研究和对应提取表结构。",
        "结构化提取记录、草稿和完整性检查。",
        "完成提取后进行质量评价。",
        "进入数据提取",
    ),
    "quality_assessment": WorkflowStepText(
        "质量评价",
        "Quality Assessment",
        "纳入研究和推荐质量评价工具。",
        "质量评价记录、质量表和质量摘要。",
        "完成质量评价后检查分析数据集。",
        "进入质量评价",
    ),
    "analysis_ready_dataset": WorkflowStepText(
        "分析数据集检查",
        "Analysis-ready Dataset",
        "提取记录、结局指标和效应量类型。",
        "可分析数据集、纳入/排除行和校验摘要。",
        "确认数据集后运行 Meta 分析。",
        "进入分析数据集检查",
    ),
    "meta_analysis_run": WorkflowStepText(
        "Meta 分析运行",
        "Meta-analysis Run",
        "分析数据集和 fixed/random 模型设置。",
        "合并效应量、异质性、研究级结果和适用性 warning。",
        "生成图表和结果表。",
        "进入 Meta 分析",
    ),
    "figures_tables": WorkflowStepText(
        "图表与结果表",
        "Figures / Tables",
        "Meta 分析结果。",
        "森林图、漏斗图和结果表。",
        "将结果纳入 PRISMA / 报告。",
        "进入图表与结果表",
    ),
    "prisma_report": WorkflowStepText(
        "PRISMA / 报告",
        "PRISMA / Report",
        "导入、去重、筛选、全文、提取、分析和图表 artifacts。",
        "PRISMA 数字、简化流程图、报告和 report manifest。",
        "导出复现包。",
        "进入 PRISMA / 报告",
    ),
    "reproducibility_package": WorkflowStepText(
        "可复现性导出",
        "Reproducibility Package",
        "完整项目 artifacts、manifest 和报告。",
        "复现包、附表、图表包和项目快照。",
        "进入 internal beta 复核。",
        "进入可复现性导出",
    ),
}


def workflow_status_zh(status: str) -> str:
    return WORKFLOW_STATUS_ZH.get(status, status)


def release_status_zh(status: str) -> str:
    return WORKFLOW_STATUS_ZH.get(status, DEVELOPER_PREVIEW_ZH if "Developer Preview" in status else status)


def workflow_step_text(step_id: str) -> WorkflowStepText:
    return WORKFLOW_STEP_TEXT.get(
        step_id,
        WorkflowStepText(
            title_zh=step_id,
            subtitle_en=step_id,
            input_summary_zh="请查看该步骤的输入说明。",
            output_summary_zh="请查看该步骤的输出说明。",
            next_step_zh="请根据页面提示继续。",
            entrypoint_zh="进入该步骤",
        ),
    )


def warning_summary_zh(warnings: tuple[str, ...] | list[str]) -> str:
    if not warnings:
        return "暂无需要处理的问题。"
    if any(str(item).startswith("missing_required_artifacts:") for item in warnings):
        return USER_MISSING_ARTIFACT_WARNING_ZH
    return f"当前有 {len(warnings)} 条问题需要复核。"
