# UI Baseline Status

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

HEAD at baseline: `0ea88c15520165b70299d715ef2645dcb79dee2b`

Scope: Phase 0 of `SOFTWARE_REMEDIATION_PLAN_UI_AND_ANALYSIS_L3.md`.

## Baseline Rule

The current UI is the only mainline. Legacy folders and historical branches are reference material only. This baseline did not merge an old branch, replace current UI, refactor layout, add analysis algorithms, or create mock outputs.

## Repository State

Pre-existing untracked files remained outside this task:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

## Commands

| Command | Result |
| --- | --- |
| `git status --short` | Completed; only pre-existing untracked files listed above before Phase 0/1 report generation. |
| `git branch --show-current` | `dev/bioinformatics` |
| `git rev-parse HEAD` | `0ea88c15520165b70299d715ef2645dcb79dee2b` |
| `python3 -m app.main --smoke-test` | Passed; app version `0.1.0-internal-beta`, channel `Developer Preview / testing`, source launch, git head `0ea88c1`. |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py tests/ui/test_meta_analysis_workflow_pages.py -q` | Passed, `131 passed`. |

## Current Main UI Areas

| Module | Current UI area | Representative source | Baseline status |
| --- | --- | --- | --- |
| Bioinformatics | Data source, Chinese dataset search, acquisition status, recognition, readiness, standardized assets, workflow status, analysis task center, result browser/report controls | `app/bioinformatics/workflow_pages.py` | Current mainline UI; do not overwrite. |
| Bioinformatics legacy/simple pages | GEO import/download/asset/cleaning, local expression import, sample grouping, differential expression preflight, enrichment preflight, correlation preflight, survival preflight, test report page | `app/bioinformatics/pages/*.py` | Current code exists, but many entries are preflight/testing paths. Do not promote to L3 without proof. |
| Meta Analysis | Protocol/search, literature import, screening, extraction, analysis, quality/reporting, audit/workflow dashboard | `app/meta_analysis/pages/*.py`, `app/meta_analysis/workflow_pages.py` | Current mainline UI. |
| Meta Analysis legacy | Older workbench/dashboard/reporting code | `app/meta_analysis/legacy/` | Reference material only. |

## Known Testing / Placeholder / Boundary Areas

| Area | Boundary |
| --- | --- |
| Bioinformatics DEG runtime | Source runtime can produce a real controlled fixture result, but CLI/backend evidence is not UI L3 proof. |
| Bioinformatics plot/report controls | Real artifact/report gates exist, but L3 requires current UI path proof from input to output. |
| Bioinformatics simple differential/enrichment/correlation/survival pages | Several simple pages explicitly run preflight or test summary actions, not formal closed-loop analysis. |
| Meta Analysis statistics v2 | Real statistics engine exists, but its canonical output path is separate from older figure/report services. |
| Meta Analysis figure/report services | Can produce testing-level forest plot/table/report exports, but not yet proven as one canonical UI loop. |
| Meta quality/reporting placeholder text | Placeholder/testing labels must not be counted as completed analysis. |

## UI Files Not To Overwrite During Remediation

These files are the current UI baseline and should be modified only with scoped Phase-specific changes:

```text
app/bioinformatics/workflow_pages.py
app/bioinformatics/pages/*.py
app/bioinformatics/analysis_ui/*.py
app/meta_analysis/workflow_pages.py
app/meta_analysis/pages/*.py
app/shared/ui_components/*.py
tests/ui/test_bioinformatics_workflow_pages.py
tests/ui/test_meta_analysis_workflow_pages.py
```

## Phase 0 Verdict

Phase 0 baseline is recorded.

Current UI smoke and UI workflow tests pass. No old branch was merged, no current UI was replaced, and no new analysis function was added.
