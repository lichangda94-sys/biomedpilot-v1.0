# UI-D1a Workbench Design System Implementation Sequence

Date: 2026-05-24

## 1. Purpose

This document converts the UI-D1a component inventory into the implementation order for later stages. It is a planning artifact only. It does not modify runtime UI, implement components, package the app, enable executors, enable report/export, or touch App icon / Finder / `Info.plist` / LaunchServices.

Source inventory:

- `docs/ui/UI_D1a_workbench_component_inventory_20260524.csv`

## 2. Fixed Sequence

| Stage | Goal | Primary components | Runtime pages to inspect after implementation | Hard boundary |
|---|---|---|---|---|
| UI-D1b | Core primitives | `AppSidebar`, `PageShell`, `PageHeader`, `StatusChip`, `ActionButton`, `WorkbenchCard`, `SectionTitle`, `IconLabel`, `EmptyState`, `InfoBanner` | Dashboard, Settings, LabTools home, Bioinformatics project home, Meta project home | No page rebuild beyond primitive adoption; no business enablement |
| UI-D1c | Common business components | `ModuleEntryCard`, `WorkflowStepper`, `SecondaryNavTabs`, `DataTable`, `FormFieldRow`, `KeyValuePanel`, `HistoryList`, `ResultPanel`, `WarningList`, `GateNotice`, `FilePickerButton`, `DisabledActionButton` | Bioinformatics workflow pages, Meta target IA pages, LabTools calculator/reagent pages, report/export gates | Components must remain service-free and must not call executors or file export |
| UI-D1d | Dense workbench layouts | `TwoColumnWorkbench`, `ThreeColumnWorkbench`, `LeftListMiddleFormRightPreview`, `RightSummaryPanel`, `SplitterWorkbench`, `DenseTablePanel`, `PreviewCard`, `LaneLayoutPreview`, `MatrixGrid96Well`, `ReferenceQueuePanel`, `ExtractionFormTable` | LabTools reagent/WB, Bioinformatics analysis tasks, Meta screening/extraction, dense Settings tables | Layout skeletons only; no fake plots, no fake gel bands, no final reviewer decisions |
| UI-D1e | Specialized Settings / Result / Export components | `ReportViewerShell`, `ExportGatePanel`, `PlotPlaceholder`, `ExternalEngineStatusPanel`, `SettingsResourceTable`, `ProjectRecentTable`, `WizardFlowShell`, `ReviewConfirmationPanel`, `AuditLogPanel` | Settings, Bioinformatics result/export, Meta result/export, dashboard recent projects | Export and report controls stay disabled unless a future explicit backend stage enables them |
| UI-D2 | Dashboard + Settings rebuild | Core + Common + Settings specialized components | Dashboard, Settings | Keep Dashboard as module entry, not Project Center; keep diagnostics collapsed |
| UI-D3 | LabTools rebuild | Core + Common + Workbench LabTools components | LabTools home, calculator, reagent, WB, experiment boundaries | Do not enable ImageJ/Fiji execution, fake gel output, ELISA/4PL, or formal report/export |
| UI-D4 | Bioinformatics rebuild | Core + Common + Workbench Bioinformatics components | Project home, data source, data check, group/design, analysis tasks, result/report, report export | Do not enable DEG/ORA/GSEA/KM/Cox/clinical formal execution or formal export |
| UI-D5 | Meta rebuild | Core + Common + Workbench Meta components | Project home, question/type, search, import/dedup, screening, full-text/extraction, QA, analysis tasks, result/report, export | Do not enable Network Meta, production systematic review claims, pooled effects, forest plots, or report-ready export |
| UI-D6 | Runtime screenshot re-review | No new component scope unless re-review finds blockers | Full source-runtime screenshot set | Review only; packaging and UI-B10 remain separate |

## 3. Stage Detail

### UI-D1b: Core primitives

Implementation target:

- Establish the component contracts that pages can adopt without changing business behavior.
- Align primitive styling with `app/ui_style_tokens.py` and existing semantic keys.
- Keep primitive APIs explicit about disabled, planned, testing, shell-only, preflight-only, blocked, draft, and available states.

Acceptance checks:

- Existing runtime smoke still passes.
- No new executor, report, export, installation, cloud, or packaging path is reachable.
- Sidebar/header/chip/button/card/empty/banner examples can be rendered in at least one safe page or isolated test surface.

### UI-D1c: Common business components

Implementation target:

- Standardize repeated business UI patterns without owning business services.
- Replace local table/form/gate/action patterns only where doing so preserves existing state and behavior.
- Add disabled-action reason fields and semantic properties so future pages cannot accidentally make gated actions look enabled.

