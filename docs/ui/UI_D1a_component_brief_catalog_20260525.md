# UI-D1a Component Brief Catalog

Date: 2026-05-25

Purpose: discussion-oriented component briefs for the 42 BioMedPilot UI components identified in UI-D1a. This catalog is for product-owner review before implementation. It is not an implementation plan, not a PySide code change, and not a packaging or runtime-enablement task.

Inputs reviewed:

- `docs/ui/UI_D1a_workbench_design_system_component_inventory_audit_20260524.md`
- `docs/ui/UI_D1a_workbench_component_inventory_20260524.csv`
- `docs/ui/UI_D1a_workbench_design_system_implementation_sequence_20260524.md`
- `docs/ui/UI_Visual_Style_Guide_v1_20260520.md`

Global visual direction: calm biomedical minimal workbench, light neutral surfaces, white cards, subtle borders, compact spacing, clear hierarchy, and semantic color only for real states. Draft, testing, preflight, shell-only, adapter-needed, report-disabled, and export-disabled states must never look like formal results or production success.

## Core / UI-D1b

### 1. AppSidebar

- Category: Core / UI-D1b
- Purpose: Provides the global navigation spine so module entries and auxiliary entries do not drift across pages.
- Visual shape: Fixed-width left rail with product label, primary navigation rows, separated auxiliary rows, compact active state, optional module icons, and Developer Preview footer.
- Typical pages: Dashboard, Settings, LabTools, Bioinformatics, Meta.
- Required states: available, disabled, planned, testing.
- Inputs / properties: items, active_key, item label, nav_key, semantic_key, module_key, icon source, tooltip, callback, usability_role.
- Business boundary: Must not create routes, call module services, open files, enable hidden centers, or imply account/subscription availability.
- Design questions for product owner:
  - Should Dashboard be labelled `Dashboard` or `工作台` in the primary rail?
  - Should auxiliary entries use text only or small icons?
  - How visible should Developer Preview be in the sidebar footer?
  - Should active module color be neutral or module-tinted?
- Priority: P0

### 2. PageShell

- Category: Core / UI-D1b
- Purpose: Standardizes page margins, background, scroll policy, and stable content region for all module pages.
- Visual shape: Neutral page canvas with consistent padding, optional scroll viewport, and controlled spacing between header, content, and footer areas.
- Typical pages: All Dashboard, Settings, LabTools, Bioinformatics, and Meta pages.
- Required states: available, disabled, blocked, planned, testing, shell-only, preflight-only, draft.
- Inputs / properties: module_key, page_key, content widgets, scrollable flag, spacing mode, max width rule, layout_no_overlap flag.
- Business boundary: Must not change routing, project state, executor state, report state, export state, or file-write behavior.
- Design questions for product owner:
  - Should ordinary pages have a max content width or use full workbench width?
  - Should dense pages keep the same margins as Dashboard and Settings?
  - Should page backgrounds be pure neutral or slightly module-tinted?
- Priority: P0

### 3. PageHeader

- Category: Core / UI-D1b
- Purpose: Gives every page a consistent title, subtitle, status row, and optional action area.
- Visual shape: Compact top block with title, one-line or wrapping subtitle, status chips below or to the side, and right-aligned actions only when safe.
- Typical pages: Dashboard, Settings, LabTools, Bioinformatics, Meta.
- Required states: available, blocked, planned, testing, shell-only, preflight-only, draft, adapter-needed.
- Inputs / properties: title, subtitle, module_key, page_key, status widgets, action widgets, icon slot, compact flag.
- Business boundary: Must not introduce production wording, report-ready wording, or executable actions that are not already enabled.
- Design questions for product owner:
  - Should status chips sit under the title or on the right edge?
  - How much bilingual text should appear in headers?
  - Should module icons appear in every page header or only project/module home pages?
- Priority: P0

### 4. StatusChip

- Category: Core / UI-D1b
- Purpose: Standardizes semantic state display so status meaning is not encoded by color alone or local wording.
- Visual shape: Small rounded label with semantic background, border, text color, optional icon, and tooltip for longer explanation.
- Typical pages: All gated modules, Settings resources, result/export gates.
- Required states: available, disabled, blocked, planned, testing, shell-only, preflight-only, draft, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: label, status_key, semantic_key, semantic_state, icon source, tooltip, compact flag.
- Business boundary: Must not treat icon/resource availability as capability availability and must not imply formal readiness from visual color.
- Design questions for product owner:
  - Which states need Chinese-only labels versus bilingual labels?
  - Should available resource chips use green or a quieter neutral-success style?
  - Should report-disabled and export-disabled be separate chip labels?
