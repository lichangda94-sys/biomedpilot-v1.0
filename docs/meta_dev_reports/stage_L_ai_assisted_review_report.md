# Stage L: AI-assisted Review Report

## 本阶段目标

在 Meta Analysis 主流程稳定后增加 AI 辅助能力。AI 只能生成候选建议，不能直接修改正式数据。所有 AI 输出必须经过人工 accepted / rejected / edited，并且 accepted 后还需要显式 apply。

本阶段不开发自动全文提取并直接保存、自动最终纳入排除、自动最终结论、外部 API 强绑定或无人工确认的 AI 修改。

## AI Suggestion 数据结构

新增 `AISuggestion`：

- `suggestion_id`
- `project_id`
- `target_type`
- `target_id`
- `suggestion_type`
- `suggested_value`
- `rationale`
- `confidence`
- `status`
- `reviewer_action`
- `created_at`
- `updated_at`

状态：

- `pending`
- `accepted`
- `rejected`
- `edited`

## 支持的 Target Type

- `search_strategy`
- `screening_decision`
- `exclusion_reason`
- `extraction_candidate`
- `report_text`
- `data_warning`

## 支持的 Suggestion Type

- `keyword_expansion`
- `relevance_screening`
- `exclusion_reason_suggestion`
- `extraction_candidate`
- `data_consistency_warning`
- `report_draft_suggestion`

## 人工确认机制

新增 `AISuggestionService`：

- `create_ai_suggestion`
- `create_mock_suggestion`
- `list_ai_suggestions`
- `accept_ai_suggestion`
- `reject_ai_suggestion`
- `edit_ai_suggestion`
- `apply_accepted_suggestion`

规则：

- suggestion 默认 `pending`。
- `pending` 不能 apply。
- `rejected` 不能 apply。
- `edited` 仍需后续 accept，不能直接 apply。
- `accepted` 也不会自动进入目标数据。
- 只有明确调用 `apply_accepted_suggestion` 后，才写入 non-overwrite application log。

## 防止 AI 覆盖正式数据的措施

Apply 当前只写入：

- `project_dir/ai/applied_suggestions.json`

该文件记录：

- suggestion id
- target type / target id
- suggestion type
- suggested value
- applied timestamp
- safety note

服务不会直接覆盖：

- `screening_decisions`
- `extraction_records`
- `analysis_results`
- formal reports

所有 create / accept / reject / edit / apply 操作均登记 Task Center。

## UI 新增内容

新增 testing page state：

- `app/meta_analysis/pages/ai_suggestions_page.py`

页面状态包含：

- AI Suggestions Queue 标题
- testing 状态
- queue columns
- target type options
- suggestion type options
- allowed actions
- safety rules
- empty state

当前没有改主 workspace 导航结构。

## Data Center / Task Center 新增类型

Data Center 新增：

- `ai_suggestions`

Task Center 新增：

- `ai_suggestion_create`
- `ai_suggestion_accept`
- `ai_suggestion_reject`
- `ai_suggestion_edit`
- `ai_suggestion_apply`

## 新增 / 修改文件

- `app/meta_analysis/models/ai_suggestion.py`
- `app/meta_analysis/services/ai_suggestion_service.py`
- `app/meta_analysis/pages/ai_suggestions_page.py`
- `app/shared/task_center/service.py`
- `app/shared/feature_availability.py`
- `tests/meta_analysis/test_ai_assisted_review.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `docs/meta_dev_reports/stage_L_ai_assisted_review_report.md`

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q tests/meta_analysis/test_ai_assisted_review.py tests/meta_analysis/test_developer_preview_stabilization.py`
  - 11 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 238 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 238 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前限制

- 当前 provider 为 mock/local suggestion provider。
- 尚未接入外部 API、本地 LLM 或真实文献语义模型。
- Apply 写入 non-overwrite AI application log，不自动改变正式 screening/extraction/analysis/report 结果。
- 没有完整多 reviewer conflict resolution UI。
- AI 不生成最终结论。

## 下一阶段建议

Stage A-L 已按 Developer Preview / testing 完成。下一步建议进入稳定化和审计：

- 做端到端 UX 验证。
- 做统计方法专家复核。
- 做正式数据格式兼容性审计。
- 明确哪些 testing 功能可以逐步升级，哪些仍应保持 placeholder / unavailable。
