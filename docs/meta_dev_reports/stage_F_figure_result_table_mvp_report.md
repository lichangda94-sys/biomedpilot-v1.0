# Stage F: Figure & Result Table MVP Report

## 本阶段目标

基于 `AnalysisResult` 生成基础 forest plot 和 analysis result table，让 Meta Analysis 模块具备 testing 级最小可视化结果输出能力。

本阶段不做 funnel plot、subgroup forest、sensitivity plot、PRISMA 正式图、Word/PDF 正式报告。

## 实际完成内容

- 新增 `FigureArtifact` 数据模型。
- 新增 `FigureResultService`。
- 支持从 `analysis_results.json` 读取 `AnalysisResult`。
- 支持生成基础 forest plot PNG。
- 支持导出 analysis result table CSV。
- 支持保存和读取 `figure_artifacts.json`。
- Analysis 页面 testing UI 增加 forest plot 和 result table 导出入口。

## 修改/新增文件列表

- `app/meta_analysis/models/figures.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/services/figure_result_service.py`
- `app/shared/feature_availability.py`
- `app/shared/task_center/service.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/meta_analysis/test_figure_result_table_mvp.py`

## Forest Plot 输出路径

- `project_dir/figures/forest_plot_<result_id>.png`

## Result Table 输出路径

- `project_dir/exports/analysis_result_table_<result_id>.csv`

## FigureArtifact 字段

- `figure_id`
- `project_id`
- `analysis_result_id`
- `figure_type`
- `file_path`
- `format`
- `dpi`
- `created_at`
- `source_summary`

## UI 新增入口

- Analysis result ID 输入。
- Generate forest plot PNG button。
- Export result table CSV button。
- Generated artifact path display。

## Data Center / Task Center 新增类型

- Data Center:
  - `forest_plot`
  - `analysis_result_table`
- Task Center:
  - `forest_plot_export`
  - `analysis_result_table_export`

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_figure_result_table_mvp.py tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_analysis_ready_dataset_service.py -q`
  - 19 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 211 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 211 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前图表限制

- Forest plot 为 testing 级基础 PNG，不是投稿级最终图。
- 当前不生成 PDF forest plot。
- 当前不支持 funnel plot。
- 当前不支持 subgroup forest 或 sensitivity plot。
- 当前不提供交互式图表编辑。

## 下一阶段建议

进入 Stage G：PRISMA & Formal Markdown Report MVP，基于现有 artifacts 生成 PRISMA 数字摘要和正式 Markdown 报告雏形。
