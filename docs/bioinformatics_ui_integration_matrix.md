# BioMedPilot 生信 UI Integration Matrix

## 范围

本矩阵记录 UI-03 到 UI-12 当前按钮和页面动作接入的 active 后端能力。标记为 unavailable / not implemented 的能力不得在 UI 中伪装为已完成。

后续 UI 开发必须同时遵守 `docs/biomedpilot_ui_design_standard.md` 中的统一视觉、术语、技术详情、测试和禁止事项规范。

| UI 动作 | 后端能力 | 当前接入状态 | 用户界面说明 | 后续建议 |
|---|---|---:|---|---|
| 创建 / 打开项目 | `project_workspace.create_bioinformatics_project()`、`open_bioinformatics_project()`、`project_manifest.json`、`project_config.json` | available | UI-03 创建或确认后自动进入 UI-04 | 接入最近项目列表 |
| 本地数据导入 | `project_workspace_binding.register_acquisition()` | available | UI-04 显示来源路径、推断类型、保存方式和登记状态 | 增加批量预检和文件类型预览 |
| copy / reference 保存策略 | `AcquisitionStrategy = copy / reference` | available | 普通 UI 显示为“已复制到项目文件夹 / 引用原始位置” | 增加默认策略设置 |
| GSE 编号登记 | `generate_gse_acquisition_plan()` | available | UI-04 标准化 GSE 编号并登记到项目 | 增加编号格式校验和历史记录 |
| GSE 元数据检索 | legacy `GeoInfoFetcher.search_series()` | available when dependencies/network are available | UI-04 尝试显示标题、样本数、平台信息；失败时说明未完成联网检索 | 增加异步进度和取消按钮 |
| 真实 GEO 自动下载 | legacy GEO downloader exists, active workflow not wired as controlled task | unavailable in ordinary UI | UI-04 明确提示当前不会自动下载数据 | 建立受控下载任务、进度、重试和校验 |
| 中文研究主题检索词 | UI 规则型关键词生成 | available | UI-04 显示英文医学词和 GEO 查询词 | 接入可审计词表和用户编辑 |
| 中文主题在线候选 GSE 检索 | legacy `GeoInfoFetcher.search_series()` with generated query | available when dependencies/network are available | 有结果时显示候选 GSE；失败时保留检索词模式 | 增加分页、筛选和候选登记 |
| GEO legacy 环境检查 | `adapters.legacy_geo.run_geo_environment_check()` | available | UI-13 可执行只读环境检查，显示退出码和输出摘要；不下载数据 | 增加依赖缺失修复建议 |
| Ollama / Translator / Media | legacy `GeoTextProcessor` supports metadata translation/summarization, not query reasoning | partial / not connected to ordinary UI | UI 不把本地 AI 做成独立入口，不参与统计结论 | 作为可选检索词增强器，需用户确认 |
| 数据识别 | `project_recognition.run_project_recognition()` wrapping legacy `detect_dataset()` | available | UI-06 “开始数据识别”调用真实识别后端 | 增加更细的文件预览 |
| Ready 检查 | `project_readiness.run_project_readiness()` | available | UI-07 “运行 Ready 检查”读取识别报告并生成 capability matrix | 增加缺失项修复入口 |
| 标准化资产 | `project_standardization.generate_standardized_assets()` | available | UI-08 生成资产注册和轻量校验，不称为正式 biological normalization | 接入正式标准化设计 |
| 工作流总控 | `project_workflow_orchestrator.run_project_workflow()`、`run_project_stage()` | available | UI-09 可运行完整流程或单步流程 | 增加异步运行和中断 |
| 分析任务中心 | `project_analysis_tasks.load_analysis_task_center()`、`create_analysis_task()` | available | UI-10 读取能力矩阵并创建 task record，不运行正式统计 | 接入正式 runner 前保持 preview 标记 |
| 结果浏览 | `results.project_results.load_result_index()` | available | UI-11 读取真实 result index / result manager | 增加文件预览和报告勾选 |
| 报告生成 | `reports.project_report_builder.generate_project_report()` | available | UI-12 生成 Markdown 项目报告；PDF/DOCX 仍为占位或 testing | 增加正式 HTML/DOCX/PDF 导出管线 |

## 边界

- 不伪造真实 GEO 下载、TCGA / GTEx 网络获取或中文数据库在线检索结果。
- 不让 AI 生成统计结论，不将 AI 输出写入正式分析结果。
- 不运行未实现的正式统计分析，不把 preview task 包装成正式科研分析。
- 不改动 Meta 分析模块和统计 runner。