- Priority: P0

### 5. ActionButton

- Category: Core / UI-D1b
- Purpose: Unifies button role, disabled reason, file-write distinction, and action safety metadata.
- Visual shape: Compact PySide button variants for primary, secondary, ghost, danger, file-picker, and disabled action roles.
- Typical pages: Dashboard cards, module pages, forms, export gates.
- Required states: available, disabled, blocked, planned, testing, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: text, role, size, semantic_state, action_key, enabled, disabled_reason, formal_action_enabled, file_write_allowed.
- Business boundary: Must not call executors, report generators, export writers, installers, uploaders, or cloud services.
- Design questions for product owner:
  - Should blocked actions remain visible as disabled buttons or move into gate notices?
  - What wording should distinguish file-picker from formal export?
  - Which actions deserve primary style in Developer Preview?
- Priority: P0

### 6. WorkbenchCard

- Category: Core / UI-D1b
- Purpose: Provides a shared card surface so repeated items and framed tools use consistent border, radius, padding, and state properties.
- Visual shape: White or near-white panel, subtle border, 8px-or-less radius, no excessive shadow, optional header and content region.
- Typical pages: Dashboard cards, LabTools entries, Bioinformatics cards, Meta cards, Settings panels.
- Required states: available, disabled, blocked, planned, testing, shell-only, draft.
- Inputs / properties: object_name, semantic_state, title, subtitle, content widgets, footer widgets, selected flag.
- Business boundary: Must not turn entire page sections into nested-card stacks or hide gate/blocker semantics.
- Design questions for product owner:
  - Should card density differ between Dashboard cards and dense workbench panels?
  - Should selected cards use border, background, or left accent?
  - Should cards ever use shadows, or borders only?
- Priority: P0

### 7. SectionTitle

- Category: Core / UI-D1b
- Purpose: Creates consistent section hierarchy inside forms, tables, cards, and side panels.
- Visual shape: Compact title with optional helper caption; no decorative blocks unless needed for separation.
- Typical pages: Forms, tables, right panels, Settings groups.
- Required states: available, disabled, blocked, planned, testing.
- Inputs / properties: title, subtitle, semantic_key, density, icon slot, action slot.
- Business boundary: Must not add visible design instructions, fake workflow status, or business logic.
- Design questions for product owner:
  - Should section headings use Chinese-first or bilingual text?
  - Should dense panels use all-caps micro labels or normal title case?
  - Should section titles include icons in Settings resource groups?
- Priority: P1

### 8. IconLabel

- Category: Core / UI-D1b
- Purpose: Standardizes icon plus text alignment, fallback behavior, and semantic metadata.
- Visual shape: Small icon on the left, one or two text lines on the right, fixed icon box, clear fallback if icon is missing.
- Typical pages: Sidebar, module cards, status rows, Settings resource rows.
- Required states: available, disabled, planned, testing, adapter-needed.
- Inputs / properties: text, secondary_text, icon_key, semantic_key, icon_size, fallback flag, tooltip.
- Business boundary: Must not imply capability availability merely because an icon asset exists.
- Design questions for product owner:
  - Should missing icons reserve space or collapse the icon slot?
  - Which icon size should be used in dense tables versus cards?
  - Should module identity icons be colored or monochrome?
- Priority: P1

### 9. EmptyState

- Category: Core / UI-D1b
- Purpose: Separates empty content from warning, blocked, draft, and result states.
- Visual shape: Centered or panel-contained empty state with optional illustration, concise title, body, and optional safe action.
- Typical pages: Dashboard recent projects, Bioinformatics no-result, Meta gates, Settings missing resources.
- Required states: disabled, blocked, planned, shell-only, preflight-only, draft, report-disabled, export-disabled.
- Inputs / properties: title, body, empty_state_key, semantic_key, semantic_state, illustration_size, action label, action disabled reason.
- Business boundary: Must not create fake projects, fake results, fake reports, fake exports, or fake readiness.
- Design questions for product owner:
  - Should empty states use illustrations in dense workbench pages?
  - How much explanatory text is acceptable before it feels like documentation?
  - Should empty states include disabled actions or only point to the next safe step?
- Priority: P0

### 10. InfoBanner

