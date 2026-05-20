# UI Rebuild Stage Index

Date: 2026-05-20

Status: current implementation-plan index

Scope: UI-B0 through UI-B10

## 1. Current Stage

Current stage: UI-B0.

UI-B0 outputs:

- `docs/ui/UI_Rebuild_MasterPlan_20260520.md`
- `docs/ui/UI_Visual_Style_Guide_v1_20260520.md`
- `docs/ui/UI_I18N_Strategy_v1_20260520.md`
- `docs/ui/UI_Rebuild_Stage_Index_20260520.md`

UI-B0 is documentation-only.

## 2. Stage Route

```text
UI-B0: MasterPlan / Visual Style Guide / I18N Strategy / Stage Index
-> UI-B1: design tokens / theme / primitives
-> UI-B2: Welcome / Dashboard / Sidebar / About / Test Feedback shell
-> UI-B3: Settings shell and external resource management
-> UI-B4: LabTools target IA shell
-> UI-B5: Bioinformatics target 7 pages + 2 auxiliary pages
-> UI-B6: Meta Analysis target IA shell
-> UI-B7: Result / Report / Export unified semantics
-> UI-B8: resource replacement
-> UI-B9: i18n key boundaries
-> UI-B10: packaging and desktop entry
```

Recommended execution order:

1. UI-B0
2. UI-B1
3. UI-B2
4. UI-B3
5. UI-B9 critical semantic i18n keys, which can start in parallel after UI-B0/UI-B1 foundations
6. UI-B4
7. UI-B5
8. UI-B6
9. UI-B7
10. UI-B8
11. UI-B10

UI-B4, UI-B5, UI-B6, UI-B7, UI-B8 and UI-B9 may be sequenced with limited overlap after their dependencies are met. UI-B10 is last.

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
| UI-B8 | Visual Style Guide and user brand/resource decisions | Shell work with placeholders | Unconfirmed App icon or desktop package changes. |
| UI-B9 | I18N Strategy, status keys, UI-B1 tokens | UI-B2-B7 shell work | One-shot full translation. |
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
| UI-B6 | Meta target shell has type-first IA, testing/shell-only status and AI disclaimer. |
| UI-B7 | Result/report/export statuses are unified and draft/report-ready cannot be confused. |
| UI-B8 | Resources have inventory and placeholder/final status; final assets are confirmed. |
| UI-B9 | Critical i18n keys and semantic status boundaries are in place. |
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
| UI-B6 | Meta shell tests, Meta type registry tests, AI suggestion disclaimer tests, smoke. |
| UI-B7 | Report status tests, export gating tests, empty state tests, disclaimer tests. |
| UI-B8 | Icon path tests, resource inventory tests, module icon loading tests, smoke. |
| UI-B9 | Key existence tests, status enum rendering tests, high-risk assertion migration tests. |
| UI-B10 | package smoke, app smoke, Info.plist, icon key, `open -W -n`, `-psn_*`, codesign if required. |

Full test suites are not mandatory for every early phase unless the changed surface requires them.

## 6. User Confirmation Gates

| gate | needed_before |
|---|---|
| Visible brand `萤火虫 / Firefly` final decision | High-fidelity Welcome/About/Dashboard and App icon changes. |
| Bundle technical name decision | UI-B10. |
| Logo/App icon/Finder icon | UI-B8/UI-B10. |
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
| `docs/ui/UI_Rebuild_Stage_Index_20260520.md` | current implementation-plan index |
| `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` | audit-only / planning input |
| `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | audit-only / planning input |
| `docs/ui/UI_A3_i18n_readiness_audit_20260520.md` | audit-only / planning input |
| `docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | audit-only / planning input |
| `docs/ui/target_design_drafts/**` | target-draft |
| `docs/stage_UI_*` | historical |
| `archive/**` | historical / legacy reference |
| `docs/packaging.md` | packaging-specific |
| `docs/bioinformatics/**` | module-specific unless adopted by MasterPlan |

## 8. Non-Goals for UI-B0 through UI-B9

- No desktop `.app` overwrite.
- No packaged app launch.
- No Finder icon replacement.
- No LaunchServices validation outside UI-B10.
- No cloud account, subscription, VIP or license purchase flow.
- No production Bioinformatics result claims before B8 gates.
- No production Meta workflow claims before runtime calibration.
- No LabTools planned module exposure as available.
- No one-shot i18n translation.

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
