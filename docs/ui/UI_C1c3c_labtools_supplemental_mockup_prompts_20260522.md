# UI-C1c3c LabTools Supplemental Detail Mockup Prompts

Date: 2026-05-22

## 1. Scope

This stage prepares supplemental LabTools detail/boundary mockup prompts based on UI-C1c3b QA. It does not generate runtime UI, does not modify `app/**`, `tests/**`, or active `assets/**`, does not add backend features, does not execute UI-B10, and does not package or run a packaged app.

Inputs:

- `docs/ui/UI_C1c3b_labtools_mockup_candidate_QA_report_20260522.md`
- `docs/ui/UI_C1c3b_labtools_mockup_revision_brief_20260522.md`
- `docs/ui/UI_C1c3b_labtools_mockup_to_implementation_mapping_20260522.csv`
- `docs/ui/UI_C1c2_labtools_visual_style_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`

No images were generated in this stage. The prompts below are ready for Figma / Canva / image-generation / Codex UI design usage. If images are generated later, place non-runtime mockup outputs under `docs/ui/mockups/labtools/c1c3_supplemental/` and do not place them in active assets.

## 2. Shared Supplemental Prompt Rules

Apply these rules to all three supplemental mockups:

- Desktop PySide-style BioMedPilot shell with the left sidebar visible and LabTools selected.
- Chinese primary UI copy; English can appear as secondary labels for standard terms.
- Clear Developer Preview / 本地测试版 state.
- Disabled / adapter-needed / blocked states must be text-labelled.
- Do not make disabled actions look active.
- Do not imply runtime implementation or backend completion.
- Do not change feature state semantics.
- Do not touch App icon, Finder icon, `.icns`, Info.plist, LaunchServices, packaging, or desktop entry.

## 3. Prompt A - Reagent Template Editor Side Panel Detail

Purpose: `implementation_detail`

Use this prompt to generate a close-up high-fidelity mockup of the Reagent Template Editor side panel, focusing on validation, dirty state, storage adapter boundary, and safe save semantics.

### Prompt

Create a high-fidelity desktop PySide mockup detail view for BioMedPilot LabTools > `试剂制备 / Reagent Preparation`, focused on the right-side `模板编辑: PBS 1x` panel. The left app sidebar and main reagent workflow can be partially visible or blurred/faded in the background, but the side panel must be crisp and readable.

The side panel is 400-440 px wide, right anchored, with a header:

`模板编辑: PBS 1x`

Status chips in the header:

- `已修改未保存`
- `需存储适配`
- `需用户复核`

Panel sections:

1. `模板信息`
   - `模板名称`: `PBS 1x`
   - `分类 Category`: `buffer`
   - `默认体积 Default volume`: `1000 mL`
   - `pH 目标值`: `7.40`
   - `备注`: placeholder `请输入模板备注信息...`

2. `pH 设置`
   - `目标 pH`: `7.40`
   - `允许偏差`: `±0.05`
   - `pH 调整说明`: text area placeholder `记录 pH 调整策略，仅供复核`

3. `组分设置（共 4 项）`
   - Table columns: `组分 Component`, `类型 Type`, `所需量 / 1000 mL`, `单位 Unit`, `备注 Notes`, `验证`, `操作`
   - Rows:
     - NaCl, solid, 8.00, g, 分析纯, validation ok
     - KCl, solid, 0.20, g, 可选, validation ok
     - Na2HPO4, solid, 1.44, g, 无水物, validation warning `水合物需确认`
     - KH2PO4, solid, blank amount or highlighted row, unit g, validation error `所需量不能为空`

4. `验证与提示`
   - Green/neutral validation rows:
     - `组分名称与类型已校验`
     - `单位已设置`
   - Amber warning rows:
     - `Na2HPO4 水合物形式需人工确认`
     - `KH2PO4 所需量缺失，不能保存为可用模板`
     - `模板保存需 BioMedPilot 存储适配器，当前不可直接写入本地`

Footer actions:

- Secondary active button: `复制组分列表`
- Disabled button: `保存模板 - 需存储适配`
- Disabled button: `导出模板 - 需文件选择器`
- Text note: `保存路径由 BioMedPilot 存储适配器提供；桌面 UI 不应默认写入 ~/.labtools。`

Visual requirements:

- The save button must look disabled or secondary adapter-needed, not primary active blue.
- Dirty state must be visible but must not imply successful persistence.
- Use restrained warning colors; red only for invalid required fields.
- Use compact table rows and clear validation icons/chips.

Must not show:

- Inventory deduction.
- Stock tracking.
- Cloud template library.
- Multi-user sync.
- Production batch release.
- Active save without adapter.

## 4. Prompt B - Western Blot Lane And Warning Detail

Purpose: `implementation_detail`

Use this prompt to generate a focused detail mockup for WB loading lane layout and warning handling.

### Prompt

Create a high-fidelity desktop PySide mockup detail view for BioMedPilot LabTools > Experiment Modules > `蛋白实验 / Protein Experiment`, focused on `WB 上样计算` lane layout and warning review.

The mockup should show the protein workflow header, but only `WB 上样计算` is active. Other workflow steps such as `SDS-PAGE 配胶`, `泳道布局`, `转膜`, `抗体孵育`, `曝光记录`, `结果辅助`, and `导出记录` must appear muted or marked as `流程占位`.

Top notice:

`当前仅展示 WB 上样计算；后续蛋白实验步骤为流程占位。`

Main layout:

- Left: compact WB config summary card.
- Center: sample table and calculation result table.
- Right: lane layout schematic detail.
- Bottom: warning and locked action strip.

WB config:

