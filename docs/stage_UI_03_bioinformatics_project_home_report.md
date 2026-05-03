# UI-03 Bioinformatics Project Home Report

## 本阶段做了什么

- 新增 `BioinformaticsProjectHomeWidget`，作为进入生信分析模块后的第一屏。
- 生信模块现在先进入项目首页，用于创建新项目、打开已有项目、验证项目目录、读取项目摘要并设置当前 project root。
- 新增薄的 `app/bioinformatics/project_workspace.py`，集中处理项目目录、`project_manifest.json`、`project_config.json`、验证和摘要读取。
- 生信工作区接入 UI-04 `数据来源与登记` 页面，项目创建或确认后直接进入该页面，不运行任何数据任务。
- 本次优化 UI-03 为更聚焦的项目建立 / 项目选择入口页，减少说明文字和重复操作。

## 修改了哪些文件

- `app/bioinformatics/project_workspace.py`
- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workspace.py`
- `app/ui_style_tokens.py`
- `tests/bioinformatics/test_project_workspace.py`
- `tests/ui/test_bioinformatics_project_home.py`
- `docs/stage_UI_03_bioinformatics_project_home_report.md`

## 如何复用既有 project workspace contract

- 当前 active 仓库中没有发现 `app/bioinformatics/project_workspace.py`、`app/bioinformatics/project_ui_adapters.py` 或 `docs/bioinformatics_project_workspace_contract.md`。
- 本阶段补齐了一个唯一的生信项目工作区契约层：`app/bioinformatics/project_workspace.py`。
- UI 只调用 `create_bioinformatics_project()`、`open_bioinformatics_project()` 和 summary/validation 对象，不在界面中手写 manifest 逻辑。
- 该契约只负责项目壳、manifest/config 和摘要读取，不接入 TCGA/GEO/GTEx 解析或统计 runner。

## 创建项目和打开项目的 UI 行为

- 创建项目：输入项目名称并选择保存位置后，创建合法项目目录，写入 `project_manifest.json` 和 `project_config.json`，显示项目摘要，并自动进入 UI-04 `数据来源与登记`。
- 打开项目：选择项目文件夹后，验证 `project_manifest.json`，合法则读取摘要并设置为当前项目；点击 `确认并继续` 后自动进入 UI-04 `数据来源与登记`。
- 非法项目：显示中文错误 `该文件夹不是有效的生信分析项目，或缺少 project_manifest.json。`，不崩溃。
- 无项目状态：显示 `尚未打开项目，请创建新项目或选择已有项目文件夹。`
- 返回模块选择首页：触发生信项目首页的返回回调，由主窗口回到 UI-02。

## 本次 UI-03 交互优化

- 精简创建项目说明文字：主页面只保留 1-2 句项目用途说明，避免目录结构和 manifest/config 细节占据主操作区域；详细结构通过 tooltip 保留给需要排查的用户。
- 强化右侧项目验证状态：验证提示改为独立状态卡片，放大验证图标并使用青绿色成功态，让用户更容易确认当前项目是否可用。
- 将 `打开项目` 改为 `确认并继续`：用户选择文件夹后还需要确认使用该项目，按钮语义应表达“确认当前选择并进入下一步”。
- 移除底部 `继续：数据来源选择` 和 `打开项目文件夹`：底部摘要改为只读信息区，不再承担主流程跳转，减少重复点击和次要操作干扰。
- 推荐主流程：创建新项目或确认已有项目成功后，软件自动进入 UI-04 `数据来源与登记`。

## 当前没有实现的边界

- 不实现真实 GEO 下载。
- 不实现 TCGA / GTEx 解析。
- 不运行数据识别。
- 不运行标准化。
- 不运行分析任务。
- 不生成正式报告。

## 测试结果

- 已新增项目工作区契约测试和生信项目首页 UI 测试。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_project_home.py -q`，结果：`8 passed`。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py -q`，结果：`45 passed`。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`，结果：`119 passed`。

## 已知限制和 UI-04 计划

- 最近项目列表仍为占位，后续可接入 Project Center 的生信项目记录。
- UI-04 已作为 `数据来源与登记` 入口，支持 GEO、TCGA、GTEx、本地表达矩阵等来源登记；仍保持不自动下载、不自动解析、不运行分析。
