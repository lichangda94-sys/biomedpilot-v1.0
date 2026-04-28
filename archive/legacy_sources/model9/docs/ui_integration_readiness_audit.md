# UI Integration Readiness Audit

## Current Conclusion

Current branch: `feature/unified-workbench-shell`.

Current recommendation:

- Do not continue submitting UI behavior changes on this branch right now.
- Do not merge the Workbench shell branch into `main` right now.
- Wait until the core feature chain is more stable before making the unified shell the default application entry.
- Keep the existing UI branch as a reference branch for later integration planning.

The branch already contains a UI shell commit that changes `app/main_window.py` startup behavior to show the new Workbench stack. This audit records that state only; it does not roll back, merge, or further refactor the UI.

## Branch Snapshot

- Current branch: `feature/unified-workbench-shell`.
- Audited base HEAD before this roadmap update: `18e02e9 docs: record UI integration readiness audit`.
- Recent local commit line:
  - `18e02e9 docs: record UI integration readiness audit`
  - `3e6d212 test(ui): add stable Qt test helper`
  - `9b94972 feat(ui): add unified workbench and bioinformatics workspace shell`
  - `40935a8 docs: document GSE27155 readiness benchmark`
  - `be64579 feat(module3): map embedded GEO SOFT platform annotations`
  - `b655d49 feat(module3): add GEO SOFT expression report`
  - `28e6428 docs: record GSE27155 SOFT readiness inspection`
  - `d42f6a5 feat(module5): refine GSE27155 group detection`
  - `2751afe feat(module3): add GEO SOFT metadata harness support`
  - `710e6a8 docs: document GSE60542 readiness baseline`

## Test Baseline Clarification

The current full pytest baseline on this branch is `491 passed`.

This is lower than the previous profile readiness mainline baseline of `736 passed` because this checkout is on a different branch and commit line. The profile readiness/reporting commits, including later work such as row-level policy readiness reasons, are present on `dev` but are not contained in `feature/unified-workbench-shell`.

This audit does not merge, cherry-pick, or reconcile those lines. It only records that future UI integration must explicitly decide how the Workbench shell branch will consume the profile readiness/reporting service work.

## Current UI Assets

### Stable Existing UI

These files exist on `main` and are tied to current behavior and tests:

- `app/main_window.py`: current desktop entry and reporting/task control surface. On this branch it has been changed to launch the Workbench stack, so this is the primary future merge risk.
- `app/reporting_summary_widget.py`: existing reporting summary table widget backed by reporting service outputs and tested by `tests/test_reporting_summary_widget.py`.
- `app/task_results_summary_widget.py`: existing task result, artifact, task plan, execution log, and readiness summary widget backed by task management models and tested by `tests/test_task_results_summary_widget.py`.
- `app/bootstrap.py`, `app/__main__.py`: application startup wrappers. These should stay stable while UI integration planning continues.

The current `main` app package does not contain separate `screening_widget.py`, `extraction_widget.py`, `analysis_widget.py`, or broader Meta workflow widgets. Those domains exist mainly as service/model modules in this branch line, not as mounted desktop pages.

### New UI Shell / Future Integration Candidates

These files were added by the Workbench shell branch and should remain candidates, not immediate replacements:

- `app/workbench_home_widget.py`: unified Workbench landing page with Bioinformatics and Meta Analysis entry cards and mock status sections.
- `app/project_shell_widget.py`: shared project workspace shell with top header, left navigation, stacked pages, and bottom mock status.
- `app/bioinformatics_workspace_widget.py`: Bioinformatics shell home with mock statistics, Volcano / Heatmap placeholders, recent results, flow, messages, and disabled settings panel.
- `app/meta_analysis_workspace_widget.py`: Meta Analysis placeholder shell.
- `tests/test_workbench_shell.py`: branch-level UI tests for Workbench entries, shell navigation, and title changes.

These files are useful for future UI convergence but should not be merged until default-entry behavior, fallback routing, and old UI access are decided.

### Implemented Shell Capabilities

- Unified Workbench startup surface.
- Bioinformatics workspace shell with left navigation, status-like cards, and placeholder analysis sections.
- Meta Analysis workspace placeholder shell.
- Shared project shell widget and route model.
- Headless Qt test helper for stable widget tests.

### Not Yet Connected

- Full user-facing project open/create/save controls. A manifest-based project state layer and explicit `MainWindow` methods now exist.
- Full profile readiness/reporting read-only panel from the profile readiness mainline. A compatible project-local `profile_readiness.json` read-only panel now exists.
- `ProfileReportService`, policy summary dashboard, and row-level policy reason tables from the profile readiness line.
- Full demo project browser. A local demo Meta readiness project seeder now exists.
- Full profile row CSV template import/export. Initial templates exist for treatment effect, diagnostic accuracy, and biomarker prevalence/association.
- Production profile row editing UI. A minimum template-driven editor exists without persistence or execution actions.
- Existing Meta analysis workflow pages inside the Workbench shell.

