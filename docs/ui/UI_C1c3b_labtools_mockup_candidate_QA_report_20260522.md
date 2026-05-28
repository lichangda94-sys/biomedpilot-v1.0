# UI-C1c3b LabTools Mockup Candidate QA Report

Date: 2026-05-22

## 1. Scope

This stage reviews the saved LabTools high-fidelity mockup candidates against:

- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`
- `docs/ui/UI_C1c2_labtools_high_fidelity_mockup_prompt_pack_20260522.md`
- `docs/ui/UI_C1c2_labtools_visual_style_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c3_cell_experiment_ia_recalibration_20260522.md`
- `docs/ui/UI_C1c3_cell_experiment_workspace_mockup_prompt_20260522.md`
- `docs/ui/UI_C1c3_cell_experiment_screen_acceptance_checklist_20260522.md`

This stage only performs image QA, revision briefing, and implementation input organization. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`; does not implement UI; does not add LabTools backend features; does not execute UI-B10; does not package or run a packaged app.

## 2. Reviewed Mockup Images

| Mockup | Image Path | File Check |
| --- | --- | --- |
| LabTools Home | `/Users/changdali/Desktop/UI/界面示意图/IMG-04 LabTools : 实验工具首页.png` | PNG, 1536 x 1024 |
| Quick Calculator + Dynamic Formula Solver | `/Users/changdali/Desktop/UI/界面示意图/labtools/Quick Calculator + Dynamic Formula Solver.png` | PNG, 1586 x 992 |
| Reagent Template + Preparation Workflow | `/Users/changdali/Desktop/UI/界面示意图/labtools/2. Reagent Template + Preparation Workflow.png` | PNG, 1536 x 1024 |
| Western Blot Loading focused mockup | `/Users/changdali/Desktop/UI/界面示意图/labtools/3. Western Blot Loading + SDS-PAGE Gel.png` | PNG, 1536 x 1024 |
| BCA / OD MVP Boundary | `/Users/changdali/Desktop/UI/界面示意图/labtools/4. BCA : OD MVP Boundary.png` | PNG, 1536 x 1024 |
| Cell Experiment Workspace | `/Users/changdali/Desktop/UI/界面示意图/labtools/图 5：Cell Experiment Workspace : 细胞实验工作区.png` | PNG, 1536 x 1024 |

## 3. Decision Summary

| Mockup | Decision | Summary |
| --- | --- | --- |
| LabTools Home | `accepted_with_text_revisions` | IA is correct; several homepage phrases still overclaim completeness/save semantics. |
| Quick Calculator + Dynamic Formula Solver | `accepted_with_boundary_review` | Strong candidate; add a small boundary label for cell plating helper and keep save/export disabled. |
| Reagent Template + Preparation Workflow | `accepted_with_text_revisions` | Structure is strong; save-template button styling should be visibly adapter-needed rather than active primary. |
| Western Blot Loading focused mockup | `accepted_with_boundary_review` | WB loading focus is correct; keep lane preview schematic and avoid treating later protein workflow steps as active. |
| BCA / OD MVP Boundary | `accepted_with_text_revisions` | MVP structure is correct; revise green success wording so it does not imply production quantification. |
| Cell Experiment Workspace | `accepted_with_boundary_review` | New IA is correctly applied; preserve shell/adapter-needed states and keep ImageJ/Fiji execution disabled. |

## 4. LabTools Home QA

Decision: `accepted_with_text_revisions`

Pass:

- Keeps exactly three first-level entries: `通用计算器`, `试剂制备`, `实验模块`.
- Does not expose ImageJ/Fiji, image analysis, inventory, cloud sync, LAN sharing, or collaboration as first-level entries.
- Chinese is the primary UI language with English secondary labels.
- Developer Preview / local testing state is visible.
- Quick access area includes `使用指南`, `常见问题`, `意见反馈`, and `最近使用`.

Issues:

