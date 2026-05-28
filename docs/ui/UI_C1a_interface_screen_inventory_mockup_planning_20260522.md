# UI-C1a Interface Screen Inventory & Mockup Planning

## 1. Scope

This stage inventories real BioMedPilot operation screens that still need design, visual mockups, or implementation calibration after the ordinary UI icon system closure.

Output files:

- `docs/ui/UI_C1a_screen_inventory_20260522.csv`
- `docs/ui/UI_C1a_interface_screen_inventory_mockup_planning_20260522.md`

Strictly deferred:

- UI-B10
- App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices
- packaging / package smoke
- packaged app runtime
- codesigning
- desktop `.app` / desktop entry replacement

This stage does not add business features and does not change Bioinformatics, Meta Analysis, LabTools, Settings, or shared UI gates.

## 2. Inventory Summary

The screen inventory contains 57 screens:

| module | count | main implementation source |
|---|---:|---|
| Bioinformatics | 16 | `app/bioinformatics/project_home.py`, `app/bioinformatics/workspace.py`, `app/bioinformatics/pages/**`, `app/bioinformatics/workflow_pages.py` |
| Meta Analysis | 11 | `app/meta_analysis/workspace.py`, `app/shared/result_report_export_shell.py` |
| LabTools | 13 | `app/shell/main_window.py` |
| Settings | 7 | `app/shell/main_window.py`, `app/shared/settings/**` |
| Shared UI | 10 | `app/shared/ui_components/primitives.py`, `app/shared/result_report_export_shell.py` |

The inventory records current status, route/file, purpose, primary action, inputs, outputs, data state, empty-state needs, warning/gate needs, result preview needs, icon family, mockup priority, implementation priority, and risk level.

## 3. Priority Grouping

### P0: Core Flow Screens

These must be designed first because they define the actual user workflow and gate semantics:

- Bioinformatics project home
- Bioinformatics data source selection
- GEO / local import
- Bioinformatics data check & preparation
- Bioinformatics group & design
- Bioinformatics DEG parameter review and result boundary
- Bioinformatics clinical variable audit
- Meta project home
- Meta search strategy builder
- Meta import/reference management
- Meta screening
- Meta extraction
- LabTools reagent calculator entry
- LabTools reagent preparation
- LabTools cell record template group
- shared warning/blocker/preflight rows
- shared status chip/status row
- shared parameter review card
- shared local file import card

Mockup fidelity: start with low-to-mid fidelity wireframes, then high-fidelity for approved core screens.

Data needs:

- realistic but clearly non-production sample project state
- local file validation examples
- GEO query draft examples
- grouping table examples
- blocker/preflight examples

Required UI structures:

- left navigation
- stepper / flow navigation
- parameter review cards
- local file import card
- readiness table
- warning rows
- status chips
- empty states

### P1: High-Frequency Screens

These should follow P0 once the core layout system is stable:

- TCGA and GTEx data source pages
- ORA/GSEA
- KM/log-rank
- Meta risk of bias
- Meta pairwise input
- LabTools dynamic formula calculator
- reagent templates
- WB loading
- SDS-PAGE
- BCA/OD
- PCR/qPCR
- ELISA/absorbance
- confirmation dialog

Mockup fidelity: low-fidelity first for interaction structure; high-fidelity only after P0 components are stable.

Data needs:

- tables with realistic row lengths
- warning states
- preflight examples
- record-template examples

### P2: Result / Report / Export Screens

These must preserve gating and avoid fake output:

- Bio result browser
- Bio report viewer
- Bio export gate
- Meta result review
- Meta forest plot/table preview
- Meta report-ready gate
- Meta export
- shared result table shell
- shared report shell
- shared export gate shell
- empty states

Mockup fidelity: low-to-mid fidelity first. High-fidelity should wait until approved copy and gate semantics are frozen.

Rules:

- no fake DEG table
- no fake forest plot
- no fake formal statistics
- no fake report-ready package
- disabled/gated export state must remain visually obvious

### P3: Settings / Diagnostics / Auxiliary Screens

These can be designed after core module screens:

- Settings external capabilities
- Settings analysis resources
- Settings models and engines
- local model status
- ImageJ/Fiji configuration
- PDF/OCR resources
- developer diagnostics
- LabTools image-analysis / ImageJ/Fiji callout pages
- quick access cards

