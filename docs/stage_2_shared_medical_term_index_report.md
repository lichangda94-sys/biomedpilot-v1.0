# Stage 2 Shared Medical Term Index Report

## Goal

Stage 2 establishes a shared BioMedPilot medical term index so Chinese disease recognition is no longer handled by one-off term patches. The shared layer lives under `app/shared/query_intelligence/medical_terms/` and can be consumed by Bioinformatics and Meta Analysis with context-specific output filtering.

## Development-Time Index Builder

`scripts/update_medical_term_index.py` is the development-time preprocessing tool. It can download or read local MONDO, DOID, NCIt, MeSH, and EFO source files, then write a unified optional sqlite index:

`data/medical_terms/medical_terms_index.sqlite`

Runtime application startup does not parse full OWL/OBO/XML files.

## Supported Sources

- MONDO: disease vocabulary, CC BY 4.0.
- DOID: disease fallback vocabulary, CC0 1.0.
- NCIt: oncology terminology, CC BY 4.0.
- MeSH: NLM medical subject headings.
- EFO: experiment factor ontology, Apache 2.0.

UMLS and SNOMED CT are not included by default.

## Runtime Loading Order

1. `zh_term_overrides.json`
2. `medical_terms_index.sqlite`, if present
3. `mini_medical_terms_index.json`
4. `biomedical_term_registry` fallback

The full sqlite index is optional. If it is absent, the built-in mini index remains sufficient for core Stage 2 behavior.

## Package Manifest

`data/package_manifest.json` records `medical_terms_index` as a BioMedPilot shared medical vocabulary, not a Bioinformatics-specific index.

Default package assets:

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`
- `data/medical_terms/license_attribution.md`

Optional enhancement:

- `data/medical_terms/medical_terms_index.sqlite`

## Context Filtering

Bioinformatics context keeps dataset-retrieval fields:

- disease terms
- tissue terms
- data modality terms
- GEO query terms
- TCGA project candidates
- GTEx tissue candidates

Bioinformatics clears PubMed and other literature-search candidates.

Meta Analysis context keeps literature-search fields:

- disease terms
- synonyms
- abbreviations
- MeSH terms
- exposure, intervention, outcome, study design, and publication type terms

Meta Analysis clears GEO query candidates and does not expose TCGA or GTEx mappings. MeSH terms are prioritized for PubMed query drafts.

## Boundaries

- Full ontology download and parsing are development-time operations only.
- Full sqlite is optional and is not required for packaged runtime behavior.
- UMLS and SNOMED CT are not included by default.
- This stage does not implement full TCGA/GTEx online retrieval.
- This stage does not implement Meta multi-database online retrieval.

## Verification

- Related subset: 84 passed.
- `python3 -m compileall -q app app/bioinformatics app/shared tests/bioinformatics tests/shared tests/ui scripts`: passed.
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`: passed.
- `python3 scripts/run_tests.py`: 230 passed.
- `python3 scripts/update_medical_term_index.py --help`: passed.
