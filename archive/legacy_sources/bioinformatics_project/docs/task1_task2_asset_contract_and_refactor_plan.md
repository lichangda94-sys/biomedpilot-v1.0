# 任务1 + 任务2：标准资产 Contract 冻结与最小破坏式改造准备

## 范围
本文件只覆盖以下准备工作：

- 冻结标准资产 contract
- 设计 `raw -> parsed -> organized` 输出路径
- 明确 `expression_gene` / `sample_annotation` / `feature_annotation` / `dataset_manifest` / `comparison_config` 的字段规范
- 识别现有 `download` / `process` / `validator` 中哪些函数保留，哪些函数改成资产写出器
- 输出最小破坏式改造方案与待修改文件清单

本轮不实现 DEG、富集、生存、批次校正等分析模块。

## 设计原则
1. 保留现有 GEO 下载、验收、检测链路，避免推翻重来。
2. 兼容现有 `raw_downloads/` 与 `organized/reports/` 目录习惯。
3. 在不破坏 UI/测试入口的前提下，引入 `parsed/` 层。
4. 标准资产优先服务后续 GEO 分析引擎，不要求本轮覆盖全部 TCGA/GTEx 落地实现。
5. 本轮只冻结 contract 和路径，不大改公共 API 的函数签名。

## 冻结后的目录路径
### 1. 数据集根目录
对 GEO，沿用当前下载根目录中的单数据集目录作为 `dataset_root`：

```text
<run_root>/<GSE>/
```

例如：

```text
geo_downloads/GSE261830_20260422_161351/GSE261830/
```

### 2. 三层路径 contract
为最小破坏式改造，约定如下：

```text
dataset_root/
├── raw_downloads/
│   ├── geo_downloads/
│   ├── metadata_records/
│   ├── supplementary/
│   └── reports/
├── parsed/
│   ├── expression/
│   ├── metadata/
│   ├── annotations/
│   └── reports/
└── organized/
    ├── expression/
    ├── sample_annotation/
    ├── clinical/
    ├── raw_data/
    ├── platform_annotation/
    ├── archives/
    ├── other_supporting_files/
    ├── expression_gene.tsv.gz
    ├── sample_annotation.tsv
    ├── feature_annotation.tsv
    ├── dataset_manifest.json
    └── reports/
```

说明：

- `raw_downloads/` 保持现有命名，不立即改成 `raw/`
- `organized/` 下现有分桶目录继续保留，作为“源文件归档层”
- 新增的标准资产文件直接写在 `organized/` 根下，不与现有目录冲突
- `comparison_config` 不属于自动生成资产，规范路径定为 `configs/comparisons/{dataset_id}.json`

### 3. `processed_GSE*` 的过渡策略
当前 `processed_GSE*` 目录不是标准资产层，只是 legacy 处理输出。

冻结策略：

- 本轮不删除 `processed_GSE*`
- 下一步重构后不再把它作为 canonical 输出
- 若有兼容需要，可由新资产写出器选择性生成 legacy mirror

## 标准资产 contract
本节为冻结后的最小字段规范。字段详细枚举以 [`configs/standards/asset_contract_v1.yaml`](../configs/standards/asset_contract_v1.yaml) 为准。

### 1. `expression_gene`
文件路径：

```text
organized/expression_gene.tsv.gz
```

格式：

- 宽矩阵
- 行表示 feature/gene
- 列表示 sample

固定列：

- `feature_id`
- `gene_symbol`
- `gene_name`
- `gene_id`
- `feature_source`

动态列：

- 每个样本一列，列名必须与 `sample_annotation.sample_id` 完全一致

约束：

- 样本列顺序必须与 `dataset_manifest.sample_id_order` 一致
- 表达值语义不写死在列名里，由 `dataset_manifest.expression_spec` 声明
- 若无法生成 gene-level 表达矩阵，则不得写出空文件；应在 manifest 中标记失败原因

### 2. `sample_annotation`
文件路径：

```text
organized/sample_annotation.tsv
```

必需字段：

- `sample_id`
- `source_sample_id`
- `subject_id`
- `sample_type`
- `group`
- `condition`
- `tissue`
- `disease`
- `organism`
- `platform_id`
- `batch_id`
- `source_dataset`

推荐字段：

- `group_display`
- `treatment`
- `timepoint`
- `replicate_id`
- `source_name`
- `raw_characteristics`

约束：

- `sample_id` 为全项目标准样本主键
- `source_sample_id` 保留原始 GSM 或来源系统样本编号
- `group` 必须是后续 comparison/filter 可直接引用的值

### 3. `feature_annotation`
文件路径：

```text
organized/feature_annotation.tsv
```

必需字段：

