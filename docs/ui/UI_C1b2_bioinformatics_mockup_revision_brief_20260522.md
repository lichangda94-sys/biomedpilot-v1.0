# UI-C1b2 Bioinformatics Mockup Revision Brief

Date: 2026-05-22

## 1. Purpose

This brief translates the Bioinformatics mockup QA findings into concrete text and boundary revisions before UI-C2a implementation planning.

## 2. Revision Priority

| Priority | Meaning |
| --- | --- |
| Must revise | Required before the mockup is used as direct UI implementation reference. |
| Should revise | Recommended before high-fidelity finalization. |
| Can keep | Acceptable as shown. |

## 3. Image-level Revision Brief

### 3.1 Project Home

Decision: `text_revisions`

Must revise:

- Change `进行中 / Active` to `项目已打开 / Project Open` or `开发者预览 / Developer Preview`.
- Change data-state labels that imply completion to registered/imported/check-passed labels.
- Replace any broad "enter formal analysis stage" wording with "enter gated preflight/task review".

Should revise:

- Add `resultSemanticKey` or `analysis.status.preflight_only` design annotation in the spec, not necessarily visible to users.
- Keep `Run DEG` disabled and visually secondary.

Can keep:

- Seven-step workflow overview.
- Gate summary card.
- Project summary and next recommended actions.

### 3.2 Data Source Selection

Decision: `text_revisions`

Must revise:

- Add TCGA/GTEx non-auto-merge warning.
- Rename `Completed` to `Imported` or `Import Record Complete`.
- Clarify that source import is not analysis readiness.

Should revise:

- Use `Choose Source` labels and explain that each source enters Data Check & Preparation.
- Add a local import schema validation hint.

Can keep:

- Four source cards.
- Recent imports table.
- Source status overview.

### 3.3 Data Check & Preparation

Decision: `boundary_review`

Must revise:

- Change `Save Report` to disabled `Save Check Summary - File Picker Required` or copy-only `Copy Check Summary`.
- Replace "All data will enter formal analysis stage" with "Data can proceed to Group & Design and analysis task preflight after required checks pass."
- Label overall readiness as input/data readiness, not formal analysis readiness.

Should revise:

- Add blocker grouping for critical vs non-critical warnings.
- Make warning rows visually persistent even when pass rate is high.

Can keep:

- Readiness table.
- Right-side data readiness overview.
- Important Notice section.

### 3.4 Group & Design

Decision: `boundary_review`

Must revise:

- Add statement: covariates do not enable multifactor DEG in current UI-C2 scope.
- Rename `Preflight-Ready` to `Ready for preflight review (not formal analysis)`.
- Mark group/covariate save behavior as adapter-needed if persistence is not active.

Should revise:

- Add design-review notice before Analysis Tasks.
- Make batch information recommendation visible but not blocking unless required by downstream task.

Can keep:

- Group setup table.
- Comparison design table.
- Covariate settings table.
- Sample distribution card.

### 3.5 Analysis Tasks / DEG Preflight

Decision: `boundary_review`

Must revise:

- If `DESeq2` remains visible, label it as parameter policy / planned formal executor, not active formal method.
- Change `Preflight Done` to `Preflight log available`.
- Keep `No Result` explicit for every task without formal result.
- Disable Review Params buttons for ORA/GSEA/survival/clinical unless source packages exist.

Should revise:

- Add disabled reason text under every disabled Run Preflight/Run Formal action.
- Keep dependency panel in sync with Data Check and Group & Design gates.

Can keep:

- Analysis task rows.
- DEG preflight parameter review structure.
- Preflight checklist.
- Important Notice.

### 3.6 Result & Report / Export Gate

Decision: `boundary_review`

Must revise:

- Split implementation reference into `Result & Report` and `Report Export` pages.
- Rename `Report Draft` to `Report Draft Boundary`.
- Add design annotations for result semantics:
  - `analysis.status.preflight_only`
  - `result.semantic.testing_summary_only`
  - `result.semantic.imported_external_result`
  - `result.semantic.formal_computed_result_future`
- Keep export action disabled.

Should revise:

- Add provenance/source column for imported external results when that tab is used.
- Move export-specific gate card to separate Report Export implementation screen.

Can keep:

- Result Browser preflight logs.
- Gate summary.
- disabled Export Gate.
- no-figures/no-report-ready cards.

## 4. UI-C2a Planning Inputs

UI-C2a can begin with these implementation planning workstreams:

1. Page registry and route mapping for six reviewed screens plus separate Report Export.
2. Shared Bioinformatics workflow header and left navigation.
3. Status/gate state model.
4. Data source state model.
5. Data readiness table model.
6. Group/design view model.
7. Analysis task/preflight view model.
8. Result/report/export gate view model.
9. Focused tests for disabled/gated semantics.

## 5. Must Not Enter UI-C2a Runtime Scope

- formal DEG execution
- active DESeq2/limma/edgeR selector as real engine
- ORA/GSEA formal run
- KM/log-rank/Cox/Clinical formal run
- fake result tables
- fake figures
- report-ready package
- export output
- TCGA+GTEx automatic merge
- full integrated report
- clinical conclusion or treatment recommendation

## 6. Suggested UI-C2a Acceptance Criteria

UI-C2a planning is accepted when it defines:

- target page keys for all Bioinformatics main-flow pages
- route ownership in current `app/bioinformatics/workspace.py`
- state model fields for status chips and gate rows
- explicit disabled reasons for formal analysis and export
- test plan proving no fake formal results, no fake figures, and no enabled export
- separation between Result & Report and Report Export pages

## 7. Supplemental Mockup Recommendation

Additional mockups recommended, but not blockers for UI-C2a planning:

- Local File Import detail
- GEO source detail
- TCGA source detail
- GTEx source detail
- Clinical Variable Audit
- Separate Report Export page
- Project Logs & Technical Details
