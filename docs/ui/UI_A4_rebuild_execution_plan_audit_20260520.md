# UI-A4 v1 Rebuild Execution Plan Audit

Date: 2026-05-20

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/UIShell`

Branch: `dev/ui-shell`

Audited HEAD at report start: `c94d9cb`

## 1. 审计范围

本阶段综合以下输入形成 UI 重构路线、阶段拆分、依赖关系、风险边界、测试策略、文档治理、资源治理、i18n 治理和后续校准规则：

| input | status | audit_use |
|---|---|---|
| `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` | found | Target IA, page map, conflicts, reuse/rebuild/hide guidance. |
| `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | found | Brand/resource/design token/style/packaging risk baseline. |
| `docs/ui/UI_A3_i18n_readiness_audit_20260520.md` | found | i18n key, terminology, report/template and test migration baseline. |
| `docs/ui/target_design_drafts/**` | found, 9 Markdown files including README | Target draft input only, not direct development standard. |
| `docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md` | found | Cross-branch LabTools and runtime IA evidence. |
| `docs/ui/UI_Current_Information_Architecture_Audit_20260519.md` | found | Current `dev/ui-shell` user-visible runtime structure. |
| `docs/ui/UI_Freeze_Consolidation_Baseline_20260519.md` | found | Freeze/consolidation boundary and technical term governance. |
| `docs/ui/BioMedPilot_UI_Design_Constitution_v2_20260519.md` | found | UI design constitution and priority rules. |
| `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md` | found | Bioinformatics B8.0.1 analysis UI gating and result/report boundary. |
| `app/**` | scanned | Current shell, Bioinformatics, Meta, shared status, theme and app identity state. |
| `tests/**` | scanned | UI, Bioinformatics, Meta, package, shared tests and future assertion migration risks. |
| `scripts/package_app.py` | found | Static packaging identity and future UI-B10 context. |
| `dist/BioMedPilot.app/Contents/Info.plist` | found; static read only | Stale dist metadata risk. |
| `/Users/changdali/Desktop/BioMedPilot.app/Contents/Info.plist` | found; static read only | Stale desktop app metadata risk. |

No required input file was missing in this workspace. The report still treats target drafts and historical reports according to their document status, not as executable proof.

## 2. 本阶段性质：A4 v1 路线规划版

UI-A4 v1 is a planning audit, not implementation and not final integration acceptance.

This stage does not require Meta Analysis, Vocabulary, Bioinformatics B8.1+, or LabTools work to already be merged into Integration. Unmerged or still-developing module work is recorded as dependency, blocker, parallel work, or future calibration input.

The immediate product decision is:

- A4 v1 can be completed now.
- The next development stage should be UI-B0.
- Do not jump directly to UI-B1 or UI-B2.
- Do not expose planned/testing/shell-only/developer-preview features as production UI.

## 3. 未等待 Integration 的原因与后续 A4.1 校准规则

A4 v1 should not wait for all module branches to finish because it defines the governing route, document priority, status semantics, dependencies, and phase gates. Waiting for every module to land would postpone the master plan and allow continued drift from target drafts, historical pages, and current runtime shortcuts.

However, A4 v1 is not enough to authorize module feature exposure. After Meta Analysis, Vocabulary, Bioinformatics B8.1+, and LabTools work are merged or rebaselined into Integration, run:

`UI-A4.1：Integration 后 UI 重构路线校准审计`

A4.1 must re-check:

- Which module capabilities are actually present in Integration runtime.
- Which buttons can move from planned/testing/preflight to enabled.
- Whether Meta remains shell-only in UIShell or gains a calibrated runtime.
- Whether LabTools has a minimal shell, full shell, or only backend/package evidence.
- Whether Vocabulary/terminology interfaces are stable enough for i18n keys and report templates.
- Whether packaging and desktop entry metadata still point to stale builds.

## 4. A1/A2/A3 关键结论汇总

