# Stage A Developer Preview Stabilization Report

## 本阶段目标

稳定当前 Meta Analysis Developer Preview 主链，确保已接入但未完成的功能均准确标记为 testing，不误标为 open 或 production，并补齐当前状态说明和稳定性测试。

## 实际完成内容

- 审查并锁定 Meta Analysis 7 步 testing 主链：
  - Literature Import
  - Prepare Screening
  - Duplicate Review
  - Screening
  - Extraction
  - Analysis
  - Reporting
- 新增 Meta Analysis 当前状态文档，明确模块仍为 Developer Preview / testing。
- 新增 Stage A 稳定性测试，覆盖 7 步 workspace、Feature Availability、Data Center 类型、Task Center 类型、Analysis preflight 和 Reporting test summary。
- 未开发正式统计、正式报告、森林图、全文管理、质量评价或 AI 辅助。

## 修改/新增文件列表

- `docs/meta_analysis_current_status.md`
- `docs/meta_dev_reports/stage_A_developer_preview_stabilization_report.md`
- `tests/meta_analysis/test_developer_preview_stabilization.py`

## 新增数据类型

无。

## 新增 Task Center 类型

无。

## 新增 Data Center 类型

无。

## 保留并验证的 Data Center 类型

- `literature_records`
- `screening_ready_records`
- `duplicate_candidate_groups`
- `deduplicated_literature`
- `screening_queue`
- `screening_decisions`
- `extraction_pool`
- `analysis_preflight`
- `meta_analysis_report`

## 保留并验证的 Task Center 类型

- `literature_import`
- `prepare_screening`
- `duplicate_review`
- `dedup_decision`
- `screening`
- `screening_decision`
- `extraction`
- `analysis`
- `report_export`

## 新增测试

- `test_meta_developer_preview_chain_has_seven_testing_steps`
- `test_meta_page_states_are_testing_and_developer_preview_scoped`
- `test_meta_feature_availability_matches_current_testing_scope`
- `test_meta_data_center_types_remain_documented_in_services`
- `test_meta_task_center_types_remain_available`
- `test_meta_analysis_and_reporting_are_not_formal_outputs`

## 测试结果

- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，无法直接运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis -q`
  - 70 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 172 passed, 1 skipped。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 172 passed, 1 skipped。

## 当前仍然 testing / experimental 的功能

当前 Meta Analysis 主链全部为 testing：

- 文献导入
- 去重准备
- Duplicate Review
- Screening
- Extraction
- Analysis
- Reporting

当前没有 Meta Analysis 功能被标记为 open 或 production。

## 已知限制

- Analysis 仍是 preflight，不执行正式 Meta 统计。
- Reporting 仍是 testing Markdown summary，不生成正式系统综述报告。
- Extraction 仍只生成 extraction pool，尚未提供正式结构化 ExtractionRecord。
- Screening 和 Duplicate Review 仍是最小人工决策能力，不是完整多人审核流程。
- 尚未实现全文管理、风险偏倚评价、森林图、漏斗图、正式 PRISMA/Word/PDF 报告或 AI 辅助。

## 阶段明确回答

- 当前 Meta Analysis 是否仍为 Developer Preview：是。
- 当前 7 步主链是否稳定：是，新增测试已锁定 7 步主链与 testing 状态。
- 当前测试数量和结果：全量测试 172 passed, 1 skipped；Meta 测试 70 passed。
- 哪些功能仍然只是 testing：当前 7 步 Meta Analysis 主链全部仍为 testing。
- 下一阶段是否可以进入 Structured Extraction Core：可以。Stage B 应在不破坏 `extraction_pool` 的前提下新增结构化 `extraction_records` core。

## 下一阶段建议

进入 Stage B：Structured Extraction Core。优先实现正式 extraction 数据模型、schema registry、validation service、storage service 和测试，不优先做复杂 UI，不开发正式统计。
