# UI-D1a Workbench Design System Component Inventory Audit

Date: 2026-05-24

## 1. Scope

This stage audits the visual gap between the real source-runtime PySide UI and the high-fidelity mockup set, then turns the gap into a product-level component inventory for BioMedPilot.

This stage is documentation-only. It does not modify `app/**`, `tests/**`, or `assets/**`; does not implement components; does not package; does not touch App icon, Finder icon, `.icns`, `Info.plist`, or LaunchServices.

## 2. Evidence Reviewed

Runtime evidence:

- `docs/ui/UI_C5_runtime_ui_screenshot_review_20260524.md`
- `docs/ui/UI_C5_runtime_screenshot_manifest_20260524.csv`
- `docs/ui/runtime_screenshots/20260524/`
- `docs/ui/UI_C5a_runtime_vs_mockup_visual_gap_audit_20260524.md`

Mockup and architecture evidence:

- `/Users/changdali/Desktop/UI/界面示意图/`
- `/Users/changdali/Desktop/UI/界面示意图/labtools/`
- `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/`
- `/Users/changdali/Desktop/UI/界面示意图/Meta/`
- `docs/ui/UI_Visual_Style_Guide_v1_20260520.md`
- `docs/ui/UI_C1b2_bioinformatics_mockup_to_implementation_mapping_20260522.csv`
- `docs/ui/UI_C1c3b_labtools_mockup_to_implementation_mapping_20260522.csv`
- `docs/ui/UI_C1d2_meta_analysis_mockup_to_implementation_mapping_20260522.csv`

Runtime code inspected for current primitive and identity boundaries:

- `app/shell/main_window.py`
- `app/shared/ui_components/primitives.py`
- `app/shared/ui_components/workbench.py`
- `app/app_identity.py`

Observed screenshot dimensions:

- Runtime screenshots are `1600 x 1000`.
- Most top-level high-fidelity mockups are `1536 x 1024`; several dense Bioinformatics mockups are taller (`1402 x 1122`) and result/export mockups vary by page.

The size difference is not the main cause of the gap. The main cause is structural: the runtime UI still uses a mixture of native Qt widgets, local card styles, and page-specific dense layouts where the mockups assume a stable workbench system.

## 3. Overall Audit Finding

The current runtime is safer than the mockups in one important way: it preserves gated semantics and does not show formal computed Bioinformatics or Meta results, fake forest plots, fake report-ready packages, or active formal export.

The visual gap is still too large for product-level sign-off because shared component ownership is incomplete:

- Sidebar, headers, cards, chips, tabs, forms, tables, banners, and disabled actions are implemented across multiple local patterns.
- Dense LabTools, Bioinformatics, Meta, and Settings pages need layout primitives before page polish can converge.
- Existing `app/shared/ui_components/primitives.py` and `app/shared/ui_components/workbench.py` provide a useful starting point, but the catalog is still implementation-thin compared with the mockup system.
- Settings and report/export pages need stricter gate-aware components so diagnostic rows and disabled actions do not look like ordinary user flows.

## 4. Visual Gap by Surface

| Surface | Runtime gap | Target mockup behavior | Component implication |
|---|---|---|---|
| sidebar | Navigation exists, but active state, icon rhythm, and auxiliary entries are not governed by one shell component. | Stable module navigation with compact active state, consistent icon/label alignment, and auxiliary entries separated from primary module flow. | `AppSidebar`, `IconLabel` |
| page header | Titles, subtitles, and status chips vary by page; dense pages lose hierarchy quickly. | Compact page header with title, status row, optional actions, and predictable spacing. | `PageHeader`, `StatusChip`, `InfoBanner` |
| module cards | Dashboard and LabTools cards work functionally but vary in icon scale, card padding, and status placement. | Module entry cards with stable icon/title/body/status/action structure. | `ModuleEntryCard`, `WorkbenchCard` |
| status chips | Status semantics exist, but repeated labels and local sizing make status prominence inconsistent. | Semantic chip tokens with optional status icon, tooltip, fixed height, and identical states across modules. | `StatusChip` |
| tabs | Settings, LabTools, Bioinformatics, and Meta use mixed buttons/lists/tabs for local navigation. | Module-local tabs or stepper controls with clear current/blocked/planned states. | `SecondaryNavTabs`, `WorkflowStepper` |
| tables | Bioinformatics, Meta, and Settings tables are native-looking, clipped, or scroll-heavy. | Dense tables with stable headers, overflow containment, read-only state, and empty/gate states. | `DataTable`, `DenseTablePanel` |
| action buttons | Button roles and disabled states vary; export pages can show enabled-looking open-file controls near disabled export gates. | Role-based actions plus explicit disabled/adapter-needed/gated variants. | `ActionButton`, `DisabledActionButton`, `ExportGatePanel` |
| forms | LabTools and Meta forms use inconsistent label/help/unit/validation layout. | Structured form rows with units, help text, validation, disabled state, and long-label handling. | `FormFieldRow` |
| right summary panels | Gate summaries are absent or page-specific, especially in dense workbench pages. | Fixed-width right summary/gate panel with compact blockers and next safe action. | `RightSummaryPanel`, `KeyValuePanel` |
| empty states | Existing empty states are useful but not consistently separated from warnings and gates. | Illustrated semantic empty state with optional disabled action and no fake data. | `EmptyState`, `ResultPanel` |
| warning/gate banners | Notices are implemented as mixed raw labels, cards, and paragraphs. | Severity-aware banners and gate notices tied to disabled actions. | `InfoBanner`, `WarningList`, `GateNotice` |
| dense workbench layout | Reagent, WB, Bioinformatics analysis/export, original Meta pages, and Settings show clipping or diagnostic density. | Explicit two-column/three-column/list-form-preview/table-panel skeletons with independent scroll regions. | `TwoColumnWorkbench`, `ThreeColumnWorkbench`, `LeftListMiddleFormRightPreview`, `DenseTablePanel` |

