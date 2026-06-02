# UI Route Contract LabTools Batch 4: Protein / Western Blot

- Created: `2026-06-02T14:18:18+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `13128f797492631045373d8a21437d47d658eda3`
- Scope: LabTools Protein / Western Blot deep live-click contract for BCA, protein loading, SDS-PAGE, workflow records, and WB ROI/result gates.

## Summary

- Rows: 83
- Connected: 82
- Disabled with reason: 1
- Broken: 0

## Screenshots

- `01_protein_wb_overview`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/01_protein_wb_overview.png`
- `02_bca_results`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/02_bca_results.png`
- `03_protein_loading_records`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/03_protein_loading_records.png`
- `04_sds_page_lane_layout`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/04_sds_page_lane_layout.png`
- `05_workflow_record`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/05_workflow_record.png`
- `06_wb_roi_analysis`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch4_protein_wb/06_wb_roi_analysis.png`

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| `LABTOOLS-WB-TAB-openBcaAssayToolButton` | Protein / Western Blot | `openBcaAssayToolButton` | connected | `opens_bca_assay_tab` | current_tab=BCA 蛋白浓度测定 |
| `LABTOOLS-WB-TAB-openProteinLoadingToolButton` | Protein / Western Blot | `openProteinLoadingToolButton` | connected | `opens_protein_loading_tab` | current_tab=蛋白上样计算 |
| `LABTOOLS-WB-TAB-openSdsPageGelToolButton` | Protein / Western Blot | `openSdsPageGelToolButton` | connected | `opens_sds_page_gel_lane_layout_tab` | current_tab=配胶与 Lane 布局 |
| `LABTOOLS-WB-LOADING-ADD-SAMPLE` | Protein Loading | `proteinLoadingAddSampleRowButton` | connected | `adds_protein_loading_sample_row` | row_count=3 |
| `LABTOOLS-WB-LOADING-CALCULATE` | Protein Loading | `proteinLoadingCalculateButton` | connected | `calculates_protein_loading_plan` | proteinLoadingResultPanel; copy_enabled=True |
| `LABTOOLS-WB-LOADING-proteinLoadingCopyResultButton` | Protein Loading | `proteinLoadingCopyResultButton` | connected | `copies_protein_loading_markdown_when_available` | WB loading Western Blot 上样计算器 / Western Blot 上样体系辅助计算草稿 / 目标上样蛋白量：20 µg / lane / 目标终体积：20 µL / lane / 4X loading buffer：5 µL / lane / 总 loading buffer 体积：10 µL /  / 纵向计算明细表 / 样本	浓度(µg/µL)	目标蛋白(µg)	样本体积(µL)	Loading buffer(µL)	还原剂(µL)	补足液(µL)	终体积(µL)	状态 / S1	2	20	10	5	0	5	20	OK / S2	4	20	5	5	0	10	20	OK /  / 横向 lane layout / 项目	Lane 1	Lane 2	Lane 3 / 类型	Marker	Sample	Sample / 样本	Protein Marker	S1	S2 / 样本体积	5 µL	10 µL	5 µL / 4X loading buffer	-	5 µL	5 µL / 还原剂	-	0 µL	0 µL / ddH2O	-	5 µL	10 µL / 状态	M |
| `LABTOOLS-WB-LOADING-wbLoadingSaveRecordButton` | Protein Loading | `wbLoadingSaveRecordButton` | connected | `persists_protein_loading_record_json_after_calculation` | 1 |
| `LABTOOLS-WB-LOADING-wbLoadingCopyMarkdownButton` | Protein Loading | `wbLoadingCopyMarkdownButton` | connected | `copies_protein_loading_record_markdown_after_calculation` | # Western Blot 上样记录 /  / 实验名称：WB loading / 创建时间：2026-06-02T14:18:18Z / 目标蛋白量：20 µg/lane / 目标终体积：20 µL/lane / Loading buffer：4X / 还原剂：none / 补足液：ddH2O / Marker：Protein Marker, 5 µL / 状态：OK /  / ## 样本计算明细 /  / | 样本 | 浓度 (µg/µL) | 样本体积 (µL) | Loading buffer (µL) | 还原剂 (µL) | ddH2O (µL) | 状态 | / |---|---:|---:|---:|---:|---:|---| / | S1 | 2 | 10 | 5 | 0 | 5 | OK | / | S2 | 4 | 5 | 5 | 0 | 10 | OK | /  / ## 横向 Lane Layout /  / | 项目 | Lane 1 | Lane 2 | Lane 3 | / |---|---|---|---| / | 类型 | Marker | Sa |
| `LABTOOLS-WB-LOADING-wbLoadingExportMarkdownButton` | Protein Loading | `wbLoadingExportMarkdownButton` | connected | `exports_protein_loading_record_markdown_after_calculation` | True |
| `LABTOOLS-WB-LOADING-wbLoadingExportCsvButton` | Protein Loading | `wbLoadingExportCsvButton` | connected | `exports_protein_loading_record_csv_after_calculation` | True |
| `LABTOOLS-WB-LOADING-wbLoadingRefreshRecordHistoryButton` | Protein Loading | `wbLoadingRefreshRecordHistoryButton` | connected | `reloads_protein_loading_record_history` | 1 |
| `LABTOOLS-WB-LOADING-wbLoadingViewRecordButton` | Protein Loading | `wbLoadingViewRecordButton` | connected | `loads_selected_protein_loading_record_into_result_panels` | 已载入记录：wb_loading_0e22b72097fb477aaf65807743ac7b85 |
| `LABTOOLS-WB-LOADING-wbLoadingDeleteRecordButton` | Protein Loading | `wbLoadingDeleteRecordButton` | connected | `deletes_selected_protein_loading_record_after_confirmation` | 记录已删除。本地 JSON 已更新。 |
| `LABTOOLS-WB-BCA-PARSE-MATRIX` | BCA | `bcaParseOdMatrixButton` | connected | `parses_bca_od_matrix_into_plate_table` | OD 矩阵已解析。 /  |
| `LABTOOLS-WB-BCA-APPLY-RANGE-0` | BCA | `bcaApplyBatchAnnotationButton` | connected | `applies_bca_annotation_to_well_range` | 已批量标注选区：A1 - A2 |
| `LABTOOLS-WB-BCA-APPLY-RANGE-1` | BCA | `bcaApplyBatchAnnotationButton` | connected | `applies_bca_annotation_to_well_range` | 已批量标注选区：A3 - A4 |
| `LABTOOLS-WB-BCA-APPLY-RANGE-2` | BCA | `bcaApplyBatchAnnotationButton` | connected | `applies_bca_annotation_to_well_range` | 已批量标注选区：A5 - A6 |
| `LABTOOLS-WB-BCA-APPLY-RANGE-3` | BCA | `bcaApplyBatchAnnotationButton` | connected | `applies_bca_annotation_to_well_range` | 已批量标注选区：A7 - A8 |
| `LABTOOLS-WB-BCA-bcaSetBlankButton` | BCA | `bcaSetBlankButton` | connected | `marks_selected_bca_wells_as_blank` | 已标注孔位：A1 |
| `LABTOOLS-WB-BCA-bcaSetStandardButton` | BCA | `bcaSetStandardButton` | connected | `marks_selected_bca_wells_as_standard` | 已标注孔位：A1 |
| `LABTOOLS-WB-BCA-bcaSetSampleButton` | BCA | `bcaSetSampleButton` | connected | `marks_selected_bca_wells_as_sample` | 已标注孔位：A1 |
| `LABTOOLS-WB-BCA-bcaSetUnusedButton` | BCA | `bcaSetUnusedButton` | connected | `marks_selected_bca_wells_as_unused` | 已标注孔位：A1 |
| `LABTOOLS-WB-BCA-bcaApplySelectedAnnotationButton` | BCA | `bcaApplySelectedAnnotationButton` | connected | `applies_bca_annotation_to_selected_wells` | 已标注孔位：A1 |
| `LABTOOLS-WB-BCA-CALCULATE` | BCA | `bcaCalculateButton` | connected | `calculates_bca_standard_curve_and_sample_concentrations` | Sample Results / Sample 1	A7, A8	稀释倍数 2	mean 0.4	SD 0.0	CV% 0.0	测定孔浓度 150.00000000000003	稀释修正后原始样本浓度 300.00000000000006 µg/mL	超出标准曲线范围 False		备注  / 结果为 BCA 蛋白浓度测定辅助计算草稿。使用前请结合试剂盒说明书、标准曲线质量、重复孔一致性和实验室 SOP 人工核对。 |
| `LABTOOLS-WB-BCA-COPY` | BCA | `bcaCopyResultButton` | connected | `copies_bca_result_text_after_calculation` | BCA 蛋白浓度测定辅助计算摘要 / Blank 扣除：未启用 / Blank 平均 OD：无 / 标准曲线公式：OD = 0.002 × concentration + 0.1 / R²：1 /  / 样本结果： / - Sample 1: 孔位 A7, A8; 稀释倍数 2; 平均 OD 0.4; 测定孔浓度 150 µg/mL; 稀释修正后原始样本浓度 300 µg/mL /  / 警告列表： / - 未标注 Blank；可考虑使用 0 浓度标准作为 blank，但不会自动扣除 /  / 结果为 BCA 蛋白浓度测定辅助计算草稿。使用前请结合试剂盒说明书、标准曲线质量、重复孔一致性和实验室 SOP 人工核对。 |
| `LABTOOLS-WB-SDS-BLANK-LANE-LAYOUT` | SDS-PAGE | `refreshBlankLaneLayoutButton` | connected | `generates_blank_sds_page_lane_layout` | lane_rows=10 |
| `LABTOOLS-WB-SDS-IMPORT-LOADING-LANES` | SDS-PAGE | `importLoadingLaneLayoutButton` | connected | `imports_latest_protein_loading_lane_layout_or_generates_blank_layout` | Protein Marker;S1;S2 |
| `LABTOOLS-WB-SDS-CALCULATE` | SDS-PAGE | `primaryButton` | connected | `calculates_sds_page_gel_batch_from_user_template` | 配胶摘要 / 基于用户录入的试剂盒/实验室模板进行批量换算 / 请先核对 SOP、试剂纯度、pH、温度和安全要求。 / 模板名称：Audit 10% gel / 胶数量：2 / 余量百分比：3.0% /  / Lane 布局摘要 / Lane 编号	样品名	总上样体积 / Lane 1	Protein Marker	5 µL / Lane 2	S1	20 µL / Lane 3	S2	20 µL /  / 总量含余量： / Resolving gel 组分表 / - Acrylamide mix: 5.15 mL（每块胶 2.5 mL; 备注：） / Stacking gel 组分表 / - Stacking buffer: 2.06 mL（每块胶 1 mL; 备注：） |
| `LABTOOLS-WB-SDS-sdsPageTemplateJsonExportButton` | SDS-PAGE | `sdsPageTemplateJsonExportButton` | connected | `exports_sds_page_template_json_after_calculation` | <audit_root>/exports/sds_page_template.json |
| `LABTOOLS-WB-SDS-sdsPageXlsxExportButton` | SDS-PAGE | `sdsPageXlsxExportButton` | connected | `exports_sds_page_gel_calculation_xlsx_after_calculation` | <audit_root>/exports/sds_page_calculation.xlsx |
| `LABTOOLS-WB-SDS-IMPORT-JSON` | SDS-PAGE | `sdsPageTemplateJsonImportButton` | connected | `imports_sds_page_template_json_with_conflict_policy` | 导入前预览完成：Audit 10% gel / 导入成功 / 使用前仍需人工核对。 |
| `LABTOOLS-WB-RECORD-sample_preparation-wbRecordSaveButton_sample_preparation` | WB Workflow Records | `wbRecordSaveButton_sample_preparation` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_07e5e6b887b148059d5e392fba5d6fbf |
| `LABTOOLS-WB-RECORD-sample_preparation-wbRecordSaveSopTemplateButton_sample_preparation` | WB Workflow Records | `wbRecordSaveSopTemplateButton_sample_preparation` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_6084df5c1c404058b120e2e9c97976fc |
| `LABTOOLS-WB-RECORD-sample_preparation-wbRecordLoadLastButton_sample_preparation` | WB Workflow Records | `wbRecordLoadLastButton_sample_preparation` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_07e5e6b887b148059d5e392fba5d6fbf |
| `LABTOOLS-WB-RECORD-sample_preparation-wbRecordExportTextButton_sample_preparation` | WB Workflow Records | `wbRecordExportTextButton_sample_preparation` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/sample_preparation_workflow_record.txt |
| `LABTOOLS-WB-RECORD-electrophoresis-wbRecordSaveButton_electrophoresis` | WB Workflow Records | `wbRecordSaveButton_electrophoresis` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_f8a01d7a4ca7413bb979d4fde83f221a |
| `LABTOOLS-WB-RECORD-electrophoresis-wbRecordSaveSopTemplateButton_electrophoresis` | WB Workflow Records | `wbRecordSaveSopTemplateButton_electrophoresis` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_b41d236534df411484353aa2e12b5ad0 |
| `LABTOOLS-WB-RECORD-electrophoresis-wbRecordLoadLastButton_electrophoresis` | WB Workflow Records | `wbRecordLoadLastButton_electrophoresis` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_f8a01d7a4ca7413bb979d4fde83f221a |
| `LABTOOLS-WB-RECORD-electrophoresis-wbRecordExportTextButton_electrophoresis` | WB Workflow Records | `wbRecordExportTextButton_electrophoresis` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/electrophoresis_workflow_record.txt |
| `LABTOOLS-WB-RECORD-transfer-wbRecordSaveButton_transfer` | WB Workflow Records | `wbRecordSaveButton_transfer` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_ab6ee7b73aeb48bc97e1eda092018558 |
| `LABTOOLS-WB-RECORD-transfer-wbRecordSaveSopTemplateButton_transfer` | WB Workflow Records | `wbRecordSaveSopTemplateButton_transfer` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_c881ca7923784172be331ca46c2c12f1 |
| `LABTOOLS-WB-RECORD-transfer-wbRecordLoadLastButton_transfer` | WB Workflow Records | `wbRecordLoadLastButton_transfer` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_ab6ee7b73aeb48bc97e1eda092018558 |
| `LABTOOLS-WB-RECORD-transfer-wbRecordExportTextButton_transfer` | WB Workflow Records | `wbRecordExportTextButton_transfer` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/transfer_workflow_record.txt |
| `LABTOOLS-WB-RECORD-blocking-wbRecordSaveButton_blocking` | WB Workflow Records | `wbRecordSaveButton_blocking` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_d53f193b3b6b4e1fa9557569c2971a50 |
| `LABTOOLS-WB-RECORD-blocking-wbRecordSaveSopTemplateButton_blocking` | WB Workflow Records | `wbRecordSaveSopTemplateButton_blocking` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_4bc8eb81b9804fd28e373d1a34fc4dc3 |
| `LABTOOLS-WB-RECORD-blocking-wbRecordLoadLastButton_blocking` | WB Workflow Records | `wbRecordLoadLastButton_blocking` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_d53f193b3b6b4e1fa9557569c2971a50 |
| `LABTOOLS-WB-RECORD-blocking-wbRecordExportTextButton_blocking` | WB Workflow Records | `wbRecordExportTextButton_blocking` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/blocking_workflow_record.txt |
| `LABTOOLS-WB-RECORD-primary_antibody-wbRecordSaveButton_primary_antibody` | WB Workflow Records | `wbRecordSaveButton_primary_antibody` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_42bca8ad58b54084a5baafccf3cf1377 |
| `LABTOOLS-WB-RECORD-primary_antibody-wbRecordSaveSopTemplateButton_primary_antibody` | WB Workflow Records | `wbRecordSaveSopTemplateButton_primary_antibody` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_4a43fd2a46ce4c5299ce7c9d3577f39a |
| `LABTOOLS-WB-RECORD-primary_antibody-wbRecordLoadLastButton_primary_antibody` | WB Workflow Records | `wbRecordLoadLastButton_primary_antibody` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_42bca8ad58b54084a5baafccf3cf1377 |
| `LABTOOLS-WB-RECORD-primary_antibody-wbRecordExportTextButton_primary_antibody` | WB Workflow Records | `wbRecordExportTextButton_primary_antibody` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/primary_antibody_workflow_record.txt |
| `LABTOOLS-WB-RECORD-primary_wash-wbRecordSaveButton_primary_wash` | WB Workflow Records | `wbRecordSaveButton_primary_wash` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_9706de4664cd4b0bb45690ea767bdb0c |
| `LABTOOLS-WB-RECORD-primary_wash-wbRecordSaveSopTemplateButton_primary_wash` | WB Workflow Records | `wbRecordSaveSopTemplateButton_primary_wash` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_8ce0e26113914d1c850b435505e871ca |
| `LABTOOLS-WB-RECORD-primary_wash-wbRecordLoadLastButton_primary_wash` | WB Workflow Records | `wbRecordLoadLastButton_primary_wash` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_9706de4664cd4b0bb45690ea767bdb0c |
| `LABTOOLS-WB-RECORD-primary_wash-wbRecordExportTextButton_primary_wash` | WB Workflow Records | `wbRecordExportTextButton_primary_wash` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/primary_wash_workflow_record.txt |
| `LABTOOLS-WB-RECORD-secondary_antibody-wbRecordSaveButton_secondary_antibody` | WB Workflow Records | `wbRecordSaveButton_secondary_antibody` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_68a7a565f268472ea8a43cee763dbe42 |
| `LABTOOLS-WB-RECORD-secondary_antibody-wbRecordSaveSopTemplateButton_secondary_antibody` | WB Workflow Records | `wbRecordSaveSopTemplateButton_secondary_antibody` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_3598e4c473324e9895d681077f8c6ade |
| `LABTOOLS-WB-RECORD-secondary_antibody-wbRecordLoadLastButton_secondary_antibody` | WB Workflow Records | `wbRecordLoadLastButton_secondary_antibody` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_68a7a565f268472ea8a43cee763dbe42 |
| `LABTOOLS-WB-RECORD-secondary_antibody-wbRecordExportTextButton_secondary_antibody` | WB Workflow Records | `wbRecordExportTextButton_secondary_antibody` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/secondary_antibody_workflow_record.txt |
| `LABTOOLS-WB-RECORD-secondary_wash-wbRecordSaveButton_secondary_wash` | WB Workflow Records | `wbRecordSaveButton_secondary_wash` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_756ec446c3f5421c947b0b6eb2d7c2a7 |
| `LABTOOLS-WB-RECORD-secondary_wash-wbRecordSaveSopTemplateButton_secondary_wash` | WB Workflow Records | `wbRecordSaveSopTemplateButton_secondary_wash` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_dc112a116d77421b9a37f9912743aa10 |
| `LABTOOLS-WB-RECORD-secondary_wash-wbRecordLoadLastButton_secondary_wash` | WB Workflow Records | `wbRecordLoadLastButton_secondary_wash` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_756ec446c3f5421c947b0b6eb2d7c2a7 |
| `LABTOOLS-WB-RECORD-secondary_wash-wbRecordExportTextButton_secondary_wash` | WB Workflow Records | `wbRecordExportTextButton_secondary_wash` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/secondary_wash_workflow_record.txt |
| `LABTOOLS-WB-RECORD-imaging-wbRecordSaveButton_imaging` | WB Workflow Records | `wbRecordSaveButton_imaging` | connected | `persists_western_blot_workflow_record_json` | 已保存：wb_workflow_31324fe636c6429f8b8ab36c48ccde6f |
| `LABTOOLS-WB-RECORD-imaging-wbRecordSaveSopTemplateButton_imaging` | WB Workflow Records | `wbRecordSaveSopTemplateButton_imaging` | connected | `persists_western_blot_workflow_sop_template_record` | 已保存：wb_workflow_c7e5b85f4b28404b869d10c2504aa034 |
| `LABTOOLS-WB-RECORD-imaging-wbRecordLoadLastButton_imaging` | WB Workflow Records | `wbRecordLoadLastButton_imaging` | connected | `loads_latest_western_blot_workflow_record_for_step` | 已载入：wb_workflow_31324fe636c6429f8b8ab36c48ccde6f |
| `LABTOOLS-WB-RECORD-imaging-wbRecordExportTextButton_imaging` | WB Workflow Records | `wbRecordExportTextButton_imaging` | connected | `exports_western_blot_workflow_record_text` | 已导出文本：<audit_root>/imaging_workflow_record.txt |
| `LABTOOLS-WB-ROI-IMPORT-IMAGE` | WB ROI Analysis | `wbImageImportButton` | connected | `loads_local_wb_image_preview` | 图片文件名：wb_preview.png；文件格式：.png；是否可读取：已记录；原始路径：<audit_root>/wb_preview.png |
| `LABTOOLS-WB-ROI-PREPROCESS-GATE` | WB ROI Analysis | `wbPreprocessButton` | disabled | `disabled_external_engine_missing` | 图像分析引擎未准备好。请在外部引擎设置中完成 ImageJ/ImageJ-Fiji 配置。当前页面仍可用于导入图片、绘制 ROI、保存任务和准备分析参数。 |
| `LABTOOLS-WB-ROI-wbCreateRoiButton` | WB ROI Analysis | `wbCreateRoiButton` | connected | `creates_manual_wb_roi` | roi_rows=1 |
| `LABTOOLS-WB-ROI-wbSetFixedRoiSizeButton` | WB ROI Analysis | `wbSetFixedRoiSizeButton` | connected | `stores_fixed_roi_size_from_selected_roi` | roi_rows=1 |
| `LABTOOLS-WB-ROI-wbCopyRoiNextLaneButton` | WB ROI Analysis | `wbCopyRoiNextLaneButton` | connected | `copies_selected_roi_to_next_lane` | roi_rows=2 |
| `LABTOOLS-WB-ROI-wbCopyRoiAllLanesButton` | WB ROI Analysis | `wbCopyRoiAllLanesButton` | connected | `copies_selected_roi_to_all_lanes` | roi_rows=3 |
| `LABTOOLS-WB-ROI-wbUnifyRoiSizeButton` | WB ROI Analysis | `wbUnifyRoiSizeButton` | connected | `normalizes_manual_roi_dimensions` | roi_rows=3 |
| `LABTOOLS-WB-ROI-wbDeleteSelectedRoiButton` | WB ROI Analysis | `wbDeleteSelectedRoiButton` | connected | `deletes_selected_manual_roi` | roi_rows=2 |
| `LABTOOLS-WB-ROI-wbClearRoiButton` | WB ROI Analysis | `wbClearRoiButton` | connected | `clears_manual_roi_collection` | roi_rows=0 |
| `LABTOOLS-WB-ROI-wbSaveRoiButton` | WB ROI Analysis | `wbSaveRoiButton` | connected | `exports_manual_roi_csv_and_json` | <audit_root>/wb_roi_tasks/manual_wb_rois/wb_rois.csv |
| `LABTOOLS-WB-ROI-wbExportRoiButton` | WB ROI Analysis | `wbExportRoiButton` | connected | `exports_manual_roi_csv_and_json` | <audit_root>/wb_roi_tasks/manual_wb_rois/wb_rois.csv |
| `LABTOOLS-WB-ROI-MEASURE-RUN-REQUEST` | WB ROI Analysis | `wbMeasureRoiButton` | connected | `creates_wb_roi_run_request_without_running_engine` | run_request_exists=True |
| `LABTOOLS-WB-ROI-LOAD-MEASUREMENT-CSV` | WB ROI Analysis | `wbLoadMeasurementCsvButton` | connected | `loads_external_measurement_csv` | measurement_rows=3 |
| `LABTOOLS-WB-ROI-wbCalculateTargetControlButton` | WB ROI Analysis | `wbCalculateTargetControlButton` | connected | `calculates_target_control_ratio_from_loaded_measurements` | normalized_rows=1 |
| `LABTOOLS-WB-ROI-wbCalculateTargetTotalButton` | WB ROI Analysis | `wbCalculateTargetTotalButton` | connected | `calculates_target_total_ratio_from_loaded_measurements` | normalized_rows=1 |
| `LABTOOLS-WB-ROI-EXPORT-NORMALIZED` | WB ROI Analysis | `wbExportNormalizedResultsButton` | connected | `exports_wb_normalized_results_csv` | <audit_root>/wb_roi_tasks/manual_wb_rois/wb_normalized_results.csv |
