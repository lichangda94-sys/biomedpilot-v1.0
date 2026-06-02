# UI Route Contract - Meta Batch 7 Full-text & Extraction

- branch: `integration/release-bio-c1-ui-shell`
- head: `fc2cdb2028d6d01d1ccdac1906b3d5b2dbc66881`
- scope: Meta mature UIShell Full-text & Extraction page: fulltext registry, extraction schema selection, manual extraction draft, and disabled placeholder tabs.
- rows: `6`
- connected: `4`
- disabled: `2`
- broken: `0`

## Matrix

| contract | UI page | capability | object | status | observed |
| --- | --- | --- | --- | --- | --- |
| `META-FULLTEXT-OPEN-DESIGN` | Full-text & Extraction | FullTextManagementService.build_registry_from_screening | `metaOpenExtractionDesignButton` | `connected` | fulltext_registry_written |
| `META-EXTRACTION-SAVE-DESIGN` | Full-text & Extraction | ExtractionSchemaRegistryV1Service.save_default_registry/save_schema_selection | `metaSaveExtractionDesignButton` | `connected` | schema_registry_and_selection_written |
| `META-EXTRACTION-CONFIRM-DRAFT` | Full-text & Extraction | ManualExtractionEffectRowService.create_study_unit/create_effect_row | `metaConfirmExtractionButton` | `connected` | draft_extraction_row_written_not_report_ready |
| `META-EXTRACTION-BACK-FULLTEXT` | Full-text & Extraction | UI tab navigation | `metaBackToFulltextButton` | `connected` | returned_to_fulltext_management_tab |
| `META-FULLTEXT-TAB-提取完成核查` | Full-text & Extraction | disabled reason for future tab adapter | `metaFulltextExtractionTab` | `disabled` | disabled_with_reason |
| `META-FULLTEXT-TAB-历史记录` | Full-text & Extraction | disabled reason for future tab adapter | `metaFulltextExtractionTab` | `disabled` | disabled_with_reason |

## Screenshots

- `fulltext_management`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch7_fulltext_extraction/01_fulltext_management.png`
- `extraction_design`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch7_fulltext_extraction/02_extraction_design.png`
- `back_to_fulltext_management`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch7_fulltext_extraction/03_back_to_fulltext_management.png`
