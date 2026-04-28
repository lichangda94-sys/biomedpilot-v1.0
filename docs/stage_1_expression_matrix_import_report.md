# Stage 1 Expression Matrix Import Report

## Stage Goal

Enhance Local Expression Matrix Import from a basic file preflight into a standard expression matrix asset entry for later cleaning, grouping, and DEG stages. This stage does not implement cleaning, grouping, DEG, or visualization.

## Completed Content

- Preserved the existing Local Expression Matrix Import page and service boundary.
- Added richer matrix diagnostics for CSV, TSV, TXT, and simple XLSX files.
- Added a standard expression matrix asset manifest.
- Kept Data Center registration as `expression_matrix`.
- Kept Task Center registration as `IMPORT`.
- Updated page state and UI summary text so the page can display suitability, duplicate gene count, numeric column ratio, summary path, and manifest path.
- Updated Feature Availability text while keeping status as `testing`.

## Modified Files

- `app/bioinformatics/models/expression_import.py`
- `app/bioinformatics/services/local_expression_import_service.py`
- `app/bioinformatics/pages/local_expression_import_page.py`
- `app/shared/feature_availability.py`
- `docs/bioinformatics_developer_preview_status.md`
- `docs/bioinformatics_asset_contracts.md`
- `docs/user_testing/feature_availability.md`
- `docs/user_testing/known_limitations.md`
- `tests/bioinformatics/test_local_expression_import_service.py`

## New JSON Schema

Each successful import writes two stable JSON files under a per-import output folder.

### `expression_matrix_import_summary.json`

- `project_id`
- `module`
- `data_type`
- `asset_id`
- `source_path`
- `source_type`
- `created_at`
- `status`
- `raw_file_modified`
- `normalization_executed`
- `summary`

### `expression_matrix_asset_manifest.json`

- `asset_id`
- `asset_type`: `expression_matrix`
- `source_file`
- `file_format`
- `row_count`
- `column_count`
- `gene_id_column_candidates`
- `selected_gene_id_column`: `null` until user confirmation exists
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

## Data Center Changes

- Data Center still registers `data_type=expression_matrix`.
- `output_path` now points to `expression_matrix_asset_manifest.json`.
- Data Center `data_id` is aligned with the manifest `asset_id`.

## Task Center Changes

- No new TaskType was added.
- Local Expression Matrix Import continues to register `TaskType.IMPORT`.

## Feature Availability Changes

- `bio-local-expression-import` remains `testing`.
- The description now states that the step supports structure diagnosis, import summary, and standard asset manifest.

## Test Coverage

Updated `tests/bioinformatics/test_local_expression_import_service.py` covers:

- Normal CSV import
- TSV import
- TXT tab-delimited import
- XLSX import using the built-in fallback parser
- Non-numeric column detection
- Duplicate gene/probe/id detection
- High missing value warning
- No gene/id column review status
- Data Center registration
- Task Center registration
- Feature Availability and page state

## Test Command And Result

Command:

```bash
/Users/changdali/Documents/model9/.venv/bin/python -m pytest tests/bioinformatics -q
```

Result:

```text
84 passed
```

## Current Limitations

- This is still testing-level import, not production analysis.
- No matrix normalization is performed.
- No sample annotation import or grouping is performed.
- No DEG runner or figure generation is performed.
- XLSX support uses `openpyxl` when available and a conservative standard-library fallback for simple first-sheet workbooks.

## Stage 2 Recommendation

Implement the cleaning and normalization runner that consumes `expression_matrix_asset_manifest.json`, writes cleaned and normalized CSV files, and registers a `normalized_expression_matrix` asset.
