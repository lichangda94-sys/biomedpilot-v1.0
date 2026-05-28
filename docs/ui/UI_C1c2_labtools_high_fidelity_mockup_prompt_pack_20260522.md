# UI-C1c2 LabTools High-Fidelity Mockup Prompt Pack

Date: 2026-05-22

## 1. Scope

This prompt pack converts the UI-C1c1 LabTools P0 wireframe specification into high-fidelity mockup prompts for Figma, Canva, image generation, and Codex UI implementation planning.

Inputs:

- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`
- `docs/ui/UI_C1c1_labtools_p0_acceptance_matrix_20260522.csv`
- `docs/ui/mockup_data/labtools/UI_C1c1_labtools_mockup_sample_data_20260522.md`
- `docs/ui/UI_C1c_labtools_backend_aligned_mockup_assurance_plan_20260522.md`

This stage only creates design prompts and visual acceptance guidance. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`; does not implement real UI; does not add LabTools backend features; does not package or run the packaged app; and does not touch App icon, Finder icon, `.icns`, Info.plist, or LaunchServices.

## 2. Shared High-Fidelity Direction

Use a desktop PySide workbench style: light surface, practical density, restrained color, left navigation retained from the app shell, and a clear LabTools module workspace. The UI should feel like a real lab operations tool rather than a landing page.

Visual language:

- Canvas: 1360 x 860 or 1440 x 900 desktop mockup, with an app sidebar already present.
- Content width: full workspace with 24 px outer padding and 16 px internal grid gaps.
- Cards: 8 px radius, 1 px neutral border, white or near-white background, subtle shadow only for selected/active surfaces.
- Tables: compact but readable, 36-40 px row height, sticky header if the mockup shows long tables.
- Side panels: 360-420 px width, right anchored, with clear section dividers and footer actions.
- Status chips: small, text-first, do not rely on icon-only status.
- Warning rows: yellow/amber-tinted background for review notices; red only for hard blockers.
- Disabled and adapter-needed buttons: visible but subdued, with label and short tooltip copy.
- Empty states: quiet illustration or icon plus concise Chinese copy; no marketing-style explanation.
- Icons: use existing LabTools icon families only as supporting markers. Never use icons to imply feature completion.

Chinese UI copy requirement:

- Use Chinese labels as the visible primary text.
- Keep stable experiment terms in English or bilingual form where standard, for example `Western Blot`, `SDS-PAGE`, `BCA / OD`, `ImageJ/Fiji`.
- Use state labels such as `本地测试版`, `需要适配`, `暂未开放`, `仅壳层`, `需用户复核`.
- Do not display developer architecture phrases such as resolver-first or backend boundary in normal user copy. User-facing boundary copy should be short and operational.

## 3. Mockup Grouping Strategy

| Batch | Screens | Purpose |
| --- | --- | --- |
| Batch 1 | LabTools Home; Quick Calculator + Dynamic Formula Solver; Reagent Workflow | Establish the LabTools visual direction and the three-entry IA. |
| Batch 2 | Western Blot Loading + SDS-PAGE Gel; BCA / OD MVP Boundary | Design the high-density experiment calculation surfaces. |
| Batch 3 | Cell Records / ELISA / ImageJ-Fiji shell-only boundary | Lock blocked/shell-only visual language without fake results. |

## 4. Prompt 1 - LabTools Home

### Page Goal

Create a high-fidelity desktop PySide mockup for the LabTools home page. It must show exactly three first-level entries and a compact workbench surface for lab utility navigation.

### Prompt

Create a high-fidelity BioMedPilot LabTools home screen in a desktop PySide style. The left app sidebar is visible and LabTools is selected. The main content area uses a light workbench layout with a top title row: `实验工具 LabTools`, subtitle `本地实验计算、试剂配制与实验模块入口`, and a small status chip `本地测试版`.

The page must show exactly three large first-level cards in one row:

1. `通用计算器`
   - Supporting text: `稀释、单位换算、动态公式求解`
   - Child chips: `快速计算`, `公式求解`
   - Status chip: `可设计 UI / 需适配历史记录`
2. `试剂制备`
   - Supporting text: `试剂模板、本次配制、复核清单`
   - Child chips: `模板`, `本次配制`
   - Status chip: `后端可用 / 存储适配中`
3. `实验模块`
   - Supporting text: `蛋白、核酸、细胞、免疫与吸光度`
   - Child chips: `Western Blot`, `SDS-PAGE`, `BCA / OD`, `qPCR`, `细胞记录`
   - Status chip: `部分可用 / 部分壳层`

