# Bioinformatics Vocabulary Integration Audit

## Scope

This audit covers the current main workspace at `/Users/changdali/Documents/BioMedPilot`.
It does not use `/Users/changdali/Documents/BioMedPilot-vocab` as a development
source and does not introduce a literal `Vocabulary/` directory.

The active shared medical vocabulary sources are:

- `data/medical_terms/`
- `app/shared/query_intelligence/medical_terms/`
- `scripts/update_medical_term_index.py`
- `scripts/audit_medical_vocabulary_coverage.py`
- `tests/shared/`

## Current Integration Status

Bioinformatics Chinese research-topic search is integrated with the shared
medical vocabulary through `build_search_translation_draft(...,
target_context="bioinformatics")`, which calls `lookup_medical_terms(...,
target_context="bioinformatics")`. The Bioinformatics query adapter consumes the
draft and emits GEO, TCGA/GDC, and GTEx-oriented search artifacts.

Confirmed shared-vocabulary fields in the Bioinformatics path include:

- `disease_terms_en`
- `mesh_terms`
- `abbreviations`
- `tissue_terms`
- `tcga_project_candidates`
- `gtex_tissue_candidates`
- `data_modality_terms`

The Bioinformatics query path removes PubMed query candidates and keeps the
output scoped to GEO/GSE, TCGA/GDC, and GTEx. Existing tests confirm this for
`build_bioinformatics_query_strategy`, `QueryUnderstandingLayer`, and the
source router.

## Project Recognition

`app/bioinformatics/project_recognition.py` is not a medical-topic recognizer.
It is a local file and table asset recognizer. It currently uses local structural
rules rather than the shared medical vocabulary:

- file suffixes and GEO container markers
- tabular header detection
- numeric density and integer ratio
- sample-like columns such as `count`, `counts`, `TPM`, and `FPKM`
- embedded annotation columns such as `gene_symbol`, `ENTREZ`, `ENSEMBL`, and
  chromosome fields

This separation is mostly appropriate because file recognition classifies
assets, not research topics. It can distinguish raw count matrices from
normalized expression matrices, and it can mark an expression matrix with
embedded annotation as both expression and platform annotation. A mixed table
containing count, FPKM, and annotation columns is currently classified as a
multi-role `tabular_text_file` with `normalized_expression_matrix` plus
`platform_annotation`.

Risk: the file recognizer duplicates a small data-modality vocabulary locally
(`count`, `counts`, `TPM`, `FPKM`, expression-like names). That is acceptable for
table-shape classification, but it should not become a separate disease or
topic vocabulary. If future recognition starts interpreting diseases, tissues,
or TCGA/GTEx concepts, it should call the shared lookup layer instead of adding
more local medical rules.

## Chinese Topic Search

The topic-search path is correctly vocabulary-backed:

- `app/bioinformatics/retrieval/bio_query_adapter.py` builds a Bioinformatics
  strategy from the shared search translation draft.
- `app/bioinformatics/search_center/query_understanding.py` also uses the
  shared draft and then filters it through the Bioinformatics search context.
- `app/shared/search_context.py` removes PubMed candidates for Bioinformatics.
- TCGA/GDC and GTEx adapters consume project and tissue candidates, not
  literature-search output.

Examples verified in the current workspace:

- `脑胶质瘤` returns GBM/LGG, Brain, `TCGA-GBM`, and `TCGA-LGG`.
- `肺腺癌` returns `TCGA-LUAD` and does not expand to `TCGA-LUSC`.
- generic `lung cancer` returns both `TCGA-LUAD` and `TCGA-LUSC`, which is
  appropriate for a broad lung-cancer input.
- `乳腺癌` returns `TCGA-BRCA`.
- `肝细胞癌` returns HCC/liver cancer terms and `TCGA-LIHC`.
- `食管鳞癌` does not leak thyroid/PTC terms.
- `乳头状甲状腺癌` does not leak ESCC terms.

## matched=True Boundary

There is an important boundary in the shared lookup contract: `matched=True`
does not always mean a disease was recognized. Bioinformatics has already added
guards in the higher-level query strategy:

- `build_bioinformatics_query_strategy()` treats missing disease terms plus
  present data modalities as a broad-query condition and requires confirmation.
- `QueryUnderstandingLayer` sets `search_execution_status` to
  `disease_terms_missing` and suppresses normal GEO candidates when no disease
  terms are present.

The safer downstream disease-recognition test is to inspect:

- non-empty `disease_terms_en`
- non-empty disease-relevant `concept_ids`
- vocabulary-backed `term_sources`, especially `zh_term_overrides` and
  `medical_terms_index.sqlite`
- non-empty `tcga_project_candidates` or `gtex_tissue_candidates`

Risk: the lower-level shared lookup can still produce false disease matches for
short English tokens or modality-only inputs because the runtime matcher uses
substring matching over normalized terms. In the current workspace, examples
such as `read count` and `microarray` can produce unrelated disease terms at the
raw lookup layer. The Bioinformatics strategy handles `表达谱`, unknown Chinese
text, and `counts TPM FPKM` as disease-missing broad-query cases, but the raw
lookup false positives should be fixed in the shared matcher with short-token
guards and regression tests.

## Hardcoded Or Duplicate Logic

Remaining duplication is concentrated in two areas:

- `project_recognition.py` has local structural modality rules for file
  classification. This is acceptable if it remains asset-oriented.
- `search_center/query_understanding.py` supplements TCGA, GTEx, tissue, and
  abbreviation mappings with hardcoded fallback helpers. These overlap with the
  shared vocabulary and should eventually be reduced or replaced by fields from
  `term_lookup` and `SearchTranslationDraft.audit`.

The current overlap is not causing the requested cancer leakage cases in the
tested paths, but it increases maintenance risk because shared vocabulary
updates may not automatically propagate to these fallback helpers.

## Recommendation

Do not create a new `Vocabulary/` directory and do not migrate development back
to the old vocab worktree.

Recommended next step: keep `project_recognition.py` focused on file/table
structure, but refactor `search_center/query_understanding.py` so TCGA, GTEx,
tissue, abbreviation, and disease-detected decisions rely first on
`SearchTranslationDraft.audit["term_lookup"]`. Add shared matcher tests for
short-token modality inputs such as `read count`, `count`, `FPKM`, `TPM`, and
`microarray` so data-modality hits cannot become false disease hits.
