from __future__ import annotations


DEMO_PROJECT = {
    "project_id": "MP-2024-0007",
    "project_name": "糖皮质激素治疗重症肺炎的疗效",
    "created_at": "2024-05-12 10:30",
    "updated_at": "2024-05-20 14:22",
    "progress_percent": 68,
    "review_type": "Intervention systematic review",
    "current_outcome": "死亡率（All-cause）",
    "current_effect_size": "Odds Ratio",
    "project_dir": "demo_projects/MP-2024-0007",
    "project_status": "Demo",
    "app_version": "0.1.0",
}

DEMO_METRICS = {
    "retrieved_literature_count": "1,248",
    "retrieved_literature_trend": "↑ 12 本周新增",
    "included_studies_count": "24",
    "included_studies_trend": "↑ 2 较上次更新",
    "current_outcome_subtitle": "二分类结局",
    "heterogeneity_i2": "48%",
    "heterogeneity_subtitle": "中等异质性",
}

DEMO_PRISMA_FLOW = {
    "search_count": "1,248",
    "deduplicated_count": "832",
    "screened_count": "312",
    "full_text_count": "58",
    "included_count": "24",
    "updated_at": "2024-05-20 14:22",
}

DEMO_FOREST_STUDIES = (
    {
        "study_name": "Yang 2023",
        "experimental_events": 14,
        "experimental_total": 96,
        "control_events": 25,
        "control_total": 101,
        "effect_size": 0.52,
        "ci_low": 0.26,
        "ci_high": 1.01,
        "weight_percent": 14.8,
    },
    {
        "study_name": "Zhang 2022",
        "experimental_events": 18,
        "experimental_total": 108,
        "control_events": 29,
        "control_total": 112,
        "effect_size": 0.57,
        "ci_low": 0.30,
        "ci_high": 1.08,
        "weight_percent": 15.4,
    },
    {
        "study_name": "Li 2021",
        "experimental_events": 9,
        "experimental_total": 84,
        "control_events": 18,
        "control_total": 86,
        "effect_size": 0.45,
        "ci_low": 0.19,
        "ci_high": 1.05,
        "weight_percent": 10.2,
    },
    {
        "study_name": "Wang 2020",
        "experimental_events": 21,
        "experimental_total": 122,
        "control_events": 34,
        "control_total": 128,
        "effect_size": 0.58,
        "ci_low": 0.32,
        "ci_high": 1.03,
        "weight_percent": 18.7,
    },
    {
        "study_name": "Chen 2019",
        "experimental_events": 13,
        "experimental_total": 88,
        "control_events": 22,
        "control_total": 94,
        "effect_size": 0.57,
        "ci_low": 0.27,
        "ci_high": 1.19,
        "weight_percent": 12.6,
    },
    {
        "study_name": "Guo 2018",
        "experimental_events": 17,
        "experimental_total": 103,
        "control_events": 24,
        "control_total": 109,
        "effect_size": 0.70,
        "ci_low": 0.36,
        "ci_high": 1.37,
        "weight_percent": 13.5,
    },
    {
        "study_name": "Sun 2017",
        "experimental_events": 14,
        "experimental_total": 89,
        "control_events": 17,
        "control_total": 102,
        "effect_size": 0.93,
        "ci_low": 0.43,
        "ci_high": 2.01,
        "weight_percent": 14.8,
    },
)

DEMO_FOREST_SUMMARY = {
    "pooled_effect_size": 0.58,
    "ci_low": 0.46,
    "ci_high": 0.74,
    "total_experimental_n": 690,
    "total_control_n": 732,
    "total_experimental_events": 106,
    "total_control_events": 169,
    "model_label": "固定效应模型（Mantel-Haenszel）",
    "outcome_type": "二分类结局",
    "heterogeneity_text": "异质性: Chi² = 11.50, df = 6 (P = 0.07); I² = 48%",
    "overall_effect_text": "总体效应检验: Z = 4.32 (P < 0.0001)",
    "x_axis_labels": (0.1, 0.2, 0.5, 1, 2, 5, 10),
}

