# Module Boundary Contract

This contract defines the current BioMedPilot boundaries for shared medical
vocabulary, Bioinformatics dataset-source workflows, and Meta Analysis
literature workflows. It is a guardrail for new work; it does not migrate
existing code or change runtime behavior.

## Overall Principles

- `app/shared/` owns common query-intelligence interfaces, lightweight registry
  fallback, context filtering, and shared data structures.
- Bioinformatics owns local data import, GEO/GSE, TCGA/GDC, GTEx, data
  recognition, standardization, analysis tasks, results, and reports.
- Meta Analysis owns PubMed, Web of Science, Embase, CNKI, NBIB/RIS/CSV,
  Zotero/EndNote import, deduplication, screening, extraction, quality
  assessment, statistics, and reports.
- Bioinformatics must not display PubMed, PICO/PICOS, or literature-search UI.
- Meta Analysis must not display GEO/GSE, TCGA/GDC, or GTEx dataset-source
  candidates.

## Shared Boundary

Allowed shared locations:

- `app/shared/search_context.py`
- `app/shared/query_intelligence/medical_terms/`
- Optional external `data/medical_terms/` assets supplied by
  `dev/shared-vocabulary`
- Common medical vocabulary interfaces and fallback lookup
- Chinese-to-English medical term mapping
- Context-specific filtering for Bioinformatics and Meta Analysis

`stable/mainline` must not require bundled `data/medical_terms` assets to start
the app or run Bioinformatics recognition. Full vocabulary data, generated
indexes, coverage reports, and vocabulary quality gates belong on
`dev/shared-vocabulary`.

Forbidden shared behavior:

- Direct GEO, TCGA/GDC, or GTEx download/execution logic
- Direct PubMed, Web of Science, CNKI, or Embase search execution logic
- Bioinformatics-only UI copy
- Meta Analysis-only UI copy

Shared code may know context names such as `bioinformatics` and
`meta_analysis`, but it must keep that knowledge as filtering policy and common
contracts, not module-specific workflow execution.

## Bioinformatics Boundary

Allowed Bioinformatics responsibilities:

- GEO/GSE dataset search and candidate registration
- TCGA/GDC project candidate mapping
- GTEx normal tissue reference candidate mapping
- Local data import
- Data recognition
- Standardization and readiness checks
- Bioinformatics analysis tasks
- Bioinformatics result browsing and reporting
- Reading shared medical vocabulary
- Using `BIOINFORMATICS_SEARCH_CONTEXT`

Forbidden Bioinformatics responsibilities:

- PubMed literature search UI
- PICO/PICOS literature-search workflow
- NBIB/RIS/Zotero/EndNote literature import
- Meta Analysis screening, extraction, quality, or statistics service calls

Bioinformatics may keep negative guard metadata such as
`pubmed_query_candidates_removed` when that metadata proves literature-search
candidates were removed from the Bioinformatics context.

## Meta Analysis Boundary

Allowed Meta Analysis responsibilities:

- PubMed, Web of Science, Embase, and CNKI search strategies
- PICO/PICOS protocol fields
- Literature import
- Deduplication
- Screening
- Extraction
- Quality assessment
- Meta-analysis statistics
- Reporting and publication export
- Reading shared medical vocabulary
- Using `META_ANALYSIS_SEARCH_CONTEXT`

Forbidden Meta Analysis responsibilities:

- GEO/GSE dataset candidates
- TCGA/GDC project candidates
- GTEx tissue candidates
- Bioinformatics recognition workflow calls
- Bioinformatics standardization workflow calls
- Bioinformatics analysis task center calls

Meta Analysis may contain audit or release-guard copy that mentions
Bioinformatics only to protect scope boundaries. That copy must not become a
user-facing Bioinformatics feature entry inside Meta Analysis.

## Legacy Directories

The following directories are historical snapshots and are not part of the
current mainline runtime path:

- `app/bioinformatics/legacy/`
- `app/meta_analysis/legacy/`

Mainline code must not import:

- `app.bioinformatics.legacy.literature_cli`
- `app.bioinformatics.legacy.literature_gui`
- `app.meta_analysis.legacy.geo_readiness`

Current Bioinformatics mainline still has approved compatibility adapters to
legacy GEO processing components. Those bridges are separate from the legacy
literature files and are not changed by this contract.

Legacy code can remain in place for audit and recovery until a separate archive
or deletion stage is approved. New feature work must target the mainline module
directories listed above.

## Future Meta Search Directory

Do not create `app/meta_analysis/search/` in this stage. If Meta retrieval grows
beyond service-level PubMed validation and protocol query drafts, create that
directory in a separate migration stage and move Meta-specific search strategy
builders and retrieval clients there. That directory should remain Meta-owned
and must not call Bioinformatics retrieval adapters.

## Shared Literature Search

Do not add `app/shared/literature_search/` yet. It should be introduced only if
a future requirement proves that multiple product modules need the same
literature-search client. Until then, literature retrieval remains a Meta
Analysis responsibility.