- Category: Core / UI-D1b
- Purpose: Provides consistent notice and warning surfaces without mixing raw labels, cards, and paragraphs.
- Visual shape: Low-height banner with severity-aware border/background, optional title, concise body, and optional action area.
- Typical pages: Developer Preview notices, gate notices, warning/review notices.
- Required states: available, blocked, planned, testing, shell-only, preflight-only, draft, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: title, body, severity, semantic_state, icon slot, action widgets, dismissible flag if later approved.
- Business boundary: Must not soften blockers into success, hide disabled state, or launch actions directly.
- Design questions for product owner:
  - Which severities should exist: info, warning, blocked, success, draft?
  - Should Developer Preview banners be persistent or page-local?
  - Should gate banners own the disabled buttons they explain?
- Priority: P0

## Common / UI-D1c

### 11. ModuleEntryCard

- Category: Common / UI-D1c
- Purpose: Presents a module or LabTools entry consistently with status, description, icon, and one clear navigation action.
- Visual shape: Medium card with icon, title, short description, status chip, and compact entry button.
- Typical pages: Dashboard, LabTools home, experiment module boundary page.
- Required states: available, disabled, blocked, planned, testing, shell-only.
- Inputs / properties: module_key, page_key, title, subtitle, description, icon_key, status_key, action label, callback.
- Business boundary: Must not expose hidden first-level modules, external engines, report center, account, or subscription flows.
- Design questions for product owner:
  - Should module cards show recent activity or stay as pure entry cards?
  - Should disabled modules remain in the card grid?
  - How much status detail belongs on a Dashboard card?
- Priority: P0

### 12. WorkflowStepper

- Category: Common / UI-D1c
- Purpose: Shows workflow progression without confusing draft, blocked, planned, or testing states with completed formal work.
- Visual shape: Vertical or horizontal step list with current marker, status chip, compact description, and disabled future steps.
- Typical pages: Bioinformatics 7-step workflow, Meta 10-step workflow, LabTools reagent/WB flows.
- Required states: available, disabled, blocked, planned, testing, shell-only, preflight-only, draft.
- Inputs / properties: steps, current_key, completed_keys, blocked_keys, status_key, page_key, callback, orientation.
- Business boundary: Must not mark formal analysis/report/export steps complete unless runtime semantics already support it.
- Design questions for product owner:
  - Should Bioinformatics and Meta use the same stepper layout?
  - Should blocked steps be clickable for explanation only?
  - How should draft progress differ visually from completed progress?
- Priority: P0

### 13. SecondaryNavTabs

- Category: Common / UI-D1c
- Purpose: Provides consistent local grouping navigation for Settings and module subpages.
- Visual shape: Compact tab or segmented control with selected state, disabled state, and optional secondary descriptions.
- Typical pages: Settings groups, LabTools calculator/reagent subpages, Bioinformatics auxiliary pages.
- Required states: available, disabled, blocked, planned, testing, shell-only.
- Inputs / properties: tabs, current_key, semantic_key, status_key, enabled, callback, compact mode.
- Business boundary: Must not create new routes, activate hidden modules, or imply disabled tabs are implemented.
- Design questions for product owner:
  - Should Settings use tabs, left local nav, or grouped cards?
  - How should long bilingual tab labels wrap?
  - Should planned tabs be visible or hidden until ready?
- Priority: P0

### 14. DataTable

- Category: Common / UI-D1c
- Purpose: Makes dense scientific and resource tables readable while preserving read-only or gated behavior.
- Visual shape: Bordered table container with stable header, alternating rows, horizontal overflow support, and empty state.
- Typical pages: Bioinformatics readiness/gate matrices, Meta reference/extraction tables, Settings resources, history lists.
- Required states: available, disabled, blocked, planned, testing, preflight-only, draft, adapter-needed.
- Inputs / properties: columns, rows, row status, read_only, min_column_width, empty_state, selected row, sort/filter metadata.
- Business boundary: Must not fetch remote data, execute analysis, edit persisted records, or treat preview rows as formal results.
- Design questions for product owner:
  - Should dense tables prioritize horizontal scroll or column wrapping?
  - Which table actions belong in the table toolbar versus row actions?
  - How prominent should status chips be inside cells?
- Priority: P0

### 15. FormFieldRow

- Category: Common / UI-D1c
- Purpose: Standardizes label, input, unit, help, validation, and disabled state in scientific forms.
- Visual shape: Aligned row with left label/help, right input/control, unit selector or helper text, and validation message.
- Typical pages: LabTools calculators, reagent forms, Meta question/search forms, Settings forms.
- Required states: available, disabled, blocked, planned, testing, adapter-needed.
- Inputs / properties: label, value widget, unit widget, help text, validation message, required flag, disabled reason.
- Business boundary: Must not calculate, validate against backend state, persist data, or modify project records by itself.
- Design questions for product owner:
  - Should labels sit above fields or in a two-column label/control layout?
  - How should unit selectors appear in dense LabTools calculators?
  - Should validation messages use inline text or banners?
