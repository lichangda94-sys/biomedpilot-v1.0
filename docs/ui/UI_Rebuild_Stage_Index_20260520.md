# UI Rebuild Stage Index

Date: 2026-05-20

Status: current implementation-plan index and UI-A4.3 checkpoint

Scope: UI-B0 through UI-B10

## 1. Current Stage

Current checkpoint: UI-C1 low-to-mid fidelity visual calibration.

Completed stages:

- UI-B0: MasterPlan / Visual Style Guide / I18N Strategy / Stage Index.
- UI-B1: design tokens, theme and basic primitives.
- UI-B2: Welcome / Dashboard / Sidebar / About / Test Feedback low-fidelity shell.
- UI-B3: Settings secondary navigation and external capability management shell.
- UI-B4: LabTools IA shell.
- UI-B5 shell: Bioinformatics target IA shell and gated/preflight copy.
- UI-B5.1: Bioinformatics legacy page routing calibration.
- UI-B5.2: Bioinformatics target page consolidation.
- UI-B6 shell: Meta Analysis target IA shell and active Meta type display.
- UI-B6.1: Meta Analysis target shell interaction calibration.
- UI-B7 shell: shared Result / Report / Export semantic shell.
- UI-B7.1: Result / Report / Export shell adoption calibration.
- UI-B8a: resource inventory / placeholder strategy.
- UI-B8b-prep: resource design brief, Figma brief and icon requirements.
- UI-B9a: semantic key registry.
- UI-B9b: key adoption / test migration.
- UI-B9c: selective key adoption / test migration expansion.
- UI-C0: low-fidelity shell usability pass.
- UI-C1: low-to-mid fidelity visual calibration from first concept image batch.

Partially completed stages:

- Full UI-B9 i18n adoption / language switch has not started.

Not started:

- UI-B8b formal resource replacement.
- UI-B10 packaging / desktop entry.

Current forbidden scope:

- Do not handle App icon, Finder icon, Info.plist icon binding, LaunchServices, packaged app validation, or desktop `.app` overwrite before UI-B10.
- Do not replace active icons or resources under the current checkpoint.
- Do not treat shell-only, testing, planned, or Developer Preview UI as production capability.
- Do not treat UI-B8b-prep as permission to implement or bind new resources.

Recommended next stage:

- UI-B8b formal resource replacement only after brand/resource owner confirmation and approved design exports, or
- UI-C2 module-specific visual/detail calibration if another concept batch needs implementation.

## 2. Stage Route

```text
UI-B0: MasterPlan / Visual Style Guide / I18N Strategy / Stage Index
-> UI-B1: design tokens / theme / primitives
-> UI-B2: Welcome / Dashboard / Sidebar / About / Test Feedback shell
-> UI-B3: Settings shell and external resource management
-> UI-B4: LabTools target IA shell
-> UI-B5: Bioinformatics target 7 pages + 2 auxiliary pages
-> UI-B5.1: Bioinformatics legacy page routing calibration
-> UI-B5.2: Bioinformatics target page consolidation
-> UI-B6: Meta Analysis target IA shell
-> UI-B6.1: Meta Analysis target shell interaction calibration
-> UI-B7: Result / Report / Export unified semantics
-> UI-B7.1: Result / Report / Export shell adoption calibration
-> UI-B8a: resource inventory / placeholder strategy
-> UI-B8b-prep: resource design / Figma / icon brief
-> UI-B8b: formal resource replacement after brand/resource confirmation
-> UI-B9a: semantic key registry
-> UI-B9b: key adoption / test migration
-> UI-B9c: selective key adoption / test migration expansion
-> UI-C0: low-fidelity shell usability pass
-> UI-C1: low-to-mid fidelity visual calibration
-> UI-B10: packaging and desktop entry
```

Recommended execution order:

1. UI-B0: completed.
2. UI-B1: completed.
3. UI-B2: completed.
4. UI-B3: completed.
5. UI-B9a critical semantic keys: completed.
6. UI-B4: completed.
7. UI-B5 shell: completed.
8. UI-B5.1 Bioinformatics legacy page routing calibration: completed.
9. UI-B5.2 Bioinformatics target page consolidation: completed.
10. UI-B6 shell: completed.
11. UI-B6.1 Meta target shell interaction calibration: completed.
12. UI-B7 shell: completed.
13. UI-B7.1 Result / Report / Export adoption calibration: completed.
14. UI-B8a inventory / placeholder strategy: completed.
15. UI-B8b-prep resource design / Figma / icon brief: completed.
16. UI-B9b key adoption / test migration: completed.
17. UI-B8b formal resource replacement only after resource decisions and approved exports.
18. UI-B9c selective key adoption / test migration expansion: completed.
19. UI-C0 low-fidelity shell usability pass: completed.
20. UI-C1 low-to-mid fidelity visual calibration: completed.
21. UI-C2 module-specific visual/detail calibration if needed.
22. UI-B10 packaging and desktop entry last.