| audit_source | key_findings | implications_for_rebuild | must_be_in_masterplan |
|---|---|---|---|
| UI-A1 target architecture audit | Target entry is Welcome -> Dashboard -> Bioinformatics / Meta Analysis / LabTools / Settings. Current Login, Dashboard, Sidebar, About and Settings need rebuild. Project/Data/Task/Report centers should not be top-level. Bioinformatics target is 7 main pages + 2 auxiliary pages. LabTools target is General Calculators, Reagent Preparation, Experiment Modules. Meta target is common workflow + Meta Type first. | Start with a MasterPlan and low-fidelity shell boundaries. Do not treat target drafts as final development standard. Hide or downgrade old technical centers and planned feature entries. | Page tree, entry hierarchy, visible/hidden/developer-diagnostic rules, reuse/rebuild/hide table, target-vs-current mapping. |
| UI-A2 visual/brand/resource audit | Current active assets are `BioMedPilot / 医研智析`, old Login, two-module Dashboard, Bio/Meta icons and partial light theme. `萤火虫 / Firefly`, Welcome/About visuals, LabTools icon, status icons, empty states, report/export icons and external resource icons are missing. Multiple palettes, local tokens and inline styles coexist. Dist and desktop app metadata are stale. | High-fidelity work must wait. UI-B1 must create token/component foundation before page rebuild. UI-B8 must handle resources after brand/Figma confirmation. UI-B10 must handle packaging and desktop entry later. | Visual Style Guide v1, brand hierarchy, resource inventory fields, placeholder/final status, single token source, packaging deferral. |
| UI-A3 i18n readiness audit | Chinese hardcoding is broad across shell, Bioinformatics workflow/report, Meta shell, feature status, tests and packaging display. Brand variables are unresolved. Bioinformatics states need keys such as `preflight_only`, `testing_level`, `imported_external_result`. Meta AI suggestion cannot become automatic conclusion. LabTools terms must stay stable. Reports need template i18n, not string replacement. | First UI version may remain mostly Chinese, but key boundaries and semantic status must be reserved. Tests should migrate away from pure literal text assertions. Report/template i18n must be separate from UI labels. | I18N Strategy v1, key naming rules, brand variables, status/result semantic keys, terminology table, test migration policy. |
| Current runtime IA audit | Current global nav is Dashboard, Bioinformatics, Meta Analysis, Settings, Testing Mode. Dashboard only has Bioinformatics and Meta. Bioinformatics has a multi-page Developer Preview workflow. Meta in UIShell is shell-only. Settings is placeholder. No LabTools in `dev/ui-shell`. | UI-B2 must rebuild global shell from current runtime, not historical reports. UI-B4 cannot claim LabTools runtime until minimal shell is integrated. UI-B6 cannot claim full Meta workflow. | Current runtime baseline and shell-only/planned/current labels. |
| Cross-branch runtime IA audit | Integration/ReleaseBuild source have fuller LabTools; stable/mainline has minimal ImageJ boundary; `dev/ui-shell` has no `app.labtools`. Project/Data/Task/Report center entries exist as hidden/model-only in some branches. | LabTools target is valid as a first-level module, but UI-B4 must begin with minimal shell or Integration-calibrated import. Do not copy old `imagej_fiji` as LabTools main page. | LabTools dependency and reuse rules; cross-branch evidence is reference until current runtime calibration. |
| Bioinformatics B8.0.1 audit | Bioinformatics is ready for rebuild planning, not formal DEG/GSEA/survival/clinical association/plot/report-ready UI. Current task center still has mixed maturity buttons like `运行 GEO 差异分析`; report is draft only. | UI-B5 may run in parallel with B8.1 but cannot bypass it. Formal-looking analysis actions must be gated, preflight-only, hidden, or disabled until resolver/result schema exists. | B8.1 dependency, analysis status keys, result semantics, report-ready blockers. |

## 5. UI 重构总原则

1. 先 `UI_Rebuild_MasterPlan`，再代码。
2. 先 low-fidelity shell，再 high-fidelity 视觉。
3. 先 token/component，再页面。
4. 先隐藏/降级旧入口，再暴露新入口。
5. 先 Settings 外部资源架构，再让模块调用外部引擎、模型和分析资源。
6. 先语义状态 key，再按钮文案。
7. Bioinformatics 不得在 B8.1 前暴露正式 DEG / GSEA / survival / clinical association / report-ready 按钮。
8. Meta Analysis 不得把 shell-only / testing / Developer Preview 写成 production workflow。
9. LabTools planned 子模块不得进入主操作区。
10. ImageJ/Fiji 配置进入 Settings，不作为 LabTools 主任务页。
11. i18n 先预留 key 边界，第一版 UI 可以仍以中文为主。
12. 打包、桌面入口、Finder 图标、LaunchServices 验证最后专项处理。
13. Integration 尚未合入的能力必须标记为依赖，不能提前作为可用 UI。
14. Codex 不得通过旧 Markdown 或旧分支页面绕过当前 MasterPlan。

## 6. UI-B0 到 UI-B10 阶段拆分