DEMO_RISK_OF_BIAS = (
    {
        "study_name": "Yang 2023",
        "randomization": "低风险",
        "deviations": "低风险",
        "missing_outcome": "低风险",
        "outcome_measurement": "某些担忧",
        "selective_reporting": "低风险",
        "overall": "某些担忧",
    },
    {
        "study_name": "Zhang 2022",
        "randomization": "低风险",
        "deviations": "低风险",
        "missing_outcome": "某些担忧",
        "outcome_measurement": "低风险",
        "selective_reporting": "低风险",
        "overall": "某些担忧",
    },
    {
        "study_name": "Li 2021",
        "randomization": "某些担忧",
        "deviations": "低风险",
        "missing_outcome": "低风险",
        "outcome_measurement": "低风险",
        "selective_reporting": "低风险",
        "overall": "某些担忧",
    },
    {
        "study_name": "Wang 2020",
        "randomization": "低风险",
        "deviations": "低风险",
        "missing_outcome": "低风险",
        "outcome_measurement": "低风险",
        "selective_reporting": "低风险",
        "overall": "低风险",
    },
    {
        "study_name": "Chen 2019",
        "randomization": "高风险",
        "deviations": "某些担忧",
        "missing_outcome": "低风险",
        "outcome_measurement": "某些担忧",
        "selective_reporting": "低风险",
        "overall": "高风险",
    },
)

DEMO_GRADE = {
    "outcome": "死亡率（All-cause）",
    "evidence_quality": "中等",
    "rating_levels": ("success", "success", "warning", "muted"),
    "rows": (
        ("研究局限性", "无严重局限性"),
        ("不一致性", "中等（I² = 48%）"),
        ("间接性", "无严重间接性"),
        ("不精确性", "无严重不精确性"),
        ("发表偏倚", "可能无发表偏倚"),
    ),
    "conclusion": "预期效应：实验组可能降低死亡率（OR 0.58, 95% CI 0.46–0.74）",
}

DEMO_RECENT_OUTPUTS = (
    {"filename": "Forest Plot - 死亡率.pdf", "file_type": "PDF", "timestamp": "2024-05-20 14:20"},
    {"filename": "Funnel Plot - 死亡率.pdf", "file_type": "PDF", "timestamp": "2024-05-20 14:18"},
    {"filename": "敏感性分析结果.pdf", "file_type": "PDF", "timestamp": "2024-05-20 13:45"},
    {
        "filename": "证据概览 (Summary of Findings).xlsx",
        "file_type": "XLSX",
        "timestamp": "2024-05-19 18:03",
    },
    {"filename": "完整报告.docx", "file_type": "DOCX", "timestamp": "2024-05-19 17:52"},
)

DEMO_ANALYSIS_SETTINGS = {
    "effect_model": "固定效应模型（Mantel-Haenszel）",
    "outcome_type": "二分类结局（Odds Ratio）",
    "subgroup_analysis": "无",
    "sensitivity_analysis": "逐一排除法",
    "publication_bias_test": "Egger 检验（P = 0.18）",
    "continuity_correction": "使用 (0.5)",
}

PLACEHOLDER_DESCRIPTIONS = {
    "PICO/Search": "管理研究问题、纳入排除标准、数据库检索式与检索历史。",
    "文献导入": "导入 RIS、NBIB、CSV 或 EndNote 导出文件，并检查字段完整性。",
    "去重审查": "审查自动去重结果，保留需要人工确认的相似记录。",
    "筛选": "进行标题摘要筛选、全文筛选和排除原因管理。",
    "数据提取": "结构化提取研究特征、结局数据和 RoB 2.0 评价。",
    "分析设置": "配置效应模型、结局类型、亚组分析、敏感性分析和发表偏倚检验。",
    "Forest Plot": "查看和导出森林图、合并效应量与异质性结果。",
    "Funnel Plot": "查看漏斗图、Egger 检验和发表偏倚评估。",
    "Reporting": "生成 Summary of Findings、图表附录和完整研究报告。",
    "项目管理": "管理项目元数据、成员、版本和输出目录。",
}