UI-B8b and UI-B10 must not be inferred from UI-B8a or later shell calibration. UI-B10 remains last.

## 3. Dependency Table

| stage | depends_on | can_parallel_with | must_not_do |
|---|---|---|---|
| UI-B0 | UI-A1/A2/A3/A4 and target IA v1 | Bioinformatics B8.1 planning, Meta/LabTools/Vocabulary audits | Code, resources, packaging. |
| UI-B1 | UI-B0 | B8.1 planning and resource inventory prep | Business page rewrites. |
| UI-B2 | UI-B1 | UI-B3 planning | Final brand/icon replacement, cloud account flow. |
| UI-B3 | UI-B0/B1 | UI-B2 | Real installers, auto download/update/delete/upload. |
| UI-B4 | UI-B0/B1 and LabTools minimal boundary audit | UI-B3 | Planned LabTools features as available. |
| UI-B5 | UI-B0/B1 and B8.1 calibration for formal actions | B8.1 backend work | Formal DEG/GSEA/survival/clinical/report-ready before gates. |
| UI-B6 | UI-B0/B1 and Meta runtime/IA calibration or shell-only boundary | Meta专线 audit | Production Meta workflow claims. |
| UI-B7 | UI-B0/B1 and result/report schema state | B8.4/B8.5/B8.6 planning | Fake plots or final reports. |
| UI-B8a | Visual Style Guide and current resource audit | Shell work with placeholders | Replacing active icons, App icon, Finder icon, desktop package changes. |
| UI-B8b-prep | UI-B8a inventory and Visual Style Guide | UI-C1 planning | Resource replacement, App icon, Finder icon, packaging. |
| UI-B8b | Confirmed brand/resource owner decisions and UI-B8a inventory | High-fidelity shell work | Unconfirmed App icon or desktop package changes. |
| UI-B9a | I18N Strategy, status keys, UI-B1 tokens | UI-B2-B7 shell work | One-shot full translation, language switch. |
| UI-B9b | UI-B9a key registry and focused test baseline | UI-B5.1 routing calibration | Full multilingual release, report template rewrite. |
| UI-B9c | UI-B9b and current Bio/Meta/LabTools/Settings shell baselines | UI-B8b | Full translation, language switch, report template rewrite. |
| UI-C0 | UI-B2-B9c low-fidelity shell baseline | UI-B8b | High-fidelity redesign, resource replacement, packaging. |
| UI-C1 | UI-C0 and first local concept image batch | UI-B8b design review | Asset replacement, App icon, Finder icon, packaging, business workflow execution. |
| UI-B10 | UI-B2-B9 stable enough for packaging | Packaging专项 only | Early desktop `.app` overwrite. |

## 4. Stage Acceptance Summary

| stage | pass_condition |
|---|---|
| UI-B0 | Four docs added, `git diff --check` passes, no code/resource/package changes. |
| UI-B1 | One token source and core primitives exist; smoke and focused UI tests pass. |
| UI-B2 | Low-fidelity shell supports Welcome, three-module Dashboard, Sidebar, About, Test Feedback. |
| UI-B3 | Settings secondary IA exists and external resources use detect-first semantics. |
| UI-B4 | LabTools module shell respects target top-level IA and planned/hidden boundaries. |
| UI-B5 | Bioinformatics target pages are reorganized with B8.1-safe gating. |
| UI-B5.1 | Legacy Bioinformatics pages are mapped to target pages or developer diagnostics. |
| UI-B5.2 | Bioinformatics target pages are consolidated as 7 main-flow pages plus 2 auxiliary pages. |
| UI-B6 | Meta target shell has type-first IA, testing/shell-only status and AI disclaimer. |
| UI-B6.1 | Meta target shell interaction is select-only/schema-shell and Network Meta remains disabled. |
| UI-B7 | Result/report/export statuses are unified and draft/report-ready cannot be confused. |
| UI-B7.1 | Bioinformatics and Meta target shells adopt the shared Result / Report / Export shell panel. |
| UI-B8a | Resource inventory and placeholder/final strategy exist; active icons are not replaced. |
| UI-B8b-prep | Resource design brief, Figma brief and icon requirements exist; active resources are not replaced. |
| UI-B8b | Formal resources are confirmed, added or replaced with focused resource tests. |
| UI-B9a | Critical i18n keys and semantic status boundaries are in place. |
| UI-B9b | Key adoption and high-risk test migration are in place; full language switch may still be future work. |
| UI-B9c | Selective page key adoption covers Bioinformatics, Meta, LabTools and Settings shell surfaces. |
| UI-C0 | Low-fidelity shell pages remain navigable, scrollable where needed and expose usability metadata. |
| UI-C1 | First concept image batch is reflected in shell layout, flow navigation, quick access and user-facing cards without changing business execution. |
| UI-B10 | Packaging, Info.plist, icon, LaunchServices and desktop entry are validated. |