| stage | goal | allowed_scope | forbidden_scope | outputs |
|---|---|---|---|---|
| UI-B0 | Build the official UI master route. | New docs for MasterPlan, Visual Style Guide v1, I18N Strategy v1, Stage Index. Mark old/current/target/historical document priority. | UI code, resources, i18n runtime extraction, packaging. | `UI_Rebuild_MasterPlan_YYYYMMDD.md`, `UI_Visual_Style_Guide_v1_YYYYMMDD.md`, `UI_I18N_Strategy_v1_YYYYMMDD.md`, `UI_Rebuild_Stage_Index_YYYYMMDD.md`. |
| UI-B1 | Establish design tokens/theme/basic primitives. | Theme/tokens/components and focused tests for buttons, cards, tables, forms, status chips, empty state, diagnostics. | Business page rewrites, final Logo/icon replacement, packaging. | Single token source, primitives, status visual taxonomy. |
| UI-B2 | Rebuild Welcome / Dashboard / Sidebar / About / Test Feedback shell. | Low-fidelity three-module Dashboard, new sidebar IA, About shell, developer preview boundary. | Cloud account/subscription, high-fidelity brand visuals, LabTools planned features, Meta production workflow, desktop entry changes. | Low-fidelity global shell with Bio/Meta/LabTools cards and safe states. |
| UI-B3 | Build Settings shell and external resource entry. | General, account/subscription placeholder, project/storage, external engines/models/resources, developer diagnostics. Detect-first UI copy. | Real installers, automatic download/update/delete/upload, API key purchase flow, ImageJ/Fiji in LabTools main page. | Settings secondary IA and external resource status shell. |
| UI-B4 | Add LabTools target IA shell. | LabTools Home, General Calculators, Reagent Preparation, Experiment Modules shell, planned/hidden states. | Copy old Integration `imagej_fiji` main page, place BCA/SDS-PAGE/MTT/CCK-8 in general calculators, LAN/local-network sharing. | LabTools low-fidelity module shell after minimal runtime boundary. |
| UI-B5 | Reorganize Bioinformatics into 7 pages + 2 auxiliary pages. | Data Source, Data Check & Preparation, Group & Design, Analysis Tasks with gated/preflight states, Result & Report, Report Export draft semantics, settings/logs auxiliary pages. | Formal DEG/GSEA/survival/clinical association/report-ready buttons before B8.1+, imported DEG as recomputed, default TCGA+GTEx merge. | Target Bioinformatics IA shell and safer task/status model. |
| UI-B6 | Build Meta Analysis target IA shell. | Project Home, Question & Meta Type, Search Strategy, Import/Dedup, Screening, Full-text/Extraction, Quality Assessment, Meta Analysis Tasks, Result & Report, Report Export, Settings shell. | Production workflow claims, Network Meta formal entry, AI automatic conclusion, Chinese DB/PDF production claims unless calibrated. | Meta target shell with testing/planned status and AI disclaimers. |
| UI-B7 | Unify Result / Report / Export shell. | Shared result preview/draft/report draft/report-ready status model, empty states, export button gating, ASCII-safe filenames. | Fake plots, draft as final report, testing result as formal result, report-ready package without provenance. | Shared report/export semantic shell. |
| UI-B8 | Replace/add resources after brand freeze. | New Logo, App icon, module icons, status icons, empty states, report/export icons through resource inventory. | Unconfirmed App icon replacement, deleting old resources, archive icon as final, desktop `.app` overwrite. | Active resource inventory and placeholder/final mapping. |
| UI-B9 | Land i18n key boundaries and critical semantics. | Brand/nav/status/analysis/result/meta/lab/report/export keys; tests migrate to objectName/page_key/status enum. | One-shot translation, report string replacement, letting text carry function state. | Key registry/semantic status foundation, selected tests migrated. |
| UI-B10 | Packaging and desktop entry专项. | Package smoke, Info.plist, bundle display/name/executable/icon, stale dist cleanup, Finder/LaunchServices gate, codesign where required. | Early low-fidelity desktop overwrite, brand/icon changes before confirmation, old dist as current evidence. | Packaging validation report and approved desktop entry update. |

## 7. 阶段依赖图

| stage | depends_on | can_run_parallel_with | blocked_by | must_not_start_before |
|---|---|---|---|---|
| UI-B0 | UI-A1/A2/A3/A4 v1 | Bioinformatics B8.1 planning, Meta/LabTools/Vocabulary audits | User refusal to freeze document priority | Any UI code development. |
| UI-B1 | UI-B0 | Bioinformatics B8.1 backend planning, resource inventory prep | Missing Visual Style Guide v1 direction | UI-B0 documents are drafted and accepted enough for token names. |
| UI-B2 | UI-B1 | UI-B3 planning, LabTools minimal boundary audit | Brand/Figma needed only for high-fidelity; low-fi can proceed | UI-B1 primitives and status chips exist. |
| UI-B3 | UI-B1 and Settings architecture in UI-B0 | UI-B2 | Undefined external resource status model | UI-B0 resource/settings hierarchy and UI-B1 status tokens. |
| UI-B4 | UI-B0/B1 | UI-B3, LabTools backend/runtime audit | No LabTools minimal shell boundary in current runtime | LabTools target IA and current Integration status are calibrated. |
| UI-B5 | UI-B0/B1 | Bioinformatics B8.1 | Missing resolver/status/result schema for formal actions | B8.1 must not be bypassed; formal actions wait for B8.1+. |
| UI-B6 | UI-B0/B1 | Meta runtime/IA audit | UIShell Meta remains shell-only or uncalibrated Integration status | Meta shell-only boundary or post-Integration calibration is documented. |
| UI-B7 | UI-B0/B1 | B8.4/B8.5/B8.6 schema work, Meta report schema planning | Missing result/report schema for report-ready claims | First stage can be shell only; formal export waits for schema gates. |
| UI-B8 | UI-B0 Visual Style Guide and user brand/resource decisions | UI-B2 low-fi, UI-B3 shell | Unconfirmed brand, Logo, App icon, Figma, resource owner decision | User confirms brand/Logo/icon/Figma or placeholder policy. |
| UI-B9 | UI-B0 I18N Strategy, A3 key draft, UI-B1 status token | UI-B2-B7 shell work | Missing key naming rules and semantic status registry | UI-B0 key strategy exists. |
| UI-B10 | UI-B2-B9 basically stable | Packaging专项 only | Unfrozen brand/icon, unstable shell, no packaging permission | UI shell/resources/i18n boundaries are stable enough for packaging. |

