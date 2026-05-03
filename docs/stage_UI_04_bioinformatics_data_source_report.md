# UI-04 生信数据来源与登记页报告

## 本阶段做了什么

- 将 UI-04 正式命名为 `数据来源与登记 / Data Source & Registration`。
- 将普通用户入口简化为三个主模块：`本地数据导入`、`GSE 编号检索`、`中文研究主题检索`。
- 原 UI-05 数据获取状态不再作为普通流程的独立下一页；登记状态合并到 UI-04 的 `当前数据来源登记状态` 和默认折叠的 `展开技术详情`。
- 普通流程调整为：项目首页 → 数据来源与登记 → 数据识别 → Ready 检查 → 标准化 → 分析任务中心 → 结果与报告。

## 为什么简化为三个入口

- GEO Series Matrix、TCGA、GTEx、TCGA + GTEx 都是“用户已有本地数据”的不同类型，不应拆成多个同级入口。
- 普通用户的真实决策只有三类：我已有数据、我知道 GSE 编号、我只有中文研究主题。
- 页面现在用推断类型展示本地数据来源，例如 `GEO Series Matrix`、`TCGA 本地数据`、`GTEx 本地数据`、`本地表达矩阵`、`样本注释`、`临床表` 或 `本地数据，待数据识别确认`。

## 三个入口的后端接入

- 本地数据导入：调用 `project_workspace_binding.register_acquisition()`，支持 `copy` / `reference`，写入数据获取计划、数据登记记录和下一步交接清单。
- GSE 编号检索：标准化 GSE 编号为大写，调用 `generate_gse_acquisition_plan()` 登记编号；若 legacy `GeoInfoFetcher` 可用，则尝试获取 GEO 元数据。当前不会自动下载数据。
- 中文研究主题检索：生成规则型英文医学词和 GEO 查询词；若 legacy `GeoInfoFetcher` 可用，则尝试用查询词检索候选 GSE。当前不让 AI 生成统计结论，不写入正式分析结果。

## UI-05 合并说明

- 数据获取计划、数据登记记录和下一步交接清单本质上是“选择数据来源后是否登记成功”的确认信息。
- 普通用户无需进入单独的 acquisition status 页面；UI-04 直接显示登记状态、保存方式、warning 和下一步建议。
- 技术字段如 `source_type`、plan 路径、record 路径、handoff 路径和 raw_data path 仅在 `展开技术详情` 中显示，默认折叠。

## 当前可用与不可用功能

- 已可用：项目创建/打开、本地数据登记、GSE 编号登记、GEO 元数据检索尝试、规则型中文主题检索词生成、数据识别、Ready 检查、标准化资产注册、工作流总控、任务记录创建、结果索引读取、项目报告生成。
- 当前不可用或未作为普通流程开放：真实 GEO 自动下载、TCGA / GTEx 网络获取、正式中文数据库在线检索、Ollama 参与检索决策、正式统计分析执行、正式 PDF/DOCX 导出。
- 不可用功能的后续建议：增加受控下载任务页、下载进度和失败重试；将 Translator/Media 作为可选检索词增强器；在分析任务中心明确区分 preview task 和正式统计 runner。

## 测试结果

- 已更新 UI-04 结构测试：确认只显示三个主模块，不再显示独立 GEO Series Matrix / TCGA / GTEx / TCGA + GTEx / 本地 AI 助手卡片。
- 已更新本地数据导入测试：覆盖本地文件、本地文件夹、路径显示、复制路径、打开来源位置、copy/reference 策略和类型推断。
- 已更新 GSE 测试：覆盖 `gse60024` → `GSE60024` 标准化、登记状态、用户友好保存方式，以及普通 UI 不显示 `acquisition` / `plan_only`。
- 已更新中文主题测试：覆盖规则型关键词 fallback、无独立 AI 助手卡片、AI/规则只辅助检索且不参与统计结论。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`，结果：`18 passed`。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py -q`，结果：`47 passed`。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`，结果：`121 passed`。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，结果：通过。