## 5. Required Tests by Stage

| stage | minimum_tests |
|---|---|
| UI-B0 | `git diff --check`, `git status --short`. |
| UI-B1 | Token/component tests, status chip tests, smoke. |
| UI-B2 | Welcome/sidebar/dashboard/about/module selection tests, smoke. |
| UI-B3 | Settings nav tests, resource status shell tests, detect-first copy tests. |
| UI-B4 | LabTools sidebar/dashboard entry tests, IA tests, planned/hidden state tests, smoke. |
| UI-B5 | Bio workflow page tests, task gating tests, report draft boundary tests, smoke. |
| UI-B5.2 | Bio target IA focused tests and legacy stack navigation smoke. |
| UI-B6 | Meta shell tests, Meta type registry tests, AI suggestion disclaimer tests, smoke. |
| UI-B6.1 | Meta shell interaction tests, active type selection tests, Network Meta disabled tests, smoke. |
| UI-B7 | Report status tests, export gating tests, empty state tests, disclaimer tests. |
| UI-B7.1 | Result / Report / Export adoption tests for shared panel plus Bio/Meta target shells. |
| UI-B8a | `git diff --check`; resource inventory review. No icon replacement tests required because no active resources change. |
| UI-B8b-prep | `git diff --check`; documentation-only brief review. No icon replacement tests required because no active resources change. |
| UI-B8b | Icon path tests, resource inventory tests, module icon loading tests, smoke. |
| UI-B9a | Key existence tests and status enum rendering tests. |
| UI-B9b | High-risk assertion migration tests and key adoption tests. |
| UI-B9c | Semantic key registry tests plus Bio/Meta/LabTools/Settings focused shell tests. |
| UI-C0 | Welcome, Dashboard/module selection, Sidebar, LabTools and Settings usability focused tests. |
| UI-C1 | Dashboard, LabTools, Bioinformatics IA, Meta IA focused tests plus source smoke and UI/shared suite. |
| UI-B10 | package smoke, app smoke, Info.plist, icon key, `open -W -n`, `-psn_*`, codesign if required. |

Full test suites are not mandatory for every early phase unless the changed surface requires them.

## 6. User Confirmation Gates

| gate | needed_before |
|---|---|
| Visible brand `萤火虫 / Firefly` final decision | High-fidelity Welcome/About/Dashboard and App icon changes. |
| Bundle technical name decision | UI-B10. |
| Logo and non-packaging module/resource icons | UI-B8b. |
| App icon / Finder icon / Info.plist icon binding / LaunchServices | UI-B10 only. |
| Figma/high-fidelity visual direction | UI-B8 and high-fidelity pass after UI-B2 shell. |
| LabTools minimal runtime boundary | UI-B4. |
| Meta runtime calibration | UI-B6. |
| Bioinformatics B8.1 status | Formal parts of UI-B5. |
| Vocabulary terminology freeze | Full multilingual reports and polished terminology. |

## 7. Document Status Index

| document_or_area | status |
|---|---|
| `docs/ui/UI_Rebuild_MasterPlan_20260520.md` | current |
| `docs/ui/UI_Visual_Style_Guide_v1_20260520.md` | current |
| `docs/ui/UI_I18N_Strategy_v1_20260520.md` | current |
| `docs/ui/UI_Rebuild_Stage_Index_20260520.md` | current implementation-plan index / UI-C1 checkpoint |
| `docs/ui/UI_A4_3_current_checkpoint_next_stage_planning_20260520.md` | current checkpoint summary |
| `docs/ui/UI_B5_1_bioinformatics_legacy_page_routing_calibration_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_B5_2_bioinformatics_target_page_consolidation_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_B6_1_meta_analysis_target_shell_interaction_calibration_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_B7_1_result_report_export_shell_adoption_calibration_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_B8b_prep_resource_design_figma_icon_brief_20260520.md` | completed design-prep checkpoint |
| `docs/ui/UI_B9b_semantic_key_adoption_test_migration_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_B9c_selective_key_adoption_test_migration_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_C0_low_fidelity_shell_usability_pass_20260520.md` | completed stage checkpoint |
| `docs/ui/UI_C1_low_to_mid_fidelity_visual_calibration_20260521.md` | completed stage checkpoint |
| `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` | audit-only / planning input |
| `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | audit-only / planning input |
| `docs/ui/UI_A3_i18n_readiness_audit_20260520.md` | audit-only / planning input |
| `docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | audit-only / planning input |
| `docs/ui/target_design_drafts/**` | target-draft |
| `docs/stage_UI_*` | historical |
| `archive/**` | historical / legacy reference |
| `docs/packaging.md` | packaging-specific |
| `docs/bioinformatics/**` | module-specific unless adopted by MasterPlan |