## 8. 各阶段允许范围与禁止范围

| stage | allowed | forbidden | boundary_reason |
|---|---|---|---|
| UI-B0 | Documentation and route governance. | Runtime code, resources, packaging. | Prevents building from raw drafts or old branches. |
| UI-B1 | Shared visual and component foundation. | Business flow changes. | Stops further style drift before page work. |
| UI-B2 | Low-fidelity shell, new global IA. | Final brand visuals, account/subscription, production module claims. | Current Login/Dashboard need rebuild but brand assets are not frozen. |
| UI-B3 | Settings resource shell, detect-first copy. | Real installers, auto updates, cloud billing. | External engines/resources must not leak into module primary flows. |
| UI-B4 | LabTools IA shell and planned states. | Old ImageJ main page, planned experiment features as available. | LabTools is target first-level module but not current UIShell runtime. |
| UI-B5 | Bio target page grouping and gated/preflight states. | Formal analysis/result/report-ready claims. | B8.1 resolver/result schema is prerequisite. |
| UI-B6 | Meta IA shell and type registry shell. | Production systematic review workflow claims. | Current UIShell Meta is shell-only until calibration. |
| UI-B7 | Shared result/report/export status shell. | Fake plots and final report packages. | Report-ready depends on result schemas and provenance. |
| UI-B8 | Resource replacement after confirmation. | App icon or desktop package changes. | App icon/package identity are packaging risks. |
| UI-B9 | Key boundaries and semantic state landing. | Full translation by search/replace. | Function state must be semantic, not text-driven. |
| UI-B10 | Packaging and launch validation. | Early desktop overwrite. | Packaging belongs after UI and resources stabilize. |

## 9. 各阶段测试策略

| stage | required_tests | optional_tests | not_required_yet | pass_condition |
|---|---|---|---|---|
| UI-B0 | `git diff --check` | Markdown lint if available | Full UI tests, smoke, packaging | Only planned docs changed and diff check passes. |
| UI-B1 | theme/token tests, status label tests, focused component tests, `python3 -m app.main --smoke-test` | selected `tests/ui/test_app_theme.py`, screenshots if frontend visual changes justify it | package smoke | Token source renders without breaking shell smoke. |
| UI-B2 | welcome/sidebar/dashboard/about tests, module selection tests, smoke | selected snapshot tests for low-fi | package smoke, high-fidelity visual tests | New global shell uses semantic objectName/page_key; old login text assertions migrated. |
| UI-B3 | Settings nav tests, resource status shell tests, detect-first copy tests, developer diagnostics collapse tests | environment check unit tests | real install/update tests | Resource entries do not auto-install/download/delete/upload. |
| UI-B4 | LabTools dashboard/sidebar entry tests, LabTools IA tests, planned/hidden state tests, smoke | backend package tests if imported | final experiment workflow tests | LabTools appears only as allowed shell and planned entries stay gated/hidden. |
| UI-B5 | Bio workflow page tests, task gating tests, readiness/standardization display tests, report draft boundary tests, smoke | selected service tests | formal DEG/GSEA/survival/report-ready tests | Formal buttons are hidden/disabled/gated; imported DEG is external. |
| UI-B6 | Meta shell tests, Meta type registry tests, planned/hidden state tests, AI suggestion disclaimer tests, smoke | Meta专线 runtime tests after calibration | production report/PDF tests | Shell-only/testing status is visible and Network Meta is not formal. |
| UI-B7 | report status tests, export button gating tests, empty state tests, report draft disclaimer tests | manifest schema tests | publication-grade report export tests | Draft/testing/formal/report-ready states cannot be confused. |
| UI-B8 | icon path tests, resource inventory tests, module icon loading tests, smoke | visual screenshot checks after asset replacement | packaging icon validation | Every resource has inventory status and placeholder/final label. |
| UI-B9 | i18n key existence tests, status enum rendering tests, high-risk assertion migration tests | selected locale smoke if implemented | full multilingual release tests | Critical states are semantic keys/enums; tests no longer protect old Chinese text where unsafe. |
| UI-B10 | `python3 scripts/package_app.py --smoke-test`, `python3 -m app.main --smoke-test`, Info.plist inspection, bundle icon key inspection, `open -W -n dist/BioMedPilot.app --args --smoke-test`, direct `-psn_*` smoke if applicable, codesign if required | LaunchServices log inspection | module feature development | Package launch, Info.plist, icon and desktop entry are validated for the packaging target. |

Testing migration rules:

- Sidebar/navigation tests should assert nav keys, objectName and routes, not only Chinese labels or old order.
- Module selection tests should assert module IDs, button roles and availability states.
- Welcome/Login tests should become Welcome semantic tests; old account/VIP/license literals should not define the new first screen.
- Report tests should move from literal Markdown assertions to manifest, semantic status, provenance and disclaimer assertions.
- Packaging tests must remain UI-B10 or packaging专项; do not run packaged app in UI-B0-B9 unless explicitly scoped.

## 10. 文档治理规则

### 10.1 文档状态分类

