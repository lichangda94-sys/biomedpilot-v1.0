# Stage V1 Medical Vocabulary Worktree Isolation

## Purpose

Stage V1 makes the shared medical vocabulary line a separate development lane.
Vocabulary work must not modify Bioinformatics UI, Meta Analysis UI, or
retrieval execution logic.

## Required Workspace

Use the dedicated vocabulary branch and worktree for vocabulary-line work:

- Branch: `codex/vocab-line-stabilization`
- Worktree: `/Users/changdali/Documents/BioMedPilot-vocab`

The main workspace `/Users/changdali/Documents/BioMedPilot` should remain
available for Bioinformatics and Meta Analysis work.

## Allowed Paths

Vocabulary-line commits may modify only:

- `data/medical_terms/`
- `app/shared/query_intelligence/medical_terms/`
- `tests/shared/test_medical_vocabulary*`
- `docs/stage_*medical_vocabulary*`
- `scripts/update_medical_term_index.py`
- `scripts/audit_medical_vocabulary_coverage.py`

## Forbidden Paths

Vocabulary-line commits must not modify:

- `app/bioinformatics/`
- `app/meta_analysis/`
- GEO, PubMed, TCGA, or GTEx retrieval execution logic
- Bioinformatics UI
- Meta Analysis UI

If a vocabulary change appears to require a forbidden path, stop and split the
work into a separate non-vocabulary stage.

## Pre-Commit Gate

Before every vocabulary-line commit, run:

```bash
git diff --name-only
git status --short --untracked-files=all
```

The output must contain only allowed vocabulary-line paths.

Then run:

```bash
python3 -m pytest tests/shared/test_medical_term_index_runtime_strategy.py tests/shared/test_medical_term_lookup.py tests/shared/test_medical_vocabulary_coverage.py tests/shared/test_medical_vocabulary_systematic_coverage.py tests/shared/test_query_intelligence_service.py -q
python3 -m compileall -q app app/shared tests/shared scripts
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

If the work touches coverage audit behavior, also run:

```bash
python3 scripts/audit_medical_vocabulary_coverage.py
```

If the work touches optional full-index construction, also run:

```bash
python3 scripts/update_medical_term_index.py --help
```

## Development Rules

- Expand vocabulary from audit gaps, not ad hoc intuition.
- Add or update shared vocabulary tests with every expansion.
- Keep Bioinformatics and Meta Analysis context filtering intact.
- Treat forbidden leakage as a release blocker.
- Fix short-token or cross-domain false positives with tests before changing
  vocabulary data.
