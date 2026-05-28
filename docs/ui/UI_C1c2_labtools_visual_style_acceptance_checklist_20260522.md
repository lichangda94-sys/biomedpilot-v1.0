# UI-C1c2 LabTools Visual Style Acceptance Checklist

Date: 2026-05-22

## 1. Scope

This checklist defines the visual acceptance criteria for LabTools high-fidelity mockups generated from `UI_C1c2_labtools_high_fidelity_mockup_prompt_pack_20260522.md`.

This stage does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`; does not implement UI; does not add backend features; and does not touch App icon, Finder icon, `.icns`, Info.plist, LaunchServices, packaging, signing, or desktop entries.

## 2. Global Visual Specification

| Area | Acceptance Rule |
| --- | --- |
| Desktop frame | Mockups should target 1360 x 860 or 1440 x 900 desktop canvas and keep the current app shell/sidebar mental model. |
| Page density | Use workbench density: compact tables, practical forms, and visible review states. Avoid landing-page hero composition. |
| Main content padding | Use 24 px outer page padding and 16 px grid gaps. |
| Cards | Use 8 px radius or less, light background, neutral border, and restrained shadow. |
| Nested cards | Avoid decorative card-in-card layouts; use section dividers inside cards instead. |
| Tables | Use readable compact rows, clear headers, numeric alignment for volumes/concentrations, and warning highlight on affected rows. |
| Side panels | Right panels should be 360-420 px wide with fixed footer actions and section headings. |
| Modals | If used for template editing, modal/side panel must show validation and action footer. |
| Buttons | Primary action for copy/navigation only when allowed; save/export buttons must be disabled or adapter-needed unless specified otherwise. |
| Empty states | Use quiet icon/illustration, concise Chinese copy, and no fake data. |
| Typography | Chinese UI labels should be primary. Experiment terms can remain English or bilingual. |

## 3. Status Chip Rules

| Status Type | Visual Rule | Copy Examples | Forbidden Interpretation |
| --- | --- | --- | --- |
| Backend-ready helper | Neutral/green-light chip with text label | `后端可用`, `可计算` | Does not mean production protocol validation. |
| Adapter-needed | Amber/neutral chip, visible explanation nearby | `需适配`, `需存储适配`, `需文件选择器` | Does not mean save/export is active. |
| Shell-only | Grey/blue-neutral chip | `仅壳层`, `暂未开放` | Does not mean feature is ready. |
| Blocked | Muted red/grey chip, not alarming unless action attempted | `后端未完成`, `blocked_until_backend` | Does not mean runtime failure. |
| Review required | Amber note row | `需用户复核` | Does not mean formal approval or QA completed. |

Acceptance rules:

- Status chips must keep text labels. No icon-only status.
- Tooltip or adjacent explanation must remain visible for disabled or adapter-needed controls.
- Status chips must not change feature availability semantics.

## 4. Warning, Blocker, And Adapter-Needed Rows

| Row Type | Visual Style | Required Behavior |
| --- | --- | --- |
| Review notice | Light amber background, compact icon, short Chinese text | Always visible on calculator, reagent, WB/SDS, and BCA pages. |
| Adapter-needed | Light neutral/amber row or button suffix | Explains missing storage/file-picker adapter. |
| Blocked | Muted red/grey row, clear reason | Used for ELISA backend, cell record saving, unsupported ImageJ/Fiji execution. |
| Calculation warning | Highlight affected result row and warning side panel | Does not hide result table; requires user review. |

Forbidden:

- Do not make warnings look like successful completion.
- Do not use red error styling for planned or adapter-needed states unless the action is truly blocked.
- Do not hide adapter-needed explanations behind icon-only tooltips.

## 5. Result Panel Rules

| Page | Result Panel Acceptance |
| --- | --- |
| Quick Calculator | Shows calculated result card, warning list, and review notice. Copy allowed; save/history adapter-needed. |
| Formula Solver | Shows solved target and formula context. Missing or invalid input must not generate fake values. |
| Reagent Preparation | Shows calculated component table before save. Save/export remains adapter-needed. |
| Western Blot Loading | Shows sample/result tables and warning rows. Lane preview is schematic only. |
| SDS-PAGE Gel | Shows resolving/stacking component tables. XLSX export remains adapter-needed. |
| BCA / OD | Shows matrix, annotation, fit summary, and warnings. Save/export disabled or adapter-needed. |
| Shell-only pages | No result panel with fake values. Use empty state or blocked state instead. |

## 6. Disabled Save / Export Button Rules

| Button | Allowed State | Required Copy |
| --- | --- | --- |
| Save calculator history | Disabled or adapter-needed | `保存到历史 - 需适配` |
| Save reagent template | Disabled or adapter-needed unless storage adapter exists | `保存模板 - 需存储适配` |
| Save preparation record | Disabled or adapter-needed | `保存配制记录 - 需存储适配` |
| WB export | Disabled or adapter-needed | `导出 CSV / Markdown - 需文件选择器` |
| SDS-PAGE export | Disabled or adapter-needed | `导出 XLSX - 需文件选择器` |
| BCA save/export | Disabled | `保存 BCA 记录 - 后端记录模型未完成` |
| ELISA action | Disabled / blocked | `运行 ELISA 分析 - 后端未完成` |
| ImageJ/Fiji run | Disabled | `运行图像分析 - 暂未开放` |

Acceptance rules:

- Disabled buttons must remain visually disabled.
- Disabled buttons must not use strong primary styling.
- Copy/navigation buttons may be active only when they do not imply persistence or production export.

## 7. Empty State Rules

| Surface | Empty State Copy |
| --- | --- |
| LabTools recent activity | `暂无最近实验工具记录` |
| Quick Calculator | `请选择计算器或公式` |
| Reagent Template List | `当前项目暂无试剂模板` |
| Reagent Preparation Run | `请选择试剂模板后计算本次配制` |
| WB Loading | `添加样本后计算上样体积` |
| SDS-PAGE Gel | `选择配胶模板后计算组分` |
| BCA / OD | `粘贴 8 x 12 OD 数据并标注孔位` |
| Cell Records | `暂无保存的细胞实验记录` |

Acceptance rules:

- Empty states must not show fake saved history, fake records, or fake analysis results.
- Empty states can include a small illustration or existing empty state asset, but the copy must carry the real state.

## 8. LabTools Icon Usage

Allowed:

- `module_labtools` as module marker.
- LabTools P1 active icons for General Calculator, Reagent Preparation, Experiment Modules, and experiment category markers.
- Settings resource icon for ImageJ/Fiji only inside Settings-linked external capability callout.
- Status icons only as auxiliary markers where existing status chip behavior allows.

Forbidden:

- Do not use ImageJ/Fiji as first-level LabTools card.
- Do not use icons to make shell-only or blocked features look complete.
- Do not use App icon, Finder icon, `.icns`, iconset, or packaging icons.
- Do not introduce new active icons or replace active resources in this stage.

## 9. IA Acceptance Checklist

| Check | Pass Criteria |
| --- | --- |
| Three-entry LabTools IA | First-level entries are exactly `通用计算器`, `试剂制备`, `实验模块`. |
| General Calculator scope | Contains Quick Calculator and Dynamic Formula Solver only. |
| Reagent Preparation scope | Contains template list/editor and preparation run. |
| Experiment Modules scope | Contains WB, SDS-PAGE, BCA/OD, qPCR/helper, cell shell, ELISA shell as nested module targets. |
| ImageJ/Fiji scope | Appears only as Settings-linked external capability, not first-level entry. |
| BCA/OD scope | Presented as MVP boundary, not ELISA and not full absorbance system. |

## 10. Per-Prompt Acceptance Checklist

### 10.1 LabTools Home

- Exactly three first-level cards are visible.
- No ImageJ/Fiji, inventory, cloud sync, LAN sharing, or collaboration first-level card.
- Recent activity uses empty state unless real data is explicitly provided by future adapter.
- Quick access includes Settings/external capability link without implying execution.

### 10.2 Quick Calculator + Dynamic Formula Solver

- Quick Calculator and Formula Solver are modes under General Calculator.
- WB, SDS-PAGE, BCA, qPCR workflow, ELISA, and cell records are not placed here.
- Result card includes warning/review notice.
- Save/history and export are disabled or adapter-needed.

### 10.3 Reagent Workflow

- Template list, template editor, and preparation run are visually connected but not confused.
- Storage-root adapter boundary is visible.
- Save/export buttons are not active production controls.
- No inventory decrement, cloud library, or multi-user sync is implied.

### 10.4 Western Blot + SDS-PAGE

- Protein workflow substep bar is visible.
- WB loading and SDS-PAGE tables use real example-like layout without fake gel bands.
- Warnings for impossible volumes are visible.
- Export remains adapter-needed.
- No image analysis or band quantification is shown.

### 10.5 BCA / OD MVP Boundary

- 8 x 12 OD matrix is visible.
- Annotation side panel is visible.
- Linear-fit summary is clearly marked MVP/testing.
- Save/export is disabled or adapter-needed.
- No ELISA, 4PL, formal report, or production save/export claim.

### 10.6 Cell / ELISA / ImageJ-Fiji Shell-Only Boundary

- Cell record categories are shown without fake saved records.
- ELISA is blocked until backend.
- ImageJ/Fiji links to Settings only.
- Unsupported actions are disabled with explanations.
- No fake result table, image preview, or completed record is shown.

## 11. High-Fidelity Mockup Rejection Criteria

Reject a generated mockup if any of these appear:

- ImageJ/Fiji as a first-level LabTools entry.
- WB, BCA, qPCR workflow, ELISA, or cell records inside General Calculator.
- ELISA appears available or complete.
- Cell record save appears active.
- ImageJ/Fiji execution or built-in image analysis appears active.
- Save/export buttons appear enabled where the required adapter/backend is missing.
- Fake gel bands, fake BCA production report, fake ELISA curve, fake history, or fake saved records.
- Default write path to `~/.labtools`.
- App icon, Finder icon, Info.plist, LaunchServices, package, signing, or desktop-entry changes.

## 12. Verification

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
