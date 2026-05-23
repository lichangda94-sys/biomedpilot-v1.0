# UI-C3b LabTools Record / Export Template Contract

Date: 2026-05-22

## 1. Scope

This stage defines LabTools record and export template contracts based on UI-C3a adapter planning.

This stage is template-only. It does not modify runtime UI, implement file export, implement record stores, enable save/history, enable PDF/DOCX, enable ELISA/BCA/Cell/ImageJ formal export, write to `~/.labtools`, write to project storage, package, or run a packaged app.

## 2. Input Check

Reviewed inputs:

- `docs/ui/UI_C3a_labtools_save_export_history_adapter_plan_20260522.md`
- `docs/ui/UI_C3a_labtools_storage_adapter_contract_20260522.md`
- `docs/ui/UI_C3a_labtools_file_picker_export_adapter_contract_20260522.md`
- `docs/ui/UI_C3a_labtools_save_export_history_enablement_matrix_20260522.csv`
- `docs/ui/UI_C3a_labtools_adapter_error_model_20260522.md`

Input not found in the current checkout:

- `docs/ui/UI_C3_LabTools_Save_Export_History_Adapter_Track_Codex_Guide_20260522.md`

This missing guide does not block C3b because UI-C3a already froze the adapter and disabled-state boundaries.

## 3. Unified LabTools Record Header

All LabTools records and export templates must use this header model:

| Field | Contract |
|---|---|
| Product | `BioMedPilot / LabTools` |
| Record type | One of the record types defined below. |
| Experiment / Tool | User-visible tool or experiment name. |
| Created at | ISO 8601 timestamp or `draft_not_saved` in examples. |
| Operator | User-entered or blank; never inferred from OS account without consent. |
| Project | BioMedPilot project display name or `project_not_bound`. |
| Sample / Template | Sample ID, template ID, or `not_applicable`. |
| Input parameters | Key/value list from UI view model. |
| Calculated results | Result table or summary, if present. |
| Warnings | Warning rows and blocked states. |
| Review notice | Required standard notice. |
| Storage/export status | `copy_only`, `adapter_needed`, `disabled`, `blocked`, or `future`. |
| Software version | BioMedPilot app version and LabTools backend version when available. |

## 4. Standard Review Notice

Required text:

> 本记录由 LabTools 生成，仅作为实验计算和记录辅助。所有结果需由实验人员复核后用于台面操作。

This notice must appear in Markdown examples, JSON draft records, and future export outputs. It must not be removed for copy-only output.

## 5. Record Types

| Record type | Status | Template boundary |
|---|---|---|
| Quick Calculator | copy_text active; markdown/json future | Calculation aid only; no history store yet. |
| Dynamic Formula Solver | copy_text active; markdown/json future | Formula aid only; no history store yet. |
| Reagent Template | storage adapter required | Template save requires project-scoped storage adapter. |
| Reagent Preparation | preview and copy active; record/export adapter required | No inventory deduction or production batch release. |
| WB Loading | preview and copy active; record/export adapter required | Lane preview only; no gel image or band analysis. |
| SDS-PAGE Gel | boundary/planned | XLSX export planned after file picker and writer review. |
| BCA / OD MVP preview | preview boundary | No formal BCA record/export/report. |
| Cell Records shell | shell only | Structure only; no real record store. |
| Image Processing preview | boundary only | Result-field preview only; no ImageJ/Fiji result export. |
| ELISA boundary | blocked_until_backend | Boundary only; no 4PL/formal report/export. |

## 6. Example Artifacts

Markdown examples:

- `docs/ui/templates/labtools/examples/quick_calculator_dilution_example.md`
- `docs/ui/templates/labtools/examples/formula_solver_example.md`
- `docs/ui/templates/labtools/examples/reagent_preparation_pbs_example.md`
- `docs/ui/templates/labtools/examples/wb_loading_example.md`
- `docs/ui/templates/labtools/examples/sds_page_export_plan_example.md`
- `docs/ui/templates/labtools/examples/bca_od_preview_boundary_example.md`

CSV examples:

- `docs/ui/templates/labtools/examples/reagent_preparation_components_example.csv`
- `docs/ui/templates/labtools/examples/wb_loading_table_example.csv`

JSON schema draft:

- `docs/ui/templates/labtools/json_schema_drafts/labtools_record_schema_draft.json`

## 7. Blocked / Boundary Template Rules

### BCA / OD

- MVP preview only.
- No formal save/export/report.
- No clinical-grade quantification.
- No ELISA or 4PL workflow.

### Cell Records

- Structure only.
- No persisted timeline.
- No saved record IDs.
- No export.

### Image Processing

- Result-field preview only.
- No automatic ROI.
- No automatic cell counting.
- No band quantification result.
- No ImageJ/Fiji analysis result export.

### ELISA

- Boundary only.
- No active ELISA analysis.
- No 4PL default workflow.
- No formal report/export.

### PDF / DOCX

- Deferred.
- Not part of UI-C3 adapter track until a formal report system exists.

## 8. Future Implementation Requirements

Before any template becomes active runtime export:

- storage adapter must prove project-scoped path resolution
- file picker adapter must prove explicit path selection
- no default `~/.labtools` write
- no implicit project storage write
- overwrite and permission errors must use UI-C3a error model
- output must include review notice
- disabled/boundary templates must not be exported as formal records

## 9. Validation

Required validation for this stage:

```bash
python3 - <<'PY'
import csv, json
from pathlib import Path
matrix = Path('docs/ui/UI_C3b_labtools_export_format_matrix_20260522.csv')
with matrix.open(newline='') as fh:
    rows = list(csv.DictReader(fh))
assert rows
schema = Path('docs/ui/templates/labtools/json_schema_drafts/labtools_record_schema_draft.json')
json.loads(schema.read_text())
print(f'{matrix}: {len(rows)} rows')
print(f'{schema}: valid JSON')
PY
git diff --check
git diff --cached --check
```

Results will be recorded after validation.

Results:

| Command | Result |
|---|---|
| CSV structure check for `UI_C3b_labtools_export_format_matrix_20260522.csv` | Passed: 10 rows |
| JSON parse check for `labtools_record_schema_draft.json` | Passed |
| `git diff --check` | Passed |

`git diff --cached --check` will be run after staging for the commit gate.
