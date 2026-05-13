# Stage AB1: Meta 用户流程总控页与状态导航

## 本阶段目标

新增 testing / Developer Preview 级 Meta project workflow dashboard，把已有主链包装成测试人员能理解的项目流程总控页。该阶段不新增统计、导入、筛选或报告算法，只汇总状态、入口、输出和 warning。

## Existing BioMedPilot modules audited

- `app/meta_analysis/workspace.py`
- `app/meta_analysis/pages/*`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/traceability_audit_service.py`
- `app/meta_analysis/services/audit_log_service.py`
- `app/meta_analysis/services/*`
- `tests/meta_analysis/*`
- `docs/meta_dev_reports/*`
- `docs/user_testing/*`

当前 git 状态审计：

- 分支：`codex/biomedpilot-root`
- 最近提交：`e3da189 docs(meta): add literature workspace tester walkthrough`
- 未跟踪：`test_inputs/`，本阶段未触碰、未提交

## Legacy modules inspected

- `/Users/changdali/Documents/model9/app/meta_analysis_dashboard_model.py`
- `/Users/changdali/Documents/model9/app/meta_analysis_workspace_widget.py`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/app/meta_analysis_workspace_widget.py`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/core/project_workspace.py`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/literature/*`

## Existing capabilities found

- 正式项目已有 Meta page states：Import、Prepare Screening、Duplicate Review、Screening、Attachment、Extraction、Quality、Analysis、Reporting、Audit。
- 已有 canonical project paths、root manifests、artifact manifest、lineage manifest、Data Center、Task Center、Audit Log。
- 已有 TraceabilityAuditService 和 MetaProjectContractService。
- Workspace 已有 Literature Import Quality Dashboard，但没有覆盖完整项目流程的总控页。
- Legacy `model9` 有 demo dashboard UI，但依赖旧模型和 demo data，不适合直接覆盖当前正式主链。

## Capabilities reused

- 复用 `CANONICAL_PROJECT_PATHS` 和 `MANIFEST_FILES`。
- 复用 `MetaAuditLogService` 读取 audit event。
- 复用 `DataCenter` / `TaskCenter` 计数。
- 复用当前 workspace，新增 dashboard page，不改现有业务服务。
- 复用当前 “missing artifact = warning, not crash” 策略。

## Legacy code migrated

无直接迁移。

## Legacy code not migrated and why

- 未迁移 `model9` 的 demo dashboard model，因为它使用静态 demo forest plot、PRISMA、GRADE 和旧 PySide shell，不读取当前 BioMedPilot manifest / audit / lineage / project artifacts。
- 未迁移 `New project 2` legacy workspace，因为当前正式项目已有更完整的 Meta services、page state、tests 和 manifest/audit/lineage 机制。

## New behavior added

新增：

- `app/meta_analysis/pages/workflow_dashboard_page.py`

提供：

- `WorkflowDashboardState`
- `WorkflowDashboardStep`
- `initial_workflow_dashboard_state`
- `workflow_dashboard_state_from_project`
- `WorkflowDashboardPage`

覆盖步骤：

- Project Setup
- Protocol / Research Question
- Literature Import
- Import Diagnostics
- Duplicate Review
- Criteria Builder
- Title / Abstract Screening
- Full-text / Attachment
- Extraction
- Quality Assessment
- Analysis-ready Dataset
- Meta-analysis Run
- Figures / Tables
- PRISMA / Report
- Reproducibility Package

每一步显示：

- workflow status：Not started / In progress / Needs review / Ready / Completed
- release status：Developer Preview
- input summary
- output summary
- next step
- entrypoint page
- required / existing / missing artifacts
- task count
- audit event count
- data asset count
- warnings
- testing limitations

Workspace 接入：

- `app/meta_analysis/workspace.py` 在 Literature Import Quality Dashboard 前新增 `WorkflowDashboardPage()`。

## Data Center / Task Center / audit / manifest / lineage impact

- 本阶段不新增 Data Center 类型。
- 本阶段不新增 Task Center 类型。
- 本阶段不写 audit log；只读取 audit event count。
- 本阶段不写 manifest；只读取 manifest/canonical artifact 状态。
- 本阶段不改变 lineage 规则；只把缺失 manifest/canonical artifacts 显示为 warning。

## Tests added

- `tests/meta_analysis/test_stage_ab1_workflow_dashboard.py`

覆盖：

- empty project 不崩溃。
- manifest missing warning。
- Project Setup / Import / Import Diagnostics / Duplicate Review / Screening ready 状态推断。
- Data Center asset count。
- Audit event count。
- Task Center running task → In progress。
- page copy 可读性和 Developer Preview 状态。

Focused tests:

- `python3 -m pytest -q tests/meta_analysis/test_stage_ab1_workflow_dashboard.py tests/meta_analysis/test_stage_r_project_contract.py tests/meta_analysis/test_stage_o_traceability_audit.py tests/meta_analysis/test_smoke.py`：22 passed

## Tests run and results

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：340 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：340 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：340 passed
- `python3 -m app.main --smoke-test`：通过

## Remaining testing limitations

- Workflow status 是本地 artifact/task/audit 推断，不是生产级项目管理引擎。
- Protocol、Criteria、部分 Full-text eligibility 等后续 AB 阶段尚未实现完整正式页面。
- 缺失 artifact 只显示 warning，不自动修复。
- Dashboard 不运行任何业务步骤；它只做状态导航和测试提示。

## Next-stage recommendation

进入 Stage AB2：Project Protocol / PICO-PICOS。建议新增 protocol 数据结构和 draft search strategy outputs，并把 `protocol/review_protocol.json` 接入当前 workflow dashboard、manifest 和 audit 机制。
