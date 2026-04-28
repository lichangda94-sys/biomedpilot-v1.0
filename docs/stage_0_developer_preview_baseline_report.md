# Stage 0 Developer Preview Baseline Report

## Stage Goal

Freeze the current Bioinformatics Developer Preview baseline without changing runtime behavior. The goal is to prevent confusion between testing/preflight/plan functionality and future real MVP runners.

## Current Code State

- Branch: `codex/biomedpilot-root`
- Project root: `/Users/changdali/Documents/BioMedPilot`
- Workspace entrypoint: `app/bioinformatics/workspace.py`
- Feature registry: `app/shared/feature_availability.py`
- Shared Data Center service: `app/shared/data_center/service.py`
- Shared Task Center service: `app/shared/task_center/service.py`
- Current Bioinformatics tests pass with the venv Python.
- Existing unrelated untracked Meta Analysis files were present before this stage and were not modified.

## Current 11-Step Functional Status

| Step | Current status | Current execution class | Real runner available |
| --- | --- | --- | --- |
| 数据检索 / 导入 | testing | GEO query/accession plan | No |
| Local Expression Matrix Import | testing | File preflight summary | No normalization runner |
| 数据下载 | testing | Download plan | No real download |
| 数据资产识别 | testing | Local asset preflight | No parser-to-standard-asset runner |
| 数据清洗 | testing | Cleaning plan | No |
| 样本分组 | testing | Grouping plan | No final comparison config |
| 差异表达分析 | testing | Readiness preflight | No |
| 富集分析 | testing | Readiness preflight | No |
| 相关性分析 | testing | Readiness preflight | No |
| 生存分析 | testing | Readiness preflight | No |
| 报告导出 | testing | Markdown testing summary | No formal report |

## Data Center State

Current Bioinformatics data types registered by services:

- `geo_query_plan`
- `expression_matrix`
- `geo_download_plan`
- `geo_asset_detection`
- `geo_cleaning_plan`
- `geo_sample_grouping_plan`
- `geo_differential_expression_preflight`
- `geo_enrichment_preflight`
- `geo_correlation_preflight`
- `geo_survival_preflight`
- `bioinformatics_report_summary`

Planned but not yet implemented MVP data types are listed in `docs/bioinformatics_asset_contracts.md`.

## Task Center State

Current Bioinformatics task type usage:

- `IMPORT`: GEO query import and local expression matrix import
- `DOWNLOAD`: GEO download plan generation
- `PREPROCESS`: asset detection, cleaning plan, sample grouping plan
- `ANALYSIS`: DEG, enrichment, correlation, and survival preflight checks
- `REPORT_EXPORT`: Bioinformatics testing summary export

`VISUALIZATION` exists in the shared Task Center enum but is not currently used by Bioinformatics real figure generation.

## Current Testing Capability

- Tests cover all current service-level preflight/plan/report steps.
- Tests verify Feature Availability status for Bioinformatics steps.
- Tests verify workspace step visibility and ordering.
- The current test suite intentionally skips one dependency-sensitive case.

## Current Main Gaps

- No default real network download.
- No standard expression matrix manifest that can drive downstream runners.
- No real cleaning/normalization runner.
- No final sample grouping or two-group `comparison_config`.
- No formal DEG, enrichment, correlation, or survival statistics.
- No volcano plot, heatmap, enrichment plot, KM plot, or correlation plot.
- No Markdown MVP analysis report beyond testing summary.
- No Word/PDF export or reproducibility package.
- Current venv lacks numerical/statistical/plotting/report dependencies needed by later stages.

## Modified Files

Stage 0 only adds documentation:

- `docs/bioinformatics_developer_preview_status.md`
- `docs/bioinformatics_mvp_roadmap.md`
- `docs/bioinformatics_asset_contracts.md`
- `docs/bioinformatics_task_contracts.md`
- `docs/stage_0_developer_preview_baseline_report.md`

## New JSON Schema / Asset Contract

No runtime schema changed. Stage 0 documents current JSON artifact contracts and reserves planned MVP asset types in `docs/bioinformatics_asset_contracts.md`.

## Data Center Registration Changes

None. Stage 0 is documentation-only.

## Task Center Registration Changes

None. Stage 0 is documentation-only.

## Feature Availability Changes

None. Stage 0 documents the existing `testing` Feature Availability state.

## Test Command And Result

Command:

```bash
/Users/changdali/Documents/model9/.venv/bin/python -m pytest tests/bioinformatics -q
```

Result before documentation edits:

```text
80 passed, 1 skipped
```

Result after documentation edits:

```text
80 passed, 1 skipped
```

## Current Limitations

This baseline is not production-ready. It freezes a Developer Preview where most functionality is still plan/preflight/testing summary rather than real analysis execution.

## Stage 1 Recommendation

Proceed to Stage 1 by enhancing Local Expression Matrix Import into a stable standard asset entry. Keep existing preflight behavior compatible, add a structured import summary and asset manifest, and stop if XLSX support requires unavailable `openpyxl`.
