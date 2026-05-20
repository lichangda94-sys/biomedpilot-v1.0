# UI-B8b-prep Resource Design / Figma / Icon Brief

Date: 2026-05-20

Status: design-prep brief only; no resource replacement

Purpose: convert the UI-B8a resource inventory and placeholder strategy into a design-facing brief for UI-B8b formal resource work. This document is the handoff for visual design, Figma structure and icon requirements. It does not authorize replacing active icons, touching App icon packaging, changing business UI flows or running packaged app validation.

## 1. Scope Boundary

In scope:

- Resource design brief for brand, module, Settings resource, status, empty state, Result / Report / Export, Bioinformatics, Meta Analysis and LabTools resource groups.
- Figma file/page/frame structure recommendation for a designer or future high-fidelity UI pass.
- Icon requirement table with semantic meaning, size classes, usage area, placeholder state and replacement gate.
- Acceptance criteria for a future UI-B8b formal resource replacement stage.

Out of scope:

- No replacement of active PNG, ICNS, SVG or bitmap resources.
- No App icon, Finder icon, Info.plist icon binding, LaunchServices, dist package or desktop entry work.
- No business page rewrite.
- No packaged app run.
- No high-fidelity UI implementation.
- No full i18n/language switching.

## 2. Source Inputs

| input | role |
|---|---|
| `docs/ui/UI_B8_resource_inventory_placeholder_strategy_audit_20260520.md` | Current resource inventory and placeholder policy baseline. |
| `docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv` | Slot-level resource status, active usage and replacement gates. |
| `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | Brand/resource conflict and missing visual asset baseline. |
| `docs/ui/UI_Visual_Style_Guide_v1_20260520.md` | Visual direction, token expectations and resource rules. |
| `docs/ui/UI_Rebuild_MasterPlan_20260520.md` | Current UI rebuild boundary and hard packaging gate. |
| `docs/ui/UI_Rebuild_Stage_Index_20260520.md` | Stage order and acceptance boundary. |

## 3. Design Principles

| principle | requirement |
|---|---|
| Semantic first | Icons must express existing `moduleKey`, `pageKey`, `statusKey`, `resource.status`, `analysis.status`, `report.status` meanings. Do not invent visual states that bypass semantic keys. |
| Low-fidelity continuity | Existing placeholders stay active until a complete replacement set and focused tests are ready. |
| No production overclaim | Planned, testing, shell-only, preflight-only and draft states must look restrained. They must not appear as completed or production-ready capability. |
| Local biomedical workbench | Visual language should be quiet, precise, work-focused and biomedical, not marketing-like. |
| Consistent families | Module icons, status icons, Settings resource icons and export format icons must each work as a coherent family. |
| Text remains authoritative | Icons support labels; they do not replace critical text for status, warnings or gated actions. |
| Packaging deferred | App icon and desktop icon design may be explored visually, but implementation and binding are UI-B10 only. |

## 4. Figma Brief

Recommended Figma file name:

`BioMedPilot_UI_B8b_Resource_System_v1_20260520`

Recommended pages:

| Figma page | required frames | notes |
|---|---|---|
| `00_Brief_and_Rules` | Brand hierarchy, forbidden scope, token references, status semantics. | Include explicit note: App icon is design exploration only before UI-B10. |
| `01_Brand_Lockups` | Horizontal lockup, stacked lockup, compact mark, text-only fallback. | Must clarify `萤火虫 / Firefly` vs `BioMedPilot / 医研智析`. |
| `02_Module_Icons` | Bioinformatics, Meta Analysis, LabTools, Settings. | LabTools must not reuse generic workspace icon as final. |
| `03_Status_Icons` | feature, resource, analysis, report status sets. | Include normal, disabled and tooltip-use variants. |
| `04_Settings_Resources` | External engines, models, analysis resources, developer diagnostics. | Python/R/ImageJ/Fiji names stay recognizable. |
| `05_Result_Report_Export` | Result empty state, report draft, export gated, format icons. | Avoid visual treatment that implies report-ready output. |
| `06_Bioinformatics_Pages` | 7 main pages + 2 auxiliary pages. | Use target IA names, not old UI04-UI13 numbering as final labels. |
| `07_Meta_Analysis_Types` | 10 active Meta type groups and planned Network Meta marker. | Network Meta must be visually planned/disabled. |
| `08_LabTools` | Three entry icons + five experiment category icons. | ImageJ/Fiji belongs to Settings, not LabTools primary IA. |
| `09_Empty_States` | Empty project, missing resource, no result, blocked/preflight, shell-only. | Keep illustrations compact and operational. |
| `10_Export_Spec` | Asset naming, size grid, light-mode export, review checklist. | Include source vector plus PNG export rules. |

Recommended frame sizes:

| frame_type | size |
|---|---|
| Desktop reference | `1440 x 900` |
| Minimum desktop check | `1180 x 760` |
| Icon design board | `1024 x 768` |
| Icon component grid | `24 / 32 / 48 / 64 px` cells |
| Empty state preview | `360 x 220` and `520 x 280` |

## 5. Resource Families and Requirements

| family | priority | required deliverables | current placeholder | replacement gate |
|---|---:|---|---|---|
| Brand lockup | P0 | Horizontal, stacked, compact mark, monochrome, text fallback. | Text brand + current app icon. | Brand hierarchy approval. |
| Module icons | P0 | Bioinformatics, Meta Analysis, LabTools, Settings at 24/32/48/64 px. | Bio/Meta active icons; LabTools workspace fallback; generic Settings icon. | Complete four-icon family and focused loader tests. |
| Status icons | P0 | `testing`, `planned`, `shell_only`, `developer_preview`, `blocked`, `available`, `not_configured`, `failed`, `preflight_only`, `draft`. | Text/color chips and `iconHint`. | Status chip mapping and focused tests. |
| Settings resource icons | P0 | External engines, local Python/R, ImageJ/Fiji, analysis resources, model resources, diagnostics. | Text/status cards. | Detect-first UI remains intact; no install/download action implied. |
| Result / Report / Export icons | P0 | Result preview empty, report draft, testing summary, export gated, Markdown/HTML/DOCX/CSV/XLSX. | Text buttons/panels. | Gating copy and disabled states preserved. |
| LabTools icons | P0 | Three primary entries and five experiment categories. | Text cards and workspace fallback. | LabTools IA remains three-entry; image analysis is not top-level. |
| Bio page icons | P1 | 7 main-flow pages + 2 auxiliary pages. | Old UI03 icons or text-only target shell. | Target page mapping frozen; no formal executor enabled. |
| Meta type icons | P1 | 10 active Meta type groups plus planned marker for Network Meta. | Text type cards. | Network Meta remains planned/disabled. |
| Empty state illustrations | P1 | Empty project, empty result, missing resource, blocked, shell-only, preflight. | Text cards. | Illustration style approved; does not obscure action gating. |
| Welcome/About visuals | P1 | Welcome main visual and About brand visual. | Text-only low-fidelity shell. | Brand lockup and visual style approved. |
| App icon / desktop icon | Deferred | May create exploration board only. | Current BioMedPilot icon set. | UI-B10 only. No implementation in UI-B8b-prep or UI-B8b without explicit gate. |

## 6. Icon Naming Requirements

Use stable semantic names. Do not name final icons after old screen numbers unless they remain only as legacy aliases.

| slot | required name pattern | examples |
|---|---|---|
| Module icon | `module_<module_key>_<size>.png` | `module_labtools_32.png` |
| Status icon | `status_<status_key>_<size>.png` | `status_developer_preview_24.png` |
| Resource icon | `resource_<resource_key>_<size>.png` | `resource_imagej_fiji_24.png` |
| Bio page icon | `bio_page_<page_key>_<size>.png` | `bio_page_data_source_32.png` |
| Meta type icon | `meta_type_<type_key>_<size>.png` | `meta_type_pairwise_meta_32.png` |
| LabTools icon | `labtools_<area_or_category>_<size>.png` | `labtools_reagent_preparation_32.png` |
| Export icon | `export_format_<format>_<size>.png` | `export_format_markdown_24.png` |
| Empty state | `empty_<semantic_state>.png` | `empty_missing_resource.png` |

Recommended future folders:

```text
assets/icons/modules/
assets/icons/status/
assets/icons/settings/resources/
assets/icons/bioinformatics/pages/
assets/icons/meta/types/
assets/icons/labtools/
assets/icons/result_report_export/
assets/images/empty_states/
assets/images/welcome/
assets/images/about/
```

Do not create or populate these folders during UI-B8b-prep unless a later implementation stage explicitly authorizes resource files.

## 7. Semantic Status Icon Map

| semantic_key | visual intent | must_not_imply |
|---|---|---|
| `feature.status.testing` | Available for testing; not validated as production. | Production readiness. |
| `feature.status.planned` | Future capability. | Clickable current capability. |
| `feature.status.shell_only` | Structural placeholder. | Working feature. |
| `feature.status.developer_preview` | Developer/test preview. | Public release. |
| `feature.status.blocked` | Blocked by prerequisite. | User error as primary blame. |
| `resource.status.available` | Detected and usable by shell. | Automatic install/update. |
| `resource.status.not_configured` | Needs user configuration. | Failure. |
| `resource.status.planned` | Future resource integration. | Current connection. |
| `resource.status.failed` | Detection failed. | Data loss. |
| `analysis.status.preflight_only` | Preflight/check only. | Formal analysis completion. |
| `analysis.status.testing_level` | Testing-level analysis. | Clinical/production result. |
| `analysis.status.blocked` | Resolver/input/state missing. | Hidden automatic fallback. |
| `report.status.draft` | User-editable draft boundary. | Report-ready package. |
| `report.status.testing_summary` | Testing summary only. | Formal publication-ready report. |
| `report.status.report_ready_future` | Future destination. | Current enabled export. |

## 8. Module-Specific Notes

### 8.1 Bioinformatics

Required target page icon set:

- Project Home
- Data Source
- Data Check & Preparation
- Group & Design
- Analysis Tasks
- Result & Report
- Report Export
- Bioinformatics Settings
- Project Logs & Technical Details

Rules:

- Do not resurrect old UI04-UI13 numbering as final IA.
- DEG/GSEA/survival/report-ready visuals must remain gated/preflight/testing where applicable.
- TCGA/GTEx and imported external result visuals must not imply automatic formal recomputation.

### 8.2 Meta Analysis

Required icon set:

- Pairwise meta
- Diagnostic test meta
- Prognostic factor meta
- Dose-response meta
- Single-arm meta
- Incidence/prevalence meta
- Correlation meta
- Risk model meta
- Genetic association meta
- Evidence map/scoping review
- Network Meta planned marker only

Rules:

- AI suggestion visuals must mean assistance, not automatic conclusion.
- Do not visually upgrade shell-only/testing workflow to production-grade systematic review.

### 8.3 LabTools

Required icon set:

- General Calculator
- Reagent Preparation
- Experiment Modules
- Cell experiments
- Protein experiments
- Nucleic acid experiments
- Immuno/absorbance experiments
- Immunohistochemistry

Rules:

- Do not make ImageJ/Fiji a LabTools primary entry; it belongs in Settings external image engine configuration.
- Do not put Western Blot, PCR, ELISA, MTT/CCK-8/AlamarBlue or BCA into the generic calculator visual family.
- LabTools is not Labors.

### 8.4 Settings

Required icon/resource groups:

- General settings
- Account/subscription placeholder
- Local project/storage
- External engines, models and analysis resources
- Developer diagnostics
- Python
- R
- ImageJ/Fiji
- External image analysis engine
- GO/KEGG/MSigDB
- Resolver/input package
- Report templates
- Local AI and cloud model placeholders

Rules:

- Detect-first visual language: detection/read status first; install/update/download only as explicit user-triggered actions in a later implementation stage.
- Technical resources stay in Settings, not ordinary module main flows.

## 9. Replacement Readiness Checklist for Future UI-B8b

A resource family is ready for implementation only when all are true:

- The Figma source frame is approved and exported with consistent names.
- The resource family is complete enough to avoid partial replacement confusion.
- Active usage paths and tests are listed before replacement.
- Placeholder-to-final migration table exists.
- Focused UI/resource tests are updated in the same stage.
- App icon / desktop icon / packaging paths are excluded unless the stage is UI-B10.
- The replacement does not change business workflow availability.

## 10. Future UI-B8b Acceptance Criteria

| area | expected UI-B8b acceptance |
|---|---|
| Resources | Add or replace only approved non-packaging resource families. |
| Inventory | Update `docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv` or create a dated successor. |
| Code references | Update only resource loader mappings needed for approved assets. |
| Tests | Add focused tests for icon path resolution and affected shell surfaces. |
| Boundaries | No App icon/Finder/Info.plist/LaunchServices/desktop `.app` work unless the task is explicitly UI-B10. |
| Verification | `git diff --check`, focused resource/UI tests, source smoke if loader paths change. |

## 11. Current Placeholder Policy

Continue placeholders until formal design is approved:

- Current App icon PNG/ICNS/iconset until UI-B10.
- Bioinformatics and Meta module icons until full module icon family is approved.
- LabTools workspace fallback until formal LabTools icon is approved.
- UI-01 login icons until Welcome/About resource plan is approved.
- UI-02 Dashboard icons until Dashboard resource map is approved.
- UI-03 Bio project icons until Bio target high-fidelity mapping is approved.
- Text-only Settings resource cards until Settings resource icons are approved.
- Text/status chips until formal status icon map is approved.
- Text-only Result / Report / Export shell until gated export icon family is approved.

## 12. Commands and Results

| command | result |
|---|---|
| `git status --short` | Clean before UI-B8b-prep edits. |
| `rg -n "UI-B8\|B8a\|B8b\|resource\|placeholder\|icon\|Figma\|Visual\|App icon\|Finder\|LaunchServices" docs/ui -S` | Read existing B8/A2/Style/MasterPlan/Stage resource boundaries. |
| `rg --files docs/ui \| sort` | Confirmed existing UI docs, resource inventory and target drafts. |
| `sed -n '1,240p' docs/ui/UI_B8_resource_inventory_placeholder_strategy_audit_20260520.md` | Read current resource inventory and placeholder policy. |
| `sed -n '1,220p' docs/ui/UI_Visual_Style_Guide_v1_20260520.md` | Read visual direction, token and resource rules. |
| `sed -n '1,120p' docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv` | Read slot-level resource inventory. |
| `git diff --check` | Passed. |

## 13. No Business Code / Resource Replacement Statement

UI-B8b-prep is documentation-only. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, `dist/**`, packaging metadata, active icon files, desktop entries or packaged apps.
