# UI-C1c3-cell0 Cell Experiment IA Recalibration

Date: 2026-05-22

## 1. Scope

This stage recalibrates the LabTools cell experiment information architecture after finding that UI-C1c2 Prompt 6 incorrectly grouped Cell Records, ELISA, and ImageJ/Fiji into one generic shell-only boundary page.

Inputs reviewed:

- `docs/ui/UI_C1c2_labtools_high_fidelity_mockup_prompt_pack_20260522.md`
- `docs/ui/UI_C1c2_labtools_visual_style_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`
- `docs/ui/UI_C1c_labtools_backend_aligned_mockup_assurance_plan_20260522.md`
- `docs/ui/references/labtools/LabTools_UI_integration_contract_20260522.md`
- `docs/ui/references/labtools/LabTools_screen_inventory_mockup_plan_20260522.md`
- `docs/ui/references/labtools/LabTools_backend_gap_audit_20260522.md`
- Current UIShell app/test surfaces related to LabTools and cell experiment semantics.

This stage only adds IA, screen spec, and mockup prompt documents. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, or `dist/**`; does not implement UI; does not add backend features; does not execute UI-B10; does not package or run a packaged app.

## 2. Current Issue

UI-C1c2 Prompt 6 currently describes a combined page named `Cell Records / ELISA / ImageJ-Fiji Shell-Only Boundary Page`. That grouping is useful as a temporary boundary reminder, but it is not the target product IA.

Problems:

- It places Cell Records, ELISA, and ImageJ/Fiji in one generic boundary page.
- It does not give `细胞实验 / Cell Experiment` its own workspace under LabTools > Experiment Modules.
- It risks making ImageJ/Fiji appear as a peer capability instead of a Settings-linked external engine used only inside result processing.
- It risks mixing ELISA into cell experiment even though ELISA belongs under Immuno / Absorbance.
- It does not model the cell lifecycle concepts needed for a real cell experiment workspace: cell profile, dynamic state, freeze/thaw/passaging timeline, and record templates.

Decision:

- UI-C1c2 Prompt 6 is superseded for the cell experiment mockup direction.
- ELISA must move out of the Cell Experiment Workspace and remain under Immuno / Absorbance or a separate ELISA boundary page.
- ImageJ/Fiji must appear only inside the Cell Experiment Workspace as a result-processing external-engine callout, with Settings as the source of configuration.

## 3. Current Runtime And Backend Audit

| Area | Current Finding | Implication |
| --- | --- | --- |
| Current UIShell LabTools home | `app/shell/main_window.py` renders LabTools as a shell with three primary entries and nested experiment category icons, including `细胞实验`. | Cell experiment exists only as an experiment category marker in the current UI branch. |
| Current semantic keys | `app/shared/semantic_keys.py` has `labtools.page.cell_experiments`. | A stable page key exists for future routing, but no full cell workspace is implemented. |
| Current active icon registry | `app/app_identity.py` maps `labtools.page.cell_experiments` to the LabTools cell experiment icon. | Icon support exists; it must not be interpreted as functional readiness. |
| Current UI tests | `tests/ui/test_labtools_shell.py` and `tests/ui/test_p1_labtools_icon_active_pilot.py` assert that cell experiment is a nested experiment category, not a first-level card. | Current runtime guards the top-level IA, but not a dedicated cell workspace. |
| Current UIShell record models/stores | No current app-side cell dossier, freeze batch, freeze vial, thawing, passage, seeding, treatment, transfection record store was found in `app/**`. | Real record save must remain `blocked_until_backend` or `adapter_needed`. |
| Standalone LabTools contract | `CellSeedingInput`, `CellSeedingResult`, and `calculate_cell_seeding_v1()` are stable for UI. | Cell seeding can be shown as a helper/calculator area, not as a complete cell record system. |
| Cell experiment records | Reference audit says no `CellExperimentTemplate`, `CellExperimentRecord`, or `CellExperimentRecordStore`. | Cell record templates are shell-only until store/model exists. |
| ImageJ/Fiji | Reference audit says no executable discovery, macro runner, ROI model, result parser, or safety boundary. | Result processing can show external-engine status and Settings link only. |
| ELISA | `labtools.elisa` has no public API. | ELISA remains blocked under Immuno / Absorbance, not Cell Experiment. |

## 4. Recalibrated Target IA

Path:

`LabTools > 实验模块 > 细胞实验 / Cell Experiment`

The Cell Experiment Workspace contains three main areas:

| Main Area | English Name | Purpose | Current Readiness |
| --- | --- | --- | --- |
| 细胞信息 | Cell Profile & Dynamic State | Track the cell line/dossier, current passage, culture state, freeze/thaw state, contamination/mycoplasma/morphology/confluence notes, and timeline. | `shell_only` / `adapter_needed` until current UI branch has a cell profile model/store. |
| 细胞实验记录 | Experiment Record Templates | Provide record template entry points for passage, recovery/thawing, freezing, seeding, treatment, and transfection. | `shell_only`; cell seeding helper may be `active_backend_ready` as a calculator/helper only. |
| 细胞结果处理工具 | Result Processing | Show scratch/transwell/fluorescence/staining image result-processing entry points and ImageJ/Fiji external engine status/configuration. | `shell_only`; ImageJ/Fiji requires external engine adapter and must not imply built-in algorithms. |

ELISA relocation:

- ELISA / Absorbance belongs under `LabTools > 实验模块 > 免疫与吸光度`.
- ELISA must not appear inside the Cell Experiment Workspace.
- ELISA remains `blocked_until_backend` until a real ELISA MVP backend exists.

## 5. Cell Experiment Workspace Screen Spec

| Field | Specification |
| --- | --- |
| `screen_id` | `cell_experiment_workspace` |
| Page name | `细胞实验 / Cell Experiment Workspace` |
| IA location | `LabTools > 实验模块 > 细胞实验` |
| Page purpose | Provide a dedicated cell experiment workspace for cell state, record templates, and result-processing entry points while preserving current backend boundaries. |
| Backend readiness | Overall `shell_only` / `adapter_needed`; cell seeding helper is `active_backend_ready` only as a calculator/helper. |
| Backend API references | Current UI branch: no cell record store found. Contract helper: `CellSeedingInput`, `CellSeedingResult`, `calculate_cell_seeding_v1()`. Future store needs `CellExperimentTemplate`, `CellExperimentRecord`, `CellExperimentRecordStore`. |
| Required panels | Cell profile panel, dynamic state strip, status timeline, record template grid, helper/action panel, result-processing panel, ImageJ/Fiji external engine callout. |
| Primary user action | Review current cell state, choose a record template, use helper calculation if available, or open Settings for external result-processing engine configuration. |
| Save/copy/export | Copy helper result can be planned/allowed if generated by stable helper; save cell record must be disabled or adapter-needed; export disabled until record/export model exists. |
| Empty state | `当前项目暂无细胞档案。请先选择或创建细胞信息模板；保存功能需后续记录模型支持。` |
| Must-not-claim | No real record save, no automatic analysis, no ImageJ/Fiji execution, no ELISA, no fake timeline generated from nonexistent records, no cloud/LAN collaboration. |

## 6. Main Area A - Cell Profile & Dynamic State

| Field | Required Mockup Content | Status Rule |
| --- | --- | --- |
| Cell name / cell line | Example: `A549` or `HEK293T`; editable-looking field is allowed in mockup. | `adapter_needed` until cell profile model/store exists. |
| Species / tissue / disease model | Example rows: human, lung, carcinoma model. | Shell display only; no ontology resolver implied. |
| Current passage | Example: `P12`; must be clearly user-entered or mock. | No automatic passage increment unless record store exists. |
| Culture conditions | Medium, serum, antibiotics, CO2, temperature. | Shell display only. |
| Current state | Chips: `培养中`, `冻存`, `复苏`, `传代后`, `待处理`. | State is visual/mock until record state model exists. |
| Freeze batches / vials | Batch and vial summary placeholders. | `blocked_until_backend` unless real freeze store exists. |
| Contamination / mycoplasma / morphology / confluence | Observation cards and latest note. | User-entered shell only; no automated detection. |
| State timeline | Recent state events. | Empty/shell timeline only; do not show fake saved records as real history. |

Safe visible copy:

- `细胞状态由实验记录更新；当前为 mockup / adapter-needed 状态。`
- `保存细胞档案需要后续记录模型与存储适配。`

## 7. Main Area B - Experiment Record Templates

Record template entries:

| Template | Purpose | Current State |
| --- | --- | --- |
| 传代 | Passage record template. | `shell_only` / `blocked_until_backend` |
| 复苏 | Thawing/recovery record template. | `shell_only` / `blocked_until_backend` |
| 冻存 | Freezing record template. | `shell_only` / `blocked_until_backend` |
| 接种 | Seeding record template, can link to cell seeding helper. | helper can be `active_backend_ready`; record save remains `adapter_needed` |
| 给药 / 处理 | Treatment record template. | `shell_only` / `blocked_until_backend` |
| 转染 | Transfection record template. | `shell_only` / `blocked_until_backend` |
| 从上次记录创建 | Create from previous record. | disabled until record store/history exists |

Required UI boundaries:

- Buttons may be shown as `打开模板预览`, `使用计算辅助`, or `待接入`.
- `保存记录` must be disabled or labelled `需记录存储适配`.
- Do not show a real saved-record list unless the data is explicitly marked sample/mock.
- Do not imply a completed cell experiment record system.

