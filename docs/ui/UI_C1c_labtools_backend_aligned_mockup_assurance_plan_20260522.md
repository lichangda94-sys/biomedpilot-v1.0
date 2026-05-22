# UI-C1c LabTools Backend-Aligned Mockup Assurance Plan

## 1. Purpose

This document re-generates the LabTools mockup planning baseline after reading the newly added LabTools reference documents:

- `docs/ui/references/labtools/LabTools_UI_integration_contract_20260522.md`
- `docs/ui/references/labtools/LabTools_screen_inventory_mockup_plan_20260522.md`
- `docs/ui/references/labtools/LabTools_backend_gap_audit_20260522.md`

It supersedes the conservative assumptions in `docs/ui/UI_C1c_labtools_record_template_mockup_plan_20260522.md` for LabTools backend readiness, while preserving the same UI safety boundaries.

This is a planning document only. It does not modify runtime UI, backend logic, tests, assets, packaging, signing, or desktop entries.

## 2. Corrected Backend Readiness Baseline

The new reference documents show that LabTools is not just a shell concept. It has a Python package with UI-callable backend contracts for several P0 surfaces.

| area | corrected backend status | UI implication |
|---|---|---|
| quick calculators | `active_backend_ready` + `ui_adapter_needed` | can design real task-card UI and adapter-bound forms |
| dynamic formula solver | `active_backend_ready` + `ui_adapter_needed` | can design formula registry, solve-target control, variable fields |
| reagent templates | `active_backend_ready` + `ui_adapter_needed` | can design template list, editor side panel, validation states |
| reagent preparation | `active_backend_ready` + `ui_adapter_needed` | can design real preparation run and record flow |
| WB loading | `active_backend_ready` + `ui_adapter_needed` | can design full WB loading calculator with lane layout and exports |
| SDS-PAGE | `active_backend_ready` + `ui_adapter_needed` | can design gel template, batch calculation, XLSX export UI |
| BCA / OD | `mockup_only` to `ui_adapter_needed` | can design MVP mockup; formal save/export waits for record store |
| qPCR mix | `active_backend_ready` + `ui_adapter_needed` | can appear as calculator/experiment-specific UI, not full qPCR workflow |
| cell plating | `active_backend_ready` + `ui_adapter_needed` | can appear as calculator/helper; full cell records still blocked |
| cell experiment records | `shell_only` / `blocked_until_backend` | record-template UI shell only until record store exists |
| ELISA / absorbance | `blocked_until_backend` | mockup boundary only; no active analytical claim |
| ImageJ/Fiji | `shell_only` | external capability callout only; Settings remains source of configuration |

## 3. Mockup Assurance Rules

All LabTools mockups must follow these rules:

1. Use only the three LabTools first-level entries: General Calculator, Reagent Preparation, Experiment Modules.
2. Do not make ImageJ/Fiji a LabTools first-level entry.
3. Do not place WB, SDS-PAGE, BCA, ELISA, PCR/qPCR, MTT/CCK-8, cell seeding, or transfection inside the generic calculator.
4. For backend-ready pages, still show `ui_adapter_needed` boundaries where storage paths, file picker, error normalization, or save/export adapters are missing.
5. Show all backend `warnings`, `review_notice`, `review_tip`, and user-level exceptions in the result/warning area.
6. Stores must be wired through a future BioMedPilot storage-root adapter; mockups must not imply default writes to `~/.labtools`.
7. File export buttons must require a desktop file picker adapter and overwrite confirmation.
8. Shell-only pages must use empty states and explicit planned/shell status, never fake results.
9. ELISA, full cell record saving, ImageJ/Fiji execution, cloud sync, LAN sharing, and collaboration remain blocked.

## 4. Priority Replan

### P0: Backend-Aligned Core Mockups

These are safe to mock as real operation screens because backend contracts exist, though UI adapters are still needed:

| screen | backend contract | mockup commitment |
|---|---|---|
| LabTools Home | `list_quick_calculator_tasks`, `list_formula_specs` | real dashboard of LabTools tasks and statuses |
| Quick Calculator | task specs + v1 calculator dataclasses | real form/result/warning/copy layout |
| Dynamic Formula Solver | `FormulaSpec`, solver functions, unit helpers | real formula-driven UI with solve-target segmented control |
| Reagent Template List | `ReagentTemplateStore`, `ReagentTemplate` | real template list/details/editor mockup |
| Reagent Template Editor | template dataclasses and validation | real side panel/modal mockup |
| Reagent Preparation Run | `calculate_preparation`, `PreparationRequest`, `PreparationResult`, record store | real preparation flow mockup with save adapter boundary |
| WB Loading Calculator | `calculate_wb_loading`, `WBLoadingRecordStore`, Markdown/CSV helpers | real calculator + lane layout + export boundary |
| SDS-PAGE Gel | `calculate_sds_page_gel_batch`, template model, JSON/XLSX helpers | real gel template/calculation/export boundary |

