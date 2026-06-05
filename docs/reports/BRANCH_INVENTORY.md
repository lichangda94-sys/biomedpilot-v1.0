# Branch Inventory

Date: 2026-06-05

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Current branch: `dev/bioinformatics`

Current HEAD: `a6ccd8c2ed8d30a769dd7eb849b0daad29e0e43f`

Current subject: `align analysis remediation queue with lock evidence gates`

## Audit Scope

Phase 2.5 is a read-only inventory of old branches, legacy directories, historical implementations, UI material, Bioinformatics features, Meta Analysis features, plots, reports, exports, tests, and helper functions.

This audit did not check out old branches, merge, cherry-pick, migrate legacy code, change the current UI, or modify analysis algorithms. The current UI remains the only mainline. Old branches and legacy directories are material libraries only.

Mock, placeholder, dry-run, preflight-only, testing-level, branch-only, and legacy-only output is not counted as completed current functionality.

## Governance Read

| Document | Rule applied |
| --- | --- |
| `../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Current UI is the only mainline; old branches are source material only; migration requires page/button mapping, contract mapping, focused tests, and real output proof. |
| `../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | A real loop must have real input, real statistics/analysis, real table, real figure, real report/export, and current UI discovery. Mock or placeholder output cannot be promoted. |

## Current Worktree State

Observed before report edits:

```text
## dev/bioinformatics
 M app/analysis_runtime/__init__.py
M  app/analysis_runtime/architecture_status.py
M  docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
M  docs/R_ANALYSIS_ARCHITECTURE.md
M  docs/R_ANALYSIS_REMEDIATION_PLAN.md
M  tests/test_r_analysis_architecture_contract.py
?? analysis/registry/standard_worker_migration_evidence.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

Those pre-existing architecture/runtime changes and untracked paths were preserved and excluded from this Phase 2.5 audit. Only `docs/reports/**` files are Phase 2.5 outputs.

## Commands Used

| Command | Purpose / result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Read migration restrictions. |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Read real-loop restrictions. |
| `git status --short --branch` | Captured current branch and untracked paths. |
| `git branch --all --no-color` | Enumerated available branches without checkout. |
| `git rev-parse HEAD` | Confirmed current HEAD `a6ccd8c2ed8d30a769dd7eb849b0daad29e0e43f`. |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' refs/heads` | Captured local branch heads and subjects. |
| `git log --oneline --decorate --max-count=30 --all` | Sampled recent cross-branch history. |
| `find app analysis archive docs tests scripts -type d ...` | Located legacy directories without executing them. |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -type f \| wc -l` | Counted 920 legacy/archive files in the audited boundary. |
| `git diff --shortstat HEAD..<branch> -- app analysis tests scripts docs` | Sampled high-relevance branch divergence without checkout. |
| `git ls-tree -r --name-only <branch> -- ...` | Sampled candidate files from old branches without checkout. |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|Meta" ...` | Sampled current UI/button/action surfaces. |

No functional tests were required for this audit-only inventory. Functional tests would validate the current checkout, not prove old-branch runtime availability.

## Local Branch Inventory

| Branch | HEAD | Date | Subject | Bio/Meta/UI relevance | Disposition |
| --- | --- | --- | --- | --- | --- |
| `dev/bioinformatics` | `a6ccd8c2` | 2026-06-05 | align analysis remediation queue with lock evidence gates | Current source of truth; includes Bio/Meta current UI, standard package governance, external analysis environment gates, R architecture status gates, remediation queue rows, migration matrix surfacing, and lock/evidence validation gates | source of truth |
| `dev/release-internal-test` | `6658c3a3` | 2026-05-29 | fix(bio): close ReleaseBuild enrichment production gate | Rich Bio DEG/enrichment/survival/risk/report history | candidate library only |
| `codex/releasebuild-formal-deg-carryover` | `a8adc29a` | 2026-05-27 | refresh ReleaseBuild analysis internal test gate | Formal DEG and ReleaseBuild gate material | candidate library only |
| `codex/mainline-survival-clinical-carryover` | `74775fe4` | 2026-05-28 | docs(bio): document MainLine enrichment convergence | Survival/clinical and enrichment convergence material | candidate library only |
| `stable/mainline` | `be8c9243` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | Historical MainLine formal DEG baseline | historical baseline |
| `feature/meta-l3-ui-loop` | `5f6150a8` | 2026-05-29 | feat(meta): prove current UI L3 result loop | Focused Meta UI proof line; represented by current reports/tests | reference |
| `dev/meta-analysis` | `3aad58a1` | 2026-05-18 | Handle LaunchServices psn arguments | Meta OCR/fulltext/package history | reference/candidate library |
| `integration/phase4-meta-l3-scoped-pick` | `3771eb3a` | 2026-05-29 | feat(meta): scope Phase 4 L3 UI proof into integration | Meta L3 receive branch | reference |
| `mainline/phase4-meta-l3-scoped-pick` | `41e02bbf` | 2026-05-29 | docs(project-control): add constitution v2 for UI baseline governance | MainLine Meta governance | reference |
| `dev/ui-shell` | `6d5dca57` | 2026-06-01 | docs(project-control): add high fidelity UI integration handoff | UI shell/design material | design reference only |
| `integration/release-ui-shell-scoped-migration` | `610cc201` | 2026-05-31 | feat(ui): restore scoped UI shell baseline | UI shell baseline/screenshots | design reference only |
| `integration/release-labtools-c1-module-nav` | `ef526dcf` | 2026-06-01 | feat(ui): gate bio report exports | Shared UI/report shell material | UI reference only |
| `integration/release-bio-c1-ui-shell` | `f0af1d43` | 2026-06-04 | fix(labtools): scope latest imagej macro extensions | LabTools/UI integration material | out of Bio/Meta analysis scope |
| `dev/labtools` | `c418eba4` | 2026-06-04 | Fix gated cell ImageJ macro integration scope | LabTools line | out of scope |
| `dev/integration` | `056a1f3a` | 2026-05-29 | docs(integration): add Phase 4 scoped integration audit | Integration audit branch | reference |
| `audit/integration-bioinformatics-merge-plan` | `d6a5914a` | 2026-05-29 | docs(integration): add bioinformatics merge plan audit | Integration merge planning audit | reference |
| `audit/mainline-phase4-meta-l3-scope-plan` | `be8c9243` | 2026-05-21 | carry over Bioinformatics formal DEG MVP to MainLine | MainLine baseline pointer | historical |
| `codex/bio-geo-real-download-test` | `a90a2a19` | 2026-05-06 | feat(bio): harden GEO asset recognition and DEG runner | Older GEO recognition/download/DEG runner material | adapter/reference only |
| `codex/stage-3.6-deg-preflight` | `750f0769` | 2026-05-12 | feat(bioinformatics): add DEG executor preflight | Pre-contract DEG preflight | superseded |
| `codex/bio-search-ui-main`, `codex/bio-search-ui-main-legacy`, `codex/bio-search-ui-integrate-main`, `codex/bio-ui-download-integration` | various | 2026-05 | GEO search/download UI refinements | Search/download UI wording and behavior references | reference only |
| `codex/bioinformatics-safe-stage2` | `75fe3c3d` | 2026-04-30 | feat(bio): add Chinese project wizard UI | Early Bio project wizard | UI material only |
| `codex/meta-workflow-ui` | `8b6d0b6c` | 2026-05-10 | feat(meta): connect workflow ui later stages | Early Meta workflow UI | superseded/reference only |
| `codex/meta-analysis-refresh` | `e9c17c2d` | 2026-05-11 | Refine Meta project home UI | Old Meta home UI refinements | UI reference only |
| `codex/meta-search-ui-main` | `b026f9d5` | 2026-05-04 | feat(meta): execute confirmed PubMed search | Older PubMed execution branch | superseded/reference only |
| `dev/ai-gateway`, `codex/ai-gateway-*` | various | 2026-05 | AI gateway/provider/governance | AI draft routing context | out of Phase 2.5 migration scope |
| `dev/shared-vocabulary`, `codex/shared-vocabulary-refresh`, vocabulary branches | various | 2026-05 | Medical vocabulary resources | Search/query resources | resource reference only |
| LabTools/UI integration branches | various | 2026-05/06 | LabTools/UI/OCR integration material | Cross-module context only | out of Bio/Meta analysis migration scope |

## High-Relevance Branch Divergence

Selected branch deltas are large. Whole-branch carry-over is unsafe because these branches would overwrite or delete current UI, standard package/runtime contracts, or current Bio/Meta paths.

| Branch | Shortstat in audited paths | Practical implication |
| --- | --- | --- |
| `dev/release-internal-test` | 2643 files changed, 209722 insertions, 101548 deletions | Rich Bio material, but whole-branch merge would reshape current contracts and scaffolds. |
| `codex/releasebuild-formal-deg-carryover` | 1572 files changed, 147623 insertions, 93970 deletions | Useful formal DEG/ReleaseBuild material, but older and layout-divergent. |
| `codex/mainline-survival-clinical-carryover` | 961 files changed, 31535 insertions, 76163 deletions | Survival/clinical history, but older than current standard package and architecture gate work. |
| `stable/mainline` | 1018 files changed, 29979 insertions, 87042 deletions | Historical formal DEG baseline only. |
| `feature/meta-l3-ui-loop` | 175 files changed, 342 insertions, 15512 deletions | Focused Meta proof; already represented by current history/reports. |
| `dev/meta-analysis` | 683 files changed, 25387 insertions, 86732 deletions | OCR/fulltext/package material; not current-proven. |
| `dev/ui-shell` | 2224 files changed, 84914 insertions, 179343 deletions | UI design/shell material only; direct migration unsafe. |
| `integration/release-ui-shell-scoped-migration` | 1039 files changed, 37624 insertions, 87591 deletions | UI shell reference, not a Bio/Meta analysis source. |
| `codex/bio-geo-real-download-test` | 652 files changed, 4728 insertions, 110886 deletions | Old GEO/DEG path diverges sharply from current contracts. |
| `codex/stage-3.6-deg-preflight` | 1143 files changed, 13294 insertions, 178985 deletions | Superseded preflight material. |
| `codex/meta-workflow-ui` | 552 files changed, 6429 insertions, 87004 deletions | Old Meta UI reference. |
| `codex/meta-search-ui-main` | 688 files changed, 2998 insertions, 121587 deletions | Old PubMed execution reference. |

## Inventory Conclusion

The repository contains substantial historical UI, Bioinformatics, Meta Analysis, plot, report, export, test, and helper material. No old branch is safe to merge wholesale.

Current HEAD has advanced beyond earlier Phase 2.5 reports. It now exposes analysis architecture status gates, remediation queue rows, standard worker migration matrix rows, lock evidence validation, and standard worker migration evidence validation in addition to standard package/result/input manifest governance. Those are current-gate facts, not permission to migrate old branch logic.

Future migration must select exactly one current UI entry and one candidate capability, then map it to the current contract, adapt or rewrite it, and prove it with current tests and real output evidence.

## Stop Point

This document is inventory output only. It does not authorize branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy runtime migration.
