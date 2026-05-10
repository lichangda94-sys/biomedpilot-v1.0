# Meta UI-06 to UI-18 Implementation Plan

Status: implemented as Developer Preview workspace pages.

Scope:

- UI-06 Dedup Review: already connected to duplicate groups, risk labels, merge preview, and reviewer decision audit.
- UI-07 Exclusion Criteria: project-level exclusion reason library, selected/default/custom reasons, reviewer confirmation only.
- UI-08 Title / Abstract Screening: queue preview, include/exclude/uncertain/needs-review decisions, structured exclusion reason required for exclude.
- UI-09 Full-text Management: full-text queue, PDF binding, parsing entry, full-text management status, and eligibility decision entry.
- UI-10 Manual Extraction: literature -> study unit -> effect row workflow, CSV template/export/import draft actions, no analysis-ready dataset.
- UI-11 AI-assisted Extraction: pending/accepted/rejected suggestion queue; accepted suggestions can only be applied as manual extraction drafts.
- UI-12 Quality Assessment: tool suggestions, draft quality records, user-completed records, CSV export, no automatic GRADE.
- UI-13 Analysis Plan: draft generation from confirmed protocol/extraction/quality and explicit reviewer confirmation.
- UI-14 Statistics: M17 engine entry, disabled until confirmed analysis plan exists, testing-level result preview only.
- UI-15 Figure Results: read existing figure artifacts and standardized results; does not recompute statistics.
- UI-16 PRISMA: collect/export PRISMA summary from real workflow records only.
- UI-17 Report Export: draft/testing Markdown/HTML/DOCX export, no final medical conclusion.
- UI-18 Reproducibility Package: export existing project artifacts through PublicationExportService.

Guardrails:

- No Bioinformatics calls or GEO/GSE/TCGA/GTEx surfaces were added.
- Page construction is read-only for statistics, figures, reports, and reproducibility exports.
- Research judgments stay behind explicit reviewer buttons.
- PRISMA counts are not model-generated and are not advanced by candidate preview alone.
