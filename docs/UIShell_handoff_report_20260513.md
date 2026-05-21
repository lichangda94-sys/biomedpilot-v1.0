# UIShell Handoff Report - 2026-05-13

## 0. Latest Development Judgment

UIShell read-only repair audit completed.

Report:

```text
docs/UIShell_repair_audit_20260513.md
```

Scoped repair commit:

```text
e44e1aa fix(ui-shell): keep shell available when bio workspace is unavailable
```

Validation:

```text
git diff --check: passed
python3 -m app.main --smoke-test: passed
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q: 46 passed, 87 skipped
```

Decision:

```text
UIShell remains NO-BLOCKED.
```

`MainWindow()` P0 instantiation blocker is mitigated, but UIShell is still not eligible for Integration Preview or ReleaseBuild because Bioinformatics workflow page tests are skipped due to missing `app.bioinformatics.deg_executor_preflight`, the branch is still 30 commits behind MainLine, and the branch contains Bioinformatics business content.

Previous untracked file status:

```text
docs/UIShell_handoff_report_20260513.md was left untouched during the scoped repair commit.
```

This section is the latest handoff/development judgment and supersedes older failure-status statements below that were captured before commit `e44e1aa`.

## 1. Branch / Worktree Summary

当前 worktree：

```text
/Users/changdali/Developer/biomedpilot v1.0/UIShell
```

当前分支：

```text
dev/ui-shell
```

当前 HEAD：

```text
391c882 docs: add workspace codex guide
```

开始审计时 `git status --short` 输出为空，说明本报告生成前 `dev/ui-shell` 工作树 clean。生成本报告后，未提交改动仅应为：

```text
?? docs/UIShell_handoff_report_20260513.md
```

实际执行过的分支检查命令：

```bash
pwd
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -5
```

结果摘要：

