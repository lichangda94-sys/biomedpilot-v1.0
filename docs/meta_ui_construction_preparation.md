# Meta Analysis UI Construction Preparation

Current status: Developer Preview / testing. This document is the preparation checklist before building or polishing the desktop UI. It is not a production design specification.

## Construction Sequence

1. Workflow shell and navigation
2. Literature import and diagnostics
3. Duplicate review and literature library
4. Screening and full-text eligibility
5. Extraction and quality assessment
6. Analysis setup and results
7. Reporting, PRISMA, exports, and reproducibility

## Reusable Page States

| Step | Page State | UI Readiness | Priority |
|---|---|---:|---:|
| Workflow Dashboard | `workflow_dashboard_state_from_project` | ready for layout | P0 |
| Protocol / Research Question | `protocol_page_state_from_project` | ready for form layout | P1 |
| Literature Import / Diagnostics | `literature_import_wizard_state_from_project` | ready for wizard layout | P0 |
| Literature Library / Duplicate Review | `literature_library_state_from_project` | needs table design | P0 |
| Screening / Full-text Eligibility | `screening_page_state_from_project` | ready for record review layout | P1 |
| Extraction | `simplified_extraction_state_from_project` | needs high-attention form design | P0 |
| Quality Assessment | `quality_state_from_project` | needs form design | P0 |
| Analysis Setup / Results | `analysis_setup_state_from_project` | ready for setup-run-explain layout | P1 |
| Reporting / PRISMA / Exports | `reporting_prisma_trace_state_from_project` | ready for export layout | P1 |

## Global UI Constraints

- Keep Meta Analysis labeled Developer Preview / testing.
- Do not modify Bioinformatics while constructing Meta UI.
- UI calls service/page-state APIs; do not put business logic directly in widgets.
- No automatic PDF download, OCR, institutional full-text access, production PDF, or production/open labels.
- Generated sample project outputs stay in temporary project directories.

## High-Risk UI Areas

- Extraction: highest user-friction page; field errors must point to exact fields, and users must not edit JSON directly.
- Quality Assessment: needs clear NOS / QUADAS-2 / RoB2 domain grouping and non-forced overall judgement suggestion.
- Literature Library / Duplicate Review: merge preview must be visible before reviewer decisions; green duplicate status only means no obvious duplicate risk.
- Literature Import: file picker should be primary, manual path entry secondary; diagnostics need plain-language warning labels.

## Acceptance Checks

- Every visible step shows current status, input, output, warning meaning, and next step.
- Missing artifacts show empty/warning states, not tracebacks.
- Extraction and Quality pages support manual user entry without editing JSON.
- Analysis page distinguishes setup, preflight, dataset, run result, advanced methods, and applicability warnings.
- Reporting page distinguishes test summary, formal Markdown, HTML/DOCX testing exports, simplified PRISMA SVG, and PDF placeholder.
- All UI text keeps Developer Preview / testing visible.

## Suggested First UI Slice

Build a narrow vertical slice first:

1. Workflow Dashboard
2. Literature Import diagnostics panel
3. Literature Library table with duplicate-risk tags
4. Extraction single-study entry form
5. Quality single-study form
6. Analysis setup summary
7. Reporting export summary

This slice is enough for internal beta usability testing before expanding each page into a full production-grade interface.
