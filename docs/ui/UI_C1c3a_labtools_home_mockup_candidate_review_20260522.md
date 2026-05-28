# UI-C1c3a LabTools Home Mockup Candidate Review

Date: 2026-05-22

## 1. Scope

This review evaluates the provided LabTools home high-fidelity mockup candidate against UI-C1c2 Prompt 1 and the LabTools visual acceptance checklist.

Reviewed image:

- `/Users/changdali/Desktop/UI/界面示意图/IMG-04 LabTools : 实验工具首页.png`
- Image metadata checked with `file`: PNG, 1536 x 1024, RGB.

Reference inputs:

- `docs/ui/UI_C1c2_labtools_high_fidelity_mockup_prompt_pack_20260522.md`
- `docs/ui/UI_C1c2_labtools_visual_style_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`

This stage only adds a design review document. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`; does not implement real UI; does not add LabTools backend features; does not package or run the packaged app; and does not touch App icon, Finder icon, `.icns`, Info.plist, or LaunchServices.

## 2. Review Conclusion

Decision: `accepted_with_text_revisions`

The candidate is structurally acceptable for Batch 1 LabTools Home. It preserves the three-entry IA, keeps Chinese as the primary UI language, includes Developer Preview / local testing state, and does not expose ImageJ/Fiji, image analysis, inventory, cloud sync, LAN sharing, or collaboration as first-level entries.

It needs text revisions before being treated as the approved LabTools Home mockup because several phrases can overstate current capability:

- `提供完整的实验方案与计算支持`
- `保存与稳定性提示`
- `更多计算工具`
- Some checkmark bullets may visually imply completed functionality rather than shell/planned/adapter-needed capability.

The layout itself does not require redesign.

## 3. Requirement-by-Requirement Review

| Requirement | Observed In Candidate | Result | Notes |
| --- | --- | --- | --- |
| Three first-level entries only | Shows `通用计算器`, `试剂制备`, `实验模块` as the only three main cards. | Pass | Matches UI-C1c2 Prompt 1 and C1c1 fixed IA. |
| No ImageJ/Fiji first-level entry | No ImageJ/Fiji card or image analysis entry is visible. | Pass | Keep ImageJ/Fiji only as Settings external capability in later screens. |
| No inventory/cloud/LAN/collaboration first-level entry | No such first-level card is visible. | Pass | Candidate stays within LabTools P0 home scope. |
| Chinese primary UI copy | Chinese is primary, English appears as secondary labels. | Pass | This matches the bilingual requirement. |
| Developer Preview / local testing retained | Shows `Developer Preview / 本地测试版` in title area and sidebar card. | Pass | Keep this state visible. |
| Homepage review notice | Not clearly present in main content. | Needs revision | Add concise notice: `实验计算结果需由用户复核后用于台面操作。` |
| General Calculator scope | Bullets show dilution, buffer/addition calculation, molecular mass conversion, unit conversion. | Mostly pass | Avoid `更多计算工具` unless it is clearly planned/limited; do not imply experiment modules are inside General Calculator. |
| Reagent Preparation scope | Shows reagent preparation and concentration conversion. | Needs text revision | `保存与稳定性提示` can imply persistence/stability management. Replace with safer wording. |
| Experiment Modules scope | Shows nested experiment module families only. | Pass with copy adjustment | `提供完整的实验方案与计算支持` overclaims. Replace with module-entry wording. |

## 4. Visual Acceptance Review

| Area | Result | Notes |
| --- | --- | --- |
| Desktop PySide workbench style | Pass | Light workspace, left sidebar, compact cards, and card-based module entry are consistent with target style. |
| Card shape and spacing | Pass | Cards are clear and readable. Border and radius are appropriate. |
| Status chip visibility | Pass | Developer Preview chip is visible. |
| Quick access area | Pass | `使用指南`, `常见问题`, `意见反馈`, `最近使用` match C1c2 direction. |
| Recent activity empty state | Partial | `最近使用` appears as quick access card, but no recent activity table/empty state. This is acceptable for this candidate if the implementation later keeps recent state clear. |
| Warning/review notice | Needs revision | Add homepage-level review notice in a compact row below the main cards or above quick access. |
| Icon usage | Pass | Uses LabTools/card icons as markers; no active resource replacement implication. |
| Disabled/adapter-needed states | Needs revision | Home page does not need many disabled buttons, but text should avoid implying save/export/history is already active. |

## 5. Overclaim Text Findings And Safer Replacements

| Current Text | Risk | Suggested Replacement |
| --- | --- | --- |
| `提供完整的实验方案与计算支持` | Implies complete experiment workflow and possibly protocol-level coverage. | `提供实验模块入口与计算辅助` |
| `保存与稳定性提示` | Implies real save, stability management, or persistence is already complete. | `配制复核提示` or `记录保存需适配` |
| `更多计算工具` | Could imply broad calculators beyond scoped General Calculator. | `更多通用计算入口` or `更多工具（规划中）` |
| `打开计算器` | Acceptable, but should route only to General Calculator. | Keep, or use `进入通用计算器` for IA clarity. |
| `进入试剂制备` | Acceptable, but avoid implying save/export is active. | Keep. |
| `选择实验模块` | Acceptable. | Keep. |
| `面向不同实验类型的专用工具，提供完整的实验方案与计算支持。` | Overstates module completeness. | `面向不同实验类型的专用入口，提供已接入工具与待接入模块的分组导航。` |

## 6. Required Text Revisions Before Approval

1. Add homepage review notice:
   - `实验计算结果需由用户复核后用于台面操作。`
2. Replace Experiment Modules card body:
   - From: `面向不同实验类型的专用工具，提供完整的实验方案与计算支持。`
   - To: `面向不同实验类型的专用入口，提供已接入工具与待接入模块的分组导航。`
3. Replace Reagent Preparation bullet:
   - From: `保存与稳定性提示`
   - To: `配制复核提示`
   - Alternative if the UI needs to expose boundary: `记录保存需适配`
4. Replace General Calculator bullet:
   - From: `更多计算工具`
   - To: `更多通用计算入口`
   - Alternative for stricter boundary: `更多工具（规划中）`
5. Consider changing checkmark bullets to neutral list bullets or pair them with status chips when the item is not fully active.

## 7. Must-Preserve Items

- Keep exactly three first-level LabTools cards:
  - `通用计算器`
  - `试剂制备`
  - `实验模块`
- Keep Developer Preview / local testing visible.
- Keep Chinese primary UI copy with English secondary labels.
- Keep quick access entries: `使用指南`, `常见问题`, `意见反馈`, `最近使用`.
- Keep ImageJ/Fiji out of first-level LabTools home.
- Keep inventory, cloud sync, LAN sharing, and collaboration out of first-level LabTools home.

## 8. Must-Not-Introduce In Revisions

- Do not add ImageJ/Fiji, image analysis, inventory, cloud sync, LAN sharing, or collaboration cards.
- Do not place WB, BCA, ELISA, qPCR workflow, or cell record saving inside `通用计算器`.
- Do not claim reagent save/history, inventory decrement, stability management, or production batch management is complete.
- Do not claim ELISA, cell experiment record save, or ImageJ/Fiji image analysis is complete.
- Do not add active save/export/report actions to the home page.

## 9. Implementation Handoff Notes

If this candidate later becomes the implementation reference, the PySide implementation should treat it as:

- Approved visual direction for LabTools Home after text revisions.
- Home IA source for three first-level cards only.
- Not a backend capability statement.
- Not a trigger to enable save/export/history behavior.
- Not a trigger to change icon resources, App icon, package metadata, or desktop entry.

## 10. Verification

| Command | Result |
| --- | --- |
| `file "/Users/changdali/Desktop/UI/界面示意图/IMG-04 LabTools : 实验工具首页.png"` | Passed: PNG image data, 1536 x 1024, 8-bit/color RGB |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
