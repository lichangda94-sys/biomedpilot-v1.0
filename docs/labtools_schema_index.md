# LabTools Schema Index

日期：2026-05-14

本文档是 LabTools 当前 persistence/export schema 的统一索引。LabTools 仍处于 Developer Preview / testing 状态；以下 schema 均不是生产级、临床级、提交级报告规范，也不替代实验室 SOP、SDS、伦理/安全审核或人工复核。

每个条目都说明用途、主要字段、用户语义、是否可公开分享、是否包含本地路径或路径片段风险，以及它属于草稿、辅助结果还是用户确认的本地持久化文件。

L6E status audit note：普通 LabTools UI 只暴露用户需要理解的本地辅助、草稿、manual-review MVP 和 placeholder 状态；本 schema index 是开发/交接文档，不应被 UI 文案替代为正式报告、完整 ELN、临床建议、production-grade 输出或 SOP。

Tool Logic Retrospective Audit note：本次回顾审计未新增 persistence schema、未修改 schema version、未新增导出格式；`docs/labtools_tool_logic_audit.md` 只记录当前工具使用逻辑与结果语义边界。

Module Architecture Alignment 1 note：本阶段只调整 LabTools 顶层入口和模块占位语义，未新增 persistence schema、未修改 schema version、未新增导出格式。后续实验特异性计算不再长期归入“通用计算器”，但现有 schema / JSON-compatible structure 保持不变。

SDS-PAGE Gel Template Tool 1 note：新增 `labtools_sds_page_gel_template_store.v1`，用于用户录入 SDS-PAGE 配胶模板的本地 JSON 备份/迁移/共享；XLSX 导出仅为本次批量换算结果，不是模板 schema。

## 1. 总览

| Schema / structure | 用途 | 写盘状态 | 用户语义 | 可公开分享 | 本地路径风险 |
| --- | --- | --- | --- | --- | --- |
| `labtools_roi_export_manifest.v1` | fluorescence / wound manual ROI 导出包 manifest | 用户选择导出目录后写盘 | manual-review / semi-quantitative 辅助结果 | 不建议直接公开；需先检查本地审计字段 | manifest 记录 source image name/reference；Markdown fragment 不应包含 raw absolute path |
| `labtools_recipe_draft_store.v1` | 用户确认 recipe draft 本地 JSON store | 用户选择 JSON 路径后写盘 | 用户确认的本地草稿持久化 | 不建议公开；可能包含用户配方、来源标题或备注 | 通常不包含保存路径；可能包含来源 URL/title/accessed_at |
| `labtools_sds_page_gel_template_store.v1` | 用户录入 SDS-PAGE 配胶模板 JSON | 用户选择 JSON 路径后写盘 | 模板备份/迁移/共享，不是通用配方 | 不建议直接公开；需检查来源、备注和实验室内部信息 | 不保存 JSON 文件自身路径；可能包含用户填写的 kit / SOP source 文本 |
| SDS-PAGE calculation `.xlsx` | 本次 SDS-PAGE 批量换算结果 | 用户选择 XLSX 路径后写盘 | 实验辅助计算草稿 | 不建议作为正式记录公开 | 不保存系统路径；可能包含模板来源和用户备注 |
| `labtools_experiment_template_draft.v1` | 单个实验记录结构化草稿 | 默认内存结构；可嵌入 record draft store | 本地结构化草稿，不是 ELN | 不建议公开；需人工去标识和复核 | 不应自动包含 raw path；用户填写的 output files 可能含本地文件名或路径片段 |
| `labtools_experiment_record_draft_store.v1` | 实验记录草稿本地 JSON store | 用户选择 JSON 路径后写盘 | 草稿持久化，不是完整 ELN | 不建议公开；可能包含实验目的、分组、试剂和备注 | 可能包含用户输入的 output file/path 文本 |
| `CalculationRecord` JSON-compatible dict | 计算器结果内存记录 | 当前不自动写盘 | 辅助计算草稿 | 不建议作为正式记录公开 | 不包含系统路径，除非用户输入中带路径 |
| `Recipe` / `RecipeDraft` JSON-compatible dict | recipe model 和用户草稿结构 | model 可序列化；持久化由 recipe draft store 负责 | 配方草稿/参考，不是 SOP | 不建议公开；需检查来源和安全备注 | 可能包含 source URL/title/accessed_at；不应包含保存路径 |

## 2. `labtools_roi_export_manifest.v1`

