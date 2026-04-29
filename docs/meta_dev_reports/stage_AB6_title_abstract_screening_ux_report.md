# Stage AB6: Title / Abstract Screening UX

## 本阶段目标

增强现有 title/abstract screening 的 testing / Developer Preview page state，让 reviewer 能逐篇查看标题、摘要、作者、期刊、年份、DOI/PMID 链接、criteria hints、决策进度和筛选导出文件。本阶段不删除文献，不改变旧 screening decision 数据格式。

## Continuity audit

正式项目根目录：

- `/Users/changdali/Documents/BioMedPilot`

当前 git 状态审计：

- 分支：`codex/biomedpilot-root`
- 基线 HEAD：`d9a14e1 feat(meta): add criteria builder`
- 未跟踪：`test_inputs/`，本阶段未触碰、未提交

审计的正式项目模块：

- `app/meta_analysis/services/screening_service.py`
- `app/meta_analysis/adapters/screening_adapter.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/services/criteria_service.py`
- `tests/meta_analysis/test_screening_service.py`
- `tests/meta_analysis/test_stage_ab5_criteria_builder.py`

正式项目已有相关能力：

- `ScreeningService.create_queue()` 已能从 Prepare Screening 或 Duplicate Review 输出生成 title/abstract queue。
- `ScreeningService.update_decision()` 已支持 `pending`、`included`、`excluded`、`maybe`。
- `excluded` 决策要求填写排除原因。
- AB5 已提供 criteria hints。

## Legacy capability audit

审计的 legacy 目录：

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project 2`
- `/Users/changdali/Documents/New project`

发现的 legacy 相关能力：

- `model9/app_meta/ui/screening_page.py`
- `New project 2/app/meta_analysis/legacy/app_meta/ui/screening_page.py`

Legacy 能力判断：

- legacy UI 已有逐篇显示、进度摘要和排除原因提示，但基于 demo records，不接入当前 BioMedPilot service / artifacts。

迁移结论：

- 未直接迁移 legacy UI。
- 参考 legacy 的上一条/下一条、进度和排除原因交互方式，新增当前架构下的 page-state。

## Capabilities reused

- 复用 `ScreeningService` 的 queue 和 decision 保存格式。
- 复用 AB5 `CriteriaBuilderService.criteria_hints()`。
- 复用现有 audit / Data Center / Task Center 行为，不新增 decision service。

## Modified files

- `app/meta_analysis/pages/screening_page.py`

## New files

- `tests/meta_analysis/test_stage_ab6_title_abstract_screening_ux.py`
- `docs/meta_dev_reports/stage_AB6_title_abstract_screening_ux_report.md`

## New behavior added

新增 page-state structures：

- `TitleAbstractScreeningRecordView`
- `TitleAbstractScreeningUXState`

新增 functions：

- `title_abstract_screening_state_from_queue(...)`
- `export_title_abstract_screening_artifacts(...)`

UX 状态支持：

- 当前记录、上一条、下一条。
- title、abstract、authors、journal、year、DOI、PMID。
- DOI / PubMed source links。
- decision options：`included`、`excluded`、`maybe`、`needs_review`、`pending`。
- exclusion reason options，优先来自 criteria hints。
- progress summary：total、pending、included、excluded、maybe、needs_review、screened。
- filter views：all、pending、included、excluded、maybe、needs_review。
- 缺 queue 或空 queue 时返回 warning，不崩溃。

输出：

- `screening/title_abstract_decisions.json`
- `screening/title_abstract_decisions.csv`
- `screening/screening_summary.json`

兼容说明：

- `needs_review` 是 UI 视图标签；当前保存服务仍使用 `pending/included/excluded/maybe`，避免破坏旧项目和旧测试。

## Data Center / Task Center / audit / manifest / lineage impact

- 本阶段不新增 Task Center 类型。
- 本阶段不新增 audit event 类型。
- 核心 decision 保存仍由 `ScreeningService.update_decision()` 负责 Data Center / Task Center / audit log。
- 新增导出函数只把当前 queue 摘要写到 project_dir/screening，供后续 AB 阶段继续接入。

## Tests added

新增：

- `tests/meta_analysis/test_stage_ab6_title_abstract_screening_ux.py`

覆盖：

- 逐篇加载当前记录、进度、上一条/下一条。
- DOI / PMID source links。
- criteria hints 和 exclusion reason options。
- 缺 queue 不崩溃。
- 导出 title_abstract_decisions JSON / CSV 和 screening_summary JSON。
- current_index 越界时安全落到最后一条。

Focused test result：

- `python3 -m compileall -q app/meta_analysis/pages/screening_page.py tests/meta_analysis/test_stage_ab6_title_abstract_screening_ux.py`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab6_title_abstract_screening_ux.py tests/meta_analysis/test_screening_service.py tests/meta_analysis/test_stage_ab5_criteria_builder.py`：19 passed

## Tests run and results

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：366 passed
- `python3 scripts/run_tests.py`：366 passed
- `python3 -m app.main --smoke-test`：通过，输出 `workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`、`pyside6_available=True`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：366 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：366 passed

## Remaining testing limitations

- 当前 PySide 页面还不是完整逐篇筛选工作台，主要是 page-state / service-level UX 加固。
- `needs_review` 不写入旧 service decision 字段。
- 不做双 reviewer 冲突仲裁。
- 不自动删除文献。

## Next-stage recommendation

进入 Stage AB7：Full-text Eligibility Screening。

建议复用现有 fulltext/attachment service，生成全文候选清单、fulltext eligibility decisions、fulltext exclusion report 和 final included studies。
