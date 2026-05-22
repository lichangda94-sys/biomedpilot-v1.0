# UI-C1b2 Bioinformatics Core Mockup Candidate QA Report

Date: 2026-05-22

## 1. Scope

This stage reviews six Bioinformatics high-fidelity mockup candidates saved under:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics`

The review checks whether the candidates are suitable as inputs for Bioinformatics UI-C2a implementation planning.

This is a mockup QA and revision brief stage only. It does not modify runtime UI, tests, assets, business logic, report templates, packaging, App icon, Finder icon, `.icns`, Info.plist, LaunchServices, or desktop entry points.

Reference constraints used:

- Bioinformatics target IA is seven main-flow pages plus two auxiliary pages.
- Formal DEG / ORA / GSEA / survival / clinical execution must remain gated.
- Preflight logs are not formal results.
- Report draft is not report-ready.
- Export must remain disabled until result/report/export gates pass.
- TCGA and GTEx must not be shown as an automatic merge/default analysis path.
- Imported external results must not be presented as BioMedPilot formal recomputed results.

## 2. Reviewed Images

| # | Image | Target screen |
| ---: | --- | --- |
| 1 | `Bioinformatics_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | Project Home |
| 2 | `Bioinformatics_Data_Source_Selection_candidate_v2_20260522.png` | Data Source Selection |
| 3 | `Bioinformatics_Data_Check_Preparation_Readiness_Table_candidate_20260522.png` | Data Check & Preparation |
| 4 | `Bioinformatics_Group_Design_Comparison_Setup_candidate_20260522.png` | Group & Design |
| 5 | `Bioinformatics_Analysis_Tasks_DEG_Preflight_candidate_20260522.png` | Analysis Tasks / DEG Preflight |
| 6 | `Bioinformatics_Result_Report_Export_Gate_candidate_v2_20260522.png` | Result & Report plus Export Gate |

## 3. Summary Decision

Overall decision: accepted for UI-C2a implementation planning with text and boundary revisions.

Recommended next stage:

`UI-C2a Bioinformatics gated shell implementation planning`

Do not proceed directly to formal analysis implementation. UI-C2a should plan shell/layout/state-model implementation only:

- 7-step target IA navigation
- preflight/gate state rows
- disabled formal analysis buttons
- result/report/export gate shell
- semanticKey/pageKey/statusKey preservation
- no fake results or fake figures

## 4. Per-image Review

### 4.1 Project Home

Image:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Project_Home_Workflow_Overview_candidate_v2_20260522.png`

Decision: `text_revisions`

Accepted parts:

- The left navigation matches the Bioinformatics flow and includes Project Home, Data Source, Data Check & Preparation, Group & Design, Analysis Tasks, Result & Report, Report Export, and Settings.
- The main workflow overview clearly shows seven steps.
- Gate summary separates Data Readiness, Design Readiness, Analysis Execution, Result Availability, Report Gate, and Export Gate.
- Important notice correctly says reports/exports are unavailable until gates pass and formal computation is completed.
- "Run DEG" is disabled.

Required revisions:

- Replace `进行中 / Active` with a safer project lifecycle label such as `项目已打开 / Project Open` or `开发者预览 / Developer Preview`. `Active` can be misread as active formal analysis.
- Replace `已完成 / 就绪` for data source-like states with `已注册 / Registered` or `数据已导入 / Imported` when the state only means source registration.
- Avoid wording that says "formal analysis stage" as an automatic transition after checks. Use "may proceed to gated analysis task review".
- Keep the bottom warning; it is important and should remain visible.

Must not claim:

- Formal DEG is ready.
- Result/report/export is ready.
- TCGA+GTEx can be auto-merged.

Implementation readiness:

- Good candidate for UI-C2a Project Home shell and workflow overview.
- Use text revisions before implementation.

### 4.2 Data Source Selection

Image:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Data_Source_Selection_candidate_v2_20260522.png`

Decision: `text_revisions`

Accepted parts:

- Four source cards are clear: GEO, TCGA, GTEx, Local File Import.
- The right-side import guide communicates that Data Check & Preparation comes before downstream analyses.
- Recent Imports table and Source Status Overview are suitable for low/mid fidelity UI.
- The bottom notice correctly says imported data enters pre-analysis first.

Required revisions:

- Add explicit TCGA/GTEx warning copy: GTEx is a reference/source option and must not be automatically merged with TCGA as normal controls.
- Rename `完成 / Completed` in recent imports to `已导入 / Imported` or `导入记录完成 / Import Record Complete`.
- Use `选择数据源 / Choose Source` rather than `选择 / Select` where selection starts a gated import workflow.
- For GEO/TCGA/GTEx cards, distinguish online search/download from local upload and from formal analysis.

Must not claim:

- Import completion means analysis readiness.
- GTEx can become TCGA normal control automatically.
- Any online source action has already downloaded or standardized data.

