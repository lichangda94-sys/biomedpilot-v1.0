# Demo Workbench Walkthrough

This walkthrough describes the current internal demo path for the unified Workbench shell. It is a demo/readiness flow only. It does not run pooled statistics, AI/PDF extraction, report export, or any analysis runner.

## Start The App

Run the desktop entry from the repository root:

```bash
python3 -m app
```

For headless test validation, use:

```bash
./.venv/bin/python -m pytest -q
```

## Demo Project

The current demo project is created by `create_demo_meta_readiness_project(...)` and can also be loaded through `MainWindow.load_demo_profile_readiness_project()`.

It creates a local project manifest and a project-local `profile_readiness.json` file. The content is fixed and does not depend on network access or external datasets.

Demo readiness rows:

- `TREATMENT_EFFECT_META`: `supported`
- `DIAGNOSTIC_ACCURACY_META`: `policy_ready`
- `BIOMARKER_PREVALENCE_ASSOCIATION_META`: `mixed`

## Meta Analysis Workspace

Open the Meta Analysis workspace from the Workbench home or by loading the demo project through the current `MainWindow` API.

The workspace currently shows:

- Profile Analysis Readiness panel.
- Template-driven Profile Row Editor table.
- Placeholder Meta Analysis page content.

## Profile Analysis Readiness

The readiness panel reads `profile_readiness.json` from the selected project directory. It displays:

- Profile
- Status
- Supported Now
- Policy Ready
- Unsupported
- Unimplemented
- Warnings
- Recommended Next Action

The disclaimer is part of the panel: readiness summaries describe structural readiness only. They do not mean pooled statistical analysis has been run. Advanced statistics such as NMA, HSROC, metaprop, and GLMM are not implemented here.

## CSV Template / Row Editing Table

The row editor is a template-based preview table. Edits are not auto-saved from this table. They can be persisted only through explicit project-file save/load APIs, which write CSV files under the project-local `profile_rows/` directory.

The editor displays unsaved-change state and basic validation status. Validation is structural only; it checks required template fields and selected row-shape rules. It does not judge medical correctness and does not run analysis.

Save/load behavior is intentionally conservative for the demo:

- Save is blocked while structural validation issues are present.
- Loading or switching profile templates while the table is dirty requires an explicit discard confirmation path.
- The demo UI exposes `Save rows` and `Load rows` buttons. They only write/read project-local CSV files and do not run analysis.
- There is no discard-confirmation dialog yet; dirty loads are blocked and reported in the row editor status text.

The row editor does not run workflow execution, statistics, or report export.

CSV template helpers currently cover only:

- `TREATMENT_EFFECT_META`
- `DIAGNOSTIC_ACCURACY_META`
- `BIOMARKER_PREVALENCE_ASSOCIATION_META`

## Available In This Demo

- Unified Workbench shell navigation.
- Project manifest create/open/save support through explicit APIs.
- Demo project seeding.
- Read-only profile readiness display from project-local JSON.
- CSV template import/export helpers for three priority profiles.
- Minimal template-driven row editing table with explicit project-file CSV persistence APIs, dirty-state display, and structural validation.

## Placeholders / Not Implemented

- No statistical runners.
- No NMA, HSROC, metaprop, or GLMM.
- No AI/PDF extraction.
- No PDF/Word export.
- No complex dashboard drill-down.
- No auto-save or user-facing save/load buttons for the row editor table.
- No all-10-profile editing UI.

## Five-Minute Demo Flow

1. Start the app and show the unified Workbench home.
2. Enter the Meta Analysis workspace.
3. Load or seed the demo profile readiness project.
4. Show the Profile Analysis Readiness table and explain `supported`, `policy_ready`, and `mixed`.
5. Point out the disclaimer that readiness is not a statistical result.
6. Show the row editor and explain that it is a template preview and does not save or execute analysis.
7. Close by showing the supported CSV template profile list and current non-goals.
