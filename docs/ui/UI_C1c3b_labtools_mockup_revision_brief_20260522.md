# UI-C1c3b LabTools Mockup Revision Brief

Date: 2026-05-22

## 1. Scope

This brief converts the UI-C1c3b mockup QA findings into concrete revision instructions for the LabTools high-fidelity image set. It is design guidance only and does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`.

## 2. Global Revision Rules

Apply these rules to all LabTools mockups:

- Keep Chinese as primary UI text.
- Keep Developer Preview / local testing state visible.
- Keep disabled / adapter-needed / shell-only states text-labelled.
- Use active primary styling only for actions that do not imply unsupported persistence, export, analysis, or record creation.
- Do not visually upgrade disabled functionality into active functionality.
- Do not introduce ImageJ/Fiji as a LabTools first-level entry.
- Do not introduce inventory, cloud sync, LAN sharing, collaboration, App icon, packaging, or desktop-entry concepts.

## 3. Must Modify

| Mockup | Required Change | Replacement / Direction |
| --- | --- | --- |
| LabTools Home | Replace overclaim in Experiment Modules card. | `提供实验模块入口与计算辅助` or `提供已接入工具与待接入模块的分组导航` |
| LabTools Home | Replace `保存与稳定性提示`. | `配制复核提示` or `记录保存需适配` |
| LabTools Home | Add homepage review notice. | `实验计算结果需由用户复核后用于台面操作。` |
| Reagent Workflow | Make `保存模板 - 需存储适配` visibly disabled or secondary adapter-needed. | Keep `复制配制摘要` as the only strong active action. |
| BCA / OD MVP | Replace green success text. | `拟合预览已生成，仅供用户复核参考。` |
| BCA / OD MVP | Qualify `可计算`. | `MVP 预览可计算` |
| Cell Experiment Workspace | Keep ImageJ/Fiji run disabled. | `运行图像分析 - 暂未开放` must remain disabled. |

## 4. Suggested Modify

| Mockup | Suggested Change | Reason |
| --- | --- | --- |
| LabTools Home | Replace `更多计算工具` with `更多通用计算入口` or `更多工具（规划中）`. | Avoid implying unsupported calculators. |
| Quick Calculator + Formula Solver | Mark `细胞铺板辅助` as `仅计算辅助`. | Prevent confusion with cell record saving. |
| Quick Calculator + Formula Solver | Keep `可计算 / 需复核` chip but avoid stronger success styling. | Calculation helper is not production protocol validation. |
| Reagent Workflow | Add short note near status chips: `后端可用仅指计算，保存需适配`. | Prevent reading persistence as complete. |
| Western Blot Loading | Add stepper note: `当前仅展示 WB 上样计算；后续步骤为流程占位。` | Avoid implying full protein workflow is active. |
| Western Blot Loading | Keep lane layout as schematic. | Prevent fake gel result interpretation. |
| Cell Experiment Workspace | If space allows, add `接种计算辅助不等于细胞记录保存`. | Clarifies cell seeding helper boundary. |

## 5. Can Keep

| Mockup | Keep |
| --- | --- |
| LabTools Home | Sidebar, three primary cards, quick access, Developer Preview chip, icon style. |
| Quick Calculator + Formula Solver | Mode tabs, task registry, dilution form, formula form, right result panel, warnings, disabled save/export. |
| Reagent Workflow | Three-zone layout, PBS examples, preparation result table, component editor, validation hints, storage path warning. |
| Western Blot Loading | WB config, sample table, calculation result table, S3 warning, lane layout preview, locked save/export. |
| BCA / OD MVP | 8 x 12 OD matrix, annotation side panel, standard/sample table, fit summary, warning panel, disabled save/export. |
| Cell Experiment Workspace | Three main areas, profile/status panel, record template grid, result processing panel, ImageJ/Fiji Settings callout, empty timeline. |

## 6. Per-Mockup Revision Instructions

### 6.1 LabTools Home

Priority: Must revise text before implementation reference.

Instructions:

- Keep the three first-level cards exactly as shown.
- Add a compact review notice under the cards or above quick access.
- Replace overclaiming text in Experiment Modules.
- Replace Reagent Preparation save/stability phrasing.
- Do not add ImageJ/Fiji or image analysis on this page.

### 6.2 Quick Calculator + Dynamic Formula Solver

Priority: Boundary review before implementation planning.

Instructions:

- Keep layout and data.
- Keep save/export disabled.
- Add boundary label for `细胞铺板辅助`: `仅计算辅助`.
- Do not add qPCR workflow, WB, SDS-PAGE, BCA, ELISA, or cell record saving.

### 6.3 Reagent Template + Preparation Workflow

Priority: Revise button styling before implementation reference.

Instructions:

- Change save-template primary button into disabled or secondary adapter-needed control.
- Keep copy summary active.
- Keep storage adapter notice.
- Do not add inventory deduction, production batch release, cloud template library, or multi-user sync.

### 6.4 Western Blot Loading

Priority: Boundary review before implementation planning.

Instructions:

- Keep focus on WB loading calculation.
- Add note that later protein workflow steps are placeholders.
- Keep lane layout schematic and sample-volume based.
- Do not show fake gel bands, antibody recommendations, band analysis, or image analysis.

### 6.5 BCA / OD MVP

Priority: Revise success wording before implementation reference.

Instructions:

- Keep OD matrix and annotations.
- Soften green fit-success language into preview/review language.
- Keep save/export disabled.
- Do not add ELISA, 4PL, formal report, production save/export, or clinical-grade claims.

### 6.6 Cell Experiment Workspace

Priority: Accepted for cell IA direction with boundary review.

Instructions:

- Keep three areas: Cell Profile, Experiment Record Templates, Result Processing.
- Keep ELISA out of the page.
- Keep ImageJ/Fiji only as Settings-linked external engine callout.
- Keep record save and image analysis disabled/adapter-needed.
- Do not show fake records, fake timeline, automatic ROI, automatic cell counting, or automatic analysis results.

## 7. Additional Mockups To Generate

| Mockup | Generate? | Brief |
| --- | --- | --- |
| Reagent side panel detail | Yes | Focus on component validation, pH fields, dirty state, disabled save, and storage adapter notice. |
| WB lane/warning detail | Yes | Focus on S3 warning, lane layout schematic, impossible volume handling, and locked export. |
| ELISA / Immuno-Absorbance boundary | Yes | Separate page under Immuno / Absorbance; blocked-until-backend; no ELISA result, 4PL, report, or active export. |

## 8. Implementation Planning Guardrails

Before any UI-C2 implementation:

- Treat mockups as visual references, not proof of implemented backend.
- Preserve `semanticKey`, `pageKey`, `moduleKey`, `statusKey`, and existing shell gating patterns.
- Keep save/export/report/image-analysis disabled unless the corresponding backend, storage adapter, and file picker are implemented.
- Do not default write to `~/.labtools`.
- Do not change App icon, Finder icon, `.icns`, Info.plist, LaunchServices, package smoke, or desktop app runtime.

## 9. Verification

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
