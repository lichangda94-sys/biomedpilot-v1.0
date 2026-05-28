# UI-C3a LabTools Save / Export / History Adapter Plan

Date: 2026-05-22

## 1. Scope

This stage plans LabTools save, export, and history adapter enablement after UI-C2b-C2f delivered:

- LabTools navigation shell
- General Calculator UI
- Reagent Preparation preview UI
- Western Blot Loading preview UI
- LabTools boundary pages

This stage is planning-only. It does not modify runtime UI behavior, enable save/export/history, create stores, write to `~/.labtools`, write to project storage, add backend functionality, package, run a packaged app, or touch UI-B10 / App icon / Finder icon / `.icns` / Info.plist / LaunchServices.

## 2. Input Check

Reviewed inputs:

- `docs/ui/UI_C2a_labtools_adapter_first_implementation_plan_20260522.md`
- `docs/ui/UI_C2a_labtools_adapter_contracts_20260522.md`
- `docs/ui/UI_C2a_labtools_view_model_contract_20260522.md`
- `docs/ui/UI_C1c3d_labtools_mockup_set_closure_audit_20260522.md`
- `docs/ui/UI_C2g_labtools_ui_implementation_closure_audit_20260522.md`
- `docs/ui/UI_C2g_labtools_ui_runtime_status_matrix_20260522.csv`
- `app/labtools_runtime.py`

Input not found in the current checkout:

- `docs/ui/UI_C3_LabTools_Save_Export_History_Adapter_Track_Codex_Guide_20260522.md`

This missing guide did not block planning because the C2a and C2g contracts already define the adapter-first boundary.

## 3. Planned Adapter Documents

Detailed contracts are split into:

- `docs/ui/UI_C3a_labtools_storage_adapter_contract_20260522.md`
- `docs/ui/UI_C3a_labtools_file_picker_export_adapter_contract_20260522.md`
- `docs/ui/UI_C3a_labtools_adapter_error_model_20260522.md`
- `docs/ui/UI_C3a_labtools_save_export_history_enablement_matrix_20260522.csv`

## 4. Project Storage Strategy

The desktop UI must never fall back to standalone LabTools defaults such as `~/.labtools`.

Planned project-scoped root:

```text
project_storage/
  labtools/
    templates/
    records/
    exports/
    attachments/
    diagnostics/
```

No directories should be created on page open. Directory creation is allowed only after a user-confirmed save/export action in a later implementation stage, and only when the storage or export adapter is active.

## 5. Store Status Summary

| Store / capability | Status | Rule |
|---|---|---|
| ReagentTemplateStore | planned_adapter_required | Can be enabled only through `BioMedPilotLabToolsStorageAdapter`. |
| PreparationRecordStore | planned_adapter_required | Can be enabled only through `BioMedPilotLabToolsStorageAdapter`. |
| WBLoadingRecordStore | planned_adapter_required | Can be enabled only through `BioMedPilotLabToolsStorageAdapter`. |
| CalculationRecordStore | future_missing_store | Quick/Formula history remains disabled. |
| BCA record/export store | blocked_future | No formal BCA record/export store yet. |
| CellExperimentRecordStore | blocked_future | No cell record store yet. |
| ELISA store/export | blocked_until_backend | ELISA backend is not complete. |
| Image Processing export | blocked_until_external_engine_adapter | External engine/result adapter missing. |

## 6. Export Format Strategy

Allowed for future planning:

- Markdown / TXT
- CSV
- XLSX
- JSON draft

Forbidden for UI-C3a and still disabled until a later explicit stage:

- PDF
- DOCX
- formal report package
- ELISA formal export
- BCA formal export
- Cell record export
- ImageJ/Fiji analysis result export

## 7. Enablement Sequence

Recommended future stages:

1. `UI-C3b`: implement read-only adapter scaffolding and tests, still no write.
2. `UI-C3c`: enable explicit project-scoped reagent template save behind adapter.
3. `UI-C3d`: enable explicit reagent preparation and WB loading record save.
4. `UI-C3e`: enable file-picker exports for safe CSV/Markdown/TXT outputs only.
5. `UI-C3f`: add history views fed only by project-scoped stores.

Do not combine BCA formal export, ELISA, cell records, image processing export, PDF/DOCX report generation, or packaged app work into the first adapter enablement stages.

## 8. Required Tests For Future Implementation

Future adapter implementation must include:

- no default `~/.labtools` write test
- no write on LabTools Home open
- project storage path resolution test
- missing project storage disables save/history
- file picker cancel makes no backend export call
- overwrite declined makes no write
- unsupported extension blocks export
- permission denied normalizes an error row
- partial write failure does not show success
- disabled/future stores return disabled capability, not fake stores

## 9. Validation

Required validation for this planning stage:

```bash
python3 - <<'PY'
import csv
from pathlib import Path
path = Path('docs/ui/UI_C3a_labtools_save_export_history_enablement_matrix_20260522.csv')
with path.open(newline='') as fh:
    rows = list(csv.DictReader(fh))
assert rows
print(f'{path}: {len(rows)} rows')
PY
git diff --check
git diff --cached --check
```

Results will be recorded after validation.

Results:

| Command | Result |
|---|---|
| CSV structure check for `UI_C3a_labtools_save_export_history_enablement_matrix_20260522.csv` | Passed: 10 rows |
| `git diff --check` | Passed |

`git diff --cached --check` will be run after staging for the commit gate.

## 10. Boundary Declaration

This stage does not enable save, export, history, stores, file writes, backend features, ELISA, BCA formal export, cell record export, ImageJ/Fiji export, PDF/DOCX reports, packaging, packaged app runtime, or UI-B10 resources.
