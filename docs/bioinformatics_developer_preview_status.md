# Bioinformatics Developer Preview Status

Bioinformatics is currently a Developer Preview / testing module. It provides a unified 11-step workspace, JSON outputs, Data Center registration, Task Center task records, and service/page-state tests. It is not a production analysis system and must not be described as one.

## Current Baseline

- Project root: `/Users/changdali/Documents/BioMedPilot`
- Branch observed for this baseline: `codex/biomedpilot-root`
- Bioinformatics tests: `/Users/changdali/Documents/model9/.venv/bin/python -m pytest tests/bioinformatics -q`
- Baseline result: `80 passed, 1 skipped`
- Runtime note: `python` is not available in the current shell; use the venv Python above for stage tests.
- Current workspace entrypoint: `app/bioinformatics/workspace.py`
- Feature registry source: `app/shared/feature_availability.py`

## 11-Step Workspace Status

| Step | Feature ID | Status | Current capability | Execution class | Current input | Current output |
| --- | --- | --- | --- | --- | --- | --- |
| 数据检索 / 导入 | `bio-data-import` | testing | Builds a GEO query/accession plan. Does not run live online search. | plan | Manual query text and/or GSE accession text | `geo_query_plan_*.json` |
| Local Expression Matrix Import | `bio-local-expression-import` | testing | Reads CSV/TSV/TXT and optionally XLSX if `openpyxl` is installed; creates an expression matrix preflight summary. | testing preflight | Local expression matrix file path | `expression_matrix_import_*.json` |
| 数据下载 | `bio-download` | testing | Reads GEO query plan and creates a download plan. Does not download NCBI data. | plan | `geo_query_plan_*.json` | `geo_download_plan_*.json` |
| 数据资产识别 | `bio-asset-detection` | testing | Scans local target paths from a download plan and summarizes expression-payload candidates. Does not network. | preflight | `geo_download_plan_*.json` | `geo_asset_detection_*.json` |
| 数据清洗 | `bio-cleaning` | testing | Creates a cleaning plan from asset detection output. Does not normalize matrices. | plan/preflight | `geo_asset_detection_*.json` | `geo_cleaning_plan_*.json` |
| 样本分组 | `bio-sample-groups` | testing | Creates a sample grouping plan from a cleaning plan. Does not infer or save final case/control groups. | plan/preflight | `geo_cleaning_plan_*.json` | `geo_sample_grouping_plan_*.json` |
| 差异表达分析 | `bio-deg` | testing | Checks whether grouping output is ready for a DEG runner. Does not compute p-values, FDR, logFC tables, limma, DESeq2, or edgeR. | preflight | `geo_sample_grouping_plan_*.json` | `geo_differential_expression_preflight_*.json` |
| 富集分析 | `bio-enrichment` | testing | Checks DEG preflight readiness for enrichment. Does not run GO/KEGG/GSEA or download databases. | preflight | `geo_differential_expression_preflight_*.json` | `geo_enrichment_preflight_*.json` |
| 相关性分析 | `bio-correlation` | testing | Checks cleaning-plan readiness for correlation setup. Does not calculate coefficients or figures. | preflight | `geo_cleaning_plan_*.json` | `geo_correlation_preflight_*.json` |
| 生存分析 | `bio-survival` | testing | Checks cleaning-plan readiness for survival setup. Does not run KM, log-rank, or Cox analysis. | preflight | `geo_cleaning_plan_*.json` | `geo_survival_preflight_*.json` |
| 报告导出 | `bio-reporting` | testing | Exports a Markdown testing summary from selected Bioinformatics JSON files. Does not generate formal reports or figure packages. | testing summary | One or more Bioinformatics JSON files | `bioinformatics_test_summary_*.md` |

## Why This Is Not Production

- No real GEO online search or default network download is active.
- GEO download currently creates a plan only.
- Cleaning does not execute matrix normalization.
- Sample grouping does not save a final comparison configuration.
- DEG, enrichment, correlation, and survival are preflight checks only.
- No formal statistics, plots, Word/PDF reports, or reproducibility package are generated.
- Numerical/statistical and plotting dependencies are absent from the current venv.
- UI pages are testing-step panels, not a complete guided workflow with ready/completed state across all steps.

## Dependency Gate Baseline

The current venv does not provide `pandas`, `numpy`, `scipy`, `matplotlib`, `openpyxl`, `docx`, `lifelines`, `statsmodels`, or `seaborn`. Stages that require these packages must stop and report the dependency decision instead of installing packages automatically.