- Producer：`export_fluorescence_analysis_package()`、`export_wound_healing_analysis_package()`。
- Consumer：LabTools 内部审计、用户手动查看导出包。
- Main fields：`schema_version`、`export_type`、`tool_slug`、`tool_label`、`analysis_mode`、`created_at`、`software_channel`、`algorithm`、`source_image`、`parameters`、`result_summary`、`result`、`output_files`、`review_status`、`safety_note`、`generated_files_count`、`persistence_note`。
- User semantics：手动 ROI / threshold 辅助分析结果，必须人工复核；wound 结果为 semi-quantitative area estimation。
- Public sharing：manifest 是本地审计文件，不建议直接作为公开报告分享。若需要分享，应先检查 source image reference、文件名、备注和所有实验上下文。
- Local path handling：manifest 使用 source image name/reference 和输出文件相对文件名；Markdown fragment 不应包含 raw absolute source path。UI 成功提示可显示用户选择的导出目录，这是本地 UI 反馈，不是报告正文。
- UI persistence behavior：导出只在用户点击“导出当前 ROI 结果”并选择目录后发生；取消目录选择不会写盘且会保留当前分析结果；导出失败显示可读错误且不清空当前结果；同一目录连续导出使用 no-overwrite 文件名策略保留既有文件。
- Boundary：不构成自动图像算法结论、正式实验 SOP、临床诊断或 production-grade 报告。

## 3. `labtools_recipe_draft_store.v1`

- Producer：`save_user_recipe_store()`。
- Consumer：`load_user_recipe_store()`、`UserRecipeStore.import_recipes_with_summary()`。
- Main fields：`schema_version`、`export_type`、`created_at`、`software_channel`、`review_status`、`safety_category`、`recipe_count`、`recipes`、`safety_reviews`、`safety_note`、`persistence_note`。
- Safety category：`routine_buffer_draft` / `user_verified_only` / `requires_lab_sop_review`，表示仅为常规 buffer / reagent 本地草稿，用户复核后使用，仍需实验室 SOP/SDS/试剂说明书审核。
- Recipe fields：`recipe_id`、`name`、`category`、`description`、`stock_concentration`、`default_volume`、`default_volume_unit`、`components`、`preparation_notes`、`safety_notes`、`source_label`、`version`、`review_notice`、`source_url`、`source_title`、`accessed_at`、`user_confirmed`、`edited_by_user`。
- User semantics：用户确认的本地 recipe draft store，便于复用和人工核对。
- Public sharing：不建议公开；可能包含用户自定义配方、来源信息、备注和实验室内部表达。
- Local path handling：store payload 不保存 JSON 文件自身路径；source URL/title/accessed_at 可来自用户手动录入来源。
- Compatibility note：v1 当前没有破坏性要求每个 recipe 必含 `created_at` / `updated_at`；顶层 `created_at` 记录 store 生成时间，来源/导入状态由 `source_*` 字段、`user_confirmed`、`edited_by_user` 和冲突 clone 后的 `user_recipe_imported_<token>` id 表示。
- Boundary：不是正式 SOP，不构成安全操作规范，不自动适配所有实验；不提供危险化学品、高风险合成、动物/人体实验或病毒实验操作方案。使用前需人工确认浓度、pH、储存条件、有效期和危险性。

## 4. `labtools_experiment_template_draft.v1`

- Producer：`create_record_draft()` / `ExperimentRecordDraft.to_dict()`。
- Consumer：`draft_markdown_preview()`、`save_experiment_draft_store()`。
- Main fields：`schema_version`、`draft_id`、`template_id`、`template_name`、`created_at`、`status`、`purpose`、`sample_groups`、`reagents`、`key_parameters`、`output_files`、`notes`、`review_notice`。
- User semantics：本地结构化实验记录草稿，状态必须保持 `draft_manual_review_required`。
- Public sharing：不建议直接公开；可能包含实验目的、样本分组、试剂、参数和备注。
- Local path handling：系统不自动加入 raw path；用户填写的 `output_files` 可能包含本地文件名或路径片段，分享前需人工检查。
- Boundary：不是完整 ELN，不提供权限、签名、合规审计或正式操作规程。

## 5. `labtools_sds_page_gel_template_store.v1`

