# BioMedPilot Branch Consolidation Audit

Date: 2026-05-10

Scope: read-only Git branch and content audit, plus this report. No merge, rebase, reset, branch deletion, push, checkout, or code edits were performed.

## 1. Baseline State

| Item | Value |
| --- | --- |
| Repository | `/Users/changdali/Documents/BioMedPilot` |
| Current branch | `codex/ai-gateway-ollama-provider` |
| Current HEAD | `f921786c74f0979a29320447ead95b18e799ba60` |
| Latest commit | `f921786 feat(bio): add explicit online dataset search actions` |
| Working tree before audit | clean |
| Local branch count | 19 |
| Remote branch count | 0 |

The current branch is the best mainline candidate for consolidation because it is the active HEAD, contains the latest AI Gateway and desktop local AI work, includes explicit Bioinformatics online dataset search actions, and was used to rebuild `/Users/changdali/Desktop/BioMedPilot.app` with bundle `git_head=f921786`.

## 2. Raw Branch Inventory

### Local Branches

- `codex/ai-gateway-call-isolation-audit`
- `codex/ai-gateway-ollama-provider`
- `codex/bio-chinese-dataset-search-page`
- `codex/bio-geo-real-download-test`
- `codex/bio-search-ui-integrate-main`
- `codex/bio-search-ui-main`
- `codex/bio-search-ui-main-legacy`
- `codex/bio-ui-download-integration`
- `codex/bioinformatics-safe-stage2`
- `codex/biomedpilot-root`
- `codex/medical-vocabulary-main`
- `codex/merge-latest-app-content`
- `codex/meta-search-main`
- `codex/meta-search-main-v2`
- `codex/meta-search-ui-main`
- `codex/meta-workflow-ui`
- `codex/migrate-medical-vocabulary-stage2`
- `codex/restore-ui01-login-baseline`
- `codex/vocab-line-stabilization`

### Remote Branches

No remote branches were listed by `git branch -r`.

### Worktree-Attached Branches

These branches are currently checked out in separate worktrees and should not be deleted or force-moved without first auditing those worktrees:

- `codex/bio-geo-real-download-test`: `/Users/changdali/Documents/BioMedPilot/.worktrees/bio-geo-real-download-test`
- `codex/bio-search-ui-main`: `/Users/changdali/Documents/BioMedPilot-bio`
- `codex/bioinformatics-safe-stage2`: `/Users/changdali/Documents/BioMedPilot/.worktrees/bioinformatics-safe-stage2`
- `codex/meta-search-main-v2`: `/Users/changdali/Documents/BioMedPilot/.worktrees/meta-search-main`
- `codex/meta-search-ui-main`: `/Users/changdali/Documents/BioMedPilot-meta`
- `codex/vocab-line-stabilization`: `/Users/changdali/Documents/BioMedPilot-vocab`

## 3. Branch Classification Table

Base used for comparison: `codex/ai-gateway-ollama-provider`.

`ahead/behind` format below is `branch-only / base-only` from `git rev-list --left-right --count base...branch`.