- Priority: P0

### 16. KeyValuePanel

- Category: Common / UI-D1c
- Purpose: Summarizes project, gate, or protocol facts without ad hoc label grids.
- Visual shape: Compact panel of key/value rows, optional status chips, muted keys, strong values, and controlled wrapping.
- Typical pages: Dashboard project summary, Bioinformatics project status, Meta protocol summary, right panels.
- Required states: available, blocked, planned, testing, preflight-only, draft, adapter-needed.
- Inputs / properties: items, title, semantic_key, value status, copyable flag, empty fallback.
- Business boundary: Must only display existing state and must not synthesize readiness, counts, reports, or result values.
- Design questions for product owner:
  - Should key/value panels support copy buttons?
  - Which values should be emphasized as primary status?
  - Should missing values show empty text, dash, or status chip?
- Priority: P1

### 17. HistoryList

- Category: Common / UI-D1c
- Purpose: Gives recent, draft, and history surfaces a consistent list pattern.
- Visual shape: Stacked rows with title, timestamp, source, status chip, optional path, and safe action.
- Typical pages: Dashboard recent projects, LabTools preparation history, Bioinformatics logs, Meta draft history.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: items, title, timestamp, source, status_key, action label, empty state, max rows.
- Business boundary: Must not create fake history, fabricate timestamps, or mark adapter-needed records as persisted.
- Design questions for product owner:
  - Should recent projects be a list, table, or compact cards?
  - How many history items should appear before scrolling?
  - Should draft and formal history ever share one list?
- Priority: P1

### 18. ResultPanel

- Category: Common / UI-D1c
- Purpose: Separates calculations, preflight summaries, draft outputs, empty states, and formal result-disabled states.
- Visual shape: Framed panel with title, result semantic chip, content area, optional empty/preview subpanel, and safe actions.
- Typical pages: Bioinformatics result/report, Meta result/report, LabTools calculator output.
- Required states: available, disabled, blocked, planned, testing, preflight-only, draft, report-disabled, export-disabled.
- Inputs / properties: result_type, title, body/content widgets, semantic_state, status_key, actions, provenance text.
- Business boundary: Must not show fake formal DEG, pooled effects, forest plots, report-ready packages, or export success.
- Design questions for product owner:
  - Should testing summaries use the same panel as real future results?
  - How should imported external results differ from BioMedPilot-computed results?
  - Should report draft and result preview be separate panels?
- Priority: P0

### 19. WarningList

- Category: Common / UI-D1c
- Purpose: Makes warnings, blockers, and validation issues scannable instead of scattered paragraphs or table cells.
- Visual shape: List of compact warning rows with severity icon/marker, source, short reason, and optional safe action.
- Typical pages: LabTools WB warnings, Bioinformatics blockers, Meta gate blockers, Settings missing resources.
- Required states: blocked, planned, testing, preflight-only, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: warnings, severity, source, reason, action label, action enabled, disabled reason.
- Business boundary: Must not resolve warnings, run checks, update records, or downgrade blockers visually.
- Design questions for product owner:
  - Should warning rows use icons, colored left borders, or both?
  - Which warnings deserve top-page banners instead of list rows?
  - Should the list group warnings by source or severity?
- Priority: P0

### 20. GateNotice

- Category: Common / UI-D1c
- Purpose: Connects disabled actions to the exact gate or blocker that prevents them.
- Visual shape: Notice panel with gate title, status chip, blocker summary, and disabled action area visually tied to the notice.
- Typical pages: Bioinformatics report/export, Meta report/export, analysis task pages, disabled engine panels.
- Required states: disabled, blocked, planned, testing, preflight-only, draft, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: gate_key, title, status_key, blockers, disabled actions, next safe action, semantic_state.
- Business boundary: Must not enable report/export, executors, engines, installers, or file writes.
- Design questions for product owner:
  - Should gate notices live in right panels or inline above blocked actions?
  - How much detail should be visible before expanding?
  - Should each disabled format button show its own reason?
- Priority: P0

### 21. FilePickerButton

