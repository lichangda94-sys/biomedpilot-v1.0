# UI-C1c LabTools Record Template & Calculator Mockup Planning

## 1. Scope

This stage converts the UI-C1a LabTools inventory into low-to-mid fidelity mockup specifications for real LabTools operation screens.

Inputs reviewed:

- `docs/ui/UI_C1a_interface_screen_inventory_mockup_planning_20260522.md`
- `docs/ui/UI_C1a_screen_inventory_20260522.csv`
- `docs/ui/target_design_drafts/LabTools_UI_Architecture_Discussion_20260520.md`
- `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md`
- current LabTools shell in `app/shell/main_window.py`

Outputs:

- `docs/ui/UI_C1c_labtools_mockup_screen_specs_20260522.csv`
- `docs/ui/UI_C1c_labtools_record_template_mockup_plan_20260522.md`

## 2. Boundary Statement

This is a planning and mockup specification stage only.

Not changed:

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/**`
- `dist/**`
- App icon, Finder icon, `.icns`, iconset, Info.plist icon binding, LaunchServices
- LabTools business logic
- calculator backends
- reagent template backends
- WB / BCA / SDS-PAGE / PCR / qPCR / cell culture backends
- Settings resource detection logic

No packaged app was run. No packaging, codesigning, package smoke, or desktop app replacement was performed.

## 3. Current LabTools Runtime Finding

The current UIShell branch has a LabTools shell in `app/shell/main_window.py`. It exposes:

- LabTools module page
- three primary entries: 通用计算器, 试剂制备, 实验模块
- experiment category icons: 细胞实验, 蛋白实验, 核酸实验, 免疫与吸光度, 免疫组化
- status chips and active LabTools icon pilot assets

No standalone `app/labtools/` backend directory exists in the current UIShell checkout. Therefore screen specs use conservative status labels:

- `ui_adapter_needed` for shell screens that need a future adapter before real operation
- `planned` for pages without current implementation
- `shell_only` for Settings-linked callouts or boundary pages

This plan does not claim `active_backend_ready` for LabTools calculation or record-template pages.

## 4. LabTools IA Rules Preserved

The mockup plan preserves the confirmed LabTools IA:

```text
LabTools / 实验工具
├── 通用计算器
├── 试剂制备
└── 实验模块
```

Rules:

- Image analysis is not a LabTools first-level entry.
- ImageJ/Fiji configuration remains in Settings external capability.
- General Calculator only contains cross-experiment formula/unit calculations.
- WB / PCR / ELISA / MTT / BCA / SDS-PAGE are not placed in General Calculator.
- Reagent preparation follows template -> preparation run -> preparation sheet -> preparation record.
- Current preparation must not directly modify the original template.
- Cell operation records may include calculation helpers, but remain cell operation records.
- SDS-PAGE belongs inside Western Blot.
- BCA belongs to protein sample/protein quantification.
- PCR and qPCR are separate within nucleic acid experiments.
- OD is a reading/data type, not an independent user-facing module.
- Cloud sync, LAN sharing, LIMS, and collaboration are not in this stage.

## 5. Screen Spec Summary

The screen-level CSV contains 13 LabTools screens from UI-C1a:

| screen_id | screen | current status | mockup priority |
|---|---|---|---|
| LAB-001 | General Reagent Calculator | `ui_adapter_needed` | P0 |
| LAB-002 | Dynamic Formula Calculator | `planned` | P1 |
| LAB-003 | My Reagent Templates | `planned` | P1 |
| LAB-004 | Reagent Preparation | `ui_adapter_needed` | P0 |
| LAB-005 | Western Blot Loading Calculator | `planned` | P1 |
| LAB-006 | SDS-PAGE Gel Preparation | `planned` | P1 |
| LAB-007 | BCA / OD Record | `planned` | P1 |
| LAB-008 | PCR / qPCR Tools | `planned` | P1 |
| LAB-009 | ELISA / Absorbance Tools | `planned` | P1 |
| LAB-010 | Cell Experiment Record Templates | `planned` | P0 |
| LAB-011 | Cell Culture Operation Records | `planned` | P0 |
| LAB-012 | Cell Image Analysis Entry | `shell_only` | P3 |
| LAB-013 | ImageJ/Fiji Callout | `shell_only` | P3 |

`LAB-003` includes the reagent template edit modal / side panel as a child surface rather than adding a 14th top-level screen, so the plan remains aligned with UI-C1a's 13 LabTools screens.

## 6. P0/P1 Wireframe Planning

### 6.1 LabTools Home

Target layout:

- Page header: LabTools / 实验工具, Developer Preview chip, concise module subtitle.
- Three primary cards only: 通用计算器, 试剂制备, 实验模块.
- Experiment module category mini row appears only inside 实验模块.
- Bottom quick access: 最近使用 / 使用指南 / 常见问题 / 意见反馈.
- No ImageJ/Fiji primary card.
- No standalone inventory, collaboration, or image analysis first-level card.

Mockup level: low-to-mid fidelity.

### 6.2 General Calculator

Target layout:

- Left rail: calculation mode list.
- Center: variable input table with unit selectors.
- Right: result summary, formula trace, copy action, recent calculations.
- Warning row for incompatible units or experimental-specialized calculations.

Allowed first version:

- C1V1 dilution
- serial dilution
- mass/concentration/volume
- molarity / normality
- percentage concentration
- RPM / RCF
- unit conversion

Excluded:

- WB loading
- SDS-PAGE
- BCA
- ELISA
- PCR / qPCR
- MTT / CCK-8 / AlamarBlue
- cell seeding
- transfection

### 6.3 Reagent Templates And Template Editor

Target layout:

- Template list with category, name, usage count, last used, status.
- Right detail panel with recipe summary and preparation CTA.
- Edit side panel/modal:
  - template name
  - category
  - target concentration/unit
  - component table
  - storage condition
  - safety/notes
  - validation summary

Rules:

- editing a template is separate from current preparation.
- current preparation cannot directly mutate original template.
- no cloud sync or shared template library.

### 6.4 Reagent Preparation

Target layout:

- Step 1: choose template.
- Step 2: review preparation parameters.
- Step 3: generated preparation sheet.
- Step 4: local preparation record placeholder.
- Right column: blocker/warning rows and recent preparation history.

Key UI components:

- parameter review card
- component amount table
- copy preparation sheet action
- disabled export/report action until backend exists

### 6.5 Cell Experiment Records

Target layout:

- Cell line summary card.
- Operation type selector:
  - passage
  - recovery
  - freezing
  - seeding/plating
  - treatment
  - transfection
- Operation-specific form area.
- Right record preview.
- History table filtered by cell line/date/operator.

Rules:

- seeding/transfection calculations are helpers inside cell operation records.
- no standalone image analysis tab.
- no cloud/LAN collaboration.

## 7. Experiment Module Wireframe Notes

### Protein Experiment

Western Blot should be a workflow, not a single calculator:

```text
Protein sample and quantification
-> WB loading calculation
-> SDS-PAGE gel preparation
-> Lane layout
-> Electrophoresis / transfer record
-> Blocking / antibody incubation record
-> Exposure / image record
-> Band image analysis assist
-> result/export record
```

Mockups in this stage focus on:

- WB loading calculator
- SDS-PAGE gel preparation
- BCA / OD record

### Nucleic Acid Experiment

PCR and qPCR should be separate second-level pages:

- PCR reaction calculation
- PCR program record
- primer selection / primer record
- qPCR reaction calculation
- qPCR 96-well plate layout
- Ct import and ΔCt / ΔΔCt only as future/gated areas

### Immuno / Absorbance

ELISA can be mocked as an MVP boundary page:

- kit/standard/sample information
- plate layout
- OD data table
- blank correction
- standard curve placeholder
- result table placeholder

Do not claim complete curve fitting unless a backend is completed.

## 8. Detailed Mockup Prompts

### Prompt 1: LabTools Home

Create a desktop PySide-style LabTools home mockup for BioMedPilot. Use a light workbench interface with a left global sidebar already implied, a compact page header, and exactly three first-level cards: General Calculator / 通用计算器, Reagent Preparation / 试剂制备, Experiment Modules / 实验模块. Each card has a LabTools icon, status chip, short description, and disabled or shell-only action button. Inside Experiment Modules only, show a small row of five category chips: Cell Experiments, Protein Experiments, Nucleic Acid Experiments, Immuno/Absorbance, IHC. Do not show ImageJ/Fiji, image analysis, inventory, collaboration, or record system as first-level cards. Bottom area has quick access: 最近使用, 使用指南, 常见问题, 意见反馈.

### Prompt 2: General Calculator

Create a low-to-mid fidelity desktop mockup for LabTools General Calculator. Layout: left calculation mode rail, center variable input table with unit selectors, right result summary and recent calculation history. Modes include C1V1 dilution, serial dilution, mass-concentration-volume, molarity/normality, percentage concentration, RPM/RCF, unit conversion. Add a warning row explaining that WB, SDS-PAGE, BCA, ELISA, PCR/qPCR, MTT/CCK-8, cell seeding, and transfection are experiment-specific and not part of the general calculator. Keep visible status chip and text label. Include copy result button and disabled save/export actions.

### Prompt 3: Reagent Template + Preparation Flow

Create a desktop mockup for LabTools reagent workflow. Main view has a template list on the left, selected template detail in the center, and a current preparation panel on the right. Include a side panel/modal for editing a reagent template with template name, category, target concentration, component table, storage condition, safety notes, and validation summary. The current preparation panel must show that the original template is read-only and cannot be edited directly during preparation. Include generated preparation sheet preview, copy button, disabled export, and preparation history empty state.

### Prompt 4: Cell Operation Record Template

Create a desktop mockup for LabTools cell culture operation records. Layout has a cell line summary card, operation type segmented control, operation-specific form, right-side record preview, and bottom history table. Operation types: passage, recovery, freezing, seeding/plating, treatment, transfection. Fields include cell line, passage number, date/time, operator, density, reagent, batch, vessel, split ratio, treatment condition, and notes. Add warning rows for missing cell line or batch information. Do not add image analysis or cloud collaboration.

### Prompt 5: Western Blot / Protein Experiment Step

Create a desktop mockup for a Protein Experiment > Western Blot workflow page. Use a stepper: Protein quantification, WB loading, SDS-PAGE gel, Lane layout, Transfer, Antibody incubation, Exposure/image record, Band analysis assist, Export record. The visible step is WB loading + SDS-PAGE. Show sample concentration table, loading calculator, SDS-PAGE recipe card, lane layout placeholder, and warning rows. Make BCA an upstream protein quantification record, not a general calculator. Image analysis assist is future/gated and points to Settings for ImageJ/Fiji configuration.

## 9. Cannot Implement Now

Do not implement or visually imply active completion for:

- automatic image analysis
- built-in ImageJ/Fiji algorithms
- ImageJ/Fiji as a LabTools first-level page
- complete ELISA curve fitting if no backend exists
- qPCR ΔCt / ΔΔCt processing if no backend exists
- cloud sync
- multi-user collaboration
- LAN sharing
- LIMS integration
- automatic inventory deduction
- automated report/export package

## 10. Follow-Up Stage Recommendation

Recommended next step:

- UI-C1c.1 LabTools mockup image generation or Figma draft for the five prompt groups.

After mockups are approved:

- UI-C2 LabTools shell implementation from approved mockups.

Implementation must remain staged:

1. shell/layout only
2. adapters only where backend exists
3. backend feature work only in a separate LabTools implementation stage

## 11. Verification

| command | result |
|---|---|
| CSV structure check for `docs/ui/UI_C1c_labtools_mockup_screen_specs_20260522.csv` | passed; 13 rows, 21 columns |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 12. This Stage Did Not Modify Runtime

This stage only adds planning documents.

Not modified:

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/**`
- `dist/**`
- App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices
- packaged app
- desktop entry
