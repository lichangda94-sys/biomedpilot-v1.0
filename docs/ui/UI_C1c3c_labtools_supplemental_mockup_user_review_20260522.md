# UI-C1c3c LabTools Supplemental Mockup User Review

Date: 2026-05-22

## 1. Scope

This document records the user review results for the UI-C1c3c supplemental LabTools mockup images.

This stage only archives mockup review state and non-runtime mockup images under `docs/ui/mockups/labtools/c1c3_supplemental/`. It does not modify `app/**`, `tests/**`, active `assets/**`, `scripts/**`, or `dist/**`; does not implement UI; does not add backend features; does not execute UI-B10; does not package or run a packaged app.

## 2. Image Archive State

| Figure | Status | Archived Path |
| --- | --- | --- |
| Figure 1 - Reagent side panel detail | Archived generated candidate | `docs/ui/mockups/labtools/c1c3_supplemental/reagent_template_editor_side_panel_detail_candidate_20260522.png` |
| Figure 2 - WB lane/warning detail | User replacement image is authoritative; original generated image is superseded | `user_inline_replacement_image_pending_local_path` |
| Figure 3 - ELISA / Immuno-Absorbance Boundary | Archived generated candidate | `docs/ui/mockups/labtools/c1c3_supplemental/elisa_immuno_absorbance_boundary_candidate_20260522.png` |

Note: Figure 2 was provided inline by the user in the conversation. It is recorded as the authoritative replacement image, but no local filesystem path was available in this turn. Do not use the original generated WB image for implementation reference.

## 3. Figure 1 Review - Reagent Side Panel Detail

Decision: `accepted_with_minor_text_review`

Purpose:

- Can be used as implementation reference for the reagent template editor side panel.

Passed:

- Right-side template editor is an independent panel and the background page is visually de-emphasized.
- Dirty state is visible: `已修改未保存`.
- Status chips are visible: `需存储适配`, `需用户复核`.
- Component validation is present:
  - `Na2HPO4` hydrate-form confirmation.
  - `KH2PO4` missing amount.
- `保存模板` does not strongly imply completed save semantics.
- Storage adapter hint is visible at the bottom.

Implementation cautions:

- `保存模板 - 需存储适配` must remain disabled or adapter-needed in implementation.
- `已修改未保存` can remain, but it must not imply full version management.
- Do not add inventory deduction, cloud template library, or production batch release.

## 4. Figure 2 Review - WB Lane / Warning Detail

Decision: `user_replacement_accepted_pending_local_path`

Purpose:

- The user-provided replacement image should replace the originally generated WB detail image.
- Use it as the authoritative WB lane/warning detail reference once a local file path is available.

Replacement image characteristics captured from user review:

- It focuses on `WB 上样计算`.
- It keeps downstream protein experiment steps as flow placeholders.
- It shows lane layout with sample IDs and sample volumes.
- It shows S3 warning for impossible volume / negative water volume.
- Save/export actions remain locked or adapter-needed.
- It avoids fake gel bands, image analysis, automatic band recognition, and antibody recommendation.

Implementation cautions:

- Treat the lane layout as schematic only.
- Keep `保存 WB 记录 - 需适配`, `导出 CSV / Markdown - 需文件选择器`, and `导出结果摘要 - 暂未开放` disabled.
- Do not infer SDS-PAGE, transfer, antibody incubation, exposure, or result assist as active features from the stepper.

Original generated image:

- `/Users/changdali/.codex/generated_images/019e4449-f0b7-7a72-8a5c-039c69f041a4/ig_06b08bc0e69611fb016a0fd47e2e248191b0a482c148b6f8c4.png`

Original generated image status:

- `superseded_by_user_inline_image`

## 5. Figure 3 Review - ELISA / Immuno-Absorbance Boundary

Decision: `accepted_with_boundary_review`

Purpose:

- Can be used as a separate ELISA boundary page reference.

Passed:

- ELISA has been moved out of Cell Experiment and placed under Immuno / Absorbance.
- `blocked_until_backend`, `后端未完成`, `不生成正式结果`, and `不导出报告` are explicit.
- `运行 ELISA`, `保存记录`, and `导出报告` are disabled.
- The right panel includes a reasonable BCA / OD MVP alternate entry.
- The page clearly states that ELISA does not belong to the Cell Experiment page.

Implementation cautions:

- `4PL` may appear on the page only if it remains disabled / undefined / backend-incomplete.
- Do not implement real ELISA calculation, 4PL fitting, report generation, production save, or export in this stage.
- Do not mix this page back into Cell Experiment.

## 6. Manifest Update

Updated manifest:

- `docs/ui/UI_C1c3c_labtools_supplemental_mockup_manifest_20260522.csv`

Key manifest changes:

- Figure 1 has `accepted_image_path` pointing to the archived docs mockup PNG.
- Figure 2 has `accepted_image_path=user_inline_replacement_image_pending_local_path` and marks the original generated WB image as superseded.
- Figure 3 has `accepted_image_path` pointing to the archived docs mockup PNG.

## 7. Verification

| Command | Result |
| --- | --- |
| `file docs/ui/mockups/labtools/c1c3_supplemental/*.png` | Passed: archived Figure 1 and Figure 3 are PNG files |
| `python3 - <<'PY' ... supplemental manifest check ... PY` | Passed: 3 rows, 14 columns; decisions and replacement state recorded |
| `git diff --check` | Passed |
| `git diff --cached --check` | Passed |