Implementation readiness:

- Good candidate for UI-C2a Data Source shell.
- Supplemental detailed mockups are still needed later for GEO, TCGA, GTEx, and Local Import subpages.

### 4.3 Data Check & Preparation

Image:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Data_Check_Preparation_Readiness_Table_candidate_20260522.png`

Decision: `boundary_review`

Accepted parts:

- Readiness table structure is strong: check item, status, summary, key metrics, suggested action, details.
- Separate tabs for overview, expression matrix, sample annotation, clinical data, gene annotation, batch/platform, and outliers are useful.
- Warning banner correctly states current data is pre-analysis and formal analyses can start only after critical checks pass.
- Right-side readiness overview and Important Notice reinforce pre-analysis boundaries.

Boundary risks:

- `保存检查报告 / Save Report` can be misread as real file export or formal report generation. It should be disabled, renamed, or gated.
- Bottom note says all data will enter formal analysis after passing the page. This is too broad; passing data checks is only one gate.
- Donut chart and 100% bars are visually strong; they must not imply formal analysis readiness unless all downstream gates also pass.

Required revisions:

- Replace `Save Report` with `保存检查摘要 - 需文件选择器 / Save Check Summary - File Picker Required` or `复制检查摘要 / Copy Check Summary`.
- Replace "All data will enter formal analysis stage" with "Data can proceed to Group & Design and analysis task preflight after required checks pass."
- Label Data Readiness as `input readiness` rather than `analysis ready`.
- Keep warnings visible even when most rows pass.

Must not claim:

- readiness table is a formal result.
- data check pass enables formal DEG/ORA/GSEA/survival directly.
- report save/export is already implemented.

Implementation readiness:

- Good candidate for UI-C2a Data Check shell after boundary copy revisions.
- If implemented before file picker, save/export actions must remain disabled or copy-only.

### 4.4 Group & Design

Image:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Group_Design_Comparison_Setup_candidate_20260522.png`

Decision: `boundary_review`

Accepted parts:

- Group setup, comparison design, covariate settings, sample distribution, and design readiness are laid out clearly.
- The right panel separates readiness and design summary.
- The warning banner says the project is still pre-analysis.
- `Run Preflight` is placed as a preflight action, not as formal analysis execution.

Boundary risks:

- Editable group/covariate controls may imply real persistence if backend adapter is not wired in the current UI branch.
- `Preflight-Ready` could be misunderstood as formal analysis ready.
- Covariate toggles may imply multifactor DEG support; current Bioinformatics boundary does not allow multifactor formal DEG.

Required revisions:

- Label covariates as `design annotation / future controlled use` unless the specific downstream task supports them.
- Replace `Preflight-Ready` with `Ready for preflight review (not formal analysis)`.
- Add a disabled/pending save state for group and covariate edits if project persistence is not implemented in the target branch.
- Add warning: formal DEG MVP is controlled two-group only; covariates do not enable multifactor DEG.

Must not claim:

- multifactor DEG is supported.
- covariate toggles change active formal DEG model.
- design pass alone enables formal analysis.

Implementation readiness:

- Good candidate for UI-C2a Group & Design shell with boundary revisions.
- Persistence/edit behavior must be adapter-aware.

### 4.5 Analysis Tasks / DEG Preflight

