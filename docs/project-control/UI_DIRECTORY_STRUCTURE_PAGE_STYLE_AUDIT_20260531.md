# UI Directory Structure and Page Style Audit

Date: 2026-05-31

Scope: read-only audit of UI construction evidence across the clean `UIShell` worktree and the current dirty `Integration` worktree. No business code was modified, no merge was run, no cherry-pick was run, no migration was performed, and `project_storage/` was not touched.

## Immediate Answer

The recovered Bioinformatics / Meta Analysis / LabTools UI content is not located in one single current Integration directory. It exists in three different layers:

1. Historical recovery source: `codex/integration-labtools-ui-c2-carryover`
   - Accepted packaged preview identity: `9d4edf3`
   - Historical carryover HEAD recorded by the earlier audit: `e13d0f5f5dfda36a5c60a00ddc7820748fa1677f`
   - Main aggregate UI import: `efb6227` (`Merge latest UI shell for release preview`)

2. Current Integration worktree source files:
   - Shell: `app/shell/login.py`, `app/shell/module_selection.py`, `app/shell/sidebar.py`, `app/shell/main_window.py`, `app/shell/settings_page.py`
   - Bioinformatics: `app/bioinformatics/project_home.py`, `app/bioinformatics/workflow_pages.py`, `app/bioinformatics/workspace.py`
   - Meta Analysis: `app/meta_analysis/workspace.py`, `app/meta_analysis/workflow_pages.py`, `app/meta_analysis/pages/**`
   - LabTools current target: `app/labtools/workspace.py`, `app/labtools/ui/image_analysis_widgets.py`

3. Design and governance evidence:
   - `docs/ui/UI_C2a_bioinformatics_page_implementation_sequence_20260522.csv`
   - `docs/ui/UI_C2a_meta_analysis_page_implementation_sequence_20260522.csv`
   - `docs/ui/UI_C2a_labtools_implementation_sequence_20260522.csv`
   - `docs/ui/UI_C5a_runtime_visual_gap_matrix_20260524.csv`
   - `docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md`
   - `docs/ui/UI线路既往检查.md`

The reason it appears to be integrated on an old version is that the current Integration worktree is no longer checked out at `codex/integration-labtools-ui-c2-carryover`; it is on `integration/release-ui-shell-scoped-migration` at `7682b98`, with staged and unstaged UI Shell migration changes. That branch is a scoped migration target, not the historical carryover branch itself. It has Shell/Bio/Meta wiring evidence, but its current LabTools route lands on a narrow old/minimal `app/labtools/workspace.py` page whose `page_keys()` returns only `("image_analysis",)`. The recovered LabTools calculator/reagent/WB pages from the historical UI line were mainly implemented through the older `app/labtools_runtime.py` plus `app/shell/main_window.py` path, so they are not automatically active in the current `app/labtools/workspace.py` target.

## Current Worktree Evidence

| Worktree | Branch | HEAD | State | Audit Use |
| --- | --- | --- | --- | --- |
| `/Users/changdali/Developer/biomedpilot v1.0/UIShell` | `dev/ui-shell` | `75255e5` | clean | Report location and Project Control baseline |
| `/Users/changdali/Developer/biomedpilot v1.0/Integration` | `integration/release-ui-shell-scoped-migration` | `7682b98` | dirty UI Shell migration changes | Read-only evidence only |

## UI Directory Structure

### Shell and Shared UI

| Directory / File | Role | Style Evidence | Current Classification |
| --- | --- | --- | --- |
| `app/shell/login.py` | Welcome/login entry, packaged preview gate buttons | `9d4edf3`, current Shell migration diffs, welcome assets | `figma/new shell baseline with placeholders` |
| `app/shell/module_selection.py` | Dashboard/module cards for Bio, Meta, LabTools | Dashboard rebuild commits and current route inventory | `figma/new shell baseline with route gaps` |
| `app/shell/sidebar.py` | App-level navigation | Shell baseline plus current route inventory | `hybrid: visible routes connected, registry-only routes missing` |
| `app/shell/main_window.py` | Root stacked navigation and module wiring | Main-window wiring commits; current Integration source | `hybrid integration router` |
| `app/shell/settings_page.py` | Settings Center / resource gates | `e13d0f5..9d4edf3` gate behavior, current dirty migration | `hybrid / placeholder until final route audit` |
| `app/shared/ui_components/**` | Workbench primitives, dense workbench, common components | C5/D1 workbench design-system docs | `figma/new foundation candidate` |
| `app/ui_style_tokens.py` | Shared tokens and style contracts | Known cherry-pick conflict point | `shared foundation, high-risk merge surface` |
| `assets/icons/**`, `assets/images/**` | Module icons, status icons, empty states, welcome image | Current Shell migration staged assets | `figma/new asset layer candidate` |

