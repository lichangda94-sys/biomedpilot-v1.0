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

IMPORT_WIZARD_TITLE_ZH = "文献导入向导"
IMPORT_WIZARD_DESCRIPTION_ZH = "按步骤选择来源、选择文件、预览格式、执行导入并查看诊断结果。"
IMPORT_WIZARD_STEP_ZH: dict[str, str] = {
    "source_selection": "选择来源",
    "file_selection": "选择文件",
    "import_preview": "导入预览",
    "import_diagnostics": "导入诊断",
    "duplicate_review_handoff": "进入去重审核",
}
IMPORT_SOURCE_OPTION_ZH: dict[str, str] = {
    "local_database_export": "本地数据库导出文件",
    "zotero_export": "Zotero 导出文件",
    "endnote_export": "EndNote 导出文件",
    "pubmed_download": "PubMed 下载文件",
    "csv_or_txt": "CSV / TXT 文件",
}
DEDUP_MODE_ZH: dict[str, str] = {
    "detect_only": "仅检测重复",
    "manual_review": "导入后人工审核",
    "skip": "暂不去重",
}
DIAGNOSTICS_FIELD_ZH: dict[str, str] = {
    "missing_title_count": "缺标题",
    "missing_author_count": "缺作者",
    "missing_year_count": "缺年份",
    "missing_doi_count": "缺 DOI",
    "missing_pmid_count": "缺 PMID",
    "empty_abstract_count": "摘要为空",
    "invalid_doi_count": "DOI 格式异常",
    "invalid_year_count": "年份格式异常",
    "duplicate_identifier_count": "重复标识符",
    "failed_record_count": "解析失败记录",
}
DIAGNOSTICS_WARNING_MESSAGE_ZH: dict[str, str] = {
    "missing_title_count": "缺少标题的记录需要在筛选前复核。",
    "missing_author_count": "部分记录缺少作者信息。",
    "missing_year_count": "部分记录缺少发表年份。",
    "missing_doi_count": "缺少 DOI 不会阻止导入，但会降低去重匹配能力。",
    "missing_pmid_count": "缺少 PMID 不会阻止导入，但会降低 PubMed 匹配能力。",
    "empty_abstract_count": "部分记录没有摘要，标题摘要筛选时需要人工判断。",
    "invalid_doi_count": "部分 DOI 无法标准化，需要复核来源文件。",
    "invalid_year_count": "部分年份无法解析，需要复核来源文件。",
    "duplicate_identifier_count": "导入批次中发现重复 DOI/PMID 标识符。",
    "failed_record_count": "部分记录解析或校验失败。",
}
LITERATURE_LIBRARY_TITLE_ZH = "文献库表格"
LITERATURE_TABLE_COLUMN_ZH: dict[str, str] = {
    "record_id": "内部记录 ID",
    "title": "题名",
    "authors": "作者",
    "first_author": "第一作者",
    "corresponding_author": "通讯作者",
    "journal": "期刊",
    "year_or_date": "年份 / 日期",
    "doi": "DOI",
    "pmid": "PMID",
    "publication_type": "文献类型",
    "abstract": "摘要",
    "source_database": "来源数据库",
    "source_file": "来源文件",
    "import_batch": "导入批次",
    "duplicate_risk": "重复风险",
    "screening_status": "筛选状态",
    "fulltext_status": "全文状态",
    "extraction_status": "提取状态",
}
DUPLICATE_RISK_LABEL_ZH: dict[str, str] = {
    "high_duplicate_risk": "高重复风险",
    "probable_duplicate": "可能重复 / 标识符冲突",
    "possible_duplicate": "疑似重复",
    "no_obvious_duplicate_risk": "未发现明显重复风险",
}
DUPLICATE_RISK_COLOR_ZH: dict[str, str] = {
    "red": "红色",
    "yellow": "黄色",
    "gray": "灰色",
    "green": "绿色",
}

DUPLICATE_REVIEW_TITLE_ZH = "去重审核"
DUPLICATE_REVIEW_DESCRIPTION_ZH = "查看重复候选组、匹配原因、字段冲突和合并预览；所有决策都需要人工确认。"
DUPLICATE_GROUP_TYPE_ZH: dict[str, str] = {
    "exact": "精确重复",
    "suspected": "疑似重复",
}
DUPLICATE_DECISION_ZH: dict[str, str] = {
    "keep_first": "保留第一条",
    "keep_second": "保留第二条",
    "keep_both": "都保留",
    "merge": "合并记录",
    "mark_not_duplicate": "标记为非重复",
    "exclude_duplicate": "排除重复记录",
    "set_master_record": "设置主记录",
    "skip": "暂不处理",
}
DUPLICATE_FIELD_ZH: dict[str, str] = {
    "title": "题名",
    "abstract": "摘要",
    "authors": "作者",
    "creators": "作者结构",
    "creators/authors": "作者 / 作者结构",
    "year": "年份",
    "date": "日期",
    "year/date": "年份 / 日期",
    "journal": "期刊",
    "publication_title": "出版物名称",
    "journal/publication_title": "期刊 / 出版物名称",
    "doi": "DOI",
    "pmid": "PMID",
    "clinical_trials_ids": "临床试验注册号",
}