- The Experiment Modules text `提供完整的实验方案与计算支持` overclaims completeness.
- The Reagent Preparation bullet `保存与稳定性提示` can imply real save/stability management.
- The General Calculator bullet `更多计算工具` is broad and may imply unsupported calculators.
- Homepage-level review notice is still not prominent.

Required revisions:

- Replace `提供完整的实验方案与计算支持` with `提供实验模块入口与计算辅助`.
- Replace `保存与稳定性提示` with `配制复核提示` or `记录保存需适配`.
- Replace `更多计算工具` with `更多通用计算入口` or `更多工具（规划中）`.
- Add `实验计算结果需由用户复核后用于台面操作。`

Keep:

- Overall layout, sidebar, three-card hierarchy, quick access, and Developer Preview chip.

## 5. Quick Calculator + Dynamic Formula Solver QA

Decision: `accepted_with_boundary_review`

Pass:

- Does not mix in WB, SDS-PAGE, BCA, ELISA, qPCR workflow, or cell record saving.
- Shows Quick Calculator and Formula Solver as General Calculator modes.
- Save history and export are disabled / adapter-needed.
- Warning and review notices are visible.
- Copy result is the only clearly active result action.

Boundary review:

- The left task list includes `细胞铺板辅助`. This is acceptable only as helper/calculator content, not cell record saving or a full cell culture workflow.
- The right result chip `可计算 / 需复核` is acceptable, but should not be upgraded to production-ready.

Required revisions:

- Add or keep a helper-specific label for `细胞铺板辅助`: `仅计算辅助`.
- Keep `保存到历史 - 需适配` and `导出结果 - 暂未开放` disabled.

Keep:

- Layout, left task registry, center form, formula section, right result/warning panel, and bottom review notice.

## 6. Reagent Template + Preparation Workflow QA

Decision: `accepted_with_text_revisions`

Pass:

- Template list, preparation run, and template editor side panel are clearly separated.
- The screen shows storage adapter boundary text: BioMedPilot storage adapter provides the save path and desktop UI should not default write to `~/.labtools`.
- No inventory decrement, production batch release, cloud template library, or multi-user sync is shown.
- Preparation result table and user review checkboxes are clear.

Issues:

- `保存模板 - 需存储适配` is styled as a strong blue primary action. Even with safe text, this can visually imply the save is active.
- `后端可用` near the preparation area is acceptable for calculation, but should not be read as record persistence being available.

Required revisions:

- Style `保存模板 - 需存储适配` as disabled or secondary adapter-needed, not strong primary.
- Keep `复制配制摘要` as the only strong active action.
- Add adjacent explanation if needed: `模板保存需 BioMedPilot 存储适配器。`

Keep:

- Three-zone layout, PBS example, validation panel, component editor, review warning, and storage path notice.

## 7. Western Blot Loading Focused Mockup QA

Decision: `accepted_with_boundary_review`

Pass:

- The visible working area focuses on WB loading calculation rather than SDS-PAGE calculation.
- Lane layout shows sample IDs and sample/loading volumes.
- Warning row for S3 is clear and tied to negative water volume / target volume issue.
- Save/export actions are adapter-needed or locked.
- No fake gel sample bands, image analysis, automatic band recognition, or antibody recommendation is shown.

Boundary review:

- The protein workflow stepper includes SDS-PAGE, transfer, antibody incubation, exposure, result assist, and export record. This is acceptable as a muted workflow roadmap only if inactive steps remain visually secondary.
- `后端可用` should apply to WB loading calculation only, not the full protein workflow.
- The marker ladder graphic is acceptable as layout context, but sample lanes must remain schematic and not display fake bands.

Required revisions:

- Add microcopy near the workflow stepper: `当前仅展示 WB 上样计算；后续步骤为流程占位。`
- Keep `编辑布局` scoped to lane layout planning, not real gel result editing.

Keep:

- WB config, sample table, calculation table, warning row, lane layout schematic, and locked save/export actions.