- Producer：`save_sds_page_gel_template_json()`。
- Consumer：`load_sds_page_gel_template_json()`、`SdsPageGelTemplateStore.import_template()`。
- Main fields：`schema_version`、`export_type`、`created_at`、`software_channel`、`review_status`、`template`、`safety_note`、`persistence_note`、`review_notice`、`context_notice`。
- Template fields：`template_id`、`template_name`、`template_version`、`gel_concentration`、`gel_thickness`、`well_count`、`gel_format_or_note`、`kit_or_sop_source`、`created_at`、`updated_at`、`review_status`、`safety_note`、`resolving_gel_section`、`stacking_gel_section`。
- Section fields：`section_name`、`is_used`、`note`、`components`。
- Component fields：`component_name`、`amount_per_gel`、`unit`、`note`。
- Supported units：`µL`、`mL`、`mg`、`g`。
- User semantics：基于用户录入的试剂盒/实验室模板进行批量换算；模板 JSON 用于备份、迁移或人工分享复核。
- Import behavior：导入前校验 schema；同名或同 `template_id` 冲突时只允许跳过或作为副本导入，不覆盖已有模板。
- Public sharing：不建议直接公开；可能包含试剂盒来源、实验室模板名称、备注、位置、有效期或其它内部信息。
- Local path handling：store payload 不保存 JSON 文件自身路径；`kit_or_sop_source` 和 notes 是用户输入，可能包含本地或内部来源描述。
- Boundary：不内置通用配方，不自动推荐配方，不自动推导胶浓度，不生成配置步骤；结果为实验辅助计算草稿，使用前请按试剂盒说明书和实验室 SOP 人工核对。

## 6. SDS-PAGE calculation `.xlsx`

- Producer：`save_sds_page_gel_calculation_xlsx()`。
- Consumer：用户手动查看本次批量换算结果。
- Workbook sheets：`Summary`、`分离胶`、`浓缩胶`。
- Summary fields：模板名称、模板版本、胶浓度、胶厚度、孔数、胶数量、余量百分比、计算时间、模板来源、人工核对提示、备注。
- Section sheet fields：组分名称、每块胶用量、单位、胶数量、余量百分比、总量含余量、备注。
- User semantics：只导出本次计算结果，不是模板，不是数据库记录，不是报告规范。
- Boundary：XLSX 不写入自动推荐、胶浓度推导、配置步骤、WB 灰度分析或蛋白浓度分析。

## 7. `labtools_experiment_record_draft_store.v1`

- Producer：`save_experiment_draft_store()`。
- Consumer：`load_experiment_draft_store()`。
- Main fields：`schema_version`、`export_type`、`created_at`、`software_channel`、`review_status`、`draft_count`、`drafts`、`draft_reviews`、`source_schema_version`、`safety_note`、`persistence_note`。
- User semantics：用户生成的实验记录草稿本地 JSON store，便于保存和载入继续编辑。
- Public sharing：不建议公开；可能包含实验目的、样本分组、试剂、关键参数、输出文件和备注。
- Local path handling：store payload 不保存 JSON 文件自身路径；`drafts.output_files` 是用户输入，可能包含本地路径片段。
- Boundary：不是完整 ELN、正式实验报告、临床建议或安全操作建议。

## 8. JSON-Compatible Structures Without Write-To-Disk Schema

### `CalculationRecord`

- Producer：LabTools calculators。
- Current persistence：内存结构 / JSON-compatible dict；当前没有用户确认写盘流程。
- Semantics：实验辅助计算草稿，使用前需人工核对单位、移液范围、试剂形式和实验 SOP。
- Boundary：不替代 SOP、临床建议、安全操作规范或正式实验记录。

### `Recipe` / `RecipeDraft`

- Producer：内置 recipe library、用户草稿、手动来源草稿转换。
- Current persistence：单个 model 可 `to_dict()`；正式写盘只通过 `labtools_recipe_draft_store.v1`。
- Semantics：本地参考配方或用户确认草稿，仍需人工核对 SOP、SDS 和试剂说明书。
- Boundary：不保存或生成高风险操作方案，不是正式 SOP。

## 9. Persistence Safety Checklist

当前写盘能力只允许以下用户触发路径：

- ROI export：用户点击“导出当前 ROI 结果”并选择目录。
- Recipe draft store：用户点击“保存用户配方 JSON”并选择路径。
- Experiment record draft store：用户点击“保存记录草稿 JSON”并选择路径。
- SDS-PAGE gel template JSON：用户点击“导出模板 JSON”并选择路径。
- SDS-PAGE calculation XLSX：用户点击“导出本次计算 XLSX”并选择路径。

所有写盘路径必须保持：

- no autosave / 不自动保存；
- no database/history/background project storage；
- no network / AI / local model；
- no silent overwrite；
- user-visible cancel/failure states；
- schema version in saved JSON artifacts；
- draft/manual-review/auxiliary wording；
- no formal report / no complete ELN / no SOP / no clinical / no production-grade claims。