- `pwd`：`/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- `git branch --show-current`：`dev/ui-shell`
- `git rev-parse --short HEAD`：`391c882`
- 最近 5 个提交：
  - `391c882 docs: add workspace codex guide`
  - `67e5b13 fix(bioinformatics): enrich geo dataset details`
  - `16372fd docs(bioinformatics): audit deg executor readiness`
  - `d7bfc61 Update standardization page UI assertion`
  - `ffa24ff feat(bioinformatics): assemble project report draft`

相对 `stable/mainline` 的分叉状态：

```text
merge-base: 67e5b13
HEAD...stable/mainline: 1 29
```

结论：`dev/ui-shell` 当前只比共同基线多 1 个提交，但落后 `stable/mainline` 29 个提交。存在明显分叉，尤其 MainLine 后续已经包含多个 UI Governance、shared UI helper、Meta / LabTools 接入规范和桌面入口修复相关提交；本分支不应直接作为打包或稳定主线来源。

当前分支职责边界来自 `CODEX.md`：

- UIShell 负责桌面壳层和 UI 统一，包括登录页、主窗口、模块选择、侧边栏、顶部状态栏、设置页、主题色、按钮语义样式、开发者诊断折叠区。
- 禁止修改 Bioinformatics 分析业务逻辑、Meta 文献业务逻辑、词库数据资产。
- 禁止为了 UI 美化破坏测试。

## 2. Current Functional Scope

本分支是统一桌面壳和 UI 集成分支，不是稳定发布分支。当前功能范围需要按“可运行 / 测试级 / 占位 / 文档”区分。

已实现并可运行的功能：

- `python3 -m app.main --smoke-test` 可运行并输出应用摘要。
- `app/main.py` 支持 `--smoke-test`，不进入 GUI event loop，输出版本、工作区数、Bioinformatics / Meta feature 数量和 PySide6 状态。
- `app/shell/login.py` 实现本地测试登录页，用户名和密码非空即可进入 session；密码不写入 session。
- `app/shell/module_selection.py` 实现统一模块选择页，展示 Bioinformatics 和 Meta 两个入口卡片、当前用户、版本、Developer Preview / 本地测试版标记。
- `app/shell/sidebar.py`、`app/shell/status_panel.py`、`app/shell/topbar.py`、`app/shell/main_window.py` 构成桌面壳层、侧边栏、设置中心和测试模式入口。
- `app/ui_style_tokens.py` 和 `app/ui_theme.py` 提供当前分支的 UI 颜色、间距和 light theme 基础。

已接入 UI 但属于测试级 / draft 的功能：

- Bioinformatics 工作区在本分支代码中包含项目首页、数据来源、中文 GEO 检索、数据识别、Ready 检查、标准化资产、分组比较设计、工作流状态、分析任务中心、结果浏览、报告草稿、设置与本地 AI 检索助手等页面。
- 这些页面主要位于 `app/bioinformatics/workspace.py` 和 `app/bioinformatics/workflow_pages.py`，配套薄服务层位于 `app/bioinformatics/project_*.py`、`app/bioinformatics/results/`、`app/bioinformatics/reports/`。
- 当前 Bioinformatics 多数能力应描述为 Developer Preview / testing / preflight / dry-run / draft。不得写成正式生信分析能力。
- Meta 在 `app/meta_analysis/workspace.py` 中只保留 mainline shell contract、项目壳和最小入口说明；完整 Meta workflow 不在本 UIShell 分支内完成。

只有后端或服务层、UI 不完整或不应视为正式流程的功能：

- `app/bioinformatics/project_recognition.py`、`project_readiness.py`、`project_standardization.py`、`project_analysis_tasks.py`、`analysis_task_runs.py`、`results/project_results.py`、`reports/project_report_builder.py` 等可写入多类 JSON/Markdown artifact，但其中很多输出是测试级 preflight、registry、dry-run 或 draft。
- `app/bioinformatics/deg_task_plan.py` 能保存 DEG task plan；`analysis_task_runs.py` 能创建 dry-run task run。当前不执行真实 DEG 统计，不生成正式 DEG 表、火山图或富集结果。

仅有设计、文档或预留接口的功能：

- 订阅/VIP/license/account system 均为 UI 占位。
- 设置中心多个项目为占位展示，不是完整配置系统。
- Packaging 文档存在，`scripts/package_app.py` 可创建本地 macOS `.app` launcher，但本分支不是当前推荐打包来源。
- LabTools 不属于本 UIShell 分支的实现范围；当前工作树没有 `app/labtools/`。

当前关键运行风险：

- `tests/ui` 证明 `MainWindow()` 当前不能正常实例化。原因是 `app.bioinformatics.workflow_pages` 导入时缺少 `app.bioinformatics.deg_executor_preflight`，导致 `app/bioinformatics/workspace.py` 走 fallback class；随后 `MainWindow` 调用 `BioinformaticsWorkspaceWidget(on_back=...)` 触发 `TypeError: BioinformaticsWorkspaceWidget() takes no arguments`。
- `--smoke-test` 不实例化 `MainWindow`，所以 smoke 通过不能证明桌面 GUI 当前可打开。

## 3. Completed Work Since Last Handoff

本分支没有发现单一最新 handoff 文件；以下按当前 HEAD 最近提交和已存在阶段报告整理。

- 完成：UIShell workspace guide
  - 涉及文件：`CODEX.md`
  - 行为变化：为 `dev/ui-shell` 写明工作区职责、禁止事项和测试入口。
  - UI 变化：无。
  - 数据/manifest：无。
  - 测试：未在该提交信息中记录测试；本次审计重新运行 smoke 和 UI tests，见第 7 节。

- 完成：GEO dataset detail enrichment
  - 涉及文件：`app/bioinformatics/retrieval/geo_detail_enrichment.py`、`app/bioinformatics/download/geo_text_summary_service.py`、`app/bioinformatics/services/organism_display.py`、`app/bioinformatics/workflow_pages.py`、`tests/bioinformatics/test_geo_detail_enrichment.py`、`tests/ui/test_bioinformatics_workflow_pages.py`、`docs/bioinformatics_geo_detail_enrichment_v1.md`
  - 行为变化：增强 GEO dataset detail 展示和 organism display；属于当前 UIShell 分支中的 Bioinformatics UI/服务集成内容。
  - UI 变化：`workflow_pages.py` 中 GEO 详情展示相关区域被扩展。
  - 数据/manifest：未发现新增稳定 project manifest；主要是页面和检索详情 enrichment。
  - 测试：新增 bioinformatics 和 UI 测试文件覆盖；本次 `tests/ui` 仍因 MainWindow 构造失败未通过。

- 完成：DEG executor readiness audit
  - 涉及文件：`docs/bioinformatics_deg_executor_readiness_audit.md`
  - 行为变化：文档审计；不接入真实 DEG executor。
  - UI 变化：无。
  - 数据/manifest：无。
  - 测试：文档提交无测试记录。

- 完成：standardization page UI assertion update
  - 涉及文件：`tests/ui/test_bioinformatics_workflow_pages.py`
  - 行为变化：调整标准化页面 UI 断言。
  - UI 变化：无代码 UI 变化。
  - 数据/manifest：无。
  - 测试：该提交只改测试断言；当前全量 UI tests 未通过，失败点不在标准化断言本身。

- 完成：Bioinformatics project report draft assembly
  - 涉及文件：`app/bioinformatics/reports/project_report_builder.py`、`app/bioinformatics/workflow_pages.py`、`tests/bioinformatics/test_result_report_manifest.py`、`tests/ui/test_bioinformatics_workflow_pages.py`、`docs/bioinformatics_project_report_draft_v1.md`
  - 行为变化：生成项目级 Markdown 报告草稿和 `reports/project_report_manifest.json`，汇总 acquisition、recognition、readiness、standardization、result index、task records 等信息。
  - UI 变化：报告查看页可生成/读取报告草稿。
  - 数据/manifest：新增或扩展 `reports/project_analysis_report.md`、`reports/project_report_draft.md`、`reports/project_report_manifest.json`、`logs/reports/project_report_builder_report.json`。
  - 测试：对应 manifest 测试和 UI 测试已存在；当前 UI 总套件因 MainWindow 构造问题失败。

已存在的 UI 阶段报告显示 UI-01 至 UI-13 曾逐步实现：

- UI-01：登录页。
- UI-02：模块选择页。
- UI-03：Bioinformatics 项目首页。
- UI-04：数据来源与登记。
- UI-05：数据获取状态页，后续普通流程中并入 UI-04。
- UI-06：数据识别页。
- UI-07：Ready 数据准备状态页。
- UI-08：标准化资产页。
- UI-09：工作流总控页。
- UI-10：分析任务中心。
- UI-11：结果浏览页。
- UI-12：报告查看页。
- UI-13：设置与本地 AI 检索助手页。

这些阶段报告是当前分支内事实记录，但部分测试结果是历史快照，不代表当前 HEAD 已全部通过。

## 4. Important Files and Entry Points

主要启动和运行入口：

- `app/main.py`：应用入口；`--smoke-test` 输出启动摘要，不进入 GUI event loop。
- `scripts/run_app.py`：从仓库根目录注入 `sys.path` 后调用 `app.main.main()`。
- `scripts/run_tests.py`：设置 `QT_QPA_PLATFORM=offscreen` 后运行 `python -m pytest -q`。
- `scripts/package_app.py`：创建本地 macOS `.app` launcher，复制 `app`、`assets`、`config`、`docs`、`examples`、`reporting`、`scripts` 等目录；不是完全独立安装器。

主要 Shell / UI 文件：

- `app/shell/main_window.py`：主窗口、登录页和 shell stack 组装处；当前 `MainWindow()` 测试失败的直接触发点。
- `app/shell/login.py`：本地测试登录页和 `LocalSession`。
- `app/shell/module_selection.py`：登录后的 Bioinformatics / Meta 模块入口页。
- `app/shell/sidebar.py`：侧边栏导航。
- `app/shell/status_panel.py`：状态面板。
- `app/shell/dashboard.py`：dashboard model 和模块 feature 摘要。
- `app/ui_style_tokens.py`、`app/ui_theme.py`：当前分支 UI token / theme 入口。
- `app/app_identity.py`：app name、icon asset loading 和身份展示。

主要 Bioinformatics UI / workflow 文件：

- `app/bioinformatics/workspace.py`：Bioinformatics workspace stack；正常导入时支持 `on_back`，但当前因 `workflow_pages` 缺失依赖触发 fallback。
- `app/bioinformatics/project_home.py`：Bioinformatics 项目首页。
- `app/bioinformatics/workflow_pages.py`：Bioinformatics 多页面 UI 的集中实现，包含数据来源、中文检索、识别、Ready、标准化、分组、任务中心、结果、报告、设置/本地 AI 页面。

主要 service / workflow 文件：

- `app/bioinformatics/project_workspace.py`：创建/打开/验证 Bioinformatics project，写入 `project_manifest.json` 和 `project_config.json`。
- `app/bioinformatics/project_workspace_binding.py`：acquisition plan / record / handoff 写入和读取。
- `app/bioinformatics/project_recognition.py`：数据识别报告与识别 run 管理。
- `app/bioinformatics/project_readiness.py`：Ready report 和 analysis capability matrix。
- `app/bioinformatics/project_standardization.py`：standardized assets registry、analysis-ready manifest 和 processing plan。
- `app/bioinformatics/group_comparison_design.py`：分组与比较设计。
- `app/bioinformatics/deg_task_plan.py`：DEG task plan 配置保存，非真实 DEG 执行。
- `app/bioinformatics/analysis_task_runs.py`：analysis run manifest / dry-run task record。
- `app/bioinformatics/project_analysis_tasks.py`：analysis task center。
- `app/bioinformatics/results/project_results.py`：result manager 和 result index。
- `app/bioinformatics/reports/project_report_builder.py`：项目报告草稿和 report manifest。
- `app/meta_analysis/workspace.py`：Meta 最小 shell contract / 项目壳。

主要 schema / manifest / artifact 文件：

- 项目根目录下运行时生成：`project_manifest.json`、`project_config.json`。
- 数据来源：`acquisition/plans/latest_acquisition_plan.json`、`acquisition/records/latest_acquisition_record.json`、`acquisition/handoffs/latest_acquisition_handoff.json`。
- 识别：`recognized_data/current.json`、`recognized_data/runs/*/recognition_report.json`、`recognized_data/runs/*/input_manifest.json`。
- Ready：`logs/readiness/readiness_report.json`、`manifests/analysis_capability_matrix.json`。
- 标准化：`manifests/standardized_assets_registry.json`、`standardized_data/analysis_ready_assets/analysis_ready_manifest.json`、`manifests/data_processing_task_plan.json`。
- 分组：`manifests/group_comparison_design.json`。
- 分析任务：`manifests/analysis_task_center.json`、`analysis/task_records/*.json`、`manifests/analysis_tasks/deg_task_plan.json`、`analysis_runs/deg/*/task_run.json`。
- 结果：`manifests/result_manager.json`、`results/summaries/result_index.json`。
- 报告：`reports/project_analysis_report.md`、`reports/project_report_draft.md`、`reports/project_report_manifest.json`、`logs/reports/project_report_builder_report.json`。

主要测试文件：

- `tests/ui/test_login_page.py`
- `tests/ui/test_module_selection.py`
- `tests/ui/test_app_identity.py`
- `tests/ui/test_sidebar.py`
- `tests/ui/test_app_theme.py`
- `tests/ui/test_bioinformatics_project_home.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/bioinformatics/test_project_workspace.py`
- `tests/bioinformatics/test_deg_task_plan.py`
- `tests/bioinformatics/test_analysis_task_runs.py`
- `tests/bioinformatics/test_result_report_manifest.py`

当前报告和阶段报告：

- `docs/UIShell_handoff_report_20260513.md`：本报告。
- `docs/stage_UI_01_login_page_report.md` 至 `docs/stage_UI_13_bioinformatics_settings_local_ai_report.md`：历史 UI 阶段报告。
- `docs/bioinformatics_project_report_draft_v1.md`
- `docs/bioinformatics_geo_detail_enrichment_v1.md`
- `docs/bioinformatics_deg_executor_readiness_audit.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`

## 5. Runtime / User Flow

当前设计用户流程：

```text
启动 app.main
-> 登录页
-> 模块选择页
-> 生信分析模块 / Meta 分析模块
```

Bioinformatics 页面设计流程：

```text
项目首页
-> 数据来源与登记
-> 数据识别
-> Ready 检查
-> 标准化资产
-> 分组与比较设计
-> 工作流总控
-> 分析任务中心
-> 结果浏览
-> 报告草稿
```

实际断点：

- `--smoke-test` 流程可运行。
- 当前 HEAD 下 `MainWindow()` 不能正常实例化，`tests/ui` 失败，原因是 `app.bioinformatics.workflow_pages` 导入缺失 `app.bioinformatics.deg_executor_preflight` 后触发 fallback workspace class。
- 因此，当前桌面 GUI 的真实点击流程不能被视为可闭环。

Meta 当前流程：

```text
模块选择页
-> Meta 分析模块最小入口 / 项目壳
```

Meta 仅是 mainline shell contract / placeholder 级别。完整 PICO、检索、筛选、提取、统计和报告流程不应从本 UIShell 分支判断。

## 6. Data Contracts / Manifest Contracts

以下契约均为当前 UIShell worktree 内代码读取或写入的实际 artifact。状态按当前代码语义判断。

| Contract | 文件位置 | 生成者 | 读取者 | 状态 | 是否建议后续模块依赖 |
| --- | --- | --- | --- | --- | --- |
| Bioinformatics project manifest | `project_manifest.json` | `create_bioinformatics_project()` | `validate_bioinformatics_project()`、项目首页 | testing / project shell | 可依赖基本项目壳字段，但进入 MainLine 前需按最新 MainLine contract 复核 |
| Bioinformatics project config | `project_config.json` | `create_bioinformatics_project()` | 项目首页和后续页面 | testing | 可依赖基础字段；不要扩展为业务结论 |
| Acquisition plan | `acquisition/plans/latest_acquisition_plan.json` 和 `acq-*.json` | `register_acquisition()` / `generate_gse_acquisition_plan()` | UI-04 / UI-05 / 后续识别 | testing plan | 可作为登记/计划输入；不能表示下载已完成 |
| Acquisition record | `acquisition/records/latest_acquisition_record.json` | `register_acquisition()` | acquisition summary / report builder | testing | 可依赖登记状态；不代表数据质量 |
| Acquisition handoff | `acquisition/handoffs/latest_acquisition_handoff.json` | `register_acquisition()` | 后续识别建议 | testing handoff | 可依赖 next stage 提示；不要当作执行完成证明 |
| Recognition current pointer | `recognized_data/current.json` | `run_project_recognition*()` | `load_recognition_report()`、standardization、report builder | testing | 可依赖当前识别 run 指针；schema 仍可能变动 |
| Recognition report | `recognized_data/runs/*/recognition_report.json` | `project_recognition.py` | Ready、standardization、report builder、UI | testing | 可依赖识别摘要；不能当作数据质量或科研可信度评分 |
| Readiness report | `logs/readiness/readiness_report.json` | `run_project_readiness()` | task center、report builder、UI | testing preflight | 可依赖 preflight 状态；不能当作真实分析结果 |
| Capability matrix | `manifests/analysis_capability_matrix.json` | `run_project_readiness()` | task center、UI | testing preflight | 可依赖分析可运行性提示；不代表 runner 已接入 |
| Standardized assets registry | `manifests/standardized_assets_registry.json` | `generate_standardized_assets()` | asset selection、task center、report builder | testing registry | 可依赖资产登记；不等于正式 biological normalization |
| Analysis-ready manifest | `standardized_data/analysis_ready_assets/analysis_ready_manifest.json` | `generate_standardized_assets()` | UI / report builder | testing | 可依赖资产存在性；不要写成正式分析就绪 |
| Data processing task plan | `manifests/data_processing_task_plan.json` | `generate_standardized_assets()` | UI / 后续规划 | draft plan | 不建议作为稳定外部依赖 |
| Group comparison design | `manifests/group_comparison_design.json` | `group_comparison_design.py` / UI | Ready、DEG task plan、task center | testing / user-confirmed config | 可依赖 confirmed 字段，但需人工确认来源 |
| Analysis task center | `manifests/analysis_task_center.json` | `load_analysis_task_center()` | task center UI、report builder | testing | 可依赖任务摘要；不代表真实任务执行 |
| DEG task plan | `manifests/analysis_tasks/deg_task_plan.json` | `save_deg_task_plan()` | `analysis_task_runs.py`、task center | configured_not_run / draft | 只可作为配置，不可作为 DEG 结果 |
| Analysis task run | `analysis_runs/deg/*/task_run.json` | `create_deg_task_run()` | result index、report builder | dry-run / configured_not_run | 不可作为真实分析完成证明 |
| Result manager | `manifests/result_manager.json` | `load_result_index()` / `write_result_index()` | result browser | testing | 可依赖索引计数；需检查文件存在 |
| Result index | `results/summaries/result_index.json` | `load_result_index()` / `write_result_index()` | result browser、report builder | testing | 可依赖 result item 列表；不要伪造图表/统计 |
| Project report Markdown | `reports/project_analysis_report.md` | `generate_project_report()` | report viewer | draft / testing | 只可作为测试报告草稿 |
| Project report manifest | `reports/project_report_manifest.json` | `generate_project_report()` | report viewer / downstream audit | draft / testing | 可用于追溯 draft 来源；不可当作正式报告 |
| Builder report | `logs/reports/project_report_builder_report.json` | `generate_project_report()` | diagnostics | testing log | 诊断用途 |
| Meta project manifest | `meta_project_manifest.json` | `app/meta_analysis/project_workspace.py` | Meta minimal workspace | shell contract / placeholder | 本 UIShell 分支不应扩展完整 Meta 业务依赖 |

## 7. Tests and Validation

本次报告生成前实际运行：

```bash
git diff --check
```

结果：通过，无输出。

```bash
python3 -m app.main --smoke-test
```

结果：通过。

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/UIShell
git_head=391c882
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=9
pyside6_available=True
```

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：失败。

