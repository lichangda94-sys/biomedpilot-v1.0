# Stage Bio-Search-3 Disease-Aware Dataset Search

## Summary

Bioinformatics Chinese topic search now consumes shared medical vocabulary
disease terms before building GEO/GSE queries. Disease-aware queries are the
primary executable drafts; broad expression-only drafts remain blocked until a
user provides a disease or tissue topic.

## Behavior

- `脑胶质瘤` produces GEO query terms containing `glioma` and `glioblastoma`.
- The primary GEO query combines disease terms, expression platform terms,
  `GSE[ETYP]`, and `Homo sapiens[Organism]`.
- TCGA/GDC candidates render as project rows with `project_id`,
  `project_name`, `primary_site`, `disease_type`, and `mapping_status`.
- GTEx candidates render as normal reference rows with `tissue`,
  `tissue_detail`, `role=normal_reference`, and `mapping_status`.
- Bioinformatics UI text is scoped to GEO/GSE, TCGA/GDC, GTEx, and local data.

## Guardrails

- When no disease term is recognized, GEO online search is blocked by the broad
  query guard.
- Meta/literature database wording must not appear in the Bioinformatics search
  page.
- GTEx online failures are converted to user-facing warnings and keep local
  normal-reference candidates available.
