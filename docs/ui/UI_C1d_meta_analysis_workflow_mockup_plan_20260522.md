# Meta Analysis UI-C1d Workflow Mockup Planning

## 1. Scope

This planning stage moves from Bioinformatics gated UI closure into Meta Analysis mockup-to-UI preparation. It creates screen planning, sample data, boundary rules, and high-fidelity mockup prompts for the Meta Analysis workflow.

This stage does not modify runtime UI code, tests, active assets, backend services, packaging scripts, `dist/**`, desktop entries, App icon, Finder icon, `.icns`, `Info.plist`, or LaunchServices.

## 2. Inputs Reviewed

Primary inputs:

- `docs/ui/UI_C1a_interface_screen_inventory_mockup_planning_20260522.md`
- `docs/ui/UI_C1a_screen_inventory_20260522.csv`
- `app/meta_analysis/workspace.py`
- `tests/ui/test_meta_analysis_ia_shell.py`
- `docs/ui/target_design_drafts/meta/Meta_Analysis_UI_Target_Architecture_Initial_20260520.md`
- `docs/mainline_meta_analysis_boundary.md`
- `docs/meta_analysis_current_status.md`

## 3. Current Runtime Capability Audit

Current mainline runtime is a target IA shell, not a production Meta workflow.

Observed current runtime surfaces:

| area | current state | audit conclusion |
|---|---|---|
| Meta module entry | present | module is available as Developer Preview / testing shell |
| Project shell | present | supports project manifest binding; not full workflow runtime |
| Target IA | present | 10 main-flow pages + auxiliary Meta Settings |
| Active Meta types | present | 10 v1 types from active schema direction; Network Meta disabled |
| Full-text / Extraction concept | present | tabs are `全文管理`, `提取表设计`, `提取完成核查`, `历史记录` |
| Result / Report / Export | present via shared shell | disabled/gated; no production result or report-ready package |
| Formal statistics | not enabled in mainline UI | must remain testing/planned boundary in mockups |
| AI suggestion | only advisory by policy | must not become automatic conclusion |

## 4. Target Workflow

The mockup planning uses the target workflow below:

1. Meta Project Home
2. Question & Meta Type Selection
3. Search Strategy Builder
4. Import / Reference Management
5. Deduplication
6. Screening Workspace
7. Full-text / Extraction
8. Risk of Bias
9. Pairwise Meta Input
10. Result Review
11. Forest Plot / Table Preview Boundary
12. Report-ready Gate
13. Export Page
14. Meta Settings

The current runtime target IA has 10 main-flow pages plus `Meta Settings`; several planning screens map to sub-panels inside these target pages, especially Import + Deduplication, Result Review + Forest/Table boundary, and Report-ready + Export.

## 5. P0 Mockup Priority

P0 mockups should be produced in this order:

1. Meta Project Home + Workflow Overview
2. Question & Meta Type Selection
3. Search Strategy Builder
4. Import / Reference Management + Deduplication
5. Screening Workspace
6. Extraction + Risk of Bias
7. Result Review + Report-ready Gate

The pack intentionally uses seven mockups rather than compressing to six, because `Question & Meta Type Selection` is a workflow-control page and should not be hidden inside Project Home. If a six-image batch is required later, combine `Result Review + Report-ready Gate + Export` into one gate mockup.

## 6. Screen Specification Matrix

Detailed screen-level planning is stored in:

- `docs/ui/UI_C1d_meta_analysis_screen_specs_20260522.csv`

The matrix covers 14 screens and records:

- current UI status
- backend capability
- mockup priority
- implementation priority
- allowed actions
- disabled actions
- gate semantics
- must-not-claim boundaries

## 7. Mockup Sample Data

Non-production sample data is stored in:

- `docs/ui/mockup_data/meta_analysis/UI_C1d_meta_analysis_mockup_sample_data_20260522.md`

The sample uses thyroid cancer and adiponectin / generic oncology biomarker examples. It includes:

- PICO / PECO draft fields
- English search query draft
- reference table rows
- deduplication group
- screening decisions
- extraction fields
- risk of bias domains
- pairwise input examples
- result/report/export gate state

All values are mockup-only and must not be treated as real evidence, real effect estimates, or report-ready content.

## 8. Core Boundary Rules

The following rules must be visible in mockup review and implementation planning:

- Chinese UI is allowed, but search and extraction processing should remain English-first unless a future audited stage adds more.
- Chinese input may assist English search query drafting; it must not directly execute Chinese database retrieval.
- CNKI / WanFang / VIP / Chinese database direct retrieval must not be shown as active.
- Chinese PDF extraction must not be shown as active.
- AI suggestion is advisory only and cannot replace reviewer screening, extraction, risk-of-bias judgement, analysis decisions, or conclusions.
- Report-ready is an internal draft workflow state, not a publication-grade, clinical-grade, or regulatory report.
- Network Meta is planned only and not active.
- Forest plot/table preview must show a boundary or empty state if no formal result exists; no fake forest plot, pooled effect, heterogeneity, or publication-bias result.
- Export is disabled unless a later formal result/report-ready/export-adapter gate is completed.

## 9. Page-Level Planning Summary

| page | mockup status | key UI elements | boundary |
|---|---|---|---|
| Meta Project Home | P0 | project card, workflow overview, status chips, blockers | Developer Preview / testing |
| Question & Meta Type | P0 | research question, PICO/PECO, 10 type cards, Network Meta planned callout | type selection controls workflow; Network Meta disabled |
| Search Strategy | P0 | English query builder, term groups, database draft tabs, reviewer checklist | no Chinese DB direct retrieval |
| Import / Reference + Dedup | P0 | import cards, reference table, duplicate risk groups | no auto merge/delete/import-to-screening |
| Screening | P0 | reference queue, decisions, exclusion reasons, AI suggestion panel | reviewer decision is authoritative |
| Full-text / Extraction | P0 | four tabs, full-text status, type-specific extraction structure | no Chinese PDF extraction or auto final extraction |
| Risk of Bias | P1 | tool selection, domain rows, missing blocker | suggestion-only; no auto judgement |
| Pairwise Meta Input | P1 | effect rows, model/preflight review, blocked rows | no formal statistics or Network Meta |
| Result Review | P0/P2 | gate summary, empty result, limitation acknowledgement | no fake formal result |
| Forest/Table Boundary | P2 | empty chart frame, required inputs, disabled controls | no fake forest plot/table |
| Report-ready Gate | P0/P2 | blocker list, draft state, reviewer acknowledgement | not publication-ready |
| Export Page | P2 | disabled format buttons, reasons | no export |
| Meta Settings | P3 | preferences, logs, resource status, developer diagnostics | no production connectors |

## 10. High-Fidelity Mockup Production Strategy

First batch:

- Meta Project Home + Workflow Overview
- Question & Meta Type Selection
- Search Strategy Builder
- Import / Reference Management + Deduplication

Second batch:

- Screening Workspace
- Extraction + Risk of Bias

Third batch:

- Result Review + Report-ready Gate
- optional separate Export Page if C2 implementation needs a dedicated export screen

Each mockup should use the same desktop PySide visual direction already established for Bioinformatics and LabTools:

- left main navigation
- top workflow stepper
- rounded cards
- dense but readable tables
- status chips
- right-side review/gate panel where needed
- disabled/gated buttons with clear reason text

## 11. Implementation Readiness

Safe to plan as shell/mockup-first:

- Project Home
- Question & Meta Type
- Search Strategy Builder
- Import / Reference + Dedup
- Screening Workspace
- Full-text / Extraction tab structure
- Result Review + Report-ready Gate shell

Needs later backend/gate audit before active implementation:

- real database execution beyond explicitly audited PubMed path
- real file import in mainline
- final screening decisions
- final extraction save
- quality assessment completion
- pairwise statistics execution
- forest/table rendering
- report-ready transition
- export

## 12. Next-Stage Recommendation

Recommended next stage:

- UI-C1d1 Meta Analysis high-fidelity mockup candidate generation and review.

Alternative if implementation sequencing is needed first:

- UI-C2a Meta Analysis adapter/gate-first implementation planning.

Do not move directly into executor integration. Formal Meta execution requires a separate readiness audit and gate model first.

## 13. Verification

Required for this stage:

```bash
python3 - <<'PY'
import csv
from pathlib import Path
path = Path('docs/ui/UI_C1d_meta_analysis_screen_specs_20260522.csv')
with path.open(newline='') as fh:
    rows = list(csv.DictReader(fh))
assert len(rows) == 14
assert all(row['screen_id'].startswith('META-') for row in rows)
print(f'{path}: {len(rows)} rows')
PY
git diff --check
git diff --cached --check
```

Results:

| Command | Result |
| --- | --- |
| CSV structure check for `docs/ui/UI_C1d_meta_analysis_screen_specs_20260522.csv` | passed, 14 rows |
| `git diff --check` | passed |

`git diff --cached --check` is run after staging the scoped UI-C1d files.
