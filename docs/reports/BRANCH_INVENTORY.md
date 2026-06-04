# Branch Inventory

Date: 2026-06-05

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `2fefc2c5e47b285683fbbbc304176fa73135bba7`

Current subject: `block standard payload schema drift`

## Audit Scope

Phase 2.5 is a read-only full-branch and legacy inventory. It exists to identify historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper-function material that may later become migration candidates.

This audit did not check out an old branch, merge, cherry-pick, replace the current UI, modify analysis algorithms, or migrate legacy code. The current UI remains the only mainline. Old branches, `legacy/` directories, and `archive/legacy_sources/**` are material libraries only.

Branch-only, legacy-only, mock, placeholder, dry-run, and testing-level outputs are not counted as completed current functionality.

## Governance Read

| Document | Rule applied |
| --- | --- |
| `../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Current UI is the only mainline; old branches are source material only; migrate one page/button/feature at a time after audit. |
| `../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Mock, placeholder, static, branch-only, and testing-level output must not be promoted to real completed analysis. |

## Current Worktree State

The worktree was already dirty before this Phase 2.5 refresh. These non-report changes were preserved and excluded from audit claims:

```text
 M analysis/modules/correlation/module.json
 M analysis/modules/deg/module.json
 M analysis/modules/docking/module.json
 M analysis/modules/enrichment/module.json
 M analysis/modules/immune_infiltration/module.json
 M analysis/modules/molecular_dynamics/module.json
 M analysis/modules/multivariate/module.json
 M analysis/modules/spatial_transcriptomics/module.json
 M analysis/modules/survival/module.json
 M analysis/modules/univariate/module.json
 M analysis/registry/analysis_modules.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

Only `docs/reports/**` files are Phase 2.5 outputs.

## Commands Used

| Command | Purpose / result |
| --- | --- |
| `sed -n '1,220p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Read migration rules. |
| `sed -n '1,220p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Read real-loop rules. |
| `git status --short --branch` | Captured branch and dirty worktree. |
| `git branch --show-current` | Confirmed `dev/bioinformatics`. |
| `git rev-parse HEAD` | Confirmed `2fefc2c5e47b285683fbbbc304176fa73135bba7`. |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' refs/heads refs/remotes` | Enumerated local branch heads. |
| `git log --all --decorate --oneline --max-count=120` | Reviewed recent multi-branch history. |
| `find . ... -name '*legacy*'` | Located legacy directories without executing them. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -type f \| wc -l` | Counted 920 tracked legacy/archive files in the audited boundary. |
| `git diff --shortstat HEAD..<branch> -- ...` | Sampled branch divergence without checkout. |
| `git ls-tree -r --name-only <branch> -- ...` | Sampled branch-only candidate files without checkout. |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|Meta\|Bioinformatics" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Sampled current UI/action/test surfaces. |

No functional tests were required for this documentation-only inventory. Tests would validate the current checkout, not prove old branch runtime availability.

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `2fefc2c` | 2026-06-05 | block standard payload schema drift | Current source of truth for this worktree | source of truth |
| `dev/release-internal-test` | `6658c3a` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | Rich Bio DEG/enrichment/survival/risk/report history | candidate library only |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | Formal DEG and ReleaseBuild gate material | candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Survival/clinical and enrichment convergence material | candidate library only |
| `stable/mainline` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Older MainLine formal DEG baseline | historical baseline |
| `feature/meta-l3-ui-loop` | `5f6150a` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Focused Meta UI proof; represented by current history | reference |
| `dev/meta-analysis` | `3aad58a` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history | reference/candidate library |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Meta L3 receive branch | reference |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bb` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine Meta governance | reference |
| `dev/ui-shell` | `6d5dca5` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell/design material | design reference only |
| `integration/release-ui-shell-scoped-migration` | `610cc20` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline/screenshots | design reference only |
| `integration/release-labtools-c1-module-nav` | `ef526dc` | 2026-06-01 | feat(ui): gate bio report exports | Cross-module UI shell/report export material | UI reference only |
| `integration/release-bio-c1-ui-shell` | `f0af1d4` | 2026-06-04 | fix(labtools): scope latest imagej macro extensions | LabTools/UI shell integration | out of Bio/Meta scope |
| `dev/labtools` | `c418eba` | 2026-06-04 | Fix gated cell ImageJ macro integration scope | LabTools feature work | out of Bio/Meta scope |
| `dev/integration` | `056a1f3` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration audit branch | reference |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Integration merge planning audit | reference |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c924` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | MainLine baseline pointer | historical |
| `codex/bio-geo-real-download-test` | `a90a2a1` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO recognition/download/DEG runner material | adapter/reference only |
| `codex/stage-3.6-deg-preflight` | `750f076` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Pre-contract DEG preflight | superseded |
| `codex/bio-search-ui-main`, `codex/bio-search-ui-main-legacy`, `codex/bio-search-ui-integrate-main`, `codex/bio-ui-download-integration` | various | 2026-05 | GEO search UI refinements | Search/download UI wording and behavior references | reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio project wizard | UI material only |
| `codex/meta-workflow-ui` | `8b6d0b6` | 2026-05-10 | feat(meta): connect workflow ui later stages | Early Meta workflow UI | superseded/reference only |
| `codex/meta-analysis-refresh` | `e9c17c2` | 2026-05-11 | Refine Meta project home UI | Old Meta home UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed execution branch | superseded/reference only |
| `codex/ai-gateway-call-isolation-audit`, `codex/ai-gateway-ollama-provider`, `dev/ai-gateway` | various | 2026-05 | AI gateway/provider/governance | AI draft routing context | out of Phase 2.5 migration scope |
| `codex/shared-vocabulary-refresh`, `dev/shared-vocabulary`, vocabulary branches | various | 2026-05 | Medical vocabulary resources | Search/query resources | resource reference only |
| `codex/integration-labtools-ui-c2-carryover`, `codex/integration-meta-ocr-labtools-carryover`, LabTools/UI branches | various | 2026-05 | LabTools/UI/OCR integration material | Cross-module design/context only | out of Bio/Meta analysis migration scope |

## High-Relevance Branch Divergence

Selected branch deltas are large. Whole-branch carry-over is unsafe because these branches would overwrite or delete current UI, standard package/runtime contracts, or current Bio/Meta paths.

| Branch | Shortstat in audited paths | Practical implication |
| --- | --- | --- |
| `dev/release-internal-test` | 2130 files changed, 135504 insertions, 85272 deletions | Rich Bio material, but whole-branch merge would reshape current contracts and scaffolds. |
| `codex/releasebuild-formal-deg-carryover` | 1104 files changed, 91914 insertions, 78237 deletions | Useful formal DEG/ReleaseBuild material, but older and layout-divergent. |
| `codex/mainline-survival-clinical-carryover` | 744 files changed, 15914 insertions, 69529 deletions | Survival/clinical history, but older than current standard package work. |
| `stable/mainline` | 801 files changed, 14358 insertions, 80408 deletions | Historical formal DEG baseline only. |
| `feature/meta-l3-ui-loop` | 165 files changed, 334 insertions, 8997 deletions | Focused Meta proof; already represented by current history. |
| `dev/meta-analysis` | 617 files changed, 20790 insertions, 78060 deletions | OCR/fulltext/package material; not current-proven. |
| `dev/ui-shell` | 2128 files changed, 66130 insertions, 170085 deletions; rename detection warning | UI design/shell material only; direct migration unsafe. |

## Inventory Conclusion

The repository contains substantial historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper material. No old branch is safe to merge wholesale. Candidate functionality must be selected one at a time, mapped to a current UI entry, adapted or rewritten against current contracts, and then proven with current tests and real output evidence.

Mock, placeholder, dry-run, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

## Stop Point

This document is inventory output only. It does not authorize branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy runtime migration.