### Bioinformatics

| Directory / File | Role | Style Evidence | Current Classification |
| --- | --- | --- | --- |
| `app/bioinformatics/project_home.py` | Bio module home / project entry | High-fidelity mockup source in C2a sequence; recovered by `900ba60`; rebuilt by `2063ce8` | `figma/high-fidelity source exists; gated shell recovered` |
| `app/bioinformatics/workflow_pages.py` | Data source, data check, group design, analysis tasks, result/report/export pages | C2a/C2b-C2f docs and recovery commits `08e9bd1`, `900ba60`, `62739aa`, `4061d72`, `2d5a560`, `2063ce8` | `figma/high-fidelity source exists; gated shell/hybrid runtime` |
| `app/bioinformatics/workspace.py` | Module-level workspace host | `efb6227`, `2063ce8`, current Integration source | `hybrid host with recovered page surfaces` |
| `app/bioinformatics/pages/**` | Older functional pages such as GEO import, cleaning, grouping, survival, report | Legacy functional page inventory | `old page structure / functional legacy` |
| `app/bioinformatics/deg_engine/**`, `enrichment/**`, `gsea/**`, `survival_clinical/**`, `reports/**` | Runtime services and report/result gates | Release action wiring `74c19ad`; not UI page proof by itself | `runtime/backend candidates; scoped UI audit required` |

### Meta Analysis

| Directory / File | Role | Style Evidence | Current Classification |
| --- | --- | --- | --- |
| `app/meta_analysis/workspace.py` | Active Meta workspace and page host | High-fidelity mockup sequence C2a; recovered commits `bf6aaf8`, `e551f44`, `557b645`, `6fe2295`, rebuilt by `87f3f9a`, wired by `8c4e8bd` | `figma/high-fidelity source exists; active gated/hybrid workspace` |
| `app/meta_analysis/workflow_pages.py` | Workflow page support | Current Integration source | `hybrid support layer` |
| `app/meta_analysis/pages/**` | Older/active functional workflow pages: literature import, screening, extraction, quality, reporting, etc. | Active service/page inventory; not identical to C2 mockup shells | `old/hybrid functional page structure` |
| `app/meta_analysis/services/**`, `models/**`, `stats/**` | Runtime/service layer | Current Meta product line; not visual proof | `runtime/backend; not a high-fidelity UI claim` |

### LabTools

| Directory / File | Role | Style Evidence | Current Classification |
| --- | --- | --- | --- |
| `app/labtools/workspace.py` | Current Integration LabTools target | Current file returns only `("image_analysis",)` | `old/minimal current page` |
| `app/labtools/ui/image_analysis_widgets.py` | ImageJ/Fiji boundary UI | Current Integration route audit | `connected boundary page` |
| `app/labtools_runtime.py` | Historical recovered calculator/reagent/WB UI path | Recovery commits `ca006ee`, `f18b9a0`, `a33cffe`, `edfa2a5`, `7afe07b`, `e64454b`, `b40cc8d` | `historical high-fidelity/recovered source, not current target route` |
| `app/labtools_storage_adapter.py` | Historical storage adapter skeleton | Recovery commit `edfa2a5` | `adapter skeleton; scoped reconciliation required` |
| `app/labtools/labtools_home.py` | LabTools home introduced by `a4edda1` | Historical workspace wiring | `recovery source; not proof of current active route` |

## Page Style Matrix

Legend:

- `figma/high-fidelity`: high-fidelity mockup or mockup-to-implementation evidence exists in `docs/ui`.
- `figma/new shell`: current Shell or Workbench design-system layer exists, but page may still need runtime proof.
- `hybrid`: new shell wraps older runtime/service pages or partial route state.
- `old`: old functional page structure or minimal target page.
- `placeholder`: visible affordance with no active target.
- `missing`: expected page or route is absent from current target.

### Shell

| Area | Page / Route | Evidence | Classification | Notes |
| --- | --- | --- | --- | --- |
| Welcome | Enter BioMedPilot | `app/shell/login.py`, `9d4edf3` | `figma/new shell` | Accepted packaged preview baseline. |
| Welcome | Register / Forgot password | current route inventory | `placeholder` | No account/password service target. |
| Home | Bio card/button | `app/shell/module_selection.py`, current route inventory | `figma/new shell + connected route` | Opens Bio workspace. |
| Home | Meta card/button | `app/shell/module_selection.py`, current route inventory | `figma/new shell + connected route` | Opens Meta workspace. |
| Home | LabTools card/button | current route inventory | `old target page` | Handler exists, but lands on minimal ImageJ/Fiji page. |
| Sidebar | Dashboard / Bio / Meta | current route inventory | `connected` | Source-visible handlers and target pages exist. |
| Sidebar | LabTools | current route inventory | `old target page` | Same LabTools risk as Home card. |
| Sidebar | Settings Center | current route inventory | `placeholder/hybrid` | Page exists, but route and final style need scoped audit. |
| Sidebar registry | Project/Data/Task/Report/Local Environment/Packaging | current route inventory | `missing` | Registry entries are not visible connected pages. |

