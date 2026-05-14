# LabTools Tool Logic Audit 1

Date: 2026-05-14

This audit pauses feature work and records the current user logic, result meaning, failure cases, and discussion gates for every LabTools tool surface that is already implemented or visibly planned. It does not add tools, algorithms, formulas, persistence schemas, export formats, or UI features.

## Summary Verdict

Current LabTools behavior is internally consistent at the feature-boundary level: implemented tools are presented as local assistance, draft, or manual-review workflows, and planned tools remain placeholder-only. No reviewed tool should be treated as a final lab conclusion, validated SOP, complete ELN, automated image interpretation, or report-ready scientific result.

The main follow-up is not code remediation. It is user logic confirmation for existing result-generating tools before expanding them further.

## ImageJ/Fiji Backend Direction Update

Current image-related behavior remains internally consistent, but the future backend direction is now explicit:

- Existing fluorescence manual ROI and wound / scratch manual ROI + threshold remain legacy/testing Python/Pillow MVP tools.
- These existing MVP tools may remain available as manual-review assistance, but they should not be expanded into a broader in-house image algorithm stack.
- Future image analysis backend work should use a local Fiji/ImageJ macro bridge.
- LabTools now has ImageJ/Fiji Bridge v1 infrastructure for user path configuration, common-path probing, version detection, macro smoke test, status display, and local config clearing.
- LabTools should own UI parameters, macro template selection, input/output path validation, dry-run/preview text, process execution feedback, result parsing, provenance, review notices, and no-overwrite export behavior.
- Fiji/ImageJ macros should own image quantification logic when future image tools are implemented.
- ImageJ/Fiji Bridge v1 is infrastructure only. It does not implement cell counting, WB grayscale, automatic ROI, batch image processing, fluorescence automated analysis, wound automated analysis, or report-ready interpretation.
- OpenCV / scikit-image are not the preferred next backend route unless a later stage explicitly overrides this decision.

## Module Architecture Alignment 1 Update

LabTools top-level navigation now uses six module entries instead of four tool-collection entries:

- 通用计算器。
- 试剂与实验记录。
- 细胞实验。
- Western Blot。
- PCR / qPCR。
- ELISA / 吸光度与标准曲线。

This alignment does not change formulas, image analysis logic, persistence schema, export formats, or implemented tool behavior. It only changes entry structure and user-visible module grouping.

Architecture conclusion:

- 通用计算器 should remain focused on general reagent calculations such as concentration, molecular weight, mass, volume, dilution, weighing, and future pH / acidity helpers.
- Experiment-specific calculations should not remain permanently grouped under 通用计算器.
- cell seeding and wound manual ROI are future 细胞实验 module candidates.
- qPCR mix is a future PCR / qPCR module candidate.
- WB loading now uses the Western Blot module protein loading tool as the user-facing entry; the older general-calculator WB loading UI entry has been removed.
- recipe draft and experiment record draft belong under 试剂与实验记录.
- fluorescence manual ROI remains a temporary image-assistance capability until ownership is confirmed.
- fluorescence manual ROI and wound manual ROI are now legacy/testing MVPs; future image work should route through Fiji/ImageJ macro bridge.
- absorbance / OD, Bradford, NanoDrop, wound healing full workflow, Transwell, WB / gel grayscale, cell counting, qPCR Delta Delta Ct, ELISA standard curve, automatic ROI, AI interpretation, formal report-ready output, full ELN, and batch image processing still require a Tool Logic Card before development.

## Western Blot Module Scaffold 1 Update

Western Blot now has a dedicated scaffold page with five placeholder sections:

- 蛋白样品准备。
- 蛋白浓度测定。
- 上样与胶。
- 电泳 / 转膜 / 抗体孵育流程。
- 结果与灰度分析。

Western Blot now has implemented child tools under 上样与胶 and 蛋白浓度测定, while unrelated child tools remain `待确认使用逻辑 / 规划中 / 暂未开放`.

Scope conclusion:

- The scaffold adds no WB grayscale analysis.
- SDS-PAGE gel template batch calculation is now implemented separately as a user-entered template tool.
- The scaffold adds no automatic recipe recommendation.
- The scaffold adds no gel concentration inference.
- The scaffold adds no SOP workflow, database, autosave, persistence schema, export format, or result interpretation.
- The 上样与胶 section may show implemented child entries for 蛋白上样体系计算 and SDS-PAGE 配胶模板与批量配制.
- The 蛋白浓度测定 section may show BCA 蛋白浓度测定 as implemented, while Bradford and NanoDrop remain planned.
- The 结果与灰度分析 section remains blocked until WB/gel grayscale, band ROI, background subtraction, target/loading control ratio, and result export logic are reviewed in a Tool Logic Card.

## SDS-PAGE Gel Template Tool 1 Update

SDS-PAGE 配胶模板与批量配制 is implemented with a narrow confirmed scope:

- It calculates batch totals only from a user-entered kit / lab template.
- It stores and imports a single template JSON using `labtools_sds_page_gel_template_store.v1`.
- It exports the current calculation result to `.xlsx` with `Summary`, `分离胶`, and `浓缩胶` sheets.
- It does not include a universal recipe, concentration recommendation, gel concentration inference, preparation step generation, protein concentration analysis, or WB grayscale analysis.
- Result meaning: experiment-assistance calculation draft requiring kit / lab SOP review.

## Western Blot Protein Loading + BCA Assay v1 Update

Protein loading and BCA are implemented with confirmed narrow scopes:

- `western_blot.protein_loading_v1` calculates Western Blot loading mix volumes from user-entered sample concentration, target protein amount, final loading volume, loading buffer stock multiple, target final buffer concentration, and overage.
- Protein loading supports multiple samples and copyable result text. It does not add a separate reducing agent component; the UI warns the user to confirm whether loading buffer already includes DTT, β-ME, or another reducing agent.
- `western_blot.bca_assay_v1` parses 8×12 OD matrices, supports Blank / Standard / Sample / Unused annotations, optional blank subtraction, linear standard curve fitting, CV% / R² / range warnings, sample concentration calculation, and copyable summary text.
- BCA v1 does not save plate layouts, does not export XLSX, does not run 4PL, does not delete outlier wells, and does not implement Bradford, NanoDrop, ELISA standard curve, or any report-ready conclusion.
- Both tools are non-write-to-disk JSON-compatible result structures only; copying results writes to clipboard only.
- Per user decision after this stage, the old 通用计算器 `WB 上样` tab is not retained; users enter protein loading through Western Blot -> 上样与胶 -> 蛋白上样体系计算.

## Current Tool Inventory

中文范围标签：实验计算器、图像辅助分析、recipe draft、experiment record draft、placeholder / planned tools。

