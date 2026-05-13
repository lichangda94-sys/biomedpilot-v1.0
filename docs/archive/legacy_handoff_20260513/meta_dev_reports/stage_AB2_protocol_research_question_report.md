# Stage AB2: Project Protocol / PICO-PICOS Research Question Module

## 本阶段目标

为 Meta Analysis Developer Preview 增加 Project Protocol / PICO-PICOS 研究方案模块，用于记录研究题目、review question、PICO/PICOS、目标 Meta 分析类型、计划检索数据库、检索日期和检索式草稿。该阶段只生成本地 draft artifacts，不执行真实数据库检索，不把任何能力标记为 production/open。

## Continuity audit

正式项目根目录：

- `/Users/changdali/Documents/BioMedPilot`

当前 git 状态审计：

- 分支：`codex/biomedpilot-root`
- 基线 HEAD：`7971305 feat(meta): add workflow dashboard`
- 未跟踪：`test_inputs/`，本阶段未触碰、未提交

审计的正式项目模块：

- `app/meta_analysis/workspace.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/pages/*`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/audit_log_service.py`
- `app/meta_analysis/services/*`
- `app/meta_analysis/extraction/schema_registry.py`
- `tests/meta_analysis/*`
- `docs/meta_dev_reports/*`
- `docs/user_testing/*`

正式项目已有相关能力：

- AB1 已有 workflow dashboard，并预留 `Protocol / Research Question` 步骤和 `protocol/review_protocol.json` prerequisite。
- 已有 canonical project manifest、artifact manifest、lineage manifest、Data Center、Task Center、Audit Log。
- 已有 method/profile registry：`app/meta_analysis/extraction/schema_registry.py`。
- 尚无正式 `ProjectProtocol` model、protocol service、protocol artifacts 或 protocol page state。

## Legacy capability audit

审计的 legacy 目录：

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project 2`
- `/Users/changdali/Documents/New project`

发现的 legacy 相关能力：

- `model9/app_meta/ui/pico_search_page.py`
- `New project 2/app/meta_analysis/legacy/app_meta/ui/pico_search_page.py`
- `model9/app/project_navigation_model.py`
- `New project 2/app/shared/feature_availability.py`
- legacy docs 中的 `PICO/Search` 页面说明

Legacy 能力判断：

- legacy `pico_search_page.py` 是 demo/PySide 页面，包含 PICO 表单、数据库 checkbox、Boolean query preview 和 readiness 文案。
- legacy 实现不写当前 BioMedPilot project_dir，不接入 manifest、artifact manifest、audit log、lineage、Data Center 或 AB1 workflow dashboard。

迁移结论：

- 未直接迁移 legacy 代码。
- 仅参考 legacy 页面分组和文案方向，正式实现采用当前 BioMedPilot 的 service/model/page-state 架构。

## Capabilities reused

- 复用 AB1 `WorkflowDashboardState` 和 Protocol step。
- 复用 `MetaProjectContractService` 写 root manifests。
- 复用 `MetaAuditLogService.record_event(... event_type="record_saved")`，用 `target_type="review_protocol"` 标记 protocol 保存。
- 复用 `DataCenter.register_asset` 登记 protocol artifacts。
- 复用 `EXTRACTION_SCHEMA_REGISTRY` 校验 method profile。
- 复用当前 workspace，不修改 shell / shared / packaging。

## New files

- `app/meta_analysis/models/protocol.py`
- `app/meta_analysis/services/protocol_service.py`
- `app/meta_analysis/pages/protocol_page.py`
- `tests/meta_analysis/test_stage_ab2_protocol_research_question.py`

## Modified files

- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/workspace.py`

## Protocol data structure

新增 `ProjectProtocol`，核心字段包括：

- `project_id`
- `protocol_id`
- `project_title`
- `review_question`
- `background`
- `rationale`
- `objective`
- `meta_analysis_type`
- `method_profile_id`
- `pico.population`
- `pico.intervention_or_exposure`
- `pico.comparator`
- `pico.outcomes`
- `pico.study_design`
- `primary_outcome`
- `secondary_outcomes`
- `eligible_study_designs`
- `planned_databases`
- `custom_databases`
- `search_date`
- `language_restriction`
- `date_range_restriction`
- `notes`
- `developer_preview`
- `readiness_status`
- `confirmed`
- `warnings`

Readiness 状态：

- `needs_review`：字段缺失或需要 reviewer 复核。
- `ready`：核心字段完整并已生成 draft search strategy。
- `completed`：用户明确确认 protocol，仍然是 Developer Preview/testing。

## Output artifacts

保存 protocol 时写入：

- `protocol/review_protocol.json`
- `protocol/search_terms_draft.json`
- `protocol/search_strategy_preview.md`
- `protocol/protocol_summary.md`

这些路径已加入 `CANONICAL_PROJECT_PATHS`，并由 `MetaProjectContractService.write_project_manifests()` 写入：

- `project.json`
- `data_manifest.json`
- `artifact_manifest.json`
- `task_manifest.json`
- `lineage_manifest.json`

Lineage 新增：

- `protocol/search_strategy_preview.md -> protocol/review_protocol.json`

## Search strategy draft logic

`ProjectProtocolService` 根据 PICO/PICOS 字段生成：

- PubMed draft：Title/Abstract Boolean query。
- Web of Science draft：`TS=(...)` copyable query。
- CNKI draft：中文数据库可复制初稿。
- WanFang draft：中文数据库可复制初稿。

`search_terms_draft.json` 保留：

- `free_text_terms`
- `synonyms`
- `mesh_placeholder`
- `chinese_terms_placeholder`

所有检索式均标记为 `draft_needs_review`。本阶段不执行 PubMed API、Web of Science、CNKI 或 WanFang 自动检索。

## Workflow dashboard integration

AB1 dashboard 的 `Protocol / Research Question` step 现在读取：

- `protocol/review_protocol.json`
- `protocol/search_terms_draft.json`
- `protocol/search_strategy_preview.md`
- protocol `warnings`
- protocol `readiness_status`
- protocol `confirmed`

状态推断：

- 无 `review_protocol.json`：`Not started`
- 有 protocol 但未生成 search strategy：`In progress`
- 有 search strategy 且存在 warnings：`Needs review`
- 核心字段完整并生成 search strategy：`Ready`
- 用户 confirmed：`Completed`

该步骤仍显示 `Developer Preview`。

## Data Center / Task Center / audit / manifest / lineage impact

Data Center 新增登记类型：

- `review_protocol`
- `search_terms_draft`
- `search_strategy_preview`
- `protocol_summary`

Task Center：

- 本阶段未新增 Task Center 类型，避免修改 shared task enum。Protocol 保存通过 Data Center、audit log、manifest 和 workflow dashboard 追踪。

Audit log：

- 保存或确认 protocol 时记录 `record_saved`。
- `target_type="review_protocol"`。

Manifest / lineage：

- 新增 protocol canonical paths。
- `artifact_manifest.json` 会列出四个 protocol artifacts。
- `lineage_manifest.json` 会记录 search strategy draft 到 review protocol 的来源关系。

## Tests added

新增：

- `tests/meta_analysis/test_stage_ab2_protocol_research_question.py`

覆盖：

- 空项目 protocol page state 不崩溃。
- 保存完整 PICO/PICOS protocol 后生成四个 protocol artifacts。
- 缺少 population / outcome / meta_analysis_type 等核心字段时生成 warnings。
- 生成 PubMed / Web of Science / CNKI / WanFang draft search strategies。
- protocol artifacts 进入 artifact manifest。
- Data Center 登记 protocol artifacts。
- audit log 记录 protocol 保存。
- workflow dashboard Protocol step 能显示 `Not started` / `Needs review` / `Ready` / `Completed`。

Focused test result:

- `python3 -m compileall -q app/meta_analysis tests/meta_analysis/test_stage_ab2_protocol_research_question.py`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab2_protocol_research_question.py`：5 passed

## Tests run and results

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：345 passed
- `python3 scripts/run_tests.py`：345 passed
- `python3 -m app.main --smoke-test`：通过，输出 `workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`、`pyside6_available=True`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：345 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：345 passed

## 未实现内容

- 未实现 PubMed API 一键检索。
- 未实现 Web of Science / CNKI / WanFang 自动登录或自动下载。
- 未实现正式数据库 adapter。
- 未实现 AI 自动生成并锁定最终检索式。
- 未实现自动 PDF 下载、OCR、机构全文访问。
- 未实现 production 级 protocol 或投稿级检索式。

## 下一阶段建议

进入 Stage AB3：Production-like Literature Import Wizard。

建议复用当前 NBIB / RIS / CSV import、Zotero / EndNote / PubMed profile、import diagnostics 和 recent import batches，把它们包装为 step-based 导入向导，不重写 parser。
