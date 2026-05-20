# B8.2 DEG-ready Matrix and Formal DEG Preflight

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `deg_task_plan.py` | 直接保留 | 旧 UI preflight 仍可作为草稿入口 | 它混用旧 readiness/recognition 兼容路径，不是 DEG-ready package contract | 新增 `deg_ready/*`，旧入口不提升为正式结果 | `test_deg_ready_matrix_builder.py` |
| `geo_differential_expression_runner.py` / `tcga/deg_runner.py` | 不迁入，仅记录 | 样本分组、均值、FDR 等测试思路 | 会执行统计并可能产生 testing/formal 混淆 | B8.2 不调用 runner | preflight 单测 |
| `project_standardization.py` / `analysis_inputs/*` | 最小迁入 | 标准化资产路径与 package id | package 仍需 DEG 专用 sample/gene policy | 从 B8.1 package 构建 DEG-ready candidate | builder 单测 |
| Integration `deg_executor_preflight.py` | 不迁入，仅记录 | preflight 文案思路 | schema/path 与当前 branch 不兼容 | 只保留“正式 DEG 前必须预检”的原则 | 文档记录 |
| ReleaseBuild `deg_ready_matrix.py` / `deg_summary.py` / `geo_readiness/*` | 不迁入，仅记录 | matrix readiness、mapping readiness 思路 | 旧 summary/descriptive table 不能作为 formal DEG | 重新实现轻量 builder/preflight | 单测覆盖 |

## DEG-ready Matrix

新增 `app/bioinformatics/deg_ready/*`，输出 `deg_ready_package_id`、`source_input_package_id`、matrix/sample/group/feature assets、`value_type`、`gene_id_type`、sample alignment、gene mapping、allowed methods、blockers、warnings。

## Sample Alignment

检查表达矩阵样本列、metadata/group design 覆盖、重复 sample id、缺失样本、case/control 非空和不同组数量。

## Gene Mapping

gene symbol / Ensembl 允许进入 DEG preflight；probe / ID_REF 未确认 mapping 阻断；transcript-level 仅 warning，不自动 collapse。

## Value Type Policy

raw count 可进入 count-model preflight；TPM/FPKM/log-normalized 不进入 count-model DEG；unknown 阻断 formal DEG。

## UI 变化

当前 UI 仍保留旧 DEG preflight 草稿入口。新 DEG-ready contract 可供下一步 UI 接入；正式 DEG 按钮仍不启用。

## 未实现边界

未生成 p-value/FDR，未生成 volcano，未自动 probe mapping/collapse，未合并 TCGA+GTEx，未新增 scipy/statsmodels/R。

## B8.3 建议

在 DEG-ready preflight 通过后，再做依赖检测和受控 Python-first DEG MVP。