- `feature_id`
- `gene_symbol`
- `gene_name`
- `gene_id`
- `feature_type`
- `platform_id`
- `annotation_source`
- `source_dataset`

推荐字段：

- `probe_id`
- `transcript_id`
- `ensembl_gene_id`
- `entrez_gene_id`
- `chromosome`
- `start`
- `end`

约束：

- `feature_id` 必须与 `expression_gene.feature_id` 对齐
- gene-level 矩阵中 `feature_type` 固定为 `gene`
- probe-to-gene 聚合时，聚合前 probe 信息可写入 `annotation_source` 或扩展字段

### 4. `dataset_manifest`
文件路径：

```text
organized/dataset_manifest.json
```

必需字段：

- `contract_version`
- `dataset_id`
- `source_db`
- `source_accession`
- `dataset_root`
- `raw_root`
- `parsed_root`
- `organized_root`
- `technology_type`
- `matrix_level`
- `value_semantic`
- `is_log_scale`
- `expression_unit`
- `sample_count`
- `feature_count`
- `sample_id_order`
- `asset_paths`
- `build_status`
- `recommended_strategy`

推荐字段：

- `title`
- `organism`
- `platform_ids`
- `has_clinical_outcome`
- `has_feature_annotation`
- `has_comparison_config`
- `source_files`
- `provenance`
- `warnings`

约束：

- `asset_paths` 中只登记 canonical 资产文件
- `recommended_strategy` 直接继承 detector 的稳定结论
- `value_semantic`、`matrix_level`、`is_log_scale` 为后续分析引擎选择方法的唯一输入来源

### 5. `comparison_config`
规范路径：

```text
configs/comparisons/{dataset_id}.json
```

这是人工维护配置，不是原始数据自动派生资产。

必需字段：

- `contract_version`
- `dataset_id`
- `comparison_id`
- `comparison_label`
- `group_column`
- `case_values`
- `control_values`

推荐字段：

- `design_formula`
- `blocking_columns`
- `covariates`
- `min_samples_per_group`
- `method_hint`
- `value_semantic_required`
- `matrix_level_required`
- `notes`

约束：

- `group_column` 必须存在于 `sample_annotation.tsv`
- `case_values` / `control_values` 只引用 `sample_annotation[group_column]` 中的标准值
- 若表达值类型不满足 `*_required`，分析引擎必须拒绝执行

## 现有函数保留/改造边界
### A. 直接保留
这些函数已经是较稳定的下载/检测骨架，应尽量保留：

- [`geo_pipeline.download.download_core_geo_records`](../geo_pipeline/download.py)
- [`geo_pipeline.download.discover_series_level_candidates`](../geo_pipeline/download.py)
- [`geo_pipeline.download.discover_series_supplementary_candidates`](../geo_pipeline/download.py)
- [`geo_pipeline.download.discover_sample_level_candidates`](../geo_pipeline/download.py)
- [`geo_pipeline.download.discover_platform_candidates`](../geo_pipeline/download.py)
- [`geo_pipeline.download.score_remote_candidates`](../geo_pipeline/download.py)
- [`geo_pipeline.download.select_remote_download_plan`](../geo_pipeline/download.py)
- [`geo_pipeline.download.execute_download_plan`](../geo_pipeline/download.py)
- [`geo_processing.download_validator.validate_downloaded_dataset`](../geo_processing/download_validator.py)
- [`geo_processing.download_validator.organize_dataset_files`](../geo_processing/download_validator.py)
- [`geo_processing.download_validator.build_dataset_core_objects`](../geo_processing/download_validator.py)
- [`geo_processing.detector.dataset_detector.detect_dataset`](../geo_processing/detector/dataset_detector.py)
- [`geo_processing.detector.matrix_classifier.classify_tabular_matrix`](../geo_processing/detector/matrix_classifier.py)

保留原因：

- 已覆盖 `raw_downloads -> organized(文件分桶) -> detector` 主链路
- 已有较完整测试
- 已形成 `recommended_strategy` 边界，可直接复用为 manifest 输入

### B. 保留为内部 helper，但不再直接作为最终输出器
这些函数应保留逻辑，但未来改为被“parsed/organized 资产写出器”调用：

- [`geo_pipeline.process.build_phenotype_table`](../geo_pipeline/process.py)
- [`geo_pipeline.process.infer_group_column`](../geo_pipeline/process.py)
- [`geo_pipeline.process.summarize_groups`](../geo_pipeline/process.py)
- [`geo_pipeline.process.build_expression_matrix`](../geo_pipeline/process.py)
- [`geo_pipeline.process.basic_clean_expression`](../geo_pipeline/process.py)
- [`geo_pipeline.process.get_single_gpl`](../geo_pipeline/process.py)
- [`geo_pipeline.process.annotate_expression_matrix`](../geo_pipeline/process.py)
- [`geo_pipeline.process.aggregate_to_gene`](../geo_pipeline/process.py)

