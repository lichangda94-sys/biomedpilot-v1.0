# Stage AB10 - Analysis Setup and Applicability

## 本阶段目标

把已有 analysis-ready dataset builder、基础 Meta 统计核心和 statistical applicability guard 包装成用户可理解的 setup -> run -> explain 流程。当前能力仍为 Developer Preview / testing，不作为投稿级最终统计结论。

## Continuity Audit

- 当前分支：`codex/biomedpilot-root`
- 起始 HEAD：`c371914 feat(meta): add quality assessment workspace flow`
- 工作区状态：仅存在既有未跟踪 `test_inputs/`，本阶段未修改或提交该目录。
- 审计正式项目模块：
  - `app/meta_analysis/services/analysis_dataset_service.py`
  - `app/meta_analysis/services/analysis_run_service.py`
  - `app/meta_analysis/services/statistical_applicability_service.py`
  - `app/meta_analysis/pages/analysis_page.py`
  - `app/meta_analysis/services/project_contract_service.py`
  - `app/meta_analysis/services/report_manifest_service.py`
  - `tests/meta_analysis/test_analysis_ready_dataset_service.py`
  - `tests/meta_analysis/test_analysis_core_mvp.py`
  - `tests/meta_analysis/test_stage_u_statistical_applicability.py`
- 已有能力：analysis-ready dataset、binary/continuous/generic effect 统计、fixed/random pooling、applicability warnings、Analysis page 基础状态。

## Legacy Capability Audit

- 检查了 legacy 目录中 analysis plan / workspace 相关文件迹象：
  - `/Users/changdali/Documents/model9`
  - `/Users/changdali/Documents/New project 2`
  - `/Users/changdali/Documents/New project`
- 发现 `model9` 中存在旧 extraction profile analysis plan 测试和 persistence 文件，但它们不遵循当前 BioMedPilot 的 manifest / audit / lineage / Data Center 机制。
- 本阶段未迁移 legacy 代码；原因是正式项目已有更完整统计与适用性服务，适合通过 wrapper 增强而不是复制旧实现。

## 本阶段新增行为

- 新增 `AnalysisSetupService`，统一：
  - analysis plan 保存；
  - analysis-ready dataset preflight；
  - meta-analysis run；
  - applicability warnings 输出；
  - result/dataset 当前 alias 输出；
  - Data Center 注册；
  - audit log；
  - project manifests 刷新。
- 新增 `AnalysisPlan` 和 `AnalysisSetupRunSummary` 数据结构。
- Analysis page 增加 `AnalysisSetupPageState` 和 `analysis_setup_state_from_project()`，用于展示 setup、preflight、run result 和 advanced method not implemented 状态。
- 明确阻断：
  - Network Meta；
  - Diagnostic HSROC；
  - meta-regression。

## 输出路径

- `analysis/analysis_plan.json`
- `analysis/analysis_ready_dataset.json`
- `analysis/analysis_result.json`
- `analysis/applicability_warnings.json`
- 保留既有：
  - `analysis/analysis_ready_datasets.json`
  - `analysis/analysis_results.json`

## Data Center / Task Center / Audit / Manifest / Lineage 影响

- Data Center 新增或刷新：
  - `analysis_plan`
  - `analysis_ready_dataset_alias`
  - `analysis_result_alias`
  - `applicability_warnings`
- Task Center 继续复用既有：
  - `analysis_dataset_build`
  - `meta_analysis_run`
- Audit log 使用既有事件类型：
  - `record_saved`
  - `analysis_run_completed`
- Project contract 新增 canonical paths 和 lineage：
  - analysis plan -> extraction records
  - analysis-ready dataset alias -> dataset set
  - analysis result alias -> result set
  - applicability warnings -> analysis plan
- Report manifest 的 Analysis section 增加 plan、alias 和 applicability warnings 来源。

## 测试

新增：

- `tests/meta_analysis/test_stage_ab10_analysis_setup_applicability.py`

覆盖：

- 空项目 Analysis Setup 状态不崩溃；
- 保存 analysis plan；
- 构建 dataset alias；
- 输出 applicability warnings；
- 运行 analysis 并输出 result alias；
- audit log 记录 analysis run；
- Network Meta not implemented 阻断；
- page state 区分 preflight、dataset、run result、advanced analysis。

## 当前限制

- 当前仍为 testing / Developer Preview。
- Network Meta、Diagnostic HSROC、meta-regression 仅显示 not implemented，不运行正式结果。
- zero-event correction 当前记录在 analysis plan 和统计 warning 中，尚未提供复杂用户自定义规则。
- subgroup selection 当前只进入 setup state，不执行正式 subgroup analysis。
- 统计结果仍需要人工复核后才能进入正式研究材料。

## 下一阶段建议

进入 AB11：Simplified PRISMA Diagram。建议复用现有 PRISMA summary 和 source references，只生成 testing 简化 SVG/Markdown，不做正式 PRISMA 2020 图。