| Branch | Type | Ahead/behind | Recent commit | Path summary | Keep? | Merge? | Risk |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `codex/ai-gateway-ollama-provider` | packaging-ui / shared-vocabulary / bio | `0 / 0` | `f921786 feat(bio): add explicit online dataset search actions` | AI Gateway, Bioinformatics local AI, desktop packaging-ready state | yes, mainline candidate | no | low |
| `codex/ai-gateway-call-isolation-audit` | meta / packaging-ui / experimental | `1 / 5` | `2fea2a6 Revert "Revert "Revert "feat(meta): integrate early workflow workspace UI"""` | `app/meta_analysis/`, `app/shell/`, meta UI tests | temporarily keep | human review only | high |
| `codex/bio-chinese-dataset-search-page` | experimental / likely merged | `0 / 40` | `dcb07cc feat(meta): add pico workspace v2` | no branch-only diff versus current base | optional archive | no | low |
| `codex/bio-geo-real-download-test` | bio | `1 / 44` | `a90a2a1 feat(bio): harden GEO asset recognition and DEG runner` | `app/bioinformatics/download/`, recognition, DEG runner tests | keep until reviewed | possibly cherry-pick or compare-equivalence | medium |
| `codex/bio-search-ui-integrate-main` | bio / shared-vocabulary / likely merged | `0 / 85` | `9bfc88b feat(bio): improve GEO disease-aware search UI` | no branch-only diff versus current base | optional archive | no | low |
| `codex/bio-search-ui-main` | bio | `30 / 70` | `26a33be fix(bio): simplify GEO Chinese summary panel` | broad Bioinformatics search/download/readiness/UI line, plus shared query intelligence changes | keep for review | cherry-pick only after file-by-file review | high |
| `codex/bio-search-ui-main-legacy` | bio / legacy | `1 / 88` | `65f1be9 feat(bio): improve GEO disease-aware search UI` | older `geo_import_page`, retrieval adapters, GEO search docs/tests | keep briefly | probably no, unless missing legacy behavior found | medium |
| `codex/bio-ui-download-integration` | bio / likely merged | `0 / 10` | `db9ad70 fix(bio): simplify GEO Chinese summary panel` | no branch-only diff versus current base | optional archive | no | low |
| `codex/bioinformatics-safe-stage2` | bio / packaging-ui / old architecture | `61 / 137` | `75fe3c3 feat(bio): add Chinese project wizard UI` | large alternate Bioinformatics architecture: acquisition center, project workspace, readiness, runners, reports | keep for careful review | cherry-pick selectively only | high |
| `codex/biomedpilot-root` | meta / packaging-ui / likely merged | `0 / 89` | `5e0627f feat(meta-ui): add chinese analysis reporting UI` | no branch-only diff versus current base | optional archive | no | low |
| `codex/medical-vocabulary-main` | shared-vocabulary / likely merged | `0 / 86` | `393b3e8 feat(shared): expand systematic medical vocabulary coverage` | no branch-only diff versus current base | optional archive | no | low |
| `codex/merge-latest-app-content` | packaging-ui / likely merged | `0 / 83` | `f87a5f6 fix(app): keep desktop theme light` | no branch-only diff versus current base | optional archive | no | low |
| `codex/meta-search-main` | shared-vocabulary / likely merged | `0 / 88` | `4e0ca45 feat(shared): migrate medical vocabulary index into BioMedPilot` | no branch-only diff versus current base | optional archive | no | low |
| `codex/meta-search-main-v2` | shared-vocabulary / likely merged | `0 / 88` | `4e0ca45 feat(shared): migrate medical vocabulary index into BioMedPilot` | no branch-only diff versus current base | optional archive after worktree check | no | low |
| `codex/meta-search-ui-main` | meta | `2 / 70` | `b026f9d feat(meta): execute confirmed PubMed search` | `app/meta_analysis/search/`, protocol/workflow pages, PubMed execution tests | keep | merge to meta branch after review | high |
| `codex/meta-workflow-ui` | meta | `1 / 4` | `8b6d0b6 feat(meta): connect workflow ui later stages` | `app/meta_analysis/workspace.py`, meta navigation tests, implementation plan | keep | likely merge to meta branch | medium |
| `codex/migrate-medical-vocabulary-stage2` | shared-vocabulary / likely merged | `0 / 88` | `4e0ca45 feat(shared): migrate medical vocabulary index into BioMedPilot` | no branch-only diff versus current base | optional archive | no | low |
| `codex/restore-ui01-login-baseline` | packaging-ui / likely merged | `0 / 81` | `ba837a7 fix(app): include restored runtime dirs in desktop package` | no branch-only diff versus current base | optional archive | no | low |
| `codex/vocab-line-stabilization` | shared-vocabulary / docs | `1 / 73` | `b778543 docs(shared): isolate medical vocabulary worktree` | `docs/stage_v1_medical_vocabulary_worktree_isolation.md` | keep or cherry-pick doc | optional cherry-pick to shared branch | low |

## 4. Branch Type Buckets

### Bioinformatics

- `codex/bio-geo-real-download-test`
- `codex/bio-search-ui-main`
- `codex/bio-search-ui-main-legacy`
- `codex/bioinformatics-safe-stage2`
- Already merged or probably obsolete bio branches: `codex/bio-chinese-dataset-search-page`, `codex/bio-search-ui-integrate-main`, `codex/bio-ui-download-integration`

### Meta Analysis

- `codex/meta-search-ui-main`
- `codex/meta-workflow-ui`
- `codex/ai-gateway-call-isolation-audit`
- Already merged or probably obsolete meta roots: `codex/biomedpilot-root`

### Shared Vocabulary / Chinese Search / Query Intelligence

- `codex/vocab-line-stabilization`
- Already merged shared vocabulary lines: `codex/medical-vocabulary-main`, `codex/meta-search-main`, `codex/meta-search-main-v2`, `codex/migrate-medical-vocabulary-stage2`
- Current mainline also contains AI Gateway and shared query intelligence work: `codex/ai-gateway-ollama-provider`

