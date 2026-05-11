# Mainline / Shared Vocabulary Boundary

## Goal

`stable/mainline` is the stable application trunk for UI, workflow state, project
navigation, Bioinformatics data recognition, and cross-module service
contracts. Shared vocabulary expansion is developed on
`dev/shared-vocabulary`.

## What Mainline Keeps

- Public query-intelligence interfaces under `app/shared/query_intelligence/`.
- Lightweight registry fallback so Bioinformatics and Meta Analysis can run
  without bundled vocabulary assets.
- Contract tests that verify context boundaries, local-model audit behavior, and
  missing-vocabulary fallback.
- Optional lookup hooks that can use external `data/medical_terms` assets when a
  vocabulary branch or packaged build supplies them.

## What Moves To `dev/shared-vocabulary`

- `data/medical_terms/` vocabulary assets and generated indexes.
- Medical vocabulary coverage and reference checklist reports.
- Vocabulary build/audit scripts.
- Domain-specific vocabulary tests and quality gates.
- Shared medical vocabulary stage reports.

## Runtime Contract

Mainline must not require `data/medical_terms` to start the desktop app, render
Bioinformatics pages, run data recognition, or generate Meta Analysis search
drafts. If external vocabulary assets are absent, lookup falls back to the
small in-code biomedical registry.

All application callers should enter vocabulary through:

- `lookup_medical_terms(query, target_context=...)`
- `default_vocabulary_providers()`
- custom `MedicalVocabularyProvider` implementations when a packaged or
  branch-local vocabulary module is available

The default provider order in mainline is:

1. external Chinese overrides
2. external runtime medical terms index
3. mainline fallback registry

Vocabulary branches may provide richer assets at the existing optional paths:

- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/mini_medical_terms_index.json`

The mainline interface must treat these files as optional enhancements.

## Branch Workflow

1. UI and Bioinformatics recognition work continues on `stable/mainline`.
2. Vocabulary data and coverage work happens on `dev/shared-vocabulary`.
3. Vocabulary branches should regularly rebase or refresh from mainline to keep
   the interface current.
4. Do not merge vocabulary data back into mainline unless that packaging policy
   is explicitly changed.
