# Stage AB5: Inclusion / Exclusion Criteria Builder

## 本阶段目标

新增 testing / Developer Preview 级 Inclusion / Exclusion Criteria Builder，为 title/abstract screening、full-text screening 和 PRISMA reason counts 提供可追溯 criteria artifacts。该阶段不自动纳入、不自动排除、不修改既有 screening decisions。

## Continuity audit

正式项目根目录：

- `/Users/changdali/Documents/BioMedPilot`

当前 git 状态审计：

- 分支：`codex/biomedpilot-root`
- 基线 HEAD：`55de656 feat(meta): add literature library table`
- 未跟踪：`test_inputs/`，本阶段未触碰、未提交

审计的正式项目模块：

- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/pages/attachment_page.py`
- `app/meta_analysis/services/screening_service.py`
- `app/meta_analysis/services/fulltext_service.py`
- `app/meta_analysis/models/systematic_review.py`
- `app/meta_analysis/services/project_contract_service.py`
- `tests/meta_analysis/test_screening_service.py`
- `tests/meta_analysis/test_systematic_review_workflow_completion.py`

正式项目已有相关能力：

- Screening decision 已要求 excluded 决策填写排除原因。
- Full-text service 已有 full-text exclusion reason dictionary 和 report export。
- AB1 workflow dashboard 已预留 Criteria Builder 步骤和 `criteria/criteria_summary.md`。
- 尚无独立 inclusion/exclusion criteria artifacts。

## Legacy capability audit

审计的 legacy 目录：

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project 2`
- `/Users/changdali/Documents/New project`

发现的 legacy 相关能力：

- `model9/literature/screening_service.py`
- `New project 2/app/meta_analysis/legacy/literature/screening_service.py`
- legacy exclusion reason store / tests。

Legacy 能力判断：

- legacy 有 screening exclusion reason registry，适合参考默认排除原因。
- legacy 不包含当前 BioMedPilot 所需的 criteria artifacts、manifest、audit、lineage 接入。

迁移结论：

- 未直接迁移 legacy 代码。
- 参考 legacy exclusion reason 思路，新增当前架构下的 criteria service。

## Capabilities reused

- 复用当前 full-text exclusion reason 范围。
- 复用 `MetaProjectContractService` 写 project manifests。
- 复用 `MetaAuditLogService.record_event(event_type="record_saved")`。
- 复用 `DataCenter.register_asset`。
- 复用 AB1 workflow dashboard 的 Criteria Builder step。

## New files

- `app/meta_analysis/models/criteria.py`
- `app/meta_analysis/services/criteria_service.py`
- `app/meta_analysis/pages/criteria_page.py`
- `tests/meta_analysis/test_stage_ab5_criteria_builder.py`

## Modified files

- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/pages/attachment_page.py`
- `app/meta_analysis/workspace.py`

## New behavior added

新增 criteria artifacts：

- `criteria/inclusion_criteria.json`
- `criteria/exclusion_criteria.json`
- `criteria/criteria_summary.md`

默认 inclusion criteria：

- human studies
- target population
- target disease
- target exposure or intervention
- eligible comparator
- eligible outcome
- eligible study design
- sufficient extractable data
- full text available

默认 exclusion criteria：

- review
- meta-analysis
- conference abstract
- letter / comment / correspondence / editorial
- case report
- animal study
- cell experiment
- duplicate population
- wrong population
- wrong intervention or exposure
- wrong comparator
- wrong outcome
- insufficient data
- full text unavailable

新增 page state：

- `CriteriaPageState`
- `initial_criteria_page_state`
- `criteria_page_state_from_project`

Screening / Full-text 集成：

- `screening_state_with_criteria(...)` 暴露 `criteria_hints` 和 `criteria_summary_path`。
- `attachment_state_from_project(...)` 暴露 full-text stage 的 `criteria_hints` 和 `criteria_summary_path`。

## Data Center / Task Center / audit / manifest / lineage impact

Data Center 新增登记类型：

- `inclusion_criteria`
- `exclusion_criteria`
- `criteria_summary`

Task Center：

- 本阶段未新增 Task Center 类型，避免修改 shared task enum。

Audit log：

- 保存 criteria 时记录 `record_saved`。
- `target_type="criteria_builder"`。

Manifest / lineage：

- `CANONICAL_PROJECT_PATHS` 新增 criteria 三个路径。
- `lineage_manifest.json` 新增 `criteria/criteria_summary.md -> protocol/review_protocol.json`。

Workflow dashboard：

- Criteria Builder step 现在读取 Data Center criteria assets 和 `record_saved` audit count。

## Tests added

新增：

- `tests/meta_analysis/test_stage_ab5_criteria_builder.py`

覆盖：

- 空项目 criteria page state 不崩溃。
- 保存默认 criteria 生成三个 artifacts。
- artifact manifest / Data Center / audit log 登记。
- 缺少 protocol reference 时生成 warning，但仍保存 draft。
- Screening / Full-text page state 能显示 criteria hints。
- Workflow dashboard Criteria Builder step 状态和 Data Center count。

Focused test result：

- `python3 -m compileall -q app/meta_analysis/models/criteria.py app/meta_analysis/services/criteria_service.py app/meta_analysis/pages/criteria_page.py app/meta_analysis/pages/screening_page.py app/meta_analysis/pages/attachment_page.py tests/meta_analysis/test_stage_ab5_criteria_builder.py`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab5_criteria_builder.py tests/meta_analysis/test_stage_ab1_workflow_dashboard.py tests/meta_analysis/test_stage_aa_literature_workspace_ui_diagnostics.py`：14 passed

## Tests run and results

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：361 passed
- `python3 scripts/run_tests.py`：361 passed
- `python3 -m app.main --smoke-test`：通过，输出 `workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`、`pyside6_available=True`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：361 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：361 passed

## Remaining testing limitations

- Criteria 只提供 reviewer hints，不自动修改 screening/full-text decisions。
- PRISMA reason counts 仍以实际 screening/full-text decisions 为准。
- 未实现复杂 criteria 编辑 UI 或 dual reviewer arbitration。

## Next-stage recommendation

进入 Stage AB6：Title / Abstract Screening UX。

建议复用现有 screening queue / decision service，新增逐篇筛选 page state、criteria hints、include/exclude/maybe/needs review、排除原因、多视图过滤和进度摘要。
