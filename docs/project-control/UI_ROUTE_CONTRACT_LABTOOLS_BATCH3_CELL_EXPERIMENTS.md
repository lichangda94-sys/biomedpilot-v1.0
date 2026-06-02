# UI Route Contract LabTools Batch 3: Cell Experiments

- Created: `2026-06-02T13:33:45.561132+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `fa4871dee1258d7006169cd21b77d38161c2e1a7`
- Scope: LabTools Cell Experiments deep live-click contract for profile, inventory, record templates, and cell image-analysis run-request gates.

## Summary

- Rows: 44
- Connected: 38
- Disabled with reason: 6
- Broken: 0

## Screenshots

- `01_cell_experiments_overview`: `docs/ui/runtime_screenshots/20260602_labtools_batch3_cell_experiments/01_cell_experiments_overview.png`
- `02_cell_record_tabs`: `docs/ui/runtime_screenshots/20260602_labtools_batch3_cell_experiments/02_cell_record_tabs.png`
- `03_cell_image_analysis_tabs`: `docs/ui/runtime_screenshots/20260602_labtools_batch3_cell_experiments/03_cell_image_analysis_tabs.png`
- `04_cell_record_after_save`: `docs/ui/runtime_screenshots/20260602_labtools_batch3_cell_experiments/04_cell_record_after_save.png`

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| `LABTOOLS-CELL-VISUAL-cellExperimentCreateFromLastDisabledButton` | Cell Experiments Visual Summary | `cellExperimentCreateFromLastDisabledButton` | disabled | `disabled_requires_saved_cell_record_history` | Requires saved cell experiment history; connected from-last actions are available in backend record tabs once records exist. |
| `LABTOOLS-CELL-VISUAL-cellExperimentSettingsRouteDisabledButton` | Cell Image Analysis Visual Summary | `cellExperimentSettingsRouteDisabledButton` | disabled | `disabled_settings_route_available_from_shell_sidebar` | Settings is reachable from the shell sidebar; this LabTools summary-card shortcut is intentionally not wired. |
| `LABTOOLS-CELL-VISUAL-cellExperimentRunImageAnalysisDisabledButton` | Cell Image Analysis Visual Summary | `cellExperimentRunImageAnalysisDisabledButton` | disabled | `disabled_image_engine_execution_gated_creates_run_request_only` | Cell image analysis execution is gated; current workbenches generate run request artifacts but do not run ImageJ/Fiji macros. |
| `LABTOOLS-CELL-PROFILE-SAVE` | Cell Profile | `cellProfileSaveButton` | connected | `upserts_cell_profile_store` | cell_profiles.json; profile_count=1 |
| `LABTOOLS-CELL-PROFILE-COPY` | Cell Profile | `cellProfileCopyButton` | connected | `copies_selected_cell_profile_store` | cell_profiles.json; profile_count=2 |
| `LABTOOLS-CELL-PROFILE-EXPORT` | Cell Profile | `cellProfileExportButton` | connected | `exports_selected_cell_profile_txt` | profile_export_status_present=True |
| `LABTOOLS-CELL-PROFILE-NEW` | Cell Profile | `cellProfileNewButton` | connected | `clears_cell_profile_form` | cell_name_field_empty=True; profile_count=2 |
| `LABTOOLS-CELL-FREEZING-BATCH-CREATE` | Cell Freezing Inventory | `freezingBatchCreateButton` | connected | `creates_freezing_batch_and_cryovial_inventory` | cell_inventory.json; cryovial_count=2 |
| `LABTOOLS-CELL-CRYOVIAL-UPDATE` | Cell Freezing Inventory | `cryovialUpdateButton` | connected | `updates_cryovial_location_and_status` | status=已转移; box_position=A2 |
| `LABTOOLS-CELL-RECORD-THAW-SAVE` | Cell Record Template / 细胞复苏记录 | `cellRecordSaveButton_thaw` | connected | `saves_cell_experiment_record` | cell_records.json; before=0; after=1 |
| `LABTOOLS-CELL-RECORD-THAW-EXPORT` | Cell Record Template / 细胞复苏记录 | `cellRecordExportButton_thaw` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-THAW-COPY` | Cell Record Template / 细胞复苏记录 | `cellRecordCopyButton_thaw` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-THAW-FROM-LAST` | Cell Record Template / 细胞复苏记录 | `cellRecordFromLastButton_thaw` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-RECORD-PASSAGE-SAVE` | Cell Record Template / 细胞传代记录 | `cellRecordSaveButton_passage` | connected | `saves_cell_experiment_record` | cell_records.json; before=1; after=2 |
| `LABTOOLS-CELL-RECORD-PASSAGE-EXPORT` | Cell Record Template / 细胞传代记录 | `cellRecordExportButton_passage` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-PASSAGE-COPY` | Cell Record Template / 细胞传代记录 | `cellRecordCopyButton_passage` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-PASSAGE-FROM-LAST` | Cell Record Template / 细胞传代记录 | `cellRecordFromLastButton_passage` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-RECORD-SEEDING-SAVE` | Cell Record Template / 细胞接种 / 铺板记录 | `cellRecordSaveButton_seeding` | connected | `saves_cell_experiment_record` | cell_records.json; before=2; after=3 |
| `LABTOOLS-CELL-RECORD-SEEDING-EXPORT` | Cell Record Template / 细胞接种 / 铺板记录 | `cellRecordExportButton_seeding` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-SEEDING-COPY` | Cell Record Template / 细胞接种 / 铺板记录 | `cellRecordCopyButton_seeding` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-SEEDING-FROM-LAST` | Cell Record Template / 细胞接种 / 铺板记录 | `cellRecordFromLastButton_seeding` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-RECORD-FREEZING-SAVE` | Cell Record Template / 细胞冻存记录 | `cellRecordSaveButton_freezing` | connected | `saves_cell_experiment_record` | cell_records.json; before=3; after=4 |
| `LABTOOLS-CELL-RECORD-FREEZING-EXPORT` | Cell Record Template / 细胞冻存记录 | `cellRecordExportButton_freezing` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-FREEZING-COPY` | Cell Record Template / 细胞冻存记录 | `cellRecordCopyButton_freezing` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-FREEZING-FROM-LAST` | Cell Record Template / 细胞冻存记录 | `cellRecordFromLastButton_freezing` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-RECORD-TREATMENT-SAVE` | Cell Record Template / 给药 / 处理记录 | `cellRecordSaveButton_treatment` | connected | `saves_cell_experiment_record` | cell_records.json; before=4; after=5 |
| `LABTOOLS-CELL-RECORD-TREATMENT-EXPORT` | Cell Record Template / 给药 / 处理记录 | `cellRecordExportButton_treatment` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-TREATMENT-COPY` | Cell Record Template / 给药 / 处理记录 | `cellRecordCopyButton_treatment` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-TREATMENT-FROM-LAST` | Cell Record Template / 给药 / 处理记录 | `cellRecordFromLastButton_treatment` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-RECORD-TRANSFECTION-SAVE` | Cell Record Template / 转染记录 | `cellRecordSaveButton_transfection` | connected | `saves_cell_experiment_record` | cell_records.json; before=5; after=6 |
| `LABTOOLS-CELL-RECORD-TRANSFECTION-EXPORT` | Cell Record Template / 转染记录 | `cellRecordExportButton_transfection` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-TRANSFECTION-COPY` | Cell Record Template / 转染记录 | `cellRecordCopyButton_transfection` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-TRANSFECTION-FROM-LAST` | Cell Record Template / 转染记录 | `cellRecordFromLastButton_transfection` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-RECORD-OTHER-SAVE` | Cell Record Template / 其他处理记录 | `cellRecordSaveButton_other` | connected | `saves_cell_experiment_record` | cell_records.json; before=6; after=7 |
| `LABTOOLS-CELL-RECORD-OTHER-EXPORT` | Cell Record Template / 其他处理记录 | `cellRecordExportButton_other` | connected | `exports_cell_experiment_record_txt` | record_export_status_present=True |
| `LABTOOLS-CELL-RECORD-OTHER-COPY` | Cell Record Template / 其他处理记录 | `cellRecordCopyButton_other` | connected | `copies_current_cell_record_draft` | 已复制当前记录为草稿。 |
| `LABTOOLS-CELL-RECORD-OTHER-FROM-LAST` | Cell Record Template / 其他处理记录 | `cellRecordFromLastButton_other` | connected | `creates_draft_from_last_cell_record` | 已从上次记录创建草稿。 |
| `LABTOOLS-CELL-SEEDING-CALCULATE` | Cell Record Template / Seeding | `seedingCalculationButton` | connected | `calculates_cell_seeding_preparation_preview` | 总目标细胞数 264000；建议总配制体积 13.2 mL；需要细胞悬液体积 0.264 mL；需要培养基体积 12.936 mL |
| `LABTOOLS-CELL-IMAGE-scratch_area-RUN-REQUEST` | Cell Image Analysis / 划痕实验图像分析 | `imageWorkbenchPrimaryActionButton` | connected | `creates_image_analysis_run_request_without_running_engine` | run_request.json exists; task.status=run_request_created |
| `LABTOOLS-CELL-IMAGE-scratch_area-EXPORT-GATE` | Cell Image Analysis / 划痕实验图像分析 | `imageWorkbenchExportPlaceholderButton` | disabled | `disabled_missing_real_image_analysis_result` | 当前页面只生成 run request；尚未产生真实图像分析结果，不能导出正式结果。 |
| `LABTOOLS-CELL-IMAGE-transwell_count-RUN-REQUEST` | Cell Image Analysis / Transwell 图像分析 | `imageWorkbenchPrimaryActionButton` | connected | `creates_image_analysis_run_request_without_running_engine` | run_request.json exists; task.status=run_request_created |
| `LABTOOLS-CELL-IMAGE-transwell_count-EXPORT-GATE` | Cell Image Analysis / Transwell 图像分析 | `imageWorkbenchExportPlaceholderButton` | disabled | `disabled_missing_real_image_analysis_result` | 当前页面只生成 run request；尚未产生真实图像分析结果，不能导出正式结果。 |
| `LABTOOLS-CELL-IMAGE-fluorescence_intensity-RUN-REQUEST` | Cell Image Analysis / 荧光 / 染色图像分析 | `imageWorkbenchPrimaryActionButton` | connected | `creates_image_analysis_run_request_without_running_engine` | run_request.json exists; task.status=run_request_created |
| `LABTOOLS-CELL-IMAGE-fluorescence_intensity-EXPORT-GATE` | Cell Image Analysis / 荧光 / 染色图像分析 | `imageWorkbenchExportPlaceholderButton` | disabled | `disabled_missing_real_image_analysis_result` | 当前页面只生成 run request；尚未产生真实图像分析结果，不能导出正式结果。 |
