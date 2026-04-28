# Bioinformatics Asset Contracts

Data Center records use the shared `DataAssetRecord` shape:

```json
{
  "data_id": "data-...",
  "project_id": "...",
  "module": "bioinformatics",
  "data_type": "...",
  "source_path": "...",
  "output_path": "...",
  "created_at": "...",
  "status": "available"
}
```

The current service layer stores detailed domain fields in JSON artifacts referenced by `output_path`; Data Center itself stores only the shared record above.

## Current Asset Types

| Asset type | Producer step | Current artifact | Current behavior |
| --- | --- | --- | --- |
| `geo_query_plan` | 数据检索 / 导入 | `geo_query_plan_*.json` | GEO search/accession plan; `online_search_executed=false` |
| `expression_matrix` | Local Expression Matrix Import | `expression_matrix_import_summary.json`, `expression_matrix_asset_manifest.json` | File structure diagnosis and standard asset manifest; raw file is not modified; normalization is not executed |
| `geo_download_plan` | 数据下载 | `geo_download_plan_*.json` | Planned accession download targets; `download_executed=false` |
| `geo_asset_detection` | 数据资产识别 | `geo_asset_detection_*.json` | Local scan summary; `network_used=false` |
| `geo_cleaning_plan` | 数据清洗 | `geo_cleaning_plan_*.json` | Cleaning plan only; `cleaning_executed=false` |
| `geo_sample_grouping_plan` | 样本分组 | `geo_sample_grouping_plan_*.json` | Manual grouping readiness plan; no final grouping execution |
| `geo_differential_expression_preflight` | 差异表达分析 | `geo_differential_expression_preflight_*.json` | DEG readiness preflight; `formal_deg_executed=false` |
| `geo_enrichment_preflight` | 富集分析 | `geo_enrichment_preflight_*.json` | Enrichment readiness preflight; `enrichment_executed=false` |
| `geo_correlation_preflight` | 相关性分析 | `geo_correlation_preflight_*.json` | Correlation readiness preflight; `correlation_executed=false` |
| `geo_survival_preflight` | 生存分析 | `geo_survival_preflight_*.json` | Survival readiness preflight; `survival_analysis_executed=false` |
| `bioinformatics_report_summary` | 报告导出 | `bioinformatics_test_summary_*.md` | Markdown testing summary only; `formal_report_executed=false` in result details |

## Current JSON Artifact Contracts

### `geo_query_plan_*.json`

Required current fields:

- `project_id`
- `created_at`
- `source`: currently `geo`
- `status`: currently `ready_for_download_step`
- `online_search_executed`: `false`
- `plan`: query plan object from the legacy GEO adapter

### `expression_matrix_import_summary.json`

Required current fields:

- `project_id`
- `module`: `bioinformatics`
- `data_type`: `expression_matrix`
- `asset_id`
- `source_path`
- `source_type`
- `created_at`
- `status`: `ready_for_asset_confirmation`
- `raw_file_modified`: `false`
- `normalization_executed`: `false`
- `summary`: current import summary result

### `expression_matrix_asset_manifest.json`

Required current fields:

- `project_id`
- `module`: `bioinformatics`
- `data_type`: `expression_matrix`
- `asset_id`
- `asset_type`: `expression_matrix`
- `source_file`
- `file_format`
- `row_count`
- `column_count`
- `gene_id_column_candidates`
- `selected_gene_id_column`: currently `null`
- `sample_column_candidates`
- `numeric_column_count`
- `numeric_column_ratio`
- `missing_value_summary`
- `duplicate_gene_id_count`
- `non_numeric_columns`
- `created_at`
- `status`: `ready_for_asset_confirmation` or `needs_review`
- `is_expression_matrix_suitable`
- `warnings`
- `errors`
- `raw_file_modified`: `false`
- `normalization_executed`: `false`
- `summary_path`

### `geo_download_plan_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `download_executed`: `false`
- `requires_user_confirmation`: `true`
- `download_items`

### `geo_asset_detection_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `network_used`: `false`
- `detections`

### `geo_cleaning_plan_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `cleaning_executed`: `false`
- `cleaning_items`

### `geo_sample_grouping_plan_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `grouping_executed`: `false`
- `group_inference_executed`: `false`
- `grouping_items`

### `geo_differential_expression_preflight_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `formal_deg_executed`: `false`
- `network_used`: `false`
- `statistical_engine`: `not_configured`
- `preflight_items`

### `geo_enrichment_preflight_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `enrichment_executed`: `false`
- `network_used`: `false`
- `database_download_executed`: `false`
- `preflight_items`

### `geo_correlation_preflight_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `correlation_executed`: `false`
- `network_used`: `false`
- `preflight_items`

### `geo_survival_preflight_*.json`

Required current fields:

- `project_id`
- `source_path`
- `created_at`
- `survival_analysis_executed`: `false`
- `network_used`: `false`
- `preflight_items`

## Planned MVP Asset Types

These are reserved for later stages and do not exist as real runner outputs in Stage 0:

- `normalized_expression_matrix`
- `sample_annotation`
- `comparison_config`
- `differential_expression_result`
- `bioinformatics_figure`
- `enrichment_result`
- `raw_geo_asset`
- `clinical_table`
- `bioinformatics_analysis_report`
- `bioinformatics_reproducibility_package`