## 8. Non-Goals for UI-B0 through UI-C1

- No desktop `.app` overwrite.
- No packaged app launch.
- No Finder icon replacement.
- No App icon replacement.
- No Info.plist icon binding.
- No LaunchServices validation outside UI-B10.
- No cloud account, subscription, VIP or license purchase flow.
- No production Bioinformatics result claims before B8 gates.
- No production Meta workflow claims before runtime calibration.
- No LabTools planned module exposure as available.
- No one-shot i18n translation.

## 8.1 Current Checkpoint Summary

| category | checkpoint_status |
|---|---|
| Completed | UI-B0, UI-B1, UI-B2, UI-B3, UI-B4, UI-B5 shell, UI-B5.1, UI-B5.2, UI-B6 shell, UI-B6.1, UI-B7 shell, UI-B7.1, UI-B8a, UI-B8b-prep, UI-B9a, UI-B9b, UI-B9c, UI-C0, UI-C1. |
| Partial | Full UI-B9 i18n adoption / language switch remains future work. |
| Not started | UI-B8b formal resource replacement; complete i18n adoption / language switch; UI-B10 packaging / desktop entry. |
| Hard stop | App icon, Finder icon, Info.plist icon binding, LaunchServices, packaged app validation and desktop `.app` overwrite stay out of scope until UI-B10. |
| Next recommended work | UI-B8b formal resource replacement after owner approval and exported assets, or UI-C2 module-specific visual/detail calibration if needed. |

## 9. UI-B0 Command Log

Commands executed while creating UI-B0 documents:

| command | result |
|---|---|
| `sed -n '1,260p' /Users/changdali/Desktop/UI/UI_Target_Information_Architecture_v1_20260520.md` | Passed; read target IA part 1. |
| `sed -n '261,620p' /Users/changdali/Desktop/UI/UI_Target_Information_Architecture_v1_20260520.md` | Passed; read target IA part 2. |
| `sed -n '621,980p' /Users/changdali/Desktop/UI/UI_Target_Information_Architecture_v1_20260520.md` | Passed; read target IA part 3. |
| `sed -n '1,260p' /Users/changdali/Desktop/UI/UI_Rebuild_Implementation_Plan_v1_20260520.md` | Passed; read implementation plan part 1. |
| `sed -n '261,620p' /Users/changdali/Desktop/UI/UI_Rebuild_Implementation_Plan_v1_20260520.md` | Passed; read implementation plan part 2 and immediate UI-B0 instruction. |
| `git status --short --branch` | Passed; branch was clean before UI-B0 document creation. |
| `rg -n "UI_Target_Information_Architecture..." /Users/changdali/.codex/memories/MEMORY.md` | Passed; confirmed scope and commit/packaging boundary memory. |
| `test -e docs/ui/UI_Rebuild_MasterPlan_20260520.md ...` | Passed; confirmed UI-B0 output files did not already exist. |

Post-write validation:

| command | result |
|---|---|
| `git diff --check` | Passed; no whitespace errors. |
| `git status --short` | Passed; only four UI-B0 Markdown files were newly untracked before staging. |
| `find docs/ui -maxdepth 1 -type f ...` | Passed; confirmed exactly the four expected UI-B0 output files. |
| `wc -l docs/ui/UI_Rebuild_MasterPlan_20260520.md docs/ui/UI_Visual_Style_Guide_v1_20260520.md docs/ui/UI_I18N_Strategy_v1_20260520.md docs/ui/UI_Rebuild_Stage_Index_20260520.md` | Passed; four files total 939 lines before this validation update. |

## 10. UI-B0 Boundary Statement

UI-B0 only adds documentation. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/package_app.py`, `dist/**`, or any desktop `.app`.
