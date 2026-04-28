# Stage E: Analysis Core MVP Report

## 本阶段目标

基于 `analysis_ready_dataset` 开发基础 Meta 分析统计核心，让 Meta Analysis 模块具备 testing 级 pooled effect 计算能力。

本阶段不做森林图、漏斗图、亚组分析、敏感性分析、发表偏倚、正式 Word/PDF 报告或生产级统计声明。

## 实际完成内容

- 新增当前主链 stats 层，不修改 legacy 统计实现。
- 新增 `AnalysisResult` 和 study-level result 数据模型。
- 新增 `AnalysisRunService`。
- 支持从 `project_dir/analysis/analysis_ready_datasets.json` 读取 dataset 并运行基础 Meta 分析。
- 支持 fixed effect inverse variance。
- 支持 random effects DerSimonian-Laird。
- 支持保存、读取和列出 `analysis_result`。
- Analysis 页面 testing UI 增加 dataset selector、model 输入、run analysis 按钮和 pooled result summary。

## 修改/新增文件列表

- `app/meta_analysis/models/analysis_result.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/services/analysis_run_service.py`
- `app/meta_analysis/stats/__init__.py`
- `app/meta_analysis/stats/heterogeneity.py`
- `app/meta_analysis/stats/meta_effects.py`
- `app/meta_analysis/stats/meta_models.py`
- `app/shared/feature_availability.py`
- `app/shared/task_center/service.py`
- `docs/meta_analysis_current_status.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/meta_analysis/test_analysis_core_mvp.py`
- `tests/meta_analysis/test_developer_preview_stabilization.py`

## 支持的效应量

- Binary outcomes:
  - OR
  - RR
  - RD
- Continuous outcomes:
  - MD
  - SMD
- Generic inverse variance:
  - HR
  - OR
  - RR
  - 其他非 log scale effect + SE/CI

## 支持的模型

- Fixed effect inverse variance。
- Random effects DerSimonian-Laird。

## 异质性指标

- Q statistic。
- I²。
- tau²。

## AnalysisResult 输出路径

- `project_dir/analysis/analysis_results.json`

## Data Center / Task Center 新增类型

- Data Center:
  - `analysis_result`
- Task Center:
  - `meta_analysis_run`

## 测试用例

- OR study effect 计算。
- RR study effect 计算。
- RD study effect 计算。
- MD study effect 计算。
- SMD study effect 计算。
- HR generic inverse variance。
- CI 转 SE。
- Fixed effect pooling。
- Random effects DerSimonian-Laird pooling。
- Q / I² / tau²。
- Zero event correction。
- Insufficient studies warning。
- `AnalysisResult` 保存与读取。
- Analysis page state 显示 result summary。

## 测试结果

已验证：

- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_analysis_ready_dataset_service.py tests/meta_analysis/test_developer_preview_stabilization.py tests/meta_analysis/test_analysis_service.py -q`
  - 31 passed。
- `python -m compileall -q .`
  - 当前 shell 中 `python` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`
  - 通过。
- `pytest -q`
  - 当前 shell 中 `pytest` 命令不存在，原样命令无法运行。
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`
  - 209 passed。
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`
  - 209 passed。
- `python3 -m app.main --smoke-test`
  - 通过，输出 `meta_analysis_features=7`。

## 当前统计限制

- 当前为 testing MVP，不是生产级统计引擎。
- 不做 subgroup analysis。
- 不做 sensitivity analysis。
- 不做 publication bias / funnel plot。
- 不做 meta-regression。
- 不做 network meta-analysis。
- 不生成森林图或正式结果表。

## 下一阶段建议

进入 Stage F：Figure & Result Table MVP，基于 `analysis_result` 生成基础 forest plot PNG 和 analysis result table CSV。