- Category: Common / UI-D1c
- Purpose: Visually separates local path selection/opening from formal export or report generation.
- Visual shape: Secondary or outline button with folder/file icon, local-file wording, and optional path preview nearby.
- Typical pages: LabTools file-picker export pilot, project folder selectors, Settings paths.
- Required states: available, disabled, blocked, planned, adapter-needed.
- Inputs / properties: label, mode, selected_path, enabled, disabled_reason, local_only flag, callback.
- Business boundary: Must not write export artifacts, generate reports, upload files, or imply cloud sync.
- Design questions for product owner:
  - Should file-picker buttons use folder icons consistently?
  - What wording best distinguishes `choose path` from `export`?
  - Should selected paths show inline, tooltip-only, or separate path rows?
- Priority: P1

### 22. DisabledActionButton

- Category: Common / UI-D1c
- Purpose: Makes blocked, planned, adapter-needed, report-disabled, and export-disabled actions explicit and consistent.
- Visual shape: Disabled-looking button with muted text, reason tooltip, and optional adjacent status chip or reason text.
- Typical pages: Report/export formats, formal run buttons, planned Settings actions.
- Required states: disabled, blocked, planned, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: label, action_key, semantic_state, disabled_reason, tooltip, would_write_file flag, would_call_executor flag.
- Business boundary: Must remain non-clickable and must not call business code, write files, or queue hidden work.
- Design questions for product owner:
  - Should disabled actions be buttons or list rows with lock/status markers?
  - Should disabled reason be visible by default or tooltip-only?
  - Should planned and blocked share one disabled style?
- Priority: P0

## Workbench / UI-D1d

### 23. TwoColumnWorkbench

- Category: Workbench / UI-D1d
- Purpose: Standardizes moderate-density pages that need two stable content regions.
- Visual shape: Left/main and right/secondary columns with fixed gutters, responsive minimum widths, and isolated scroll if needed.
- Typical pages: LabTools general calculator, Bioinformatics data source, Settings resource groups.
- Required states: available, disabled, blocked, planned, testing, shell-only, adapter-needed.
- Inputs / properties: left widgets, right widgets, ratio, min widths, scroll policy, module_key, page_key.
- Business boundary: Must not move capabilities between modules or activate hidden pages.
- Design questions for product owner:
  - What column ratio should LabTools calculators use?
  - Should right columns be summary panels or independent work areas?
  - Should two-column pages collapse at smaller widths?
- Priority: P0

### 24. ThreeColumnWorkbench

- Category: Workbench / UI-D1d
- Purpose: Defines dense workbench structure so list, task area, and summary do not compete in one scroll.
- Visual shape: Left list/nav, central work surface, right summary/preview panel, each with stable minimum width.
- Typical pages: LabTools reagent, LabTools WB, Meta screening/extraction, Bioinformatics analysis tasks.
- Required states: available, disabled, blocked, planned, testing, preflight-only, draft, adapter-needed.
- Inputs / properties: left panel, center panel, right panel, widths, scroll isolation, active item, module_key, page_key.
- Business boundary: Must not add persistence, export, formal analysis, or engine execution.
- Design questions for product owner:
  - Should three-column pages always show the right panel?
  - Which column should own primary actions?
  - How should columns behave at 1366px and 1600px widths?
- Priority: P0

### 25. LeftListMiddleFormRightPreview

- Category: Workbench / UI-D1d
- Purpose: Provides a specific dense pattern for selecting an item, editing fields, and previewing draft output.
- Visual shape: Left selectable list, middle form/editor, right preview card or summary, with independent scrolling.
- Typical pages: LabTools reagent templates, Meta extraction forms, Bioinformatics group/design previews.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: list items, selected key, form widgets, preview widget, validation summary, action area.
- Business boundary: Must not save drafts, persist templates, or promote previews to formal inputs without approved adapters.
- Design questions for product owner:
  - Should the preview update live or only after user action?
  - Should the left list show status chips per item?
  - Where should save/adapter-needed actions sit?
- Priority: P0

### 26. RightSummaryPanel

- Category: Workbench / UI-D1d
- Purpose: Keeps gate state, blockers, and next safe action visible without crowding primary content.
- Visual shape: Fixed-width right panel with title, status chips, key/value rows, warning summary, and optional safe action.
- Typical pages: Bioinformatics project/readiness, Meta project/gate summaries, LabTools preparation/WB summaries.
- Required states: available, disabled, blocked, planned, testing, preflight-only, draft, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: title, status items, key/value items, blockers, next action, diagnostics link.
- Business boundary: Must reflect existing runtime state only and must not change gate state or run actions.
- Design questions for product owner:
  - Should right panels be sticky while center content scrolls?
  - What width is acceptable for Chinese and English labels?
  - Should right panels include developer diagnostics links?
- Priority: P0

### 27. SplitterWorkbench

