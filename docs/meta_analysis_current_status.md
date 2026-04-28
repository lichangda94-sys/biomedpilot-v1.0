# Meta Analysis Current Status

## Module Positioning

Meta Analysis is currently a Developer Preview / testing module. It is not a production systematic review or pooled meta-analysis application.

No Meta Analysis workflow should be presented as production-ready. Connected features are intended for controlled developer preview testing and workflow stabilization.

## Connected Main Chain

The current testing chain is:

1. Literature Import
2. Prepare Screening
3. Duplicate Review
4. Screening
5. Extraction Pool
6. Analysis Preflight
7. Reporting Test Summary

## Implemented Testing Capabilities

- Literature Import supports NBIB / RIS / CSV smoke testing and registers imported literature records.
- Prepare Screening reads Literature Import output and writes normalized screening-ready records.
- Duplicate Review detects candidate duplicate groups and supports minimal manual deduplication decisions.
- Screening creates a title/abstract screening queue and supports minimal include / exclude / maybe decisions.
- Extraction creates an extraction pool from included screening records.
- Analysis runs readiness preflight only; it does not execute pooled statistics.
- Reporting exports a testing Markdown summary from Analysis preflight only; it is not a formal report.

## Not Implemented Yet

- Formal structured extraction records and extraction form workflow.
- Formal pooled meta-analysis statistics.
- Forest plots, funnel plots, subgroup analysis, sensitivity analysis, and publication bias analysis.
- PRISMA formal report generation, Word/PDF reports, and publication-ready report packages.
- Full-text PDF management and full-text screening.
- Risk of bias, quality assessment, GRADE, and related evidence-certainty workflow.
- AI-assisted review and extraction.
- Multi-reviewer adjudication, team workflow, and production audit trail.

## Why This Cannot Be Marked Production

- The current Analysis step is a preflight check only.
- The current Reporting step exports a test summary only.
- Extraction does not yet provide formal structured extraction records for real statistical analysis.
- Screening and Duplicate Review provide minimal testing decisions, not a complete systematic review adjudication workflow.
- Full-text, quality assessment, publication export, and formal reproducibility packages are not complete.

## Next Priority

The next implementation priority is Structured Extraction Core. That phase should add formal extraction data models, schema registry, validation service, storage service, and tests while preserving the existing extraction_pool workflow.
