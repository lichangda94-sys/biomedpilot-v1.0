from __future__ import annotations


STATUS_LABELS = {
    "enabled_preflight_only": "仅预检可用",
    "enabled_review_only": "仅查看可用",
    "disabled_missing_project": "未打开项目",
    "disabled_missing_resolver": "缺少 resolver / input package",
    "disabled_missing_report_ready": "缺少 report-ready gate",
    "disabled_missing_file_picker": "缺少文件选择器",
    "blocked_until_carryover": "等待 scoped carry-over",
    "blocked_until_backend": "等待后端",
    "hidden_until_ready": "后续开放",
    "developer_diagnostics_only": "开发者诊断",
}


ACTION_LABELS = {
    "deg_preflight": "DEG preflight / DEG 预检",
    "formal_deg": "Run controlled two-group DEG / 运行受控 DEG",
    "formal_ora": "Run formal ORA / 运行正式 ORA",
    "formal_gsea": "Run formal GSEA / 运行正式 GSEA",
    "km_logrank": "Run KM / log-rank / 运行 KM 与 log-rank",
    "cox_univariate": "Run univariate Cox / 运行单变量 Cox",
    "clinical_variable_audit": "Clinical variable audit / 临床变量审计",
    "result_review": "Result review / 结果查看",
    "report_draft": "Report draft / 报告草稿",
    "report_ready_package": "Report-ready package / 正式报告包",
    "export_package": "Export package / 导出包",
}


def label_status(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def label_action(action_id: str) -> str:
    return ACTION_LABELS.get(action_id, action_id)