- Category: Workbench / UI-D1d
- Purpose: Supports source/detail review where users need adjustable space between related regions.
- Visual shape: Resizable split panes with minimum sizes, neutral divider, and stable default ratio.
- Typical pages: Meta full-text/detail review, Bioinformatics source/detail review, future report viewer.
- Required states: available, disabled, blocked, planned, testing, draft.
- Inputs / properties: panes, default sizes, min sizes, orientation, selected item, persistence disabled or later-approved.
- Business boundary: Must not persist splitter state into project data or alter reviewer decisions.
- Design questions for product owner:
  - Which workflows actually need user-resizable panes?
  - Should splitters remember layout per session?
  - Should the divider be visually prominent or nearly invisible?
- Priority: P1

### 28. DenseTablePanel

- Category: Workbench / UI-D1d
- Purpose: Wraps dense data tables with toolbar, filters, status, overflow handling, and empty state.
- Visual shape: Table container with compact title/toolbar, filter/search placeholder, status chips, and scroll-safe table area.
- Typical pages: Bioinformatics analysis tasks, Bioinformatics readiness tables, Settings resource table, Meta reference queues.
- Required states: available, disabled, blocked, planned, testing, preflight-only, draft, adapter-needed.
- Inputs / properties: title, table columns, rows, filters, search placeholder, toolbar actions, empty state, read_only flag.
- Business boundary: Must not execute searches, fetch remote records, run analysis, or write edits unless later explicitly wired.
- Design questions for product owner:
  - Should filters be visible by default or collapsed?
  - How should table panels handle very long scientific headers?
  - Should dense table panels show row counts prominently?
- Priority: P0

### 29. PreviewCard

- Category: Workbench / UI-D1d
- Purpose: Makes draft/preflight previews visually distinct from formal result or report output.
- Visual shape: Framed preview with label, semantic chip, muted background if draft, and clear non-final watermark or marker.
- Typical pages: LabTools reagent preparation sheet, WB lane preview, Meta query/report previews, Bio result preview.
- Required states: disabled, blocked, planned, testing, shell-only, preflight-only, draft, adapter-needed, report-disabled.
- Inputs / properties: title, preview content, semantic_state, status_key, provenance, actions, empty fallback.
- Business boundary: Must not show fake gel bands, fake plots, fake reports, or formal computed result visuals.
- Design questions for product owner:
  - Should previews use a watermark like `Draft preview`?
  - Should preflight previews and draft report previews look different?
  - Should preview actions be copy-only in early stages?
- Priority: P1

### 30. LaneLayoutPreview

- Category: Workbench / UI-D1d
- Purpose: Provides a safe WB lane schematic without implying image analysis or generated gel output.
- Visual shape: Horizontal lane grid with lane numbers, sample labels, volumes, warning markers, and no band imagery.
- Typical pages: LabTools WB Loading.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: lanes, lane label, sample name, loading volume, marker lane, warnings, selected lane.
- Business boundary: Must not show fake gel bands, band quantification, antibody recommendation, or image-analysis execution.
- Design questions for product owner:
  - How many lanes should be visible before horizontal scrolling?
  - Should warnings appear inside lanes or below the schematic?
  - Should marker lanes use a distinct visual treatment?
- Priority: P0

### 31. MatrixGrid96Well

- Category: Workbench / UI-D1d
- Purpose: Establishes a safe grid pattern for future plate-based LabTools workflows.
- Visual shape: 8x12 grid with row/column labels, selection states, legend, and compact metadata area.
- Typical pages: LabTools BCA/OD future, cell experiment workspace future.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: wells, row labels, column labels, selected wells, state per well, legend, disabled reason.
- Business boundary: Must not enable ELISA/4PL, formal quantification, clinical interpretation, or export before approved backend scope.
- Design questions for product owner:
  - Should well states use color, symbols, or both?
  - How should replicate groups be shown?
  - Should 96-well grids be editable in the first implementation?
- Priority: P1

### 32. ReferenceQueuePanel

- Category: Workbench / UI-D1d
- Purpose: Gives Meta reference queues a stable review layout with draft/manual decision semantics.
- Visual shape: Queue list or lanes, selected reference summary, detail preview, decision controls, and advisory status markers.
- Typical pages: Meta screening, Meta import/dedup, full-text management.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: references, selected_reference, queue state, decision draft, reason options, AI advisory flag.
- Business boundary: Must not make final inclusion decisions, auto-merge duplicates, auto-import online databases, or turn AI suggestions into decisions.
- Design questions for product owner:
  - Should screening use queue lanes or a table plus detail panel?
  - How should AI advisory text be visually separated from reviewer decisions?
  - Should draft counts be visible in the queue header?
