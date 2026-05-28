# UI-C2a LabTools View Model Contract

Date: 2026-05-22

## 1. Scope

This document defines UI-facing view model contracts for LabTools result rendering, warning rows, review notices, copy/export/save states, status chips, and shell-only boundaries.

It is a planning artifact only. It does not implement runtime UI, modify backend logic, enable save/export/history, or touch packaging/App icon/Finder icon resources.

## 2. Core View Models

### 2.1 LabToolsActionState

```text
LabToolsActionState
  state: active | disabled_missing_storage_adapter | disabled_missing_file_picker | disabled_backend_missing | shell_only | blocked_until_backend | future | testing_preview_only
  label: str
  explanation: str
  semantic_key: str
  disabled: bool
  tooltip: str | None
```

Rules:

- `label` must remain visible in the UI.
- Disabled or adapter-needed states must not be icon-only.
- `active` is only allowed when backend capability and required UI adapter both exist.

### 2.2 LabToolsStatusChipModel

```text
LabToolsStatusChipModel
  label: str
  status_key: str
  semantic_key: str
  tone: neutral | info | success_light | warning | blocked
  tooltip: str | None
```

Rules:

- `success_light` can represent backend-ready calculation helper, but not production protocol validation.
- `blocked` is for real backend missing or impossible action, not for planned/future by itself.
- Status icons are auxiliary; text labels are mandatory.

### 2.3 LabToolsIssueRow

```text
LabToolsIssueRow
  severity: info | warning | error | blocked
  title: str
  message: str
  affected_field: str | None
  affected_row_id: str | None
  suggested_action: str | None
  semantic_key: str
  blocking: bool
```

Rules:

- Warning rows remain visible in result panels.
- Blocking rows prevent the affected action/result only.
- Review notices are separate from backend errors and must remain visible.

### 2.4 LabToolsResultTableModel

```text
LabToolsResultTableModel
  columns: list[ResultColumn]
  rows: list[ResultRow]
  empty_state: EmptyStateModel | None
  highlighted_row_ids: list[str]
  semantic_key: str
```

Required column metadata:

- key
- display label
- unit label if applicable
- numeric alignment flag
- warning/error highlight flag

### 2.5 LabToolsResultViewModel

```text
LabToolsResultViewModel
  page_key: str
  module_key: str
  semantic_key: str
  status_chip: LabToolsStatusChipModel
  primary_result: PrimaryResult | None
  secondary_results: list[SecondaryResult]
  result_table: LabToolsResultTableModel | None
  warning_rows: list[LabToolsIssueRow]
  review_notice: LabToolsIssueRow
  copy_text: str | None
  copy_state: LabToolsActionState
  save_state: LabToolsActionState
  export_state: LabToolsActionState
```

Rules:

- Pages with no backend result must use empty/shell/blocker states, not fake rows.
- `review_notice` must be present for calculators, reagent preparation, WB/SDS, and BCA MVP.
- `copy_state` can be active when safe text is generated and no persistence/export is implied.
- `save_state` and `export_state` must be disabled unless adapter requirements are satisfied.

## 3. Page-Specific Contracts

### 3.1 LabTools Home

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.home` |
| `module_key` | `module.labtools` |
| First-level entries | Exactly `General Calculator`, `Reagent Preparation`, `Experiment Modules`. |
| Result view model | Not needed; use navigation/card models and review notice. |
| Required state | Recent activity remains empty/shell until history adapter exists. |
| Forbidden | ImageJ/Fiji first-level card, inventory, cloud sync, LAN sharing, collaboration. |

### 3.2 Quick Calculator

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.general.quick_calculator` |
| Backend | `list_quick_calculator_tasks`, selected v1 calculator dataclass/API. |
| `primary_result` | Main calculated amount/volume. |
| `warning_rows` | Low volume, low mass, tiny value, invalid input. |
| `copy_state` | `active` after valid result. |
| `save_state` | `disabled_missing_storage_adapter` or `future` until `CalculationRecordStore` exists. |
| `export_state` | `future` or `disabled_missing_file_picker`. |
| Boundary | Cell plating helper is calculation-only, not cell record saving. |

### 3.3 Dynamic Formula Solver

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.general.formula_solver` |
| Backend | `list_formula_specs`, `get_formula_spec`, formula solver APIs. |
| `primary_result` | Solved target variable. |
| `secondary_results` | Formula context and converted values if available. |
| `copy_state` | `active` after valid result. |
| `save_state` | `disabled_missing_storage_adapter` or `future`. |
| `export_state` | `future`. |
| Boundary | Solver output is calculation aid, not validated experiment protocol. |

### 3.4 Reagent Template List / Editor

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.reagents.templates` |
| Backend | `ReagentTemplate`, `ReagentComponent`, `ReagentTemplateStore` through storage adapter. |
| Template list state | Empty/adapter-needed until project storage adapter active. |
| Editor issues | Required fields, invalid component type, missing amount/unit, pH warnings. |
| `save_state` | `disabled_missing_storage_adapter` until adapter active. |
| `copy_state` | Component/summary copy can be active if generated. |
| Forbidden | Inventory deduction, cloud library, production batch release, collaboration. |