Acceptance checks:

- Tables remain read-only unless an existing adapter already permits editing.
- File picker controls are visually distinct from formal export/report actions.
- Gate notices control adjacent disabled action display consistently.

### UI-D1d: Workbench dense layout components

Implementation target:

- Solve the structural C5a gap by defining reusable two-column, three-column, split, list-form-preview, and table-panel layouts.
- Give dense pages independent scroll regions and fixed summary/preview widths.
- Make preview components visibly draft/preflight/shell-only when they are not formal output.

Acceptance checks:

- LabTools reagent and WB pages can fit their primary regions without horizontal clipping at the current review viewport.
- Bioinformatics analysis-task tables and Meta reference/extraction views have clear table/list/detail boundaries.
- Lane, plot, and extraction previews cannot be mistaken for completed analysis outputs.

### UI-D1e: Settings / Result / Export specialized components

Implementation target:

- Address Settings diagnostic density and report/export gate ambiguity.
- Create specialized components only after Core/Common/Workbench contracts exist.
- Bind export/open-file actions to artifact existence and gate state instead of placing them as standalone buttons.

Acceptance checks:

- Settings first viewport is user-oriented, with diagnostics collapsed or clearly separated.
- Export format actions remain disabled under disabled gates.
- Result/report surfaces explicitly separate draft/preflight/empty from formal result/report-ready states.

## 4. Page Rebuild Order After D1

### UI-D2: Dashboard + Settings rebuild

Rationale:

- Dashboard and Settings are the highest-traffic shell pages.
- Settings currently has the most user-facing hierarchy gap because resource diagnostics dominate the first viewport.
- Rebuilding these first validates the Core/Common/Specialized components before domain-heavy pages consume them.

Do not:

- Turn Dashboard into Project Center.
- Expose account/subscription/purchase flows.
- Auto-detect or configure external engines beyond existing safe detection semantics.

### UI-D3: LabTools rebuild

Rationale:

- LabTools reagent and WB pages are among the clearest dense-layout failures.
- LabTools can validate workbench list/form/preview and warning-list components without touching Bioinformatics or Meta executors.

Do not:

- Show fake gel bands or image-analysis output.
- Enable ImageJ/Fiji execution.
- Enable ELISA/4PL or formal report/export.
- Convert adapter-needed save/export boundaries into production persistence.

### UI-D4: Bioinformatics rebuild

Rationale:

- Bioinformatics needs table, gate, result-panel, and export-panel consistency.
- Analysis Tasks and Report Export need strong disabled/gated visual ownership.

Do not:

- Enable formal DEG, ORA, GSEA, survival, clinical, or external statistical executor paths.
- Show fake result tables, plots, or report-ready packages.
- Treat preflight logs as formal analysis results.

### UI-D5: Meta rebuild

Rationale:

- Meta uses the widest workflow and needs the most consistent stepper, reference queue, extraction table, and report/export gate behavior.
- Earlier C5b local polish reduced overlap, but D5 should rebuild from shared components rather than stacking more local patches.

Do not:

- Enable Network Meta as an active type.
- Turn AI suggestions into automatic reviewer decisions.
- Show formal pooled effects, heterogeneity, forest plots, publication-bias results, final PRISMA counts, or report-ready export.

### UI-D6: Runtime screenshot re-review

Rationale:

- D6 is the first point where the rebuilt source-runtime UI should be compared again against the high-fidelity mockups.
- It should use the same source-runtime screenshot discipline as C5.

Expected verification:

- Capture source-runtime screenshots at the current review viewport.
- Confirm screenshots are non-empty and non-blank.
- Compare Dashboard, Settings, LabTools, Bioinformatics, and Meta against approved mockups.
- Re-check that no formal executor/report/export/App icon/packaging/LaunchServices surface was enabled by UI work.

## 5. Cross-Stage Rules

- Keep `app_identity.py` semantics authoritative for icons and status-resource meaning.
- Keep status semantic keys authoritative over visual color or icon.
- Keep disabled/gated actions non-clickable unless a future explicit implementation stage changes the underlying business capability.
- Prefer shared components over page-local styles once a D1 component exists.
- Do not use UI polish to change business state, write files, call engines, generate reports, or package the app.

## 6. Verification for UI-D1a

This document belongs to the UI-D1a audit stage. Verification for this stage is limited to:

- CSV structure check
- `git diff --check`
- `git diff --cached --check`

No runtime UI change, screenshot recapture, packaging, App icon work, Finder work, `Info.plist` work, LaunchServices run, executor enablement, report generation, or export enablement is part of UI-D1a.