| status | meaning | examples |
|---|---|---|
| `current` | Current governing document for development. | Future `UI_Rebuild_MasterPlan_YYYYMMDD.md`. |
| `target-draft` | User/target design input, preserved but not direct standard. | `docs/ui/target_design_drafts/**`. |
| `audit-only` | Evidence and risk analysis; informs MasterPlan but not implementation by itself. | UI-A1/A2/A3/A4, runtime IA audits, B8.0.1 audit. |
| `implementation-plan` | Stage route or implementation plan approved by MasterPlan. | Future UI-B stage plans. |
| `superseded` | Older plan replaced by MasterPlan or later audit. | Old stage reports after conflict resolution. |
| `historical` | Historical evidence only. | `docs/stage_UI_*`, old handoff reports, legacy archives. |
| `module-specific` | Module roadmap/status docs. | Bioinformatics B8 reports, Meta reports, LabTools reports. |
| `packaging-specific` | Packaging and desktop entry documents. | `docs/packaging.md`, future UI-B10 reports. |

### 10.2 Governance decisions

- A1/A2/A3/A4 are `audit-only / planning input`.
- `docs/ui/target_design_drafts/**` is `target-draft`, not direct development standard.
- `UI_Rebuild_MasterPlan` becomes the highest priority UI development standard after UI-B0.
- Historical stage reports cannot override the current MasterPlan.
- Future UI-B reports should live under `docs/ui/` unless clearly module-specific.
- Create `docs/ui/UI_Document_Index_YYYYMMDD.md` or `docs/ui/README.md` in UI-B0 to mark document status and priority.
- MasterPlan must declare precedence: MasterPlan > Visual Style Guide/I18N Strategy/Stage Index > current audit evidence > target drafts > historical reports.
- Integration changes after A4 v1 require UI-A4.1 calibration before module feature exposure.

## 11. 资源治理规则

| rule_area | rule |
|---|---|
| Active assets directory | Keep active resources under explicit directories such as `assets/icons/app`, `assets/icons/modules`, `assets/icons/status`, `assets/icons/settings`, `assets/images/empty_states`, `assets/images/welcome`, with inventory. |
| Legacy/archive resources | Archive resources are reference only; do not use directly as new standard without inventory, style review and owner decision. |
| New Logo/App icon/module icons | Require brand decision, Visual Style Guide, resource inventory and placeholder/final status before active use. |
| Resource inventory fields | `resource_id / path / type / purpose / module / status / size / format / light_dark_policy / source / used_by / owner_decision_required`. |
| Naming rules | Use stable module and purpose names: `app_icon`, `brand_logo`, `module_labtools`, `status_testing`, `empty_bio_no_project`, `report_export`. |
| Packaging icon changes | Defer to UI-B10 or packaging专项; do not change bundle icon key during low-fidelity phases. |
| Introduction order | First LabTools module icon for three-module Dashboard, then status icons, empty states, report/export icons, Settings resource icons, final App icon. |
| Figma resources | Enter repo only with export spec, owner decision, source note, size/format and light/dark policy. |
| Placeholder/final status | Placeholder resources must be labeled in inventory and UI copy when needed; never present placeholder as final brand asset. |

High-priority resource gaps from A2:

- Firefly / 萤火虫 Logo.
- Welcome/About visual.
- LabTools module icon.
- Settings resource icons.
- Status icons.
- Empty states.
- Report/export icons.
- External engines/models/analysis resources icons.

## 12. i18n 治理规则

First version can remain Chinese-first, but it must reserve i18n key and semantic boundaries.

| rule_area | rule |
|---|---|
| When to extract keys | Start in UI-B9 after UI-B0 strategy and UI-B1 status tokens; critical status keys may be introduced earlier if needed for gating. |
| Key naming | Use domain groups: `brand.*`, `nav.*`, `feature.status.*`, `analysis.status.*`, `result.semantic.*`, `meta.ai_suggestion.*`, `labtools.term.*`, `report.status.*`, `export.*`. |
| Brand variables | Separate visible brand, technical bundle name and report title; do not hardcode `BioMedPilot 生信项目报告` into future report templates. |
| Terminology location | UI-B0 should define the terminology table location; future Vocabulary work can fill canonical zh/en/es terms. |
| Report template language parameters | Report templates should accept `language`, `brand`, `module`, `status`, `result_semantics`, `terminology_profile`, `provenance`. |
| Test migration | Move high-risk tests to objectName/page_key/status enum/message code; keep limited locale snapshot tests. |
| Disallowed approach | No global search/replace translation; no report-body string replacement as template strategy. |
| Must semanticize before translation | `analysis.status.*`, `result.semantic.*`, `bio.warning.tcga_gtex_no_auto_merge`, `meta.ai_suggestion.*`, `report.status.*`, `export.*`. |

Required initial keys:

- `brand.*`
- `nav.*`
- `feature.status.*`
- `analysis.status.*`
- `result.semantic.*`
- `bio.warning.tcga_gtex_no_auto_merge`
- `meta.ai_suggestion.*`
- `labtools.term.*`
- `report.status.*`
- `export.*`

## 13. 与 Bioinformatics B8.1 的关系