| Tool ID | Tool name | Category | Current status | Generates result | Writes to disk | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| `calculator.dilution_v1` | Dilution calculator | experiment_calculator | implemented | yes | no | medium |
| `calculator.mass_molarity_v1` | Mass / molarity calculator | experiment_calculator | implemented | yes | no | medium |
| `calculator.cell_seeding_v1` | Cell seeding calculator | experiment_calculator | implemented | yes | no | medium |
| `calculator.qpcr_mix_v1` | qPCR mix calculator | experiment_calculator | implemented | yes | no | medium |
| `calculator.wb_loading_v1` | WB loading calculator legacy service | experiment_calculator_legacy_service | hidden UI / legacy service | yes | no | medium |
| `western_blot.sds_page_gel_template_v1` | SDS-PAGE gel template batch calculator | western_blot_template_calculator | implemented | yes | yes | medium |
| `western_blot.protein_loading_v1` | Protein loading calculator | western_blot_calculator | implemented | yes | no | medium |
| `western_blot.bca_assay_v1` | BCA protein concentration assay | western_blot_assay_calculator | implemented | yes | no | medium |
| `image.fluorescence_manual_roi_v1` | Fluorescence manual ROI | image_assistance | implemented | yes | no | medium |
| `image.wound_manual_roi_threshold_v1` | Wound / scratch manual ROI + threshold | image_assistance | implemented | yes | no | medium |
| `image.roi_export_package_v1` | ROI export package | image_export | implemented | yes | yes | medium |
| `imagej_fiji.bridge_v1` | ImageJ/Fiji bridge infrastructure | image_backend_config | implemented | no | yes | medium |
| `recipe.draft_store_v1` | Recipe draft store | recipe_draft | implemented | yes | yes | medium |
| `recipe.import_export_v1` | Recipe import / export | recipe_draft | implemented | yes | yes | medium |
| `recipe.safety_category_v1` | Recipe safety category | recipe_draft | implemented | yes | yes | medium |
| `recipe.conflict_import_v1` | Recipe conflict import behavior | recipe_draft | implemented | yes | no | low |
| `experiment.template_draft_v1` | Experiment template draft | experiment_record_draft | implemented | yes | no | medium |
| `experiment.record_draft_store_v1` | Experiment record draft JSON persistence | experiment_record_draft | implemented | yes | yes | medium |
| `planned.automatic_cell_counting` | Automatic cell counting | planned_image_tool | placeholder | no | no | high |
| `planned.grayscale_ink_value` | Grayscale / ink-value | planned_image_tool | placeholder | no | no | high |
| `planned.wb_gel_grayscale` | WB / gel grayscale | planned_image_tool | placeholder | no | no | high |
| `planned.automatic_roi` | Automatic ROI | planned_image_tool | placeholder | no | no | high |
| `planned.full_eln` | Full ELN | planned_record_system | placeholder | no | no | high |
| `planned.batch_image_processing` | Batch image processing | planned_image_tool | placeholder | no | no | high |

## Tool Logic Audit Table

| Tool ID | user_logic_confirmed | needs_user_discussion | needs_code整改 | Recommended next action |
| --- | --- | --- | --- | --- |
| `calculator.dilution_v1` | partial | yes | no | Confirm units, formula wording, and copy text fields before expanding. |
| `calculator.mass_molarity_v1` | partial | yes | no | Confirm assumptions around MW, salts/hydrates, purity notes, and result fields. |
| `calculator.cell_seeding_v1` | partial | yes | no | Confirm seeding assumptions, overage semantics, and invalid cases. |
| `calculator.qpcr_mix_v1` | partial | yes | no | Confirm qPCR mix assumptions before any Delta Delta Ct or plate logic. |
| `calculator.wb_loading_v1` | partial | no | no | Keep hidden from 通用计算器 UI; use Western Blot protein loading as current entry. |
| `western_blot.sds_page_gel_template_v1` | yes | no | no | Keep as user-entered template batch calculator; discuss before adding recommendations or built-in recipes. |
| `western_blot.protein_loading_v1` | yes | no | no | Keep as WB loading assistance; discuss before adding reducer component automation or SOP workflow. |
| `western_blot.bca_assay_v1` | yes | no | no | Keep as BCA linear-fit assistance; discuss before adding 4PL, ELISA, Bradford, NanoDrop, export, or plate template persistence. |
| `image.fluorescence_manual_roi_v1` | partial | yes | no | Keep as legacy/testing MVP; future image expansion should move to Fiji/ImageJ macro bridge. |
| `image.wound_manual_roi_threshold_v1` | partial | yes | no | Keep as legacy/testing MVP; future wound workflow should move to Fiji/ImageJ macro bridge. |
| `image.roi_export_package_v1` | partial | yes | no | Confirm manifest summary fields and shareability boundaries. |
| `imagej_fiji.bridge_v1` | yes | no | no | Keep as local external-backend configuration and smoke-test infrastructure; discuss every concrete macro workflow separately. |
| `recipe.draft_store_v1` | partial | yes | no | Confirm recipe fields and safety wording before richer templates. |
| `recipe.import_export_v1` | partial | yes | no | Keep non-overwrite behavior; confirm import review workflow if expanded. |
| `recipe.safety_category_v1` | partial | yes | no | Confirm category names and user-visible meaning. |
| `recipe.conflict_import_v1` | yes | no | no | Keep imported-copy behavior as-is. |
| `experiment.template_draft_v1` | partial | yes | no | Confirm template field set and wording before additional templates. |
| `experiment.record_draft_store_v1` | partial | yes | no | Confirm record fields and non-ELN language before richer records. |
| `planned.*` tools | no | yes | unknown | Require a Tool Logic Card before implementation. |

## Audit Record Matrix

Each row is a compact audit record. Detailed Tool Logic Cards below expand the same fields.