## 5. Component Inventory Summary

The detailed inventory is stored in:

- `docs/ui/UI_D1a_workbench_component_inventory_20260524.csv`

Inventory counts:

| Category | Count | Implementation band |
|---|---:|---|
| Core | 10 | UI-D1b |
| Common | 12 | UI-D1c |
| Workbench | 11 | UI-D1d |
| Future | 9 | UI-D1e |
| Total | 42 | UI-D1b to UI-D1e |

Priority distribution:

| Priority | Meaning | Components |
|---|---|---:|
| P0 | Blocks broad visual convergence or semantic safety | 27 |
| P1 | Needed for strong product polish or near-term specialized pages | 13 |
| P2 | Useful for later workflow depth or diagnostics | 2 |

## 6. Category Decisions

### A. Core / 核心基础组件

Core components are the smallest shared primitives required before page-level rebuilds:

- `AppSidebar`
- `PageShell`
- `PageHeader`
- `StatusChip`
- `ActionButton`
- `WorkbenchCard`
- `SectionTitle`
- `IconLabel`
- `EmptyState`
- `InfoBanner`

These should be implemented first because every later component depends on consistent tokens, spacing, status semantics, and disabled-action behavior.

### B. Common / 通用业务组件

Common components express repeated BioMedPilot business UI patterns:

- `ModuleEntryCard`
- `WorkflowStepper`
- `SecondaryNavTabs`
- `DataTable`
- `FormFieldRow`
- `KeyValuePanel`
- `HistoryList`
- `ResultPanel`
- `WarningList`
- `GateNotice`
- `FilePickerButton`
- `DisabledActionButton`

These should not call business services. They should expose safe UI state and properties so pages can preserve current runtime semantics.

### C. Workbench / 高密度工作台组件

Workbench components are the main solution for the current C5/C5a visual gap:

- `TwoColumnWorkbench`
- `ThreeColumnWorkbench`
- `LeftListMiddleFormRightPreview`
- `RightSummaryPanel`
- `SplitterWorkbench`
- `DenseTablePanel`
- `PreviewCard`
- `LaneLayoutPreview`
- `MatrixGrid96Well`
- `ReferenceQueuePanel`
- `ExtractionFormTable`

These components should define layout regions and scroll behavior before individual LabTools, Bioinformatics, or Meta pages are rebuilt.

### D. Future / 后续扩展组件

Future components are specialized enough to wait until Settings, result, export, and later workflow surfaces are ready:

- `ReportViewerShell`
- `ExportGatePanel`
- `PlotPlaceholder`
- `ExternalEngineStatusPanel`
- `SettingsResourceTable`
- `ProjectRecentTable`
- `WizardFlowShell`
- `ReviewConfirmationPanel`
- `AuditLogPanel`

They are included now because the runtime already shows their pressure points, especially Settings diagnostics and report/export gates.

## 7. Semantic Boundaries

All implementation stages derived from this audit must preserve these boundaries:

- Do not enable Bioinformatics or Meta executor paths.
- Do not enable report generation or export.
- Do not make draft/preflight/testing states look like formal results.
- Do not show fake forest plots, DEG tables, report-ready packages, gel bands, band quantification, or export success.
- Do not auto-install, auto-download, auto-update, delete, upload, enable cloud services, or configure external engines.
- Do not touch App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, packaging, `dist/**`, or desktop app overwrite.
- Do not treat icon/resource availability as capability availability.

## 8. Recommended Implementation Order

The resulting implementation sequence is:

1. `UI-D1b`: Core primitives
2. `UI-D1c`: Common business components
3. `UI-D1d`: Workbench dense layout components
4. `UI-D1e`: Settings / Result / Export specialized components
5. `UI-D2`: Dashboard + Settings rebuild
6. `UI-D3`: LabTools rebuild
7. `UI-D4`: Bioinformatics rebuild
8. `UI-D5`: Meta rebuild
9. `UI-D6`: Runtime screenshot re-review

Detailed stage boundaries are documented in:

- `docs/ui/UI_D1a_workbench_design_system_implementation_sequence_20260524.md`

## 9. Verification

Checks expected for this audit stage:

- CSV structure check for `docs/ui/UI_D1a_workbench_component_inventory_20260524.csv`
- `git diff --check`
- `git diff --cached --check`

No package smoke, packaged app runtime, codesign, `dist/**` write, desktop app overwrite, App icon work, or LaunchServices run belongs to this stage.