| bio_stage | ui_dependency | allowed_ui_state | forbidden_ui_state | next_calibration_needed |
|---|---|---|---|---|
| B8.1 standardized analysis input resolver | UI-B0/UI-B1 can run in parallel. UI-B5 depends on resolver semantics for formal tasks. | Resolver status shell, input package status, preflight/gated copy. | Formal DEG/GSEA/survival/clinical association buttons. | Re-check after B8.1 lands to update UI-B5 gating. |
| B8.2 DEG-ready matrix / formal DEG preflight | UI-B5 task center can show readiness and preflight. | Configure and run preflight when prerequisites exist. | Formal DEG as product action. | Calibrate DEG button states and result schema. |
| B8.3 formal DEG backend decision | UI-B5 waits for backend/output contract before formal run. | Disabled/hidden formal DEG with blocker. | Any claim of BioMedPilot recomputed DEG before backend and schema. | Formal DEG UI acceptance audit. |
| B8.4 result semantics / imported result hardening | UI-B7 and UI-B5 result display depend on it. | `imported_external_result`, testing/developer preview. | Imported DEG as recomputed result. | Result browser/report draft calibration. |
| B8.5 plot artifact schema | UI-B7 can shell plot slots only. | Empty/disabled plot states. | Fake volcano/heatmap/KM/forest plot. | Plot shell to artifact schema calibration. |
| B8.6 report-ready gate/export package | UI-B7 can show draft and disabled report-ready. | Markdown/report draft. | Report-ready export package. | Report/export shell calibration. |
| B8.7 survival/clinical association design | UI-B5 can show preflight-only clinical/survival status. | Preflight-only and blocked states. | KM/Cox/log-rank/clinical association as formal run. | Survival/clinical UI acceptance audit. |

Specific Bioinformatics rules:

- B8.1 can and should run parallel to UI-B0/UI-B1.
- UI-B5 must not bypass B8.1.
- Before B8.1, show standardized repository, analysis input resolver, preflight and gated states only.
- DEG/GSEA/survival/clinical association/plot/report-ready cannot be formal primary actions.
- Imported DEG must be external imported result.
- TCGA+GTEx must not auto-merge as default path.
- Report-ready export waits for B8.6.

## 14. 与 Meta Analysis 的关系

| meta_area | current_status | allowed_ui_state | blocker | next_calibration_needed |
|---|---|---|---|---|
| UIShell Meta runtime | Current UIShell has shell-only pages: `workflow_home`, `project_contract`, `dev_branch`. | Target IA shell with Developer Preview/testing status. | Full Meta workflow not represented in current UIShell. | Meta runtime/IA calibration audit or UI-A4.1 after Integration. |
| Meta Type first | Target IA input; not current full runtime. | Schema shell / selection shell. | Method availability and runtime status not calibrated in UIShell. | Type registry and status calibration. |
| Network Meta | Planned only. | Hidden or planned/disabled. | No production Network Meta workflow. | Future module-specific audit. |
| AI suggestion | Testing-level assisted workflow concept. | Suggestion/assistant copy with accept/reject/edit/apply boundaries. | Risk of implying automatic conclusions. | AI suggestion disclaimer tests. |
| Search/screening/extraction/statistics/report | Present in target or Meta专线 contexts, not current UIShell runtime proof. | Shell-only unless Integration evidence is current. | Meta专线 not calibrated into current UIShell. | Meta专线 runtime audit before UI-B6. |
| Chinese DB/PDF/PRISMA/publication PDF | Not first-round available in UIShell. | Hidden/planned unless proven. | Overclaiming production systematic review capability. | Integration and capability audit. |

## 15. 与 LabTools 的关系

| labtools_area | current_status | reuse_source | allowed_ui_state | forbidden_ui_state | blocker |
|---|---|---|---|---|---|
| LabTools as first-level module | Target first-level module; no current `dev/ui-shell` runtime. | A1 target drafts, cross-branch Integration/ReleaseBuild source evidence. | Dashboard/sidebar shell after minimal boundary. | Full capability claims before current runtime integration. | Missing `app/labtools` in `dev/ui-shell`. |
| General Calculators | Target top-level LabTools area. | `dev/labtools` backend and Integration references after calibration. | Shell or calibrated calculators. | BCA/SDS-PAGE/MTT/CCK-8 in general calculators. | Need minimal access boundary and IA review. |
| Reagent Preparation | Target top-level area. | LabTools backend concepts. | Template/current prep/record shell. | Full SOP library claims. | Runtime integration and record schema. |
| Experiment Modules | Target top-level area with cell/protein/nucleic acid/immuno/IHC. | Integration/ReleaseBuild and backend references. | Planned/testing shell; hide unavailable submodules. | Planned PCR/qPCR/ELISA/cell workflows as complete. | Current capability calibration. |
| ImageJ/Fiji | External engine/config concept. | Integration `imagej_fiji` page as reference only. | Settings external engine status. | LabTools main task page. | Settings resource architecture. |
| Image analysis | Embedded assistant inside specific experiments. | Legacy/reference only. | Future embedded flow after experiment IA. | First-level module or generic primary task. | Experiment-specific workflow design. |
| LAN/local sharing | Out of route. | None. | Not included. | Any LAN/local-network sharing planning. | Not part of target scope. |