| tool_id | tool_name | tool_category | current_status | implemented_files | test_files | does_generate_result | does_write_to_disk | current_inputs | current_user_workflow | current_outputs | current_result_meaning | review_level | known_failure_cases | user_logic_confirmed | risk_level | needs_user_discussion | needs_code整改 | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `calculator.dilution_v1` | Dilution calculator | experiment_calculator | implemented | `experiment_calculator_center.py`; `calculator_widgets.py` | `test_experiment_calculator_center.py`; `test_labtools_calculator_copy_ui.py` | yes | no | stock concentration; target concentration; final volume | enter values; calculate; optionally copy | stock volume; solvent volume; dilution factor | C1V1 planning aid | manual review | invalid units; target > stock; invalid numbers | partial | medium | yes | no | confirm units and copy fields |
| `calculator.mass_molarity_v1` | Mass / molarity calculator | experiment_calculator | implemented | `experiment_calculator_center.py`; `calculator_widgets.py` | `test_experiment_calculator_center.py`; `test_unit_conversion.py` | yes | no | MW; target molarity; volume; mass unit | enter values; calculate; optionally copy | required mass; moles | weighing / molarity planning aid | manual review | invalid MW; invalid unit; invalid numbers | partial | medium | yes | no | confirm MW and purity assumptions |
| `calculator.cell_seeding_v1` | Cell seeding calculator | experiment_calculator | implemented | `experiment_calculator_center.py`; `calculator_widgets.py` | `test_experiment_calculator_center.py`; `test_cell_seeding_calculator.py` | yes | no | cell concentration; target cells; wells; volume; overage | enter values; calculate; optionally copy | suspension volume; medium volume; total cells | seeding volume planning aid | manual review | invalid numbers; suspension exceeds final volume | partial | medium | yes | no | confirm overage and viability language |
| `calculator.qpcr_mix_v1` | qPCR mix calculator | experiment_calculator | implemented | `experiment_calculator_center.py`; `calculator_widgets.py` | `test_l5c_qpcr_wb_calculators.py`; `test_qpcr_mix_calculator.py` | yes | no | reactions; reaction volume; mix; primers; template; overage | enter mix setup; calculate | per reaction and total component volumes | qPCR mix setup aid | manual review | component volume exceeds reaction; invalid percent | partial | medium | yes | no | confirm qPCR assumptions |
| `calculator.wb_loading_v1` | WB loading calculator legacy service | experiment_calculator_legacy_service | hidden UI / legacy service | `experiment_calculator_center.py` | `test_l5c_qpcr_wb_calculators.py` | yes | no | protein concentration; target mass; final volume; buffer multiple | no current user-facing workflow in 通用计算器 | sample; buffer; water volumes | legacy WB loading volume aid only | manual review | sample + buffer exceeds final volume | partial | medium | no | no | keep hidden; use `western_blot.protein_loading_v1` |
| `western_blot.sds_page_gel_template_v1` | SDS-PAGE gel template batch calculator | western_blot_template_calculator | implemented | `sds_page_gel_templates.py`; `western_blot_widgets.py`; `labtools_schema_index.md` | `test_sds_page_gel_templates.py`; `test_labtools_sds_page_gel_tool_ui.py` | yes | yes | user template; resolving / stacking sections; components; gel count; overage | enter or import template; calculate; optional JSON/XLSX export | per-section total amounts; template JSON; calculation XLSX | user-template batch conversion draft | kit / lab SOP review | invalid JSON; conflicts; unsupported unit; invalid gel count; write failure | yes | medium | no | no | keep as user-entered template only |
| `western_blot.protein_loading_v1` | Protein loading calculator | western_blot_calculator | implemented | `protein_loading.py`; `western_blot_widgets.py`; `labtools_schema_index.md` | `test_western_blot_protein_loading.py`; `test_labtools_western_blot_loading_bca_ui.py` | yes | no | sample concentrations; target protein; final volume; buffer multiple; target buffer concentration; overage | enter multiple samples; calculate; optionally copy | per-sample sample / buffer / water volumes; totals; warnings | WB loading mix assistance draft | manual review | invalid concentration; invalid target or volume; buffer setting invalid; negative water volume; small pipetting volumes | yes | medium | no | no | keep as auxiliary loading calculator |
| `western_blot.bca_assay_v1` | BCA protein concentration assay | western_blot_assay_calculator | implemented | `bca_assay.py`; `western_blot_widgets.py`; `labtools_schema_index.md` | `test_bca_assay.py`; `test_labtools_western_blot_loading_bca_ui.py` | yes | no | 8x12 OD matrix; well annotations; standards; samples; blank setting | paste OD matrix; annotate wells; calculate; optionally copy | raw data table; standard curve; sample results; warnings | BCA linear-fit assistance draft | kit / lab SOP review | insufficient standards; invalid slope; low R2; high CV; out-of-range sample; negative corrected OD; negative concentration | yes | medium | no | no | keep as BCA v1 linear-fit tool |
| `image.fluorescence_manual_roi_v1` | Fluorescence manual ROI | image_assistance | implemented | `fluorescence_analyzer.py`; `fluorescence_models.py`; `image_analysis_widgets.py` | `test_fluorescence_analyzer.py`; `test_fluorescence_export.py`; `test_fluorescence_report.py` | yes | no | image path; signal ROI; background ROI | select image; enter manual ROI; run | grayscale metrics; warnings; previews | manual ROI measurement assistance | manual review | unreadable image; ROI out of bounds; negative CTF warning | partial | medium | yes | no | confirm metrics and background correction |
| `image.wound_manual_roi_threshold_v1` | Wound / scratch manual ROI + threshold | image_assistance | implemented | `wound_analyzer.py`; `wound_models.py`; `image_analysis_widgets.py` | `test_wound_analyzer.py`; `test_wound_export.py`; `test_wound_report.py` | yes | no | image path; ROI; threshold; mode | select image; enter manual ROI and threshold; run | area pixels and fractions | threshold-based area estimation | manual review | unreadable image; ROI out of bounds; invalid threshold | partial | medium | yes | no | confirm metric meanings |
| `image.roi_export_package_v1` | ROI export package | image_export | implemented | `export_package.py`; `image_analysis_widgets.py` | `test_roi_export_package_schema.py`; `test_labtools_image_export_ui.py` | yes | yes | current ROI result; output directory | run analysis; choose export directory | JSON; CSV; Markdown; overlay PNG | local manual-review package | manual review | no result; cancel; write failure; source unreadable | partial | medium | yes | no | confirm result summary and path policy |
| `imagej_fiji.bridge_v1` | ImageJ/Fiji bridge infrastructure | image_backend_config | implemented | `imagej_bridge.py`; `imagej_bridge_widgets.py`; `workspace.py`; `labtools_schema_index.md` | `test_imagej_bridge.py`; `test_labtools_imagej_bridge_ui.py` | no | yes | user-selected executable/app path; auto-detected candidate path | configure path; run smoke test; view status; clear config | local config JSON; status; version fields; smoke-test summary | backend availability check only | manual setup review | missing executable; invalid path; timeout; output missing; version unknown | yes | medium | no | no | keep infrastructure only; require Tool Logic Card for every macro workflow |
| `recipe.draft_store_v1` | Recipe draft store | recipe_draft | implemented | `recipe_persistence.py`; `user_recipe_store.py`; `recipe_widgets.py` | `test_recipe_persistence.py`; `test_user_recipe_store.py` | yes | yes | confirmed user recipes; save path | confirm draft; save JSON | recipe draft JSON | local recipe draft persistence | SOP/SDS review | no recipes; invalid path; unsafe terms | partial | medium | yes | no | confirm fields and safety wording |
| `recipe.import_export_v1` | Recipe import / export | recipe_draft | implemented | `recipe_persistence.py`; `user_recipe_store.py`; `recipe_widgets.py` | `test_recipe_persistence.py`; `test_labtools_recipe_persistence_ui.py` | yes | yes | recipe JSON; current store | save or load JSON | saved file; imported recipes; summary | local draft import/export | manual review | malformed JSON; schema mismatch; unsafe terms | partial | medium | yes | no | confirm import review workflow |
| `recipe.safety_category_v1` | Recipe safety category | recipe_draft | implemented | `recipe_persistence.py`; `recipe_widgets.py`; `labtools_schema_index.md` | `test_recipe_persistence.py`; `test_labtools_recipe_persistence_ui.py` | yes | yes | recipe draft payload | save/load recipe draft | safety category fields and UI text | draft review category reminder | manual review | category naming may be misunderstood | partial | medium | yes | no | confirm category names |
| `recipe.conflict_import_v1` | Recipe conflict import behavior | recipe_draft | implemented | `user_recipe_store.py`; `recipe_widgets.py` | `test_recipe_persistence.py`; `test_labtools_recipe_persistence_ui.py` | yes | no | imported recipe IDs; current store | load JSON with duplicate ID | imported copy; conflict count | non-destructive conflict handling | manual review | unsafe imported recipe blocks import | yes | low | no | no | keep as-is |
| `experiment.template_draft_v1` | Experiment template draft | experiment_record_draft | implemented | `template_library.py`; `template_models.py`; `template_widgets.py` | `test_experiment_templates.py`; `test_labtools_template_ui.py` | yes | no | template; purpose; groups; reagents; parameters; outputs | choose template; edit fields; generate preview | draft object; Markdown preview | local structured draft | manual review | missing required fields | partial | medium | yes | no | confirm field set |
| `experiment.record_draft_store_v1` | Experiment record draft JSON persistence | experiment_record_draft | implemented | `template_persistence.py`; `template_widgets.py` | `test_experiment_template_persistence.py`; `test_labtools_template_ui.py` | yes | yes | record drafts; JSON path | save or load draft JSON | draft store JSON; loaded drafts | local draft persistence; not full ELN | manual review | no drafts; malformed JSON; schema mismatch; blocked terms | partial | medium | yes | no | confirm record fields |
| `planned.automatic_cell_counting` | Automatic cell counting | planned_image_tool | placeholder | `analysis_task.py`; `result_models.py`; `image_analysis_widgets.py` | `test_image_analysis_task.py`; `test_labtools_status_semantics.py` | no | no | none for result | create placeholder task only | `algorithm_not_available` | planned only | not available | any count output would be out of scope | no | high | yes | unknown | create Tool Logic Card and Fiji/ImageJ macro bridge design before development |
| `planned.grayscale_ink_value` | Grayscale / ink-value | planned_image_tool | placeholder | `analysis_task.py`; `result_models.py`; `image_analysis_widgets.py` | `test_image_analysis_task.py`; `test_labtools_status_semantics.py` | no | no | none for result | create placeholder task only | `algorithm_not_available` | planned only | not available | any grayscale result would be out of scope | no | high | yes | unknown | create Tool Logic Card and Fiji/ImageJ macro bridge design before development |
| `planned.wb_gel_grayscale` | WB / gel grayscale | planned_image_tool | placeholder | `calculator_widgets.py`; `image_analysis_widgets.py` | `test_labtools_imports.py`; `test_labtools_status_semantics.py` | no | no | none for result | WB loading only; no image workflow | none | planned only | not available | any band quantification would be out of scope | no | high | yes | unknown | create Tool Logic Card and Fiji/ImageJ macro bridge design before development |
| `planned.automatic_roi` | Automatic ROI | planned_image_tool | placeholder | `roi_models.py`; `image_analysis_widgets.py` | `test_image_analysis_task.py`; `test_labtools_status_semantics.py` | no | no | none for result | manual ROI only | none | planned only | not available | any auto ROI claim would be out of scope | no | high | yes | unknown | create Tool Logic Card and Fiji/ImageJ macro bridge design before development |
| `planned.full_eln` | Full ELN | planned_record_system | placeholder | `template_models.py`; `template_widgets.py` | `test_labtools_template_ui.py`; `test_labtools_status_semantics.py` | no | no | none for full ELN | draft records only | none for full ELN | planned only | not available | any signature or compliance workflow claim would be out of scope | no | high | yes | unknown | create Tool Logic Card before development |
| `planned.batch_image_processing` | Batch image processing | planned_image_tool | placeholder | `image_analysis_widgets.py` | `test_labtools_status_semantics.py` | no | no | none for batch | single-image tools only | none | planned only | not available | any batch table/export claim would be out of scope | no | high | yes | unknown | create Tool Logic Card and Fiji/ImageJ macro bridge design before development |

