# BioMedPilot Branch Consolidation Plan

Date: 2026-05-10

Scope: branch structure setup and consolidation plan only. No old branch was merged, deleted, rebased, reset, cherry-picked, force-moved, or pushed.

## 1. Stable/Mainline

The requested baseline was `f921786 feat(bio): add explicit online dataset search actions`.

Before branch creation, the audit report was committed as:

- `10e6b3e docs(repo): add branch consolidation audit`

This commit only adds `docs/branch_consolidation_audit.md`; it does not change application code. The new long-lived branches were created from `10e6b3e`, which is `f921786` plus the committed audit report.

Current stable/mainline branch:

- `stable/mainline`
- start commit: `10e6b3e8d50aae6908cca9c65677fba5174ec6a4`

## 2. Development Branch Starts

All target branches currently point to the same commit:

| Branch | Start commit | Purpose |
| --- | --- | --- |
| `dev/shared-vocabulary` | `10e6b3e8d50aae6908cca9c65677fba5174ec6a4` | Shared medical vocabulary, Chinese term mapping, query intelligence, AI Gateway follow-up |
| `dev/meta-analysis` | `10e6b3e8d50aae6908cca9c65677fba5174ec6a4` | Meta Analysis workflows, PICO, literature search/import, screening, extraction, PRISMA/GRADE |
| `dev/bioinformatics` | `10e6b3e8d50aae6908cca9c65677fba5174ec6a4` | Bioinformatics workflows, GEO/TCGA/GTEx, data recognition, readiness, standardization, runners |

## 3. Old Branch Handling Plan

### Shared Vocabulary

- `codex/vocab-line-stabilization`
  - Has one branch-only documentation commit.
  - Candidate for manual review and possible cherry-pick into `dev/shared-vocabulary`.
  - Do not merge the whole branch automatically.

- `codex/medical-vocabulary-main`
- `codex/meta-search-main`
- `codex/meta-search-main-v2`
- `codex/migrate-medical-vocabulary-stage2`
  - Appear already merged or superseded by current stable/mainline.
  - Keep temporarily; do not delete yet.

### Meta Analysis

- `codex/meta-workflow-ui`
  - Review first.
  - Candidate for `dev/meta-analysis` after checking current workspace/navigation behavior.

- `codex/meta-search-ui-main`
  - Review after `codex/meta-workflow-ui`.
  - Candidate for `dev/meta-analysis`, especially PubMed search execution and search draft UI work.
  - Verify module boundaries before integration.

- `codex/ai-gateway-call-isolation-audit`
  - High-risk revert-of-revert branch.
  - Manual review only.
  - Do not directly merge.

### Bioinformatics

- `codex/bio-geo-real-download-test`
  - Review first because it has one branch-only commit.
  - Candidate for selective integration into `dev/bioinformatics` if current stable/mainline lacks the same hardening.

- `codex/bio-search-ui-main`
  - High-risk branch with 30 branch-only commits.
  - Review file by file.
  - Do not merge as a whole branch.

- `codex/bioinformatics-safe-stage2`
  - High-risk old large architecture branch with 61 branch-only commits.
  - Treat as reference material.
  - Do not merge as a whole branch.

- `codex/bio-search-ui-main-legacy`
  - Older Bioinformatics retrieval path.
  - Keep temporarily as reference; likely superseded.

### Likely Archive Later, But Do Not Delete Now

These branches showed no branch-only commits relative to the current stable/mainline during audit and can likely be archived later after worktree checks:

- `codex/bio-chinese-dataset-search-page`
- `codex/bio-search-ui-integrate-main`
- `codex/bio-ui-download-integration`
- `codex/biomedpilot-root`
- `codex/medical-vocabulary-main`
- `codex/merge-latest-app-content`
- `codex/meta-search-main`
- `codex/meta-search-main-v2`
- `codex/migrate-medical-vocabulary-stage2`
- `codex/restore-ui01-login-baseline`

## 4. Recommended Merge / Review Order

1. Keep `stable/mainline` as the packaging-ready integration base.
2. Work on `dev/shared-vocabulary` first:
   - Review `codex/vocab-line-stabilization`.
   - Decide whether to cherry-pick the documentation commit.
3. Work on `dev/meta-analysis` second:
   - Review `codex/meta-workflow-ui`.
   - Then review `codex/meta-search-ui-main`.
   - Treat `codex/ai-gateway-call-isolation-audit` as manual-only.
4. Work on `dev/bioinformatics` third:
   - Review `codex/bio-geo-real-download-test`.
   - Then inspect `codex/bio-search-ui-main` file by file.
   - Use `codex/bioinformatics-safe-stage2` only as reference unless a specific feature is proven missing.
5. After each dev branch integration, run targeted tests and package smoke before merging anything back to `stable/mainline`.

## 5. Branches Forbidden From Direct Merge

Do not directly merge these branches into `stable/mainline` or a dev branch:

- `codex/ai-gateway-call-isolation-audit`
- `codex/bio-search-ui-main`
- `codex/bioinformatics-safe-stage2`
- `codex/bio-search-ui-main-legacy`

Reasons:

- revert-of-revert history
- high file churn
- old architecture overlap
- likely conflicts with current desktop AI and Bioinformatics workflow pages

## 6. Validation Commands

### Shared Vocabulary

```bash
python3 -m pytest tests/shared -q
python3 -m pytest tests/architecture -q
python3 -m app.main --smoke-test
```

### Meta Analysis

```bash
python3 -m pytest tests/meta_analysis -q
python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q
python3 -m app.main --smoke-test
```

### Bioinformatics

```bash
python3 -m pytest tests/bioinformatics -q
python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q
python3 -m app.main --smoke-test
```

### Stable/Mainline Packaging Gate

```bash
python3 scripts/run_tests.py
python3 scripts/package_app.py --output-dir /Users/changdali/Desktop --app-name BioMedPilot --smoke-test
```

## 7. Operational Guardrails

- Do not delete old branches until attached worktrees are audited and removed intentionally.
- Do not force-move branches attached to worktrees.
- Prefer cherry-pick or manual patch review for old high-risk branches.
- Keep AI Gateway and query intelligence module boundaries intact:
  - Bioinformatics uses `bio_` task types.
  - Meta Analysis uses `meta_` task types.
  - Direct Ollama calls remain isolated to `app/shared/ai_gateway/providers/ollama_provider.py`.
- Rebuild `/Users/changdali/Desktop/BioMedPilot.app` only from `stable/mainline` or an explicitly approved release branch.

## 8. Consolidation Log

### Meta Analysis Round 1

Completed on `dev/meta-analysis`.

- Reviewed `codex/meta-workflow-ui` against `dev/meta-analysis`.
- Branch-only commit: `8b6d0b6 feat(meta): connect workflow ui later stages`.
- Scope: Meta workspace page routing, UI-07 to UI-18 developer preview pages, navigation tests, and `docs/meta_ui_06_18_implementation_plan.md`.
- `git merge-tree` reported no text conflicts.
- Required Meta service imports already existed on `dev/meta-analysis`.
- Cherry-picked `8b6d0b6` into `dev/meta-analysis`.
- Did not process `codex/meta-search-ui-main`.
- Did not process high-risk `codex/ai-gateway-call-isolation-audit`.

Validation passed before this log update:

```bash
python3 -m pytest tests/meta_analysis -q
python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py tests/meta_analysis/test_meta_workspace_ui_navigation.py -q
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

Result:

- `tests/meta_analysis`: 451 passed
- Meta UI/navigation subset: 26 passed