Below the cards, show a two-column lower area. Left: `最近使用` table shell with empty state `暂无最近实验工具记录`. Right: `快速入口` list with `使用指南`, `常见问题`, `意见反馈`, and `外部能力设置`.

Use LabTools module icons only as card markers. Do not show ImageJ/Fiji, image analysis, inventory, cloud sync, LAN sharing, or collaboration as first-level cards. If ImageJ/Fiji is referenced, show it only as a small Settings-linked callout under `外部能力设置`.

### Layout Structure

- Left app sidebar: existing main shell navigation.
- Center: page title, 3 first-level cards, recent use table.
- Right: quick access and Settings-linked capability callout.

### Required States And Copy

- Status chips: `本地测试版`, `需适配`, `仅壳层`.
- Warning/review notice: `实验计算结果需由用户复核后用于台面操作。`
- Empty state: `暂无最近实验工具记录`.

### Must Not Claim

- No ImageJ/Fiji first-level entry.
- No full inventory, cloud sync, LAN sharing, collaboration, or completed ELISA/cell record system.
- No active save/export claim on the home page.

## 5. Prompt 2 - Quick Calculator + Dynamic Formula Solver

### Page Goal

Create one high-fidelity mockup that shows General Calculator with two tabs or segmented modes: Quick Calculator and Dynamic Formula Solver.

### Prompt

Create a high-fidelity desktop PySide mockup for `通用计算器`. The page belongs under LabTools > General Calculator, not under experiment modules. Use a two-mode segmented control near the top: `快速计算` and `动态公式求解`.

For `快速计算`, show a left calculator selector list with options such as `稀释计算`, `单位换算`, `细胞铺板辅助`. The center form uses the dilution sample data:

- Stock concentration: `10 mM`
- Final concentration: `100 uM`
- Final volume: `2 mL`
- Diluent: `PBS`

The center result card shows:

- Stock volume: `20 uL`
- Diluent volume: `1980 uL`
- Result status: `需用户复核`

For `动态公式求解`, show a formula preview card: `C1 * V1 = C2 * V2`. Use a solve-target segmented control with `V1` selected. Show inputs `C1 = 5 mg/mL`, `C2 = 0.25 mg/mL`, `V2 = 10 mL`, and result `V1 = 0.5 mL`.

The right panel is a persistent review and warnings panel. It includes:

- `单位兼容性需确认`
- `小体积移液需注意精度`
- `保存历史记录需要后续存储适配`

Actions at the bottom:

- Primary active button: `复制结果`
- Secondary disabled button: `保存到历史 - 需适配`
- Disabled button: `导出 - 暂未开放`

Use Chinese visible copy. Keep formula variables in English. Keep status chip text-first. Use small calculator icons only as supporting markers.

### Layout Structure

- Left panel: calculator/formula selector, 260-300 px.
- Center panel: form, formula preview, result card.
- Right panel: warnings, review notice, adapter-needed state.

### Required States And Copy

- Status chip: `可计算 / 需复核`.
- Warning row: `实验计算结果需由用户复核后使用。`
- Empty state when no calculator selected: `请选择计算器或公式。`

### Must Not Claim

- Do not put Western Blot, SDS-PAGE, BCA, ELISA, qPCR workflow, or cell record saving inside General Calculator.
- Do not imply protocol validation or production record saving.
- Do not show fake history rows.

## 6. Prompt 3 - Reagent Template List + Template Editor + Reagent Preparation Run

### Page Goal

Create a high-fidelity reagent workflow mockup combining template list, right-side template editor, and preparation run preview.

### Prompt

Create a high-fidelity desktop PySide mockup for LabTools > `试剂制备`. The screen uses a three-zone workbench layout.

Left panel: `试剂模板` list with search and filter. Show one selected template `PBS 1x`, category `buffer`, target volume `1000 mL`, component count `4`, pH target `7.40`, status chip `模板可编辑 / 存储需适配`. Also show empty state styling for when no templates exist: `当前项目暂无试剂模板`.

Center panel: `本次配制` run form using selected template:

- Template: `PBS 1x`
- Target volume: `500 mL`
- Operator: `demo user`
- pH measured: `7.36`
- pH adjusted: `7.40`

Below the form, show calculated component preview:

- NaCl `4.00 g`
- KCl `0.10 g`
- Na2HPO4 `0.72 g`
- KH2PO4 `0.12 g`