## Tools Safe to Keep As-Is

These are low-risk support behaviors and can remain without a product-logic discussion unless their scope changes:

- UI wording that says local assistance, draft, placeholder, or manual-review.
- Schema index documentation.
- No-overwrite file naming.
- Cancel / failure / success feedback.
- Import conflict behavior that does not overwrite existing user recipes.
- Draft save/load initiated by a user-selected path.
- Copyable text limited to clipboard.
- Manual-review reminders.

## Tools Requiring User Logic Confirmation

Existing tools that generate user-visible scientific or lab workflow values should be confirmed before expansion:

- Dilution / mass-molarity / cell seeding calculators.
- qPCR calculator.
- Western Blot protein loading calculator.
- BCA v1 only before adding export, template persistence, or non-linear model support.
- Fluorescence manual ROI.
- Wound / scratch manual ROI + threshold.
- ROI export result summary.
- Recipe template fields and safety boundaries.
- Experiment record draft fields.

## Tools Requiring Future Redesign Before Development

The following must not be developed directly from the current placeholder state. Each needs a Tool Logic Card, user discussion, formulas/inputs/outputs review, and risk review first:

- Absorbance / OD calculation.
- Bradford / NanoDrop and protein concentration workflows beyond BCA v1.
- Wound healing full workflow.
- Transwell assay.
- WB / gel grayscale.
- Cell counting.
- Fiji/ImageJ macro bridge for any future image backend.
- qPCR Delta Delta Ct.
- ELISA standard curve.
- Automatic ROI.
- AI interpretation.
- Formal report-ready result.
- Batch image processing.
- Full ELN.

## Potential Mismatches Between UI / Docs / Code

No blocking mismatch found in this audit.

Non-blocking observations:

- qPCR remains in the calculator center. The older general-calculator WB loading service remains only as legacy service code; its 通用计算器 UI entry is removed.
- Western Blot protein loading and BCA v1 now have user-confirmed narrow Tool Logic Cards; future expansion still requires a new discussion.
- Wound / scratch manual ROI exposes `non_scratch_area_fraction` as a computed metric; documentation correctly says this is threshold-based estimation, not automatic migration interpretation.
- ROI export writes local paths in UI success feedback. The schema index correctly treats this as local UI feedback, not public report content.
- Image analysis backend direction is now Fiji/ImageJ macro bridge. Current Python/Pillow ROI tools are legacy/testing MVPs, not a signal to continue building broad self-developed image algorithms in LabTools.
- Recipe safety category exists in payload and UI, but category naming should be user-confirmed before richer recipe templates are added.
- Experiment record draft persistence exists, but documentation correctly says it is not a complete ELN.

## Recommended整改 Order

Priority 1: current implemented result-semantics tools

- Dilution / mass-molarity / cell seeding calculators.
- Western Blot protein loading calculator.
- BCA v1 result summary.
- Fluorescence manual ROI.
- Wound manual ROI + threshold.
- ROI export summary.
- ImageJ/Fiji macro workflow Tool Logic Card before any future image backend expansion.

Priority 2: current draft / persistence semantics

- Recipe draft.
- Experiment record draft.

Priority 3: next tools requiring discussion before development

- Absorbance / OD calculation.
- Protein concentration workflows beyond BCA v1.
- Wound healing full workflow.
- Transwell assay.
- WB / gel grayscale.
- Cell counting.
- qPCR Delta Delta Ct.
- ELISA standard curve.

## Proposed Tool Logic Cards Needed Next

Before development resumes, create user-reviewed Tool Logic Cards for:

- `calculator.dilution_v1`: unit conversions, dilution factor, invalid states, copy fields.
- `calculator.mass_molarity_v1`: MW assumptions, unit conversions, salt/hydrate/purity warning text.
- `calculator.cell_seeding_v1`: overage, concentration units, viability caveat, output fields.
- `image.fluorescence_manual_roi_v1`: legacy MVP status, ROI metrics, background correction, negative CTF handling, and migration path to Fiji/ImageJ macro bridge.
- `image.wound_manual_roi_threshold_v1`: legacy MVP status, threshold mode, scratch vs covered area language, and migration path to Fiji/ImageJ macro bridge.
- `image.roi_export_package_v1`: manifest summary fields, local path policy, shareability.
- Concrete ImageJ/Fiji macro workflow cards: input files, macro parameter schema, expected result files, provenance, warnings, export policy, and manual-review output semantics.
- `recipe.draft_store_v1`: required recipe fields and safety category meaning.
- `experiment.record_draft_store_v1`: required record fields and non-ELN wording.
- Future WB/BCA expansion: reducer component automation, BCA 4PL, Bradford, NanoDrop, ELISA standard curves, plate layout persistence, export formats.

## Non-goals Confirmed

The original Tool Logic Audit 1 stage did not add:

- Tools.
- Algorithms.
- Image processing logic.
- Calculation formulas.
- Persistence schema.
- Export formats.
- Bioinformatics / Meta / ReleaseBuild / MainLine changes.
- `dist` or desktop app package changes.
- Remote push.

## Validation

Expected validation for this stage:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
- `python3 -m compileall app/labtools`
- `git diff --check`

## Tool Logic Card: Dilution calculator

Current implementation:

- tool_id: `calculator.dilution_v1`
- tool_name: Dilution calculator
- tool_category: experiment_calculator
- current_status: implemented
- implemented_files: `app/labtools/calculators/experiment_calculator_center.py`, `app/labtools/ui/calculator_widgets.py`
- test_files: `tests/labtools/test_experiment_calculator_center.py`, `tests/ui/test_labtools_calculator_copy_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User enters stock concentration, target concentration, and final volume.
- User runs the calculator.
- UI shows stock volume, solvent volume, dilution factor, summary, and review note.
- Optional copy action writes plain text to clipboard only.

Inputs:

- Stock concentration and unit.
- Target concentration and unit.
- Final volume and unit.

Outputs:

- Stock volume.
- Solvent volume.
- Final volume.
- Dilution factor.
- Warnings or validation errors.

Result meaning:

- Local C1V1=C2V2 assistance for planning a dilution.
- It is not a validated SOP or safety instruction.

Review level:

- Manual review required.

Failure / invalid cases:

- Missing, non-numeric, zero, or negative values.
- Incompatible concentration dimensions.
- Target concentration greater than stock concentration.
- Invalid volume unit.

Current tests:

- Unit conversion and calculator center tests cover valid and invalid cases.
- UI copy tests cover copyable result enablement.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm unit scope and copy text fields before any new dilution modes.

## Tool Logic Card: Mass / molarity calculator

Current implementation:

- tool_id: `calculator.mass_molarity_v1`
- tool_name: Mass / molarity calculator
- tool_category: experiment_calculator
- current_status: implemented
- implemented_files: `app/labtools/calculators/experiment_calculator_center.py`, `app/labtools/ui/calculator_widgets.py`
- test_files: `tests/labtools/test_experiment_calculator_center.py`, `tests/labtools/test_unit_conversion.py`, `tests/ui/test_labtools_calculator_copy_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User enters molecular weight, target concentration, final volume, and output mass unit.
- UI returns required mass and moles.
- Optional copy action writes plain text to clipboard only.