```text
6 failed, 40 passed, 87 skipped in 2.17s
```

失败测试：

- `tests/ui/test_app_identity.py::test_main_window_uses_app_icon`
- `tests/ui/test_login_page.py::test_main_window_starts_at_login_and_enters_dashboard`
- `tests/ui/test_login_page.py::test_settings_page_displays_icon_asset_details`
- `tests/ui/test_module_selection.py::test_main_window_logout_returns_to_login_and_clears_session`
- `tests/ui/test_module_selection.py::test_main_window_module_buttons_enter_existing_workspaces`
- `tests/ui/test_module_selection.py::test_main_window_open_meta_project_binds_workspace_project_dir`

共同失败原因：

```text
TypeError: BioinformaticsWorkspaceWidget() takes no arguments
```

进一步导入检查：

```bash
python3 - <<'PY'
import importlib
for m in ['app.bioinformatics.workflow_pages','app.bioinformatics.project_home','app.bioinformatics.workspace']:
    try:
        mod = importlib.import_module(m)
        print(m, 'OK', getattr(mod, 'BioinformaticsWorkspaceWidget', None))
    except Exception as exc:
        print(m, 'FAIL', type(exc).__name__, exc)
PY
```

结果关键行：

```text
app.bioinformatics.workflow_pages FAIL ModuleNotFoundError No module named 'app.bioinformatics.deg_executor_preflight'
app.bioinformatics.project_home OK None
app.bioinformatics.workspace OK <class 'app.bioinformatics.workspace.BioinformaticsWorkspaceWidget'>
```

