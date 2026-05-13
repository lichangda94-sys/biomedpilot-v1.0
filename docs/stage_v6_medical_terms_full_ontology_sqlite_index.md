# Stage V6 Medical Terms Optional SQLite Index

## Goal

Stage V6 adds an optional sqlite medical terms index without making it a runtime
requirement. The current stable mini vocabulary JSON path remains intact.

## Why Optional

The full ontology sources are large and may require separate download,
licensing, and build workflows. BioMedPilot must continue to work when
`data/medical_terms/medical_terms_index.sqlite` is missing, invalid, or built
from only the project mini vocabulary.

## SQLite Schema

The sqlite index uses schema version
`biomedpilot.medical_terms.sqlite.v6` and includes:

- `ontology_terms`
- `ontology_synonyms`
- `ontology_crossrefs`
- `ontology_search_index`
- `ontology_build_metadata`

The runtime validates `ontology_build_metadata.schema_version` before reading
the index.

## Build Command

```bash
python3 scripts/update_medical_term_index.py
```

Optional local ontology files can be passed with `--mondo`, `--doid`, `--ncit`,
`--mesh`, and `--efo`. Network downloads are not runtime behavior; source
download requires the explicit `--download-sources` flag.

## Output Files

- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/medical_terms_index_build_report.json`

## Runtime Strategy

Runtime lookup is sqlite-first if the sqlite file exists and matches the V6
schema. If the sqlite file is missing, unreadable, corrupt, or schema-mismatched,
lookup returns to the existing JSON mini vocabulary path without raising a
user-visible exception.

Load order remains:

1. `zh_term_overrides.json`
2. optional `medical_terms_index.sqlite`
3. `mini_medical_terms_index.json`
4. biomedical registry fallback

## Relationship To Mini Vocabulary

The mini vocabulary remains the stable fallback and package-safe runtime input.
The Stage 2.3 / Stage 2.5 coverage audit remains based on the mini vocabulary
and reference checklists; sqlite availability does not lower or redefine audit
coverage.

Current audit after V6 remains:

- 88 covered
- 0 partial
- 0 missing
- coverage rate 1.000
- weighted coverage rate 1.000

## Explicitly Not Done

- Did not modify Meta Analysis business code.
- Did not actively modify Bioinformatics business code.
- Did not introduce mandatory online ontology download.
- Did not make sqlite the only runtime dependency.
- Did not connect this work to UI.
- Did not change GEO, TCGA/GDC, GTEx, PubMed, WOS, Embase, or CNKI retrieval.

## Ontology Source Status

Importer scaffold exists for MONDO, DOID, NCIt, MeSH, and EFO. In this stage,
no local full ontology source files were present under `data/medical_terms/raw`,
so the generated sqlite index is a **mini-derived sqlite index**, not a complete
MONDO / DOID / NCIt / MeSH / EFO ontology build.

Build report summary:

- build_status: success
- schema_version: `biomedpilot.medical_terms.sqlite.v6`
- fallback_mode: `mini_vocabulary_only`
- index_kind: `mini-derived sqlite index`
- terms_count: 116
- synonyms_count: 1968
- crossrefs_count: 175

## Tests

Validated with:

- `python3 scripts/update_medical_term_index.py`
- `python3 scripts/audit_medical_vocabulary_coverage.py`
- shared sqlite build, runtime strategy, lookup, coverage audit, systematic
  coverage, and query intelligence tests
- `python3 -m compileall app/shared/query_intelligence scripts tests/shared`
- app smoke-test