### Pure Logic UI Supporting Model

These files can be reused with lower integration risk:

- `app/project_navigation_model.py`: pure Python navigation model with no PySide6 dependency. This is suitable for keeping as a tested contract for future shell navigation.
- `app/ui_style_tokens.py`: shared visual token and stylesheet definitions. Reusable, but should be adopted gradually to avoid changing stable widgets unexpectedly.
- `tests/test_project_navigation_model.py`: pure logic tests for Bioinformatics and Meta Analysis navigation lists.

### Test / Environment Support

- `tests/conftest.py`: branch-level pytest setup for headless Qt runs.
- `tests/qt_test_utils.py`: branch-level stable Qt test helper introduced after the Workbench shell commit.

These are not product UI files, but they reduce PySide6/headless test instability and should be evaluated separately from shell UI behavior.

### Local Manual Test Data

- Former untracked `tests/pubmed/` PubMed CSV/TXT data was reviewed for test and code references. No test or product code references were found.
- The PubMed files were moved to ignored local data under `manual_test_data/pubmed/` instead of being cropped into fixtures or committed.
- Any future UI files from active feature branches should be compared against this branch before merge to avoid overwriting newer functional work.

## Main-Line Protection Check

### `main_window.py` Entry Conflict

On this branch, `app/main_window.py` imports the new Workbench shell widgets and sets the central widget to `mainWorkbenchStack`. Startup title is switched to `BioMedPilot · 研究分析平台`.

This means the branch already changes the default desktop entry. That should not be merged into `main` until a fallback plan exists.

### Current Startup Entry

The branch startup entry is the new Workbench home. The prior reporting/task controls are still instantiated as `_legacy_reporting_task_widget`, but they are not mounted as the visible central widget.

### Existing Meta Analysis Main Chain Access

This branch has a Meta Analysis placeholder shell only. It does not mount a real Meta workflow page chain. Because the current app package does not expose separate Meta workflow widgets on `main`, future integration needs an explicit mapping from services/pages to shell routes.

### Reporting / Task / Analysis Preservation

Reporting and task summary widgets are still present and methods remain on `MainWindow`, but the old control surface is not visibly reachable through the central widget on this branch. That is acceptable for a prototype branch, but risky for a direct merge.

### Test Status

The latest recorded branch validation passed on this branch:

- `git diff --check`: pass.
- `./.venv/bin/python -m pytest -q`: `491 passed`.

The profile readiness/reporting line has a later `736 passed` baseline, but that number belongs to a different commit line. It should not be treated as the expected count on this branch until the branches are intentionally integrated.

## Future Integration Principles

- Treat the new UI shell as an outer container first; do not let it call analysis functions directly.
- Use view models or service adapters to expose state to UI widgets.
- Connect read-only state before enabling action buttons.
- First expose project status, data assets, task status, and output files.
- Add real execution actions only after readiness, preflight, and task lifecycle states are visible.
- Keep mock values clearly labeled until replaced by service-backed values.
- Keep the old UI surface available as a fallback until the new shell passes full workflow tests.

## Suggested Integration Order

1. Stabilize the unified Workbench shell as an optional or explicitly selected entry, not as an immediate default replacement. Minimum implementation completed.
2. Connect project navigation and project open/create/save state through a read-only project shell contract. Minimum implementation completed through project manifests and explicit methods.
3. Connect the profile readiness read-only panel from the profile readiness/reporting line. Minimum compatible implementation completed through project-local readiness JSON.
4. Add a demo project loader for controlled internal application testing. Minimum implementation completed.
5. Add profile row CSV template import/export. Minimum implementation completed for three priority profiles.
6. Add the smallest useful profile row editing UI. Minimum implementation completed as a template-driven table.
7. Migrate existing functional pages into the Workbench shell one page at a time.
8. Preserve old UI fallback during migration.
9. Run full workflow, reporting, and headless Qt tests before considering a default-entry switch.

## Risk List

- `main_window.py` default-entry conflict between old functional UI and new shell.
- Duplicate navigation between old UI pages and new shell routes.
- Mock data being mistaken for real scientific results.
- Placeholder buttons becoming enabled before task/service readiness exists.
- Active feature development and UI refactoring causing merge conflicts or hidden regressions.
- PySide6/headless Qt differences between local, CI, and developer machines.
- Future merge conflicts in `app/main_window.py`, `tests/conftest.py`, and documentation task queues.

## Deferred / Not Implemented

- Do not replace the default main window entry.
- Do not connect real analysis execution.
- Do not refactor the Meta Analysis main chain.
- Do not refactor Bioinformatics core analysis modules.
- Do not migrate report export UI.
- Do not implement a full user-facing project creation flow.
- Do not implement statistical runners.
- Do not implement NMA, HSROC, `metaprop`, or GLMM.
- Do not implement AI/PDF extraction.
- Do not implement PDF/Word export.
- Do not implement complex dashboard drill-down.
- Do not implement simultaneous editing UI for all 10 Meta profiles.
