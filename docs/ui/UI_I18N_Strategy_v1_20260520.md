# UI I18N Strategy v1

Date: 2026-05-20

Status: current i18n strategy draft for UI-B9 and earlier semantic gates

Scope: UIShell / Bioinformatics / Meta Analysis / LabTools / Settings / Reports / Exports

## 1. Strategy

The first rebuilt UI can remain Chinese-first. It must still reserve i18n key boundaries and semantic status keys before major page implementation.

Do not begin i18n with search-and-replace translation. Do not translate report templates by replacing literal strings in generated Markdown.

## 2. Key Naming Groups

Required initial groups:

- `brand.*`
- `nav.*`
- `module.*`
- `feature.status.*`
- `analysis.status.*`
- `result.semantic.*`
- `bio.warning.*`
- `meta.ai_suggestion.*`
- `labtools.term.*`
- `report.status.*`
- `report.action.*`
- `export.*`
- `settings.resource.*`
- `developer_diagnostics.*`

## 3. Brand Variables

| key | intended value | rule |
|---|---|---|
| `brand.visible.zh` | `萤火虫` | Visible Chinese primary brand after confirmation. |
| `brand.visible.en` | `Firefly` | Visible English primary brand after confirmation. |
| `brand.subtitle.zh` | `BioMedPilot / 医研智析` | Product lineage/subtitle. |
| `brand.technical_name` | `BioMedPilot` | Bundle/executable technical name until UI-B10 decision. |
| `brand.report_title` | derived by report template | Never hardcode future report title directly in code. |

The visible brand, technical bundle name, and report title are separate variables.

## 4. Navigation and Module Keys

Initial keys:

- `nav.dashboard`
- `nav.bioinformatics`
- `nav.meta_analysis`
- `nav.labtools`
- `nav.settings`
- `nav.test_feedback`
- `nav.about`
- `module.bioinformatics.name`
- `module.meta_analysis.name`
- `module.labtools.name`
- `module.settings.name`

Navigation tests should prefer nav keys, route keys, objectName, and page_key over literal localized labels.

## 5. Status and Result Semantics

Function state must not be inferred from localized button text.

Required status keys:

- `feature.status.testing`
- `feature.status.planned`
- `feature.status.shell_only`
- `feature.status.developer_preview`
- `feature.status.blocked`
- `feature.status.available`
- `feature.status.not_configured`
- `feature.status.missing`
- `feature.status.failed`
- `analysis.status.preflight_only`
- `analysis.status.blocked_missing_resolver`
- `analysis.status.blocked_missing_result_schema`
- `result.semantic.imported_external_result`
- `result.semantic.formal_computed_result`
- `result.semantic.testing_level`
- `result.semantic.draft`

Bioinformatics-specific required warning:

- `bio.warning.tcga_gtex_no_auto_merge`

Rule: `preflight-only`, `testing-level`, `developer-preview`, and `imported-external-result` must never be localized into wording that implies a completed formal analysis.

## 6. Bioinformatics I18N Rules

Keep official source names:

- GEO
- TCGA
- GTEx
- GO
- KEGG
- Reactome

Required keys:

- `bio.page.project_home`
- `bio.page.data_source`
- `bio.page.data_check_preparation`
- `bio.page.group_design`
- `bio.page.analysis_tasks`
- `bio.page.result_report`
- `bio.page.report_export`
- `bio.page.settings`
- `bio.page.logs_technical_details`
- `bio.action.run_preflight`
- `bio.action.generate_input_package`
- `bio.report.disclaimer.testing_summary_only`

Before B8.1, button labels must be driven by gated semantic states. Do not expose formal DEG/GSEA/survival/clinical association/report-ready actions.

## 7. Meta Analysis I18N Rules

Meta type keys:

- `meta.type.binary_outcome_meta`
- `meta.type.continuous_outcome_meta`
- `meta.type.survival_outcome_meta`
- `meta.type.prevalence_incidence_meta`
- `meta.type.diagnostic_accuracy_meta`
- `meta.type.exposure_disease_risk_meta`
- `meta.type.biomarker_expression_difference_meta`
- `meta.type.correlation_meta`
- `meta.type.prognostic_factor_meta`
- `meta.type.dose_response_meta`
- `meta.type.network_meta_analysis_planned`

Rules:

- Network Meta is planned only.
- PICO, PECO, PICOS remain acronyms with localized explanation.
- `meta.ai_suggestion.label` must mean AI-assisted suggestion.
- `meta.ai_suggestion.disclaimer` must state that AI does not produce automatic conclusions.
- Search/screening/extraction/quality/report terms need a methods glossary.

## 8. LabTools I18N Rules

Required term keys:

- `labtools.term.general_calculators`
- `labtools.term.reagent_preparation`
- `labtools.term.experiment_modules`
- `labtools.term.materials_record`
- `labtools.term.western_blot`
- `labtools.term.bca`
- `labtools.term.sds_page`
- `labtools.term.mtt`
- `labtools.term.cck8`
- `labtools.term.alamarblue`
- `labtools.term.imagej_fiji`
- `labtools.term.ihc`

Rules:

- `LabTools` is not `Labors`.
- Western Blot, BCA, SDS-PAGE, MTT, CCK-8, AlamarBlue, ImageJ/Fiji are stable technical terms.
- ImageJ/Fiji is an external engine name and should not be translated.
- Formula, units, reagent templates and preparation records require parameterized strings, not sentence concatenation.

## 9. Report and Export I18N

UI i18n and report-template i18n are separate.

Report templates should accept:

- `language`
- `brand`
- `module`
- `status`
- `result_semantics`
- `terminology_profile`
- `provenance`

Rules:

- Markdown report draft is not report-ready.
- Default export filenames should use ASCII-safe slugs.
- Localized titles can appear in UI and report content.
- Medical, statistical and experimental terms go through terminology tables.
- Figure titles, captions, limitations and provenance sections need template-level keys.

## 10. Test Migration Strategy

High-risk tests should migrate from literal localized copy to:

- objectName
- page_key
- nav key
- module id
- button role
- status enum
- message code
- result semantics
- report manifest fields

Keep a small set of locale snapshot tests after semantic tests are stable. Do not let old Chinese copy snapshots preserve the old IA.

## 11. UI-B9 Acceptance Criteria

UI-B9 can pass when:

- Key naming rules exist in code or documented registry.
- Critical status/result semantics are not text-only.
- Navigation and module tests can assert semantic identifiers.
- Report/export semantics are separated from localized wording.
- The first UI remains Chinese-first only by choice, not because keys are impossible.