解释：`app/bioinformatics/workspace.py` 的 GUI imports 被 broad `except Exception` 捕获后降级为 fallback `BioinformaticsWorkspaceWidget: pass`。`MainWindow` 仍按正常类调用 `BioinformaticsWorkspaceWidget(on_back=...)`，因此触发 TypeError。当前不修复，只记录。

未运行的测试：

- 未运行 `python3 scripts/run_tests.py`，因为 `tests/ui` 已失败，继续跑全量只会扩大失败面且不属于本报告任务修复范围。
- 未运行 `tests/bioinformatics`，因为本任务是 UIShell handoff 文档生成，不修改 Bioinformatics 业务代码；但当前 UIShell 分支确实包含大量 Bioinformatics UI/service 代码，进入集成前需要补跑。
- 未运行 packaging，因为本分支不是当前推荐打包来源，且 GUI 主窗口测试已失败。

## 8. Known Issues / Risks

1. `tests/ui` 当前失败，桌面 `MainWindow()` 不能实例化。
   - 具体原因：缺少 `app.bioinformatics.deg_executor_preflight` 导致 `workflow_pages` 导入失败，`workspace.py` 降级为 fallback class，随后 `on_back` 参数不兼容。
   - 影响：登录、模块选择、settings、Meta project binding 等依赖 `MainWindow()` 的 UI 测试全部失败。