### P0 Mockup But Not Full Runtime Commit

These need visual planning now but must not overclaim:

| screen | backend status | mockup rule |
|---|---|---|
| BCA / OD Record | `mockup_only` to `ui_adapter_needed` | show OD matrix, annotation side panel, linear-fit summary, warnings; mark save/export blocked until record store |
| Cell Experiment Record Home | `shell_only` / `blocked_until_backend` | show template categories and empty states only |

### P1: Adapter / History / Secondary Screens

| screen | reason |
|---|---|
| Calculation History | `CalculationResult.to_record()` exists but unified `CalculationRecordStore` is missing |
| Reagent Preparation History | `PreparationRecordStore` exists; needs BioMedPilot storage adapter |
| WB Loading History | `WBLoadingRecordStore` exists; needs UI storage/file adapter |
| SDS-PAGE Template Import/Export | backend helpers exist; needs file picker and persistence adapter |
| qPCR Mix | backend exists; use as experiment-specific calculator, not full qPCR workflow |
| Cell Plating | backend exists; use as helper, not full cell culture record system |

### P2 / Blocked

| screen | blocker |
|---|---|
| ELISA / Absorbance | `labtools.elisa` has no public API |
| Cell Experiment Record Save | no record model/store |
| ImageJ/Fiji Image Analysis | no discovery, macro runner, ROI model, result parser, or safety boundary |
| Cloud / LAN / collaboration | out of scope |

## 5. Backend Adapter Requirements Before Real UI Integration

Mockups should reserve UI space for these adapters but not implement them in the mockup stage:

| adapter | needed by | purpose |
|---|---|---|
| BioMedPilotLabToolsStorageAdapter | templates, preparation records, WB history, future history | avoid direct default writes to `~/.labtools` |
| UI-facing error normalization | all calculator/store pages | convert backend exceptions into user-readable warning rows |
| file picker/export adapter | WB Markdown/CSV, SDS-PAGE XLSX/JSON, future records | handle save location, overwrite, permissions |
| calculation record store | quick calculator and formula solver histories | persist general calculation records |
| BCA record/export store | BCA / OD | enable formal save/export |
| ELISA MVP backend | ELISA | define API before active UI |
| cell experiment record store | cell records | enable real record saving |
| ImageJ/Fiji external engine adapter | image analysis callouts | detect/configure external engine via Settings only |

## 6. Page-Level Mockup Specifications

### 6.1 LabTools Home

Goal: compact workbench home, not a marketing page.

Layout:

- header with LabTools title and Developer Preview / testing status
- three first-level entry cards only:
  - General Calculator
  - Reagent Preparation
  - Experiment Modules
- P0 backend-ready badges inside relevant cards
- experiment module mini chips nested only inside Experiment Modules
- recent tasks / recently used records shell
- quick access: recent, guide, FAQ, feedback

Do not show ImageJ/Fiji, image analysis, inventory, cloud sync, or collaboration as first-level cards.

### 6.2 Quick Calculator

Backend source:

- `list_quick_calculator_tasks()`
- `get_quick_calculator_task(task_id)`
- task-specific dataclass calculators
- copy text helpers

Layout:

- left task list generated from backend task specs
- center form generated from field metadata and unit helper functions
- right result panel with main result, secondary values, warnings, review notice, and copy action
- bottom calculation history placeholder

Mockup must include:

- user-level error state
- warning row
- review tip
- copy result
- save/history as adapter-needed, not complete if unified store is absent

### 6.3 Dynamic Formula Solver

Backend source:

- `list_formula_specs()`
- `get_formula_spec(spec_id)`
- `FormulaFieldSpec`
- `FormulaSolveTargetSpec`
- `supported_units_for_formula_field(field)`
- solver functions returning `CalculationResult`

Layout:

- formula list
- formula display card
- solve-target segmented control
- auto-generated variable field table with unit selectors
- substitution trace
- main result
- warnings and manual review notice

Do not use “leave one field empty” as the main solve-target interaction. The solve-target control should be explicit.

### 6.4 Reagent Templates And Editor

Backend source:

- `ReagentTemplateStore`
- `ReagentTemplate`
- `ReagentComponent`
- `CommercialReagentInfo`
- `PHRecord`
- `UI_COMPONENT_TYPES`
- `COMPONENT_TYPE_DESCRIPTIONS`
- `normalize_component_type()`

Layout:

- template list with search/filter
- selected template detail
- component table
- pH and storage details
- edit side panel with validation summary
- component editor modal inside side panel

Rules:

- editing template and running current preparation are separate
- duplicate/copy template is allowed as a UI action concept
- current preparation cannot mutate the original template directly

### 6.5 Reagent Preparation Run

Backend source:

- `PreparationRequest`
- `calculate_preparation()`
- `PreparationResult`
- `PreparationRecordStore`

Layout:

- template picker
- request parameters: target volume, target strength, overage/loss mode, operator, notes
- calculation result tree with component rows and preparation stages
- warnings, pH notes, staged steps, review notice
- save preparation record boundary
- copy preparation summary
- history table shell

UI must show storage adapter dependency before claiming real BioMedPilot-integrated persistence.

### 6.6 Western Blot Loading

Backend source:

- `WBLoadingConfig`
- `WBSampleInput`
- `calculate_wb_loading()`
- `WBLoadingRecordStore`
- Markdown/CSV helpers

Layout:

- config panel: target protein amount, final volume, buffer ratio, reducing reagent, marker, lane count
- editable sample table
- result table with sample volume, buffer, water, warnings
- lane layout preview
- summary status badge
- save record, copy Markdown, export CSV/Markdown with file picker boundary

This is an experiment-module page, not a General Calculator page.

### 6.7 SDS-PAGE Gel

Backend source:

- `SdsPageGelTemplate`
- `SdsPageGelCalculationInput`
- `calculate_sds_page_gel_batch()`
- JSON template helpers
- XLSX export helper

Layout:

- template selector/editor
- resolving gel section
- stacking gel section
- gel count and overage inputs
- batch result table
- safety/review note
- export XLSX with file picker boundary
- template JSON import/export with adapter boundary

This belongs inside Western Blot/protein experiment flow.

### 6.8 BCA / OD

Backend source:

- `parse_bca_od_matrix()`
- `annotate_well()`
- `annotate_well_range()`
- `analyze_bca_assay()`
- `BcaAnalysisResult`

Layout:

- 8 x 12 OD paste/import matrix
- well annotation side panel
- standard/sample assignment table
- linear-fit summary panel
- warnings: low R2, high CV, negative corrected OD, out of range
- result table placeholder
- save/export disabled until record store/export is available

This may be mocked as an MVP screen, but must not claim full production save/export.

### 6.9 qPCR Mix And Cell Plating

Backend source:

- `QpcrMixInput`, `calculate_qpcr_mix_v1()`
- `CellSeedingInput`, `calculate_cell_seeding_v1()`

Mockup rule:

- these may appear as specific calculator/helper pages or quick calculator tasks
- qPCR must not imply plate setup, Ct import, Delta Ct, standard curve, or qPCR record store
- cell plating must not imply full cell culture record system

### 6.10 ELISA / ImageJ/Fiji / Cell Record Shells

ELISA:

- `labtools.elisa` is empty
- mock only a boundary page and blocked state
- do not show complete curve fitting as available

ImageJ/Fiji:

- no LabTools backend API
- mock only external capability status and Settings link
- do not run ImageJ/Fiji or imply built-in algorithms

Cell records:

- no record model/store
- mock template homepage and operation-type structure only
- save actions must be disabled/planned

## 7. Updated Core Mockup Prompts

### Prompt 1: LabTools Backend-Aware Home

Create a desktop PySide-style LabTools home mockup for BioMedPilot. The page is a compact workbench, not a landing page. It has exactly three first-level cards: General Calculator, Reagent Preparation, Experiment Modules. General Calculator shows backend-ready badges for quick calculators and formula solver. Reagent Preparation shows backend-ready badges for templates and preparation runs. Experiment Modules shows nested chips for Cell, Protein, Nucleic Acid, Immuno/Absorbance, and IHC. Do not show ImageJ/Fiji, image analysis, cloud sync, inventory, or collaboration as first-level cards. Include status chips, recent tasks shell, and quick access links.

### Prompt 2: Quick Calculator + Formula Solver