## 16. 与 Vocabulary / 词库模块的关系

| vocabulary_area | ui_dependency | current_assumption | risk | later_calibration |
|---|---|---|---|---|
| i18n terminology table | UI-B0/I18N Strategy defines location and schema. | Can start as governance and empty/seed table. | Hardcoding terms before vocabulary freezes. | Update after Vocabulary Integration. |
| Medical vocabulary mapping | Bioinformatics and Meta query terms need interface. | Existing shared query intelligence has zh/en terms, but not UI glossary governance. | UI terms drift from backend query terms. | A4.1 checks canonical term IDs and display terms. |
| Meta type vocabulary | UI-B6 type labels need stable zh/en terms. | A3 initial labels are planning input. | Free translation of effect types/methods. | Calibrate with Meta module and Vocabulary. |
| Bioinformatics query terms | Data source/search UI needs disease/database terms. | Current query intelligence has fixtures and registry. | Locale UI could imply unsupported source behavior. | Map to i18n terminology and source status. |
| LabTools experiment terms | LabTools UI needs assay/unit/glossary terms. | A3 initial terms define boundaries. | BCA/SDS-PAGE/Western Blot/ImageJ free translation. | LabTools + Vocabulary calibration. |

Vocabulary can proceed parallel to A4 v1 and UI-B0/B1. UI-A4 v1 does not require Vocabulary to finish first. Do not hardcode all translated terms into UI before Vocabulary or terminology governance is stable.

## 17. 打包与桌面入口处理时机

| packaging_item | current_risk | do_now | defer_to | required_validation |
|---|---|---|---|---|
| `dist/BioMedPilot.app` | Static Info.plist shows `BioMedPilotGitHead=db4e27b`, older than current HEAD `c94d9cb`. | Static reference only. | UI-B10 / packaging专项. | Package smoke, Info.plist, LaunchServices, codesign if required. |
| Desktop `/Users/changdali/Desktop/BioMedPilot.app` | Static Info.plist shows `BioMedPilotGitHead=21e1a0f`, older than current HEAD. | Static reference only. | UI-B10 / packaging专项. | Finder/LaunchServices launch and desktop entry update only after permission. |
| `CFBundleDisplayName` | Still `BioMedPilot / 医研智析`, while target visible brand may be `萤火虫 / Firefly`. | Do not change. | UI-B10 after brand freeze. | Info.plist and user-visible Finder checks. |
| `CFBundleName` / executable | `BioMedPilot`; may stay as technical name. | Do not change. | UI-B10 only if technical rename approved. | Executable path, `-psn_*`, direct binary smoke. |
| App icon / Finder icon | Current BioMedPilot icon may conflict with Firefly target. | Do not replace. | UI-B8 for resource confirmation, UI-B10 for packaging. | Icon inventory, bundle icon key, `.icns` in Resources. |
| LaunchServices | Required only in packaging stage. | Do not run packaged app in A4 v1. | UI-B10. | `open -W -n dist/BioMedPilot.app --args --smoke-test`, logs, code signing if required. |

Packaging and desktop entry are not part of UI-B0-B9 early work. Old dist and desktop packages are historical evidence, not current runtime proof.

## 18. 可立即执行的下一步建议

| question | answer |
|---|---|
| 是否可以进入 UI 开发？ | 可以进入 UI-B0 文档总线阶段；不应直接进入代码页面开发。 |
| 第一条开发指令应该是什么？ | `执行 UI-B0：建立 UI_Rebuild_MasterPlan、Visual Style Guide v1、I18N Strategy v1、Stage Index，只新增文档，不改 UI 代码。` |
| 是先做 UI-B0 还是跳到 UI-B1/B2？ | 必须先做 UI-B0；不建议跳到 UI-B1/B2。 |
| 哪些阶段需要用户先确认品牌、图标、Figma？ | UI-B8 和高保真 UI；UI-B2 低保真不需要最终图标，但需要 placeholder 策略。 |
| 哪些阶段可以 Codex 独立完成？ | UI-B0 文档、UI-B1 token/component初稿、UI-B2低保真 shell、UI-B3 Settings shell、UI-B9 key边界初稿可由 Codex 推进后交审。 |
| 哪些内容必须继续 planned/gated/hidden？ | Bio formal DEG/GSEA/survival/clinical/report-ready, Meta production workflow/Network Meta/AI conclusions, LabTools planned experiment modules, ImageJ/Fiji main-task entry, packaging UI. |
| 哪些内容不能在第一轮 UI 重构中做？ | 高保真品牌视觉、App icon替换、桌面 `.app` 覆盖、云账号/订阅购买、正式 report-ready、生产级 Meta/生信/实验结果生成。 |
| 是否建议 Bioinformatics B8.1 与 UI-B0/B1 并行推进？ | 是。B8.1 可并行，但 UI-B5 不得绕过 B8.1。 |
| 是否建议先做 Meta 专线 runtime 审计后再做 UI-B6？ | 是。若未完成，则 UI-B6 只能做 shell-only 目标 IA。 |
| 是否建议先做 LabTools 最小接入边界审计后再做 UI-B4？ | 是。否则 UI-B4 只能记录 shell/占位策略。 |
| 是否需要等 Meta / 词库 / 生信全部合入 Integration 后才做 UI-B0？ | 不需要。UI-B0 是治理和路线总线，应先做。 |
| 是否需要后续 UI-A4.1 Integration 校准审计？ | 需要。模块合入后必须校准能力、状态、按钮、测试和资源。 |