CRITERIA_TITLE_ZH = "纳入与排除标准"
CRITERIA_DESCRIPTION_ZH = "维护纳入标准和排除标准，供标题摘要筛选、全文筛选和 PRISMA 排除原因统计参考。"
CRITERIA_READINESS_STATUS_ZH: dict[str, str] = {
    "not_started": "未开始",
    "needs_review": "需要复核",
    "ready": "已就绪",
    "completed": "已完成",
}
CRITERIA_SECTION_ZH: dict[str, str] = {
    "inclusion": "纳入标准",
    "exclusion": "排除标准",
}

SCREENING_TITLE_ZH = "标题摘要筛选"
SCREENING_DESCRIPTION_ZH = "逐篇查看题名、摘要和来源链接，按纳入/排除标准记录 include、exclude、maybe 或 needs review。"
SCREENING_DECISION_ZH: dict[str, str] = {
    "included": "纳入",
    "excluded": "排除",
    "maybe": "可能纳入",
    "needs_review": "需要复核",
    "pending": "待筛选",
}
SCREENING_FILTER_ZH: dict[str, str] = {
    "all": "全部",
    "pending": "待筛选",
    "included": "纳入",
    "excluded": "排除",
    "maybe": "可能纳入",
    "needs_review": "需要复核",
}
SCREENING_PROGRESS_ZH: dict[str, str] = {
    "total": "总数",
    "pending": "待筛选",
    "included": "纳入",
    "excluded": "排除",
    "maybe": "可能纳入",
    "needs_review": "需要复核",
    "screened": "已筛选",
}

ATTACHMENT_TITLE_ZH = "全文 / 附件管理"
ATTACHMENT_DESCRIPTION_ZH = "查看全文状态、附件登记、缺失全文报告和 link/copy/ignore 文件处理状态；不自动下载 PDF。"
ATTACHMENT_MODE_ZH: dict[str, str] = {
    "ignore_attachments": "忽略附件",
    "link_existing_files": "链接现有文件",
    "copy_to_project_library": "复制到项目库",
}
ATTACHMENT_STATUS_ZH: dict[str, str] = {
    "not_generated": "未生成",
    "available": "已生成",
    "unreadable": "无法读取",
    "empty": "无附件",
    "broken_paths_detected": "发现失效路径",
    "valid": "路径验证通过",
    "not_run": "未验证",
}

FULLTEXT_ELIGIBILITY_TITLE_ZH = "全文筛选"
FULLTEXT_ELIGIBILITY_DESCRIPTION_ZH = "根据标题摘要纳入或可能纳入记录，人工记录全文状态、全文排除原因和最终纳入研究。"
FULLTEXT_STATUS_ZH: dict[str, str] = {
    "not_checked": "未检查",
    "available_online": "在线可获得",
    "local_pdf_linked": "已链接本地 PDF",
    "local_pdf_copied": "已复制本地 PDF",
    "missing_full_text": "缺失全文",
    "failed_to_access": "访问失败",
    "manual_review_required": "需要人工复核",
    "excluded_after_full_text_review": "全文后排除",
    "included_for_extraction": "纳入数据提取",
}

EXTRACTION_TITLE_ZH = "数据提取"
EXTRACTION_DESCRIPTION_ZH = "以研究为单位填写 study characteristics 和 outcome rows，显示草稿、完整性评分、必填字段和人工补充记录。"
EXTRACTION_FIELD_ZH: dict[str, str] = {
    "record_id": "文献记录 ID",
    "study_id": "研究 ID",
    "reviewer_id": "提取人",
    "profile_type": "Meta 类型",
    "first_author": "第一作者",
    "year": "年份",
    "country": "国家/地区",
    "study_design": "研究设计",
    "population": "研究人群",
    "sample_size": "样本量",
    "intervention_or_exposure": "干预 / 暴露",
    "comparator": "对照",
    "follow_up": "随访",
    "outcome_name": "结局名称",
    "effect_measure": "效应量",
    "source_location": "数据来源位置",
    "manual_supplement": "人工补充",
}

QUALITY_TITLE_ZH = "质量评价"
QUALITY_DESCRIPTION_ZH = "根据研究设计推荐 NOS / QUADAS-2 / RoB2 simplified，逐 domain 填写 judgement 和 notes，overall judgement 只作建议。"
QUALITY_FIELD_ZH: dict[str, str] = {
    "study_selector": "选择研究",
    "tool_selector": "选择评价工具",
    "domain_judgements": "领域判断",
    "domain_notes": "领域备注",
    "overall_judgement": "总体判断",
    "reviewer_notes": "评价人备注",
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