- Target protein per lane: `20 ug`
- Sample buffer: `4x`
- Final loading volume: `20 uL`
- Reducing agent: `Yes`
- Denaturation: `95 C, 5 min`

Sample table:

| Sample ID | Protein concentration | Unit | Replicate | Notes |
| --- | --- | --- | --- | --- |
| S1 | 2.0 | ug/uL | A | control |
| S2 | 1.5 | ug/uL | A | treatment low |
| S3 | 0.8 | ug/uL | A | treatment high |

Calculation result table:

| Sample ID | Sample volume | 4x Buffer | Water | Total | Status |
| --- | --- | --- | --- | --- | --- |
| S1 | 10.0 uL | 5.0 uL | 5.0 uL | 20.0 uL | OK |
| S2 | 13.3 uL | 5.0 uL | 1.7 uL | 20.0 uL | OK |
| S3 | 25.0 uL | 5.0 uL | -10.0 uL | 20.0 uL | Warning |

Lane layout schematic:

- Include marker lane and lanes labelled `1` through `8`.
- Each lane card shows sample ID, target total volume, and sample volume:
  - Lane 1: S1, total 20 uL, sample 10.0 uL
  - Lane 2: S2, total 20 uL, sample 13.3 uL
  - Lane 3: S3, total 20 uL, sample 25.0 uL, warning highlight
  - Lane 4: S1 repeat
  - Lane 5: S3 repeat, warning highlight
  - Lane 6: Ctrl
  - Lane 7: Blank
  - Lane 8: empty

Warning detail panel:

- Title: `S3 上样体积异常`
- Warning text: `样品体积超过目标上样体积，水体积为负值。请降低目标上样量、提高样品浓度或重新分配泳道。`
- Review note: `结果需实验人员复核后用于台面操作。`

Action strip:

- Active: `复制上样表`
- Disabled: `保存 WB 记录 - 需适配`
- Disabled: `导出 CSV / Markdown - 需文件选择器`
- Disabled: `导出结果摘要 - 暂未开放`

Visual requirements:

- Lane layout must be schematic only.
- Show no fake gel bands.
- Show no transfer/antibody/image-analysis results.
- Warning lanes must be highlighted, but not look like failed runtime.
- Disabled actions must remain clearly locked.

Must not show:

- Fake gel band image.
- Image analysis.
- Automatic band recognition.
- Antibody recommendation.
- Active export.
- Completed WB record persistence.

## 5. Prompt C - ELISA / Immuno-Absorbance Boundary

Purpose: `boundary_clarification` and `blocked_feature_guardrail`

Use this prompt to generate a separate boundary mockup for ELISA under Immuno / Absorbance. This page exists to prevent ELISA from being mixed into Cell Experiment or BCA / OD MVP.

### Prompt

Create a high-fidelity desktop PySide mockup for BioMedPilot LabTools > Experiment Modules > `免疫与吸光度 / Immuno & Absorbance`, focused on an `ELISA / 吸光度` boundary page.

The page title:

`ELISA / 吸光度边界页`

Breadcrumb:

`实验工具 > 实验模块 > 免疫与吸光度 > ELISA / 吸光度`

Top status chips:

- `blocked_until_backend`
- `后端未完成`
- `不生成正式结果`
- `不导出报告`

Top blocker notice:

`ELISA 标准曲线、样本稀释、4PL/linear 策略、记录保存和导出模型尚未固化。当前页面仅用于说明边界，不执行 ELISA 分析。`

Layout:

Left panel: `当前不可用能力`

- `标准曲线拟合`: disabled, `后端未完成`
- `4PL 默认工作流`: disabled, `未定义`
- `样本稀释倍数计算`: disabled, `待 API 固化`
- `记录保存`: disabled, `需 record store`
- `报告导出`: disabled, `暂未开放`

Center panel: `未来 MVP 输入结构（预览）`

Show a greyed-out wireframe-like form:

- Plate format: `96-well`
- Standards: placeholder only
- Samples: placeholder only
- Dilution factor: placeholder only
- Fit strategy: disabled segmented control with `linear`, `4PL` muted

All controls must be disabled or visually non-editable.

Right panel: `边界与替代入口`

- `BCA / OD MVP` link-style row: `仅用于 BCA / OD 预览，不等于 ELISA`
- `设置中心`: external resources / analysis resources link if needed
- `开发状态`: `后端 MVP 之后再进入正式 UI`

Action footer:

- Disabled: `运行 ELISA 分析 - 后端未完成`
- Disabled: `保存 ELISA 记录 - 暂未开放`
- Disabled: `导出报告 - 暂未开放`
- Optional active navigation: `返回免疫与吸光度`

Visual requirements:

- Use blocked/disabled styling, not error panic.
- Make boundary explanation clear without developer-only architecture language.
- Keep ELISA separate from Cell Experiment and separate from BCA / OD MVP.
- No result chart, no standard curve, no calculated concentration table, no report preview.

Must not show:

- Active ELISA analysis.
- 4PL as default available workflow.
- Formal report.
- Production save/export.
- Clinical-grade quantification.
- Fake standard curve.
- Fake sample results.
- ELISA inside Cell Experiment.

## 6. Output And Asset Handling

This stage created prompt assets only. If future images are generated from these prompts:

- Save them under `docs/ui/mockups/labtools/c1c3_supplemental/`.
- Mark them as mockup-only, not runtime assets.
- Do not copy them into `assets/**`.
- Do not wire them into app loaders.

## 7. Verification

| Command | Result |
| --- | --- |
| `python3 - <<'PY' ... manifest CSV structure check ... PY` | Passed: 3 rows, 12 columns; no images generated |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