Right side panel: `模板编辑` with metadata and component table:

- Template name
- Category
- Target volume
- pH target
- Component rows with component name, type, amount, unit, note

Footer actions:

- Active: `复制配制摘要`
- Disabled/adapter-needed: `保存配制记录 - 需存储适配`
- Disabled/adapter-needed: `导出记录 - 需文件选择器适配`

Show a warning/review notice block: `试剂模板和配制结果需要用户复核；桌面 UI 不应默认写入 ~/.labtools。`

### Layout Structure

- Left panel: template list, 300 px.
- Center panel: preparation run form and calculated result table.
- Right side panel: editor, 380-420 px, with footer buttons.

### Required States And Copy

- Status chips: `后端可用`, `需存储适配`, `需复核`.
- Empty state: `当前项目暂无试剂模板`.
- Adapter notice: `保存路径由 BioMedPilot 存储适配器提供`.

### Must Not Claim

- Do not imply inventory decrement, stock tracking, production batch release, cloud template library, or multi-user sync.
- Do not show save/export as active production actions.
- Do not show default `~/.labtools` storage as selected.

## 7. Prompt 4 - Western Blot Loading + SDS-PAGE Gel

### Page Goal

Create a high-density protein experiment mockup that combines Western Blot loading and SDS-PAGE gel calculation without claiming complete WB workflow or image analysis.

### Prompt

Create a high-fidelity desktop PySide mockup for LabTools > Experiment Modules > `蛋白实验`. Use a top substep bar with `蛋白定量`, `WB 上样`, `SDS-PAGE 配胶`, `泳道布局`, `转膜`, `抗体孵育`, `曝光记录`, `结果辅助`, `导出记录`. Highlight `WB 上样` and `SDS-PAGE 配胶` as the visible working area. Later substeps are muted or shell-only.

Left panel: Western Blot configuration:

- Target protein per lane: `20 ug`
- Sample buffer: `4x`
- Final loading volume: `20 uL`
- Reducing agent: `yes`

Center panel: WB sample table and result table:

Samples:

- S1, `2.0 ug/uL`, control
- S2, `1.5 ug/uL`, treatment low
- S3, `0.8 ug/uL`, treatment high

Result preview:

- S1: `10.0 uL` sample, `5.0 uL` buffer, `5.0 uL` water
- S2: `13.3 uL` sample, `5.0 uL` buffer, `1.7 uL` water
- S3: show warning because sample volume exceeds final volume and water is negative

Right panel: SDS-PAGE gel setup:

- Gel format: `mini gel`
- Number of gels: `2`
- Resolving gel: `10%`
- Stacking gel: `4%`

Show resolving/stacking result tables and a small lane layout helper. The lane layout must be schematic only, not a fake gel result.

Actions:

- Active: `复制上样表`
- Disabled/adapter-needed: `保存 WB 记录 - 需适配`
- Disabled/adapter-needed: `导出 CSV / Markdown - 需文件选择器`
- Disabled/adapter-needed: `导出 SDS-PAGE XLSX - 需文件选择器`

Show review notice: `配胶和上样结果需由实验人员复核；此页不提供图像分析或条带判读。`

### Layout Structure

- Top: protein workflow substep bar.
- Left: WB config card.
- Center: sample table and loading result table.
- Right: SDS-PAGE gel parameters, component tables, lane helper.

### Required States And Copy

- Status chips: `后端可用`, `需文件适配`, `需复核`.
- Warning row for S3: `上样体积超过目标体积，需复核浓度或目标上样量`.
- Empty state: `添加样本后计算上样体积`.

### Must Not Claim

- Do not show fake gel bands, fake image analysis, transfer optimization, antibody recommendation, band quantification, or completed WB record export.
- Do not place WB or SDS-PAGE inside General Calculator.

## 8. Prompt 5 - BCA / OD MVP Boundary

### Page Goal

Create a high-fidelity BCA / OD MVP boundary page with plate matrix, annotations, linear-fit summary, warnings, and disabled save/export.

### Prompt

Create a high-fidelity desktop PySide mockup for LabTools > Experiment Modules > `BCA / OD 记录`. This is an MVP boundary page, not ELISA, not a production report, and not a final save/export workflow.

Center-left: show a large 8 x 12 OD matrix grid with row labels A-H and column labels 1-12. Use the sample OD matrix values from the mockup sample data. Make the grid readable, with subtle selected-cell highlight.