### Bioinformatics

| Page | High-Fidelity Evidence | Recovery / Runtime Evidence | Classification |
| --- | --- | --- | --- |
| Project Home | `Bioinformatics_Project_Home_Workflow_Overview_candidate_v2_20260522.png` | `900ba60`, `2063ce8` | `figma/high-fidelity source; gated shell` |
| Data Source | `Bioinformatics_Data_Source_Selection_candidate_v2_20260522.png` | `900ba60` | `figma/high-fidelity source; gated shell` |
| Data Check & Preparation | `Bioinformatics_Data_Check_Preparation_Readiness_Table_candidate_20260522.png` | `62739aa` | `figma/high-fidelity source; gated shell` |
| Group & Design | `Bioinformatics_Group_Design_Comparison_Setup_candidate_20260522.png` | `62739aa` | `figma/high-fidelity source; gated shell` |
| Analysis Tasks | `Bioinformatics_Analysis_Tasks_DEG_Preflight_candidate_20260522.png` | `4061d72`, C5 gap `high` | `figma/high-fidelity source; runtime needs skeleton rebuild` |
| Result & Report | Result/report/export mockup | `2d5a560`, C5 gap `high` | `figma/high-fidelity source; export/report gated` |
| Report Export | Result/report/export mockup | `2d5a560`, C5 gap `high` | `figma/high-fidelity source; formal export missing` |
| Settings & Resources | existing shell reference | resource gates and Settings docs | `hybrid/reference shell` |
| Project Logs / Technical Details | existing shell reference | developer diagnostics only | `hybrid/diagnostic` |
| GEO / local import older pages | legacy `app/bioinformatics/pages/**` | old service/page stack | `old functional pages` |
| TCGA / GTEx / Cox / clinical audit advanced pages | service/runtime files exist | no final page proof in this audit | `missing or preflight-only until scoped page audit` |

### Meta Analysis

| Page | High-Fidelity Evidence | Recovery / Runtime Evidence | Classification |
| --- | --- | --- | --- |
| Project Home | `META-MOCK-001` | `bf6aaf8`, `87f3f9a`, C5 gap `critical` | `figma/high-fidelity source; runtime rebuild still needed` |
| Question / Meta Type | `META-MOCK-002` | `bf6aaf8`, C5 gap `critical` | `figma/high-fidelity source; draft-only gated shell` |
| Search Strategy | `META-MOCK-003` | `e551f44`, C5 gap `high` | `figma/high-fidelity source; execution disabled/gated` |
| Import / Reference / Dedup | `META-MOCK-004` | `e551f44` | `figma/high-fidelity source; hybrid with old functional stack` |
| Screening | `META-MOCK-005` | `557b645`, C5 gap `high` | `figma/high-fidelity source; manual-review gated shell` |
| Full-text / Extraction | `META-MOCK-006` | `557b645` | `figma/high-fidelity source; no automatic extraction claim` |
| Risk of Bias | `META-MOCK-006` | `557b645` | `figma/high-fidelity source; draft/manual-review boundary` |
| Result Review | `META-MOCK-007` | `6fe2295`, C5 gap `critical` | `figma/high-fidelity source; no fake formal result` |
| Report-ready Gate / Export | `META-MOCK-008` | `6fe2295`, C5 gap `critical` | `figma/high-fidelity source; export disabled until artifact proof` |
| Network Meta | C2a forbids activation | no active target | `missing/disabled by policy` |
| Forest/table preview | future/shell-only in inventory | no final formal plot proof | `missing or shell-only` |

### LabTools

| Page | High-Fidelity / Mockup Evidence | Recovery / Runtime Evidence | Current Integration Classification |
| --- | --- | --- | --- |
| LabTools Home | C2a sequence, C5 gap `medium` | `3bf79f4`, `ed396b4`, `a4edda1` | `missing from current target / recovery source exists` |
| General / Quick Calculator | C2a sequence, C5 gap `high` | `ca006ee` via `app/labtools_runtime.py` | `missing from current target / recovery source exists` |
| Dynamic Formula Solver | C2a sequence | historical calculator line | `missing from current target` |
| Reagent Template / Preparation | C2a sequence, C5 gap `critical` | `f18b9a0`, `edfa2a5`, `e64454b` | `missing from current target / recovery source exists` |
| WB Loading | C2a sequence, C5 gap `critical` | `a33cffe`, `ed396b4` | `missing from current target / recovery source exists` |
| SDS-PAGE | C2a placeholder plan | no current route proof | `missing / planned placeholder` |
| BCA / OD | C2a MVP boundary | no current route proof | `missing / planned boundary` |
| Cell Experiment Workspace | C2a shell plan; later `4cd06fb` in carryover graph | current inventory says absent | `missing from current target / recovery source exists` |
| ELISA / Immuno-Absorbance | C2a boundary plan | no current route proof | `missing / blocked boundary` |
| Image Processing / ImageJ-Fiji | C2a boundary plan | current `app/labtools/workspace.py` + `image_analysis_widgets.py` | `old/minimal connected boundary page` |