## 8. Main Area C - Result Processing

Result processing entries:

| Entry | Intended Scope | Current State |
| --- | --- | --- |
| 划痕实验 | Image-processing workflow concept for scratch assay. | `shell_only`; no auto ROI. |
| Transwell | Image/result processing concept. | `shell_only`; no automatic count. |
| 荧光 / 染色图像 | Future image review / processing entry. | `shell_only`; no automatic segmentation. |
| ImageJ/Fiji 外部引擎状态 | Show external engine status and Settings link. | Settings-linked only; no execution. |
| 设置中心入口 | Navigate to Settings external capability configuration. | Allowed as navigation, not analysis execution. |

Forbidden result-processing claims:

- No automatic ROI.
- No automatic cell counting.
- No automatic scratch closure measurement.
- No automatic Transwell counting.
- No automatic fluorescence quantification.
- No batch image analysis completed state.
- No ImageJ/Fiji macro execution.
- No built-in ImageJ/Fiji algorithms.

Safe visible copy:

- `结果处理工具用于规划与外部能力配置；自动分析需后续外部引擎适配。`
- `ImageJ/Fiji 配置在设置中心完成，当前不执行图像分析。`

## 9. Capabilities Matrix

| Capability | Can Be Mocked Now | Active UI Claim Allowed | Needs Backend / Adapter | Notes |
| --- | --- | --- | --- | --- |
| Cell profile layout | Yes | Shell/adapter-needed only | Cell profile model/store | Can design fields and state chips. |
| Dynamic state strip | Yes | Shell/adapter-needed only | Cell state model and record-derived updates | Do not show automatic state transitions. |
| Freeze batch / vial display | Yes | Shell-only | Freeze batch/vial models and store | Use placeholder or empty state. |
| Passage / thaw / freeze / treatment / transfection records | Yes | Shell-only | Record template/model/store | Save disabled. |
| Cell seeding helper | Yes | Helper/calculator only | UI adapter for helper and optional record bridge | Does not equal full cell record save. |
| Create from previous record | Yes | Disabled/future only | Record history store | No fake history. |
| Scratch / Transwell / fluorescence processing | Yes | Shell-only | Result-processing adapters | No automatic analysis. |
| ImageJ/Fiji status | Yes | Settings-linked status only | External engine adapter | No execution or macro runner. |
| ELISA | No in cell workspace | Not allowed here | ELISA MVP backend under Immuno/Absorbance | Must be removed from cell mockup. |

## 10. Required Corrections To UI-C1c2 Direction

| Existing C1c2 Item | Correction |
| --- | --- |
| `Prompt 6 - Cell Records / ELISA / ImageJ-Fiji Shell-Only Boundary Page` | Supersede with `Cell Experiment Workspace`. |
| ELISA appears in the same prompt as Cell Records | Move ELISA to Immuno / Absorbance or a separate ELISA boundary prompt. |
| ImageJ/Fiji appears as a sibling boundary block | Move ImageJ/Fiji into Result Processing as external-engine status and Settings link. |
| Cell Records shown only as category cards | Expand into a dedicated workspace with Cell Profile, Record Templates, and Result Processing. |

## 11. Must Not Appear In Cell Experiment Mockups

- ELISA / Absorbance as a cell experiment section.
- ImageJ/Fiji as a LabTools first-level entry.
- ImageJ/Fiji as an active built-in image algorithm.
- Automatic ROI, automatic cell counting, automatic band recognition, or real batch image analysis.
- Real cell record save unless a current branch backend store is implemented and wired.
- Fake saved records, fake timelines, fake result tables, or fake analysis outputs.
- Cloud sync, LAN sharing, collaboration, or inventory decrement.
- Default writes to `~/.labtools`.

## 12. Next Stage Recommendation

Use `docs/ui/UI_C1c3_cell_experiment_workspace_mockup_prompt_20260522.md` as the replacement prompt for the cell experiment image. Keep C1c2 Prompt 6 only as historical context, not as the target mockup instruction.

Recommended follow-up:

1. Generate a new high-fidelity `Cell Experiment Workspace` mockup candidate.
2. Separately generate an `ELISA / Immuno-Absorbance Boundary` mockup candidate.
3. Review both independently before any UI-C2 implementation planning.

## 13. Verification

| Command | Result |
| --- | --- |
| `rg -n "cell|Cell|细胞|...|ImageJ|Fiji|ELISA" docs/ui ...` | Passed: confirmed C1c2 mixed Prompt 6 and reference backend boundaries |
| `rg -n "LabTools|实验工具|实验模块|细胞实验|..." app tests ...` | Passed: current UIShell has category/page key/icon shell only; no cell record store found |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