- Priority: P0

### 33. ExtractionFormTable

- Category: Workbench / UI-D1d
- Purpose: Supports type-specific extraction and quality-assessment fields without page-level ad hoc tables.
- Visual shape: Structured table/form hybrid with section groups, field labels, value cells, validation rows, and draft marker.
- Typical pages: Meta full-text/extraction, quality assessment, future evidence tables.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: schema sections, fields, values, validation messages, reviewer state, draft save action, read_only flag.
- Business boundary: Must not auto-extract PDFs, make final ROB judgments, compute pooled effects, or promote draft data to formal analysis input.
- Design questions for product owner:
  - Should extraction fields appear as table rows or grouped form sections?
  - How should type-specific schemas be distinguished visually?
  - Should validation appear per field or as a summary panel?
- Priority: P0

## Future / UI-D1e

### 34. ReportViewerShell

- Category: Future / UI-D1e
- Purpose: Creates a read-only shell for report drafts and future report views without implying report readiness.
- Visual shape: Viewer frame with section navigation, draft/status chip, content preview, and disabled export gate area.
- Typical pages: Bioinformatics result/report, Meta result/report, future report preview.
- Required states: disabled, blocked, planned, testing, draft, report-disabled, export-disabled.
- Inputs / properties: sections, active section, report_status, draft content, provenance, disabled actions.
- Business boundary: Must not generate reports, mark report-ready, export files, or create report artifacts.
- Design questions for product owner:
  - Should draft reports use document-like pages or workbench panels?
  - Should report section navigation be left or top?
  - How should report-ready future status be represented before it exists?
- Priority: P1

### 35. ExportGatePanel

- Category: Future / UI-D1e
- Purpose: Makes report/export readiness and disabled format actions one coherent gate surface.
- Visual shape: Gate card with readiness checks, artifact presence state, disabled format buttons, and open-file controls only when safe.
- Typical pages: Bioinformatics Report Export, Meta Report Export Gate, LabTools export pilot boundaries.
- Required states: disabled, blocked, planned, testing, draft, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: gate_key, readiness checks, artifact exists flag, formats, disabled reasons, open actions, export policy.
- Business boundary: Must not enable DOCX/HTML/PDF/CSV/XLSX/ZIP export or report package generation.
- Design questions for product owner:
  - Should all export formats show at once when disabled?
  - How should open-file/open-folder actions behave when no artifact exists?
  - Should LabTools pilot exports use the same gate as formal report exports?
- Priority: P0

### 36. PlotPlaceholder

- Category: Future / UI-D1e
- Purpose: Prevents planned chart areas from looking like real analysis output.
- Visual shape: Empty chart frame with placeholder label, semantic chip, explanatory text, and no fake axes/data unless explicitly allowed later.
- Typical pages: Bioinformatics result/report, Meta result/report, LabTools image-analysis futures.
- Required states: disabled, blocked, planned, testing, preflight-only, draft, report-disabled.
- Inputs / properties: plot_type, title, semantic_state, message, required inputs, future availability label.
- Business boundary: Must not show fake forest plots, volcano plots, survival curves, gel bands, publication-bias charts, or formal chart results.
- Design questions for product owner:
  - Should placeholders show abstract chart skeletons or no chart geometry?
  - Which plot types need unique placeholder copy?
  - Should planned plot placeholders be visible on first release pages?
- Priority: P1

### 37. ExternalEngineStatusPanel

- Category: Future / UI-D1e
- Purpose: Shows detect-only status for engines/resources without turning Settings into an installer.
- Visual shape: Grouped panel with engine icon, status chip, path/version rows, detect action, and disabled install/configure actions.
- Typical pages: Settings external engines, LabTools image analysis, Bioinformatics/Meta analysis resources.
- Required states: available, disabled, blocked, planned, testing, adapter-needed.
- Inputs / properties: engine_key, label, version, path, status_key, detect action, configure action, disabled reason.
- Business boundary: Must not install, update, delete, upload, enable cloud, configure API keys, or execute engines.
- Design questions for product owner:
  - Should engines be grouped by module or capability type?
  - Should unavailable engines show install guidance or only status?
  - How visible should cloud AI planned state be?
- Priority: P1

### 38. SettingsResourceTable

