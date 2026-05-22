# UI-C1c1 LabTools P0 Wireframe Specification

Date: 2026-05-22

## 1. Scope

This stage converts the backend-aligned LabTools mockup plan into executable page-level wireframe specifications, field lists, state rules, mock example data, and acceptance criteria.

Inputs:

- `docs/ui/UI_C1c_labtools_backend_aligned_mockup_assurance_plan_20260522.md`
- `docs/ui/references/labtools/LabTools_UI_integration_contract_20260522.md`
- `docs/ui/references/labtools/LabTools_screen_inventory_mockup_plan_20260522.md`
- `docs/ui/references/labtools/LabTools_backend_gap_audit_20260522.md`

This stage did not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`. It did not generate real UI, implement LabTools backend features, run packaging, run a packaged app, or touch App icon / Finder icon / `.icns` / Info.plist / LaunchServices.

## 2. Fixed LabTools IA

LabTools first-level entries must remain exactly:

| First-level Entry | Child Screens |
| --- | --- |
| General Calculator | Quick Calculator, Dynamic Formula Solver |
| Reagent Preparation | Reagent Template List, Reagent Template Editor, Reagent Preparation Run |
| Experiment Modules | Western Blot Loading, SDS-PAGE Gel, BCA / OD MVP Boundary, qPCR helper, Cell Plating helper, ELISA shell, Cell Experiment Record Home shell |

Rules:

- ImageJ/Fiji is not a LabTools first-level entry. It can appear only as a Settings-linked external capability callout.
- Western Blot, SDS-PAGE, BCA, qPCR, Cell Plating, ELISA, and cell records must not be placed inside General Calculator.
- BCA / OD is not ELISA and must not be used to imply a complete ELISA backend.
- Desktop UI must not default writes to `~/.labtools`; future stores require an explicit BioMedPilot storage-root adapter.
- File export actions require an explicit UI file-picker/export adapter before they can be production actions.

## 3. Global Wireframe Rules

| Rule | Required Behavior |
| --- | --- |
| Status display | Show status chip plus explanatory text. Icons, if present later, are auxiliary only. |
| Save actions | Use `adapter-needed`, `disabled`, or `future` states unless the required store and UI adapter are both present. |
| Copy actions | May be shown for calculated text/table previews when backend result exists. |
| Export actions | Must be disabled or adapter-needed until file picker/export adapter exists. |
| Review notices | Every calculation screen needs a visible "review before bench use" notice. |
| No fake results | Shell-only pages must not show fake analytical output. |
| No packaging | This specification does not change packaging, bundle identity, or desktop entry behavior. |

## 4. Page Specifications

### 4.1 LabTools Home

| Field | Specification |
| --- | --- |
| `screen_id` | `labtools_home` |
| Page purpose | Provide the LabTools module entry surface and route users into the three allowed IA branches. |
| IA location | First-level LabTools page. |
| Backend readiness | `shell_ready`; child readiness varies by target screen. |
| Backend API references | `list_quick_calculator_tasks`, `list_formula_specs`, template/preparation/WB/SDS/BCA availability surfaced only as child status summaries. |
| Required panels | Header, three first-level entry cards, recent LabTools activity shell, quick access links, Settings external capability callout. |
| Input fields | None. |
| Result fields | Child availability summary, recent item rows if available later. |
| Warnings / review notice area | Compact notice that LabTools calculations require user review before bench use. |
| Save / copy / export buttons | None on home. |
| Disabled or adapter-needed states | Recent activity is shell/empty until history adapter is wired. |
| Empty state | "No recent LabTools activity" with empty project/history illustration if available. |
| Example data | Three cards: General Calculator, Reagent Preparation, Experiment Modules. |
| Must-not-claim list | No inventory system, no cloud sync, no LAN sharing, no ImageJ/Fiji first-level card, no completed ELISA or cell record system. |
| Acceptance criteria | Exactly three first-level entry cards are visible; each child screen is grouped under the correct IA branch; Settings-linked ImageJ/Fiji appears only as a secondary callout if shown. |

### 4.2 Quick Calculator

| Field | Specification |
| --- | --- |
| `screen_id` | `quick_calculator` |
| Page purpose | Let users select a backend-ready quick calculator and review calculated output. |
| IA location | General Calculator / second-level page. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `list_quick_calculator_tasks`, `get_quick_calculator_task`, v1 calculator dataclasses, calculator warnings, `CalculationError`. |
| Required panels | Calculator selector, input form, result preview card, warning/review panel, copy actions, history placeholder. |
| Input fields | Calculator-specific fields such as stock concentration, final concentration, final volume, concentration unit, volume unit, optional notes. |
| Result fields | Primary calculated volume/amount, helper values, warning list, review tip. |
| Warnings / review notice area | Unit compatibility, pipetting precision, invalid or missing value, review-before-use notice. |
| Save / copy / export buttons | Copy result allowed; save/history adapter-needed; export not P0. |
| Disabled or adapter-needed states | Save to history disabled until storage adapter exists. |
| Empty state | "Select a calculator to begin." |
| Example data | Dilution example in `docs/ui/mockup_data/labtools/UI_C1c1_labtools_mockup_sample_data_20260522.md`. |
| Must-not-claim list | Do not place WB, SDS-PAGE, BCA, ELISA, qPCR workflow, or cell records here. Do not imply production protocol validation. |
| Acceptance criteria | Selecting a calculator changes fields without page navigation; invalid input shows an error state; result preview always keeps warnings and review notice visible. |

### 4.3 Dynamic Formula Solver

| Field | Specification |
| --- | --- |
| `screen_id` | `formula_solver` |
| Page purpose | Provide formula-driven solving with a visible solve-target control and unit-aware inputs. |
| IA location | General Calculator / second-level page. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `list_formula_specs`, `get_formula_spec`, `FormulaFieldSpec`, `FormulaSolveTargetSpec`, `supported_units_for_formula_field`, formula solver functions, `CalculationResult`. |
| Required panels | Formula selector, formula expression preview, solve-target segmented control, input form, result card, unit/help panel. |
| Input fields | Formula-specific numeric fields, units, solve target, optional rounding/precision. |
| Result fields | Solved target value, converted value if supported, calculation warnings, review note. |
| Warnings / review notice area | Missing variable, incompatible unit, unsupported solve target, review-before-use notice. |
| Save / copy / export buttons | Copy result allowed; save/history adapter-needed; export not P0. |
| Disabled or adapter-needed states | Save formula run disabled until history adapter exists. |
| Empty state | "Choose a formula and solve target." |
| Example data | `C1 * V1 = C2 * V2` solve-target example. |
| Must-not-claim list | Do not use formula solver as a generic replacement for validated experiment modules. |
| Acceptance criteria | The solve-target control determines which field becomes output; all non-target required fields remain editable; errors do not generate fake values. |

### 4.4 Reagent Template List

| Field | Specification |
| --- | --- |
| `screen_id` | `reagent_template_list` |
| Page purpose | List reusable reagent templates and open the editor or preparation flow. |
| IA location | Reagent Preparation / second-level page. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `ReagentTemplateStore.list_templates`, `ReagentTemplate`, `ReagentComponent`, component type helpers. |
| Required panels | Search/filter bar, template table/cards, selected template summary, empty state, adapter notice. |
| Input fields | Search text, category filter, status filter. |
| Result fields | Template name, category, component count, target volume, pH target, last edited, status. |
| Warnings / review notice area | Storage path adapter notice; template content requires user review. |
| Save / copy / export buttons | New template opens editor; duplicate/copy summary can be planned; direct export not P0. |
| Disabled or adapter-needed states | List is empty or sample-only until BioMedPilot storage adapter supplies path. |
| Empty state | "No reagent templates in this project." with create-template action. |
| Example data | PBS 1x template sample. |
| Must-not-claim list | Do not imply shared inventory, cloud template library, or multi-user sync. |
| Acceptance criteria | Template list can represent empty, loading, and adapter-needed states; no default `~/.labtools` write path is implied. |

### 4.5 Reagent Template Editor Side Panel

| Field | Specification |
| --- | --- |
| `screen_id` | `reagent_template_editor` |
| Page purpose | Create or edit reagent template metadata and components in a side panel/modal. |
| IA location | Reagent Preparation / side panel launched from Template List. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `ReagentTemplate`, `ReagentComponent`, `PHRecord`, `UI_COMPONENT_TYPES`, `COMPONENT_TYPE_DESCRIPTIONS`, `normalize_component_type`, `ReagentTemplateStore.upsert_template`. |
| Required panels | Metadata section, component editor table, pH section, validation summary, footer actions. |
| Input fields | Template name, category, target volume, unit, component name, component type, amount, unit, vendor/lot notes, pH target. |
| Result fields | Validation state, component count, normalized component type, preview summary. |
| Warnings / review notice area | Missing unit, invalid component type, pH target missing when required, storage adapter notice. |
| Save / copy / export buttons | Save disabled or adapter-needed until storage adapter is available; copy component list allowed if generated. |
| Disabled or adapter-needed states | Save/update requires BioMedPilot storage-root adapter. |
| Empty state | New template starts with one blank component row and visible validation hints. |
| Example data | PBS 1x template components. |
| Must-not-claim list | Do not claim inventory decrement, stock tracking, or collaboration. |
| Acceptance criteria | Validation prevents save-ready visual state when required fields are missing; side panel close does not imply persistence. |

### 4.6 Reagent Preparation Run

| Field | Specification |
| --- | --- |
| `screen_id` | `reagent_preparation_run` |
| Page purpose | Calculate one preparation run from a selected template and show a reviewable preparation summary. |
| IA location | Reagent Preparation / second-level page. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `PreparationRequest`, `calculate_preparation`, `PreparationResult`, `PreparationRecordStore`. |
| Required panels | Template picker, run parameter form, calculated component table, pH/checklist panel, warning/review panel, action footer. |
| Input fields | Template, target volume, unit, operator note, preparation date, pH measured/adjusted, lot note. |
| Result fields | Required component amount, unit, scaling factor, preparation summary, validation warnings. |
| Warnings / review notice area | pH adjustment review, unit conversion warning, storage adapter notice. |
| Save / copy / export buttons | Copy summary allowed; save record adapter-needed; export adapter-needed. |
| Disabled or adapter-needed states | Save/export disabled until storage and file-picker adapters are wired. |
| Empty state | "Select a template to calculate a preparation run." |
| Example data | PBS 500 mL preparation sample. |
| Must-not-claim list | Do not imply inventory consumption, audit trail, cloud sync, or production batch release. |
| Acceptance criteria | Calculation preview can be shown before save; save/export state remains explicitly adapter-needed. |

### 4.7 Western Blot Loading

| Field | Specification |
| --- | --- |
| `screen_id` | `wb_loading_calculator` |
| Page purpose | Calculate sample/buffer/water loading volumes for Western Blot lanes. |
| IA location | Experiment Modules / Protein Experiment / second-level page. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `WBLoadingConfig`, `WBSampleInput`, `calculate_wb_loading`, `WBLoadingRecordStore`, `wb_loading_record_markdown`, `wb_loading_record_csv`, export helpers. |
| Required panels | Protein workflow substep bar, config card, sample table, result table, lane preview shell, warnings/review panel, action footer. |
| Input fields | Target protein per lane, final loading volume, sample buffer concentration, reducing agent, sample ID, concentration, replicate, notes. |
| Result fields | Sample volume, buffer volume, water volume, lane assignment, warnings. |
| Warnings / review notice area | Negative water volume, concentration too low, sample volume exceeds final volume, review-before-use. |
| Save / copy / export buttons | Copy table allowed; save record adapter-needed; Markdown/CSV export adapter-needed. |
| Disabled or adapter-needed states | History and export require storage/file-picker adapter. |
| Empty state | "Add samples to calculate loading volumes." |
| Example data | Three-sample WB loading table. |
| Must-not-claim list | Do not imply complete WB protocol, transfer optimization, antibody incubation, band analysis, or image analysis. |
| Acceptance criteria | Warning rows remain visible in result table; lane preview is a layout helper only; no fake gel image or band result is shown. |

### 4.8 SDS-PAGE Gel

| Field | Specification |
| --- | --- |
| `screen_id` | `sds_page_gel` |
| Page purpose | Calculate SDS-PAGE gel component amounts from template and batch parameters. |
| IA location | Experiment Modules / Protein Experiment / second-level page. |
| Backend readiness | `active_backend_ready` + `ui_adapter_needed`. |
| Backend API references | `SdsPageGelTemplate`, `GelSection`, `GelComponent`, `SdsPageGelCalculationInput`, `calculate_sds_page_gel_batch`, JSON/XLSX helpers. |
| Required panels | Gel template selector, batch parameter form, resolving/stacking section tables, safety/review notice, export boundary panel. |
| Input fields | Gel format, number of gels, resolving percentage, stacking percentage, section volume, template source. |
| Result fields | Component amount per section, total amount, unit, preparation notes. |
| Warnings / review notice area | Safety/review notice, template pH notice, unit conversion notice, file-picker boundary. |
| Save / copy / export buttons | Copy table allowed; XLSX export adapter-needed; JSON template import/export P1. |
| Disabled or adapter-needed states | Template persistence and XLSX export require adapters. |
| Empty state | "Choose a gel template to calculate component amounts." |
| Example data | Mini gel, 2 gels, 10% resolving / 4% stacking. |
| Must-not-claim list | Do not imply safety validation, complete protein workflow, or generic calculator placement. |
| Acceptance criteria | Resolving and stacking sections are visually distinct; export is never shown as active without file-picker boundary. |

### 4.9 BCA / OD MVP Boundary

| Field | Specification |
| --- | --- |
| `screen_id` | `bca_od_mvp_boundary` |
| Page purpose | Mock up the BCA / OD MVP boundary with plate matrix, annotations, fit summary, and warnings. |
| IA location | Experiment Modules / Immuno & Absorbance / second-level page. |
| Backend readiness | `mockup_only` to `ui_adapter_needed`; calculation helpers are testing-only, no record store/export. |
| Backend API references | `parse_bca_od_matrix`, `annotate_well`, `annotate_well_range`, `analyze_bca_assay`, `BcaAnalysisResult`. |
| Required panels | 8 x 12 OD matrix paste/grid, annotation side panel, standards/sample table, linear-fit summary, warning list, disabled action footer. |
| Input fields | OD matrix, well role, well range, standard concentration, sample dilution note. |
| Result fields | Corrected OD, fit R2, slope/intercept preview, concentration preview, warning list. |
| Warnings / review notice area | Low R2, high CV, negative corrected OD, out-of-range standard/sample, testing-only notice. |
| Save / copy / export buttons | Copy preview may be allowed; save/export disabled or adapter-needed. |
| Disabled or adapter-needed states | Save BCA record and export result disabled until BCA record/export store exists. |
| Empty state | "Paste an 8 x 12 OD matrix and annotate wells." |
| Example data | 8 x 12 OD matrix and annotation sample. |
| Must-not-claim list | Do not claim ELISA, 4PL, production save/export, formal report, or complete absorbance system. |
| Acceptance criteria | The page can show matrix, annotation, fit summary, and warnings; save/export is not active; BCA is not placed under General Calculator or ELISA. |

### 4.10 Cell Experiment Record Home Shell

| Field | Specification |
| --- | --- |
| `screen_id` | `cell_experiment_record_home_shell` |
| Page purpose | Provide a shell overview of future cell experiment record templates without real persistence. |
| IA location | Experiment Modules / Cell Experiment / second-level shell page. |
| Backend readiness | `shell_only` / `blocked_until_backend`; helper calculators may be linked separately. |
| Backend API references | No record model/store. Optional helper-only references: `CellSeedingInput`, `calculate_cell_seeding_v1`. |
| Required panels | Category cards for passage, recovery, freezing, seeding, treatment, transfection; shell state notice; recent records empty state; Settings-linked ImageJ/Fiji callout if needed. |
| Input fields | None for real record save. Optional helper links only. |
| Result fields | None. |
| Warnings / review notice area | "Record saving is not available until backend record model/store is implemented." |
| Save / copy / export buttons | Save/export disabled; helper calculator links may route to existing calculator/helper surfaces. |
| Disabled or adapter-needed states | All record-create/save actions disabled or blocked. |
| Empty state | "No saved cell experiment records. Record storage is planned." |
| Example data | Category names only; no fake saved records. |
| Must-not-claim list | No real save, no complete template system, no cloud sync, no LAN sharing, no ImageJ/Fiji execution. |
| Acceptance criteria | Shell shows categories without fake records; disabled actions have explanation; ImageJ/Fiji remains Settings-linked only. |

## 5. Shell-Only And Blocked Boundaries

| Area | Boundary |
| --- | --- |
| ELISA / Absorbance | `blocked_until_backend`. Do not show active ELISA analysis, standard-curve production output, 4PL default workflow, report-ready output, or fake result. |
| Cell records | `shell_only` until record model/store exists. Do not show real save, history, export, or audit trail. |
| ImageJ/Fiji | Settings-linked external capability only. Do not show it as a LabTools first-level entry and do not imply executable discovery, macro runner, ROI model, parser, or built-in image analysis. |
| BCA / OD | MVP boundary only. Show OD matrix, annotation panel, linear-fit summary, and warnings; keep save/export disabled or adapter-needed. |

## 6. Acceptance Matrix

The screen-level acceptance matrix is in:

`docs/ui/UI_C1c1_labtools_p0_acceptance_matrix_20260522.csv`

## 7. Mockup Sample Data

The non-production sample data pack is in:

`docs/ui/mockup_data/labtools/UI_C1c1_labtools_mockup_sample_data_20260522.md`

## 8. Next Stage Recommendations

1. `UI-C1c2 LabTools high-fidelity mockup prompt pack`: convert these P0 specifications into compact prompt packs for Figma/image mockup production, keeping backend boundary labels explicit.
2. `UI-C2a LabTools adapter-first implementation planning`: plan PySide implementation around storage-root adapter, file-picker/export adapter, and disabled states before adding any new visible save/export affordance.

## 9. Verification

| Command | Result |
| --- | --- |
| `python3 - <<'PY' ... csv structure check ... PY` | Passed: 10 rows, 16 columns, expected P0 screen IDs present |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
