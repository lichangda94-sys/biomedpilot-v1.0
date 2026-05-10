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

### Shared Vocabulary Round 1

Completed on `dev/shared-vocabulary`.

- `stable/mainline` has incorporated the branch consolidation plan originally created as `a44144b`.
- `dev/shared-vocabulary`, `dev/meta-analysis`, and `dev/bioinformatics` were fast-forwarded to `stable/mainline`.
- `dev/shared-vocabulary` cherry-picked `b778543 docs(shared): isolate medical vocabulary worktree`.
- `codex/vocab-line-stabilization` is now an archive candidate, but it was not deleted in this round.

Validation passed:

```bash
python3 -m pytest tests/shared -q
python3 -m compileall -q app tests scripts
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
python3 scripts/run_tests.py
```

Result:

- `tests/shared`: 154 passed
- `scripts/run_tests.py`: 978 passed

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

### Meta Analysis Round 2

Completed on `dev/meta-analysis`.

- Reviewed `codex/meta-search-ui-main` against `dev/meta-analysis`.
- Branch-only commits reported by `git log dev/meta-analysis..codex/meta-search-ui-main`:
  - `8e323ae feat(meta): connect search strategy draft to workflow page`
  - `b026f9d feat(meta): execute confirmed PubMed search`
- `git merge-tree` reported text conflicts in:
  - `app/meta_analysis/pages/protocol_page.py`
  - `app/meta_analysis/search/__init__.py`
- The conflicting branch content is older than the current `dev/meta-analysis` implementation:
  - PubMed execution service and report writing already exist.
  - Search strategy concept blocks already include `role`.
  - Embase drafts already use `ti,ab,kw`.
  - Current `dev/meta-analysis` also includes the newer PubMed candidate handoff path from `codex/meta-workflow-ui` consolidation.
- No commits were cherry-picked from `codex/meta-search-ui-main`.
- Recommendation: treat `codex/meta-search-ui-main` as represented by current `dev/meta-analysis`; do not directly merge. Keep temporarily as an archive/reference candidate until final branch cleanup.
- Did not process high-risk `codex/ai-gateway-call-isolation-audit`.

Validation passed before this log update:

```bash
python3 -m pytest tests/meta_analysis/test_meta_pubmed_search_service.py tests/meta_analysis/test_pubmed_candidates_handoff.py tests/ui/test_meta_analysis_workflow_pages.py -q
```

Result:

- PubMed service / handoff / Meta workflow UI subset: 29 passed

### Meta Analysis Final Review

Completed on `dev/meta-analysis`.

- Current HEAD: `e9e6d00 docs(repo): record meta search branch consolidation`.
- `dev/meta-analysis` is 3 commits ahead of `stable/mainline` and 0 commits behind.
- Current branch-only commits:
  - `df411c3 feat(meta): connect workflow ui later stages`
  - `4db1286 docs(repo): record meta workflow branch consolidation`
  - `e9e6d00 docs(repo): record meta search branch consolidation`
- Current branch-only file changes are limited to:
  - `app/meta_analysis/workspace.py`
  - `tests/meta_analysis/test_meta_workspace_ui_navigation.py`
  - `docs/meta_ui_06_18_implementation_plan.md`
  - `docs/branch_consolidation_plan.md`
- No Bioinformatics, shared query intelligence, AI Gateway, medical vocabulary data, Bio scripts, or packaging script changes were found in the branch diff against `stable/mainline`.

Meta branch handling status:

- `codex/meta-workflow-ui`: integrated by cherry-picking its workflow UI change as `df411c3`.
- `codex/meta-search-ui-main`: not cherry-picked during consolidation because its remaining branch commits are already covered by the newer current Meta implementation and conflict with the newer PubMed candidate handoff UI.
- `codex/ai-gateway-call-isolation-audit`: high-risk revert-of-revert branch. Do not integrate automatically. It touches `app/shell/` and broad Meta UI/test files and requires separate human review if anything is needed.

Validation passed:

```bash
python3 -m pytest tests/meta_analysis -q
python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q
python3 -m compileall -q app tests scripts
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
python3 scripts/run_tests.py
```

Result:

- `tests/meta_analysis`: 451 passed
- Meta workflow UI tests: 21 passed
- `compileall`: passed
- App smoke test: passed
- `scripts/run_tests.py`: 979 passed

Conclusion:

- `dev/meta-analysis` consolidation is complete for the reviewed Meta branches.
- Next consolidation work can move to `dev/bioinformatics`, starting with the low-risk `codex/bio-geo-real-download-test` branch.

### Bioinformatics Round 1

Completed on `dev/bioinformatics`.