2. `--smoke-test` 通过不代表 GUI 可用。
   - smoke test 不创建 `MainWindow`，只能说明版本、feature registry 和环境摘要能加载。

3. 分支与 `stable/mainline` 明显分叉。
   - `dev/ui-shell` 相对 `stable/mainline` ahead 1、behind 29。
   - MainLine 已包含后续 UI Governance、shared UI helper、Meta/LabTools 规范、active runtime 等提交；直接从 UIShell 打包或合入存在过期风险。

4. 当前分支名是 UIShell，但历史提交和实际文件包含大量 Bioinformatics UI / service 工作。
   - 这不代表 Bioinformatics 独立 worktree 的当前状态。
   - 后续合入前需要明确哪些 Bioinformatics 文件属于 UIShell 集成成果，哪些应由 Bioinformatics worktree 接管。

5. 多数 Bioinformatics 功能仍是 testing / preflight / draft。
   - DEG task plan、task run、report builder、readiness、standardization registry 不应被描述为正式分析、正式统计或投稿级报告。

6. `app/bioinformatics/workspace.py` 使用 broad import fallback。
   - 这让真实 import 错误变成运行时 TypeError，降低诊断清晰度。
   - 该问题本报告不修复，但应列为下一阶段 immediate blocker。

7. 当前 UI 技术字段暴露治理不完整。
   - 本分支早于 MainLine 后续 UI Governance 阶段，仍可能在主界面暴露 raw path、manifest、internal status、developer wording。

