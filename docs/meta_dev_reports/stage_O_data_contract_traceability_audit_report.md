# Stage O Data Contract Traceability Audit Report

## 本阶段目标

确认 Meta Analysis 当前 testing 工作流生成的核心结果可以追溯到上游数据，并且在缺失来源时以 warning 方式报告，不崩溃、不伪装完整。

## 实际完成内容

- 新增轻量审计层：`TraceabilityAuditService`。
- 支持 artifact manifest、data lineage checker、reproducibility package checker、formal report artifact checker。
- 新增 Stage O tests，覆盖完整 lineage、缺失来源 warning、复现包完整性、artifact lock 不覆盖、AI suggestion 不覆盖正式数据。

## 修改/新增文件列表

- `app/meta_analysis/services/traceability_audit_service.py`
- `tests/meta_analysis/test_stage_o_traceability_audit.py`
- `docs/meta_dev_reports/stage_O_data_contract_traceability_audit_report.md`

## 数据契约检查

- `analysis_result -> analysis_ready_dataset`
- `analysis_ready_dataset -> extraction_records`
- `extraction_records -> included literature/screening records`
- `forest_plot / funnel_plot -> analysis_result`
- `formal_meta_report -> figures / result table / extraction / analysis artifacts`
- `PRISMA summary -> project source artifacts`
- `reproducibility package -> required project entries`

## 缺失来源策略

缺失 dataset、extraction source、figure file、formal report artifact、PRISMA source 或 reproducibility entry 时返回 warning。审计服务不直接抛出异常，也不把缺失内容标为完成。

## Reproducibility Package 检查

当前 checker 要求至少包含：

- `project.json`
- `reports/formal_meta_report.md`
- `reports/prisma_flow_summary.json`
- `extraction/extraction_records.json`
- `quality/quality_assessments.json`
- `analysis/analysis_ready_datasets.json`
- `analysis/analysis_results.json`
- `software_version.json`

## Artifact Lock

测试确认 formal report lock 后再次导出 HTML 会生成带时间戳的新版本，原文件不被覆盖，并返回 `formal_report_locked_new_version_created` warning。

## AI Safety

测试确认 AI suggestion 经过 accept/apply 后也只写入 AI applied suggestions 记录，不覆盖 `extraction_records.json` 等正式数据。

## 新增数据类型

本阶段是审计与测试层增强，没有新增 Data Center 类型。

## 新增 Task Center 类型

本阶段没有新增 Task Center 类型。

## 测试结果

Stage O 新增测试覆盖 lineage、manifest、reproducibility、lock 和 AI safety。

- Stage O focused tests: `5 passed`
- M-P focused tests: `18 passed`
- Full venv pytest: `256 passed`
- Unified `scripts/run_tests.py`: `256 passed`
- Smoke test: passed
- Local shell `python` / `pytest`: unavailable in this environment; venv commands passed.

## 当前限制

- Traceability audit 目前为轻量本地 checker，不是完整 JSON schema validator。
- Formal report artifact checker 基于当前 Markdown 内容和路径模式识别，后续可升级为结构化 report manifest。
- Import/Prepare/Dedup 早期输出仍有部分 storage-root 路径，真实 beta 前应进一步统一项目目录数据契约。

## 下一阶段建议

进入 Stage P：UX 与生产化差距清单。