### Packaging / Desktop App / UI Shell

- Current mainline: `codex/ai-gateway-ollama-provider`
- Already merged or probably obsolete packaging branches: `codex/merge-latest-app-content`, `codex/restore-ui01-login-baseline`
- Meta/shell-impact branch needing review: `codex/ai-gateway-call-isolation-audit`

### Experimental / Archive Candidates

- Branches with `0` branch-only commits relative to current base are likely safe archive candidates after confirming no external worktree state is needed:
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

## 5. Branches With Unmerged Commits

The following branches have branch-only commits relative to `codex/ai-gateway-ollama-provider`:

| Branch | Branch-only commits | Primary value | Recommendation |
| --- | ---: | --- | --- |
| `codex/ai-gateway-call-isolation-audit` | 1 | meta/shell revert state | Do not merge blindly; inspect because it is a revert-of-revert chain touching shell and Meta UI. |
| `codex/bio-geo-real-download-test` | 1 | GEO recognition/DEG hardening | Compare with current Bioinformatics files; cherry-pick only if behavior is missing. |
| `codex/bio-search-ui-main` | 30 | large Bioinformatics feature line | Treat as historical integration source; diff-equivalence review before any cherry-pick. |
| `codex/bio-search-ui-main-legacy` | 1 | old GEO retrieval path | Probably superseded; review only if legacy `geo_import_page` behavior is needed. |
| `codex/bioinformatics-safe-stage2` | 61 | older broad Bioinformatics app architecture | High-conflict historical line; use only as reference or selective cherry-pick. |
| `codex/meta-search-ui-main` | 2 | Meta PubMed execution and search draft UI | Candidate for `dev/meta-analysis`, but must verify module boundary and no Bio query contamination. |
| `codex/meta-workflow-ui` | 1 | Meta workflow navigation/later-stage UI | Candidate for `dev/meta-analysis`; likely simpler than `meta-search-ui-main`. |
| `codex/vocab-line-stabilization` | 1 | shared vocabulary worktree isolation doc | Candidate for `dev/shared-vocabulary` or direct doc cherry-pick. |

## 6. Suggested Long-Term Branch Structure

Recommended stable base:

- `main` or current stable trunk should point to the content currently in `codex/ai-gateway-ollama-provider` at `f921786`.

Recommended long-lived development branches:

- `dev/bioinformatics`
  - Start from the stable base.
  - Integrate only reviewed Bioinformatics changes.
  - Primary audit sources: `codex/bio-geo-real-download-test`, `codex/bio-search-ui-main`, `codex/bioinformatics-safe-stage2`.

- `dev/meta-analysis`
  - Start from the same stable base.
  - Integrate only reviewed Meta Analysis changes.
  - Primary audit sources: `codex/meta-workflow-ui`, `codex/meta-search-ui-main`, and possibly selected shell/meta changes from `codex/ai-gateway-call-isolation-audit`.

- `dev/shared-vocabulary`
  - Start from the same stable base.
  - Integrate shared vocabulary, Chinese term mapping, query intelligence, and AI Gateway follow-up work.
  - Primary audit source: `codex/vocab-line-stabilization`; earlier shared vocabulary branches appear already merged.

## 7. Per-Branch Handling Recommendations

| Branch | Suggested target | Handling |
| --- | --- | --- |
| `codex/ai-gateway-ollama-provider` | stable base / future `main` | Preserve as current integration trunk until a formal `main` is chosen. |
| `codex/ai-gateway-call-isolation-audit` | `dev/meta-analysis` only if needed | Review manually; do not auto-merge revert chain. |
| `codex/bio-chinese-dataset-search-page` | archive | No branch-only commits relative to trunk. |
| `codex/bio-geo-real-download-test` | `dev/bioinformatics` | Compare six changed files against current trunk; cherry-pick missing hardening only. |
| `codex/bio-search-ui-integrate-main` | archive | No branch-only commits relative to trunk. |
| `codex/bio-search-ui-main` | `dev/bioinformatics` reference | Use as historical source; cherry-pick only validated missing commits. |
| `codex/bio-search-ui-main-legacy` | archive/reference | Likely superseded by current search center; preserve temporarily for regression comparison. |
| `codex/bio-ui-download-integration` | archive | No branch-only commits relative to trunk. |
| `codex/bioinformatics-safe-stage2` | `dev/bioinformatics` reference | High-conflict old architecture; review by feature, not by whole-branch merge. |
| `codex/biomedpilot-root` | archive | No branch-only commits relative to trunk. |
| `codex/medical-vocabulary-main` | archive | No branch-only commits relative to trunk. |
| `codex/merge-latest-app-content` | archive | No branch-only commits relative to trunk. |
| `codex/meta-search-main` | archive | No branch-only commits relative to trunk. |
| `codex/meta-search-main-v2` | archive after worktree check | No branch-only commits relative to trunk; currently has attached worktree. |
| `codex/meta-search-ui-main` | `dev/meta-analysis` | Review and likely merge/cherry-pick PubMed execution/search UI commits. |
| `codex/meta-workflow-ui` | `dev/meta-analysis` | Review and likely merge/cherry-pick workflow navigation commit. |
| `codex/migrate-medical-vocabulary-stage2` | archive | No branch-only commits relative to trunk. |
| `codex/restore-ui01-login-baseline` | archive | No branch-only commits relative to trunk. |
| `codex/vocab-line-stabilization` | `dev/shared-vocabulary` | Cherry-pick doc commit or keep as documentation reference. |

