# UI Route Contract - Meta Batch 8 Quality Assessment

- branch: `integration/release-bio-c1-ui-shell`
- head: `fc2cdb2028d6d01d1ccdac1906b3d5b2dbc66881`
- scope: Meta mature UIShell Quality Assessment page: reviewer-controlled quality draft, quality summary, and export artifacts.
- rows: `3`
- connected: `3`
- disabled: `0`
- broken: `0`

## Matrix

| contract | UI page | capability | object | status | observed |
| --- | --- | --- | --- | --- | --- |
| `META-QUALITY-SAVE-DRAFT` | Quality Assessment | QualityAssessmentService.create_quality_assessment_draft | `metaSaveRiskOfBiasDraftButton` | `connected` | draft_saved={"assessment_count": 1, "assessment_id": "qa-49937c1b62a7", "report_ready": false, "statistics_run": false, "status": "draft", "tool_name": "ROB2"} |
| `META-QUALITY-EXPORT-DRAFT-ARTIFACTS` | Quality Assessment | QualityAssessmentService.export_quality_assessments_v1_json/export_quality_assessments_v1_csv | `metaSaveRiskOfBiasDraftButton` | `connected` | quality_json_and_csv_exported |
| `META-QUALITY-NO-FORMAL-GRADE-GATE` | Quality Assessment | quality boundary gate | `metaSaveRiskOfBiasDraftButton` | `connected` | formal_quality_gate_closed={"assessment_count": 1, "assessment_id": "qa-49937c1b62a7", "report_ready": false, "statistics_run": false, "status": "draft", "tool_name": "ROB2"} |

## Screenshots

- `quality_assessment`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch8_quality_assessment/01_quality_assessment.png`
- `quality_after_save`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_meta_batch8_quality_assessment/02_quality_after_save.png`
