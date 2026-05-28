# UI-C2a0 LabTools Record / Export Template Contract

Date: 2026-05-22

## 1. Scope

This document defines the deferred LabTools record and export template contract before any real save, export, or history workflow is enabled in the desktop UI.

This is a docs/spec stage only. It does not implement runtime export, file picker integration, storage adapter behavior, report generation, packaging, or new LabTools backend functions.

Inputs reviewed:

- `/Users/changdali/Desktop/UI/UI_C2a0_labtools_record_export_template_deferred_task_20260522.md`
- `docs/ui/UI_C2a_labtools_adapter_contracts_20260522.md`
- `docs/ui/UI_C2g_labtools_ui_runtime_status_matrix_20260522.csv`

Created in this stage:

- `docs/ui/UI_C2a0_labtools_record_export_template_contract_20260522.md`
- `docs/ui/UI_C2a0_labtools_export_format_matrix_20260522.csv`
- `docs/ui/templates/labtools/examples/*.md`
- `docs/ui/templates/labtools/examples/*.csv`

## 2. Non-runtime Boundary

This contract must not be interpreted as runtime enablement.

Still disabled or deferred:

- real save to project storage
- real history store
- file picker export
- PDF / DOCX report export
- formal report-ready package
- BCA formal records
- ELISA analysis/export
- cell experiment saved records
- ImageJ/Fiji analysis result export
- cloud sync, LAN sharing, collaboration, or LIMS integration
- default writes to `~/.labtools`

## 3. Shared Metadata Header

Every LabTools record/export should include this common metadata envelope when the format allows it:

| Field | Required | Notes |
| --- | --- | --- |
| `product` | yes | `BioMedPilot / LabTools` |
| `record_type` | yes | Stable type key such as `reagent_preparation` or `wb_loading`. |
| `experiment_or_tool` | yes | Human-facing page/tool name. |
| `created_at` | yes | ISO datetime or local timestamp with timezone. |
| `operator` | yes | User-entered or current session display; may be `not recorded`. |
| `project` | yes | BioMedPilot project id/name; may be `not attached` until storage adapter exists. |
| `sample_or_template` | conditional | Sample id, template name, cell line, or tool input subject. |
| `input_parameters` | yes | Key/value section or table. |
| `calculated_results` | conditional | Required for calculation/export types with result preview. |
| `warnings` | yes | Empty list allowed; warning section must still be present. |
| `review_notice` | yes | Fixed review notice below. |
| `storage_status` | yes | `disabled_missing_storage_adapter`, `blocked_until_backend`, or future adapter status. |
| `export_status` | yes | `disabled_missing_file_picker`, `blocked_until_backend`, or future export status. |
| `software_version` | yes | BioMedPilot version/channel. |

Required review notice:

```text
本记录由 LabTools 生成，仅作为实验计算和记录辅助。
所有结果需由实验人员复核后用于台面操作。
```

Required disabled/boundary labels:

```text
保存状态：需存储适配
导出状态：需文件选择器适配
分析状态：MVP preview / shell-only / blocked_until_backend
```

## 4. Supported Format Semantics

| Format | Current Priority | Contract Meaning | Runtime Enablement |
| --- | ---: | --- | --- |
| Copy text | P0 | Plain text copied from visible result panels. | Allowed only where current UI already exposes copy safely. |
| Markdown / TXT | P0 | Human-readable experiment record draft. | Template only until file picker/export adapter exists. |
| CSV | P0/P1 | Flat table export for result tables and component rows. | Template only until file picker/export adapter exists. |
| XLSX | P1 | Multi-sheet workbook structure, especially SDS-PAGE and future plate/matrix data. | Plan only; no runtime XLSX export in this stage. |
| JSON | P1 | Internal record draft for future recovery/history/migration. | Schema draft only; no runtime write in this stage. |
| PDF / DOCX | P2+ | Formal report-like export. | Explicitly out of scope. |

## 5. Record Type Contracts

### 5.1 Quick Calculator

Status: copy / Markdown first.

Required sections:

- metadata header
- selected task
- input fields and units
- result summary
- warning rows
- review notice
- save/export status

Allowed current action:

- Copy visible result text.

Still blocked:

- save history
- file export
- calculation history store

Example:

- `docs/ui/templates/labtools/examples/quick_calculator_copy_template.md`

### 5.2 Dynamic Formula Solver

Status: copy / Markdown first.

Required sections:

- metadata header
- formula id/name
- displayed formula expression
- solve target
- input values and units
- solved result
- warnings/errors
- review notice
- save/export status

Allowed current action:

- Copy solved result when valid.

Still blocked:

- save history
- file export
- formula record store

Example:

- `docs/ui/templates/labtools/examples/dynamic_formula_solver_record_template.md`

### 5.3 Reagent Template

Status: Markdown / JSON draft.

Required sections:

- metadata header
- template name/category
- intended use
- target pH/osmolality if relevant
- component table
- validation notes
- dirty state
- storage adapter status
- review notice

Still blocked:

- real template save
- version management
- inventory deduction
- cloud template library

Example:

- `docs/ui/templates/labtools/examples/reagent_template_draft_template.md`

### 5.4 Reagent Preparation

Status: Markdown + CSV table contract.

Required sections:

- metadata header
- selected template
- target volume
- operator
- pH measured / pH adjusted if relevant
- component result table
- warnings/review notice
- storage/export status

Allowed current action:

- Copy preparation summary preview.

Still blocked:

- preparation record save
- Markdown/CSV file export
- inventory consumption
- batch release

Examples:

- `docs/ui/templates/labtools/examples/reagent_preparation_record_template.md`
- `docs/ui/templates/labtools/examples/reagent_preparation_components_template.csv`

### 5.5 Western Blot Loading

Status: Markdown + CSV.

Required sections:

- metadata header
- WB configuration
- sample input table
- loading result table
- lane layout summary
- warnings, including impossible volume handling
- review notice
- storage/export status

Allowed current action:

- Copy loading table/summary.

Still blocked:

- WB record save
- Markdown/CSV file export
- history
- fake gel bands
- image analysis

Examples:

- `docs/ui/templates/labtools/examples/wb_loading_record_template.md`
- `docs/ui/templates/labtools/examples/wb_loading_result_template.csv`

### 5.6 SDS-PAGE Gel

Status: Markdown + XLSX plan.

Required sections:

- metadata header
- gel system and percentage
- resolving gel section
- stacking gel section
- component table per layer
- workbook sheet plan
- warnings/review notice
- export status

Still blocked:

- XLSX export without file picker
- template save
- complete protein workflow claim

Example:

- `docs/ui/templates/labtools/examples/sds_page_workbook_plan_template.md`

### 5.7 BCA / OD MVP

Status: preview template only.

Required sections:

- metadata header
- plate/matrix shape
- annotation fields
- fit summary preview
- warnings for low R2, high CV, negative corrected OD, out-of-range samples
- testing/MVP boundary notice

Still blocked:

- formal BCA record save
- formal export
- ELISA
- 4PL
- clinical-grade quantification

Example:

- `docs/ui/templates/labtools/examples/bca_od_mvp_preview_template.md`

### 5.8 Cell Records

Status: structure only.

Required sections:

- cell line/profile
- passage and dynamic state
- record template type
- operation fields
- warnings/review notice
- store status

Still blocked:

- real cell record save
- timeline persistence
- fake records
- automatic image analysis

Example:

- `docs/ui/templates/labtools/examples/cell_records_structure_template.md`

### 5.9 Image Processing

Status: preview/result-field template only.

Required sections:

- workflow type
- external engine status
- image set summary
- planned result fields
- manual review notice
- disabled run/save/export status

Still blocked:

- ImageJ/Fiji runner
- macro exposure
- automatic ROI
- automatic cell counting
- automatic band recognition
- formal result export

Example:

- `docs/ui/templates/labtools/examples/image_processing_preview_template.md`

### 5.10 ELISA / Absorbance

Status: boundary only.

Required sections:

- blocked backend status
- planned standard curve fields
- planned sample dilution fields
- disabled action labels
- no formal report/export notice

Still blocked:

- ELISA backend
- active 4PL
- production save/export
- clinical-grade quantification

Example:

- `docs/ui/templates/labtools/examples/elisa_absorbance_boundary_template.md`

## 6. CSV Rules

CSV examples are field contracts, not live exports.

Required CSV rules:

- Header row must use stable snake_case fields.
- Units should be explicit in either field names or adjacent unit columns.
- Warning/status columns must not be omitted.
- Empty warnings use an empty cell, not a fake success statement.
- Negative or impossible calculated values remain visible with `Warning` or `Error` status; do not hide them.
- CSV examples should remain ASCII-compatible where feasible, but human-facing notes may use Chinese where the UI requires it.

## 7. JSON Draft Rules

JSON internal record drafts are planned but not produced as files in this stage.

Future JSON draft should include:

```json
{
  "schema_version": "labtools.record.v0",
  "record_type": "reagent_preparation",
  "metadata": {},
  "inputs": {},
  "results": {},
  "warnings": [],
  "review_notice": "",
  "storage_status": "disabled_missing_storage_adapter",
  "export_status": "disabled_missing_file_picker"
}
```

No JSON schema draft is added in this stage because runtime record persistence remains disabled.

## 8. Runtime Adoption Gate

Before any save/export/history button becomes active, a later implementation stage must provide:

1. `BioMedPilotLabToolsStorageAdapter`
2. `FilePickerExportAdapter`
3. UI-facing error normalization
4. record view model with warning rows and review notice
5. focused tests proving no default `~/.labtools` write
6. focused tests proving disabled/export gates remain disabled until adapters are active
7. file picker cancel/overwrite/permission handling tests

## 9. Verification

| Command | Result |
| --- | --- |
| CSV structure check for `docs/ui/UI_C2a0_labtools_export_format_matrix_20260522.csv` | Passed; 10 rows with required columns and existing example paths |
| CSV structure check for `docs/ui/templates/labtools/examples/*.csv` | Passed; 2 example CSV files parsed |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed after staging docs/templates |

No runtime tests are required for this stage because only documentation and template examples are added.

## 10. Non-modification Statement

This stage does not modify runtime app code, tests, active assets, packaging scripts, `dist/**`, App icon / Finder icon / `.icns` / Info.plist / LaunchServices, or desktop entry points. It does not enable real save, export, history, report generation, or LabTools backend functionality.
