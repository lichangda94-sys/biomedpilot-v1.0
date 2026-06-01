# High-Fidelity Mockup to PySide Page Mapping

Date: 2026-06-01

Scope: all software page content in this UI line that was produced from high-fidelity mockup PNG / concept screenshot evidence. This is a page-production mapping document. It maps design images to PySide files, page classes or route hosts, recovery/rebuild commits, and current implementation status.

This file intentionally says `high-fidelity mockup PNG / concept screenshot`, not `Figma source`. The repository audit found no `.fig`, `.figjam`, or `figma.com` source file for these pages. The available evidence is screenshot/mockup imagery plus mapping, QA, implementation sequence, runtime screenshot, and visual gap documents.

## Evidence Sources

| Evidence | Path |
| --- | --- |
| Concept/mockup image root | `/Users/changdali/Desktop/UI/界面示意图/` |
| Bio mockup mapping | `docs/ui/UI_C1b2_bioinformatics_mockup_to_implementation_mapping_20260522.csv` |
| Bio implementation sequence | `docs/ui/UI_C2a_bioinformatics_page_implementation_sequence_20260522.csv` |
| Bio closure audit | `docs/ui/UI_C2g_bioinformatics_gated_ui_closure_audit_20260522.md` |
| Meta mockup mapping | `docs/ui/UI_C1d2_meta_analysis_mockup_to_implementation_mapping_20260522.csv` |
| Meta implementation sequence | `docs/ui/UI_C2a_meta_analysis_page_implementation_sequence_20260522.csv` |
| LabTools mockup mapping | `docs/ui/UI_C1c3b_labtools_mockup_to_implementation_mapping_20260522.csv` |
| LabTools implementation sequence | `docs/ui/UI_C2a_labtools_implementation_sequence_20260522.csv` |
| Runtime visual gap audit | `docs/ui/UI_C5a_runtime_vs_mockup_visual_gap_audit_20260524.md` |
| Runtime visual gap matrix | `docs/ui/UI_C5a_runtime_visual_gap_matrix_20260524.csv` |
| UI directory/page style audit | `docs/project-control/UI_DIRECTORY_STRUCTURE_PAGE_STYLE_AUDIT_20260531.md` |

## Status Vocabulary

| Status | Meaning |
| --- | --- |
| `implemented-runtime-page` | PySide page exists and is reachable in this line. Runtime behavior may still be gated. |
| `implemented-gated-shell` | PySide page exists, but formal executor/report/export behavior is intentionally disabled or preflight-only. |
| `implemented-shell-frame` | Shell/dashboard/settings frame exists, but individual actions may still be placeholders. |
| `mockup-source-only` | Mockup exists, but this audit did not find a current matching final PySide page. |
| `not-final-fidelity` | Runtime page exists but visual gap matrix says it is not pixel/fidelity complete relative to the mockup. |

## Shell / Global Pages

| Mockup / Concept Screenshot | Page Content | PySide Code | Primary Commits | Current Status | Production Notes |
| --- | --- | --- | --- | --- | --- |
| `IMG-01 Welcome / 欢迎页` | Welcome / login / about entry | `app/shell/login.py` (`BioMedPilotLoginWidget`) | `2423dd1`, `8a92120` | `implemented-shell-frame` | Packaged preview baseline later accepted at `9d4edf3`; account registration and password recovery remain placeholder-class actions. |
| `IMG-02 Dashboard : 工作台首页.png` | Dashboard module selection / module cards | `app/shell/module_selection.py` (`ModuleSelectionWidget`); `app/shell/dashboard.py`; `app/shell/main_window.py` | `35446c5`, `78385b2`, `285d234` | `implemented-shell-frame`, `not-final-fidelity` | Runtime visual gap matrix rates dashboard gap as `medium`; Bio and Meta routes are connected, LabTools must be checked against the current target branch. |
| `IMG-03 Settings : 设置中心.png` | Settings home / resource status / external engines | `app/shell/settings_page.py`; `app/shell/main_window.py` | `78385b2`, `e24a8c8`, `285d234`, provenance update `9d4edf3` | `implemented-shell-frame`, `not-final-fidelity` | Runtime visual gap matrix rates Settings as `critical`; resource detection must remain detect-first and not imply installed tools are enabled. |