Right side panel: `孔位标注`:

- A1:B2 blank, `0 ug/mL`
- A3:B12 standard, `25-2000 ug/mL`
- E1:H12 sample, `unknown`

Below the matrix: standards/sample table and a linear-fit summary card:

- Fit model: `linear`
- R2: `0.992`
- Slope: `mockup-only`
- Intercept: `mockup-only`

Warning panel:

- `低 R2 时需复核标准曲线`
- `高 CV 时需复核复孔`
- `负校正 OD 或超出标准范围时不得直接采用`
- `当前无正式记录保存和导出模型`

Action footer:

- Active: `复制预览`
- Disabled: `保存 BCA 记录 - 后端记录模型未完成`
- Disabled: `导出结果 - 暂未开放`

Use BCA/OD icon family as a page marker only. Do not show ELISA 4PL, report-ready state, or production save/export.

### Layout Structure

- Header with page title and status chips.
- Main left: OD matrix and paste area.
- Main right: annotation side panel.
- Bottom: fit summary, warnings, disabled actions.

### Required States And Copy

- Status chips: `MVP 边界`, `testing only`, `保存未开放`.
- Empty state: `粘贴 8 x 12 OD 数据并标注孔位`.
- Review notice: `BCA / OD 结果仅作为 MVP 预览，正式记录和导出需后续后端支持。`

### Must Not Claim

- Do not claim ELISA, 4PL analysis, formal report, production export, completed absorbance system, or clinical-grade quantification.
- Do not place BCA in General Calculator.

## 9. Prompt 6 - Cell Records / ELISA / ImageJ-Fiji Shell-Only Boundary Page

### Page Goal

Create a high-fidelity shell-only boundary page for future cell records, ELISA, and ImageJ/Fiji capability callouts without fake results or active unsupported actions.

### Prompt

Create a high-fidelity desktop PySide mockup for LabTools > Experiment Modules > `壳层与待接入能力`. The page groups three boundary areas: `细胞实验记录`, `ELISA / 吸光度`, and `ImageJ/Fiji 外部能力`.

Top notice: `以下能力仍处于壳层或后端待完成状态，不会生成正式记录或分析结果。`

Section 1: `细胞实验记录`

Show category cards for:

- `传代`
- `复苏`
- `冻存`
- `接种`
- `给药`
- `转染`

Each card has status chip `仅壳层` or `记录保存未开放`. Show empty state `暂无保存的细胞实验记录`.

Section 2: `ELISA / 吸光度`

Show blocked card with status chip `blocked_until_backend` and Chinese label `后端未完成`. Include concise copy: `标准曲线、样本稀释、记录保存和导出尚未固化。`

Section 3: `ImageJ/Fiji 外部能力`

Show Settings-linked external capability row:

- Status chip: `外部能力配置`
- Button: `前往设置中心`
- Disabled action: `运行图像分析 - 暂未开放`

Footer actions:

- `前往设置中心` can look active as navigation.
- `新建细胞记录`, `运行 ELISA 分析`, `运行 ImageJ/Fiji` are disabled with explanations.

### Layout Structure

- Top shell-only notice.
- Three vertical sections or a 2-column layout with larger Cell Records section and smaller ELISA/ImageJ cards.
- No result table, no fake image preview, no fake saved record.

### Required States And Copy

- Status chips: `仅壳层`, `后端未完成`, `外部能力配置`, `暂未开放`.
- Empty state: `暂无保存的细胞实验记录`.
- Warning row: `保存、导出和图像分析需后续后端与外部能力适配。`

### Must Not Claim

- Do not claim ELISA analysis availability.
- Do not claim cell record save availability.
- Do not claim ImageJ/Fiji execution, built-in image analysis, macro runner, ROI parser, or automatic result extraction.
- Do not make ImageJ/Fiji a LabTools first-level entry.

## 10. Cross-Prompt Must-Preserve Checklist

Every generated mockup must preserve:

- LabTools first-level IA: General Calculator, Reagent Preparation, Experiment Modules.
- Text label plus status chip for every testing, shell-only, blocked, or adapter-needed state.
- Chinese UI copy as primary visible text.
- Warning/review notice on calculation and MVP pages.
- Disabled or adapter-needed state for save/export where adapters are missing.
- No default write path to `~/.labtools`.
- No fake records, fake reports, fake exports, fake gel bands, fake image analysis, or fake ELISA results.

## 11. Verification

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