8. Packaging 风险。
   - `scripts/package_app.py` 存在，但当前 GUI 主窗口测试失败，不应从本分支生成桌面测试包。

9. 跨模块污染风险。
   - UIShell 分支应只做 shell / UI 统一，但当前实际包含 Bioinformatics 服务层、report builder、retrieval enrichment 等工作。
   - 后续开发者不得继续在 UIShell 中扩展 Bioinformatics 业务逻辑。

## 9. Do Not Touch / Boundary Rules

- 不要修改其他 worktree：`MainLine`、`Bioinformatics`、`Meta`、`Vocabulary`、`LabTools`、`AI`、`Integration`、`ReleaseBuild`。
- 不要在 UIShell 分支中继续开发 Bioinformatics 真实分析逻辑。
- 不要把 Bioinformatics 的 preflight、dry-run、draft report 写成正式分析结果。
- 不要让 Bioinformatics 调 PubMed 或承担 Meta 文献检索。
- 不要让 Meta 混入 GEO / TCGA / GTEx 表达数据分析逻辑。
- 不要绕过 AI Gateway，不要保存 raw prompt / raw response。
- 不要默认联网、默认下载 GEO / PubMed / PDF / full text。
- 不要删除 `app/bioinformatics/legacy/`、`app/meta_analysis/legacy/`、`docs/` 阶段报告、测试文件或 packaging 文件。
- 不要覆盖 `/Users/changdali/Desktop/BioMedPilot.app` 或 `dist/BioMedPilot.app`。
- 不要从当前 `dev/ui-shell` 直接打包发布；当前 GUI 主窗口测试未通过。
- 不要执行 `git push`，除非人工明确授权并确认凭据边界。
- 不要自动回退、reset、stash 或合并分支。