## Bioinformatics Pages

The Bioinformatics target flow is seven main pages plus auxiliary settings/resources and technical logs. The seven main pages are implemented as gated PySide UI pages. They are not proof of formal DEG, ORA/GSEA, KM/Cox, report-ready package, or export execution.

| Mockup PNG | Target Page | Page Key | PySide Code | Primary Commits | Current Status | Runtime/Fidelity Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `bioinformatics/Bioinformatics_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | Project Home / 项目首页 | `bio.page.project_home` | `app/bioinformatics/project_home.py` (`BioinformaticsProjectHomeWidget`); hosted by `app/bioinformatics/workspace.py` | `900ba60`, visual rebuild `2063ce8` | `implemented-gated-shell`, `not-final-fidelity` | C5a rates visual gap `medium`; seven-step shell is correct but project summary/card hierarchy still needs polish. |
| `bioinformatics/Bioinformatics_Data_Source_Selection_candidate_v2_20260522.png` | Data Source / 数据来源 | `bio.page.data_source` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsDataSourceWidget`); hosted by `app/bioinformatics/workspace.py` | `900ba60`, visual rebuild `2063ce8` | `implemented-gated-shell`, `not-final-fidelity` | Source cards for GEO/TCGA/GTEx/Local exist as gated source registration; no direct formal analysis. C5a gap `medium`. |
| `bioinformatics/Bioinformatics_Data_Check_Preparation_Readiness_Table_candidate_20260522.png` | Data Check & Preparation / 数据检查与准备 | `bio.page.data_check_preparation` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsReadinessDashboardWidget`, recognition/standardization folded routes); hosted by `app/bioinformatics/workspace.py` | `62739aa`, visual rebuild `2063ce8` | `implemented-gated-shell` | Readiness display is preflight-only; no formal quality score or report save. Runtime screenshot set includes earlier C1/C2 captures. |
| `bioinformatics/Bioinformatics_Group_Design_Comparison_Setup_candidate_20260522.png` | Group & Design / 分组与分析设计 | `bio.page.group_design` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsGroupComparisonDesignWidget`); hosted by `app/bioinformatics/workspace.py` | `62739aa`, visual rebuild `2063ce8` | `implemented-gated-shell` | Draft grouping/comparison/covariate preflight only; no multifactor DEG or Cox activation. |
| `bioinformatics/Bioinformatics_Analysis_Tasks_DEG_Preflight_candidate_20260522.png` | Analysis Tasks / 分析任务 | `bio.page.analysis_tasks` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsAnalysisTaskCenterWidget`); hosted by `app/bioinformatics/workspace.py` | `4061d72`, visual rebuild `2063ce8` | `implemented-gated-shell`, `not-final-fidelity` | C5a rates visual gap `high`; page has DEG/ORA/GSEA/KM/Cox/clinical task matrix but all formal actions remain disabled or gated. |
| `bioinformatics/Bioinformatics_Result_Report_Export_Gate_candidate_v2_20260522.png` | Result & Report / 结果与报告 | `bio.page.result_report` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsResultsBrowserWidget`); hosted by `app/bioinformatics/workspace.py` | `2d5a560`, visual rebuild `2063ce8` | `implemented-gated-shell`, `not-final-fidelity` | C5a groups result/export as visual gap `high`; page shows result/report gate preview, empty result, preflight/imported/testing boundaries only. |
| `bioinformatics/Bioinformatics_Result_Report_Export_Gate_candidate_v2_20260522.png` | Report Export / 报告导出 | `bio.page.report_export` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsReportViewerWidget` in export-gate mode); hosted by `app/bioinformatics/workspace.py` | `2d5a560`, visual rebuild `2063ce8` | `implemented-gated-shell`, `not-final-fidelity` | Export remains disabled until report-ready package and file/export adapter proof. No DOCX/HTML/PDF/CSV/XLSX active export. |
| Existing shell reference | Bioinformatics Settings & Resources | `bio.page.settings_resources` | `app/bioinformatics/workflow_pages.py` (`BioinformaticsSettingsAndLocalAIWidget`); hosted by `app/bioinformatics/workspace.py` | gate shell `08e9bd1`, rebuild `2063ce8` | `implemented-gated-shell` | This is not a high-fidelity Bio mockup PNG row; it is an auxiliary reference shell. |
| Existing shell reference | Project Logs / Technical Details | `bio.page.project_logs_technical_details` | `app/bioinformatics/workspace.py` auxiliary route / diagnostics surfaces | gate shell `08e9bd1`, rebuild `2063ce8` | `implemented-gated-shell` | Diagnostic route only; not a primary high-fidelity page. |

### Bioinformatics Legacy / Old Page Code Not To Treat As High-Fidelity Pages

| Old Code Area | Reason |
| --- | --- |
| `app/bioinformatics/pages/**` | Functional legacy pages such as GEO import, cleaning, grouping, enrichment, survival, and report pages. They are not the seven-page high-fidelity mockup implementation surface. |
| `app/bioinformatics/legacy/**` | Historical tools and sandbox code; not current UI page truth. |
| runtime/service packages under `app/bioinformatics/**` | Backend/service evidence only; not proof of high-fidelity page implementation. |

## Meta Analysis Pages

The Meta Analysis pages are also high-fidelity mockup sourced, but many are gated/draft-only. Runtime layout was subsequently rebuilt using Workbench primitives.

| Mockup PNG / Mockup ID | Target Page Group | PySide Code | Primary Commits | Current Status | Runtime/Fidelity Notes |
| --- | --- | --- | --- | --- | --- |
| `Meta_Project_Home_Workflow_Overview_candidate_v2_20260522.png` / `META-MOCK-001` | Project Home | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `bf6aaf8`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | C5a original gap `critical`; C5c later rebuild adds runtime screenshots but still requires sign-off. |
| `Meta_Question_Meta_Type_Selection_candidate_v2_20260522.png` / `META-MOCK-002` | Question & Meta Type | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `bf6aaf8`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | Network Meta remains planned/disabled; no final question confirmation or executor activation. |
| `Meta_Search_Strategy_Builder_candidate_20260522.png` / `META-MOCK-003` | Search Strategy | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `e551f44`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | English-first draft/query shell; no Chinese DB direct retrieval or live search execution. |
| `图 4：Import : Reference Management + Deduplication` / `META-MOCK-004` | Import / Reference Management / Deduplication | `app/meta_analysis/workspace.py`; older functional pages also exist under `app/meta_analysis/pages/**` | `e551f44`, visual rebuild `87f3f9a` | `implemented-gated-shell` / `hybrid` | Draft/reference/dedup preview only; no automatic merge/delete or production library promotion. |
| `Meta_Screening_Workspace_candidate_20260522.png` / `META-MOCK-005` | Screening | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `557b645`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | Manual-review/draft decisions only; no AI final decision or final PRISMA count. |
| `图 6：Extraction + Risk of Bias` / `META-MOCK-006` | Full-text / Extraction / Risk of Bias | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `557b645`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | Draft extraction and RoB preview only; no automatic PDF extraction, final extraction save, or automatic RoB judgement. |
| `Meta 图 7：Result Review + Report-ready Gate` / `META-MOCK-007` | Result Review / Report-ready Gate | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `6fe2295`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | No fake forest plot, pooled effect, heterogeneity, publication bias, or report-ready success. |
| `Meta_Report_Export_Gate_candidate_20260522.png` / `META-MOCK-008` | Report Export | `app/meta_analysis/workspace.py` (`MetaAnalysisWorkspaceWidget`) | `6fe2295`, visual rebuild `87f3f9a`, layout rebuild `dde15c2` | `implemented-gated-shell`, `not-final-fidelity` | All export formats remain disabled; no file write. |

### Meta Old / Hybrid Page Code Not To Treat As Final High-Fidelity Pages

| Code Area | Reason |
| --- | --- |
| `app/meta_analysis/pages/**` | Older/active functional workflow pages exist, but they are not identical to C2 high-fidelity shell pages. Treat as hybrid/legacy functional surface unless specifically reconciled. |
| `app/meta_analysis/services/**`, `models/**`, `stats/**` | Runtime/service layer; not visual page proof. |

## LabTools Pages

In this UI line, LabTools high-fidelity mockup sourced pages were implemented primarily through `app/labtools_runtime.py` plus UI wiring in `app/shell/main_window.py`. This differs from later/current Integration branches that may use `app/labtools/workspace.py`.

| Mockup PNG | Target Page | PySide Code | Primary Commits | Current Status In This UI Line | Runtime/Fidelity Notes |
| --- | --- | --- | --- | --- | --- |
| `IMG-04 LabTools : 实验工具首页.png` | LabTools Home | `app/shell/main_window.py` LabTools shell/page builder; runtime state from `app/labtools_runtime.py` | navigation `3bf79f4`, rebuild `ed396b4`, dense rebuild `4999405` | `implemented-runtime-page`, `not-final-fidelity` | C5a gap `medium`; three-entry IA is correct but cards and visual rhythm need polish. |
| `labtools/Quick Calculator + Dynamic Formula Solver.png` | General Calculator / Quick Calculator / Dynamic Formula Solver | `app/labtools_runtime.py` calculation runtime; `app/shell/main_window.py` UI page | `ca006ee`, rebuild `ed396b4`, dense rebuild `4999405` | `implemented-runtime-page`, `not-final-fidelity` | C5a gap `high`; form/result panels are dense and need shared primitives. |
| `labtools/2. Reagent Template + Preparation Workflow.png` | Reagent Template / Preparation Workflow | `app/labtools_runtime.py`; `app/shell/main_window.py` UI page | `f18b9a0`, storage `edfa2a5`, write integration `e64454b`, rebuild `ed396b4`, dense rebuild `4999405` | `implemented-runtime-page`, `not-final-fidelity` | C5a gap `critical`; layout needs controlled list/main/editor proportions. Save/export must remain adapter/file-picker gated. |
| `labtools/3. Western Blot Loading + SDS-PAGE Gel.png`; supplemental `labtools/图 2：WB lane : warning detail.png` | Western Blot Loading | `app/labtools_runtime.py`; `app/shell/main_window.py` UI page | `a33cffe`, rebuild `ed396b4`, dense rebuild `4999405` | `implemented-runtime-page`, `not-final-fidelity` | C5a gap `critical`; lane/result/warning layout needs rebuild. No fake gel bands or automatic band recognition. |
| `labtools/4. BCA : OD MVP Boundary.png` | BCA / OD MVP Boundary | `app/shell/main_window.py` boundary/experiment modules page; runtime references in `app/labtools_runtime.py` | boundary `00f4ec6`, rebuild `ed396b4` | `implemented-gated-shell` / `mockup-source-only for final page` | Boundary/MVP only; no active ELISA, formal report, 4PL, or production export. |
| `labtools/图 5：Cell Experiment Workspace : 细胞实验工作区.png` | Cell Experiment Workspace / Experiment Boundaries | `app/shell/main_window.py`; local read/write models in `app/labtools_runtime.py` | boundary `00f4ec6`, cell revamp `4cd06fb`, rebuild `ed396b4` | `implemented-gated-shell`, `not-final-fidelity` | C5a gap `medium`; no fake records/timeline, no automatic ROI/cell counting. |
| `labtools/通用图像处理工作台.png` | Image Processing Workspace Boundary | `app/shell/settings_page.py` resource gate and LabTools boundary routing in `app/shell/main_window.py` | boundary `00f4ec6`, settings rebuild `78385b2`, settings polish `e24a8c8` | `implemented-gated-shell` | Settings-linked ImageJ/Fiji boundary only; no macro execution or automatic image analysis. |

### LabTools Branch/Route Warning

Do not infer that all LabTools pages above are active in every Integration target. The page code in this UI line is centered on `app/labtools_runtime.py` and `app/shell/main_window.py`. Later Integration targets may route LabTools through `app/labtools/workspace.py`, where the currently audited target can expose only a narrow ImageJ/Fiji page. Any migration must reconcile the route host before moving page code.

## Runtime Screenshot Coverage

The following runtime screenshot sets are evidence that pages rendered in this line:

| Screenshot Set | Coverage |
| --- | --- |
| `docs/ui/runtime_screenshots/UI_C1_20260521/` | Welcome, Dashboard, Settings, LabTools Home, Bio Home/Data Source/Data Check/Group/Result, Meta Question/Search/Full-text/Extraction. |
| `docs/ui/runtime_screenshots/UI_C2_1_20260521/` | Follow-up runtime screenshot set for the same early concept pages. |
| `docs/ui/runtime_screenshots/20260524/` | Runtime vs mockup visual gap baseline for Dashboard, Settings, Bio, Meta, LabTools. |
| `docs/ui/runtime_screenshots/20260525_c5c_meta_layout_rebuild/` | Meta layout rebuild screenshots. |
| `docs/ui/runtime_screenshots/20260525_c5d_labtools_layout_rebuild/` | LabTools dense layout rebuild screenshots. |
| `docs/ui/runtime_screenshots/20260525_c5e_bioinformatics_polish/` | Bioinformatics polish screenshots. |
| `docs/ui/runtime_screenshots/20260526_d6_runtime_review/` | D6 runtime review screenshots across Shell, Bio, Meta, LabTools, Settings. |

## Commit Index For Page Recovery / Rebuild

| Area | Commits |
| --- | --- |
| Welcome / About | `2423dd1`, `8a92120` |
| Dashboard / Settings Shell | `35446c5`, `78385b2`, `e24a8c8`, `285d234` |
| Shared Workbench Components | `b691fe6`, `a731f8a`, `1d663a7`, `cb10694`, `d834c5a` |
| Bioinformatics High-Fidelity Mockup Pages | `08e9bd1`, `900ba60`, `62739aa`, `4061d72`, `2d5a560`, `2063ce8`, `7cacf28`, `285d234` |
| Meta Analysis High-Fidelity Mockup Pages | `bf6aaf8`, `e551f44`, `557b645`, `6fe2295`, `87f3f9a`, `ed726b6`, `dde15c2`, `285d234` |
| LabTools High-Fidelity Mockup Pages | `3bf79f4`, `ca006ee`, `f18b9a0`, `a33cffe`, `00f4ec6`, `ed396b4`, `4999405`, `4cd06fb` |

## Production Use Rules

1. Use this file as the page-production entry map before editing or migrating UI pages.
2. Treat PNG/mockup references as visual direction and QA inputs, not as editable Figma source.
3. For Bio and Meta, preserve `implemented-gated-shell` semantics unless a separate runtime/executor gate has been approved.
4. For LabTools, reconcile the active route host before moving code: `app/labtools_runtime.py` plus `app/shell/main_window.py` in this line is not the same route shape as later `app/labtools/workspace.py`.
5. Do not promote legacy pages under `app/bioinformatics/pages/**` or `app/meta_analysis/pages/**` to high-fidelity pages without a separate mockup-to-runtime audit.
6. Use `docs/ui/UI_C5a_runtime_visual_gap_matrix_20260524.csv` before final visual sign-off; many pages are implemented but explicitly not final-fidelity.