Recommended UI-B order:

1. UI-B0 MasterPlan / Visual Style Guide / I18N Strategy / Stage Index.
2. UI-B1 design tokens / theme / primitives.
3. UI-B2 Welcome / Dashboard / Sidebar / About / Test Feedback low-fidelity shell.
4. UI-B3 Settings external resource shell.
5. UI-B9 critical semantic i18n keys can begin once UI-B0/B1 foundations exist.
6. UI-B4 LabTools shell after minimal boundary audit.
7. UI-B5 Bioinformatics target IA after B8.1 status is calibrated enough for safe gating.
8. UI-B6 Meta shell after Meta runtime/IA calibration.
9. UI-B7 shared result/report/export shell.
10. UI-B8 resource replacement after brand/Figma/icon confirmation.
11. UI-B10 packaging and desktop entry专项.

## 19. 本阶段未修改业务代码声明

This stage only adds this audit report:

`docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md`

Not modified:

- `app/**`
- `tests/**`
- `assets/**`
- `config/**`
- `scripts/package_app.py`
- `dist/**`
- `/Users/changdali/Desktop/BioMedPilot.app`

Not performed:

- No UI page implementation or refactor.
- No Logo/icon/image replacement.
- No i18n file extraction.
- No report template or config changes.
- No dependency changes.
- No repackaging.
- No packaged app launch.
- No desktop entry overwrite.
- No Bioinformatics / Meta Analysis / LabTools / Vocabulary feature development.

## 20. 命令记录与验证

| command | result |
|---|---|
| `sed -n '1,260p' /Users/changdali/Downloads/UI_A4_v1_rebuild_execution_plan_audit_task.md` | Passed; read task brief part 1. |
| `sed -n '261,620p' /Users/changdali/Downloads/UI_A4_v1_rebuild_execution_plan_audit_task.md` | Passed; read task brief part 2. |
| `sed -n '621,980p' /Users/changdali/Downloads/UI_A4_v1_rebuild_execution_plan_audit_task.md` | Passed; read task brief part 3. |
| `sed -n '981,1160p' /Users/changdali/Downloads/UI_A4_v1_rebuild_execution_plan_audit_task.md` | Passed; read validation and submission requirements. |
| `git status --short --branch` | Passed; branch `dev/ui-shell` was clean before report creation. |
| `ls docs/ui \| sort` | Passed; A1/A2/A3 and reference UI docs exist. |
| `rg -n "UI-A4\|UI-B\|MasterPlan..." /Users/changdali/.codex/memories/MEMORY.md` | Passed; confirmed scoped audit commit defaults and packaging boundary memory. |
| `sed -n '1,220p' docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` | Passed; extracted target IA conclusions. |
| `sed -n '1,220p' docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | Passed; extracted brand/resource/design-token conclusions. |
| `sed -n '1,220p' docs/ui/UI_A3_i18n_readiness_audit_20260520.md` | Passed; extracted i18n conclusions. |
| `rg --files app tests docs/bioinformatics scripts dist assets \| sed -n '1,260p'` | Passed; inventoried current code/test/resource/dist paths. |
| `find docs/ui/target_design_drafts -type f -name '*.md' \| sort` | Passed; confirmed target drafts. |
| `rg -n "LabTools\|Labors\|实验工具\|imagej..." app tests docs/ui docs/bioinformatics ...` | Passed; confirmed key boundary references and Bio/Meta/LabTools risks. |
| `plutil -p dist/BioMedPilot.app/Contents/Info.plist` | Passed; static read only, dist GitHead `db4e27b`. |
| `sed -n '1,220p' docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md` | Passed; extracted cross-branch LabTools/runtime evidence. |
| `sed -n '1,220p' docs/ui/UI_Current_Information_Architecture_Audit_20260519.md` | Passed; extracted current runtime IA. |
| `sed -n '1,220p' docs/ui/UI_Freeze_Consolidation_Baseline_20260519.md` | Passed; extracted freeze/baseline rules. |
| `sed -n '1,240p' docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md` | Passed; extracted B8.0.1 gating and result/report boundary. |
| `plutil -p /Users/changdali/Desktop/BioMedPilot.app/Contents/Info.plist` | Passed; static read only, desktop app GitHead `21e1a0f`. |
| `git rev-parse --short HEAD` | Passed; current HEAD before report commit was `c94d9cb`. |
| `for f in ...; do test -e "$f" ...; done` | Passed; required input files checked as found. |

Post-write validation:

| command | result |
|---|---|
| `git diff --check` | Passed; no whitespace errors. |
| `git status --short` | Passed; only `docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` was newly untracked before staging. |
| `wc -l docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | Passed; report had 401 lines before this validation update. |