改造方向：

- 不再只写 `processed_GSE*/phenotype_table.csv`
- 改为先写 `parsed/` 中间文件，再写 `organized/` 标准资产

### C. 应改造成资产写出器的 orchestrator
这些函数当前承担处理入口，但输出目标不符合新 contract，建议改造成新写出器的兼容封装：

- [`geo_pipeline.process.process_from_gse_object`](../geo_pipeline/process.py)
- [`geo_pipeline.process.process_from_local_family_soft`](../geo_pipeline/process.py)
- [`geo_pipeline.process.run_processing_pipeline`](../geo_pipeline/process.py)
- [`geo_tool.geo_workflow.run_download_and_process_workflow`](../geo_tool/geo_workflow.py)

目标职责：

- 读取 detector / validator 结论
- 根据 `recommended_strategy` 选择 source matrix
- 写出 `parsed/` 资产
- 生成 `organized/expression_gene.tsv.gz`
- 生成 `organized/sample_annotation.tsv`
- 生成 `organized/feature_annotation.tsv`
- 生成 `organized/dataset_manifest.json`

### D. 视为重复实现，进入弃用队列
这些文件不应继续扩散逻辑：

- [`process_geo_family_soft.py`](../process_geo_family_soft.py)
- [`geo_tool/geo_pipeline/process.py`](../geo_tool/geo_pipeline/process.py)
- [`geo_tool/geo_pipeline/download.py`](../geo_tool/geo_pipeline/download.py)
- [`geo_tool/geo_pipeline/__init__.py`](../geo_tool/geo_pipeline/__init__.py)

处理建议：

- 本轮不删除
- 后续将调用统一收敛到 `geo_pipeline/`
- 在下一阶段给出 deprecation note

## 最小破坏式改造方案
### 方案核心
1. 现有下载和 validator 不推翻，继续负责：
   - 下载原始文件
   - 组织原始文件到 `organized/` 分桶目录
   - 产生 `data_asset_index.json`
   - 给出 `recommended_strategy`
2. 新增 `parsed/` 层作为 process 与标准资产之间的稳定接口。
3. `geo_pipeline/process.py` 只重构为“标准资产写出器”，不进入分析逻辑。
4. `dataset_manifest.json` 成为后续 GEO 分析引擎的唯一入口描述文件。
5. `comparison_config` 从 process 中抽离，不靠脚本内猜测生成正式比较关系。

### 不做的事
- 不实现 DEG / enrichment / survival / batch correction
- 不统一改造 TCGA/GTEx 下载器
- 不把所有历史输出一次性迁移

## 建议的下一步改动文件清单
### 本轮已新增
- `docs/task1_task2_asset_contract_and_refactor_plan.md`
- `configs/standards/asset_contract_v1.yaml`

### 下一阶段需要修改
- `geo_pipeline/process.py`
  - 新增 parsed/organized 资产写出
  - 保留兼容 wrapper
- `geo_pipeline/__init__.py`
  - 导出新的资产写出入口
- `geo_tool/geo_workflow.py`
  - 从 legacy `processed_GSE*` 输出切到 manifest 驱动
- `geo_processing/download_validator.py`
  - `data_asset_index` 增加 canonical asset path 挂载位
  - 保持现有文件分桶行为
- `geo_processing/download_models.py`
  - 视需要补充 canonical asset path 字段
- `geo_processing/detector/models.py`
  - 视需要补充 manifest-ready 字段
- `tests/test_geo_workflow_integration.py`
  - 断言改为检查 `parsed/` 与 `organized/` 标准资产
- `tests/test_download_validator.py`
  - 对 canonical asset 挂载位补测试
- `README.md`
  - 更新标准资产与路径说明

### 后续待弃用
- `process_geo_family_soft.py`
- `geo_tool/geo_pipeline/*`

## 对后续 GEO 分析引擎的直接收益
当本文件中的 contract 被实现后，分析引擎只需要读取：

- `organized/expression_gene.tsv.gz`
- `organized/sample_annotation.tsv`
- `organized/feature_annotation.tsv`
- `organized/dataset_manifest.json`
- `configs/comparisons/{dataset_id}.json`

这样后续分析模块将不再直接依赖：

- `family.soft.gz`
- `series_matrix.txt.gz`
- 各种 supplementary 原始文件名
- detector 内部 heuristics

## 结论
现有工程最值得保留的是“下载 + 验收 + detector”骨架，不该保留的是“直接把处理结果散落到 `processed_GSE*` 的 legacy 输出方式”。  
最小破坏式改造的关键不是重写全部流程，而是在现有骨架上补一层稳定的 `parsed/` 与标准资产写出规则。