## Why the Current Integration Looks Like an Older Version

1. The historical recovery branch and the current Integration worktree are different lines.
   - `codex/integration-labtools-ui-c2-carryover` contains the recovered UI line.
   - Current `/Users/changdali/Developer/biomedpilot v1.0/Integration` is on `integration/release-ui-shell-scoped-migration` at `7682b98`.

2. The accepted packaged preview baseline is not a license to merge the whole branch.
   - `9d4edf3` is accepted as the Shell / packaged preview baseline.
   - Project Control already states that neither `9d4edf3` nor `e13d0f5` may be merged wholesale into MainLine.
   - Page recovery must be scoped by route, page, runtime, and test evidence.

3. LabTools has a concrete path mismatch.
   - Historical recovered pages: `app/labtools_runtime.py` plus `app/shell/main_window.py`.
   - Current Integration target: `app/labtools/workspace.py` plus `app/labtools/ui/image_analysis_widgets.py`.
   - Current `app/labtools/workspace.py` exposes only `image_analysis`, so calculator/reagent/WB/cell pages are absent even though historical recovery commits exist.

4. Direct cherry-pick was already shown to be risky.
   - Shared UI foundation conflicts occur in `app/ui_style_tokens.py`, `app/app_identity.py`, `app/shared/ui_components/**`, `app/bioinformatics/workflow_pages.py`, and tests.
   - Therefore the correct next step is scoped reconciliation, not replaying whole historical commits.

## Missing / Not Fully Made Pages

### High priority missing from current Integration target

| Module | Missing / Incomplete Area | Reason |
| --- | --- | --- |
| LabTools | Module home and second-level IA | Current route lands on single ImageJ/Fiji boundary page. |
| LabTools | General calculator, reagent preparation, WB loading | Historical recovery exists, but current `app/labtools/workspace.py` does not expose these pages. |
| LabTools | Cell experiment workspace / cell information | Historical/recovery evidence exists, current target route absent. |
| Project Control / Shell | Project Center, Data Center, Task Center, Report Center, Local Environment, Packaging | Sidebar registry-only or missing target pages. |
| Dashboard | Recent project rows | Placeholder in current visible Home route. |

### Design exists but runtime still needs visual rebuild or proof

| Module | Pages | Evidence |
| --- | --- | --- |
| Bioinformatics | Analysis Tasks, Result/Report/Export | C5 gap matrix marks `high`; gates must remain disabled until artifact proof. |
| Meta Analysis | Project Home, Question/Type, Search, Screening/Extraction, Result/Export | C5 gap matrix marks `high` or `critical`; formal execution/export still gated. |
| Settings | Settings home/resources | C5 gap matrix marks `critical`; current route inventory still treats Settings Center as placeholder/hybrid. |

### Old / hybrid pages that should not be counted as final high-fidelity UI

| Module | Area | Reason |
| --- | --- | --- |
| Bioinformatics | `app/bioinformatics/pages/**` legacy GEO/local/import/group/report pages | Functional old page stack remains alongside new gated shell. |
| Meta Analysis | `app/meta_analysis/pages/**` functional workflow pages | Active services/pages exist, but they are not identical to C2 high-fidelity mockup shell pages. |
| LabTools | Current `app/labtools/workspace.py` ImageJ/Fiji page | Connected boundary page only; not the recovered LabTools multi-page workbench. |

## Recommended Next Governance Step

1. Keep `codex/integration-labtools-ui-c2-carryover` as the UI page recovery reference line.
2. Keep `9d4edf3` as the accepted Shell / packaged preview baseline.
3. Do not wholesale merge `9d4edf3`, `e13d0f5`, or the full carryover branch.
4. Create a scoped LabTools reconciliation plan before touching code:
   - compare `app/labtools_runtime.py` recovery pages against current `app/labtools/workspace.py`;
   - map each LabTools page to current page style: `figma/new`, `old`, `hybrid`, `placeholder`, or `missing`;
   - only then migrate page-by-page with route tests.
5. Run a separate live screenshot audit of current Integration after the dirty Shell migration stabilizes, because current source evidence and historical design evidence are not enough to certify final visual fidelity.