Inputs:

- Molecular weight.
- Target molarity.
- Final volume.
- Output mass unit.

Outputs:

- Required mass.
- Moles.
- Summary and review note.

Result meaning:

- Local calculation draft for mass / molarity planning.
- Requires user review for purity, salt/hydrate form, effective content, and SOP context.

Review level:

- Manual review required.

Failure / invalid cases:

- Missing or invalid numeric fields.
- Non-molar concentration unit.
- Invalid volume or mass unit.

Current tests:

- Calculator center and unit conversion tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm result field wording and assumptions around molecular form before expanding.

## Tool Logic Card: Cell seeding calculator

Current implementation:

- tool_id: `calculator.cell_seeding_v1`
- tool_name: Cell seeding calculator
- tool_category: experiment_calculator
- current_status: implemented
- implemented_files: `app/labtools/calculators/experiment_calculator_center.py`, `app/labtools/ui/calculator_widgets.py`
- test_files: `tests/labtools/test_experiment_calculator_center.py`, `tests/labtools/test_cell_seeding_calculator.py`, `tests/ui/test_labtools_calculator_copy_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User enters current cell concentration, target cells per well, well count, volume per well, and overage.
- UI returns suspension volume, medium volume, total final volume, and total cells.
- Optional copy action writes plain text to clipboard only.

Inputs:

- Current cell concentration.
- Concentration unit.
- Target cells per well.
- Well count.
- Volume per well.
- Overage percentage.

Outputs:

- Required cell suspension volume.
- Required medium volume.
- Total final volume.
- Total cells required.

Result meaning:

- Local seeding volume planning aid.
- It does not validate cell viability, contamination status, counting quality, or experimental design.

Review level:

- Manual review required.

Failure / invalid cases:

- Invalid numeric fields.
- Unsupported concentration or volume unit.
- Cell suspension volume exceeds final planned volume.
- Negative overage.

Current tests:

- Calculator center and cell seeding calculator tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm overage semantics and whether viability correction should remain out of scope.

## Tool Logic Card: qPCR mix calculator

Current implementation:

- tool_id: `calculator.qpcr_mix_v1`
- tool_name: qPCR mix calculator
- tool_category: experiment_calculator
- current_status: implemented
- implemented_files: `app/labtools/calculators/experiment_calculator_center.py`, `app/labtools/ui/calculator_widgets.py`
- test_files: `tests/labtools/test_l5c_qpcr_wb_calculators.py`, `tests/labtools/test_qpcr_mix_calculator.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User enters reaction count, reaction volume, master mix value/mode, primers, template, and overage.
- UI returns per-reaction, total, and overage-adjusted volumes.

Inputs:

- Reaction count.
- Reaction volume.
- Master mix volume or percent.
- Forward primer, reverse primer, template volumes.
- Overage percentage.

Outputs:

- Per-reaction volumes by component.
- Total volumes by component.
- Overage-adjusted volumes.

Result meaning:

- Local qPCR mix setup aid.
- It does not design primers, plate layouts, controls, Ct interpretation, or Delta Delta Ct.

Review level:

- Manual review required.

Failure / invalid cases:

- Component volume exceeds reaction volume.
- Invalid master mix percentage.
- Negative overage.
- Invalid numeric inputs.

Current tests:

- qPCR calculator and L5C calculator tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm qPCR setup assumptions; require a new card before Delta Delta Ct work.

## Tool Logic Card: WB loading calculator legacy service

Current implementation:

- tool_id: `calculator.wb_loading_v1`
- tool_name: WB loading calculator legacy service
- tool_category: experiment_calculator_legacy_service
- current_status: hidden UI / legacy service
- implemented_files: `app/labtools/calculators/experiment_calculator_center.py`
- test_files: `tests/labtools/test_l5c_qpcr_wb_calculators.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- No current user-facing workflow in 通用计算器.
- Users should enter Western Blot loading calculations through `western_blot.protein_loading_v1`.

Inputs:

- Protein concentration and unit.
- Target protein mass.
- Final loading volume and unit.
- Loading buffer multiple.

Outputs:

- Sample volume.
- Loading buffer volume.
- Water volume.
- Final loading volume.

Result meaning:

- Local WB/SDS-PAGE loading volume planning aid.
- It does not perform WB / gel grayscale, band detection, normalization, or image interpretation.

Review level:

- Manual review required.

Failure / invalid cases:

- Sample plus buffer exceeds final volume.
- Invalid protein concentration unit.
- Invalid numeric inputs.

Current tests:

- L5C qPCR/WB calculator tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: no for removal from current UI
- needs_code整改: no

Recommended next step:

- Keep hidden from 通用计算器 UI; use Western Blot protein loading as the current entry.

## Tool Logic Card: SDS-PAGE gel template batch calculator

Current implementation:

- tool_id: `western_blot.sds_page_gel_template_v1`
- tool_name: SDS-PAGE gel template batch calculator
- tool_category: western_blot_template_calculator
- current_status: implemented
- implemented_files: `app/labtools/western_blot/sds_page_gel_templates.py`, `app/labtools/ui/western_blot_widgets.py`, `docs/labtools_schema_index.md`
- test_files: `tests/labtools/test_sds_page_gel_templates.py`, `tests/ui/test_labtools_sds_page_gel_tool_ui.py`
- does_generate_result: yes
- does_write_to_disk: yes, only after user-selected JSON or XLSX path

User workflow:

- User enters a template from a kit or lab template.
- User fills resolving gel and stacking gel sections; either section can be marked `0 / 不使用`.
- User enters gel count and optional overage percent.
- UI calculates batch totals and can export a single template JSON or current calculation XLSX.
- Imported JSON is schema-checked; conflicts are skipped or imported as a copy.

Inputs:

- Template name, version, gel concentration, gel thickness, well count, format/note, and source.
- Resolving gel and stacking gel component name, amount per gel, unit, and note.
- Gel count.
- Overage percent, default 3%.

Outputs:

- Total amount with overage per component.
- Template JSON with `labtools_sds_page_gel_template_store.v1`.
- Current calculation `.xlsx` with `Summary`, `分离胶`, and `浓缩胶` sheets.

Result meaning:

- User-template batch conversion draft.
- It does not define a universal correct formula, recommend concentration, infer gel concentration, generate preparation steps, analyze protein concentration, or analyze WB grayscale.

Review level:

- Kit / lab SOP review required.

Failure / invalid cases:

- Empty template name.
- Invalid gel count.
- Negative overage.
- No active gel section.
- Empty component name.
- Negative component amount.
- Unsupported unit.
- Invalid JSON.
- Template ID or name conflict.
- XLSX write failure or user-cancelled export.

Current tests:

- SDS-PAGE gel template service tests.
- SDS-PAGE gel tool UI tests.

Confirmed by user:

- user_logic_confirmed: yes

Risk:

- risk_level: medium
- needs_user_discussion: no for current user-template scope
- needs_code整改: no

Recommended next step:

- Keep current tool limited to user-entered templates; require a new Tool Logic Card before built-in recipes, concentration recommendations, gel concentration inference, or WB grayscale analysis.

## Tool Logic Card: Western Blot protein loading calculator

Current implementation:

- tool_id: `western_blot.protein_loading_v1`
- tool_name: Protein loading calculator
- tool_category: western_blot_calculator
- current_status: implemented
- implemented_files: `app/labtools/western_blot/protein_loading.py`, `app/labtools/ui/western_blot_widgets.py`
- test_files: `tests/labtools/test_western_blot_protein_loading.py`, `tests/ui/test_labtools_western_blot_loading_bca_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User opens Western Blot -> 上样与胶 -> 蛋白上样体系计算.
- User enters one or more samples with protein concentration and concentration unit.
- User enters target protein amount, final loading volume, loading buffer multiple, target final buffer concentration, and overage percent.
- UI calculates per-well component volumes and total volumes, then allows copying the result text.