Image:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Analysis_Tasks_DEG_Preflight_candidate_20260522.png`

Decision: `boundary_review`

Accepted parts:

- The task table makes DEG, ORA, GSEA, KM/log-rank, Cox, and Clinical Association independent task rows.
- Most formal task actions are disabled when dependencies are partial.
- DEG is clearly marked `Preflight Only`.
- The preflight checklist states no formal results will be generated.
- Dependency overview makes partial clinical/batch dependencies visible.

Boundary risks:

- The DEG parameter panel includes `DESeq2`; current UI contract says limma / DESeq2 / edgeR must not be claimed as formal execution unless backend and dependency gates exist.
- `Run Preflight` is acceptable, but the visual hierarchy must not make it look like `Run DEG`.
- `Preflight Passed (with Warnings)` could be mistaken as computed result availability.

Required revisions:

- Rename method selector from actual formal engines to `method preference / placeholder` or `preflight method policy` unless the target backend can support it.
- Add a small line near `DESeq2`: `parameter policy only; formal executor disabled`.
- Replace `Preflight Done` in task cards with `Preflight log available`.
- Keep "No result" column prominent.
- Disable or hide Review Params actions for ORA/GSEA/survival/clinical until source result/input packages exist.

Must not claim:

- DEG has formal DESeq2/limma/edgeR execution.
- ORA/GSEA/KM/Cox/Clinical rows are runnable formal tasks.
- preflight is a result.

Implementation readiness:

- Suitable for UI-C2a Analysis Tasks planning as gated shell and preflight UI.
- Do not implement formal task execution from this mockup.

### 4.6 Result & Report / Export Gate

Image:

`/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Result_Report_Export_Gate_candidate_v2_20260522.png`

Decision: `boundary_review`

Accepted parts:

- Strong top warning: all analyses are pre-analysis and formal outputs are unavailable until formal computation.
- Task result cards distinguish preflight, not started, and missing formal result states.
- Result Browser is clearly labeled `Preflight Logs Only`.
- Formal Results tab shows zero.
- Report Draft, Figures Preview, Report-ready, and Export Gate are blocked/not ready.
- Export button is disabled.

Boundary risks:

- This image combines Result & Report and Export Gate; target IA has `Result & Report` and `Report Export` as separate main-flow pages.
- `Imported Results` tab exists; it needs imported_external_result semantics if used.
- `Report Draft` panel must not become "Generate report" unless it is clearly a draft/testing summary and not report-ready.
- `Result table` visual markers must not show fake rows beyond preflight logs.

Required revisions:

- Split implementation planning into two pages:
  - `Result & Report`: preflight logs, imported external results, testing summaries, report draft boundary.
  - `Report Export`: disabled export gate, future formats, blockers, provenance requirements.
- Rename `Report Draft` to `Report Draft Boundary / 报告草稿边界`.
- Add `resultSemanticKey` labels in design notes: `preflight_only`, `testing_summary_only`, `imported_external_result`, `formal_computed_result_future`.
- Keep export button disabled and visibly gated.

Must not claim:

- report-ready package exists.
- figures are generated.
- export is available.
- preflight logs are formal results.

Implementation readiness:

- Good candidate for UI-C2a Result/Report/Export gated shell planning.
- Needs split-page mapping before runtime implementation.

## 5. Cross-image Findings

### Accepted Direction

- Light desktop workbench style is consistent.
- Left-side Bioinformatics navigation is stable.
- Most pages preserve Chinese primary UI with English helper labels.
- Important notices are present and useful.
- Status chips and gate cards are visually clear.
- The mockup set strongly supports a real PySide shell implementation pass.

### Required Global Text Revisions

Replace or qualify these risky terms:

| Current wording pattern | Safer wording |
| --- | --- |
| `Active` | `Project Open`, `Developer Preview`, or `Testing Workspace` |
| `Completed` for imports/checks | `Imported`, `Registered`, `Check Passed` |
| `Ready` | `Ready for preflight`, `Input ready`, or `Gate passed` |
| `Save Report` | `Copy Summary`, `Save Summary - File Picker Required`, or disabled state |
| `Preflight Done` | `Preflight log available` |
| formal method names as active choices | `method policy / formal executor disabled` unless backend gate proves availability |

### Required Boundary Rules

- No formal DEG / ORA / GSEA / survival / clinical run in UI-C2a.
- No fake DEG table, fake enrichment table, fake KM curve, fake Cox output, fake figure, or fake report-ready package.
- No TCGA+GTEx automatic merge path.
- No imported external result shown as BioMedPilot recomputed result.
- Export remains disabled until result/report/export gate implementation is explicitly approved.
- Save/report actions must be disabled, copy-only, or adapter-needed until file picker/report adapter exists.

## 6. Missing Mockups Before Full Implementation

Not required before UI-C2a planning, but needed before full implementation:

- GEO detailed search/import/download subpage.
- TCGA source detail and clinical import constraints.
- GTEx source detail with non-auto-merge warning.
- Local expression import file-card and validation table.
- Clinical variable audit page.
- Separate Report Export page.
- Bioinformatics Settings / Resources page.
- Project Logs & Technical Details page.

## 7. Go / No-go For UI-C2a

Decision: go for UI-C2a implementation planning.

Allowed UI-C2a scope:

- turn these mockups into an implementation plan
- map UI shells to current code routes
- define page-level state models
- define semanticKey/pageKey/statusKey/resultSemanticKey/reportStatusKey/exportGate requirements
- define focused tests

Not allowed in UI-C2a:

- enabling formal analysis execution
- generating fake results or figures
- enabling report-ready exports
- implementing save/export/report file output
- changing backend business workflows
- packaging or App icon work

## 8. Verification

| Command | Result |
| --- | --- |
| `find /Users/changdali/Desktop/UI/界面示意图/bioinformatics -maxdepth 2 -type f` | Found 6 candidate images |
| Image visual review via local image inspection | Completed for all 6 images |
| CSV structure check for `docs/ui/UI_C1b2_bioinformatics_mockup_to_implementation_mapping_20260522.csv` | Passed; 6 rows with required columns and existing image paths |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed after staging docs |

No runtime tests were run because this stage only adds mockup QA documentation.

## 9. Non-modification Statement

This stage did not modify runtime code, tests, active assets, packaging scripts, `dist/**`, App icon / Finder icon / `.icns` / Info.plist / LaunchServices, or desktop entry points.
