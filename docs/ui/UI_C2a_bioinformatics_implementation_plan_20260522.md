# UI-C2a Bioinformatics Implementation Planning

## 1. Scope

This stage converts the six accepted Bioinformatics mockup candidates into an implementation plan for the PySide target IA shell. It does not implement UI code, carry over executors, enable formal analysis, generate reports, export packages, or modify runtime assets.

Inputs reviewed:

- `docs/ui/UI_C1b2_bioinformatics_mockup_candidate_QA_report_20260522.md`
- `docs/ui/UI_C1b2_bioinformatics_mockup_revision_brief_20260522.md`
- `docs/ui/UI_C1b2_bioinformatics_mockup_to_implementation_mapping_20260522.csv`
- `docs/ui/references/bioinformatics/Bioinformatics_UI_design_readiness_contract_20260522.md`
- `docs/ui/UI_B5_2_bioinformatics_target_page_consolidation_20260520.md`
- `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md`
- Current `app/bioinformatics/**`, `app/shell/**`, `tests/ui/**`, and `tests/bioinformatics/**`
- Read-only comparison against local worktree `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics` on `dev/bioinformatics`

## 2. Non-Modification Statement

This stage only adds planning and audit documents. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, `dist/**`, packaged app resources, App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, or desktop entries.

## 3. Mockup To Page Implementation Plan

| Mockup | Target page | Implementation scope | Required revision before UI work | Runtime boundary |
| --- | --- | --- | --- | --- |
| Project Home / Workflow Overview | `bio.page.project_home` | Project summary, 7-step flow overview, recent project/status cards, quick links | Replace `Active`, `Completed`, and broad `Ready` copy with `testing`, `preflight`, `draft`, or `blocked` wording | Must not claim formal DEG, report-ready, export-ready, or TCGA+GTEx merge readiness |
| Data Source Selection | `bio.page.data_source` | Source cards for local import, GEO, TCGA, GTEx, and source registration status | Add TCGA/GTEx non-auto-merge warning; rename import completion as source registration, not analysis readiness | Data source selection cannot bypass standardized repository or analysis input package |
| Data Check & Preparation | `bio.page.data_check_preparation` | File recognition, readiness table, missing field rows, repair hints | Make Save Report copy-only or disabled; label checks as input readiness | Readiness checks do not execute DEG, ORA, GSEA, survival, Cox, or report generation |
| Group & Design | `bio.page.group_design` | Comparison setup, sample grouping, covariate audit, design preflight | Rename ready state to preflight-ready; mark persistence as adapter-needed | Covariates do not enable multifactor DEG or clinical modeling |
| Analysis Tasks / DEG Preflight | `bio.page.analysis_tasks` | Task cards and preflight panels for DEG, ORA/GSEA, KM, Cox, clinical audit | Label DESeq2/limma/edgeR as policy/planned unless formal backend gate is present; rename preflight done to preflight log available | No formal task button can be enabled in UIShell without imported gate contracts |
| Result / Report / Export Gate | Split into `bio.page.result_report` and `bio.page.report_export` | Result browser, report draft preview, export gate shell | Split the mockup into two pages; add result semantic chips and export gate state | No fake plots, fake p-values, report-ready package, or active export |

## 4. Target Runtime Page Sequence

The implementation sequence should preserve the target IA from UI-B5.2:

1. `bio.page.project_home`: project shell and flow overview.
2. `bio.page.data_source`: source registration and import boundary.
3. `bio.page.data_check_preparation`: file recognition and input readiness.
4. `bio.page.group_design`: grouping and design preflight.
5. `bio.page.analysis_tasks`: gated task center.
6. `bio.page.result_report`: result browser and report draft boundary.
7. `bio.page.report_export`: export gate and package-readiness boundary.
8. Auxiliary `bio.page.settings_resources`.
9. Auxiliary `bio.page.project_logs`.

The sixth mockup must not be implemented as a single combined result/report/export page. It is acceptable as visual reference, but runtime should split page 6 and page 7 to prevent export-ready overclaiming.

## 5. Page-Level Implementation Plan

### Project Home

- Build a lightweight page header with module status chip `Developer Preview / 本地测试版`.
- Show the 7-step main flow and two auxiliary links.
- Show project summary cards only when project state exists; otherwise use empty project illustration and create/open project actions.
- Disable formal run, report-ready, and export actions.
- Keep quick links: 最近使用, 使用指南, 常见问题, 意见反馈.
- Do not show architecture boundary copy to normal users.

### Data Source

- Render source cards for local file, GEO, TCGA, GTEx.
- Each source card must expose `source.status.*` and `analysis_input_package_status`.
- Local import can open file selection only where existing UI already supports it; planning does not add new import backend.
- TCGA and GTEx must show explicit warning: they are not auto-merged by default.
- Download, merge, or repository write actions remain disabled unless existing source-specific backend and user confirmation are present.

### Data Check & Preparation

- Display file recognition, sample count, value type, identifier mapping, missing metadata, and blocker rows.
- Result state is `analysis.status.preflight_only`.
- Save report is disabled or copy-only until report template and storage/export gates are implemented.
- Repair actions should route to source/data settings or developer diagnostics if no user-facing adapter exists.

### Group & Design

- Display comparison groups, sample assignment, contrast selection, covariate audit, and design warnings.
- Persist design is `disabled_missing_storage_adapter` unless project storage adapter is confirmed.
- Covariate panels are audit/preflight only. They do not enable multifactor DEG, Cox, or clinical claims.
- The only allowed enabled action before executor carry-over is preflight/design review.

### Analysis Tasks

