# UI-C5b Workbench Layout Primitives Refactor Plan

Date: 2026-05-24

## 1. Goal

Introduce shared PySide workbench layout primitives so BioMedPilot runtime pages can match the high-fidelity mockup structure without repeatedly hand-building dense native layouts.

This plan does not enable any executor, formal result, report, export, packaging, App icon, Finder icon, Info.plist, LaunchServices, or desktop app overwrite.

## 2. Required Primitives

Create shared primitives in the existing UI component layer, preferably under `app/shared/ui_components/`:

- `WorkbenchShell`
  - Owns module-local page composition below the global app sidebar.
  - Provides header, optional status chips, secondary navigation, main content, optional right panel, and action/footer slots.
- `WorkbenchSecondaryNav`
  - Vertical or compact flow navigation.
  - Supports active item, disabled/planned state, semantic keys, and icon fallback.
- `WorkbenchContentArea`
  - Stable scrollable main content region.
  - Prevents hidden pages from participating in layout compression.
- `WorkbenchRightPanel`
  - Gate/summary/inspector region with fixed min/max width.
  - Used for Result/Report/Export gates, local data summary, resource status, and review notices.
- `WorkbenchActionBar`
  - Bottom or section-level action row.
  - Distinguishes primary safe actions, copy-only actions, disabled adapter-needed actions, and blocked actions.

Supporting components:

- `make_workbench_status_row()`
- `make_workbench_card()`
- `make_workbench_section()`
- `make_workbench_notice()`
- `make_workbench_disabled_action()`
- `make_workbench_table()`
- `make_workbench_empty_state()`

## 3. Styling Rules

The primitives should enforce:

- consistent 8 px card radius
- shared margins and spacing
- no nested card-in-card page sections
- dense tables wrapped in a stable table container
- right panel width around 300-360 px where present
- action rows that cannot imply enabled formal report/export unless the button is actually enabled
- status chips with text label preserved
- no icon-only status or gate state

## 4. Migration Order

1. Add primitives without migrating business logic.
2. Add tests for primitive object names, slot composition, disabled button semantics, and scrollable content.
3. Migrate Meta layout first because C5 screenshots already exposed target IA/content overlap.
4. Migrate LabTools Reagent and WB dense pages.
5. Migrate Bioinformatics Analysis Tasks and Result/Export.
6. Migrate Settings hierarchy.
7. Re-run C5g full screenshot review.

## 5. Module-Specific Rules

### Meta

- Preserve 10 main-flow pages + Meta Settings.
- Keep Network Meta planned/disabled.
- Keep no formal pooled effect, forest plot, report-ready package, or export.
- Use secondary nav + central stack + optional RRE right panel.

### LabTools

- Preserve three top-level IA entries.
- Reagent and WB pages should use list/config region, main result region, and right review/gate panel.
- Keep save/export/history boundaries exactly as current adapter stages allow.
- Do not enable BCA/Cell/ELISA/Image Processing save/export.

### Bioinformatics

- Preserve 7-step IA.
- Analysis Tasks should move from table-first to task-card + DEG preflight review layout.
- Result/Export should remove misleading active affordances and use explicit disabled gate panels.
- Formal DEG/ORA/GSEA/KM/Cox/survival/report/export remain disabled.

### Settings

- Separate normal user settings from developer diagnostics.
- Keep external capability detect-first semantics.
- Do not imply ImageJ/Fiji, Cloud AI, local model, PDF/OCR, or external packages are installed/enabled.

## 6. Tests

Required tests after primitive implementation:

- primitives render offscreen
- secondary nav preserves active/disabled/planned states
- right panel does not compress main content
- disabled actions remain disabled and expose `disabledState` / `formalActionEnabled=false`
- status chips preserve labels and semantic keys
- no module regression for Meta/LabTools/Bio/Settings IA
- source smoke passes

## 7. Acceptance Criteria

The primitive refactor is acceptable when:

- Runtime pages can be composed without cross-page overlap.
- Main content and right gate/summary panels have stable proportions at `1600 x 1000`.
- Dense tables no longer force first-viewport horizontal scroll unless the page is intentionally table-only.
- Existing gate semantics remain unchanged.
- C5g screenshots show materially smaller runtime/mockup gaps.