### 3.5 Reagent Preparation Run

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.reagents.preparation_run` |
| Backend | `PreparationRequest`, `calculate_preparation`, `PreparationResult`, `PreparationRecordStore` through adapter. |
| `primary_result` | Preparation summary. |
| `result_table` | Component amounts/stages. |
| `copy_state` | `active` for summary preview. |
| `save_state` | `disabled_missing_storage_adapter` until adapter active. |
| `export_state` | `disabled_missing_file_picker` or `future`. |
| Boundary | No inventory consumption, audit trail, production batch release. |

### 3.6 Western Blot Loading

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.experiments.protein.wb_loading` |
| Backend | `WBLoadingConfig`, `WBSampleInput`, `calculate_wb_loading`, WB record/export helpers. |
| `primary_result` | WB loading summary. |
| `result_table` | Sample volume, buffer volume, water volume, total volume, status. |
| `warning_rows` | Negative water, sample volume too high, concentration too low. |
| `copy_state` | `active` for table/summary. |
| `save_state` | `disabled_missing_storage_adapter` until adapter active. |
| `export_state` | `disabled_missing_file_picker` until file picker active. |
| Boundary | Lane preview is schematic only; no fake gel bands or image analysis. |

### 3.7 SDS-PAGE

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.experiments.protein.sds_page` |
| Backend | `calculate_sds_page_gel_batch`, template models, XLSX helper. |
| `result_table` | Resolving/stacking component tables. |
| `copy_state` | `active` only for preview text/table. |
| `save_state` | `disabled_missing_storage_adapter` until template persistence adapter exists. |
| `export_state` | `disabled_missing_file_picker`. |
| Boundary | Later subpage/workflow placeholder in first implementation wave. |

### 3.8 BCA / OD MVP Boundary

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.experiments.immuno_absorbance.bca_od` |
| Backend | Testing-only BCA helpers, no record/export store. |
| `status_chip` | `testing_preview_only`. |
| `result_table` | OD matrix/annotation/fit preview if input exists. |
| `save_state` | `disabled_backend_missing`. |
| `export_state` | `disabled_backend_missing`. |
| Boundary | No ELISA, 4PL, formal report, production save/export, or clinical-grade quantification. |

### 3.9 Cell Experiment Workspace Shell

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.experiments.cell.workspace` |
| Backend | No record model/store. |
| `status_chip` | `shell_only` or `blocked_until_backend` for save actions. |
| Main areas | Cell Profile & Dynamic State, Experiment Record Templates, Result Processing. |
| `save_state` | `blocked_until_backend`. |
| `export_state` | `blocked_until_backend`. |
| Boundary | No fake records, fake timeline, automatic ROI, cell counting, ImageJ/Fiji execution, or ELISA. |

### 3.10 ELISA / Immuno-Absorbance Boundary

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.experiments.immuno_absorbance.elisa_boundary` |
| Backend | `labtools.elisa` namespace only; no public API. |
| `status_chip` | `blocked_until_backend`. |
| `copy_state` | Disabled unless static guidance copy is used. |
| `save_state` | `blocked_until_backend`. |
| `export_state` | `blocked_until_backend`. |
| Boundary | No active ELISA analysis, 4PL default workflow, report, save, export, or clinical-grade quantification. |

### 3.11 Image Processing Workspace Boundary

| Field | Contract |
| --- | --- |
| `page_key` | `labtools.experiments.image_processing.boundary` |
| Backend | No ImageJ/Fiji adapter/API. |
| `status_chip` | `shell_only` or `blocked_until_backend`. |
| `save_state` | `blocked_until_backend`. |
| `export_state` | `blocked_until_backend`. |
| Boundary | Settings-linked external engine only; no macro runner, auto ROI, auto cell counting, auto band recognition, or batch analysis. |

## 4. Disabled State Display Copy

| State | Required Copy Pattern |
| --- | --- |
| `disabled_missing_storage_adapter` | `保存 - 需存储适配` |
| `disabled_missing_file_picker` | `导出 - 需文件选择器` |
| `disabled_backend_missing` | `后端未完成` |
| `shell_only` | `仅壳层` or `暂未开放` |
| `blocked_until_backend` | `后端未完成，暂不可运行` |
| `future` | `规划中` |
| `testing_preview_only` | `MVP 预览，仅供复核` |

## 5. Test Expectations

| Test Target | Expected Assertion |
| --- | --- |
| Home model | Exactly three first-level entries; no ImageJ/Fiji first-level card. |
| Quick/formula models | Save/export disabled; copy active only with valid result; warnings remain visible. |
| Reagent models | Save state is adapter-needed until storage adapter active; no inventory/cloud/collab fields. |
| WB model | S3/negative water warning maps to affected row; export state remains file-picker-needed. |
| BCA model | `testing_preview_only`; save/export disabled; no ELISA/4PL/formal report semantic key. |
| Cell model | Shell-only; no fake records/timeline; ImageJ/Fiji action disabled. |
| ELISA model | Blocked until backend; all run/save/export disabled. |
| Image processing model | External-engine boundary; no run/macro/batch action active. |

## 6. Implementation Guardrails

- View models must preserve `page_key`, `module_key`, `status_key`, and `semantic_key` for tests.
- Do not test user-visible Chinese literals as the sole assertion for critical states; prefer semantic keys and object names.
- Do not make a disabled button visually primary.
- Do not show fake results to fill result tables.
- Do not treat `testing_preview_only` as formal result readiness.
