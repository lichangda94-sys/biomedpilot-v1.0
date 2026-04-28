# BioMedPilot Unified Workbench UI Shell Baseline

## Goal

This baseline adds a unified desktop UI shell for BioMedPilot / 医研智析. The shell starts at a shared Workbench home page and provides entry points for Bioinformatics and Meta Analysis workspaces.

The implementation is UI-only. It does not connect new real analysis, download, search, AI, network, or reporting behavior.

## Unified Workbench Home

The startup page title is `BioMedPilot · 研究分析平台`.

The home page contains:

- Left navigation: 工作台, 项目中心, 数据中心, 任务中心, 报告中心, 团队协作, 设置.
- Hero area: 统一科研分析工作台.
- Bioinformatics entry card with Volcano Plot and Heatmap Top 50 placeholders.
- Meta Analysis entry card with Forest Plot and PRISMA placeholders.
- Mock cards for 最近项目, 统一任务中心, 共享资源, 快速开始.
- Mock status strip for Ready, UI shell loaded, Saved / Mock, memory and CPU placeholders.

Only the `进入模块` buttons switch workspaces. Recent project and creation buttons are disabled placeholders.

## Bioinformatics Workspace

The Bioinformatics workspace title is `BioMedPilot · 生信分析`.

It uses the shared `ProjectShellWidget` and includes:

- Left navigation for 首页, 数据检索, 数据资产, 样本分组, 差异分析, 富集分析, 相关性分析, 生存分析, 可视化, 报告导出, 任务中心.
- Home statistics for data sources, current project, active tasks, and sample counts.
- Volcano Plot and Heatmap Top 50 placeholder cards.
- Mock sections for recent results, analysis flow, and system messages.
- Right settings panel for data source, project / dataset, comparison group, gene set, method, filtering conditions, advanced options, and a disabled start button.

Navigation changes update the current page title and selected state. Non-home pages show a standard placeholder page with description, current development status, future service / view model name, and a disabled primary action.

## Meta Analysis Placeholder Shell

The Meta Analysis workspace title is `BioMedPilot · Meta 分析`.

It uses the shared `ProjectShellWidget` and includes:

- Left navigation for 首页, PICO / 研究问题, 文献检索, 文献导入, 去重管理, 文献筛选, 数据提取, 偏倚风险, Meta 分析, 可视化, 报告导出, 任务中心.
- A home placeholder message: `Meta Analysis workspace is ready. Detailed workflow pages will be implemented later.`

Existing Meta Analysis services and reporting/task interfaces are not refactored in this baseline.

## Component Responsibilities

- `app/workbench_home_widget.py`: unified startup home, module entry cards, mock project/task/resource/quick-start sections.
- `app/project_shell_widget.py`: reusable workspace shell with header, left navigation, main content stack, and bottom status.
- `app/bioinformatics_workspace_widget.py`: Bioinformatics home dashboard, plot placeholders, recent results, workflow, messages, and settings panel.
- `app/meta_analysis_workspace_widget.py`: Meta Analysis shell placeholder.
- `app/project_navigation_model.py`: pure navigation model with no PySide6 dependency.
- `app/ui_style_tokens.py`: shared colors, spacing, radius, font sizing, and stylesheet tokens.

## Not Implemented In This Task

- Real GEO / TCGA / GTEx search or download.
- Real PubMed search.
- Real differential expression, enrichment, correlation, survival, or Meta Analysis statistics.
- Real Word / PDF report export.
- AI calls or network requests.
- Large-scale refactoring of existing analysis, reporting, task, or Meta workflow modules.

## Suggested Integration Order

1. Connect Bioinformatics project context and data asset read models to the Bioinformatics home statistics.
2. Add read-only task status from existing task management into the unified task center card.
3. Mount existing Bioinformatics readiness and analysis views behind matching navigation items.
4. Connect existing Meta Analysis PICO, literature import, screening, extraction, analysis, and reporting pages into the Meta shell one navigation item at a time.
5. Add report export actions only after workspace-level project context and task preflight states are visible.
