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
6. Analysis Preflight / Analysis-ready Dataset / Basic Testing Meta Analysis / Result Artifacts
7. Reporting Test Summary / PRISMA Summary / Formal Markdown/HTML/DOCX Report Draft / Reproducibility Exports

## Implemented Testing Capabilities

- Literature Import supports NBIB / RIS / CSV smoke testing and registers imported literature records.
- Prepare Screening reads Literature Import output and writes normalized screening-ready records.
- Duplicate Review detects candidate duplicate groups and supports minimal manual deduplication decisions.
- Screening creates a title/abstract screening queue and supports minimal include / exclude / maybe decisions.
- Full-text and Quality workflows support testing registries, full-text exclusion CSV export, quality tool registry, and quality assessment table export.
- Extraction creates an extraction pool from included screening records and now supports testing-level structured ExtractionRecord save, validation, CSV export, and advanced method outcome structures for prevalence, correlation, and diagnostic basic data.
- Analysis runs readiness preflight, builds testing-level analysis-ready datasets from structured extraction records, supports basic testing pooled effects, prevalence / incidence proportion effects, Fisher z correlation effects, diagnostic basic 2x2 metrics, subgroup analysis, leave-one-out sensitivity analysis, basic Egger publication-bias testing, and exports forest/funnel plot PNG plus result table CSV.
- Reporting exports the older testing Markdown summary, testing PRISMA flow numbers, a formal Markdown/HTML/DOCX report draft, advanced method and advanced add-on summaries, supplementary CSV tables, a figure package ZIP, project snapshot metadata, and a reproducibility package ZIP; these are testing outputs, not production publication packages.

## Not Implemented Yet

- Funnel plots, subgroup analysis, sensitivity analysis, and publication bias analysis.
- Production-level statistical validation, advanced diagnostic bivariate / HSROC models, network meta-analysis, meta-regression, trim-and-fill, and publication-ready result interpretation.
- PRISMA diagram generation, production Word/PDF reports, and publication-ready report packages.
- OCR, PDF table extraction, and automated full-text data extraction.
- Production risk of bias, GRADE, and related evidence-certainty workflow.
- AI-assisted review and extraction.
- Multi-reviewer adjudication, team workflow, and production audit trail.

## Why This Cannot Be Marked Production

- The current Analysis step has a basic testing statistics core, several advanced method MVP calculations, and common add-on analyses, but it is not production-grade statistical software.
- The current Reporting step exports Markdown/HTML/DOCX testing drafts and ZIP packages; production Word/PDF reporting is not complete, and PDF remains a placeholder.
- ExtractionRecord form integration, analysis-ready dataset builder, basic pooled effects, forest plot PNG, and result table CSV exist at testing level only.
- Screening and Duplicate Review provide minimal testing decisions, not a complete systematic review adjudication workflow.
- Full-text, quality, publication export, and reproducibility package workflows are testing-level only.

## Next Priority

The next implementation priority is AI-assisted Review, with strict human confirmation and no direct AI overwrite of formal data.