## 10. Recommended Next Tasks

### Immediate Next Step

1. 修复 UIShell 当前 GUI blocker。
   - 目标：让 `MainWindow()` 能实例化，恢复 `tests/ui`。
   - 起点：`app.bioinformatics.workflow_pages` 缺少 `app.bioinformatics.deg_executor_preflight`。
   - 建议先审计 MainLine 或 Bioinformatics worktree 是否已有对应文件或替代实现，再决定在 UIShell 中补兼容 shim、同步缺失文件，还是回退调用点。

2. 复跑 UIShell 最小验证。
   - `python3 -m app.main --smoke-test`
   - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
   - `git diff --check`

3. 审计 UIShell 分支与 `stable/mainline` 的差异。
   - 目标：确认 `dev/ui-shell` 唯一 ahead commit `391c882` 是否仍需保留，以及 MainLine 后续 29 个提交是否已覆盖更完整的 UI governance。

### Before Integration

1. 明确 UIShell 与 Bioinformatics 文件归属。
   - 对 `app/bioinformatics/workflow_pages.py`、`project_*.py`、`results/`、`reports/`、`tests/bioinformatics/` 做文件级归属清单。
   - 不要把业务服务层作为 UIShell 视觉任务继续扩张。

2. 与 MainLine UI Governance 对齐。
   - 对照 MainLine 后续 UI Stage 0.1-0.8 文档，检查当前分支是否仍使用旧 token、旧按钮层级、技术字段主界面暴露或独立主题。

