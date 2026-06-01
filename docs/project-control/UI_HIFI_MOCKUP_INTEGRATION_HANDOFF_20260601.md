# High-Fidelity Mockup UI Integration Handoff

Date: 2026-06-01

Purpose: provide Integration with a copied working packet for every software page in this UI line that was made from high-fidelity mockup PNG / concept screenshot evidence. This is not only a route mapping. It transcribes the relevant source-document content Integration needs before moving or reconciling UI page code.

Important terminology: the audited repository does not contain editable Figma files (`.fig`, `.figjam`) or `figma.com` links for these pages. The source evidence is high-fidelity mockup PNG / concept screenshot files under `/Users/changdali/Desktop/UI/界面示意图/`, plus mapping, implementation sequence, closure audit, and runtime screenshot review documents.

## Integration Use Rules

1. Treat this document as a source handoff packet for Integration planning.
2. Do not wholesale merge a branch from this evidence alone.
3. Do not treat legacy module pages as final high-fidelity pages without a page-by-page audit.
4. Preserve gated behavior unless a separate executor/report/export gate has been approved.
5. For LabTools, first reconcile route host differences. This UI line implemented LabTools pages mostly through `app/labtools_runtime.py` plus `app/shell/main_window.py`; later Integration work may route through `app/labtools/workspace.py`.

## Source Documents Copied Into This Handoff

| Source | What is copied here |
| --- | --- |
| `docs/ui/UI_C1_runtime_screenshot_review_20260521.md` | Concept screenshot inputs, runtime screenshot outputs, residual Figma/pixel-match limitation. |
| `docs/ui/UI_C1b2_bioinformatics_mockup_to_implementation_mapping_20260522.csv` | Bio mockup image paths, review decisions, required revisions, blocked runtime claims. |
| `docs/ui/UI_C2a_bioinformatics_page_implementation_sequence_20260522.csv` | Bio implementation scopes, state models, enabled/disabled actions, export gates, blockers. |
| `docs/ui/UI_C2g_bioinformatics_gated_ui_closure_audit_20260522.md` | Bio seven-step IA closure and formal executor/export boundaries. |
| `docs/ui/UI_C1d2_meta_analysis_mockup_to_implementation_mapping_20260522.csv` | Meta mockup IDs, image paths, allowed/disabled actions, gate semantics, forbidden claims. |
| `docs/ui/UI_C2a_meta_analysis_page_implementation_sequence_20260522.csv` | Meta staged implementation scope, allowed/forbidden runtime changes, tests, exit criteria. |
| `docs/ui/UI_C1c3b_labtools_mockup_to_implementation_mapping_20260522.csv` | LabTools accepted mockups, backend dependencies, required revisions, shell-only scope, forbidden features. |
| `docs/ui/UI_C2a_labtools_implementation_sequence_20260522.csv` | LabTools page build sequence, adapters, allowed active actions, disabled actions, must-not-enable items, tests. |
| `docs/ui/UI_C5a_runtime_visual_gap_matrix_20260524.csv` | Runtime screenshot vs mockup gap severity and rebuild/polish recommendations. |

## Global Concept Screenshot Packet

From `UI_C1_runtime_screenshot_review_20260521.md`:

- Source runtime: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`
- Concept image folder: `/Users/changdali/Desktop/UI/界面示意图`
- Runtime screenshot output: `docs/ui/runtime_screenshots/UI_C1_20260521/`
- Runtime limitation copied from the source review: UI-C1 screenshots are low-to-mid fidelity source renders, not pixel-matched Figma output.

Concept inputs copied for Integration:

| Concept | Runtime screenshot |
| --- | --- |
| IMG-01 Welcome / 欢迎页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-01_welcome_runtime.png` |
| IMG-02 Dashboard / 工作台首页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-02_dashboard_runtime.png` |
| IMG-03 Settings / 设置中心 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-03_settings_runtime.png` |
| IMG-04 LabTools / 实验工具首页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-04_labtools_home_runtime.png` |
| IMG-05 Bioinformatics 首页 | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-05_bioinformatics_home_runtime.png` |
| IMG-06 Meta Question & Type | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-06_meta_question_type_runtime.png` |
| IMG-07 Bio Data Source | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-07_bio_data_source_runtime.png` |
| IMG-08 Bio Data Check & Preparation | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-08_bio_data_check_preparation_runtime.png` |
| IMG-09 Meta Search Strategy | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-09_meta_search_strategy_runtime.png` |
| IMG-10 Bio Result & Report | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-10_bio_result_report_runtime.png` |
| IMG-11 Bio Group & Design | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-11_bio_group_design_runtime.png` |
| IMG-12 Meta Full-text Management | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-12_meta_fulltext_management_runtime.png` |
| IMG-13 Meta Extraction Form Design | `docs/ui/runtime_screenshots/UI_C1_20260521/IMG-13_meta_extraction_form_design_runtime.png` |

## Shell Pages For Integration

| Page | Concept input | PySide files | Current handoff note |
| --- | --- | --- | --- |
| Welcome / About | IMG-01 | `app/shell/login.py`; `app/shell/main_window.py` | Login/welcome shell exists. Register and forgot-password remain placeholder-class behavior unless separately implemented. |
| Dashboard / Module selection | IMG-02 | `app/shell/module_selection.py`; `app/shell/dashboard.py`; `app/shell/sidebar.py`; `app/shell/main_window.py` | Shell route to Bio and Meta exists. LabTools target must be audited in the receiving Integration branch. |
| Settings Center | IMG-03 | `app/shell/settings_page.py`; `app/shell/main_window.py` | Settings is detect-first/resource-gated. Do not imply external engines, models, or packages are installed. |

## Bioinformatics: Copied Mockup And Implementation Content

### Bioinformatics PySide Code Targets

| Target | PySide code |
| --- | --- |
| Module host / IA | `app/bioinformatics/workspace.py` |
| Project Home | `app/bioinformatics/project_home.py` |
| Data Source / Data Check / Group Design / Analysis Tasks / Result / Export | `app/bioinformatics/workflow_pages.py` |
| Legacy pages not final high-fidelity | `app/bioinformatics/pages/**`; `app/bioinformatics/legacy/**` |

### Bioinformatics Mockup Mapping Copied From Source

| Image file | Target screen | Page key | Review decision | Implementation reference status | Readiness | Required revisions | Blocked runtime claims |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | Project Home | `bio.page.project_home` | `text_revisions` | `implementation_reference_with_text_revision` | `ready_for_planning` | replace Active; revise Completed/Ready labels; keep formal gates disabled | formal DEG ready; report/export ready; TCGA+GTEx auto merge |
| `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Data_Source_Selection_candidate_v2_20260522.png` | Data Source Selection | `bio.page.data_source` | `text_revisions` | `implementation_reference_with_text_revision` | `ready_for_planning` | add TCGA/GTEx non-auto-merge warning; rename Completed to Imported; clarify import is not analysis readiness | analysis readiness from import; source download complete by selection; TCGA+GTEx default merge |
| `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Data_Check_Preparation_Readiness_Table_candidate_20260522.png` | Data Check & Preparation | `bio.page.data_check_preparation` | `boundary_review` | `implementation_reference_with_boundary_review` | `ready_for_planning_with_gates` | make Save Report disabled/copy-only; revise formal-stage wording; label data readiness as input readiness | formal analysis enabled by data checks alone; formal report save; analysis result |
| `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Group_Design_Comparison_Setup_candidate_20260522.png` | Group & Design | `bio.page.group_design` | `boundary_review` | `implementation_reference_with_boundary_review` | `ready_for_planning_with_gates` | rename Preflight-Ready; mark persistence adapter-needed; clarify covariates do not enable multifactor DEG | multifactor DEG; design pass enables formal run; active persistent edits without adapter |
| `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Analysis_Tasks_DEG_Preflight_candidate_20260522.png` | Analysis Tasks / DEG Preflight | `bio.page.analysis_tasks` | `boundary_review` | `implementation_reference_with_boundary_review` | `ready_for_planning_with_gates` | label DESeq2 as policy/planned executor if shown; rename Preflight Done to Preflight log available; keep No Result explicit | formal DEG/ORA/GSEA/KM/Cox/Clinical run; preflight as result; active formal DESeq2 |
| `/Users/changdali/Desktop/UI/界面示意图/bioinformatics/Bioinformatics_Result_Report_Export_Gate_candidate_v2_20260522.png` | Result & Report plus Export Gate | `bio.page.result_report`; `bio.page.report_export` | `boundary_review` | `split_reference_for_two_pages` | `ready_for_planning_with_split` | split Result & Report from Report Export; rename Report Draft Boundary; add result semantic annotations; keep export disabled | report-ready package; formal figures; active export; preflight logs as formal results |

### Bioinformatics Implementation Sequence Copied For Integration

| Stage | Page key | Page | Implementation scope | State model | Enabled actions | Disabled actions | Result/report/export gate | Implementation blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UI-C2b | `bio.page.project_home` | Project Home / 项目首页 | project summary, seven-step flow, recent project, quick links | `feature.status.developer_preview`; `dataState=no_project_or_project_loaded` | navigation; create/open project if existing runtime supports it | formal run; report-ready; export | `resultSemanticKey=not_a_result`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | text revisions for Active/Completed/Ready wording |
| UI-C2b | `bio.page.data_source` | Data Source / 数据来源 | source cards for local/GEO/TCGA/GTEx and source registration boundary | `feature.status.testing`; `source.status.*` | source card navigation; existing source registration actions if already available | TCGA+GTEx auto merge; direct analysis run | `resultSemanticKey=not_a_result`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | must add TCGA/GTEx non-auto-merge warning |
| UI-C2b | `bio.page.data_check_preparation` | Data Check & Preparation / 数据检查与准备 | file recognition, readiness table, blocker/warning rows | `analysis.status.preflight_only`; `dataState=input_preflight_ready_or_blocked` | view/copy readiness; run preflight if existing runtime supports it | save formal report; execute analysis | `resultSemanticKey=preflight_only`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | report save must be disabled/copy-only |
| UI-C2b | `bio.page.group_design` | Group & Design / 分组与分析设计 | group assignment, comparison setup, covariate audit, design warnings | `analysis.status.preflight_only`; `dataState=design_preflight_ready_or_blocked` | in-memory design review; copy summary | persistent save; multifactor DEG; Cox modeling | `resultSemanticKey=preflight_only`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | storage adapter and covariate boundary copy required |
| UI-C2b | `bio.page.analysis_tasks` | Analysis Tasks / 分析任务 | gated task cards for DEG, ORA/GSEA, KM, Cox, clinical audit | `analysis.status.preflight_only_or_blocked`; `dataState=task_preflight_ready_or_blocked` | open preflight panels; developer diagnostics if explicit | formal DEG; formal ORA/GSEA; KM/log-rank; Cox; clinical conclusion | `resultSemanticKey=preflight_only`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | state/action gate carry-over required before any formal action |
| UI-C2b | `bio.page.result_report` | Result & Report / 结果与报告 | result browser, semantic chips, report draft preview | `feature.status.testing`; resultSemanticKey from result registry or testing_level | view testing/imported/preflight entries; copy draft text | fake plots; formal report generation; report-ready package | `resultSemanticKey=testing_level_by_default`; `reportStatusKey=draft`; `exportGate=disabled_missing_report_ready` | split from Report Export and carry result semantic contract |
| UI-C2b | `bio.page.report_export` | Report Export / 报告导出 | export gate status, disabled export actions, package readiness explanation | `report.status.draft_or_blocked`; `exportGate=disabled_missing_report_ready` | view gate status only | PDF/DOCX/ZIP/package export; share/archive | resultSemanticKey mirrors selected result; `reportStatusKey=draft`; `exportGate=disabled_missing_report_ready` | report-ready gate and file/export adapter missing |
| UI-C2b | `bio.page.settings_resources` | Bioinformatics Settings & Resources | resource status, external dependencies, diagnostics link | resource.status.not_configured_or_available | detect/review existing resources if implemented | install/update/cloud config unless existing safe gate exists | `resultSemanticKey=not_a_result`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | resource install/update policy must stay user-triggered |
| UI-C2b | `bio.page.project_logs` | Project Logs & Technical Details | developer diagnostics, logs, technical artifact paths | `feature.status.developer_preview` | view diagnostics | normal user formal run actions | `resultSemanticKey=not_a_result`; `reportStatusKey=draft`; `exportGate=disabled_empty_result` | must stay diagnostic and not normal user workflow |

### Bioinformatics Closure Text Copied For Integration

The implemented target main flow remains seven steps:

1. Project Home / 项目首页
2. Data Source / 数据来源
3. Data Check & Preparation / 数据检查与准备
4. Group & Design / 分组与分析设计
5. Analysis Tasks / 分析任务
6. Result & Report / 结果与报告
7. Report Export / 报告导出

Implemented and retained in the gate shell:

- state builder / page state summary
- action gate model
- dependency/gate status model
- result availability gate
- report/export gate preview
- semantic labels and status keys

Data Source ordinary UI shows exactly four primary sources:

- GEO
- TCGA
- GTEx
- Local File

Data Check & Preparation includes readiness coverage for:

- expression matrix integrity
- sample annotation completeness
- clinical data completeness
- gene annotation mapping
- batch/platform consistency
- missing rate check
- outlier sample detection

Analysis Tasks includes a gated task matrix for:

- DEG
- ORA
- GSEA
- KM / log-rank
- Cox
- Clinical Association

All visible task write/preflight/formal run/plot/report/export actions remain disabled or gated. No formal DEG, ORA, GSEA, KM, Cox, survival, clinical association, result table, plot, report, or export executor is enabled in the ordinary UI.

### Bioinformatics Commits For Integration Reference

| Commit | Meaning |
| --- | --- |
| `08e9bd1` | Bioinformatics gate shell |
| `900ba60` | Project Home + Data Source gated pages |
| `62739aa` | Data Check & Preparation + Group & Design gated pages |
| `4061d72` | Analysis Tasks gated page |
| `2d5a560` | Result & Report / Report Export split pages |
| `2063ce8` | Bioinformatics Workbench surface rebuild |

## Meta Analysis: Copied Mockup And Implementation Content

### Meta PySide Code Targets

| Target | PySide code |
| --- | --- |
| Active Meta workspace and high-fidelity shell pages | `app/meta_analysis/workspace.py` |
| Older functional/hybrid pages | `app/meta_analysis/pages/**` |
| Runtime services, not visual page proof | `app/meta_analysis/services/**`, `app/meta_analysis/models/**`, `app/meta_analysis/stats/**` |

### Meta Mockup Mapping Copied From Source

| Mockup ID | Screen ID | Image path | Review decision | Priority | UI stage | Allowed actions | Disabled actions | Gate semantics | Must not implement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META-MOCK-001 | META-001 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | accepted | P0 | Meta UI-C2a gate/state planning | open/create project shell; view workflow overview; view project summary; navigate next step | run search; import references; run statistics; generate report; export | feature.status.shell_only; developer_preview; result.semantic.testing_summary_only; report.status.draft | production systematic review; fake result; forest plot; pooled effect; report-ready; active export; CNKI/WanFang/VIP direct retrieval |
| META-MOCK-002 | META-002 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Question_Meta_Type_Selection_candidate_v2_20260522.png` | accepted | P0 | Meta UI-C2a gate/state planning | edit research question; edit English question; edit PICO/PECO draft; select active Meta type; proceed to Search Strategy | Network Meta activation; reviewer final confirmation; search execution; result generation; report/export | feature.status.testing; schema_shell; Network Meta planned_disabled | Network Meta active; AI final question; pooled effect; forest plot; report-ready; export |
| META-MOCK-003 | META-003 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Search_Strategy_Builder_candidate_20260522.png` | accepted_with_minor_revision | P0 | Meta UI-C2a gate/state planning | draft English query; edit term groups; preview Boolean query; copy query; select database draft scope | execute PubMed/Embase/WOS; Chinese database direct retrieval; auto import; auto PRISMA update; final search confirmation | feature.status.testing; English-first processing; draft_only; AI suggestion advisory | CNKI/WanFang/VIP execution; executed result list; automatic search conclusion |
| META-MOCK-004 | META-003;META-004;META-005 | `/Users/changdali/Desktop/UI/界面示意图/Meta/图 4：Import : Reference Management + Deduplication` | accepted_with_boundary_review | P0 | Meta UI-C2a gate/state planning | view import source cards; preview reference table; review duplicate groups; compare duplicates as draft | real import; automatic merge; automatic delete; auto-send to screening; final included studies | feature.status.testing; local_draft_only; reviewer_dedup_required | silent dedup merge; production library; Chinese DB online import; final PRISMA counts |
| META-MOCK-005 | META-006 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Screening_Workspace_candidate_20260522.png` | accepted_with_minor_revision | P0 | Meta UI-C2a gate/state planning | view queue; view reference detail; save include/exclude/uncertain/full-text draft decision; record exclusion reason draft | final screening decision; AI automatic decision; final PRISMA count; automatic full-text inclusion | feature.status.testing; manual_review; AI suggestion advisory; draft_counts | AI automatic conclusion; final included studies; multi-reviewer adjudication complete |
| META-MOCK-006 | META-007;META-008 | `/Users/changdali/Desktop/UI/界面示意图/Meta/图 6：Extraction + Risk of Bias` | accepted_with_minor_revision | P0/P1 | Meta UI-C2a gate/state planning | view full-text library; edit draft extraction fields; view ROB draft domains; mark draft extracted only if adapter planned | automatic PDF extraction; Chinese PDF OCR; final extraction save; automatic ROB judgement; formal analysis input | feature.status.testing; draft_extraction; risk_of_bias_preview; reviewer_confirmation_required | Chinese PDF extraction; auto final extraction; auto risk judgement; formal pooled effect; forest plot; report-ready |
| META-MOCK-007 | META-010;META-011;META-012 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta 图 7：Result Review + Report-ready Gate` | accepted_with_boundary_review | P0/P2 | Meta UI-C2a gate/state planning | view result readiness summary; view draft pairwise input preview; view report-ready blockers; acknowledge gate state | formal pooled result; forest plot; heterogeneity; publication bias; mark report-ready; generate report; export | result.semantic.testing_summary_only; report.status.draft; report_ready blocked; exportGate disabled_empty_result | fake forest plot; pooled HR/OR/RR; fake heterogeneity; publication bias result; report-ready success |
| META-MOCK-008 | META-013 | `/Users/changdali/Desktop/UI/界面示意图/Meta/Meta_Report_Export_Gate_candidate_20260522.png` | accepted_with_boundary_review | P2 | Meta UI-C2a gate/state planning | view report template preview; view export readiness; view disabled format reasons | DOCX export; HTML export; PDF export; CSV export; XLSX export; ZIP export; report-ready package generation | report.status.draft; report_ready gate_not_passed; exportGate disabled; no_file_write | active export; fake report-ready; formal package; generated report artifacts |

### Meta Implementation Sequence Copied For Integration

| Stage | Sequence | Target pages | Source mockups | Implementation scope | Allowed runtime changes | Forbidden runtime changes | Required tests | Exit criteria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Meta UI-C2b | 1 | Project Home; Question & Meta Type | META-MOCK-001; META-MOCK-002 | Implement gated project overview and question/type shell pages | page layout; workflow navigation; status chips; draft research question fields; active Meta type selection shell; Network Meta planned disabled callout | executor integration; Network Meta activation; final protocol confirmation; search execution; report/export | IA stability; 10 main-flow + Meta Settings; Network Meta inactive; question/type draft-only; no result/report/export | Project Home and Question/Type render with Developer Preview/testing boundaries and no executable analysis actions |
| Meta UI-C2c | 2 | Search Strategy; Import/Reference Management; Deduplication | META-MOCK-003; META-MOCK-004 | Implement gated search draft and reference/dedup preview shells | English query draft UI; term groups; database draft selection; reference table preview; duplicate risk panel; adapter-needed import actions | Chinese DB direct retrieval; PubMed/Embase/WOS execution; real import; auto dedup merge/delete; auto screening handoff; PRISMA updates | no Chinese DB direct retrieval; database selections draft-only; import/dedup actions disabled/gated; no files written | Search and reference/dedup pages render as draft-only/gated surfaces |
| Meta UI-C2d | 3 | Screening; Full-text/Extraction; Risk of Bias | META-MOCK-005; META-MOCK-006 | Implement gated manual-review shells for screening, extraction, and risk-of-bias preview | reference queue; draft screening decisions; advisory AI panel; full-text library shell; type-specific extraction form; draft RoB domain table | AI final decisions; final included studies; Chinese PDF extraction; automatic extraction; automatic RoB judgement; final quality score; analysis input promotion | AI suggestion only; draft decision wording; no Chinese PDF extraction; no final extraction/ROB; no analysis-ready dataset | Screening/extraction/RoB pages render with draft/manual-review boundaries and disabled final actions |
| Meta UI-C2e | 4 | Result Review; Report-ready Gate; Report Export | META-MOCK-007; META-MOCK-008 | Implement gated result/report/export pages and shared RRE shell adoption | result readiness summary; empty forest/table boundary; report-ready blocker checklist; disabled export format controls | fake forest plot; fake pooled effect; heterogeneity/publication bias values; mark report-ready; generate report; DOCX/HTML/PDF/CSV/XLSX/ZIP export | result_semantic testing_summary_only/no_formal_result; report_status draft/blocked; export disabled; no file write | Result/report/export shell renders with all actions disabled and no fake outputs |
| Meta UI-C2f | 5 | Closure audit | all | Audit C2b-C2e implementation closure | documentation and status matrix only | runtime UI changes; tests changes unless audit-only test is explicitly needed; executor/report/export enablement | all focused UI tests; source smoke; diff checks | Closure report confirms gates remain intact and forbidden capabilities remain off |

### Meta Commits For Integration Reference

| Commit | Meaning |
| --- | --- |
| `bf6aaf8` | Meta Analysis project and question gated pages |
| `e551f44` | Search and reference gated pages |
| `557b645` | Screening / extraction / ROB gated pages |
| `6fe2295` | Result / report / export gates |
| `87f3f9a` | Meta Analysis Workbench surface rebuild |
| `dde15c2` | Meta layout rebuild with Workbench primitives |

## LabTools: Copied Mockup And Implementation Content

### LabTools PySide Code Targets

| Target | PySide code |
| --- | --- |
| Runtime/calculation/storage models | `app/labtools_runtime.py` |
| Page host in this UI line | `app/shell/main_window.py` |
| Settings-linked external engine surface | `app/shell/settings_page.py` |
| Later Integration route host to reconcile | `app/labtools/workspace.py` if present in target branch |

### LabTools Mockup Mapping Copied From Source

| Mockup ID | Mockup name | Image path | Review decision | Implementation group | Priority | Backend / adapter dependency | Can enter C2a | Required revision | Shell-only scope | Must not implement now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `labtools_home` | LabTools Home | `/Users/changdali/Desktop/UI/界面示意图/IMG-04 LabTools : 实验工具首页.png` | accepted_with_text_revisions | first_batch_ui_c2a_planning | P0 | none for shell; text revisions before implementation reference | yes | replace overclaim text; add homepage review notice | none | ImageJ/Fiji first-level; inventory; cloud sync; LAN sharing; collaboration |
| `quick_formula` | Quick Calculator + Dynamic Formula Solver | `/Users/changdali/Desktop/UI/界面示意图/labtools/Quick Calculator + Dynamic Formula Solver.png` | accepted_with_boundary_review | first_batch_ui_c2a_planning | P0 | UI adapter for calculator/formula surfaces; history store later | yes | mark cell plating helper as calculation helper only | save history and export remain adapter-needed | WB; SDS-PAGE; BCA; ELISA; qPCR workflow; cell record saving |
| `reagent_workflow` | Reagent Template + Preparation Workflow | `/Users/changdali/Desktop/UI/界面示意图/labtools/2. Reagent Template + Preparation Workflow.png` | accepted_with_text_revisions | first_batch_ui_c2a_planning | P0 | BioMedPilot storage-root adapter; file-picker/export adapter | yes | make save-template action visually disabled or secondary adapter-needed | save template/preparation/export remain adapter-needed | inventory decrement; production batch release; cloud template library; multi-user sync |
| `wb_loading` | Western Blot Loading focused mockup | `/Users/changdali/Desktop/UI/界面示意图/labtools/3. Western Blot Loading + SDS-PAGE Gel.png` | accepted_with_boundary_review | first_batch_ui_c2a_planning | P0 | WB UI adapter; storage/export adapter for save/export | yes | add note that later protein workflow steps are placeholders | later protein workflow steps are roadmap/shell | fake gel bands; image analysis; automatic band recognition; antibody recommendation |
| `bca_od` | BCA / OD MVP Boundary | `/Users/changdali/Desktop/UI/界面示意图/labtools/4. BCA : OD MVP Boundary.png` | accepted_with_text_revisions | second_batch_adapter_review | P1 | BCA record store/export model; UI adapter for MVP preview | conditional | soften success wording; qualify calculation as MVP preview | save/export remain disabled or adapter-needed | ELISA; 4PL; formal report; production save/export; clinical-grade quantification |
| `cell_workspace` | Cell Experiment Workspace | `/Users/changdali/Desktop/UI/界面示意图/labtools/图 5：Cell Experiment Workspace : 细胞实验工作区.png` | accepted_with_boundary_review | shell_only_until_store_adapter | P1 | CellExperimentRecordStore; cell profile/state models; ImageJ/Fiji external engine adapter | conditional | keep save/run actions disabled; preserve no-ELISA boundary | cell profile; record templates; result processing; ImageJ/Fiji callout | ELISA in cell page; real record save; fake records; fake timeline; automatic ROI; automatic cell counting; ImageJ/Fiji execution |
| `reagent_side_panel_detail` | Additional mockup: Reagent side panel detail | not_generated | recommended | additional_mockup_needed | P1 | storage adapter and validation mapping | no | generate detailed side panel mockup | validation/save boundary | active template save without adapter |
| `wb_lane_warning_detail` | Additional mockup: WB lane/warning detail | not_generated | recommended | additional_mockup_needed | P1 | WB UI adapter; warning row semantics | no | generate lane and warning detail mockup | lane schematic/warning boundary | fake gel bands; completed export |
| `elisa_immuno_boundary` | Additional mockup: ELISA / Immuno-Absorbance boundary | not_generated | recommended | additional_mockup_needed | P2 | ELISA MVP backend | no | generate separate boundary mockup under Immuno/Absorbance | blocked_until_backend | ELISA inside Cell Experiment; ELISA result; 4PL; formal report; active export |

### LabTools Implementation Sequence Copied For Integration

| Batch | Sequence | Screen ID | Screen name | Implementation scope | Backend readiness | Required adapter / contract | Allowed active actions | Disabled / adapter-needed actions | Must not enable | Required tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ui_c2_first_batch | 1 | `labtools_home` | LabTools Home | Apply accepted three-entry IA, text revisions, review notice, recent activity empty state, quick access links. | shell_ready | LabTools IA model; disabled state model | navigation to three LabTools branches | recent activity history remains empty/shell | ImageJ/Fiji first-level entry; inventory; cloud sync; LAN sharing; collaboration; save/export on home | IA regression; no ImageJ/Fiji first-level; UI smoke |
| ui_c2_first_batch | 2 | `quick_calculator` | Quick Calculator | Render quick task registry, calculator form, result preview, warning/review rows, copy action. | active_backend_ready_ui_adapter_needed | UI-facing error normalization; LabTools result/warning view model | copy calculated text when valid | save history disabled_missing_storage_adapter or future; export future/disabled_missing_file_picker | WB/SDS-PAGE/BCA/ELISA/qPCR workflow/cell record saving inside General Calculator | view model tests; disabled save/export tests; calculation error tests |
| ui_c2_first_batch | 3 | `formula_solver` | Dynamic Formula Solver | Render formula selector, solve-target control, unit-aware inputs, solved result preview. | active_backend_ready_ui_adapter_needed | UI-facing error normalization; LabTools result/warning view model | copy solved result when valid | save history disabled_missing_storage_adapter or future; export future | fake values on invalid input; validated protocol claim | formula view model tests; invalid input tests; copy-only tests |
| ui_c2_first_batch | 4 | `reagent_template_preparation_shell` | Reagent Template / Preparation Shell | Render template list, selected template summary, preparation run preview shell, adapter notices. | active_backend_ready_ui_adapter_needed | BioMedPilotLabToolsStorageAdapter contract; result/warning view model | copy preparation summary preview if calculated | save template/preparation disabled_missing_storage_adapter; export disabled_missing_file_picker/future | inventory deduction; production batch release; cloud template library; multi-user sync | storage adapter disabled-state tests; no default `~/.labtools` write test; reagent model tests |
| ui_c2_second_batch | 5 | `reagent_template_editor` | Reagent Template Editor Side Panel | Implement validation, dirty state, pH fields, component table, disabled save footer. | active_backend_ready_ui_adapter_needed | BioMedPilotLabToolsStorageAdapter contract; error normalization | copy component summary if generated | save template disabled_missing_storage_adapter until adapter active | active save without project storage; version management claim; inventory/cloud features | editor validation tests; disabled save tests |
| ui_c2_second_batch | 6 | `reagent_preparation_run` | Reagent Preparation Run | Render calculation preview, component table, pH/review notice, copy summary. | active_backend_ready_ui_adapter_needed | BioMedPilotLabToolsStorageAdapter; FilePickerExportAdapter future; result view model | copy preparation summary | save preparation disabled_missing_storage_adapter; export disabled_missing_file_picker | inventory consumption; audit trail; production batch release | preparation result view model tests; save/export disabled tests |
| ui_c2_second_batch | 7 | `wb_loading_focused` | Western Blot Loading Focused Page | Render WB config, sample table, calculation table, schematic lane preview, S3 warning. | active_backend_ready_ui_adapter_needed | UI-facing error normalization; FilePickerExportAdapter; storage adapter; WB result/warning model | copy WB table/summary | save WB record disabled_missing_storage_adapter; CSV/Markdown export disabled_missing_file_picker | fake gel bands; image analysis; automatic band recognition; antibody recommendation; downstream workflow activation | WB warning row tests; export gate tests; lane preview boundary tests |
| ui_c2_third_batch | 8 | `sds_page_placeholder` | SDS-PAGE Placeholder/Subpage | Render adapter-safe SDS-PAGE subpage or workflow placeholder after WB focus is stable. | active_backend_ready_ui_adapter_needed | FilePickerExportAdapter; persistent template adapter future | copy component table preview | template save disabled_missing_storage_adapter; XLSX export disabled_missing_file_picker | complete protein workflow claim; active export without file picker | SDS disabled export tests; template state tests |
| ui_c2_third_batch | 9 | `bca_od_mvp_boundary` | BCA / OD MVP Boundary | Render OD matrix, annotation side panel, linear-fit preview, warning list as MVP/testing only. | testing_preview_only_ui_adapter_needed | BCA result/warning view model; BCA record/export future | copy safe preview only if supported | save/export disabled_backend_missing | ELISA; 4PL; formal report; production save/export; clinical-grade quantification | BCA boundary tests; no ELISA/formal report semantic tests |
| ui_c2_third_batch | 10 | `cell_experiment_workspace_shell` | Cell Experiment Workspace Shell | Render cell profile/state area, record template categories, result processing callout, empty timeline. | shell_only_blocked_until_backend | CellExperimentRecordStore future; ImageJ/Fiji external engine adapter future | navigation/help links only | record save blocked_until_backend; image analysis blocked_until_backend | fake records; fake timeline; automatic ROI; automatic cell counting; ImageJ/Fiji execution; ELISA card | cell shell boundary tests; no fake records tests; Settings-linked ImageJ/Fiji tests |
| ui_c2_third_batch | 11 | `elisa_immuno_absorbance_boundary` | ELISA / Immuno-Absorbance Boundary | Render blocked ELISA boundary under Immuno/Absorbance with disabled run/save/export. | blocked_until_backend | ELISA MVP backend future | navigation to BCA/OD MVP or guidance only | run/save/export blocked_until_backend | active ELISA; active 4PL; formal report; production save/export; clinical-grade quantification | ELISA blocked-state tests; disabled action tests |
| ui_c2_third_batch | 12 | `image_processing_workspace_boundary` | Image Processing Workspace Boundary | Render Settings-linked ImageJ/Fiji external-engine boundary and disabled processing controls. | shell_only_until_external_engine_adapter | ImageJ/Fiji external engine adapter future | Settings navigation/help only | run image analysis blocked_until_backend; save/export blocked_until_backend | macro execution; automatic ROI; automatic cell counting; automatic band recognition; active batch processing | image processing boundary tests; no macro/auto analysis tests |

### LabTools Commits For Integration Reference

| Commit | Meaning |
| --- | --- |
| `3bf79f4` | LabTools navigation shell |
| `ca006ee` | General calculator UI |
| `f18b9a0` | Reagent preparation UI |
| `a33cffe` | WB loading UI |
| `00f4ec6` | LabTools boundary pages |
| `edfa2a5` | LabTools storage adapter skeleton |
| `7afe07b` | Local data store UI read paths |
| `e64454b` | Local reagent write UI integration |
| `b40cc8d` | Local sample write UI integration |
| `ed396b4` | LabTools Workbench surface rebuild |
| `4999405` | LabTools dense page layout rebuild |
| `4cd06fb` | LabTools cell experiment workspace revamp |

## Runtime Visual Gap Content Copied For Integration

From `UI_C5a_runtime_visual_gap_matrix_20260524.csv`:

| Runtime page | Mockup reference | Gap severity | Recommended action | Integration meaning |
| --- | --- | --- | --- | --- |
| Dashboard home | `IMG-02 Dashboard : 工作台首页.png` | medium | local polish | Shell is usable but not final visual fidelity. |
| LabTools home | `IMG-04 LabTools : 实验工具首页.png` | medium | local polish | IA is acceptable, visual rhythm still needs polish. |
| LabTools general calculator | `labtools/Quick Calculator + Dynamic Formula Solver.png` | high | extract primitives then rebuild | Calculator exists but should not be treated as final visual quality. |
| LabTools reagent preparation | `labtools/2. Reagent Template + Preparation Workflow.png` | critical | rebuild layout skeleton | Three-column layout pressure must be rebuilt before final UI. |
| LabTools WB loading | `labtools/图 2：WB lane : warning detail.png` | critical | rebuild layout skeleton | Config/sample/result/lane layout needs controlled widths. |
| LabTools experiment boundaries | `labtools/图 5：Cell Experiment Workspace : 细胞实验工作区.png` | medium | local polish | Boundary cards exist but do not match richer workspace structure. |
| Bioinformatics project home | `bioinformatics/Bioinformatics_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | medium | local polish | Seven-step IA and gates are acceptable; visual polish still needed. |
| Bioinformatics data source | `bioinformatics/Bioinformatics_Data_Source_Selection_candidate_v2_20260522.png` | medium | local polish | Source cards exist; no formal import/execution should be enabled. |
| Bioinformatics analysis tasks | `bioinformatics/Bioinformatics_Analysis_Tasks_DEG_Preflight_candidate_20260522.png` | high | rebuild layout skeleton | Task matrix is clipped/scroll-heavy; preserve disabled formal actions. |
| Bioinformatics result/export | `bioinformatics/Bioinformatics_Result_Report_Export_Gate_candidate_v2_20260522.png` | high | rebuild layout skeleton | Export affordance and gate hierarchy need rebuild; no active export. |
| Meta project home | `Meta_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | critical | rebuild layout skeleton | Original runtime differs from mockup hierarchy; C5c improves but does not prove final fidelity. |
| Meta question/type | `Meta_Question_Meta_Type_Selection_candidate_v2_20260522.png` | critical | rebuild layout skeleton | Candidate cards and PICO table need shared primitives. |
| Meta search strategy | `Meta_Search_Strategy_Builder_candidate_20260522.png` | high | rebuild layout skeleton | English-first/no Chinese DB execution must remain. |
| Meta screening/extraction | `Meta_Screening_Workspace_candidate_20260522.png` | high | rebuild layout skeleton | No AI final decision or automatic extraction. |
| Meta result/export | `Meta_Report_Export_Gate_candidate_20260522.png` | critical | rebuild layout skeleton | Export remains disabled and file write false. |
| Settings home | `IMG-03 Settings : 设置中心.png` | critical | rebuild layout skeleton | User settings hierarchy must not imply external tools/cloud/model enabled. |

## Final Integration Boundary

This handoff is meant to help Integration recover and reconcile page code. It is not approval to migrate everything at once. Integration should:

1. start from the accepted Shell baseline and current target branch state;
2. compare each target page against the PySide files listed above;
3. migrate one route/page group at a time;
4. keep all formal executor/report/export actions disabled unless separate runtime proof exists;
5. run screenshot and route tests after each page group;
6. update Project Control ledgers with `figma/new`, `old`, `hybrid`, `placeholder`, `missing`, or `not-final-fidelity` status after runtime inspection.
