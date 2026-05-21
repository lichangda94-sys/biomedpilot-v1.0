# UI-B8b3 Vector Redraw Brief

Date: 2026-05-21

## 1. Purpose

This brief defines the production design requirements for redrawing the 74 non App-icon resources extracted in UI-B8b2. The current PNGs are placeholder QA artifacts only. Final resources must be rebuilt as clean SVG assets, then exported to PNG at 24, 32, 48, and 64 px.

App icon, Finder icon, `.icns`, iconset, `Info.plist` icon binding, LaunchServices, and desktop app identity are out of scope and remain deferred to UI-B10.

## 2. Global Production Rules

| Area | Rule |
| --- | --- |
| Source format | Produce clean SVG as the primary asset. |
| PNG exports | Export transparent PNGs at 24, 32, 48, and 64 px from the final SVG or design source. |
| Background | Transparent. Do not preserve board card backgrounds, white mattes, screenshots, labels, or badges from the icon board. |
| Canvas | Use square canvases. Keep glyph alignment consistent within each family. |
| Padding | Use consistent safe-area padding so icons do not touch canvas edges. |
| Stroke | Normalize stroke weight per family; avoid detail that collapses at 24 px. |
| Fill | Use product palette-compatible fills; avoid one-off colors that do not map to tokens. |
| Shadows | Avoid baked shadows unless a future visual style guide explicitly allows them. |
| Light/dark mode | Validate contrast and edge visibility on both light and dark surfaces. |
| Naming | Match `resource_id`; final paths must match `UI_B8b3_icon_replacement_readiness_matrix_20260521.csv`. |

## 3. Modules

Resources:

- `module_bioinformatics`
- `module_meta_analysis`
- `module_labtools`
- `module_settings`

Visual target:

- Clear, module-level symbols that can work in Dashboard cards, side navigation, and module headers.
- Distinct family colors may be used, but the drawing style, stroke weight, corner radius, and padding must stay consistent.

Semantic constraints:

- Module icons are navigation identifiers only.
- Do not imply a module has production-ready execution capability.
- Do not include text labels inside the icon.

Needs redesign:

- All 4 require vector redraw from the board reference.

## 4. Status Icons

Resources:

- `status_testing`
- `status_planned`
- `status_shell_only`
- `status_developer_preview`
- `status_blocked`
- `status_available`
- `status_not_configured`
- `status_failed`
- `status_preflight_only`
- `status_draft`

Visual target:

- Small, high-legibility status symbols suitable for chips and badges.
- Strong distinction between available, testing, planned, blocked, failed, preflight-only, draft, developer preview, and shell-only.

Semantic constraints:

- `testing`, `planned`, `shell_only`, `developer_preview`, `blocked`, `preflight_only`, and `draft` must not look completed or production-ready.
- `available` must be limited to resource availability and must not imply analysis correctness.
- `preflight_only` must not imply formal analysis execution.

Forbidden:

- Green checkmark treatment for incomplete states.
- Celebration, completion, or report-ready metaphors for draft/testing/planned states.
- Ambiguous icons that make `not_configured` look like `failed`.

Needs redesign:

- All 10 require vector redraw and separate status semantic review before replacement.

## 5. Settings Resources

Resources:

- `resource_external_engine`
- `resource_image_analysis_engine`
- `resource_imagej_fiji`
- `resource_pdf_ocr`
- `resource_local_model`
- `resource_cloud_ai`
- `resource_python`
- `resource_r`
- `resource_go`
- `resource_kegg`
- `resource_analysis_package`
- `resource_plotting_package`
- `resource_developer_diagnostics`

Visual target:

- Settings-oriented resource icons that read as configurable capabilities, not active workflow buttons.
- Use restrained technical motifs and avoid implying an installed or connected state.

Semantic constraints:

- ImageJ/Fiji, Cloud AI, local model, PDF/OCR, Python, R, GO, KEGG, and package resources must preserve detect-first and user-triggered install/update semantics.
- Cloud AI must not imply enabled cloud configuration.
- Local model must not imply model availability.

Forbidden:

- Auto-connected cloud symbols.
- Download/install success marks.
- Icons that send ordinary users into developer diagnostics by default.

Needs redesign:

- All 13 require vector redraw and Settings resource-state review before replacement.

## 6. LabTools

Resources:

- `labtools_general_calculator`
- `labtools_reagent_preparation`
- `labtools_experiment_modules`
- `labtools_cell_experiments`
- `labtools_protein_experiments`
- `labtools_nucleic_acid_experiments`
- `labtools_immuno_absorbance`
- `labtools_ihc`

Visual target:

- Friendly but precise lab workflow icons for the LabTools IA shell.
- General calculator, reagent preparation, and experiment modules must be visually distinct as first-level LabTools entries.

Semantic constraints:

- Do not present cell/protein/nucleic acid/immuno/IHC categories as LabTools homepage first-level entries.
- Do not imply inventory system, cloud collaboration, LAN sharing, or rewritten calculation engines.
- Do not mix WB, PCR, ELISA, MTT, BCA, or SDS-PAGE into the general calculator concept.

Needs redesign:

- All 8 require vector redraw.

## 7. Result / Report / Export

Resources:

- `result_overview`
- `result_chart`
- `result_table`
- `result_statistics`
- `result_summary`
- `report_generate`
- `report_template`
- `export_result`
- `export_pdf`
- `export_excel`
- `export_csv`
- `export_archive`
- `share_result`
- `result_clear`

Visual target:

- Clear result, report draft, and export action icons for a gated shell.
- Distinguish preview, draft, export format, archive, share, and clear operations.

Semantic constraints:

- Icons must not imply formal report-ready packages, computed final results, or enabled export pipelines.
- `report_generate` and `report_template` must remain draft/report-template semantics until report production is approved.
- Export icons are resource preparation only in UI-B8b3.

Forbidden:

- Final seal, completed package, or automatic share metaphors.
- Fake chart/result implications.
- Visual treatment that looks like enabled production export.

Needs redesign:

- All 14 require vector redraw and Result / Report / Export gating review before replacement.

## 8. Bioinformatics Page Icons

Resources:

- `bio_page_project_home`
- `bio_page_data_source`
- `bio_page_data_check_preparation`
- `bio_page_group_design`
- `bio_page_analysis_tasks`
- `bio_page_result_report`
- `bio_page_report_export`
- `bio_page_settings_resources`
- `bio_page_project_logs`

Visual target:

- Seven main-flow plus two auxiliary Bioinformatics page icons.
- Use consistent Bioinformatics visual language and enough shape distinction for flow navigation.

Semantic constraints:

- Page icons are IA markers only.
- Do not imply DEG, GSEA, survival, clinical association, report export, or formal result generation is enabled.
- Result & Report and Report Export must preserve shell/gated semantics.

Needs redesign:

- All 9 require vector redraw.

## 9. Meta Page Icons

Resources:

- `meta_page_project_home`
- `meta_page_question_meta_type`
- `meta_page_search_strategy`
- `meta_page_import_deduplication`
- `meta_page_screening`
- `meta_page_fulltext_extraction`
- `meta_page_quality_assessment`
- `meta_page_analysis_tasks`
- `meta_page_result_report`
- `meta_page_report_export`

Visual target:

- Meta Analysis flow icons with consistent purple visual language.
- Search, deduplication, screening, full text, extraction, quality assessment, analysis, result/report, and export must remain distinct.

Semantic constraints:

- Do not imply production-grade systematic review automation.
- AI suggestion must remain suggestion/assistant semantics if represented later.
- Network Meta remains planned and must not be visualized as an active production path.

Needs redesign:

- All 10 require vector redraw.

## 10. Empty States

Resources:

- `empty_project`
- `empty_result`
- `empty_missing_resource`
- `empty_blocked`
- `empty_shell_only`
- `empty_preflight_only`

Visual target:

- Low-pressure empty-state illustrations with clear status meaning.
- Larger than normal icons, but still compatible with the same visual system.

Semantic constraints:

- `empty_result` must not imply a hidden formal result exists.
- `empty_missing_resource` must point to configuration/resource detection, not failure.
- `empty_shell_only` and `empty_preflight_only` must remain honest about limits.

Forbidden:

- Completed results, formal report packets, or success imagery.
- Error severity inflation for planned/shell-only states.

Needs redesign:

- All 6 require vector or illustration redraw before active use.

## 11. Figma / Design Tool Recommendation

If the source Figma file is available, final production should use Figma component frames named by `resource_id`. Export should record the Figma node ID in a future manifest before active replacement. If only the PNG boards are available, redraw manually from the board reference and treat all B8b2 placeholder PNGs as visual references only.