## 8. BCA / OD MVP Boundary QA

Decision: `accepted_with_text_revisions`

Pass:

- Shows 8 x 12 OD matrix.
- Shows well annotation for Blank, Standard, and Sample.
- Shows linear-fit summary and warning/review panel.
- Save/export actions are disabled or locked.
- No ELISA, 4PL workflow, formal report, formal save, or clinical-grade quantification is shown.

Issues:

- Green wording `拟合效果良好，可用于样本浓度估算（需用户复核）` is close to acceptable, but for an MVP boundary page it should be softer and not imply formal quantification readiness.
- Top status chip `可计算` should be interpreted only as MVP calculation preview, not production analysis.

Required revisions:

- Replace `拟合效果良好，可用于样本浓度估算（需用户复核）` with `拟合预览已生成，仅供用户复核参考。`
- Replace or qualify `可计算` with `MVP 预览可计算`.

Keep:

- Matrix, annotation side panel, standard/sample table, fit summary, warnings, disabled save/export, and storage-path notice.

## 9. Cell Experiment Workspace QA

Decision: `accepted_with_boundary_review`

Pass:

- Correctly uses the recalibrated `细胞实验 / Cell Experiment` workspace instead of the old mixed boundary page.
- Includes three main areas: `细胞信息`, `细胞实验记录`, and `细胞结果处理工具`.
- ELISA is not part of the main page; the review notice explicitly says ELISA / absorbance is not on this page.
- ImageJ/Fiji appears only as an external engine callout with Settings entry and disabled analysis action.
- Save cell record and image analysis actions are disabled or adapter-needed.
- No fake saved records, fake timeline, automatic ROI, automatic cell counting, or automatic analysis results are shown.

Boundary review:

- `新建记录 - 需记录存储适配` appears on multiple cards. This is acceptable because it is visually disabled, but it must stay disabled in implementation.
- `计算辅助可用` on seeding is acceptable only for the cell seeding helper, not full cell record saving.
- The bottom timeline correctly uses an empty state. Keep it empty unless a real record store is implemented.

Required revisions:

- Keep `运行图像分析 - 暂未开放` disabled.
- Keep `保存记录` disabled or adapter-needed.
- Add no ELISA cards or absorbance plate UI to this workspace.

Keep:

- Three-area IA, status overview, record template cards, ImageJ/Fiji Settings callout, timeline empty state, and review notice.

## 10. Cross-Candidate Findings

Strengths:

- Visual style is now consistently high fidelity and aligned with a desktop PySide workbench.
- The LabTools first-level IA is preserved.
- Developer Preview / local testing state is consistently present.
- Most disabled / adapter-needed actions are labelled clearly.
- Cell Experiment IA correction is successfully reflected in the latest cell workspace image.

Main risks:

- Strong primary styling on adapter-needed save actions can visually contradict disabled boundary text.
- Green success styling on MVP calculations can overstate readiness.
- Workflow steppers may imply downstream steps are available unless marked as roadmap/shell.
- General Calculator can safely contain `cell plating helper`, but it must not become cell record saving or workflow management.

## 11. Extra Mockup Recommendation

| Additional Mockup | Recommendation | Reason |
| --- | --- | --- |
| Reagent side panel detail | Yes | Needed to inspect validation states, disabled save styling, dirty-state behavior, and storage adapter messaging. |
| WB lane/warning detail | Yes | Needed to inspect lane layout warnings, negative volume handling, and schematic-only lane visualization at implementation detail level. |
| ELISA / Immuno-Absorbance boundary | Yes | ELISA was correctly removed from Cell Experiment; a separate boundary mockup is needed for Immuno / Absorbance without overclaiming. |

## 12. Verification

| Command | Result |
| --- | --- |
| `file ... LabTools mockup images ...` | Passed: all six reviewed images are PNG files |
| `python3 - <<'PY' ... CSV structure check ... PY` | Passed: 9 rows, 12 columns |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
