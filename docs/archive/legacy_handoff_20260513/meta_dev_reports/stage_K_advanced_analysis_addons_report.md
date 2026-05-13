# Stage K: Advanced Analysis Add-ons Report

## 本阶段目标

在已有基础 Meta 分析统计核心上，增加常用高级分析：subgroup analysis、leave-one-out sensitivity analysis、influence summary、publication bias basic tests 和 funnel plot。

本阶段不做 network meta、AI、云协作、meta-regression 或完整统计 GUI 编辑器。

## 新增高级分析类型

新增数据模型：

- `SubgroupAnalysisResult`
- `LeaveOneOutResult`
- `PublicationBiasResult`

新增 service：

- `AdvancedAnalysisService`

新增能力：

- `run_subgroup_analysis(project_dir, dataset_id, subgroup_variable, model)`
- `save_subgroup_result`
- `load_subgroup_result`
- `run_leave_one_out(project_dir, analysis_result_id)`
- `save_leave_one_out_result`
- `run_publication_bias_test(project_dir, analysis_result_id)`
- `save_publication_bias_result`
- `load_publication_bias_result`
- `generate_funnel_plot(project_dir, analysis_result_id)`

## 支持范围

Subgroup analysis:

- 支持按 `subgroup` 字段分组。
- 也可读取 `normalized_data` / `raw_data` 中的 testing 字段。
- 字段不存在时返回 `subgroup_variable_missing:<field>` warning。
- 当前 between-group heterogeneity 是 testing descriptive summary，不是正式推断。

Leave-one-out:

- 对每个 study 生成一次 omitted pooled result。
- 记录 `delta_from_original` 和 `is_influential`。
- 少于 3 个研究时返回 warning。

Publication bias:

- 实现基础 Egger regression。
- Begg test 当前为明确 placeholder。
- 小样本会提示 publication bias tests unreliable。

Funnel plot:

- 输出基础 PNG。
- 显示 study effect、standard error 和 pooled effect reference line。

## 小样本 Warning 策略

Publication bias study 数量少于 10 时返回：

- `Publication bias tests are unreliable when the number of studies is small.`

Leave-one-out study 数量少于 3 时返回：

- `leave_one_out_has_fewer_than_three_studies`

## 新增图表

新增 funnel plot 输出：

- `project_dir/figures/funnel_plot_<analysis_result_id>.png`

同时登记 `FigureArtifact`：

- `figure_type = funnel_plot`

## Reporting 集成

Formal Markdown report 增加：

- Subgroup analysis artifact
- Leave-one-out sensitivity artifact
- Publication bias artifact
- Funnel plot artifact
- 小样本 publication-bias warning 说明

## Data Center / Task Center 新增类型

Data Center 新增：

- `subgroup_analysis_result`
- `leave_one_out_result`
- `publication_bias_result`
- `funnel_plot`

Task Center 新增：

- `subgroup_analysis_run`
- `leave_one_out_run`
- `publication_bias_test`
- `funnel_plot_export`

## 新增 / 修改文件

- `app/meta_analysis/models/advanced_analysis.py`
- `app/meta_analysis/services/advanced_analysis_service.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/services/formal_report_service.py`
- `app/shared/task_center/service.py`
- `app/shared/feature_availability.py`
- `tests/meta_analysis/test_advanced_analysis_addons.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `docs/meta_dev_reports/stage_K_advanced_analysis_addons_report.md`

## 测试结果

已验证：

- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q tests/meta_analysis/test_advanced_analysis_addons.py tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_figure_result_table_mvp.py tests/meta_analysis/test_prisma_formal_report_mvp.py`
  - 19 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 233 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 233 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前限制

- Subgroup between-group heterogeneity 是 descriptive testing summary。
- Egger test 是基础线性回归实现，未做完整统计报告解释。
- Begg test 未实现，明确返回 placeholder。
- Funnel plot 是基础 PNG，不是发表级图形。
- 未实现 meta-regression、trim-and-fill、network meta、AI、完整统计 GUI editor。

## 下一阶段建议

进入 Stage L：AI-assisted Review。AI 必须只生成 suggestion，不允许直接覆盖 screening、extraction、analysis 或 report 正式数据。
