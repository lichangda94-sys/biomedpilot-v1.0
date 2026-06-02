# UI Route Contract LabTools Batch 2

- Created: `2026-06-02T14:00:52.394935+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `6ffcbe7a650809cbbf25df8842619322d177f83d`
- Scope: LabTools approved home, second-level module list, connected calculators/reagent/cell/WB/image run-request gates.

## Summary

- Rows: 21
- Connected: 18
- Disabled with reason: 3
- Broken: 0

## Approved Structure

- Home primary entries: General Calculators, Reagent Preparation, Experiment Modules.
- Experiment Modules second-level entries: Cell Experiments, Protein Experiments, Nucleic Acid Experiments, Immunoassay & Absorbance, Immunohistochemistry.
- Image analysis is not a primary or second-level module entry; it is a gated workbench inside Cell Experiments and Protein / Western Blot.

## Screenshots

Runtime screenshots for this batch are stored under:

`docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract`

- `01_home` / `home`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/01_home.png`
- `02_general_calculators` / `general_calculators`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/02_general_calculators.png`
- `03_reagent_preparation` / `reagent_preparation`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/03_reagent_preparation.png`
- `04_experiment_modules` / `experiment_modules`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/04_experiment_modules.png`
- `05_cell_experiments` / `cell_experiments`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/05_cell_experiments.png`
- `06_protein_experiments` / `protein_experiments`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/06_protein_experiments.png`
- `07_nucleic_acid_experiments` / `nucleic_acid_experiments`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/07_nucleic_acid_experiments.png`
- `08_immuno_absorbance` / `immuno_absorbance`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/08_immuno_absorbance.png`
- `09_ihc` / `ihc`: `docs/ui/runtime_screenshots/20260602_labtools_batch2_route_contract/09_ihc.png`

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| LABTOOLS-HOME-GENERAL_CALCULATORS | LabTools Home | `labtoolsEntryButton` | connected | `navigates_to_labtools_primary_general_calculators` | current_page_key=general_calculators |
| LABTOOLS-HOME-REAGENT_PREPARATION | LabTools Home | `labtoolsEntryButton` | connected | `navigates_to_labtools_primary_reagent_preparation` | current_page_key=reagent_preparation |
| LABTOOLS-HOME-EXPERIMENT_MODULES | LabTools Home | `labtoolsEntryButton` | connected | `navigates_to_labtools_primary_experiment_modules` | current_page_key=experiment_modules |
| LABTOOLS-SECONDARY-CELL_EXPERIMENTS | LabTools Experiment Modules | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_cell_experiments` | current_page_key=cell_experiments |
| LABTOOLS-SECONDARY-PROTEIN_EXPERIMENTS | LabTools Experiment Modules | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_protein_experiments` | current_page_key=protein_experiments |
| LABTOOLS-SECONDARY-NUCLEIC_ACID_EXPERIMENTS | LabTools Experiment Modules | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_nucleic_acid_experiments` | current_page_key=nucleic_acid_experiments |
| LABTOOLS-SECONDARY-IMMUNO_ABSORBANCE | LabTools Experiment Modules | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_immuno_absorbance` | current_page_key=immuno_absorbance |
| LABTOOLS-SECONDARY-IMMUNO_ABSORBANCE-DISABLED-GATE | 免疫与吸光度实验 | `labToolsC1DisabledActionButton` | disabled | `disabled_labtools_secondary_backend_not_connected` | ELISA/BCA formal records, curve fitting, and report export are not connected in C1. |
| LABTOOLS-SECONDARY-IHC | LabTools Experiment Modules | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_ihc` | current_page_key=ihc |
| LABTOOLS-SECONDARY-IHC-DISABLED-GATE | 免疫组化 | `labToolsC1DisabledActionButton` | disabled | `disabled_labtools_secondary_backend_not_connected` | IHC record model, review workflow, and Settings-linked image assistance are not connected in C1. |
| LABTOOLS-HEADER-HOME | LabTools Header | `labToolsHomeButton` | connected | `navigates_to_labtools_home` | current_page_key=home |
| LABTOOLS-CALCULATOR-DILUTION-RUN | General Calculators | `primaryButton` | connected | `calls_dilution_calculator` | result_panel_contains_stock_volume; copy_button_enabled=True |
| LABTOOLS-REAGENT-TEMPLATE-SAVE | Reagent Preparation | `reagentTemplateSaveButton` | connected | `upserts_reagent_template_local_json` | reagent_templates.json exists; template_count=1 |
| LABTOOLS-REAGENT-PREPARATION-CALCULATE | Reagent Preparation | `preparationCalculateButton` | connected | `generates_reagent_preparation_preview_without_record_write` | preview_contains_template_and_component; no preparation_records.json |
| LABTOOLS-CELL-PROFILE-SAVE | Cell Experiments | `cellProfileSaveButton` | connected | `upserts_cell_profile_store` | cell_profiles.json exists; profile_count=1 |
| LABTOOLS-CELL-FREEZING-BATCH-CREATE | Cell Experiments | `freezingBatchCreateButton` | connected | `creates_freezing_batch_and_cryovial_inventory` | cell_inventory.json exists; cryovial_count>=1 |
| LABTOOLS-CELL-SEEDING-CALCULATE | Cell Experiments | `seedingCalculationButton` | connected | `calculates_cell_seeding_preparation_preview` | seedingCalculationResult QLabel |
| LABTOOLS-WB-PROTEIN-LOADING-CALCULATE | Protein / Western Blot | `proteinLoadingCalculateButton` | connected | `calculates_protein_loading_plan` | proteinLoadingResultPanel; copy_button_enabled=True |
| LABTOOLS-WB-ROI-RUN-REQUEST | Protein / Western Blot | `wbMeasureRoiButton` | connected | `creates_wb_roi_run_request_without_running_engine` | wb_roi run_request.json exists; wb_rois.csv exists |
| LABTOOLS-WB-ROI-PREPROCESS-GATE | Protein / Western Blot | `wbPreprocessButton` | disabled | `disabled_external_engine_missing` | 图像分析引擎未准备好。请在外部引擎设置中完成 ImageJ/ImageJ-Fiji 配置。当前页面仍可用于导入图片、绘制 ROI、保存任务和准备分析参数。 |
| LABTOOLS-CELL-IMAGE-RUN-REQUEST | Cell Image Analysis | `imageWorkbenchPrimaryActionButton` | connected | `creates_image_analysis_run_request_without_running_engine` | cell_image run_request.json exists; task.status=run_request_created |
