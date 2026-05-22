# UI-C1c3 Cell Experiment Screen Acceptance Checklist

Date: 2026-05-22

## 1. Scope

This checklist reviews future `Cell Experiment Workspace` mockup candidates. It replaces the UI-C1c2 combined Cell Records / ELISA / ImageJ-Fiji boundary checklist for the cell experiment area.

It is a design review checklist only. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`; does not implement UI; does not add backend features; does not package; and does not touch App icon, Finder icon, `.icns`, Info.plist, or LaunchServices.

## 2. Required IA

| Check | Pass Criteria |
| --- | --- |
| Workspace path | The mockup is clearly under `LabTools > 实验模块 > 细胞实验`. |
| Cell experiment independence | The page is a dedicated cell experiment workspace, not a generic mixed boundary page. |
| Three main areas | The page includes `细胞信息`, `细胞实验记录`, and `细胞结果处理工具`. |
| ELISA excluded | ELISA / Absorbance does not appear inside the cell experiment workspace. |
| ImageJ/Fiji placement | ImageJ/Fiji appears only inside Result Processing as an external-engine status and Settings link. |
| LabTools top-level IA | ImageJ/Fiji is not a LabTools first-level card or sibling of the three LabTools first-level entries. |

## 3. Cell Profile & Dynamic State Checklist

| Required Content | Pass Criteria |
| --- | --- |
| Cell name / line | Shows a cell line field such as `A549` or equivalent sample. |
| Source metadata | Shows species, tissue, and disease/model metadata if applicable. |
| Current passage | Shows passage as user-entered/display state, not auto-derived. |
| Culture conditions | Shows medium/serum/CO2/temperature or equivalent culture condition fields. |
| Dynamic state | Shows state chips such as `培养中`, `冻存`, `复苏`, `传代后`, `待处理`. |
| Freeze batch / vial | Shows empty/shell or adapter-needed state, not real stored inventory. |
| Contamination/mycoplasma | Shows manual observation state, not automatic detection. |
| Morphology/confluence | Shows manual observation or placeholder state. |
| Timeline | Shows empty/shell timeline unless data is explicitly marked mock. |

Reject if:

- It shows real saved freeze batches or vials without a store.
- It shows automatic passage increment or state transition.
- It shows fake timeline events as real records.

## 4. Experiment Record Templates Checklist

| Template | Required State |
| --- | --- |
| 传代 | `shell_only` / disabled save |
| 复苏 | `shell_only` / disabled save |
| 冻存 | `shell_only` / disabled save |
| 接种 | may show `计算辅助可用`; record save remains `adapter_needed` |
| 给药 / 处理 | `shell_only` / disabled save |
| 转染 | `shell_only` / disabled save |
| 从上次记录创建 | disabled until history/store exists |

Pass criteria:

- Every template has a clear status chip.
- Disabled buttons have visible explanations.
- `保存记录` is disabled or marked `需记录存储适配`.
- Cell seeding helper does not imply a full record store.

Reject if:

- Cell record save appears active.
- A fake saved-record list appears as real data.
- Cloud sync, LAN sharing, collaboration, or inventory decrement appears.

## 5. Result Processing Checklist

| Entry | Required Boundary |
| --- | --- |
| 划痕实验 | Shell/planned; no automatic ROI. |
| Transwell | Shell/planned; no automatic cell counting. |
| 荧光 / 染色图像 | Shell/planned; no automatic segmentation or quantification. |
| ImageJ/Fiji | Settings-linked external engine status only. |
| 设置中心入口 | Allowed as navigation only. |

Pass criteria:

- Result processing is visually inside the cell workspace, not a LabTools first-level entry.
- ImageJ/Fiji has a Settings link and disabled run action.
- Copy states are clear: `暂不执行图像分析`, `外部能力配置`, `规划中`.

Reject if:

- Automatic ROI, automatic cell counting, automatic scratch closure, automatic Transwell counting, automatic fluorescence quantification, batch image analysis, or macro execution is shown as available.
- ImageJ/Fiji is represented as a built-in algorithm.
- ImageJ/Fiji has an active "run" action.

## 6. ELISA Exclusion Checklist

Pass criteria:

- ELISA is absent from the cell experiment mockup.
- No ELISA curve, 4PL model, absorbance plate workflow, standard curve, or ELISA result appears.
- Any ELISA mention points to a separate Immuno / Absorbance boundary page, not this workspace.

Reject if:

- ELISA appears as a section inside Cell Experiment.
- ELISA appears available, complete, or report-ready.
- BCA/OD or ELISA content is visually mixed with cell profile/records.

## 7. Status And Button Checklist

| UI Element | Required Behavior |
| --- | --- |
| Developer Preview chip | Visible near page title. |
| Record save state | `需记录存储适配`, `仅壳层`, or `blocked_until_backend`. |
| Result processing state | `规划中`, `外部能力配置`, or `暂未开放`. |
| Save buttons | Disabled unless a real current branch store exists. |
| Export buttons | Disabled unless a real current branch export adapter exists. |
| Settings button | Can be active navigation to Settings external capability page. |
| ImageJ/Fiji run button | Disabled. |

Reject if:

- Status is icon-only without text.
- Disabled actions use strong primary styling.
- Save/export/run controls look active when capability is missing.

## 8. Visual Style Checklist

| Area | Pass Criteria |
| --- | --- |
| Layout | Three-column desktop workbench layout or equivalent clear three-area hierarchy. |
| Density | Compact tables/cards suitable for repeated lab work. |
| Cards | 8 px radius or less, neutral borders, no decorative nesting. |
| Timeline | Empty/shell state is visually quiet and not confused with saved history. |
| Icons | LabTools cell icon is a marker only; Settings ImageJ/Fiji icon appears only in external engine callout if used. |
| Chinese copy | Chinese is primary; English appears as secondary labels or standard terms. |

## 9. Capability Classification For Review

| Capability | Review Label |
| --- | --- |
| Cell profile layout | `can_mockup_now / shell_only` |
| Cell dynamic state | `can_mockup_now / adapter_needed` |
| Passage/thaw/freezing/treatment/transfection records | `shell_only / blocked_until_backend` |
| Cell seeding helper | `active_backend_ready helper / record save adapter_needed` |
| Create from previous record | `blocked_until_history_store` |
| Scratch/Transwell/fluorescence result processing | `shell_only / external_adapter_needed` |
| ImageJ/Fiji status | `settings_linked_only / external_engine_adapter_needed` |
| ELISA | `out_of_scope_for_cell_workspace` |

## 10. Required Review Output

When reviewing a future image candidate, report:

- Decision: `accepted`, `accepted_with_text_revisions`, `accepted_with_boundary_review`, or `needs_redesign`.
- Whether the three main areas are present.
- Whether ELISA is absent.
- Whether ImageJ/Fiji is only a Settings-linked external engine callout.
- Whether record save and result processing states are correctly disabled/shell-only/adapter-needed.
- Text revisions needed to avoid overclaiming.

## 11. Verification

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