- Category: Future / UI-D1e
- Purpose: Reworks resource rows into user-oriented groups while keeping diagnostics separate.
- Visual shape: Grouped table with resource name, status, path/version, last check, safe action, and collapsed diagnostics.
- Typical pages: Settings external resources, developer diagnostics.
- Required states: available, disabled, blocked, planned, testing, adapter-needed.
- Inputs / properties: resources, group label, status_key, path, version, action policy, diagnostics payload.
- Business boundary: Must not auto-download, install, update, delete, configure cloud, or imply resource availability enables analysis.
- Design questions for product owner:
  - Which resource groups belong in ordinary Settings versus Developer Diagnostics?
  - Should resource paths be visible by default?
  - Should failed detections be warning rows or separate diagnostics?
- Priority: P0

### 39. ProjectRecentTable

- Category: Future / UI-D1e
- Purpose: Gives recent project surfaces a stable scan pattern without turning Dashboard into Project Center.
- Visual shape: Compact table/list with project name, module, path, last opened, status, and open action.
- Typical pages: Dashboard recent projects, project home summaries.
- Required states: available, disabled, blocked, planned, draft.
- Inputs / properties: project records, module_key, path, last_opened, status_key, open callback, empty state.
- Business boundary: Must not create fake project records, run migrations, scan disks unexpectedly, or expand Dashboard into a full Project Center.
- Design questions for product owner:
  - Should recent projects appear as cards or table rows?
  - How many recent projects should be shown on Dashboard?
  - Should missing paths remain visible with a warning?
- Priority: P1

### 40. WizardFlowShell

- Category: Future / UI-D1e
- Purpose: Provides a constrained pattern for future guided workflows that should not become freeform dense pages.
- Visual shape: Step title, progress indicator, main step body, validation summary, back/next/cancel actions.
- Typical pages: Future onboarding, guided import, long LabTools workflows.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed.
- Inputs / properties: steps, current_step, validation state, next/back callbacks, cancel policy, disabled reasons.
- Business boundary: Must not bypass adapters, gates, reviewer confirmation, or user confirmation requirements.
- Design questions for product owner:
  - Which workflows deserve wizard treatment instead of workbench treatment?
  - Should wizard steps save drafts automatically?
  - Should validation block next-step navigation or only warn?
- Priority: P2

### 41. ReviewConfirmationPanel

- Category: Future / UI-D1e
- Purpose: Makes reviewer confirmation, draft/final distinction, and blockers explicit.
- Visual shape: Confirmation panel with status chip, decision summary, blocker list, reviewer action, and disabled/final-state warning.
- Typical pages: Meta screening, Meta extraction, Bioinformatics group/design, export gates.
- Required states: available, disabled, blocked, planned, testing, draft, adapter-needed, report-disabled, export-disabled.
- Inputs / properties: decision_state, reviewer label, confirmation text, blockers, action label, disabled reason, finalization policy.
- Business boundary: Must not convert draft reviewer actions into final decisions or formal analysis/report readiness.
- Design questions for product owner:
  - What visual language distinguishes draft confirmation from final confirmation?
  - Should confirmation require a checkbox, typed confirmation, or simple button?
  - Which workflows need audit trail display in the panel?
- Priority: P1

### 42. AuditLogPanel

- Category: Future / UI-D1e
- Purpose: Keeps logs and diagnostics available without polluting ordinary user workflows.
- Visual shape: Collapsible panel with timestamped log rows, source filters, copy diagnostics action, and muted technical styling.
- Typical pages: Developer diagnostics, project logs, export/report trace.
- Required states: available, disabled, blocked, planned, testing, draft.
- Inputs / properties: entries, source, level, timestamp, collapsed flag, copy action, export diagnostics action if later approved.
- Business boundary: Must not package, run LaunchServices checks, generate reports, export traces, or expose diagnostics as ordinary workflow status.
- Design questions for product owner:
  - Should audit logs be visible to normal users or Developer Diagnostics only?
  - Should logs support copy only or future export diagnostics?
  - How much technical detail should be shown by default?
- Priority: P2

## Coverage Summary

| Category | Stage | Components |
|---|---|---:|
| Core | UI-D1b | 10 |
| Common | UI-D1c | 12 |
| Workbench | UI-D1d | 11 |
| Future | UI-D1e | 9 |
| Total | UI-D1b to UI-D1e | 42 |

## Review Notes

- This catalog intentionally asks product/design questions before implementation.
- Component briefs describe expected PySide parameters but do not define classes, functions, imports, tests, or runtime wiring.
- No component should call executors, external engines, downloaders, uploaders, cloud services, report generators, or export writers.
- No component should make draft, preflight, testing, shell-only, adapter-needed, report-disabled, or export-disabled states look like formal results.