## 8. Conflict and Risk Notes

### Likely Conflict Hotspots

- `app/bioinformatics/workflow_pages.py`: touched by current AI/online search work and older Bio UI branches.
- `app/bioinformatics/search_center/*`: touched by current query intelligence routing and old Bio search branches.
- `app/bioinformatics/download/*`: current Gateway-based GEO summary path may conflict with older direct/local model or download code.
- `app/meta_analysis/workflow_pages.py`, `app/meta_analysis/workspace.py`: likely conflicts between Meta workflow UI and search UI branches.
- `app/shell/main_window.py`, `app/shell/module_selection.py`: shell-level changes in `codex/ai-gateway-call-isolation-audit` may conflict with packaging/UI baseline.
- `tests/ui/test_bioinformatics_workflow_pages.py` and `tests/ui/test_meta_analysis_workflow_pages.py`: high churn, likely non-semantic conflicts.
- `docs/stage_*` and audit docs: many branches added stage-specific reports; merge selectively.

### Duplicate Implementation Risks

- Bioinformatics GEO search/download exists in multiple historical shapes: old `retrieval/geo_search_service.py`, newer `search_center`, and current desktop page integration.
- Bioinformatics project/workflow architecture in `codex/bioinformatics-safe-stage2` may duplicate current `project_workspace`, `project_readiness`, `project_standardization`, and workflow pages.
- Shared query intelligence and AI Gateway now live on current trunk; older local-model or vocabulary branches may predate the module/task boundary rules.
- Meta search branches may reintroduce PubMed execution paths that should remain isolated to Meta Analysis and never leak into Bioinformatics.

### Packaging Risks

- The current desktop App was rebuilt from `f921786`; any future base switch should rerun `scripts/package_app.py --output-dir /Users/changdali/Desktop --app-name BioMedPilot --smoke-test`.
- Branches touching `app/main.py`, shell navigation, `scripts/package_app.py`, or runtime resource directories can change packaged behavior even if module tests pass.
- Attached worktree branches should be handled carefully because Git will reject some branch operations while those worktrees exist.

## 9. Suggested Merge Order

1. Establish formal stable base from `codex/ai-gateway-ollama-provider` as `main` or equivalent.
2. Create `dev/shared-vocabulary` from that base; cherry-pick or copy the `codex/vocab-line-stabilization` doc if still useful.
3. Create `dev/meta-analysis` from the same base; review `codex/meta-workflow-ui` first, then `codex/meta-search-ui-main`.
4. Create `dev/bioinformatics` from the same base; review `codex/bio-geo-real-download-test` first because it is small, then selectively audit `codex/bio-search-ui-main` and `codex/bioinformatics-safe-stage2`.
5. After each target branch integration, run targeted tests plus full packaging smoke before merging back to the stable base.

## 10. Recent Commit Snapshot

The global graph top 80 commits shows current HEAD at `f921786`, followed by:

- `adca54a feat(app): add desktop local ai module via ai gateway`
- `d2a006d refactor(shared): route query intelligence local model through ai gateway`
- `a0e1b64 feat(shared): add ollama provider for ai gateway`
- `d6eb9d7 feat(meta): add dedup review workspace page`
- `92d70ca test(shared): guard ai gateway ollama call isolation`
- `75c3f0a feat(shared): add internal ai gateway foundation`

Branches with no branch-only commits are behind the current integration trunk and appear already incorporated or superseded by later work.