Mockup fidelity: low-to-mid fidelity is enough for first pass.

Rules:

- detect-first semantics remain visible
- install/update/cloud actions stay disabled unless current logic allows them
- developer diagnostics should remain visually secondary

### P4: Future / Shell-Only Screens

These should stay shell-only until backend or product decisions mature:

- Meta forest plot/table preview
- LabTools ImageJ/Fiji callout beyond Settings link
- future Cox refinements
- future report-ready transitions
- future export affordances

Mockup fidelity: low-fidelity placeholders only, with clear planned/shell-only states.

## 4. Module Planning Notes

## Bioinformatics

Bioinformatics needs the most immediate design work because it has the largest number of real operation pages and the highest semantic risk.

Recommended UI-C1b scope:

- project home
- data source selection
- local import
- data check & preparation
- group & design
- DEG preflight/result boundary
- clinical variable audit
- result/report/export gate shell

Do not design DEG, ORA/GSEA, survival, clinical association, or export as formal executable production flows. Mockups should keep `preflight_only`, `testing_level`, `blocked`, `draft`, and `imported_external_result` boundaries visible.

## Meta Analysis

Meta Analysis mockups should prioritize flow structure and review states, not production claims.

Recommended UI-C1d scope:

- project home
- question/type entry
- search strategy
- import/reference management
- screening
- full-text/extraction tabs
- risk of bias shell
- result/report gate

Rules:

- AI suggestion is only advisory
- English-only processing boundaries remain
- no Chinese database direct retrieval
- no Chinese PDF extraction
- no Network Meta active flow
- no production-grade systematic review claim

## LabTools

LabTools should move toward record-template mockups and practical calculator layouts.

Recommended UI-C1c scope:

- general reagent calculator
- reagent preparation
- my reagent templates
- cell experiment record templates
- passage/recovery/freezing/seeding/treatment/transfection records
- WB/SDS-PAGE/BCA/PCR/qPCR/ELISA as module-specific screens

Rules:

- do not put WB/PCR/ELISA/MTT into the general calculator
- ImageJ/Fiji remains Settings external capability
- no cloud collaboration or LAN sharing

## Settings / Shared UI

Recommended UI-C1e scope:

- Settings external capabilities
- analysis resources
- models and engines
- developer diagnostics
- shared empty states
- shared warning/blocker/preflight rows
- shared parameter review cards
- shared local file import cards
- shared confirmation dialog

## 5. Mockup Production Guidance

| group | first artifact | high-fidelity need | example data | required UI patterns |
|---|---|---|---|---|
| Bioinformatics P0 | low-to-mid fidelity wireframes | yes after approval | yes | stepper, tables, import cards, preflight rows, status chips |
| Meta Analysis P0 | low-to-mid fidelity wireframes | yes after approval | yes | flow navigation, reference table, screening states, extraction tabs |
| LabTools P0/P1 | low-to-mid fidelity wireframes | yes for record templates | yes | calculators, record forms, parameter cards, status chips |
| Result / Report / Export | low fidelity first | high fidelity after gate copy approval | limited non-fake examples | empty states, disabled export buttons, draft report cards |
| Settings / Shared | low-to-mid fidelity | medium | no production data needed | status rows, resource cards, developer disclosure |

Desktop considerations:

- primary target remains desktop PySide shell
- no mobile layout is required for this stage
- responsive desktop widths should still be considered for long English/Spanish labels
- Chinese UI copy should remain in mockups unless a later i18n stage requests translation work

## 6. Suggested Next Stages

1. UI-C1b Bioinformatics core workflow mockups
2. UI-C1c LabTools record-template mockups
3. UI-C1d Meta Analysis workflow mockups
4. UI-C1e Settings / shared shell mockups
5. UI-C2 Codex implementation from approved mockups

UI-B10 should remain deferred until core operation screens are visually planned and approved.

## 7. Verification

| command | result |
|---|---|
| CSV structure check for `docs/ui/UI_C1a_screen_inventory_20260522.csv` | passed; 57 rows, 19 columns |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 8. This Stage Did Not Modify Runtime

This stage only adds documentation and CSV inventory.

Not modified:

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/**`
- `dist/**`
- App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices
- packaged app
- desktop entry