- Render task cards for DEG, ORA/GSEA, survival KM/log-rank, Cox, clinical variable audit, and report draft.
- The default action state is preflight/testing/draft. Formal execution is disabled unless imported state/action contracts confirm every gate.
- DEG formal action requires standardized input package, DEG-ready gate, dependency gate, parameter gate, user confirmation, result schema gate, and result registry.
- ORA/GSEA remain preflight or disabled in UIShell; current Bioinformatics branch marks formal GSEA hidden until ready.
- KM/log-rank and Cox are carry-over candidates from `dev/bioinformatics`, but must remain disabled in UIShell until scoped carry-over and tests land.

### Result & Report

- Show result cards grouped by `resultSemanticKey`.
- Allowed display semantics: `preflight_only`, `testing_level`, `imported_external_result`, `formal_computed_result` only when result registry confirms it.
- Draft report preview is allowed as `report.status.draft` or `report.status.testing_summary`.
- Do not render fake volcano plots, fake DEG table, fake KM plot, fake Cox forest plot, or fake p-values.

### Report Export

- Implement as a separate gate page.
- Export buttons are visible only with disabled/gated states until report-ready package gate passes.
- Default `exportGate` is `disabled_no_report_ready_package` or `disabled_empty_result`.
- `report.status.report_ready_future` is a future state, not current readiness.

## 6. Disabled Button Inventory

These buttons must be disabled or hidden until their gates exist in the current UIShell runtime:

| Area | Button / action | Required disabled state |
| --- | --- | --- |
| Data Source | Auto merge TCGA+GTEx | Hidden or disabled, `blocked_no_auto_merge_policy` |
| Data Source | Download and register source | Disabled unless existing source backend and user confirmation are wired |
| Data Check | Save readiness report | Disabled or copy-only, `disabled_missing_report_storage` |
| Group & Design | Save design | Disabled, `disabled_missing_storage_adapter` |
| Group & Design | Apply covariates to formal model | Disabled, `blocked_until_backend` |
| Analysis Tasks | Run formal DEG | Disabled in UIShell until scoped carry-over lands all gates |
| Analysis Tasks | Run formal ORA/GSEA | Disabled or hidden; formal GSEA is hidden until ready in `dev/bioinformatics` |
| Analysis Tasks | Run KM/log-rank | Disabled in UIShell until scoped carry-over lands all gates |
| Analysis Tasks | Run Cox | Disabled in UIShell until scoped carry-over lands all gates |
| Analysis Tasks | Generate clinical conclusion | Hidden or blocked |
| Result & Report | Generate formal report | Disabled unless report-ready gate passes |
| Report Export | Export PDF / DOCX / ZIP package | Disabled unless report-ready package gate passes |

## 7. Pages Limited To Preflight, Testing, Or Draft

| Page | Allowed current status | Reason |
| --- | --- | --- |
| Data Source | testing / source_registered / blocked | Selection and import do not prove analysis readiness |
| Data Check & Preparation | preflight_only | It checks input readiness only |
| Group & Design | preflight_only / adapter_needed | Design persistence and model gates are not complete in UIShell |
| Analysis Tasks | preflight_only / testing_level / blocked | Formal executors are not wired into UIShell action gates |
| Result & Report | testing_summary / imported_external_result / draft | Formal result display requires result registry semantics |
| Report Export | draft / blocked / report_ready_future | Export package requires report-ready gate |

## 8. Implementation Stages After This Plan

Recommended next stages:

1. `Bioinformatics UI-C2b State/Action Gate Carry-Over Audit`: carry only `analysis_ui/state.py`, `analysis_ui/action_rules.py`, labels, result semantics, and report gate contracts from `dev/bioinformatics` if compatible.
2. `Bioinformatics UI-C2c Target Shell Visual Implementation`: implement the six mockup visual layouts with all formal actions disabled by default.
3. `Bioinformatics UI-C2d Formal DEG Scoped Carry-Over`: only after C2b proves state/action gates and result schema tests pass.
4. `Bioinformatics UI-C2e Survival/Cox Scoped Carry-Over Audit`: only after DEG gate is stable; survival and Cox carry more clinical interpretation risk.

## 9. Commands Run

| Command | Result |
| --- | --- |
| `git status --short --branch` | UIShell clean before edits on `dev/ui-shell` |
| `find app/bioinformatics -maxdepth 3 -type f ...` | Current UIShell contains preflight/testing services and no `analysis_ui` directory |
| `git -C /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics status --short --branch` | Read-only source branch is `dev/bioinformatics`; it has unrelated untracked files not touched |
| `git -C /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics ls-tree ...` | `dev/bioinformatics` contains analysis UI gates, formal DEG, KM/Cox, result registry, report gates |
| `git diff --name-status dev/ui-shell..dev/bioinformatics -- app/bioinformatics tests/bioinformatics config/bioinformatics docs/bioinformatics` | Confirmed scoped carry-over would be large and must be staged by gate family |
| `rg ... app/bioinformatics tests/bioinformatics config/bioinformatics` | UIShell has old/test DEG/ORA runners plus preflight services; formal product gates are absent |

Validation commands for this document are recorded after file creation in the final response and in the git commit.

## 10. Conclusion

The six Bioinformatics mockups are sufficient to start a gated shell implementation, but not sufficient to enable formal analysis actions. UI-C2a should be followed by a scoped carry-over audit of state/action/result/report gate contracts from `dev/bioinformatics`. Formal DEG, KM/log-rank, and Cox executors should not be carried into UIShell until those contracts and their focused tests land first. ORA/GSEA should remain preflight or disabled because `dev/bioinformatics` still marks formal GSEA as hidden until ready and no product-ready GSEA executor was identified.
