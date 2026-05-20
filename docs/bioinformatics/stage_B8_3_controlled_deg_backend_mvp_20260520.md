# B8.3 Controlled DEG Backend Decision and MVP

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `services/geo_differential_expression_runner.py` | 不迁入，仅记录 | matrix reader、log2FC、BH FDR 思路 | 内含 standard-library fallback，容易产生“看似正式”的 p-value | 新 backend 缺 scipy/statsmodels 时直接 blocked | `test_controlled_deg_python_backend.py` |
| `tcga/deg_runner.py` | 不迁入，仅记录 | TCGA grouping 思路 | 不是 B8.2 DEG-ready package 消费者 | 保留为旧测试级路径 | dependency/schema 测试 |
| `deg_ready/*` / `analysis_task_runs.py` | 直接保留 | package id、blockers、parameters contract | 本阶段需消费新 contract | backend 只接 DEG-ready dict | result schema 测试 |
| `config/package_requirements.yaml` / Settings | 最小迁入 | 已记录 R 包需求 | 未声明 scipy/statsmodels 运行依赖 | 新增检测逻辑，不自动安装 | dependency check 测试 |
| ReleaseBuild `deg_summary.py` / `deg_ready_matrix.py` | 不迁入，仅记录 | descriptive table 形态 | 缺 dependency snapshot / result schema 边界 | 不复用旧输出 | 文档记录 |

## 后端选择

采用 Python-first 设计：`scipy` 负责 Welch t-test / Mann-Whitney，`statsmodels` 负责 FDR。当前 `pyproject.toml` 未新增依赖；本机缺 scipy/statsmodels 时，正式 DEG 被 blocker 阻断，不产生假 p-value。

R backend 仅保留设计占位，不调用系统 R、不使用 rpy2。

## DEG MVP 范围

新增 `deg_engine/*`。当依赖和输入均通过时支持两组 gene-level numeric matrix、Welch t-test / Mann-Whitney、log2FC、p-value、adjusted p-value、significance label，并记录 engine/version/parameters/dependency snapshot。

## Result Schema

DEG row 至少包含 `feature_id`、`gene_symbol`、`base_mean_or_mean_expression`、`case_mean`、`control_mean`、`log2_fold_change`、`statistic`、`p_value`、`adjusted_p_value`、`significance_label`、`warnings`。

## UI 变化

正式 DEG 仍应由 resolver package、DEG-ready preflight、gene mapping、value type/method、dependency check 和 parameters 全部通过后才启用；当前阶段只提供检测/contract。

## 未实现边界

未实现 DESeq2/edgeR/limma、rpy2、系统 R 调用、TPM/FPKM count-model DEG、ID_REF 未映射 DEG、TCGA+GTEx 合并、volcano、report-ready。

## B8.4 建议

所有 DEG bundle 必须先注册 result index，带完整 semantics 和 provenance 后再被 UI / plot / report 消费。