Inputs:

- Sample name.
- Protein concentration and unit: `µg/µL`, `ug/uL`, `mg/mL`, `µg/mL`, `ug/mL`.
- Target protein amount in `µg`.
- Final loading volume in `µL`.
- Loading buffer stock multiple and target final concentration.
- Overage percent, default 3%.

Outputs:

- Per-sample protein sample volume.
- Per-sample loading buffer volume.
- Per-sample water volume.
- Per-sample final loading volume.
- Total protein sample, loading buffer, and water volumes after overage.
- Warning list and copyable text.

Result meaning:

- Western Blot loading mix assistance draft.
- The result does not verify the protein assay, sample dilution history, reducer status, heating condition, or lab SOP.
- First version assumes reducing agent is handled outside the calculator and requires the user to confirm whether loading buffer already contains DTT, β-ME, or another reducing agent.

Review level:

- Manual review required.

Failure / invalid cases:

- Protein concentration <= 0.
- Target protein amount <= 0.
- Final loading volume <= 0.
- Loading buffer stock multiple <= target final concentration.
- Component volumes exceed final loading volume.
- Protein sample volume < 1 µL.
- Water volume < 1 µL.

Current tests:

- Protein loading service tests.
- Western Blot loading/BCA UI tests.

Confirmed by user:

- user_logic_confirmed: yes

Risk:

- risk_level: medium
- needs_user_discussion: no for current v1 formulas and result fields
- needs_code整改: no

Recommended next step:

- Keep as auxiliary loading mix calculator; discuss before adding reducer component automation, heating workflow, built-in SOP templates, or WB image result workflows.

## Tool Logic Card: BCA protein concentration assay

Current implementation:

- tool_id: `western_blot.bca_assay_v1`
- tool_name: BCA protein concentration assay
- tool_category: western_blot_assay_calculator
- current_status: implemented
- implemented_files: `app/labtools/western_blot/bca_assay.py`, `app/labtools/ui/western_blot_widgets.py`
- test_files: `tests/labtools/test_bca_assay.py`, `tests/ui/test_labtools_western_blot_loading_bca_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User opens Western Blot -> 蛋白浓度测定 -> BCA 蛋白浓度测定.
- User pastes an 8x12 OD matrix or fills the 96-well grid.
- User annotates wells as Blank, Standard, Sample, or Unused, with batch range support.
- User chooses whether to enable blank subtraction.
- UI calculates Plate Raw Data, Standard Curve, Sample Results, warnings, and copyable summary text.

Inputs:

- 8x12 OD matrix, with optional A-H row names and 1-12 column numbers.
- Well annotations.
- Standard name and concentration, with units `µg/mL` or `mg/mL`.
- Sample name, dilution factor, and note.
- Optional blank subtraction setting.

Outputs:

- Plate Raw Data rows with raw OD, blank-corrected OD, include flag, and warnings.
- Standard Curve rows with mean OD, SD, CV%, fit inclusion, and warnings.
- Linear fit: slope, intercept, R², standard OD range, and standard concentration range.
- Sample Results rows with mean OD, SD, CV%, measured concentration, dilution-corrected original concentration, range status, warnings, and note.
- Copyable summary text with blank state, formula, R², sample results, warning list, and review notice.

Result meaning:

- BCA protein concentration measurement assistance draft.
- It is a linear-fit helper only and does not prove assay success, sample validity, or report-ready concentration.
- Results require kit instructions, standard curve quality, replicate consistency, and lab SOP review.

Review level:

- Kit / lab SOP review required.

Failure / invalid cases:

- Fewer than 3 standard concentration points.
- Slope <= 0.
- R² < 0.98.
- Standard or sample CV% > 15%.
- Sample OD or calculated concentration outside standard curve range.
- Blank-corrected OD < 0.
- Negative calculated sample concentration.
- Missing, non-numeric, negative, or unusually high OD.
- Invalid well annotation or concentration unit.

Current tests:

- BCA service tests.
- Western Blot loading/BCA UI tests.

Confirmed by user:

- user_logic_confirmed: yes

Risk:

- risk_level: medium
- needs_user_discussion: no for current BCA v1 linear-fit scope
- needs_code整改: no

Recommended next step:

- Keep as BCA v1 linear-fit assistance; discuss before adding 4PL, ELISA standard curves, Bradford, NanoDrop, automatic outlier deletion, plate layout persistence, or XLSX export.

## Tool Logic Card: Fluorescence manual ROI

Current implementation:

- tool_id: `image.fluorescence_manual_roi_v1`
- tool_name: Fluorescence manual ROI
- tool_category: image_assistance
- current_status: implemented
- implemented_files: `app/labtools/image_analysis/fluorescence/fluorescence_analyzer.py`, `app/labtools/image_analysis/fluorescence/fluorescence_models.py`, `app/labtools/image_analysis/fluorescence/fluorescence_export.py`, `app/labtools/image_analysis/fluorescence/fluorescence_report.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_fluorescence_analyzer.py`, `tests/labtools/test_fluorescence_models.py`, `tests/labtools/test_fluorescence_export.py`, `tests/labtools/test_fluorescence_quality.py`, `tests/labtools/test_fluorescence_report.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User provides a local image path.
- User manually enters signal ROI and background ROI.
- UI runs grayscale ROI analysis and displays metrics, warnings, preview rows, and review note.

Inputs:

- Local image path.
- Signal ROI coordinates.
- Background ROI coordinates.
- Background correction toggle in model defaults.

Outputs:

- ROI area pixels.
- Mean intensity.
- Integrated density.
- Background mean intensity.
- Corrected total fluorescence.
- Min and max intensity.
- Warnings and review note.

Result meaning:

- Manual ROI grayscale measurement assistance.
- It does not identify cells, choose ROI automatically, or interpret biology.
- Current Python/Pillow implementation is a legacy/testing MVP and not the preferred path for future image backend expansion.

Review level:

- Manual review required.

Failure / invalid cases:

- Missing, unreadable, unsupported, or out-of-bound image.
- Empty ROI.
- Negative corrected total fluorescence warning.
- Saturation or quality warnings.

Current tests:

- Fluorescence analyzer, model, export, quality, and report tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Keep current tool as manual-review legacy MVP.
- Route future fluorescence image backend work through Fiji/ImageJ macro bridge.
- Confirm metric names, background correction language, and negative CTF meaning before migrating or expanding.

## Tool Logic Card: Wound / scratch manual ROI + threshold

Current implementation:

- tool_id: `image.wound_manual_roi_threshold_v1`
- tool_name: Wound / scratch manual ROI + threshold
- tool_category: image_assistance
- current_status: implemented
- implemented_files: `app/labtools/image_analysis/wound_healing/wound_analyzer.py`, `app/labtools/image_analysis/wound_healing/wound_models.py`, `app/labtools/image_analysis/wound_healing/wound_export.py`, `app/labtools/image_analysis/wound_healing/wound_report.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_wound_analyzer.py`, `tests/labtools/test_wound_models.py`, `tests/labtools/test_wound_export.py`, `tests/labtools/test_wound_quality.py`, `tests/labtools/test_wound_report.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User provides a local image path.
- User manually enters analysis ROI, threshold, and bright/dark mode.
- UI displays threshold-based area metrics and review note.

Inputs:

- Local image path.
- Analysis ROI coordinates.
- Threshold 0-255.
- Scratch mode: bright or dark.

Outputs:

- ROI area pixels.
- Scratch candidate area pixels and fraction.
- Non-scratch area pixels and fraction.
- Threshold and mode.
- Warnings and review note.

Result meaning:

- Threshold-based manual ROI area estimation.
- It must not be treated as automatic migration-effect interpretation.
- Current Python/Pillow implementation is a legacy/testing MVP and not the preferred path for future wound workflow expansion.

Review level:

- Manual review required.

Failure / invalid cases:

- Missing, unreadable, unsupported, or out-of-bound image.
- Invalid threshold.
- Small ROI or extreme fraction quality warnings.

Current tests:

- Wound analyzer, model, export, quality, and report tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Keep current tool as manual-review legacy MVP.
- Route future wound workflow work through Fiji/ImageJ macro bridge.
- Confirm scratch-area and non-scratch-area field meanings before full wound healing workflow.

## Tool Logic Card: ROI export package

Current implementation:

- tool_id: `image.roi_export_package_v1`
- tool_name: ROI export package
- tool_category: image_export
- current_status: implemented
- implemented_files: `app/labtools/image_analysis/export_package.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_roi_export_package_schema.py`, `tests/labtools/test_fluorescence_export.py`, `tests/labtools/test_wound_export.py`, `tests/ui/test_labtools_image_export_ui.py`
- does_generate_result: yes
- does_write_to_disk: yes

User workflow:

- User runs fluorescence or wound ROI analysis.
- User clicks export and selects a local directory.
- Tool writes manifest, CSV summary, Markdown fragment, and ROI overlay PNG.

Inputs:

- Existing ROI analysis result.
- User-selected output directory.

Outputs:

- `labtools_roi_export_manifest.v1` JSON.
- CSV summary.
- Markdown fragment.
- ROI overlay PNG.

Result meaning:

- Local package for manual review and traceability.
- Not a final report or automated proof.
- Future image backend outputs should preserve this export package discipline: provenance, macro/version metadata, no-overwrite behavior, and manual-review semantics.

Review level:

- Manual review required.

Failure / invalid cases:

- Missing result.
- User cancels directory selection.
- Output path is not a directory.
- Directory is not writable.
- Source image cannot be read for overlay.

Current tests:

- Export package schema, fluorescence export, wound export, and UI export tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm result summary fields and local-path exposure policy.
- Extend manifest/result provenance for Fiji/ImageJ macro bridge outputs before adding future image tools.

## Tool Logic Card: Recipe draft store

Current implementation:

- tool_id: `recipe.draft_store_v1`
- tool_name: Recipe draft store
- tool_category: recipe_draft
- current_status: implemented
- implemented_files: `app/labtools/recipes/recipe_persistence.py`, `app/labtools/recipes/user_recipe_store.py`, `app/labtools/recipes/recipe_models.py`, `app/labtools/ui/recipe_widgets.py`
- test_files: `tests/labtools/test_recipe_persistence.py`, `tests/labtools/test_user_recipe_store.py`, `tests/ui/test_labtools_recipe_persistence_ui.py`
- does_generate_result: yes
- does_write_to_disk: yes

User workflow:

- User confirms a recipe draft.
- User chooses a JSON save path.
- Tool writes a local draft store.

Inputs:

- Confirmed user recipes.
- User-selected JSON path.

Outputs:

- `labtools_recipe_draft_store.v1` JSON payload.

Result meaning:

- Local user recipe draft persistence.
- Not SOP, not a safety protocol, and not automatically adapted to all labs.

Review level:

- Manual SOP/SDS review required.

Failure / invalid cases:

- No user recipe.
- Invalid path.
- Existing file path triggers no-overwrite suffix.
- High-risk keywords blocked.
- Invalid schema on load.

Current tests:

- Recipe persistence, user recipe store, and UI persistence tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm recipe field requirements and safety wording before more templates.

## Tool Logic Card: Recipe import / export

Current implementation:

- tool_id: `recipe.import_export_v1`
- tool_name: Recipe import / export
- tool_category: recipe_draft
- current_status: implemented
- implemented_files: `app/labtools/recipes/recipe_persistence.py`, `app/labtools/recipes/user_recipe_store.py`, `app/labtools/ui/recipe_widgets.py`
- test_files: `tests/labtools/test_recipe_persistence.py`, `tests/ui/test_labtools_recipe_persistence_ui.py`
- does_generate_result: yes
- does_write_to_disk: yes

User workflow:

- User saves confirmed recipes to JSON or loads a compatible JSON.
- Loaded recipes are imported into current memory store.

Inputs:

- Confirmed recipes for save.
- JSON file for load.

Outputs:

- Saved JSON file.
- Imported in-memory recipes.
- Import summary.

Result meaning:

- Local draft import/export utility.
- Not sync, cloud backup, database, or source validation.

Review level:

- Manual review required.

Failure / invalid cases:

- Malformed JSON.
- Schema mismatch.
- Unsafe recipe content.
- Read/write errors.

Current tests:

- Recipe persistence and UI persistence tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Keep current behavior; discuss import preview only if requested.

## Tool Logic Card: Recipe safety category

Current implementation:

- tool_id: `recipe.safety_category_v1`
- tool_name: Recipe safety category
- tool_category: recipe_draft
- current_status: implemented
- implemented_files: `app/labtools/recipes/recipe_persistence.py`, `app/labtools/ui/recipe_widgets.py`, `docs/labtools_schema_index.md`
- test_files: `tests/labtools/test_recipe_persistence.py`, `tests/ui/test_labtools_recipe_persistence_ui.py`
- does_generate_result: yes
- does_write_to_disk: yes

User workflow:

- User sees safety category language in recipe persistence support text and save/load summaries.
- Saved JSON includes the safety category mapping.

Inputs:

- Recipe draft store payload.

Outputs:

- `safety_category` in JSON.
- User-visible category text.

Result meaning:

- Category reminder for draft review state.
- It is not a real chemical safety classification engine.

Review level:

- Manual review required.

Failure / invalid cases:

- Category could be misunderstood if richer recipe templates are added without user confirmation.

Current tests:

- Recipe persistence and UI persistence tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm category labels and whether they should remain internal wording.

## Tool Logic Card: Recipe conflict import behavior

Current implementation:

- tool_id: `recipe.conflict_import_v1`
- tool_name: Recipe conflict import behavior
- tool_category: recipe_draft
- current_status: implemented
- implemented_files: `app/labtools/recipes/user_recipe_store.py`, `app/labtools/recipes/recipe_persistence.py`, `app/labtools/ui/recipe_widgets.py`
- test_files: `tests/labtools/test_recipe_persistence.py`, `tests/ui/test_labtools_recipe_persistence_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User loads a JSON containing a recipe ID that already exists.
- Tool imports conflicting recipe as a new imported copy.
- UI reports conflict count and non-overwrite behavior.

Inputs:

- Loaded recipe list.
- Current in-memory recipe store.

Outputs:

- Imported copy with new ID.
- Conflict count and warning.

Result meaning:

- Non-destructive import behavior.
- No merge or version reconciliation.

Review level:

- Manual review recommended.

Failure / invalid cases:

- Unsafe imported recipe blocks import.

Current tests:

- Recipe persistence and UI conflict tests.

Confirmed by user:

- user_logic_confirmed: yes

Risk:

- risk_level: low
- needs_user_discussion: no
- needs_code整改: no

Recommended next step:

- Keep as-is.

## Tool Logic Card: Experiment template draft

Current implementation:

- tool_id: `experiment.template_draft_v1`
- tool_name: Experiment template draft
- tool_category: experiment_record_draft
- current_status: implemented
- implemented_files: `app/labtools/experiment_templates/template_library.py`, `app/labtools/experiment_templates/template_models.py`, `app/labtools/ui/template_widgets.py`
- test_files: `tests/labtools/test_experiment_templates.py`, `tests/ui/test_labtools_template_ui.py`
- does_generate_result: yes
- does_write_to_disk: no

User workflow:

- User selects a template.
- User edits purpose, groups, reagents, parameters, output files, and notes.
- Tool generates a structured draft and Markdown preview.

Inputs:

- Selected template.
- User-entered draft fields.

Outputs:

- `labtools_experiment_template_draft.v1` draft object.
- Markdown preview.

Result meaning:

- Local structured record draft.
- Not complete ELN, not signed record, not compliance workflow.

Review level:

- Manual review required.

Failure / invalid cases:

- Missing purpose.
- Missing groups, reagents, key parameters, or output files.

Current tests:

- Experiment template and UI template tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm field sets before adding templates or richer record workflows.

## Tool Logic Card: Experiment record draft JSON persistence

Current implementation:

- tool_id: `experiment.record_draft_store_v1`
- tool_name: Experiment record draft JSON persistence
- tool_category: experiment_record_draft
- current_status: implemented
- implemented_files: `app/labtools/experiment_templates/template_persistence.py`, `app/labtools/ui/template_widgets.py`
- test_files: `tests/labtools/test_experiment_template_persistence.py`, `tests/ui/test_labtools_template_ui.py`
- does_generate_result: yes
- does_write_to_disk: yes

User workflow:

- User generates one or more record drafts.
- User chooses a JSON save path or load file.
- Tool saves or loads a local draft store.

Inputs:

- Record drafts.
- User-selected JSON path.

Outputs:

- `labtools_experiment_record_draft_store.v1` JSON.
- Loaded in-memory drafts.

Result meaning:

- Local draft persistence.
- Not complete ELN, signature, permission, or compliance audit.

Review level:

- Manual review required.

Failure / invalid cases:

- No drafts.
- Invalid path.
- Malformed JSON.
- Schema mismatch.
- Blocked high-risk terms.
- Missing manual-review notice.

Current tests:

- Experiment template persistence and UI template tests.

Confirmed by user:

- user_logic_confirmed: partial

Risk:

- risk_level: medium
- needs_user_discussion: yes
- needs_code整改: no

Recommended next step:

- Confirm draft fields and non-ELN wording before any richer record system.

## Tool Logic Card: Automatic cell counting

Current implementation:

- tool_id: `planned.automatic_cell_counting`
- tool_name: Automatic cell counting
- tool_category: planned_image_tool
- current_status: placeholder / planned
- implemented_files: `app/labtools/image_analysis/analysis_task.py`, `app/labtools/image_analysis/result_models.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_image_analysis_task.py`, `tests/ui/test_labtools_status_semantics.py`
- does_generate_result: no
- does_write_to_disk: no

User workflow:

- User may create a task draft only.

Inputs:

- Optional image record for a placeholder task.

Outputs:

- `algorithm_not_available` placeholder.

Result meaning:

- Planned capability only.

Review level:

- Not available for result use.

Failure / invalid cases:

- Any attempt to treat placeholder as a count should be blocked by product policy.

Current tests:

- Placeholder status tests.

Confirmed by user:

- user_logic_confirmed: no

Risk:

- risk_level: high
- needs_user_discussion: yes
- needs_code整改: unknown

Recommended next step:

- Create Tool Logic Card before development.

## Tool Logic Card: Grayscale / ink-value

Current implementation:

- tool_id: `planned.grayscale_ink_value`
- tool_name: Grayscale / ink-value
- tool_category: planned_image_tool
- current_status: placeholder / planned
- implemented_files: `app/labtools/image_analysis/analysis_task.py`, `app/labtools/image_analysis/result_models.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_image_analysis_task.py`, `tests/ui/test_labtools_status_semantics.py`
- does_generate_result: no
- does_write_to_disk: no

User workflow:

- User may create a task draft only.

Inputs:

- Optional image record for a placeholder task.

Outputs:

- `algorithm_not_available` placeholder.

Result meaning:

- Planned capability only.

Review level:

- Not available for result use.

Failure / invalid cases:

- Any output resembling a grayscale quantification result would be out of scope.

Current tests:

- Placeholder status tests.

Confirmed by user:

- user_logic_confirmed: no

Risk:

- risk_level: high
- needs_user_discussion: yes
- needs_code整改: unknown

Recommended next step:

- Create Tool Logic Card before development.

## Tool Logic Card: WB / gel grayscale

Current implementation:

- tool_id: `planned.wb_gel_grayscale`
- tool_name: WB / gel grayscale
- tool_category: planned_image_tool
- current_status: placeholder / planned
- implemented_files: `app/labtools/ui/calculator_widgets.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_labtools_imports.py`, `tests/ui/test_labtools_status_semantics.py`
- does_generate_result: no
- does_write_to_disk: no

User workflow:

- Existing WB calculator only computes loading volumes.
- Image grayscale workflow is not implemented.

Inputs:

- None for gel grayscale result generation.

Outputs:

- None.

Result meaning:

- Planned capability only.

Review level:

- Not available for result use.

Failure / invalid cases:

- Any band detection, normalization, or gel interpretation would be out of scope.

Current tests:

- Status semantics and imports tests verify this is not claimed as implemented.

Confirmed by user:

- user_logic_confirmed: no

Risk:

- risk_level: high
- needs_user_discussion: yes
- needs_code整改: unknown

Recommended next step:

- Create Tool Logic Card before development.

## Tool Logic Card: Automatic ROI

Current implementation:

- tool_id: `planned.automatic_roi`
- tool_name: Automatic ROI
- tool_category: planned_image_tool
- current_status: placeholder / planned
- implemented_files: `app/labtools/image_analysis/roi_models.py`, `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/labtools/test_image_analysis_task.py`, `tests/ui/test_labtools_status_semantics.py`
- does_generate_result: no
- does_write_to_disk: no

User workflow:

- Current workflows require manually entered rectangular ROI.

Inputs:

- None for automatic ROI generation.

Outputs:

- None.

Result meaning:

- Planned capability only.

Review level:

- Not available for result use.

Failure / invalid cases:

- Any automated ROI selection claim would be out of scope.

Current tests:

- Status semantics tests.

Confirmed by user:

- user_logic_confirmed: no

Risk:

- risk_level: high
- needs_user_discussion: yes
- needs_code整改: unknown

Recommended next step:

- Create Tool Logic Card before development.

## Tool Logic Card: Full ELN

Current implementation:

- tool_id: `planned.full_eln`
- tool_name: Full ELN
- tool_category: planned_record_system
- current_status: placeholder / planned
- implemented_files: `app/labtools/experiment_templates/template_models.py`, `app/labtools/ui/template_widgets.py`
- test_files: `tests/ui/test_labtools_template_ui.py`, `tests/ui/test_labtools_status_semantics.py`
- does_generate_result: no
- does_write_to_disk: no

User workflow:

- Current tool only creates local structured record drafts and optional JSON draft persistence.

Inputs:

- None for full ELN.

Outputs:

- None for full ELN.

Result meaning:

- Planned capability only.

Review level:

- Not available for complete record use.

Failure / invalid cases:

- Any implication of signatures, permissions, compliance audit, or team collaboration is out of scope.

Current tests:

- Template and status tests.

Confirmed by user:

- user_logic_confirmed: no

Risk:

- risk_level: high
- needs_user_discussion: yes
- needs_code整改: unknown

Recommended next step:

- Create Tool Logic Card before development.

## Tool Logic Card: Batch image processing

Current implementation:

- tool_id: `planned.batch_image_processing`
- tool_name: Batch image processing
- tool_category: planned_image_tool
- current_status: placeholder / planned
- implemented_files: `app/labtools/ui/image_analysis_widgets.py`
- test_files: `tests/ui/test_labtools_status_semantics.py`
- does_generate_result: no
- does_write_to_disk: no

User workflow:

- Current image tools operate on a single local image and one current ROI result.

Inputs:

- None for batch processing.

Outputs:

- None.

Result meaning:

- Planned capability only.

Review level:

- Not available for result use.

Failure / invalid cases:

- Any batch result table, batch export, or unattended image processing would be out of scope.

Current tests:

- Status semantics tests verify batch image processing is not claimed as implemented.

Confirmed by user:

- user_logic_confirmed: no

Risk:

- risk_level: high
- needs_user_discussion: yes
- needs_code整改: unknown

Recommended next step:

- Create Tool Logic Card before development.