3. 完成测试矩阵。
   - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
   - `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`，如果继续保留 Bioinformatics service/UI 改动。
   - `python3 -m app.main --smoke-test`
   - `python3 -m compileall -q app tests scripts`

4. 若要进入 MainLine，先经 Integration 或等效集成验证。
   - 不要直接把 `dev/ui-shell` 当前状态打包或发布。

### Later / Optional

1. 拆分 `app/bioinformatics/workflow_pages.py`。
   - 该文件承载过多页面，后续可按页面或阶段拆分，但应在测试恢复后进行。

2. 抽取共享 Developer Diagnostics / 技术详情组件。
   - 减少各页面手写折叠区和技术字段展示。

3. 更新 user testing 文档。
   - 在 GUI blocker 修复后，重新生成 `docs/user_testing/feature_availability.md` 和 `known_limitations.md`，确保不夸大功能。

4. Packaging 验证。
   - 仅在 GUI tests 恢复、MainLine/Integration 验证通过后，再运行 `scripts/package_app.py --smoke-test`。

## 11. Suggested Codex Instruction for Next Stage

请在 `/Users/changdali/Developer/biomedpilot v1.0/UIShell` 的 `dev/ui-shell` 分支执行下一阶段 UIShell blocker 修复与验证。

目标：

- 修复当前 `MainWindow()` 无法实例化的问题。
- 让 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` 至少恢复到通过或明确只剩无关 skip。
- 保持 UIShell 分支职责为桌面壳层和 UI 统一，不扩展 Bioinformatics 真实业务逻辑。

开始前必须阅读：

- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `CODEX.md`
- `docs/UIShell_handoff_report_20260513.md`
- `docs/stage_UI_01_login_page_report.md` 至 `docs/stage_UI_13_bioinformatics_settings_local_ai_report.md`

开始前必须执行并记录：

```bash
pwd
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -5
```

允许修改范围：

- `app/shell/*`
- `app/bioinformatics/workspace.py`
- `app/bioinformatics/workflow_pages.py`
- 仅为修复缺失 import / 兼容当前 UI 测试所必需的最小 Bioinformatics UI adapter 文件
- `tests/ui/*`
- 必要的阶段报告或 handoff 文档

禁止事项：

- 不要修改其他 worktree。
- 不要执行 `git push`。
- 不要引入真实 Bioinformatics 分析执行器。
- 不要接入外部网络、GEO 下载、PubMed 检索、AI 调用或外部模型。
- 不要删除 legacy、测试、docs、packaging 文件。
- 不要把 dry-run、preflight、testing-level、draft report 写成正式结果。
- 不要从本分支创建或覆盖桌面 app。

建议修复路径：

1. 定位 `app.bioinformatics.workflow_pages` 对 `app.bioinformatics.deg_executor_preflight` 的导入来源。
2. 检查 MainLine / Bioinformatics worktree 是否已有对应实现，必要时只同步最小兼容层。
3. 避免 broad fallback 掩盖真实导入错误；如调整 fallback，必须保持非 GUI 环境可导入 feature registry。
4. 恢复 `MainWindow()` 实例化并保留 `BioinformaticsWorkspaceWidget(on_back=...)` 行为。

必须运行测试：

```bash
git diff --check
python3 -m app.main --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

如果修改了 Bioinformatics service 或 adapter，额外运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
```

报告要求：

- 新增或更新阶段报告，说明修复文件、行为变化、测试结果、未解决风险和是否未 push。
- 如果测试失败，记录失败命令、失败测试名、关键错误，不要写“应该通过”。

停止条件：

- 需要修改其他 worktree。
- 需要引入真实 DEG / enrichment / correlation / survival executor。
- 需要联网、下载、AI 调用或凭据。
- 需要删除或回退用户未授权文件。
- 测试失败且修复方向不唯一。
