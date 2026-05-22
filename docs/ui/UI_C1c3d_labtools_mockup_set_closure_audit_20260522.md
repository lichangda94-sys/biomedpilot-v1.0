# UI-C1c3d LabTools Mockup Set Closure Audit

Date: 2026-05-22

## 1. Scope

This closure audit summarizes the LabTools main mockup set and supplemental detail/boundary mockups. It identifies which images can be used as UI-C2 implementation references, which are boundary-only references, which still need text revisions, and which states must remain disabled / adapter-needed / shell-only.

This stage only adds audit documentation and an implementation readiness matrix. It does not modify `app/**`, `tests/**`, active `assets/**`, `scripts/**`, or `dist/**`; does not implement UI; does not add LabTools backend features; does not execute UI-B10; does not package or run a packaged app.

## 2. Reference Inputs

- `docs/ui/UI_C1c3b_labtools_mockup_candidate_QA_report_20260522.md`
- `docs/ui/UI_C1c3b_labtools_mockup_revision_brief_20260522.md`
- `docs/ui/UI_C1c3b_labtools_mockup_to_implementation_mapping_20260522.csv`
- `docs/ui/UI_C1c3c_labtools_supplemental_mockup_manifest_20260522.csv`
- `docs/ui/UI_C1c3c_labtools_supplemental_mockup_user_review_20260522.md`
- `docs/ui/UI_C1c1_labtools_p0_wireframe_spec_20260522.md`
- `docs/ui/UI_C1c2_labtools_visual_style_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c3_cell_experiment_ia_recalibration_20260522.md`

## 3. Reviewed Mockup Inventory

| Mockup | Path | Closure Status |
| --- | --- | --- |
| LabTools Home | `/Users/changdali/Desktop/UI/界面示意图/IMG-04 LabTools : 实验工具首页.png` | `implementation_reference_with_text_revision` |
| Quick Calculator + Dynamic Formula Solver | `/Users/changdali/Desktop/UI/界面示意图/labtools/Quick Calculator + Dynamic Formula Solver.png` | `implementation_reference` |
| Reagent Template + Preparation Workflow | `/Users/changdali/Desktop/UI/界面示意图/labtools/2. Reagent Template + Preparation Workflow.png` | `implementation_reference_with_text_revision` |
| Western Blot Loading focused page | `/Users/changdali/Desktop/UI/界面示意图/labtools/3. Western Blot Loading + SDS-PAGE Gel.png` | `implementation_reference` |
| BCA / OD MVP Boundary | `/Users/changdali/Desktop/UI/界面示意图/labtools/4. BCA : OD MVP Boundary.png` | `boundary_reference_only` |
| Cell Experiment Workspace | `/Users/changdali/Desktop/UI/界面示意图/labtools/图 5：Cell Experiment Workspace : 细胞实验工作区.png` | `boundary_reference_only` |
| Reagent Template Editor side panel detail | `docs/ui/mockups/labtools/c1c3_supplemental/reagent_template_editor_side_panel_detail_candidate_20260522.png` | `detail_reference` |
| WB lane/warning detail user replacement | `docs/ui/mockups/labtools/c1c3_supplemental/wb_lane_warning_detail_user_replacement_20260522.png` | `detail_reference` |
| ELISA / Immuno-Absorbance boundary | `docs/ui/mockups/labtools/c1c3_supplemental/elisa_immuno_absorbance_boundary_candidate_20260522.png` | `boundary_reference_only` |
| Image Processing Workspace | `/Users/changdali/Desktop/UI/界面示意图/labtools/通用图像处理工作台.png` | `boundary_reference_only` |
| Analysis Function Templates | `/Users/changdali/Desktop/UI/界面示意图/labtools/“多个实验类型参数模板”细节图.png` | `detail_reference` |
| Generated WB lane/warning original | `/Users/changdali/.codex/generated_images/019e4449-f0b7-7a72-8a5c-039c69f041a4/ig_06b08bc0e69611fb016a0fd47e2e248191b0a482c148b6f8c4.png` | `superseded` |

All reviewed image paths passed PNG path checks.

## 4. UI-C2 First Batch

These pages can enter UI-C2a implementation planning first, after preserving the boundary revisions listed below:

| Page | Status | Required Pre-Implementation Notes |
| --- | --- | --- |
| LabTools Home | `implementation_reference_with_text_revision` | Revise overclaim copy and add homepage review notice. Keep exactly three first-level entries. |
| Quick Calculator + Dynamic Formula Solver | `implementation_reference` | Keep General Calculator limited to calculator/formula helpers. Save history and export remain adapter-needed/disabled. |
| Reagent Template / Preparation Workflow | `implementation_reference_with_text_revision` | Save-template and save-preparation actions must stay disabled/adapter-needed until storage adapter exists. |
| Reagent Template Editor side panel detail | `detail_reference` | Use for validation, dirty-state, and disabled-save implementation detail. Do not imply version management. |

First-batch implementation must not add inventory, cloud template library, production batch release, or real persistence without `BioMedPilotLabToolsStorageAdapter`.

## 5. UI-C2 Second Batch

These pages can enter UI-C2 planning after first-batch shell and adapter planning:

| Page | Status | Required Pre-Implementation Notes |
| --- | --- | --- |
| Western Blot Loading focused page | `implementation_reference` | Implement WB loading only. Downstream protein workflow steps remain placeholders. |
| WB lane/warning detail | `detail_reference` | Use the user replacement image, not the superseded generated WB image. Preserve S3 warning and schematic lane layout. |
| SDS-PAGE | `later subpage / workflow placeholder` | SDS-PAGE appears in protein workflow but should be a later subpage, not active in WB focused implementation. |
| BCA / OD MVP Boundary | `boundary_reference_only` | Can inform MVP boundary screen, but formal save/export waits for record/export store. |

Second-batch implementation must not show fake gel bands, image analysis, automatic band recognition, antibody recommendations, active export, ELISA, 4PL, or formal reports.

## 6. Boundary / Shell-Only Pages

These references must remain boundary-only until required backend/adapters exist:

| Page | Boundary Reason | Required Future Capability |
| --- | --- | --- |
| Cell Experiment Workspace | No current UI-branch cell profile/state/record store. | `CellExperimentRecordStore`, cell profile/state models, storage adapter. |
| ELISA / Immuno-Absorbance boundary | ELISA backend not implemented. | ELISA MVP backend, record model, export/report model. |
| Image Processing Workspace | External engine adapter and result model not implemented. | ImageJ/Fiji external engine adapter, image import/store, result review model. |
| Analysis Function Templates | Template/result schema not wired to runtime. | Analysis template model, result field schema, external engine adapter. |

Boundary pages may be used for visual direction and copy structure, but not as proof that the related feature is active.

## 7. Required Adapters And View Models Before Runtime Claims

| Adapter / Model | Needed For | Current Use In Mockups |
| --- | --- | --- |
| `BioMedPilotLabToolsStorageAdapter` | Reagent templates, preparation records, WB records, future cell records. | Required before any save action becomes active. |
| `FilePickerExportAdapter` | WB CSV/Markdown export, SDS-PAGE XLSX export, reagent export, BCA/ELISA export. | Required before export buttons become active. |
| UI-facing error normalization | Calculator/formula/WB/BCA/reagent validation errors. | Required for consistent warning rows and disabled reasons. |
| LabTools result/warning view model | Result preview, review notices, warning rows, impossible volume states. | Required before UI-C2 implementation can safely render runtime results. |
| Disabled / adapter-needed state model | Save/export/run states across LabTools. | Required to prevent visual activation of blocked capabilities. |
| Cell experiment record/profile store | Cell profile, dynamic state, timeline, passage/thaw/freeze/treatment/transfection records. | Required before Cell Experiment moves beyond shell/boundary. |
| ImageJ/Fiji external engine adapter | Image processing workspace and result-processing callouts. | Required before any ImageJ/Fiji detection/run state becomes runtime truth. |
| ELISA MVP backend | ELISA boundary page. | Required before ELISA analysis, 4PL, save, export, or report can be active. |

## 8. Must-Preserve Prohibitions

The following must remain prohibited in UI-C2 unless the specific backend/adapters are implemented and separately approved:

- Do not default write to `~/.labtools`.
- Do not enable unfinished save actions.
- Do not enable unfinished export actions.
- Do not show fake records.
- Do not show fake reports.
- Do not auto-run ImageJ/Fiji.
- Do not expose macro execution.
- Do not show automatic ROI.
- Do not show automatic cell counting.
- Do not show automatic band recognition.
- Do not make ELISA active.
- Do not show fake standard curves, fake ELISA results, or clinical-grade quantification.
- Do not show fake gel bands or completed WB image analysis.
- Do not turn shell-only / adapter-needed / disabled states into active controls.

## 9. Superseded Mockups

The original generated WB lane/warning image is superseded by:

`docs/ui/mockups/labtools/c1c3_supplemental/wb_lane_warning_detail_user_replacement_20260522.png`

Do not use the generated original WB image as implementation reference.

## 10. Implementation Readiness Matrix

Detailed readiness matrix:

`docs/ui/UI_C1c3d_labtools_mockup_implementation_readiness_matrix_20260522.csv`

## 11. UI-C2a Next Task Recommendation

Recommended next task:

`UI-C2a LabTools adapter-first implementation planning`

Scope:

1. Define LabTools UI shell routing and page composition from the accepted mockup set.
2. Establish adapter boundaries before runtime UI implementation:
   - `BioMedPilotLabToolsStorageAdapter`
   - `FilePickerExportAdapter`
   - UI-facing error normalization
   - result/warning view model
   - disabled/adapter-needed state model
3. Implement planning for first-batch pages only:
   - LabTools Home
   - Quick Calculator + Dynamic Formula Solver
   - Reagent Template / Preparation Workflow
4. Keep WB/BCA/Cell/Image Processing/ELISA as second-batch or boundary-only until adapter requirements are met.

Do not begin App icon / Finder icon / packaging work in UI-C2a.

## 12. Verification

| Command | Result |
| --- | --- |
| `file ... reviewed mockup image paths ...` | Passed: all reviewed image paths are PNG files |
| `python3 - <<'PY' ... readiness matrix check ... PY` | Passed: 12 rows, 12 columns, all referenced image paths exist |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