- Reviewed `codex/bio-geo-real-download-test` against `dev/bioinformatics`.
- Branch-only commit reported by `git log dev/bioinformatics..codex/bio-geo-real-download-test`:
  - `a90a2a1 feat(bio): harden GEO asset recognition and DEG runner`
- Branch-only file scope was limited to allowed Bioinformatics paths:
  - `app/bioinformatics/download/dataset_download_service.py`
  - `app/bioinformatics/project_recognition.py`
  - `app/bioinformatics/services/geo_differential_expression_runner.py`
  - `tests/bioinformatics/test_dataset_download_service.py`
  - `tests/bioinformatics/test_geo_differential_expression_runner.py`
  - `tests/bioinformatics/test_workflow_adapters.py`
- No Meta Analysis, shared query intelligence, AI Gateway, shell, main app, or packaging paths were touched by the branch diff.
- No code was cherry-picked. Current `dev/bioinformatics` already has the same capabilities in newer form:
  - GEO real download and manifest audit handling.
  - GEO asset recognition hardening for family SOFT, Series Matrix, and supplementary assets.
  - Series Matrix expression table parsing.
  - Incomplete `.part` download handling through atomic partial download replacement and cleanup.
  - GEO differential expression runner.
  - Group preview support.
  - Enrichment and correlation runners.
  - Random GEO recognition audit script.
  - Supplementary expression candidate prioritization.
  - GSE invalid accession handling in the current download service.
- Recommendation: treat `codex/bio-geo-real-download-test` as covered by current `dev/bioinformatics`; keep it temporarily as an archive/reference candidate. Do not merge the whole branch.
- Did not process `codex/bio-search-ui-main`.
- Did not process `codex/bioinformatics-safe-stage2`.

Validation passed before this log update:

```bash
python3 -m pytest tests/bioinformatics -q
python3 -m compileall -q app tests scripts
```

Result:

- `tests/bioinformatics`: 215 passed
- `compileall`: passed

### Bioinformatics Round 2

Completed on `dev/bioinformatics`.

- Reviewed `codex/bio-search-ui-main` against `dev/bioinformatics` in read-only mode.
- Audit report: `docs/bio_search_ui_main_gap_audit.md`.
- Ahead / behind from `dev/bioinformatics` to `codex/bio-search-ui-main`: `73 30`.
- Branch-only commits reviewed: 30.
- No code was merged, cherry-picked, copied, or manually migrated.
- The branch contains a large older Bioinformatics search/download/UI line. Current `dev/bioinformatics` already covers the substantive functionality in newer form:
  - Chinese dataset search and GSE accession search.
  - Dataset detail, notes, pending list, cache actions, selected recognition, and readiness flow.
  - GEO download manifests, supplementary prioritization, metadata profiles, candidate comparisons, group preview, and random GEO recognition audit.
  - GEO DEG, enrichment, and correlation runners.
- High-risk content identified:
  - Cross-module changes under `app/shared/query_intelligence/` and `tests/shared/`.
  - Old direct Ollama calls in `app/bioinformatics/download/geo_text_summary_service.py`.
- Recommendation: do not merge or cherry-pick `codex/bio-search-ui-main`. Treat it as historical reference. At most, manually review UI copy or test-case ideas later.
- Did not process `codex/bioinformatics-safe-stage2`.

### Bioinformatics Round 3

Completed on `dev/bioinformatics`.

- Reviewed `codex/bioinformatics-safe-stage2` against `dev/bioinformatics` in read-only mode.
- Audit report: `docs/bioinformatics_safe_stage2_gap_audit.md`.
- Ahead / behind from `dev/bioinformatics` to `codex/bioinformatics-safe-stage2`: `141 61`.
- Branch-only commits reviewed: 61.
- No code was merged, cherry-picked, copied, or manually migrated.
- The branch is an old large Bioinformatics architecture line. It adds or changes project workspace contracts, acquisition center, recognition/readiness/standardization layers, analysis task center, result manager, report builder, local venv packaging, examples, and broad tests.
- High-risk content identified:
  - Cross-cutting app and shell changes under `app/main.py` and `app/shell/theme.py`.
  - Packaging/dependency changes under `scripts/package_app.py`, `pyproject.toml`, `requirements.txt`, and `requirements-dev.txt`.
  - Shared storage/feature availability changes under `app/shared/`.
- Current `dev/bioinformatics` already covers the core workflow in a newer form through current workspace pages, search/download, metadata profile, group preview, project recognition/readiness/standardization, project analysis tasks, result/report surfaces, and AI Gateway boundaries.
- Recommendation: keep `codex/bioinformatics-safe-stage2` only as a historical architecture reference. Do not merge or cherry-pick it. If future work needs it, extract design ideas manually from the audit report.