Create a low-to-mid fidelity desktop mockup with a left task/formula registry, center auto-generated fields with unit selectors, and right result panel. The UI uses backend task specs and formula specs. Include solve-target segmented control, main result, substitution trace, warnings, review notice, copy action, and adapter-needed save/history state. Include examples for dilution, serial dilution, mass/molarity, solution preparation, RPM/RCF, qPCR mix, and cell plating, but clearly separate experiment-specific quick tasks from the generic formula area.

### Prompt 3: Reagent Template And Preparation Workflow

Create a desktop mockup for Reagent Templates and Current Preparation. Left: template list with filters. Center: selected template detail, components, pH/storage, validation summary. Right: current preparation run with target volume, target strength, overage/loss mode, operator, and notes. Add a template editor side panel with component editor modal. Show that template editing and current preparation are separate. Current preparation cannot directly mutate the original template. Include preparation result tree, warnings, review notice, copy action, and storage adapter-needed save state.

### Prompt 4: Western Blot + SDS-PAGE Protein Flow

Create a desktop mockup for Protein Experiment > Western Blot. Use a stepper: Protein quantification, WB loading, SDS-PAGE gel, Lane layout, Transfer, Antibody incubation, Exposure/image record, Band analysis assist, Export record. The visible area combines WB loading and SDS-PAGE gel preparation. Include config panel, sample table, loading result table, lane layout preview, gel template selector, resolving/stacking gel result table, warnings, review notice, save record, Markdown/CSV/XLSX export buttons with file picker boundary. Do not place these tools in the generic calculator.

### Prompt 5: BCA / OD MVP Boundary

Create a desktop mockup for BCA / OD Record as an MVP boundary page. Show an 8 x 12 OD matrix paste area, well annotation side panel, standards/sample table, linear-fit summary, warnings for low R2/high CV/out-of-range/negative corrected OD, and a result table preview. Mark save/export as disabled or adapter-needed because BCA record store/export is not finalized. Do not place BCA in General Calculator or ELISA.

### Prompt 6: Shell-Only ELISA / Cell Records / ImageJ-Fiji Callouts

Create three small shell-only mockups: ELISA boundary page, Cell Experiment Record homepage, and ImageJ/Fiji external capability callout. ELISA must show blocked-until-backend state. Cell records must show operation categories but disabled save. ImageJ/Fiji must show Settings external capability link and detect-first status only. Do not imply automatic image analysis, ImageJ/Fiji execution, cloud sync, LAN sharing, or complete records.

## 8. What Must Not Be Implemented Or Claimed Now

- UI-B10, App icon, Finder icon, `.icns`, iconset, Info.plist, LaunchServices
- packaged app validation
- ImageJ/Fiji execution
- ImageJ/Fiji as LabTools first-level entry
- automatic band detection or ROI analysis
- ELISA production analysis
- ELISA 4PL default workflow
- cell experiment record saving
- cloud sync
- LAN sharing
- multi-user collaboration
- LIMS integration
- automatic inventory deduction
- direct writes to default `~/.labtools` from desktop UI

## 9. Implementation Readiness By Screen

| screen | mockup now | UI implementation after mockup | backend work needed first |
|---|---:|---:|---|
| LabTools Home | yes | yes | no |
| Quick Calculator | yes | yes, with adapter | UI adapter only |
| Formula Solver | yes | yes, with adapter | UI adapter only |
| Reagent Templates | yes | yes, with adapter | BioMedPilot storage adapter |
| Reagent Preparation | yes | yes, with adapter | BioMedPilot storage adapter |
| WB Loading | yes | yes, with adapter | file picker/storage adapter |
| SDS-PAGE | yes | yes, with adapter | file picker/storage adapter |
| BCA / OD | yes | limited MVP | record store/export before formal save |
| qPCR Mix | yes | yes as calculator/helper | UI adapter only |
| Cell Plating | yes | yes as calculator/helper | UI adapter only |
| Cell Records | shell yes | no real save | record model/store |
| ELISA | boundary yes | no active analysis | ELISA MVP backend |
| ImageJ/Fiji | callout yes | Settings-linked only | external engine adapter |

## 10. Recommended Next Steps

1. Produce visual mockups from Prompts 1-5 first.
2. Keep Prompt 6 as shell-only boundary mockups.
3. Start UI implementation only for backend-ready screens after mockups are approved.
4. Before real save/history/export implementation, define BioMedPilot LabTools storage-root adapter and file picker/export adapter.
5. Keep UI-B10 deferred until LabTools and other core operation screens are visually approved.

## 11. Verification

| command | result |
|---|---|
| `git diff --check` | passed |
| `git diff --cached --check` | passed |
