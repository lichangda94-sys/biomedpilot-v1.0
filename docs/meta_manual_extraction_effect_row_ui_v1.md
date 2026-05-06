# Meta Manual Data Extraction UI v1

Stage M13 adds a draft-only manual extraction workspace for Meta Analysis.

## Active Service

- Service: `app/meta_analysis/services/manual_extraction_effect_row_service.py`
- Page state: `manual_extraction_effect_row_state_from_project()` in `app/meta_analysis/pages/extraction_page.py`
- Manifest: `extraction/extraction_manifest.json`
- Study units: `extraction/extraction_study_units.json`
- Effect rows: `extraction/extraction_effect_rows.json`
- Evidence refs: `extraction/extraction_evidence_refs.json`
- Validation report: `extraction/extraction_validation_report.json`
- Extraction audit: `extraction/extraction_audit.jsonl`

## Data Structure

The v1 structure is:

1. Literature record
2. Study unit
3. Extraction effect row
4. Source evidence ref

One literature record can contain multiple study units. One study unit can contain multiple candidate effect rows.

Each effect row is a candidate analysis row only. It stores raw group data and reported effect sizes in separate objects.

## Supported First-pass Field Groups

- Binary raw data: group totals and event counts.
- Continuous raw data: group means, SDs, and sample sizes.
- Survival reported effect: HR with 95% CI.
- Diagnostic 2x2: TP / FP / FN / TN.

Other schema types can still use a generic reported-effect or note-only draft structure.

## Governance

The service writes extraction audit and research-governance events for:

- `extraction_row draft_created`
- `extraction_row user_edited`
- `extraction_row marked_missing`
- `extraction_row completed_by_user`
- `extraction_csv exported`
- `extraction_csv imported_as_draft`

`completed_by_user` means the reviewer marked the row complete in the manual extraction workspace. It does not mean the row is analysis-ready.

## Safety Boundaries

- No analysis-ready dataset is created.
- No statistical analysis is run.
- No PRISMA counts are advanced.
- CSV import creates new drafts only.
- CSV conflicts create diagnostics and do not silently overwrite existing rows.
- AI or PDF parsing output remains reference material only and is not written into final extraction values.

## Validation

Validation is currently field-level and testing-oriented:

- Missing required fields produce Chinese diagnostics.
- Required fields missing cannot be marked `valid`.
- Raw group data and reported effect size should not be mixed in one data structure.
- Multiple `primary_effect_candidate` rows under the same study unit produce a warning.
- `analysis_candidate_row_count` is a candidate count only, not an analysis-ready dataset count.

## Current Limitations

- This is a UI/data-layer scaffold, not a production extraction system.
- It does not perform complex CSV merge/overwrite.
- It does not resolve multiple-reviewer extraction conflicts.
- It does not validate every planned M12 schema with production statistical rigor.
