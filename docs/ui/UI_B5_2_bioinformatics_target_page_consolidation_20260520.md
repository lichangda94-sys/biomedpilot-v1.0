# UI-B5.2 Bioinformatics Target Page Consolidation

Date: 2026-05-20

Goal: consolidate the Bioinformatics target IA registry into the MasterPlan shape of seven main-flow pages plus two auxiliary pages, without enabling formal analysis executors, generating fake results, rewriting legacy business pages, replacing resources, packaging, or running the packaged app.

## 1. Scope

Allowed:

- Tighten Bioinformatics target page metadata.
- Separate main-flow pages from auxiliary pages.
- Calibrate target page keys used by shell navigation and legacy route mapping.
- Add focused UI assertions for page grouping, flow order, and canonical target keys.
- Add this checkpoint document.

Forbidden in this stage:

- No formal DEG / GSEA / ORA / correlation / survival / clinical association execution.
- No fake figures, fake results, or report-ready package.
- No report template rewrite.
- No Bioinformatics business workflow rewrite.
- No resource, icon, App icon, Finder icon, Info.plist, LaunchServices, desktop entry, packaging, or packaged app work.

## 2. Consolidated Target Pages

Main flow:

| flow_index | target_page_key | label | status boundary |
|---|---|---|---|
| 1 | `project_home` | Project Home / 项目首页 | shell-only project status and next step summary. |
| 2 | `data_source` | Data Source / 数据来源 | testing-level source registration; TCGA+GTEx is not auto-merged. |
| 3 | `data_check_preparation` | Data Check & Preparation / 数据检查与准备 | preflight-only resolver/input preparation. |
| 4 | `group_design` | Group & Design / 分组与设计 | shared design page, not DEG-only. |
| 5 | `analysis_tasks` | Analysis Tasks / 分析任务 | blocked/gated until resolver and result schema gates are complete. |
| 6 | `result_report` | Result & Report / 结果与报告 | testing summary and imported external result semantics only. |
| 7 | `report_export` | Report Export / 报告导出 | report draft/testing summary boundary only. |

Auxiliary:

| flow_index | target_page_key | label | status boundary |
|---|---|---|---|
| 1 | `settings_resources` | Bioinformatics Settings / 生信设置 | module settings and resource pointers, with external resources managed in Settings. |
| 2 | `project_logs_technical_details` | Project Logs & Technical Details / 项目日志与技术详情 | technical logs, manifests, workflow status and feedback package details. |

## 3. Runtime Changes

Implemented:

- Extended `BioinformaticsIAPage` with `page_group` and `flow_index`.
- Added `bioinformatics_main_flow_pages()` and `bioinformatics_auxiliary_pages()`.
- Rendered the target IA shell as explicit main-flow and auxiliary groups.
- Added per-nav-item Qt properties:
  - `pageGroup`
  - `flowIndex`
- Changed the canonical target Result page key from `results` to `result_report` to match the MasterPlan wording.
- Mapped legacy `results_browser` to canonical `result_report`.
- Preserved disabled/gated target IA navigation and existing legacy stack navigation for focused tests.

Not changed:

- Existing legacy Bioinformatics workflow pages remain mounted.
- Existing `show_*` workflow navigation methods still route to current widgets for testing and developer validation.
- Formal analysis execution remains gated/blocked.
- No new result/report generation path was introduced.

## 4. Acceptance

UI-B5.2 is accepted when:

- Target IA exposes exactly seven `main_flow` pages and two `auxiliary` pages.
- `result_report` is the canonical target key for Result & Report.
- `results_browser` legacy route maps to `result_report`.
- Report Export remains a separate canonical target page.
- Target IA nav items expose `pageGroup`, `flowIndex`, `statusKey`, and `semanticKey`.
- Legacy navigation still reaches existing pages for focused workflow tests.

## 5. Command Log

| command | result |
|---|---|
| `rg -n "B5\\.2\|B5\\.1\|Bioinformatics target\|Bioinformatics.*shell\|legacy routing\|target page" docs app tests -S` | Passed; identified B5.1 and target IA references. |
| `rg --files app tests docs/ui \| rg "bio\|Bio\|B5\|semantic\|result_report\|module_selection\|sidebar"` | Passed; identified Bioinformatics shell, tests and docs. |
| `sed -n '1,240p' docs/ui/UI_B5_1_bioinformatics_legacy_page_routing_calibration_20260520.md` | Passed; read B5.1 routing baseline. |
| `sed -n '90,150p' docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | Passed; confirmed UI-B5 target scope. |
| `sed -n '1,340p' app/bioinformatics/workspace.py` | Passed; read target page and legacy route registry. |
| `sed -n '1,220p' tests/ui/test_bioinformatics_ia_shell.py` | Passed; read focused IA shell tests. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py` | Passed; `7 passed in 1.32s`. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py::test_workspace_navigation_reaches_full_stack` | Passed; `1 passed in 0.58s`. |
| `git diff -- app/bioinformatics/workspace.py tests/ui/test_bioinformatics_ia_shell.py` | Passed; reviewed scoped implementation diff. |

## 6. Verification

Completed verification:

| command | result |
|---|---|
| `python3 -m app.main --smoke-test` | Passed; source launch smoke reports `workspace_entries=3` and `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_bioinformatics_workflow_pages.py::test_workspace_navigation_reaches_full_stack` | Passed; `8 passed in 1.38s`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed; `171 passed in 17.54s`. |
| `git diff --check` | Passed, no whitespace errors. |
| `git status --short` | Only `app/bioinformatics/workspace.py`, `tests/ui/test_bioinformatics_ia_shell.py`, and this document changed before staging. |

## 7. Boundary Statement

This stage only changes Bioinformatics target IA metadata, disabled shell grouping, focused tests and this checkpoint document. It does not modify packaging, desktop entries, active icons/resources, report templates, language switching, or Bioinformatics business execution flows.
