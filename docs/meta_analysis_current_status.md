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
6. Analysis Preflight / Analysis-ready Dataset / Basic Testing Meta Analysis
7. Reporting Test Summary

## Implemented Testing Capabilities

- Literature Import supports NBIB / RIS / CSV smoke testing and registers imported literature records.
- Prepare Screening reads Literature Import output and writes normalized screening-ready records.
- Duplicate Review detects candidate duplicate groups and supports minimal manual deduplication decisions.
- Screening creates a title/abstract screening queue and supports minimal include / exclude / maybe decisions.
- Extraction creates an extraction pool from included screening records and now supports testing-level structured ExtractionRecord save, validation, and CSV export.
- Analysis runs readiness preflight, builds testing-level analysis-ready datasets from structured extraction records, and supports basic testing pooled effects.
- Reporting exports a testing Markdown summary from Analysis preflight only; it is not a formal report.

## Not Implemented Yet

- Forest plots, funnel plots, subgroup analysis, sensitivity analysis, and publication bias analysis.
- Production-level statistical validation, advanced methods, and publication-ready result interpretation.
- PRISMA formal report generation, Word/PDF reports, and publication-ready report packages.
- Full-text PDF management and full-text screening.
- Risk of bias, quality assessment, GRADE, and related evidence-certainty workflow.
- AI-assisted review and extraction.
- Multi-reviewer adjudication, team workflow, and production audit trail.

## Why This Cannot Be Marked Production

- The current Analysis step has a basic testing statistics core, but it is not production-grade statistical software.
- The current Reporting step exports a test summary only.
- ExtractionRecord form integration, analysis-ready dataset builder, and basic pooled effects exist at testing level only.
- Screening and Duplicate Review provide minimal testing decisions, not a complete systematic review adjudication workflow.
- Full-text, quality assessment, publication export, and formal reproducibility packages are not complete.

## Next Priority

The next implementation priority is Figure & Result Table MVP. That phase should generate a basic forest plot and CSV result table from `analysis_result`.
